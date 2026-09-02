#!/usr/bin/env python3
"""Conditional permission-bounded reflection triage LangGraph Operation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OPERATION_NAME = "concorde-reflections-triage"
OPERATION_CAPABILITIES = (
    "concorde-analyze",
    "concorde-fast-loop",
    "concorde-plan",
    "concorde-tasks",
    "concorde-implement",
    "concorde-validate",
)
OPERATION_STAGES = (
    ("investigate", ("concorde-analyze",)),
    ("route", ("concorde-fast-loop", "concorde-plan")),
    ("implement", ("concorde-tasks", "concorde-implement")),
    ("validate", ("concorde-validate",)),
)
OPERATION_BINDINGS = (
    ("investigate", 0, "concorde-analyze", "reflection-investigator", None, (), False, "none"),
    (
        "route",
        0,
        "concorde-fast-loop",
        "fast-loop-implementer",
        ("reflection-worktrees", "reflections"),
        ("reflection-worktrees", "reflections"),
        False,
        "none",
    ),
    ("route", 1, "concorde-plan", "planner"),
    ("implement", 0, "concorde-tasks", "task-author"),
    (
        "implement",
        1,
        "concorde-implement",
        "worktree-implementer",
        ("reflection-worktrees", "reflections"),
        ("reflection-worktrees", "reflections"),
        False,
        "none",
    ),
    ("validate", 0, "concorde-validate", "validator"),
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
        resolve_permission_runtime_context,
    )

    return (
        OperationExecution,
        build_operation,
        permission_launch_factory,
        resolve_permission_runtime_context,
    )


@dataclass(frozen=True)
class _ConditionalGraph:
    graph: Any | None
    action: str
    route: str | None

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        if state.get("capability_results"):
            raise ValueError("Operation input must start with no capability results")
        if self.graph is None:
            return {
                "request": state.get("request", self.action),
                "capability_results": [],
                "action": self.action,
                "route": self.route,
            }
        result = dict(self.graph.invoke(state))
        result["action"] = self.action
        result["route"] = self.route
        return result


def _selected_topology(
    action: str,
    route: str | None,
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], tuple[tuple[Any, ...], ...]]:
    if action == "status":
        if route is not None:
            raise ValueError("status action does not accept a route")
        return (), ()
    if action == "investigate":
        if route is not None:
            raise ValueError("investigate action does not accept a route")
        return (
            (("investigate", ("concorde-analyze",)),),
            (("investigate", 0, "concorde-analyze", "reflection-investigator", None, (), False, "none"),),
        )
    if action == "implement":
        if route not in {"fast-loop", "plan"}:
            raise ValueError("implement action requires route 'fast-loop' or 'plan'")
        if route == "fast-loop":
            return (
                (
                    ("investigate", ("concorde-analyze",)),
                    ("route", ("concorde-fast-loop",)),
                    ("validate", ("concorde-validate",)),
                ),
                (
                    ("investigate", 0, "concorde-analyze", "reflection-investigator", None, (), False, "none"),
                    (
                        "route",
                        0,
                        "concorde-fast-loop",
                        "fast-loop-implementer",
                        ("reflection-worktrees", "reflections"),
                        ("reflection-worktrees", "reflections"),
                        False,
                        "none",
                    ),
                    ("validate", 0, "concorde-validate", "validator"),
                ),
            )
        return (
            (
                ("investigate", ("concorde-analyze",)),
                ("route", ("concorde-plan",)),
                ("implement", ("concorde-tasks", "concorde-implement")),
                ("validate", ("concorde-validate",)),
            ),
            (
                ("investigate", 0, "concorde-analyze", "reflection-investigator", None, (), False, "none"),
                ("route", 0, "concorde-plan", "planner"),
                ("implement", 0, "concorde-tasks", "task-author"),
                (
                    "implement",
                    1,
                    "concorde-implement",
                    "worktree-implementer",
                    ("reflection-worktrees", "reflections"),
                    ("reflection-worktrees", "reflections"),
                    False,
                    "none",
                ),
                ("validate", 0, "concorde-validate", "validator"),
            ),
        )
    if action == "merge":
        if route is not None:
            raise ValueError("merge action does not accept a route")
        return (
            (("validate", ("concorde-validate",)),),
            (("validate", 0, "concorde-validate", "validator"),),
        )
    raise ValueError(f"unsupported reflection action: {action!r}")


def build_reflections_triage(
    executor,
    *,
    action: str,
    route: str | None = None,
    project_root: str | Path | None = None,
    feature_path: str | None = None,
    integration: str = "codex",
    native_enforcement: bool = True,
    outer_sandbox: str | None = None,
    framework_prefix: str = "",
    permission_context: Any | None = None,
    nested_dispatcher=None,
) -> Any:
    """Compile only the model capabilities reachable for the explicit action and route."""

    definition, bindings = _selected_topology(action, route)
    if not definition:
        return _ConditionalGraph(None, action, route)
    _, build_operation, launch_factory, resolve_context = _runtime()
    context = permission_context or resolve_context(project_root or package_root(), feature_path)
    graph = build_operation(
        package_root(),
        OPERATION_NAME,
        definition,
        bindings,
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
    return _ConditionalGraph(graph, action, route)


def _parse_request(value: str) -> tuple[str, str | None]:
    parts = value.split()
    action = parts[0] if parts else "status"
    route = parts[1] if action == "implement" and len(parts) > 1 else None
    return action, route


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
    """Invoke the paired planner so its internal leaves enforce independently."""

    path = package_root() / "operations/concorde-plan/operation.py"
    specification = importlib.util.spec_from_file_location("concorde_triage_nested_plan", path)
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
    parser.add_argument("request", nargs="?", default="status")
    parser.add_argument("--route", choices=("fast-loop", "plan"))
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
    action, inferred_route = _parse_request(arguments.request)
    route = arguments.route or inferred_route
    visits: list[dict[str, object]] = []
    OperationExecution, _, _, _ = _runtime()
    if arguments.execute:
        from concorde.operation_executor import AgentProcessExecutor

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
    try:
        nested_dispatcher = executor
        if arguments.execute and action == "implement" and route == "plan":
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
        graph = build_reflections_triage(
            executor,
            action=action,
            route=route,
            project_root=Path.cwd(),
            feature_path=arguments.feature_path,
            integration=arguments.integration,
            native_enforcement=not arguments.no_native_enforcement,
            outer_sandbox=arguments.outer_sandbox,
            framework_prefix=arguments.framework_prefix,
            nested_dispatcher=nested_dispatcher,
        )
    except ValueError as error:
        parser.error(str(error))
    result = graph.invoke({"request": arguments.request, "capability_results": []})
    print(
        json.dumps(
            {
                "operation": OPERATION_NAME,
                "request": arguments.request,
                "action": action,
                "route": route,
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
