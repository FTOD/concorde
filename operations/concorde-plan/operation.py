#!/usr/bin/env python3
"""Permission-bounded context → author planning LangGraph Operation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


OPERATION_NAME = "concorde-plan"
OPERATION_CAPABILITIES = (
    "concorde-plan-context",
    "concorde-plan-author",
)
OPERATION_STAGES = (
    ("context", ("concorde-plan-context",)),
    ("author", ("concorde-plan-author",)),
)
OPERATION_BINDINGS = (
    ("context", 0, "concorde-plan-context", "planning-context"),
    ("author", 0, "concorde-plan-author", "plan-author"),
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
    )
    from concorde.understanding.planning_context import resolve_planning_context

    return OperationExecution, build_operation, permission_launch_factory, resolve_planning_context


def build_plan_operation(
    executor,
    *,
    project_root: str | Path,
    feature_path: str | None = None,
    integration: str = "codex",
    native_enforcement: bool = True,
    outer_sandbox: str | None = None,
    framework_prefix: str = "",
    permission_context: Any | None = None,
) -> Any:
    """Compile the exact bounded context→author graph for an injected leaf executor."""

    _, build_operation, launch_factory, resolve_context = _runtime()
    context = permission_context or resolve_context(project_root, feature_path)
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
