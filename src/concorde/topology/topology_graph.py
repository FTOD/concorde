"""Topology authoring and atomic application Graphs shared by execution and inspection."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class TopologyState(TypedDict, total=False):
    result: dict
    occurrence: int
    route: str
    output: dict


def build_topology_graph(node_factory):
    graph = StateGraph(TopologyState)
    for name in (
        "prepare_authors",
        "author_module",
        "validate_candidate",
        "review_contexts",
        "persist_application",
    ):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "prepare_authors")
    for name in ("prepare_authors", "author_module"):
        graph.add_conditional_edges(
            name,
            lambda state: state["route"],
            ["author_module", "validate_candidate", END],
        )
    graph.add_conditional_edges(
        "validate_candidate", lambda state: state["route"], ["review_contexts", END]
    )
    graph.add_conditional_edges(
        "review_contexts", lambda state: state["route"], ["persist_application", END]
    )
    graph.add_edge("persist_application", END)
    return graph.compile(name="topology_graph", checkpointer=False)


def build_topology_apply_graph(node_factory):
    graph = StateGraph(TopologyState)
    for name in (
        "admit_application",
        "validate_application",
        "apply_atomically",
        "cleanup",
    ):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "admit_application")
    graph.add_conditional_edges(
        "admit_application", lambda state: state["route"], ["validate_application", END]
    )
    graph.add_conditional_edges(
        "validate_application",
        lambda state: END if state.get("result") else "apply_atomically",
        [END, "apply_atomically"],
    )
    graph.add_conditional_edges(
        "apply_atomically",
        lambda state: END if state.get("result") else "cleanup",
        [END, "cleanup"],
    )
    graph.add_edge("cleanup", END)
    return graph.compile(name="topology_apply_graph", checkpointer=False)
