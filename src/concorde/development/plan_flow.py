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
    compiled = flow.compile(name="plan_flow", checkpointer=False)
    # The two model-backed nodes execute their worker through an AgentNode Flow whose state is the
    # worker's typed contract; expose those same factories so inspection shows the worker inside.
    from ..harness.agent_model import agent_definition
    from ..harness.agent_node import AgentNode
    from .capability_flow import expose_stateless_subflow
    expose_stateless_subflow(compiled, "assess_context", AgentNode(agent_definition("context_assessor")).flow())
    expose_stateless_subflow(compiled, "author_plan", AgentNode(agent_definition("planner")).flow())
    return compiled
