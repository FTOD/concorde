"""Coordinated writers finish before shared consumer verification and completion."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CoordinationState(TypedDict, total=False):
    output: dict | None
    route: str


def build_coordination_flow(node_factory):
    flow = StateGraph(CoordinationState)
    names = ("reconcile_specs", "validate_specs", "implement_components", "implement_local",
             "finalize_components", "record_completion")
    for name in names:
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, names[0])
    for name, successor in zip(names, names[1:]):
        flow.add_conditional_edges(name,
            lambda state, successor=successor: END if state.get("output") is not None else successor,
            [END, successor])
    flow.add_edge(names[-1], END)
    return flow.compile(name="coordination_flow", checkpointer=False)


def build_stabilization_flow(node_factory):
    flow = StateGraph(CoordinationState)
    for name in ("snapshot", "verify_components", "check_stability"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "snapshot")
    flow.add_edge("snapshot", "verify_components")
    flow.add_conditional_edges("verify_components",
        lambda state: END if state.get("output") is not None else "check_stability", [END, "check_stability"])
    flow.add_conditional_edges("check_stability", lambda state: state["route"], ["snapshot", END])
    return flow.compile(name="stabilization_flow", checkpointer=False)
