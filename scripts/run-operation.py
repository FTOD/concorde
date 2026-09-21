#!/usr/bin/env python3
"""Executable boundary for Concorde's public Operations (proposal section 6.3).

Only public Operations are directly invocable. This launcher accepts exactly one of the public Operation names,
maps it to its operation module through the `operation:` front-matter field of its operation guidance source
`prompts/operation-guidance/<name>.md`, and runs the shared trusted stdin/envelope handling
(`concorde.harness.entry.json_main`) through that module's own `run`. Stage
operations have no launcher and no direct invocation. `<operation-name> --runtime-check` is a
lightweight offline smoke check used by the managed runtime provisioner: it loads the operation
module and confirms LangGraph is importable, without touching stdin or launching an agent.

In an installed project the launcher runs inside the managed runtime the installer provisioned
beside the framework, whatever interpreter started it: the caller may start it with ambient
`python3`, which need not carry LangGraph, so the launcher re-executes itself with
`.concorde/.venv`'s interpreter first. The source checkout keeps the interpreter that started it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
# The installer's verified runtime leaves this owner marker (managed_runtime.MARKER_NAME).
MANAGED_RUNTIME_MARKER = ".concorde-runtime.json"

PUBLIC_OPERATIONS = (
    "concorde-context-solve",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-issues",
    "concorde-spec-review",
    "concorde-code-review",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
)


class UnknownOperationError(ValueError):
    code = "unknown_operation"


class MissingRuntimeError(ValueError):
    code = "missing_runtime"


def _managed_runtime_python(package_root: Path) -> Path | None:
    """The interpreter of an installed project's verified managed runtime, or None.

    The installer deploys the framework at ``<project>/.concorde/framework`` and provisions the
    locked runtime beside it at ``<project>/.concorde/.venv`` (the manifest's ``runtime.venv``),
    writing its owner marker there only after verification. The source checkout matches neither
    layout, and an unverified or foreign environment is never entered.
    """
    if package_root.name != "framework" or package_root.parent.name != ".concorde":
        return None
    venv = package_root.parent / ".venv"
    marker = venv / MANAGED_RUNTIME_MARKER
    if (
        venv.is_symlink()
        or not venv.is_dir()
        or marker.is_symlink()
        or not marker.is_file()
    ):
        return None
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if not isinstance(value, dict) or value.get("owner") != "concorde":
        return None
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return python if python.is_file() else None


def _enter_managed_runtime(arguments: list[str]) -> int | None:
    """Re-execute this launcher inside the managed runtime unless it already runs there."""
    python = _managed_runtime_python(FRAMEWORK_ROOT)
    if python is None or Path(sys.prefix).resolve() == python.parent.parent.resolve():
        return None
    argv = [str(python), str(Path(__file__).resolve()), *arguments]
    # execv does not replace the process on Windows; run the runtime's launcher as a child there.
    if os.name == "nt":  # pragma: no cover
        import subprocess

        return subprocess.call(argv)
    # pi-lens-ignore: S606
    os.execv(argv[0], argv)
    return None  # pragma: no cover - execv does not return


def _declared_operation(package_root: Path, operation_name: str) -> str:
    from concorde.spec.frontmatter import FrontMatterError, parse_document

    source = package_root / "prompts" / "operation-guidance" / f"{operation_name}.md"
    try:
        metadata, _ = parse_document(
            source.read_text(encoding="utf-8"), source.as_posix()
        )
    except (OSError, UnicodeError, FrontMatterError) as error:
        raise UnknownOperationError(
            f"cannot read operation guidance source for {operation_name!r}: {error}"
        ) from error
    operation = metadata.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        raise UnknownOperationError(
            f"guidance for {operation_name!r} declares no operation"
        )
    return operation


def _runtime_check(operation_name: str, operation: str, module) -> int:
    import importlib.metadata
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
                "operation": operation_name,
                # The interpreter and the environment it runs in: the provisioner checks that
                # the prefix is the managed runtime itself, not the interpreter that started it.
                "prefix": sys.prefix,
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
    # ambient bytecode caches beside a guidance/operation source.
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    arguments = list(sys.argv[1:] if argv is None else argv)
    exit_code = _enter_managed_runtime(arguments)
    if exit_code is not None:
        return exit_code
    import signal

    signal.signal(signal.SIGTERM, _terminated)
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

    if arguments[:1] == ["--native-context"]:
        from concorde.harness.native_context import main as native_context_main

        return native_context_main(package_root, arguments[1:])

    from concorde.harness.entry import invocation_failure, json_main, runtime_selection
    from concorde.spec.contracts import load_operation_inventory
    from concorde.spec.typed_data import canonical

    runtime_check = len(arguments) == 2 and arguments[1] == "--runtime-check"
    valid_call = (
        bool(arguments)
        and arguments[0] in PUBLIC_OPERATIONS
        and (len(arguments) == 1 or runtime_check)
    )
    if not valid_call:
        operation_name = arguments[0] if len(arguments) == 1 else None
        result = invocation_failure(
            operation_name,
            UnknownOperationError(
                f"usage: run-operation.py <{'|'.join(PUBLIC_OPERATIONS)}> [--runtime-check] < invocation.json"
            ),
        )
        print(canonical(result))
        return 3
    operation_name = arguments[0]

    try:
        runtime_selection(package_root)
    except Exception as error:
        print(canonical(invocation_failure(operation_name, error)))
        return 3

    try:
        operation = _declared_operation(package_root, operation_name)
        external_name = "concorde-" + operation.replace("_", "-")
        if external_name != operation_name:
            raise UnknownOperationError(
                f"guidance for {operation_name!r} declares operation {operation!r}, expected {operation_name!r}"
            )
        inventory = load_operation_inventory()
        module = importlib.import_module(f"{inventory.__name__}.{operation}")
    except (UnknownOperationError, ImportError) as error:
        print(
            canonical(
                invocation_failure(
                    operation_name,
                    error
                    if isinstance(error, UnknownOperationError)
                    else UnknownOperationError(str(error)),
                )
            )
        )
        return 3

    if runtime_check:
        return _runtime_check(operation_name, operation, module)

    # json_main expects a bare invocation on stdin with no positional arguments; the Operation
    # name (this launcher's own argument) has already been consumed and verified above.
    sys.argv = sys.argv[:1]
    return json_main(package_root, operation_name, runner=module.run)


if __name__ == "__main__":
    raise SystemExit(main())
