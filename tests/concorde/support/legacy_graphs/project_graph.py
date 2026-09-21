"""Initialization and configuration select explicit deterministic operations."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ProjectState(TypedDict, total=False):
    route: str
    output: dict
    result: dict


def build_project_graph(node_factory):
    graph = StateGraph(ProjectState)
    for name in ("select_action", "configure", "propose", "apply"):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "select_action")
    graph.add_conditional_edges(
        "select_action",
        lambda state: state["route"],
        ["configure", "propose", "apply", END],
    )
    for name in ("configure", "propose", "apply"):
        graph.add_edge(name, END)
    return graph.compile(name="project_graph", checkpointer=False)
