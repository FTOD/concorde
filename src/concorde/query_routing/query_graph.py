"""Direct answers and topology design share the same bounded discovery subgraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .discovery_graph import build_discovery_graph


class QueryState(TypedDict, total=False):
    occurrence: int
    decision: dict | None
    routes: list[dict]
    route: str
    result: dict
    output: dict


def build_query_graph(node_factory):
    from ..harness.operation_graph import expose_stateless_subgraph

    graph = StateGraph(QueryState)
    discovery = build_discovery_graph(node_factory)
    graph.add_node("discover", discovery)
    graph.add_node("respond", node_factory("respond"))
    graph.add_edge(START, "discover")
    graph.add_conditional_edges(
        "discover",
        lambda state: END if state.get("result") else "respond",
        [END, "respond"],
    )
    graph.add_edge("respond", END)
    compiled = graph.compile(name="query_graph", checkpointer=False)
    expose_stateless_subgraph(compiled, "discover", discovery)
    return compiled
