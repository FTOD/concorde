#!/usr/bin/env python3
"""Concorde's permission-bounded specify → plan → tasks → deliver Operation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


OPERATION_NAME = "concorde-standard-dev-loop"
OPERATION_CAPABILITIES = (
    "concorde-specify",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-validate",
    "concorde-deliver",
)
OPERATION_STAGES = (
    ("specify", ("concorde-specify",)),
    ("plan", ("concorde-plan",)),
    ("tasks", ("concorde-tasks", "concorde-implement")),
    ("deliver", ("concorde-validate", "concorde-deliver")),
)
OPERATION_BINDINGS = (
    ("specify", 0, "concorde-specify", "specifier"),
    ("plan", 0, "concorde-plan", "planner"),
    ("tasks", 0, "concorde-tasks", "task-author"),
    ("tasks", 1, "concorde-implement", "implementer"),
    ("deliver", 0, "concorde-validate", "validator"),
    ("deliver", 1, "concorde-deliver", "deliverer"),
)


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime():
    root = package_root()
    source = str(root / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from concorde.capabilities.operation_runtime import (
        OperationExecution,
        build_operation,
        permission_launch_factory,
        resolve_permission_runtime_context,
    )

    return (
        OperationExecution,
        build_operation,
        permission_launch_factory,
        resolve_permission_runtime_context,
    )


def build_standard_dev_loop(
    executor,
    *,
    project_root: str | Path | None = None,
    feature_path: str | None = None,
    integration: str = "codex",
    native_enforcement: bool = True,
    outer_sandbox: str | None = None,
    framework_prefix: str = "",
    permission_context: Any | None = None,
    nested_dispatcher=None,
) -> Any:
    """Compile the standard Operation with one concrete launch policy per direct leaf."""

    _, build_operation, launch_factory, resolve_context = _runtime()
    context = permission_context or resolve_context(project_root or package_root(), feature_path)
    return build_operation(
        package_root(),
        OPERATION_NAME,
        OPERATION_STAGES,
        OPERATION_BINDINGS,
        executor,
        framework_prefix=framework_prefix,
        launch_factory=launch_factory(
            context,
            integration,
            native_enforcement=native_enforcement,
            outer_sandbox=outer_sandbox,
        ),
        nested_dispatcher=nested_dispatcher,
    )


def run(configuration: dict, runtime_input: dict, *, host_context):
    """Execute this registered Operation with separate structured configuration and task data."""
    _runtime()
    from concorde.capabilities.operation_service import run_operation

    return run_operation(OPERATION_NAME, configuration, runtime_input, host_context=host_context)


def main() -> int:
    _runtime()
    from concorde.capabilities.operation_service import operation_main

    return operation_main(OPERATION_NAME, package_root())


if __name__ == "__main__":
    raise SystemExit(main())
