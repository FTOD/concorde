"""Compatibility-named finite capability dispatch table; no graph execution."""

from typing import TypedDict


class DispatchState(TypedDict, total=False):
    route: str
    output: dict
    # The complete result envelope a candidate worktree's launcher returned for a mutation
    # admitted in the primary worktree; the operation Graph adopts it as its own result.
    relayed: dict
    result: dict


SUBGRAPH_NODES = {
    "prepare_target": ("bind_target",),
    "issues": ("select_operation", "inspect", "report", "reopen"),
    "project": ("select_action", "configure", "propose", "apply"),
}

DISPATCH_NODES = (
    "native_issue",
    "select_operation",
    "relay",
    "deliver",
    "project",
    "review",
    "describe_policy",
    "issues",
    "plan",
    "tasks",
    "implement",
    "validate",
    "context_solve",
    *(name + "/" + node for name, nodes in SUBGRAPH_NODES.items() for node in nodes),
)
