"""The capability admission/dispatch/result Flow used by both local calls and Studio.

The live session is private, trusted Python runtime context. This Flow is deliberately stateless with
respect to checkpointing; public callers checkpoint only the JSON input and final envelope.
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

# Domain-specific counters govern discovery, work items and repair. Leave room for nested
# scheduling rather than applying LangGraph's small default to an otherwise admitted request.
CAPABILITY_RECURSION_LIMIT = 100000


class CapabilityFlowState(TypedDict, total=False):
    result: dict
    policies: list[dict]
    events: list[dict]
    invocation: dict
    expected_workspace: dict | None


def build_capability_flow(node_factory, *, name="capability_flow", input_schema=None, output_schema=None,
                          context_schema=None):
    from .dispatch_flow import build_dispatch_flow
    flow = StateGraph(CapabilityFlowState, input_schema=input_schema, output_schema=output_schema,
                      context_schema=context_schema)
    for node in ("initialize", "admit_request", "bind_workspace", "check_configuration", "finalize"):
        flow.add_node(node, node_factory(node))
    dispatch = build_dispatch_flow(lambda node: node_factory("dispatch/" + node),
                                   capability=name if name.startswith("concorde-") else None)
    flow.add_node("execute", dispatch)
    flow.add_edge(START, "initialize")
    for node, successor in (("initialize", "admit_request"), ("admit_request", "bind_workspace"),
                            ("bind_workspace", "check_configuration"), ("check_configuration", "execute")):
        flow.add_conditional_edges(node,
            lambda state, next_node=successor: "finalize" if state.get("result") is not None else next_node,
            ["finalize", successor])
    flow.add_edge("execute", "finalize")
    flow.add_edge("finalize", END)
    compiled = flow.compile(name=name, checkpointer=False)
    expose_stateless_subflow(compiled, "execute", dispatch)
    return compiled


def expose_stateless_subflow(parent, node: str, child):
    """Register the actual child for LangGraph's Studio/xray topology discovery.

    LangGraph's automatic discovery omits children with checkpointer=False. They still execute
    as subflows; explicitly exposing that same instance keeps inspection accurate without
    serializing trusted host objects or suggesting that internal checkpoints can be resumed.
    """
    if child.checkpointer is not False:
        raise ValueError("only stateless host subflows may use this adapter")
    parent.nodes[node].subgraphs = [child]
