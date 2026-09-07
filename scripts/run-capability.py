#!/usr/bin/env python3
"""Executable boundary for Concorde's public skills (proposal section 6.3).

Only skills are directly invocable. This launcher accepts exactly one of the seven skill names,
maps it to its capability module through the `capability:` front-matter field of
`skills/<name>/SKILL.md`, and runs the shared trusted stdin/envelope handling
(`concorde.host.capability_host.json_main`) through that module's own `run`. Stage
capabilities have no launcher and no direct invocation. `<skill-name> --runtime-check` is a
lightweight offline smoke check used by the managed runtime provisioner: it loads the capability
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
    "concorde-reflections-triage",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
)


class UnknownCapabilityError(ValueError):
    code = "unknown_capability"


def _declared_capability(package_root: Path, skill_name: str) -> str:
    from concorde.frontmatter import FrontMatterError, parse_document

    source = package_root / "skills" / skill_name / "SKILL.md"
    try:
        metadata, _ = parse_document(source.read_text(encoding="utf-8"), source.as_posix())
    except (OSError, UnicodeError, FrontMatterError) as error:
        raise UnknownCapabilityError(f"cannot read skill source for {skill_name!r}: {error}") from error
    capability = metadata.get("capability")
    if not isinstance(capability, str) or not capability.strip():
        raise UnknownCapabilityError(f"skill {skill_name!r} declares no capability")
    return capability


def _runtime_check(skill_name: str, capability: str, module) -> int:
    import importlib.metadata
    import json
    import platform

    if not callable(getattr(module, "run", None)) or not isinstance(getattr(module, "REQUEST", None), dict):
        raise UnknownCapabilityError(f"capability module {capability!r} has no registered JSON data boundary")
    import langgraph.graph as graph_api
    for name in ("END", "START", "StateGraph"):
        if not hasattr(graph_api, name):
            raise UnknownCapabilityError(f"installed LangGraph omits required public symbol: {name}")
    print(json.dumps({
        "langgraph": importlib.metadata.version("langgraph"),
        "capability": skill_name,
        "python": sys.executable,
        "python_version": platform.python_version(),
        "status": "ok",
    }, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    # Installed framework bytes remain receipt-owned and exact. Capability imports must never add
    # ambient bytecode caches beside a skill/capability source.
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
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

    from concorde.host.capability_host import invocation_failure, json_main
    from concorde.host.typed_data import canonical
    from concorde.host.contracts import load_capability_inventory

    runtime_check = len(arguments) == 2 and arguments[1] == "--runtime-check"
    valid_call = bool(arguments) and arguments[0] in SKILL_NAMES and (len(arguments) == 1 or runtime_check)
    if not valid_call:
        skill_name = arguments[0] if len(arguments) == 1 else None
        result = invocation_failure(skill_name, UnknownCapabilityError(
            f"usage: run-capability.py <{'|'.join(SKILL_NAMES)}> [--runtime-check] < invocation.json"))
        print(canonical(result))
        return 3
    skill_name = arguments[0]

    try:
        capability = _declared_capability(package_root, skill_name)
        external_name = "concorde-" + capability.replace("_", "-")
        if external_name != skill_name:
            raise UnknownCapabilityError(
                f"skill {skill_name!r} declares capability {capability!r}, expected {skill_name!r}")
        inventory = load_capability_inventory()
        module = importlib.import_module(f"{inventory.__name__}.{capability}")
    except (UnknownCapabilityError, ImportError) as error:
        print(canonical(invocation_failure(skill_name, error if isinstance(error, UnknownCapabilityError)
                                           else UnknownCapabilityError(str(error)))))
        return 3

    if runtime_check:
        return _runtime_check(skill_name, capability, module)

    # json_main expects a bare invocation on stdin with no positional arguments; the skill
    # name (this launcher's own argument) has already been consumed and verified above.
    sys.argv = sys.argv[:1]
    return json_main(package_root, skill_name, runner=module.run)


if __name__ == "__main__":
    raise SystemExit(main())
