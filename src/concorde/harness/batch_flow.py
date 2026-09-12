"""Sequential bounded composition of independently admitted work items."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class BatchState(TypedDict, total=False):
    index: int
    output: Any
    stop: bool


def build_batch_flow(node_factory, *, name: str, item_node: str):
    flow = StateGraph(BatchState)
    flow.add_node("select_item", node_factory("select_item"))
    flow.add_node(item_node, node_factory(item_node))
    flow.add_edge(START, "select_item")
    flow.add_conditional_edges("select_item", lambda state: END if state["stop"] else item_node,
                              [END, item_node])
    flow.add_conditional_edges(item_node, lambda state: END if state["stop"] else "select_item",
                              [END, "select_item"])
    return flow.compile(name=name, checkpointer=False)


def run_batch_flow(items, operation, *, name: str, item_node: str):
    """A non-None item result stops the Flow; None advances to the next item."""
    items = tuple(items)

    def select(state):
        return {"stop": state["index"] >= len(items)}

    def execute(state):
        output = operation(items[state["index"]])
        return {"index": state["index"] + 1, "output": output, "stop": output is not None}

    nodes = {"select_item": select, item_node: execute}
    return build_batch_flow(nodes.__getitem__, name=name, item_node=item_node).invoke(
        {"index": 0, "output": None}, {"recursion_limit": 2 * len(items) + 3})["output"]
