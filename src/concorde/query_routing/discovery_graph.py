"""Executable, bounded Module discovery Graph; inspection never starts an WorkerProfile."""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class DiscoveryState(TypedDict, total=False):
    result: dict
    occurrence: int
    decision: dict[str, Any]
    routes: list[dict[str, Any]]
    route: str


def build_discovery_graph(node_factory):
    graph = StateGraph(DiscoveryState)
    for name in ("decide", "expand_context", "bind_routes", "finish"):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "decide")
    graph.add_conditional_edges(
        "decide",
        lambda state: state["route"],
        ["expand_context", "bind_routes", "finish", END],
    )
    graph.add_conditional_edges(
        "expand_context",
        lambda state: END if state.get("result") else "decide",
        [END, "decide"],
    )
    graph.add_edge("bind_routes", END)
    graph.add_edge("finish", END)
    return graph.compile(name="discovery_graph", checkpointer=False)
