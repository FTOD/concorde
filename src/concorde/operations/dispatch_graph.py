"""Operation selection and stage dispatch are executable LangGraph transitions."""

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
    "issues": (
        "select_operation",
        "inspect",
        "report",
        "reopen",
        "prepare",
        "decide",
        "verify",
        "close",
        "ready",
        "finish",
    ),
    "plan": ("assess_context", "author_plan", "persist_plan"),
    "project": ("select_action", "configure", "propose", "apply"),
}

DISPATCH_NODES = (
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


def build_dispatch_graph(node_factory, *, operation=None):
    from langgraph.graph import END, START, StateGraph

    from ..harness.operation_graph import expose_stateless_subgraph
    from ..issues.graph import build_issue_graph
    from ..planning.plan_graph import build_plan_graph
    from ..spec.project_graph import build_project_graph
    from .target_graph import build_target_graph

    factories = {
        "plan": build_plan_graph,
        "project": build_project_graph,
        "issues": build_issue_graph,
        "prepare_target": build_target_graph,
    }
    graph = StateGraph(DispatchState)
    # A mutation admitted in the primary worktree is relayed into its host-created candidate
    # before any entry leaf; every operation kind can be admitted that way.
    leaves = (
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
    )
    entry = [
        "relay",
        "deliver",
        "project",
        "prepare_target",
    ]
    targeted = list(leaves[leaves.index("review") :])
    if operation in {"concorde-init", "concorde-configure", "concorde-deliver"}:
        entry, targeted = (
            ["relay", "deliver" if operation == "concorde-deliver" else "project"],
            [],
        )
    elif operation is not None:
        entry = ["relay", "prepare_target"]
        target = {
            "concorde-spec-review": "review",
            "concorde-code-review": "review",
            "concorde-issues": "issues",
            "concorde-plan": "plan",
            "concorde-tasks": "tasks",
            "concorde-implement": "implement",
            "concorde-validate": "validate",
        }.get(operation, "context_solve")
        targeted = [target] + ([] if target == "review" else ["describe_policy"])
    leaves = tuple(name for name in leaves if name in entry or name in targeted)
    children = {}
    for name in (
        "select_operation",
        *(["prepare_target"] if targeted else []),
        *leaves,
    ):
        if name in factories:
            children[name] = factories[name](
                lambda child, name=name: node_factory(name + "/" + child)
            )
            graph.add_node(name, children[name])
        else:
            graph.add_node(name, node_factory(name))
    graph.add_edge(START, "select_operation")
    graph.add_conditional_edges(
        "select_operation", lambda state: state["route"], [*entry, END]
    )
    if targeted:
        graph.add_conditional_edges(
            "prepare_target", lambda state: state["route"], [*targeted, END]
        )
    for name in leaves:
        graph.add_edge(name, END)
    compiled = graph.compile(name="dispatch_graph", checkpointer=False)
    for name, child in children.items():
        expose_stateless_subgraph(compiled, name, child)
    return compiled
