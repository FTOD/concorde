"""The operation admission/dispatch/result Graph used by both local calls and Studio.

The live session is private, trusted Python runtime context. This Graph is deliberately stateless with
respect to checkpointing; public callers checkpoint only the JSON input and final envelope.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# Domain-specific counters govern discovery, work items and repair. Leave room for nested
# scheduling rather than applying LangGraph's small default to an otherwise admitted request.
OPERATION_RECURSION_LIMIT = 100000


class OperationGraphState(TypedDict, total=False):
    result: dict
    policies: list[dict]
    events: list[dict]
    invocation: dict
    expected_workspace: dict | None


def build_operation_graph(
    node_factory,
    *,
    name="operation_graph",
    input_schema=None,
    output_schema=None,
    context_schema=None,
):
    from .dispatch_graph import build_dispatch_graph

    graph = StateGraph(
        OperationGraphState,
        input_schema=input_schema,
        output_schema=output_schema,
        context_schema=context_schema,
    )
    for node in (
        "initialize",
        "admit_request",
        "bind_workspace",
        "check_configuration",
        "finalize",
    ):
        graph.add_node(node, node_factory(node))
    dispatch = build_dispatch_graph(
        lambda node: node_factory("dispatch/" + node),
        operation=name if name.startswith("concorde-") else None,
    )
    graph.add_node("execute", dispatch)
    graph.add_edge(START, "initialize")
    for node, successor in (
        ("initialize", "admit_request"),
        ("admit_request", "bind_workspace"),
        ("bind_workspace", "check_configuration"),
        ("check_configuration", "execute"),
    ):
        graph.add_conditional_edges(
            node,
            lambda state, *, next_node=successor: (
                "finalize" if state.get("result") is not None else next_node
            ),
            ["finalize", successor],
        )
    graph.add_edge("execute", "finalize")
    graph.add_edge("finalize", END)
    compiled = graph.compile(name=name, checkpointer=False)
    expose_stateless_subgraph(compiled, "execute", dispatch)
    return compiled


def expose_stateless_subgraph(parent, node: str, child):
    """Register the actual child for LangGraph's Studio/xray topology discovery.

    LangGraph's automatic discovery omits children with checkpointer=False. They still execute
    as subgraphs; explicitly exposing that same instance keeps inspection accurate without
    serializing trusted host objects or suggesting that internal checkpoints can be resumed.
    """
    if child.checkpointer is not False:
        raise ValueError("only stateless host subgraphs may use this adapter")
    parent.nodes[node].subgraphs = [child]
