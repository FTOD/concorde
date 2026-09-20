"""Planning: context assessment followed by one revision-bound plan."""

from __future__ import annotations

from ..harness.change_worktree import (
    WORK_PATH,
    progress,
    read_change,
    save_target_state,
    target_state,
    work_path,
)
from ..harness.revisions import target_revision
from ..review.review import require_spec_review
from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError
from ..spec.typed_data import artifact


def plan(run) -> dict:
    from .plan_graph import build_plan_graph

    return build_plan_graph(plan_nodes(run).__getitem__).invoke({})["output"]


def plan_nodes(run):
    from langgraph.graph import END

    result = None

    def assess_context(state):
        require_spec_review(run)
        if not run.host.coordinated:
            progress(
                run.repository.root, phase="plan", status="active", invalidate=True
            )
        assessment = run.stage("concorde-context-solve")
        if assessment["outcome"] not in {"completed", "sufficient"}:
            return {
                "output": run.response(
                    assessment["outcome"],
                    assessment["answer"],
                    blockers=assessment["blockers"],
                ),
                "route": END,
            }
        return {"route": "author_plan"}

    def author_plan(state):
        nonlocal result
        result = run.stage("concorde-plan", defer_gap_resolution=True)
        if result["outcome"] not in {"completed", "sufficient"}:
            return {
                "output": run.response(
                    result["outcome"], result["answer"], blockers=result["blockers"]
                ),
                "route": END,
            }
        if run.host.mode == "describe-policy":
            return {"output": run.response("described"), "route": END}
        return {"route": "persist_plan"}

    def persist_plan(state):
        assert result is not None, (
            "plan persistence requires an admitted planner result"
        )
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
        return {
            "output": run.response(
                answer=result["answer"],
                artifacts=[artifact(run.repository.root, "plan", path)],
            ),
            "route": END,
        }

    return {
        "assess_context": assess_context,
        "author_plan": author_plan,
        "persist_plan": persist_plan,
    }


def context_solve(run, operation: str) -> dict:
    """One context-assessor stage; a sufficient assessment completes the operation."""
    result = run.stage(operation)
    return run.response(
        "completed" if result["outcome"] == "sufficient" else result["outcome"],
        result["answer"],
        blockers=result["blockers"],
    )
