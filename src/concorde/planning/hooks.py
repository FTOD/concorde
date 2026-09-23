"""Planning's Agent hooks and the plan workflow hook.

Agent execution's native driver freezes the context, prepares every call, stages and verifies each
proposal and records the run; these hooks do only what depends on Planning: the checks before an
Agent starts, the stage inputs, the business rules of a proposal and what an accepted one records.
"""

from __future__ import annotations

from pathlib import Path

from ..harness.change_worktree import progress, repository_lock
from ..harness.context import ContextSnapshot, recheck_context, resolve_context
from ..harness.invocation import validate_stage_identity
from ..harness.native_driver import (
    StagePlan,
    WorkflowPlan,
    candidate_input_digest,
    stage_response,
    stop_plan,
)
from ..review.review import require_spec_review
from ..spec.repository import SpecError, digest
from ..spec.typed_data import canonical
from .gaps import assessment_dependencies, pending_gaps, record_gaps
from .plan import persist_plan_result
from .tasks import persist_tasks, prepare_tasks, validate_tasks

SUCCESS = {"completed", "sufficient"}


def _mark_active(run, phase: str) -> None:
    """The candidate's progress enters ``phase`` when a planning step is prepared."""
    if run.host.mode == "execute" and not run.host.coordinated:
        progress(run.repository.root, phase=phase, status="active", invalidate=True)


def _pending_stop(run, phase: str) -> dict | None:
    pending = pending_gaps(run, phase)
    if not pending:
        return None
    return run.response(
        "spec_incomplete",
        "Repair the recorded necessary contracts before resuming this step.",
        blockers=pending,
    )


def with_issue_context(run, inputs: tuple[dict, ...]) -> tuple[dict, ...]:
    """Add the Issue context of the findings a review repair cites, once."""
    reviews = [v for v in inputs if v["type_id"] == "concorde-review-result"]
    if not reviews or any(v["type_id"] == "concorde-issue-context" for v in inputs):
        return inputs
    from ..issues.references import observation_context

    return (
        *inputs,
        observation_context(run.repository.root, reviews[0]["data"]["issues"]),
    )


def _record_blockers(run, phase: str, data: dict) -> dict:
    """The response of a proposal that is not a success; its blockers become pending gaps."""
    if data["blockers"]:
        record_gaps(run, phase, data["blockers"])
    return stage_response(run, data)


class ContextAssessorHook:
    """The context assessor in ``context-solve``, alone or as the first step of the plan."""

    def prepare(self, run, admitted):
        in_plan = run.operation != "concorde-context-solve"
        if in_plan:
            require_spec_review(run)
        if admitted is not None:
            return StagePlan()
        if in_plan:
            _mark_active(run, "plan")
            stop = _pending_stop(run, "context-solve")
            if stop is not None:
                return StagePlan(stop=stop)
        if run.host.mode == "execute":
            snapshot = resolve_context(
                run.repository,
                run.target.id,
                agent="context_assessor",
                task=run.task["task"],
                focus_id=run.task.get("focus_id"),
                constraints=tuple(run.task.get("constraints", [])),
            )
            blocked = assessment_dependencies(run, snapshot)
            if blocked is not None:
                run.last_context = snapshot.id
                return StagePlan(stop=stage_response(run, blocked))
        return StagePlan()

    def recheck(self, run, descriptor):
        return None

    def validate(self, run, snapshot, plan, data):
        validate_stage_identity(data, snapshot.id)

    def accept(self, run, snapshot, plan, data):
        run.completed.append("concorde-context-solve")
        if data["outcome"] == "sufficient":
            record_gaps(run, "context-solve", [])
            return stage_response(run, data)
        return _record_blockers(run, "context-solve", data)


class PlannerHook:
    """The planner in ``plan``, the second step of the plan workflow."""

    def prepare(self, run, admitted):
        require_spec_review(run)
        if admitted is None:
            _mark_active(run, "plan")
            stop = _pending_stop(run, "plan")
            if stop is not None:
                return StagePlan(stop=stop)
        return StagePlan()

    def recheck(self, run, descriptor):
        return None

    def validate(self, run, snapshot, plan, data):
        validate_stage_identity(data, snapshot.id)
        if data["outcome"] in SUCCESS and not data["plan"].strip():
            raise SpecError("planning produced no usable plan", "invalid_completion")

    def accept(self, run, snapshot, plan, data):
        run.completed.append("concorde-plan")
        if data["outcome"] in SUCCESS:
            run.completed.insert(0, "concorde-context-solve")
            return persist_plan_result(run, data)
        return _record_blockers(run, "plan", data)


class TaskAuthorHook:
    """The task author in ``tasks``."""

    def prepare(self, run, admitted):
        inputs = with_issue_context(run, prepare_tasks(run)[1])
        if admitted is None:
            _mark_active(run, "tasks")
            stop = _pending_stop(run, "tasks")
            if stop is not None:
                return StagePlan(stop=stop)
        return StagePlan(stage_inputs=inputs)

    def recheck(self, run, descriptor):
        return None

    def validate(self, run, snapshot, plan, data):
        validate_stage_identity(data, snapshot.id)
        if data["outcome"] in SUCCESS:
            validate_tasks(run, data, prepare_tasks(run)[2])

    def accept(self, run, snapshot, plan, data):
        run.completed.append("concorde-tasks")
        if data["outcome"] in SUCCESS:
            state, _, _, repair, scope = prepare_tasks(run)
            return persist_tasks(run, data, state, repair, scope)
        return _record_blockers(run, "tasks", data)


class PlanWorkflowHook:
    """The plan workflow: the context assessor, then, after a sufficient assessment, the planner."""

    SCRIPT = "pi/workflows/plan.js"
    HOST = "pi/native-plan-host.mjs"
    STEPS = ("bind", "advance", "finalize")

    def prepare(self, run, driver):
        if run.host.mode == "describe-policy":
            return stop_plan(
                run.response(
                    "described",
                    "A fresh context assessor, then after a sufficient assessment a fresh "
                    "planner; prompt-level read policy; no Agent ran.",
                )
            )
        checked = context_assessor.prepare(run, None)
        if checked.stop is not None:
            return stop_plan(checked.stop, accepted=checked.stop_accepted)
        call = driver.issue_slot("assessor", "context_assessor", run.task)
        return WorkflowPlan(
            script=self.SCRIPT,
            host=self.HOST,
            steps=self.STEPS,
            expansion={"assessor": call},
        )

    def step(self, run, driver, name):
        if name == "bind":
            driver.check("assessor")
            return {"state": "ready"}
        if name == "advance":
            return self._advance(run, driver)
        driver.coverage(["assessor", "planner"])
        value = driver.accept("planner")
        driver.receipt(
            {"state": "accepted", "accepted": True, "output": value["result"]["output"]}
        )
        return {"state": "finished", "accepted": True, "outcome": value.get("outcome")}

    def _advance(self, run, driver):
        driver.coverage(["assessor"])
        value = driver.accept("assessor")
        output = value["result"]["output"]
        if value.get("outcome") != "sufficient":
            driver.receipt({"state": "accepted", "accepted": True, "output": output})
            return {
                "state": "finished",
                "accepted": True,
                "outcome": value.get("outcome"),
            }
        # The assessment's own recorded effects are not a change: recheck the assessed
        # contracts against the state recorded when the assessment was accepted.
        prior = driver.slot("assessor")
        terminal = driver.terminal("assessor")
        continuation = dict(prior["snapshot"])
        continuation["workspace"] = terminal["workspace"]
        continuation.pop("context_id")
        continuation["context_id"] = digest(continuation)
        recheck_context(run.repository, ContextSnapshot(canonical(continuation)))
        if (
            run.configuration != prior["configuration"]
            or digest(run.repository.registry_bytes) != prior["registry_digest"]
            or candidate_input_digest(run.repository.root) != terminal["change_digest"]
        ):
            raise SpecError("assessed inputs changed before planning", "stale_context")
        checked = planner.prepare(run, None)
        if checked.stop is not None:
            driver.receipt(
                {"state": "failed", "accepted": False, "output": checked.stop}
            )
            return {"state": "stopped", "accepted": False}
        call = driver.issue_slot("planner", "planner", run.task)
        return {
            "state": "prepared",
            "ticket": driver.slot("planner")["ticket"],
            "call": call,
        }

    def on_failure(self, run, driver, native_state):
        # Record the failure only while this Workflow still owns the same candidate inputs;
        # an old status poll never blocks newer work.
        latest = driver.slot("planner") or driver.slot("assessor")
        root = Path(latest["project_root"])
        with repository_lock(root):
            if candidate_input_digest(root) == latest["change_digest"]:
                progress(
                    root,
                    status="blocked",
                    outcome="execution_cancelled"
                    if native_state == "stopped"
                    else "execution_failed",
                )
        return None


context_assessor = ContextAssessorHook()
planner = PlannerHook()
task_author = TaskAuthorHook()
plan_workflow = PlanWorkflowHook()
