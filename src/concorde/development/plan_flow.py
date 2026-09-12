"""Context assessment precedes planning; only a successful plan is persisted."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class PlanState(TypedDict, total=False):
    route: str
    result: dict
    output: dict


def build_plan_flow(node_factory):
    flow = StateGraph(PlanState)
    for name in ("assess_context", "author_plan", "persist_plan"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "assess_context")
    flow.add_conditional_edges("assess_context", lambda state: state["route"], ["author_plan", END])
    flow.add_conditional_edges("author_plan", lambda state: state["route"], ["persist_plan", END])
    flow.add_edge("persist_plan", END)
    return flow.compile(name="plan_flow", checkpointer=False)
