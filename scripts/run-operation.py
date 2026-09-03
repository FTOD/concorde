#!/usr/bin/env python3
"""Run one paired Concorde Operation with its project-local managed interpreter."""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path


class LauncherError(RuntimeError):
    """The managed Operation runtime cannot be selected safely."""


def framework_root() -> Path:
    return Path(__file__).absolute().parent.parent


def managed_venv(root: Path) -> Path:
    if root.parent.name == ".concorde":
        return root.parent / ".venv"
    return root / ".venv"


def managed_python(venv: Path) -> Path:
    relative = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
    python = venv / relative
    if python.is_symlink() and not python.exists():
        raise LauncherError(f"managed Concorde interpreter is a broken symlink: {python}")
    if not python.is_file():
        raise LauncherError(
            f"managed Concorde interpreter is missing at {python}; "
            f"install or repair the Concorde runtime at {venv}"
        )
    return python


def checked_operation(root: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_symlink() or not candidate.is_file():
        raise LauncherError(f"Operation must be one real file: {value}")
    operation = candidate.resolve()
    operations = (root / "operations").resolve()
    try:
        relative = operation.relative_to(operations)
    except ValueError as error:
        raise LauncherError(
            f"Operation must resolve below the colocated {operations} directory: {value}"
        ) from error
    if relative.name != "operation.py" or len(relative.parts) != 2:
        raise LauncherError(
            f"Operation must be an exact operations/<name>/operation.py pair: {value}"
        )
    return operation


def _runtime_check(operation: Path, venv: Path, python: Path) -> int:
    specification = importlib.util.spec_from_file_location(
        f"concorde_runtime_check_{operation.parent.name.replace('-', '_')}",
        operation,
    )
    if specification is None or specification.loader is None:
        raise LauncherError(f"cannot load paired Operation: {operation}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    runtime = getattr(module, "_runtime", None)
    if not callable(runtime):
        raise LauncherError(f"paired Operation has no runtime loader: {operation}")
    runtime()
    graph_api = importlib.import_module("langgraph.graph")
    for name in ("END", "START", "StateGraph"):
        if not hasattr(graph_api, name):
            raise LauncherError(f"installed LangGraph omits required public symbol: {name}")

    print(
        json.dumps(
            {
                "langgraph": importlib.metadata.version("langgraph"),
                "operation": str(getattr(module, "OPERATION_NAME", operation.parent.name)),
                "python": str(python),
                "python_version": platform.python_version(),
                "status": "ok",
                "venv": str(venv),
            },
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    # Installed framework bytes remain receipt-owned and exact. Operation imports must never add
    # ambient bytecode caches beside a paired SKILL.md/operation.py source.
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        raise LauncherError("usage: run-operation.py <operations/name/operation.py> [arguments]")
    root = framework_root()
    operation = checked_operation(root, arguments.pop(0))
    venv = managed_venv(root).absolute()
    python = managed_python(venv).absolute()
    bootstrapped = os.environ.get("CONCORDE_MANAGED_VENV")
    if bootstrapped != str(venv):
        environment = os.environ.copy()
        environment["CONCORDE_MANAGED_VENV"] = str(venv)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        os.execve(
            python,
            [str(python), str(Path(__file__).absolute()), str(operation), *arguments],
            environment,
        )
    if Path(sys.prefix).absolute() != venv:
        raise LauncherError(
            f"managed interpreter prefix mismatch: expected {venv}, observed {sys.prefix}"
        )
    if arguments == ["--runtime-check"]:
        return _runtime_check(operation, venv, python)
    os.execv(python, [str(python), str(operation), *arguments])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LauncherError, ModuleNotFoundError, OSError) as error:
        print(f"CONCORDE OPERATION FAILED: {error}", file=sys.stderr)
        raise SystemExit(3)
