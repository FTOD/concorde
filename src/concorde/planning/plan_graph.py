"""Context assessment precedes planning; only a successful plan is persisted."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class PlanState(TypedDict, total=False):
    route: str
    result: dict
    output: dict


def build_plan_graph(node_factory):
    graph = StateGraph(PlanState)
    for name in ("assess_context", "author_plan", "persist_plan"):
        graph.add_node(name, node_factory(name))
    graph.add_edge(START, "assess_context")
    graph.add_conditional_edges(
        "assess_context", lambda state: state["route"], ["author_plan", END]
    )
    graph.add_conditional_edges(
        "author_plan", lambda state: state["route"], ["persist_plan", END]
    )
    graph.add_edge("persist_plan", END)
    compiled = graph.compile(name="plan_graph", checkpointer=False)
    # The two model-backed nodes execute their worker through an OperationNode Graph whose state is the
    # worker's typed contract; expose those same factories so inspection shows the worker inside.
    from ..harness.operation_graph import expose_stateless_subgraph
    from ..harness.operation_node import OperationNode

    expose_stateless_subgraph(
        compiled, "assess_context", OperationNode("context_assessor").graph()
    )
    expose_stateless_subgraph(compiled, "author_plan", OperationNode("planner").graph())
    return compiled
