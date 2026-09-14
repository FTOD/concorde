"""Standalone Spec authoring/review flow, also composed by the development loop."""
from dataclasses import replace
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


def build_specify_flow(node_factory):
    class State(TypedDict, total=False):
        output: dict
        result: dict

    flow = StateGraph(State)
    for name in ("initialize", "specify", "review_spec", "summarize"):
        flow.add_node(name, node_factory(name))
    flow.add_edge(START, "initialize")
    flow.add_conditional_edges("initialize",
                               lambda state: END if state.get("result") else state["output"]["_route"],
                               ["specify", "review_spec", END])
    flow.add_conditional_edges("specify",
                               lambda state: END if state.get("result") else state["output"]["_route"],
                               {"review_spec": "review_spec", END: "summarize"})
    flow.add_edge("review_spec", "summarize")
    flow.add_edge("summarize", END)
    return flow.compile(name="specify_flow", checkpointer=False)


def has_authored_spec(change, target_id, task):
    blocked = any(item["status"] == "open" and item["target_id"] == target_id
                  and item["task"] == task["task"] and item["phase"] == "specify"
                  for item in change.get("gap_history", []))
    authored = change.get("authored_specs", {}).get(target_id, {})
    return bool(authored and not blocked and all(authored.get(key) == value for key, value in {
        "task": task["task"], "focus_id": task.get("focus_id"),
        "constraints": task.get("constraints", [])}.items()))


def specify_nodes(run):
    from .capability_host import invoke_capability
    from .review import current_spec_scope, require_reviews, skip
    from ..harness.change_worktree import read_change, progress, record_transition
    from ..spec.repository import SpecRepository, SpecError
    from ..spec.typed_data import typed, canonical

    require_reviews(run, run.task.get("run_reviews", True), modes=("spec",))
    artifacts = []

    def initialize(state):
        change = read_change(run.repository.root, required=True)
        author = run.task.get("specify", True) and not has_authored_spec(change, run.target.id, run.task)
        return {"output": {"_route": "specify" if author else "review_spec"}}

    def execute(name):
        def node(state):
            run.host.observe("stage_started", capability=run.capability, stage=name,
                             invocation_id=run.host.invocation_id, iteration=0, trigger="deterministic")
            try:
                result = perform(name)
            except Exception:
                run.host.observe("stage_failed", capability=run.capability, stage=name,
                                 invocation_id=run.host.invocation_id)
                raise
            run.host.observe("stage_finished", capability=run.capability, stage=name,
                             invocation_id=run.host.invocation_id, outcome=result["output"]["outcome"],
                             iteration=0, trigger="ai-review" if name == "review_spec" else "deterministic")
            return result
        return node

    def perform(name):
        run.repository = SpecRepository(run.host.project_root, run.host.package_root)
        data = None
        if name == "review_spec":
            change = read_change(run.repository.root, required=True)
            if not change["review_requirements"][run.target.id]["spec"]:
                skip(run, "spec")
                reference = read_change(run.repository.root, required=True)["reviews"][run.target.id]["spec"]["artifact"]
                data = run.response(answer="Spec review explicitly skipped.", artifacts=[reference])["data"]
            elif (references := current_spec_scope(run)) is not None:
                data = run.response(answer="Current owner and consumer Spec reviews retained.",
                                    artifacts=references)["data"]
            elif not run.host.coordinated:
                progress(run.repository.root, phase="spec-review", status="active", invalidate=True)
        if data is None:
            capability = "concorde-specify" if name == "specify" else "concorde-review"
            payload = {key: run.task[key] for key in ("task", "constraints", "focus_id") if key in run.task}
            payload["target_id"] = run.target.id
            if run.change_id:
                payload["change_id"] = run.change_id
            if name == "review_spec":
                payload["review_mode"] = "spec"
            host = replace(run.host, evidence=[], descriptions=run.host.descriptions,
                           lifecycle=run.host.lifecycle, track_gaps=True)
            result = invoke_capability(run.capability, capability, run.configuration,
                                       typed(capability + "-request", payload), host)
            run.host.evidence.extend(host.evidence)
            if result["output"] is None:
                code = result["errors"][0]["code"] if result["errors"] else None
                if code in {"execution_cancelled", "execution_limit"}:
                    run.host.lifecycle["status"] = "cancelled" if code == "execution_cancelled" else "limit_exhausted"
                raise SpecError(f"{capability} blocked: " + canonical(result["errors"]), "child_blocked")
            data = result["output"]["data"]
            run.change_id = data["change_id"] or run.change_id
            run.last_context = data["context_id"] or run.last_context
            run.completed.extend(data["completed_capabilities"])
            run.repository = SpecRepository(run.host.project_root, run.host.package_root)
        artifacts.extend(data["artifacts"])
        route = "review_spec" if name == "specify" and data["outcome"] == "completed" else END
        if data["outcome"] not in {"completed", "ready"}:
            status = ("waiting" if data["outcome"] == "spec_incomplete" else
                      "failed" if data["outcome"] == "failed" else "blocked")
            if run.host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}:
                status = run.host.lifecycle["status"]
            run.host.lifecycle["status"] = status
            record = read_change(run.repository.root, required=True).get("graph", {}).get(run.target.id)
            if record is not None:
                record_transition(run.repository.root, run.target.id, iteration=record.get("repair_iteration", 0),
                    **{"from": name, "to": "END"}, trigger="ai-review" if name == "review_spec" else "ai-assessment",
                    outcome=data["outcome"], source="code-driven" if data["outcome"] == "failed" else "model-driven",
                    artifact=None, input_digest=None, finding_ids=[], status=status)
        return {"output": {**data, "_route": route}}

    def summarize(state):
        if state.get("result"):
            return {}
        data = state["output"]
        references = list({item["id"]: item for item in artifacts}.values())
        return {"output": run.response(data["outcome"], data["answer"], gaps=data["gaps"],
                                        checks=data["checks"], artifacts=references)}

    return {"initialize": initialize, "specify": execute("specify"),
            "review_spec": execute("review_spec"), "summarize": summarize}
