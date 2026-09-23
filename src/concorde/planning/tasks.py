"""Task authoring: implementation acceptance tasks derived from the accepted plan."""

from __future__ import annotations

from ..harness.change_worktree import (
    status_path,
    read_change,
    save_target_state,
    target_state,
)
from ..review.review import repair_feedback, require_spec_review
from .scope import change_scope
from ..spec.repository import SpecError, digest
from ..harness.status_store import record_artifact
from ..spec.typed_data import (
    canonical,
    typed,
)


def tasks(run) -> dict:
    """Agent hook of the task author; only the native driver prepares and accepts it."""
    raise SpecError("Task authoring requires its native Pi Agent", "native_required")


def prepare_tasks(run):
    require_spec_review(run)
    if not run.work_directory:
        raise SpecError("task authoring requires a managed change", "missing_change")
    state = target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
    scope_repair = run.task.get("repair_task_scope")
    run.check_state(state)
    if not state["plan"]:
        raise SpecError("tasks require an authored plan", "missing_plan")
    repair = run.task.get("repair_review")
    if scope_repair and (
        not state["tasks"]
        or scope_repair["tasks_digest"] != digest(canonical(state["tasks"]).encode())
        or all(task["complete"] for task in state["tasks"])
        or repair is not None
    ):
        raise SpecError(
            "task scope repair requires the exact current incomplete task list and no pending review repair",
            "incompatible_handoff",
        )
    reserved_ids = {
        t["id"] for entry in state.get("task_history", []) for t in entry["tasks"]
    }
    reserved_ids.update(t["id"] for t in state["tasks"])
    inputs = (
        typed("concorde-plan-artifact", {"plan": state["plan"]}),
        typed(
            "concorde-task-identity-constraints",
            {"reserved_task_ids": sorted(reserved_ids)},
        ),
    )
    if scope_repair:
        inputs = (
            *inputs,
            typed(
                "concorde-implementation-task",
                {"plan": state["plan"], "tasks": state["tasks"]},
            ),
            typed(
                "concorde-task-scope-feedback",
                {**scope_repair, "reason": "implementation_boundary"},
            ),
        )
    if repair is not None:
        review_value = repair_feedback(run, repair)
        inputs = (
            *inputs,
            typed(
                "concorde-implementation-task",
                {"plan": state["plan"], "tasks": state["tasks"]},
            ),
            review_value,
        )
    return state, inputs, reserved_ids, repair, scope_repair


def validate_tasks(run, result, reserved_ids):
    tasks = result["tasks"]
    collisions = sorted({t["id"] for t in tasks} & reserved_ids)
    if collisions:
        raise SpecError(
            "task IDs are reserved by retained task history or the list being replaced: "
            + ", ".join(collisions),
            "invalid_completion",
        )
    if (
        not tasks
        or len({t["id"] for t in tasks}) != len(tasks)
        or any(t["complete"] for t in tasks)
    ):
        raise SpecError(
            "tasks must be nonempty, uniquely identified and initially incomplete",
            "invalid_completion",
        )
    scope = change_scope(run.repository, run.target.id)
    for task in tasks:
        run.repository.module(task["target_id"])
        if task["target_id"] not in scope:
            raise SpecError(
                "Module tasks may target only this Module's change scope",
                "permission_denied",
            )


def persist_tasks(run, result, state, repair, scope_repair):
    tasks = result["tasks"]
    if repair is not None:
        state.setdefault("task_history", []).append(
            {
                "reason": "review_feedback",
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
            }
        )
        state["repair_review"] = repair
    if scope_repair:
        state.setdefault("task_history", []).append(
            {
                "reason": "implementation_boundary",
                "tasks_digest": scope_repair["tasks_digest"],
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
                "spec_digest": state["spec_digest"],
            }
        )
    if state["tasks"] and not scope_repair and repair is None:
        state.setdefault("task_history", []).append(
            {
                "reason": "caller_replacement",
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
            }
        )
    if repair is None:
        state.pop("repair_review", None)
    state.pop("component_revisions", None)
    state.pop("coordination", None)
    state.update(
        tasks=tasks,
        checks=[],
        implementation_digest=None,
        phase="tasks",
        status="active",
    )
    save_target_state(run.repository.root, state)
    run.record_gaps("tasks", [])
    return run.response(
        answer=result["answer"],
        artifacts=[
            record_artifact(
                run.repository.root,
                "change",
                status_path(
                    read_change(run.repository.root, required=True)["change_id"]
                ),
            )
        ],
    )
