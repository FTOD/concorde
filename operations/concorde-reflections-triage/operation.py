#!/usr/bin/env python3
"""Conditional permission-bounded reflection triage LangGraph Operation."""

from __future__ import annotations

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
        None,
        ("selected-feature", "module-architecture", "owned-implementation", "task-authorized", "reflections", "generated-projections"),
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
        None,
        ("task-authorized", "attempt", "reflections", "generated-projections"),
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
    if action == "close":
        if route is not None:
            raise ValueError("close action does not accept a route")
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
                        None,
                        ("selected-feature", "module-architecture", "owned-implementation", "task-authorized", "reflections", "generated-projections"),
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
                    None,
                    ("task-authorized", "attempt", "reflections", "generated-projections"),
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
