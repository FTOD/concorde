"""The development Graph's node bindings: one change carried to a ready candidate."""

from __future__ import annotations

import importlib
from dataclasses import replace

from ..harness.change_worktree import (
    WORK_PATH,
    blocker_scope,
    graph_state,
    progress,
    read_change,
    record_transition,
    save_change,
    target_state,
)
from ..harness.invocation import Invocation
from ..harness.revisions import implementation_digest, issues_revision, target_revision
from ..spec.contracts import load_operation_inventory
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from ..spec.typed_data import (
    OPERATION_CONTRACTS,
    canonical,
    decode,
    typed,
    validate_typed,
    verify_artifacts,
)
from ..validation.validate import mark_ready, validate


def loop(run) -> dict:
    """The development Graph (G1-G4): a bounded ``review_code -> tasks`` repair edge is the
    only automatic revision; every other non-advancing outcome stops the Graph for a human,
    with the stopping status recorded on the change and the transition recorded under
    ``graph`` in ``.concorde/worktree.json`` (development.md's "AI and human feedback").
    """
    from .loop_graph import build_loop_graph

    return build_loop_graph(loop_nodes(run).__getitem__, dynamic=True).invoke(
        {"output": {}, "artifacts": []}, {"recursion_limit": 100000}
    )["output"]


def loop_nodes(run):
    from langgraph.graph import END
    from langgraph.types import Command

    from ..harness.admission import invoke_operation
    from ..review.review import current, current_code_scope, require_reviews, skip
    from ..specify_loop.specify_graph import has_authored_spec as authored_for_task
    from .loop_graph import loop_successors, stage_command

    specify = run.task.get("specify", True)
    run_reviews = run.task.get("run_reviews", True)
    require_reviews(run, run_reviews)
    policy = importlib.import_module(
        f"{load_operation_inventory().__name__}.dev_loop"
    ).GRAPH
    graph_state(
        run.repository.root,
        run.target.id,
        policy=policy,
        spec_digest=target_revision(run.repository, run.target),
        implementation_digest=implementation_digest(run.repository, run.target)
        if run.target.files
        else None,
    )
    stages = (
        ["specify", "plan", "tasks", "implement", "validate"]
        if specify
        else ["plan", "tasks", "implement", "validate"]
    )
    change = read_change(run.repository.root, required=True)
    existing = change["targets"].get(run.target.id) if change else None
    blocked_phases = {
        item["phase"]
        for item in change.get("issue_blockers", [])
        if item["status"] == "open"
        and item["target_id"] == run.target.id
        and item["scope_id"] == blocker_scope(change, run.target.id, run.task["task"])
    }
    has_authored_spec = authored_for_task(change, run.target.id, run.task)
    if specify and has_authored_spec:
        stages.remove("specify")
    if (
        (not specify or has_authored_spec)
        and existing
        and existing.get("plan")
        and not blocked_phases.intersection({"context-solve", "plan"})
        and existing.get("task") == run.task["task"]
        and existing.get("focus_id") == run.task.get("focus_id")
        and existing.get("constraints", []) == run.task.get("constraints", [])
        and existing.get("spec_digest") == target_revision(run.repository, run.target)
    ):
        stages = ["tasks", "implement", "validate"]
        if existing.get("tasks") and "tasks" not in blocked_phases:
            stages = ["implement", "validate"]
            if (
                not existing.get("coordination")
                and all(item["complete"] for item in existing["tasks"])
                and "implementation" not in blocked_phases
                and existing.get("implementation_digest")
                == implementation_digest(run.repository, run.target)
            ):
                stages = ["validate"]
    if (
        run.host.finalize_components
        and existing
        and all(task["complete"] for task in existing.get("tasks", []))
    ):
        stages = ["validate"]

    scope_repair = run.task.get("repair_task_scope")
    if scope_repair:
        if not existing:
            raise SpecError(
                "task scope repair requires an existing task list", "missing_tasks"
            )
        run.check_state(existing, allow_stale_spec=True)
        consumed = any(
            item.get("tasks_digest") == scope_repair["tasks_digest"]
            and item.get("reason") == "implementation_boundary"
            for item in existing.get("task_history", [])
        )
        if consumed:
            scope_repair = (
                None  # replay resumes; it never reauthors an accepted replacement
            )
        elif (
            not existing.get("tasks")
            or all(t["complete"] for t in existing["tasks"])
            or digest(canonical(existing["tasks"]).encode())
            != scope_repair["tasks_digest"]
            or change.get("graph", {}).get(run.target.id, {}).get("repair") is not None
            or blocked_phases
        ):
            raise SpecError(
                "task scope repair requires current incomplete tasks without unresolved gaps or review repair",
                "incompatible_handoff",
            )
        else:
            stages = ["tasks", "implement", "validate"]

    # Resume trimming (above) only decides where the traversed path *enters*; every node from
    # "tasks" onward is still declared below so a repair can re-enter "tasks" even when this
    # run resumed past it (e.g. straight at "validate").
    include_specify = stages[0] == "specify"
    entry = stages[1] if include_specify else stages[0]
    successor = loop_successors(
        include_specify=include_specify,
        entry=entry,
        has_code=bool(run.target.files),
    )

    def current_iteration() -> int:
        record = (
            read_change(run.repository.root, required=True)
            .get("graph", {})
            .get(run.target.id, {})
        )
        return record.get("repair_iteration", 0)

    def stop(name: str, outcome: str) -> str:
        """A non-advancing, non-repairable outcome: record it and end the Graph for a human."""
        status = (
            "waiting"
            if outcome == "spec_incomplete"
            else "failed"
            if outcome == "failed"
            else "blocked"
        )
        if run.host.lifecycle.get("status") in {"cancelled", "limit_exhausted"}:
            status = run.host.lifecycle["status"]
        run.host.lifecycle["status"] = status
        trigger = (
            "ai-review"
            if name in {"review_spec", "review_code"}
            else "deterministic"
            if name == "validate"
            else "ai-assessment"
        )
        record_transition(
            run.repository.root,
            run.target.id,
            iteration=current_iteration(),
            **{"from": name, "to": "END"},
            trigger=trigger,
            outcome=outcome,
            source="code-driven"
            if name == "validate" or outcome == "failed"
            else "model-driven",
            artifact=None,
            input_digest=None,
            finding_ids=[],
            status=status,
        )
        return END

    def route_review_code(data: dict) -> str:
        """Blocking code-review findings without a gap: repair once, unless unchanged
        feedback or the declared iteration limit says otherwise (G2/G3 "AI review")."""
        if data["outcome"] != "conflicting":
            return stop("review_code", data["outcome"])
        if any(
            value["data"]["target_id"] != run.target.id
            and any(
                finding["severity"] == "blocking" for finding in value["data"]["issues"]
            )
            for value in data.get("reviews", [])
        ):
            # A peer's contract is not this planner's context. Preserve the peer result
            # for separately routed work instead of inventing a repair from the first artifact.
            return stop("review_code", data["outcome"])
        reference = next(
            item
            for item in data["artifacts"]
            if item["id"] == f"review.{run.target.id}.code"
        )
        verify_artifacts(run.repository.root, reference)
        reviewed = validate_typed(
            decode(read_file(run.repository.root, reference["path"]).decode()),
            "concorde-review-result",
        )["data"]
        blocking = [f for f in reviewed["issues"] if f["severity"] == "blocking"]
        from ..issues.references import receipt
        from ..issues.store import resolve_report

        feedback_digest = digest(
            sorted(
                canonical(
                    {
                        key: value
                        for key, value in resolve_report(
                            run.repository.root, receipt(f)
                        )["report"].items()
                        if key not in {"report_key", "issue_id", "expected_revision"}
                    }
                )
                for f in blocking
            )
        )
        finding_ids = sorted(f["issue_id"] for f in blocking)
        change = read_change(run.repository.root, required=True)
        record = change["graph"][run.target.id]
        common = dict(
            **{"from": "review_code", "to": "tasks"},
            trigger="ai-review",
            outcome="conflicting",
            source="model-driven",
            artifact=reference,
            input_digest=reviewed["input_digest"],
            finding_ids=finding_ids,
        )
        if feedback_digest == record["last_feedback_digest"]:
            run.host.lifecycle["status"] = "waiting"
            record_transition(
                run.repository.root,
                run.target.id,
                iteration=record["repair_iteration"],
                **{**common, "to": "END", "source": "code-driven"},
                status="waiting",
            )
            return END
        if record["repair_iteration"] >= record["policy"]["max_repair_iterations"]:
            run.host.lifecycle["status"] = "limit_exhausted"
            record_transition(
                run.repository.root,
                run.target.id,
                iteration=record["repair_iteration"],
                **{**common, "to": "END", "source": "code-driven"},
                status="limit_exhausted",
            )
            return END
        iteration = record["repair_iteration"] + 1
        record.update(
            repair_iteration=iteration,
            last_feedback_digest=feedback_digest,
            repair={"artifact": reference, "iteration": iteration},
        )
        save_change(run.repository.root, change)
        record_transition(
            run.repository.root,
            run.target.id,
            iteration=iteration,
            **common,
            status=None,
        )
        return "tasks"

    def execute(name):
        def node(state):
            run.repository = SpecRepository(
                run.host.project_root, run.host.package_root
            )
            if name == "ready":
                work = target_state(
                    run.repository.root, run.target.id, run.task.get("focus_id")
                )
                if work.get("validation_issue_digest") != issues_revision(
                    run.repository.root
                ):
                    # Reviews may report advisory Issues after the earlier checks. Refresh
                    # deterministic evidence for those new deliverable bytes without reusing
                    # a stale ready receipt or making Issue reporting fail the task.
                    validator = Invocation(
                        "concorde-validate",
                        run.configuration,
                        run.task,
                        replace(run.host, defer_ready=True),
                    )
                    checked = validate(validator)["data"]
                    if checked["outcome"] != "completed":
                        return Command(goto="summarize", update={"output": checked})
                return Command(
                    goto="summarize", update={"output": mark_ready(run)["data"]}
                )
            mode = name.removeprefix("review_")
            is_review = name.startswith("review_")
            data = None
            review_artifacts: list[dict] = []
            if is_review:
                mode = name.removeprefix("review_")
                enabled = read_change(run.repository.root, required=True)[
                    "review_requirements"
                ][run.target.id][mode]
                if not enabled:
                    skip(run, mode)
                    reference = read_change(run.repository.root, required=True)[
                        "reviews"
                    ][run.target.id][mode]["artifact"]
                    review_artifacts.append(reference)
                    data = run.response(
                        answer=f"{mode} review explicitly skipped.",
                        artifacts=[reference],
                    )["data"]
                elif current(run, mode) is not None and (
                    mode != "code" or current_code_scope(run) is not None
                ):
                    review_artifacts.append(
                        read_change(run.repository.root, required=True)["reviews"][
                            run.target.id
                        ][mode]["artifact"]
                    )
                    data = run.response(answer=f"Current {mode} review retained.")[
                        "data"
                    ]
                elif not run.host.coordinated:
                    progress(
                        run.repository.root,
                        phase=mode + "-review",
                        status="active",
                        invalidate=True,
                    )
            if data is None:
                child_operation = "concorde-" + name.replace("_", "-")
                if is_review:
                    child_operation = "concorde-review"
                payload = {
                    "target_id": run.target.id,
                    "task": run.task["task"],
                    "constraints": run.task.get("constraints", []),
                }
                if name == "specify_loop":
                    payload.update(specify=specify, run_reviews=run_reviews)
                if (
                    name == "tasks"
                    and scope_repair
                    and not any(
                        item.get("tasks_digest") == scope_repair["tasks_digest"]
                        for item in target_state(
                            run.repository.root,
                            run.target.id,
                            run.task.get("focus_id"),
                        ).get("task_history", [])
                    )
                ):
                    # The request only binds a list. Host-generated semantic feedback
                    # contains neither source contents nor raw validation output.
                    payload["repair_task_scope"] = scope_repair
                if is_review:
                    payload["review_mode"] = mode
                if run.task.get("focus_id"):
                    payload["focus_id"] = run.task["focus_id"]
                if run.change_id:
                    payload["change_id"] = run.change_id
                child_host = replace(
                    run.host,
                    evidence=[],
                    descriptions=run.host.descriptions,
                    lifecycle=run.host.lifecycle,
                    track_gaps=True,
                    defer_ready=name == "validate",
                )
                result = invoke_operation(
                    run.operation,
                    child_operation,
                    run.configuration,
                    typed(OPERATION_CONTRACTS[child_operation][0], payload),
                    child_host,
                )
                run.host.evidence.extend(child_host.evidence)
                if result["output"] is None:
                    first_code = (
                        result["errors"][0]["code"] if result["errors"] else None
                    )
                    if first_code in {"execution_cancelled", "execution_limit"}:
                        run.host.lifecycle["status"] = (
                            "cancelled"
                            if first_code == "execution_cancelled"
                            else "limit_exhausted"
                        )
                    raise SpecError(
                        f"{child_operation} blocked: " + canonical(result["errors"]),
                        "child_blocked",
                    )
                data = result["output"]["data"]
                run.change_id = data["change_id"] or run.change_id
                run.work_directory = (
                    f"{WORK_PATH}/{run.target.id}" if run.change_id else None
                )
                run.last_context = data["context_id"] or run.last_context
                run.completed.extend(data["completed_operations"])
                if is_review or name in {"implement", "specify_loop"}:
                    review_artifacts.extend(
                        item
                        for item in data["artifacts"]
                        if item["id"].startswith("review.")
                    )
                run.repository = SpecRepository(
                    run.host.project_root, run.host.package_root
                )
            if (
                run.host.defer_component_checks
                and data["outcome"] in {"completed", "ready"}
                and (
                    name == "implement"
                    or name == "specify_loop"
                    and entry == "validate"
                )
            ):
                record_transition(
                    run.repository.root,
                    run.target.id,
                    iteration=current_iteration(),
                    **{"from": name, "to": "END"},
                    trigger="deterministic",
                    outcome="completed",
                    source="code-driven",
                    artifact=None,
                    input_digest=None,
                    finding_ids=[],
                    status="active",
                )
                data = {
                    **data,
                    "outcome": "completed",
                    "answer": "Component code draft is complete; the enclosing Module verifies the final shared candidate.",
                }
                route = END
            elif data["outcome"] in {"completed", "ready"}:
                route = successor[name]
            elif name == "review_code":
                route = route_review_code(data)
            else:
                route = stop(name, data["outcome"])
            return stage_command(route, output=data, artifacts=review_artifacts)

        def observed(state):
            iteration = current_iteration()
            run.host.observe(
                "stage_started",
                operation=run.operation,
                stage=name,
                invocation_id=run.host.invocation_id,
                iteration=iteration,
                trigger="ai-review"
                if name == "tasks" and iteration
                else "deterministic",
            )
            try:
                command = node(state)
            except Exception:
                run.host.observe(
                    "stage_failed",
                    operation=run.operation,
                    stage=name,
                    invocation_id=run.host.invocation_id,
                )
                raise
            if not isinstance(command.update, dict):
                raise SpecError(
                    "Graph stage returned no typed output update",
                    "invalid_completion",
                )
            run.host.observe(
                "stage_finished",
                operation=run.operation,
                stage=name,
                invocation_id=run.host.invocation_id,
                outcome=command.update["output"].get("outcome"),
                iteration=current_iteration(),
                trigger="ai-review" if name == "review_code" else "deterministic",
            )
            return command

        return observed

    def initialize(state):
        return Command(goto="specify_loop")

    def summarize(state):
        if state.get("result"):
            return {}
        result = state["output"]
        artifacts = list(
            {
                item["id"]: item
                for item in [*state.get("artifacts", []), *result["artifacts"]]
            }.values()
        )
        coverage = []
        for reference in artifacts:
            if reference["id"].startswith("review."):
                verify_artifacts(run.repository.root, reference)
                value = validate_typed(
                    decode(read_file(run.repository.root, reference["path"]).decode()),
                    "concorde-review-result",
                )["data"]
                coverage.append(
                    f"{value['target_id']}/{value['review_mode']}={value['status']}"
                )
        answer = result["answer"] + (
            " Review coverage: " + "; ".join(coverage) + "." if coverage else ""
        )
        return {
            "output": run.response(
                result["outcome"],
                answer,
                blockers=result["blockers"],
                checks=result["checks"],
                artifacts=artifacts,
            )
        }

    names = (
        "specify_loop",
        "plan",
        "tasks",
        "implement",
        "validate",
        "review_code",
        "ready",
    )
    return {
        "initialize": initialize,
        "summarize": summarize,
        **{name: execute(name) for name in names},
    }
