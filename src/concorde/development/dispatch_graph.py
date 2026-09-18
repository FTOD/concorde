"""Operation selection and stage dispatch are executable LangGraph transitions."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..spec.contracts import DISCOVERY_OPERATIONS, MAIN_OPERATION

# Target admission composes a discovery child for every discovering operation except main, which
# discovers through its own query nodes and never enters target admission.
TARGET_DISCOVERY_OPERATIONS = frozenset(DISCOVERY_OPERATIONS - {MAIN_OPERATION})


class DispatchState(TypedDict, total=False):
    route: str
    output: dict
    # The complete result envelope a candidate worktree's launcher returned for a mutation
    # admitted in the primary worktree; the operation Graph adopts it as its own result.
    relayed: dict
    result: dict


SUBGRAPH_NODES = {
    "prepare_target": (
        "initialize_target",
        "decide",
        "expand_context",
        "bind_routes",
        "finish",
        "bind_target",
    ),
    "answer": ("decide", "expand_context", "bind_routes", "finish", "respond"),
    "design_topology": ("decide", "expand_context", "bind_routes", "finish", "respond"),
    "prepare_topology": (
        "prepare_authors",
        "author_module",
        "validate_candidate",
        "review_contexts",
        "persist_application",
    ),
    "apply_topology": (
        "admit_application",
        "validate_application",
        "apply_atomically",
        "cleanup",
    ),
    "issues": (
        "select_operation",
        "inspect",
        "report",
        "reopen",
        "prepare",
        "decide",
        "develop",
        "repair_spec",
        "verify",
        "close",
        "ready",
        "finish",
    ),
    "plan": ("assess_context", "author_plan", "persist_plan"),
    "project": ("select_action", "configure", "propose", "apply"),
    "specify_loop": ("initialize", "specify", "review_spec", "summarize"),
    "development_loop": (
        "initialize",
        "specify_loop",
        "plan",
        "tasks",
        "implement",
        "validate",
        "review_code",
        "ready",
        "summarize",
    ),
}

DISPATCH_NODES = (
    "select_operation",
    "relay",
    "deliver",
    "project",
    "answer",
    "design_topology",
    "prepare_topology",
    "apply_topology",
    "review",
    "describe_policy",
    "issues",
    "specify",
    "plan",
    "tasks",
    "implement",
    "validate",
    "development_loop",
    "specify_loop",
    "context_solve",
    *(name + "/" + node for name, nodes in SUBGRAPH_NODES.items() for node in nodes),
)


def build_dispatch_graph(node_factory, *, operation=None):
    from ..issues.graph import build_issue_graph
    from .loop_graph import build_loop_graph
    from .operation_graph import expose_stateless_subgraph
    from .plan_graph import build_plan_graph
    from .project_graph import build_project_graph
    from .query_graph import build_query_graph
    from .specify_graph import build_specify_graph
    from .target_graph import build_target_graph
    from .topology_graph import build_topology_apply_graph, build_topology_graph

    factories = {
        "answer": build_query_graph,
        "design_topology": build_query_graph,
        "prepare_topology": build_topology_graph,
        "apply_topology": build_topology_apply_graph,
        "plan": build_plan_graph,
        "project": build_project_graph,
        "issues": build_issue_graph,
        "development_loop": lambda nodes: build_loop_graph(nodes, dynamic=True),
        "specify_loop": build_specify_graph,
        "prepare_target": lambda nodes: build_target_graph(
            nodes,
            discover=operation is None or operation in TARGET_DISCOVERY_OPERATIONS,
        ),
    }
    graph = StateGraph(DispatchState)
    # A mutation admitted in the primary worktree is relayed into its host-created candidate
    # before any entry leaf; every operation kind can be admitted that way.
    leaves = (
        "relay",
        "deliver",
        "project",
        "answer",
        "design_topology",
        "prepare_topology",
        "apply_topology",
        "review",
        "describe_policy",
        "issues",
        "specify",
        "plan",
        "tasks",
        "implement",
        "validate",
        "development_loop",
        "specify_loop",
        "context_solve",
    )
    entry = [
        "relay",
        "deliver",
        "project",
        "answer",
        "design_topology",
        "prepare_topology",
        "apply_topology",
        "prepare_target",
    ]
    targeted = list(leaves[leaves.index("review") :])
    if operation == "concorde-main":
        entry, targeted = (
            ["relay", "answer", "design_topology", "prepare_topology", "apply_topology"],
            [],
        )
    elif operation in {"concorde-init", "concorde-configure", "concorde-deliver"}:
        entry, targeted = (
            ["relay", "deliver" if operation == "concorde-deliver" else "project"],
            [],
        )
    elif operation is not None:
        entry = ["relay", "prepare_target"]
        target = {
            "concorde-review": "review",
            "concorde-issues": "issues",
            "concorde-specify": "specify",
            "concorde-plan": "plan",
            "concorde-tasks": "tasks",
            "concorde-implement": "implement",
            "concorde-validate": "validate",
            "concorde-dev-loop": "development_loop",
            "concorde-specify-loop": "specify_loop",
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
