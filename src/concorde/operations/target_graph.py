"""Target admission composes the discovery instance that Studio expands."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..query_routing.discovery_graph import build_discovery_graph


class TargetState(TypedDict, total=False):
    occurrence: int
    routes: list[dict]
    decision: dict | None
    route: str
    result: dict
    output: dict


def build_target_graph(node_factory, *, discover=True):
    from ..harness.operation_graph import expose_stateless_subgraph

    graph = StateGraph(TargetState)
    graph.add_node("initialize_target", node_factory("initialize_target"))
    graph.add_node("bind_target", node_factory("bind_target"))
    graph.add_edge(START, "initialize_target")
    choices = ["bind_target", END]
    discovery = None
    if discover:
        discovery = build_discovery_graph(node_factory)
        graph.add_node("discover", discovery)
        choices.append("discover")
        graph.add_conditional_edges(
            "discover",
            lambda state: END if state.get("result") else "bind_target",
            [END, "bind_target"],
        )
    graph.add_conditional_edges(
        "initialize_target", lambda state: state["route"], choices
    )
    graph.add_edge("bind_target", END)
    compiled = graph.compile(name="target_graph", checkpointer=False)
    if discovery is not None:
        expose_stateless_subgraph(compiled, "discover", discovery)
    return compiled
