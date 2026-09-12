"""Executable, bounded Module discovery Flow; inspection never starts an Agent."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class DiscoveryState(TypedDict, total=False):
    result: dict
    occurrence: int
    decision: dict[str, Any]
    routes: list[dict[str, Any]]
    route: str


def build_discovery_flow(node_factory):
    flow = StateGraph(DiscoveryState)
    for name in ("decide", "expand_context", "bind_routes", "finish"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "decide")
    flow.add_conditional_edges("decide", lambda state: state["route"],
                              ["expand_context", "bind_routes", "finish", END])
    flow.add_conditional_edges("expand_context", lambda state: END if state.get("result") else "decide", [END, "decide"])
    flow.add_edge("bind_routes", END)
    flow.add_edge("finish", END)
    return flow.compile(name="discovery_flow", checkpointer=False)
