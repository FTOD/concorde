"""A small sample LangGraph Graph API graph used to exercise the Graph Spec check."""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class BatchState(TypedDict, total=False):
    index: int
    output: Any
    stop: bool


def build_batch_graph(node_factory, *, name: str, item_node: str):
    graph = StateGraph(BatchState)
    graph.add_node("select_item", node_factory("select_item"))
    graph.add_node(item_node, node_factory(item_node))
    graph.add_edge(START, "select_item")
    graph.add_conditional_edges(
        "select_item",
        lambda state: END if state["stop"] else item_node,
        [END, item_node],
    )
    graph.add_conditional_edges(
        item_node,
        lambda state: END if state["stop"] else "select_item",
        [END, "select_item"],
    )
    return graph.compile(name=name, checkpointer=False)
