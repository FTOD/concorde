"""Standalone Spec authoring/review graph, also composed by the development loop.

The Graph's state is typed like the development Graph's: ``output`` holds the last stage's typed
response data, ``result`` a terminal failure envelope, and ``artifacts`` accumulates every
stage's artifact references through a reducer. Each stage returns a ``Command`` naming the
node it hands over to.
"""

from dataclasses import replace
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from .loop_graph import merge_artifacts


class SpecifyState(TypedDict, total=False):
    output: dict
    result: dict
    artifacts: Annotated[list[dict], merge_artifacts]


def build_specify_graph(node_factory):
    graph = StateGraph(SpecifyState)
    graph.add_node(
        "initialize",
        node_factory("initialize"),
        destinations=("specify", "review_spec", END),
    )
    graph.add_node(
        "specify",
        node_factory("specify"),
        destinations=("review_spec", "summarize", END),
    )
    graph.add_node(
        "review_spec", node_factory("review_spec"), destinations=("summarize", END)
    )
    graph.add_node("summarize", node_factory("summarize"))
    graph.add_edge(START, "initialize")
    graph.add_edge("summarize", END)
    return graph.compile(name="specify_graph", checkpointer=False)


def has_authored_spec(change, target_id, task):
    blocked = any(
        item["status"] == "open"
        and item["target_id"] == target_id
        and item["task"] == task["task"]
        and item["phase"] == "specify"
        for item in change.get("issue_blockers", [])
    )
    authored = change.get("authored_specs", {}).get(target_id, {})
    return bool(
        authored
        and not blocked
        and all(
            authored.get(key) == value
            for key, value in {
                "task": task["task"],
                "focus_id": task.get("focus_id"),
                "constraints": task.get("constraints", []),
            }.items()
        )
    )


def specify_nodes(run):
    from ..harness.change_worktree import progress, read_change, record_transition
    from ..spec.repository import SpecError, SpecRepository
    from ..spec.typed_data import canonical, typed
    from .operation_host import invoke_operation
    from .review import current_spec_scope, require_reviews, skip

    require_reviews(run, run.task.get("run_reviews", True), modes=("spec",))

    def initialize(state):
        change = read_change(run.repository.root, required=True)
        author = run.task.get("specify", True) and not has_authored_spec(
            change, run.target.id, run.task
        )
        return Command(goto="specify" if author else "review_spec")

    def execute(name):
        def node(state):
            run.host.observe(
                "stage_started",
                operation=run.operation,
                stage=name,
                invocation_id=run.host.invocation_id,
                iteration=0,
                trigger="deterministic",
            )
            try:
                command = perform(name)
            except Exception:
                run.host.observe(
                    "stage_failed",
                    operation=run.operation,
                    stage=name,
                    invocation_id=run.host.invocation_id,
                )
                raise
            run.host.observe(
                "stage_finished",
                operation=run.operation,
                stage=name,
                invocation_id=run.host.invocation_id,
                outcome=command.update["output"]["outcome"],
                iteration=0,
                trigger="ai-review" if name == "review_spec" else "deterministic",
            )
            return command

        return node

    def perform(name) -> Command:
        run.repository = SpecRepository(run.host.project_root, run.host.package_root)
        data = None
        if name == "review_spec":
            change = read_change(run.repository.root, required=True)
            if not change["review_requirements"][run.target.id]["spec"]:
                skip(run, "spec")
                reference = read_change(run.repository.root, required=True)["reviews"][
                    run.target.id
                ]["spec"]["artifact"]
                data = run.response(
                    answer="Spec review explicitly skipped.", artifacts=[reference]
                )["data"]
            elif (references := current_spec_scope(run)) is not None:
                data = run.response(
                    answer="Current owner and consumer Spec reviews retained.",
                    artifacts=references,
                )["data"]
            elif not run.host.coordinated:
                progress(
                    run.repository.root,
                    phase="spec-review",
                    status="active",
                    invalidate=True,
                )
        if data is None:
            operation = "concorde-specify" if name == "specify" else "concorde-review"
            payload = {
                key: run.task[key]
                for key in ("task", "constraints", "focus_id")
                if key in run.task
            }
            payload["target_id"] = run.target.id
            if run.change_id:
                payload["change_id"] = run.change_id
            if name == "review_spec":
                payload["review_mode"] = "spec"
            host = replace(
                run.host,
                evidence=[],
                descriptions=run.host.descriptions,
                lifecycle=run.host.lifecycle,
                track_gaps=True,
            )
            result = invoke_operation(
                run.operation,
                operation,
                run.configuration,
                typed(operation + "-request", payload),
                host,
            )
            run.host.evidence.extend(host.evidence)
            if result["output"] is None:
                code = result["errors"][0]["code"] if result["errors"] else None
                if code in {"execution_cancelled", "execution_limit"}:
                    run.host.lifecycle["status"] = (
                        "cancelled"
                        if code == "execution_cancelled"
                        else "limit_exhausted"
                    )
                raise SpecError(
                    f"{operation} blocked: " + canonical(result["errors"]),
                    "child_blocked",
                )
            data = result["output"]["data"]
            run.change_id = data["change_id"] or run.change_id
            run.last_context = data["context_id"] or run.last_context
            run.completed.extend(data["completed_operations"])
            run.repository = SpecRepository(
                run.host.project_root, run.host.package_root
            )
        route = (
            "review_spec"
            if name == "specify" and data["outcome"] == "completed"
            else "summarize"
        )
        if data["outcome"] not in {"completed", "ready"}:
            status = (
                "waiting"
                if data["outcome"] == "spec_incomplete"
                else "failed"
                if data["outcome"] == "failed"
                else "blocked"
            )
            if run.host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}:
                status = run.host.lifecycle["status"]
            run.host.lifecycle["status"] = status
            record = (
                read_change(run.repository.root, required=True)
                .get("graph", {})
                .get(run.target.id)
            )
            if record is not None:
                record_transition(
                    run.repository.root,
                    run.target.id,
                    iteration=record.get("repair_iteration", 0),
                    **{"from": name, "to": "END"},
                    trigger="ai-review" if name == "review_spec" else "ai-assessment",
                    outcome=data["outcome"],
                    source="code-driven"
                    if data["outcome"] == "failed"
                    else "model-driven",
                    artifact=None,
                    input_digest=None,
                    finding_ids=[],
                    status=status,
                )
        return Command(
            goto=route, update={"output": data, "artifacts": list(data["artifacts"])}
        )

    def summarize(state):
        if state.get("result"):
            return {}
        data = state["output"]
        return {
            "output": run.response(
                data["outcome"],
                data["answer"],
                blockers=data["blockers"],
                checks=data["checks"],
                artifacts=list(state.get("artifacts", [])),
            )
        }

    return {
        "initialize": initialize,
        "specify": execute("specify"),
        "review_spec": execute("review_spec"),
        "summarize": summarize,
    }
