"""Reflection disposition, investigation and implementation as an executable Flow."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class TriageState(TypedDict, total=False):
    result: dict
    index: int
    output: dict
    route: str


def build_triage_flow(node_factory):
    flow = StateGraph(TriageState)
    names = ("select_records", "record_gaps", "status", "remove_records", "prepare_investigation",
             "investigate", "persist_findings", "implement_resolution", "validate_candidate", "finish")
    for name in names:
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "select_records")
    flow.add_conditional_edges("select_records", lambda state: state["route"],
        ["record_gaps", "status", "remove_records", "prepare_investigation", END])
    for name in ("record_gaps", "status", "remove_records", "validate_candidate", "finish"):
        flow.add_edge(name, END)
    flow.add_conditional_edges("prepare_investigation", lambda state: state["route"], ["investigate", END])
    flow.add_conditional_edges("investigate", lambda state: state["route"], ["persist_findings", END])
    flow.add_conditional_edges("persist_findings", lambda state: state["route"],
                              ["implement_resolution", "validate_candidate", "finish", END])
    flow.add_conditional_edges("implement_resolution", lambda state: state["route"],
                              ["implement_resolution", "validate_candidate", END])
    return flow.compile(name="triage_flow", checkpointer=False)
