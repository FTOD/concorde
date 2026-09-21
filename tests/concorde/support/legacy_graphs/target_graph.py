"""Deterministic admission of an explicitly caller-selected Module."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class TargetState(TypedDict, total=False):
    route: str
    result: dict
    output: dict


def build_target_graph(node_factory):
    graph = StateGraph(TargetState)
    graph.add_node("bind_target", node_factory("bind_target"))
    graph.add_edge(START, "bind_target")
    graph.add_edge("bind_target", END)
    return graph.compile(name="target_graph", checkpointer=False)
