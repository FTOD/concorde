#!/usr/bin/env python3
"""Permission-bounded context → author planning LangGraph Operation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
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
    from concorde.operation_runtime import (
        OperationExecution,
        build_operation,
        permission_launch_factory,
    )
    from concorde.planning_context import resolve_planning_context

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="Planning request carried from context to author.")
    parser.add_argument("--framework-prefix", default="")
    parser.add_argument("--feature-path")
    parser.add_argument("--integration", choices=("codex", "claude"), default="codex")
    parser.add_argument("--describe-policy", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--no-native-enforcement", action="store_true")
    parser.add_argument("--outer-sandbox")
    arguments = parser.parse_args()
    if arguments.describe_policy and arguments.execute:
        parser.error("--describe-policy and --execute are mutually exclusive")
    visits: list[dict[str, object]] = []
    OperationExecution, _, _, _ = _runtime()

    if arguments.execute:
        from concorde.operation_executor import AgentProcessExecutor

        process = AgentProcessExecutor()

        def execute(invocation: OperationExecution):
            if invocation.launch_specification is None:
                raise RuntimeError("planner leaf has no enforcement launch specification")
            return process(invocation.launch_specification)

        executor = execute
    else:
        def describe(invocation: OperationExecution) -> str:
            specification = invocation.launch_specification
            if specification is None:
                raise RuntimeError("planner leaf has no enforcement launch specification")
            visits.append(
                {
                    "stage": invocation.stage,
                    "occurrence": invocation.occurrence,
                    "capability": invocation.capability.name,
                    "kind": invocation.capability.kind,
                    "prior_capabilities": [item.capability for item in invocation.prior_results],
                    "policy": asdict(specification.policy),
                    "native_configuration": asdict(specification.native_configuration),
                    "launch_digest": specification.digest,
                }
            )
            return f"prepared:{invocation.capability.name}"

        executor = describe

    graph = build_plan_operation(
        executor,
        project_root=Path.cwd(),
        feature_path=arguments.feature_path,
        integration=arguments.integration,
        native_enforcement=not arguments.no_native_enforcement,
        outer_sandbox=arguments.outer_sandbox,
        framework_prefix=arguments.framework_prefix,
    )
    result = graph.invoke({"request": arguments.request, "capability_results": []})
    print(
        json.dumps(
            {
                "operation": OPERATION_NAME,
                "request": arguments.request,
                "mode": "execute" if arguments.execute else "describe-policy",
                "stages": ["context", "author"],
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
