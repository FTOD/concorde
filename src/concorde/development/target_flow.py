"""Target admission composes the discovery instance that Studio expands."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .discovery_flow import build_discovery_flow


class TargetState(TypedDict, total=False):
    occurrence: int
    routes: list[dict]
    decision: dict | None
    route: str
    result: dict
    output: dict


def build_target_flow(node_factory, *, discover=True):
    from .capability_flow import expose_stateless_subflow
    flow = StateGraph(TargetState)
    flow.add_node("initialize_target", node_factory("initialize_target"))
    flow.add_node("bind_target", node_factory("bind_target"))
    flow.add_edge(START, "initialize_target")
    choices = ["bind_target", END]
    discovery = None
    if discover:
        discovery = build_discovery_flow(node_factory)
        flow.add_node("discover", discovery)
        choices.append("discover")
        flow.add_conditional_edges("discover",
            lambda state: END if state.get("result") else "bind_target", [END, "bind_target"])
    flow.add_conditional_edges("initialize_target", lambda state: state["route"], choices)
    flow.add_edge("bind_target", END)
    compiled = flow.compile(name="target_flow", checkpointer=False)
    if discovery is not None:
        expose_stateless_subflow(compiled, "discover", discovery)
    return compiled
