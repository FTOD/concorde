"""Implementation of an accepted task list, or coordination of participating components."""

from __future__ import annotations

from ..harness.change_worktree import (
    progress,
    read_change,
    save_target_state,
    target_state,
)
from ..harness.revisions import (
    implementation_digest,
    target_revision,
    unconfirmed_files,
)
from ..review.review import repair_feedback, require_spec_review
from ..spec.repository import SpecError
from ..spec.typed_data import typed
from ..spec.validation import validate_repository


def component_intent(tasks: list[dict]) -> str:
    return "\n\n".join(
        task["description"] + "\nAcceptance: " + task["acceptance"] for task in tasks
    )


def implement(run) -> dict:
    require_spec_review(run)
    pending = run.pending_gaps("implementation")
    if pending:
        return run.response(
            "spec_incomplete",
            "Resolve the prerequisite task gaps before implementation.",
            blockers=pending,
        )
    if not run.work_directory:
        raise SpecError(
            "implementation requires a managed change and authored tasks",
            "missing_change",
        )
    state = target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
    run.check_state(state)
    if not state["tasks"]:
        raise SpecError("implementation requires tasks", "missing_tasks")
    if state.get("coordination") or any(
        task["target_id"] != run.target.id for task in state["tasks"]
    ):
        return implement_scope(run, state)
    if (
        validate_repository(
            run.repository.root, package_root=run.host.package_root
        ).status
        != "success"
    ):
        raise SpecError(
            "reconcile all shared contracts before implementation",
            "incompatible_contracts",
        )
    if not run.host.coordinated:
        progress(
            run.repository.root,
            phase="implementation",
            status="active",
            invalidate=True,
        )
    inputs = (
        typed(
            "concorde-implementation-task",
            {"plan": state["plan"], "tasks": state["tasks"]},
        ),
    )
    repair_review = state.get("repair_review")
    if repair_review:
        inputs = (*inputs, repair_feedback(run, repair_review))
    result = run.stage("concorde-implement", inputs=inputs, defer_gap_resolution=True)
    if result["outcome"] not in {"completed", "sufficient"}:
        return run.response(
            result["outcome"], result["answer"], blockers=result["blockers"]
        )
    if run.host.mode == "describe-policy":
        return run.response("described")
    returned = result["tasks"]
    expected = [{**task, "complete": True} for task in state["tasks"]]
    if returned != expected:
        raise SpecError(
            "implementation must report every exact task complete",
            "incomplete_tasks",
        )
    missing = unconfirmed_files(run.repository, run.target)
    if missing:
        raise SpecError(
            "implementation did not materialize required listed files: "
            + ", ".join(missing),
            "incomplete_tasks",
        )
    state["tasks"] = returned
    state["implementation_digest"] = implementation_digest(run.repository, run.target)
    state["checks"] = []
    state.pop("repair_review", None)
    state.update(phase="implementation", status="completed")
    save_target_state(run.repository.root, state)
    run.record_gaps("implementation", [])
    return run.response(answer=result["answer"])


def implement_scope(run, state: dict) -> dict:
    """Return separately selected component work; never author Specs or run child workflows."""
    grouped = {}
    allowed = {
        run.target.id,
        *run.target.uses,
        *(child.id for child in run.repository.children(run.target)),
    }
    for task in state["tasks"]:
        if task["target_id"] not in allowed:
            raise SpecError(
                "component is not a declared dependency or child", "permission_denied"
            )
        grouped.setdefault(task["target_id"], []).append(task)
    local_tasks = grouped.pop(run.target.id, [])
    needed = []
    revisions = {}
    for target_id, tasks in grouped.items():
        component = run.repository.select(target_id)
        intent = component_intent(tasks)
        child = read_change(run.repository.root, required=True)["targets"].get(
            target_id, {}
        )
        if (
            child.get("task") != intent
            or child.get("constraints", []) != run.task.get("constraints", [])
            or child.get("spec_digest") != target_revision(run.repository, component)
            or not child.get("tasks")
            or any(not item["complete"] for item in child["tasks"])
            or child.get("implementation_digest")
            != implementation_digest(run.repository, component)
        ):
            needed.append({"target_id": target_id, "task": intent})
        else:
            revisions[target_id] = {
                "spec": target_revision(run.repository, component),
                "implementation": implementation_digest(run.repository, component),
            }
    if needed:
        from ..spec.typed_data import canonical

        return run.response(
            "unsupported",
            "The calling agent must select and complete component work independently, "
            "including any needed Spec/metadata/registry edits and checks, then retry: "
            + canonical(needed),
        )
    if (
        validate_repository(
            run.repository.root, package_root=run.host.package_root
        ).status
        != "success"
    ):
        return run.response(
            "conflicting",
            "The calling agent must reconcile participating Specs, paired metadata and registry before implementation.",
        )
    repair = state.get("repair_review")
    feedback = (repair_feedback(run, repair),) if repair else ()
    if local_tasks:
        result = run.stage(
            "concorde-implement",
            inputs=(
                typed(
                    "concorde-implementation-task",
                    {"plan": state["plan"], "tasks": local_tasks},
                ),
                *feedback,
            ),
            defer_gap_resolution=True,
        )
        if result["outcome"] not in {"completed", "sufficient"}:
            return run.response(
                result["outcome"], result["answer"], blockers=result["blockers"]
            )
        if result["tasks"] != [{**task, "complete": True} for task in local_tasks]:
            raise SpecError(
                "local implementation must complete every exact task",
                "incomplete_tasks",
            )
        if unconfirmed_files(run.repository, run.target):
            raise SpecError("listed implementation is missing", "incomplete_tasks")
    state.pop("repair_review", None)
    state["component_revisions"] = revisions
    state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
    state.update(
        implementation_digest=implementation_digest(run.repository, run.target),
        checks=[],
        phase="implementation",
        status="completed",
    )
    save_target_state(run.repository.root, state)
    run.record_gaps("implementation", [])
    return run.response(
        answer="Local and separately completed component tasks are current; checks and reviews remain separate."
    )
