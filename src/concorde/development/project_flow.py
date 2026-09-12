"""Initialization and configuration select explicit deterministic operations."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ProjectState(TypedDict, total=False):
    route: str
    output: dict
    result: dict


def build_project_flow(node_factory):
    flow = StateGraph(ProjectState)
    for name in ("select_action", "configure", "propose", "apply"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "select_action")
    flow.add_conditional_edges("select_action", lambda state: state["route"], ["configure", "propose", "apply", END])
    for name in ("configure", "propose", "apply"):
        flow.add_edge(name, END)
    return flow.compile(name="project_flow", checkpointer=False)
