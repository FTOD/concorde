"""Route names of capability dispatch: the steps admission may dispatch a request to.

``DISPATCH_NODES`` names every dispatch step; ``SUBGRAPH_NODES`` names the child steps of the
routes that run several. These are plain names looked up in dictionaries, not LangGraph nodes.
"""

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
