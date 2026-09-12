"""The executable development topology, shared with Concorde's own documentation.

This factory performs no project access or Agent execution. Node functions and the resume
entry are supplied by the admitted invocation; conditional outcomes remain host decisions.
"""
from typing import TypedDict


def loop_successors(*, include_specify: bool, entry: str, has_code: bool) -> dict[str, str]:
    nodes = (["specify"] if include_specify else []) + [
        "review_spec", "plan", "tasks", "implement", "validate"]
    if has_code:
        nodes.append("review_code")
    nodes.append("ready")
    successors = dict(zip(nodes, nodes[1:]))
    successors["review_spec"] = entry
    return successors


def build_loop_flow(node_factory, *, include_specify: bool = True, entry: str = "plan",
                    has_code: bool = True, dynamic: bool = False):
    from langgraph.graph import StateGraph, START, END

    class State(TypedDict):
        result: dict
        route: str
        output: dict

    successors = loop_successors(include_specify=include_specify, entry=entry, has_code=has_code)
    flow = StateGraph(State)
    for name in [*successors, "ready"]:
        flow.add_node(name, node_factory(name))
    if dynamic:
        flow.add_node("initialize", node_factory("initialize"))
        flow.add_node("summarize", node_factory("summarize"))
        flow.add_edge(START, "initialize")
        flow.add_conditional_edges("initialize",
            lambda state: END if state.get("result") else state["output"]["_route"],
            ["specify", "review_spec", END])
    else:
        flow.add_edge(START, "specify" if include_specify else "review_spec")
    for name, destination in successors.items():
        destinations = {destination: destination, END: "summarize" if dynamic else END}
        if dynamic and name == "review_spec":
            destinations.update({node: node for node in ("tasks", "implement", "validate")})
        if dynamic and name == "validate":
            destinations["ready"] = "ready"
        if name == "review_code":
            destinations["tasks"] = "tasks"
        flow.add_conditional_edges(name,
            lambda state: END if state.get("result") else state["output"]["_route"], destinations)
    flow.add_edge("ready", "summarize" if dynamic else END)
    if dynamic:
        flow.add_edge("summarize", END)
    return flow.compile(name="development_flow", checkpointer=False)
