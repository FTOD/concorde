"""Capability selection and stage dispatch are executable LangGraph transitions."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class DispatchState(TypedDict, total=False):
    route: str
    output: dict
    result: dict


SUBFLOW_NODES = {
    "answer": ("decide", "expand_context", "bind_routes", "finish", "respond"),
    "design_topology": ("decide", "expand_context", "bind_routes", "finish", "respond"),
    "prepare_topology": ("prepare_authors", "author_module", "validate_candidate", "review_contexts", "persist_application"),
    "apply_topology": ("admit_application", "validate_application", "apply_atomically", "cleanup"),
    "triage": ("select_records", "record_gaps", "status", "remove_records", "prepare_investigation", "investigate",
               "persist_findings", "implement_resolution", "validate_candidate", "finish"),
    "plan": ("assess_context", "author_plan", "persist_plan"),
    "project": ("select_action", "configure", "propose", "apply"),
    "development_loop": ("initialize", "specify", "review_spec", "plan", "tasks", "implement", "validate",
                         "review_code", "ready", "summarize"),
}

DISPATCH_NODES = ("select_capability", "prepare_target", "deliver", "project", "answer", "design_topology",
                  "prepare_topology", "apply_topology", "review", "describe_policy", "triage", "specify",
                  "plan", "tasks", "implement", "validate", "development_loop", "context_solve",
                  *(name + "/" + node for name, nodes in SUBFLOW_NODES.items() for node in nodes))


def build_dispatch_flow(node_factory, *, capability=None):
    from .capability_flow import expose_stateless_subflow
    from .query_flow import build_query_flow
    from .topology_flow import build_topology_flow, build_topology_apply_flow
    from .plan_flow import build_plan_flow
    from .project_flow import build_project_flow
    from .loop_flow import build_loop_flow
    from ..reflections.triage_flow import build_triage_flow
    factories = {"answer": build_query_flow, "design_topology": build_query_flow,
                 "prepare_topology": build_topology_flow, "apply_topology": build_topology_apply_flow,
                 "plan": build_plan_flow, "project": build_project_flow, "triage": build_triage_flow,
                 "development_loop": lambda nodes: build_loop_flow(nodes, dynamic=True)}
    flow = StateGraph(DispatchState)
    leaves = ("deliver", "project", "answer", "design_topology", "prepare_topology", "apply_topology",
              "review", "describe_policy", "triage", "specify", "plan", "tasks", "implement",
              "validate", "development_loop", "context_solve")
    entry = ["deliver", "project", "answer", "design_topology", "prepare_topology", "apply_topology", "prepare_target"]
    targeted = list(leaves[6:])
    if capability == "concorde-main":
        entry, targeted = ["answer", "design_topology", "prepare_topology", "apply_topology"], []
    elif capability in {"concorde-init", "concorde-configure", "concorde-deliver"}:
        entry, targeted = ["deliver" if capability == "concorde-deliver" else "project"], []
    elif capability is not None:
        entry = ["prepare_target"]
        target = {"concorde-review": "review", "concorde-reflections-triage": "triage",
                  "concorde-specify": "specify", "concorde-plan": "plan", "concorde-tasks": "tasks",
                  "concorde-implement": "implement", "concorde-validate": "validate",
                  "concorde-dev-loop": "development_loop"}.get(capability, "context_solve")
        targeted = [target] + ([] if target == "review" else ["describe_policy"])
    leaves = tuple(name for name in leaves if name in entry or name in targeted)
    children = {}
    for name in ("select_capability", *(["prepare_target"] if targeted else []), *leaves):
        if name in factories:
            children[name] = factories[name](lambda child, name=name: node_factory(name + "/" + child))
            flow.add_node(name, children[name])
        else:
            flow.add_node(name, node_factory(name))
    flow.add_edge(START, "select_capability")
    flow.add_conditional_edges("select_capability", lambda state: state["route"],
        [*entry, END])
    if targeted:
        flow.add_conditional_edges("prepare_target", lambda state: state["route"], [*targeted, END])
    for name in leaves:
        flow.add_edge(name, END)
    compiled = flow.compile(name="dispatch_flow", checkpointer=False)
    for name, child in children.items():
        expose_stateless_subflow(compiled, name, child)
    return compiled
