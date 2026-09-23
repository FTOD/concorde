#!/usr/bin/env python3
"""The launcher of Concorde's public capabilities.

``run-operation.py <capability>`` accepts exactly one public capability name of the Operation
catalog, reads one capability request on standard input and prints one result envelope. It imports
the catalog and hands admission what admission must not import itself: the capability
declarations, Operations' dispatcher, the local installation service and the verified session
selection as the run's session provenance. ``<capability> --runtime-check`` is the offline probe
the managed runtime provisioner runs: it loads the capability's declaration and confirms LangGraph
is importable, without touching stdin or launching an Agent. ``--native-context <step> ...`` runs
one native preparation or acceptance step of Agent execution.

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


def _runtime_check(operation_name: str) -> int:
    import importlib.metadata
    import platform

    from concorde.operations.catalog import operation

    if not isinstance(operation(operation_name).request, dict):
        raise UnknownOperationError(
            f"capability {operation_name!r} declares no request schema"
        )
    try:
        import langgraph.graph as graph_api
    except ImportError as error:
        raise MissingRuntimeError(
            f"installed runtime requires LangGraph for full-runtime health in {sys.executable}"
        ) from error

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
    # The declaration packages ``agents`` and ``operations`` live at the package root.
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    sys.path.insert(0, source)
    from concorde.harness.entry import invocation_failure, json_main
    from concorde.spec.typed_data import canonical

    try:
        from concorde.operations.catalog import PUBLIC_OPERATIONS, register_types
        from concorde.operations.dispatch import services

        # The one registration entry: every owner's typed values before anything is checked.
        register_types()
    except ValueError as error:
        # A refused catalog stops the launcher before any request is admitted.
        print(canonical(invocation_failure(None, error)))
        return 3
    from concorde.distribution.local_installation import LocalInstallationService

    admission_services = services(installation=LocalInstallationService())

    def select_session():
        # The verified session selection is this run's provenance; none is active without one.
        if not os.environ.get("CONCORDE_SESSION_SELECTION"):
            return None
        from concorde.distribution.session_selection import runtime_selection

        return runtime_selection(package_root)

    if arguments[:1] == ["--native-context"]:
        from concorde.harness.native_context import main as native_context_main

        return native_context_main(
            package_root,
            arguments[1:],
            services=admission_services,
            select_session=select_session,
        )

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

    if runtime_check:
        try:
            return _runtime_check(operation_name)
        except (UnknownOperationError, MissingRuntimeError, ImportError) as error:
            print(canonical(invocation_failure(operation_name, error)))
            return 3

    try:
        selection = select_session()
    except Exception as error:
        print(canonical(invocation_failure(operation_name, error)))
        return 3

    # json_main expects a bare invocation on stdin with no positional arguments; the capability
    # name (this launcher's own argument) has already been consumed and verified above.
    sys.argv = sys.argv[:1]
    return json_main(
        package_root,
        operation_name,
        services=admission_services,
        session_provenance=selection,
    )


if __name__ == "__main__":
    raise SystemExit(main())
