#!/usr/bin/env python3
"""Executable boundary for Concorde's public skills (proposal section 6.3).

Only skills are directly invocable. This launcher accepts exactly one of the public skill names,
maps it to its operation module through the `operation:` front-matter field of
`skills/<name>/SKILL.md`, and runs the shared trusted stdin/envelope handling
(`concorde.development.operation_host.json_main`) through that module's own `run`. Stage
operations have no launcher and no direct invocation. `<skill-name> --runtime-check` is a
lightweight offline smoke check used by the managed runtime provisioner: it loads the operation
module and confirms LangGraph is importable, without touching stdin or launching an agent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent

SKILL_NAMES = (
    "concorde-main",
    "concorde-dev-loop",
    "concorde-specify-loop",
    "concorde-issues",
    "concorde-review",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
)


class UnknownOperationError(ValueError):
    code = "unknown_operation"


def _declared_operation(package_root: Path, skill_name: str) -> str:
    from concorde.spec.frontmatter import FrontMatterError, parse_document

    source = package_root / "skills" / skill_name / "SKILL.md"
    try:
        metadata, _ = parse_document(
            source.read_text(encoding="utf-8"), source.as_posix()
        )
    except (OSError, UnicodeError, FrontMatterError) as error:
        raise UnknownOperationError(
            f"cannot read skill source for {skill_name!r}: {error}"
        ) from error
    operation = metadata.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        raise UnknownOperationError(f"skill {skill_name!r} declares no operation")
    return operation


def _runtime_check(skill_name: str, operation: str, module) -> int:
    import importlib.metadata
    import json
    import platform

    if not callable(getattr(module, "run", None)) or not isinstance(
        getattr(module, "REQUEST", None), dict
    ):
        raise UnknownOperationError(
            f"operation module {operation!r} has no registered JSON data boundary"
        )
    import langgraph.graph as graph_api

    for name in ("END", "START", "StateGraph"):
        if not hasattr(graph_api, name):
            raise UnknownOperationError(
                f"installed LangGraph omits required public symbol: {name}"
            )
    print(
        json.dumps(
            {
                "langgraph": importlib.metadata.version("langgraph"),
                "operation": skill_name,
                "python": sys.executable,
                "python_version": platform.python_version(),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


def _terminated(signum, frame):
    # A developer's client ends a run it no longer wants with SIGTERM (a Pi tool abort, a
    # supervisor's stop). It takes the same path as Ctrl-C: the host cancels the running worker,
    # records the cancellation and prints the result envelope instead of dying mid-write.
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    # Installed framework bytes remain receipt-owned and exact. Operation imports must never add
    # ambient bytecode caches beside a skill/operation source.
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    import signal

    signal.signal(signal.SIGTERM, _terminated)
    arguments = list(sys.argv[1:] if argv is None else argv)
    package_root = FRAMEWORK_ROOT
    source = str(package_root / "src")
    # A pre-existing sys.path entry for src/ (for example from an inherited PYTHONPATH=src,
    # relative to a different cwd) must not be left ahead of this insert: scripts/ is also on
    # sys.path for a direct script invocation, and scripts/concorde.py would otherwise shadow
    # the concorde package for any entry that runs ahead of the one this line adds.
    if source in sys.path:
        sys.path.remove(source)
    sys.path.insert(0, source)
    import importlib

    from concorde.development.operation_host import invocation_failure, json_main
    from concorde.spec.contracts import load_operation_inventory
    from concorde.spec.typed_data import canonical

    runtime_check = len(arguments) == 2 and arguments[1] == "--runtime-check"
    valid_call = (
        bool(arguments)
        and arguments[0] in SKILL_NAMES
        and (len(arguments) == 1 or runtime_check)
    )
    if not valid_call:
        skill_name = arguments[0] if len(arguments) == 1 else None
        result = invocation_failure(
            skill_name,
            UnknownOperationError(
                f"usage: run-operation.py <{'|'.join(SKILL_NAMES)}> [--runtime-check] < invocation.json"
            ),
        )
        print(canonical(result))
        return 3
    skill_name = arguments[0]

    try:
        operation = _declared_operation(package_root, skill_name)
        external_name = "concorde-" + operation.replace("_", "-")
        if external_name != skill_name:
            raise UnknownOperationError(
                f"skill {skill_name!r} declares operation {operation!r}, expected {skill_name!r}"
            )
        inventory = load_operation_inventory()
        module = importlib.import_module(f"{inventory.__name__}.{operation}")
    except (UnknownOperationError, ImportError) as error:
        print(
            canonical(
                invocation_failure(
                    skill_name,
                    error
                    if isinstance(error, UnknownOperationError)
                    else UnknownOperationError(str(error)),
                )
            )
        )
        return 3

    if runtime_check:
        return _runtime_check(skill_name, operation, module)

    # json_main expects a bare invocation on stdin with no positional arguments; the skill
    # name (this launcher's own argument) has already been consumed and verified above.
    sys.argv = sys.argv[:1]
    return json_main(package_root, skill_name, runner=module.run)


if __name__ == "__main__":
    raise SystemExit(main())
