#!/usr/bin/env python3
"""Concorde's permission-bounded specify → plan → tasks → deliver Operation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
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


def _dispatch_plan(
    invocation,
    leaf_executor,
    *,
    project_root: str | Path,
    feature_path: str | None,
    integration: str,
    native_enforcement: bool,
    outer_sandbox: str | None,
    framework_prefix: str,
) -> str:
    """Invoke the trusted paired planner so its inner leaves enforce independently."""

    path = package_root() / "operations/concorde-plan/operation.py"
    specification = importlib.util.spec_from_file_location("concorde_nested_plan", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load paired concorde-plan Operation")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    graph = module.build_plan_operation(
        leaf_executor,
        project_root=project_root,
        feature_path=feature_path,
        integration=integration,
        native_enforcement=native_enforcement,
        outer_sandbox=outer_sandbox,
        framework_prefix=framework_prefix,
    )
    result = graph.invoke({"request": invocation.request, "capability_results": []})
    return json.dumps(
        [asdict(item) for item in result["capability_results"]],
        sort_keys=True,
        default=str,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="Development request carried through the Operation.")
    parser.add_argument("--framework-prefix", default="")
    parser.add_argument("--feature-path")
    parser.add_argument("--integration", choices=("codex", "claude"), default="codex")
    parser.add_argument("--describe-policy", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-primary-worktree", action="store_true")
    parser.add_argument("--no-native-enforcement", action="store_true")
    parser.add_argument("--outer-sandbox")
    arguments = parser.parse_args()
    if arguments.describe_policy and arguments.execute:
        parser.error("--describe-policy and --execute are mutually exclusive")
    visits: list[dict[str, object]] = []
    OperationExecution, _, _, _ = _runtime()

    if arguments.execute:
        from concorde.capabilities.worktree import (
            WorktreeBoundaryError,
            require_isolated_worktree,
        )

        try:
            require_isolated_worktree(
                Path.cwd(),
                allow_primary_worktree=arguments.allow_primary_worktree,
            )
        except WorktreeBoundaryError as error:
            parser.error(str(error))

    if arguments.execute:
        from concorde.capabilities.operation_executor import AgentProcessExecutor

        process = AgentProcessExecutor()

        def execute(invocation: OperationExecution):
            if invocation.launch_specification is None:
                raise RuntimeError(
                    f"nested Operation {invocation.capability.name} requires a dispatcher"
                )
            return process(invocation.launch_specification)

        executor = execute
    else:
        def describe(invocation: OperationExecution) -> str:
            specification = invocation.launch_specification
            item: dict[str, object] = {
                "stage": invocation.stage,
                "occurrence": invocation.occurrence,
                "capability": invocation.capability.name,
                "kind": invocation.capability.kind,
                "prior_capabilities": [item.capability for item in invocation.prior_results],
            }
            if specification is not None:
                item["policy"] = asdict(specification.policy)
                item["native_configuration"] = asdict(specification.native_configuration)
                item["launch_digest"] = specification.digest
            visits.append(item)
            return f"prepared:{invocation.capability.name}"

        executor = describe

    nested_dispatcher = executor
    if arguments.execute:
        nested_dispatcher = lambda invocation: _dispatch_plan(
            invocation,
            executor,
            project_root=Path.cwd(),
            feature_path=arguments.feature_path,
            integration=arguments.integration,
            native_enforcement=not arguments.no_native_enforcement,
            outer_sandbox=arguments.outer_sandbox,
            framework_prefix=arguments.framework_prefix,
        )
    graph = build_standard_dev_loop(
        executor,
        project_root=Path.cwd(),
        feature_path=arguments.feature_path,
        integration=arguments.integration,
        native_enforcement=not arguments.no_native_enforcement,
        outer_sandbox=arguments.outer_sandbox,
        framework_prefix=arguments.framework_prefix,
        nested_dispatcher=nested_dispatcher,
    )
    result = graph.invoke({"request": arguments.request, "capability_results": []})
    print(
        json.dumps(
            {
                "operation": OPERATION_NAME,
                "request": arguments.request,
                "mode": "execute" if arguments.execute else "describe-policy",
                "capabilities": visits,
                "results": [asdict(item) for item in result["capability_results"]],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
