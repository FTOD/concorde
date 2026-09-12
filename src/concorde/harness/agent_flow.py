"""The actual recursive Agent decision/delegation Flow, without authority-bearing inputs."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class AgentFlowState(TypedDict, total=False):
    result: Any
    action: str


def build_agent_flow(node_factory):
    flow = StateGraph(AgentFlowState)
    for name in ("admit", "decide", "validate_step", "delegate", "complete"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "admit")
    for name, successor in (("admit", "decide"), ("decide", "validate_step"),
                            ("delegate", "decide")):
        flow.add_conditional_edges(name,
            lambda state, next_node=successor: END if state.get("result") is not None else next_node,
            [END, successor])
    flow.add_conditional_edges("validate_step",
        lambda state: END if state.get("result") is not None else state["action"],
        [END, "delegate", "complete"])
    flow.add_edge("complete", END)
    return flow.compile(name="agent_flow", checkpointer=False)
