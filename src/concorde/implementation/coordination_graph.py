"""Coordinated writers finish before shared consumer verification and completion."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CoordinationState(TypedDict, total=False):
    output: dict | None
    route: str


def build_coordination_graph(node_factory):
    graph = StateGraph(CoordinationState)
    names = (
        "reconcile_specs",
        "validate_specs",
        "implement_components",
        "implement_local",
        "finalize_components",
        "record_completion",
    )
    for name in names:
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, names[0])
    for name, successor in zip(names, names[1:], strict=False):
        graph.add_conditional_edges(
            name,
            lambda state, *, successor=successor: (
                END if state.get("output") is not None else successor
            ),
            [END, successor],
        )
    graph.add_edge(names[-1], END)
    return graph.compile(name="coordination_graph", checkpointer=False)


def build_stabilization_graph(node_factory):
    graph = StateGraph(CoordinationState)
    for name in ("snapshot", "verify_components", "check_stability"):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "snapshot")
    graph.add_edge("snapshot", "verify_components")
    graph.add_conditional_edges(
        "verify_components",
        lambda state: END if state.get("output") is not None else "check_stability",
        [END, "check_stability"],
    )
    graph.add_conditional_edges(
        "check_stability", lambda state: state["route"], ["snapshot", END]
    )
    return graph.compile(name="stabilization_graph", checkpointer=False)
