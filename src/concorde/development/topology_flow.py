"""Topology authoring and atomic application Flows shared by execution and inspection."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class TopologyState(TypedDict, total=False):
    result: dict
    occurrence: int
    route: str
    output: dict


def build_topology_flow(node_factory):
    flow = StateGraph(TopologyState)
    for name in ("prepare_authors", "author_module", "validate_candidate", "review_contexts", "persist_application"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "prepare_authors")
    for name in ("prepare_authors", "author_module"):
        flow.add_conditional_edges(name, lambda state: state["route"],
                                  ["author_module", "validate_candidate", END])
    flow.add_conditional_edges("validate_candidate", lambda state: state["route"], ["review_contexts", END])
    flow.add_conditional_edges("review_contexts", lambda state: state["route"], ["persist_application", END])
    flow.add_edge("persist_application", END)
    return flow.compile(name="topology_flow", checkpointer=False)


def build_topology_apply_flow(node_factory):
    flow = StateGraph(TopologyState)
    for name in ("admit_application", "validate_application", "apply_atomically", "cleanup"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "admit_application")
    flow.add_conditional_edges("admit_application", lambda state: state["route"], ["validate_application", END])
    flow.add_conditional_edges("validate_application", lambda state: END if state.get("result") else "apply_atomically", [END, "apply_atomically"])
    flow.add_conditional_edges("apply_atomically", lambda state: END if state.get("result") else "cleanup", [END, "cleanup"])
    flow.add_edge("cleanup", END)
    return flow.compile(name="topology_apply_flow", checkpointer=False)
