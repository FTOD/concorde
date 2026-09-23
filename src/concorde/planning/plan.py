"""Planning: context assessment followed by one revision-bound plan."""

from __future__ import annotations

from ..harness.change_worktree import (
    WORK_PATH,
    read_change,
    save_target_state,
    target_state,
    work_path,
)
from ..harness.invocation import native_call
from ..harness.revisions import target_revision
from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError
from ..spec.typed_data import artifact


def plan(request) -> dict:
    """Workflow hook of ``concorde-plan``: planning always runs as a prepared native workflow."""
    return native_call(request)


def context_solve(run) -> dict:
    """Agent hook of the context assessor; only the native driver prepares and accepts it."""
    raise SpecError(
        "Context assessment requires the native Pi prepare/Agent boundary",
        "native_required",
    )


def persist_plan_result(run, result):
    if not result["plan"].strip():
        raise SpecError("planning produced no usable plan", "invalid_completion")
    change = read_change(run.repository.root, required=True)
    run.change_id = change["change_id"]
    run.work_directory = f"{WORK_PATH}/{run.target.id}"
    state = target_state(
        run.repository.root,
        run.target.id,
        run.task.get("focus_id"),
        create=True,
    )
    if state["tasks"]:
        state.setdefault("task_history", []).append(
            {
                "reason": "replan",
                "tasks": state["tasks"],
                "implementation_digest": state.get("implementation_digest"),
            }
        )
    state.pop("repair_review", None)
    state.pop("coordination", None)
    state.pop("component_revisions", None)
    state.update(
        plan=result["plan"],
        tasks=[],
        checks=[],
        spec_digest=target_revision(run.repository, run.target),
        task=run.task["task"],
        constraints=run.task.get("constraints", []),
        implementation_digest=None,
        completed_operations=list(run.completed),
        phase="plan",
        status="active",
    )
    path = work_path(run.target.id, "plan.md")
    apply_files(
        run.repository.root,
        [file_change(run.repository.root, path, result["plan"])],
        {path},
    )
    save_target_state(run.repository.root, state)
    run.record_gaps("plan", [])
    return run.response(
        answer=result["answer"],
        artifacts=[artifact(run.repository.root, "plan", path)],
    )
