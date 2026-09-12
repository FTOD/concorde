"""Direct answers and topology design share the same bounded discovery subflow."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .discovery_flow import build_discovery_flow


class QueryState(TypedDict, total=False):
    occurrence: int
    decision: dict | None
    routes: list[dict]
    route: str
    result: dict
    output: dict


def build_query_flow(node_factory):
    from .capability_flow import expose_stateless_subflow
    flow = StateGraph(QueryState)
    discovery = build_discovery_flow(node_factory)
    flow.add_node("discover", discovery)
    flow.add_node("respond", node_factory("respond"))
    flow.add_edge(START, "discover")
    flow.add_conditional_edges("discover", lambda state: END if state.get("result") else "respond",
                              [END, "respond"])
    flow.add_edge("respond", END)
    compiled = flow.compile(name="query_flow", checkpointer=False)
    expose_stateless_subflow(compiled, "discover", discovery)
    return compiled
