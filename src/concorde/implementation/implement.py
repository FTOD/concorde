"""Finite implementation admission and persistence; Pi owns programmer execution."""

from __future__ import annotations

from ..harness.change_worktree import read_change, save_target_state, target_state
from ..harness.revisions import (
    implementation_digest,
    target_revision,
    unconfirmed_files,
)
from ..review.review import repair_feedback, require_spec_review
from ..planning.scope import change_scope
from ..spec.repository import SpecError
from ..spec.typed_data import typed, canonical
from ..spec.validation import validate_repository


def component_intent(tasks: list[dict]) -> str:
    return "\n\n".join(
        task["description"] + "\nAcceptance: " + task["acceptance"] for task in tasks
    )


def implement(run) -> dict:
    raise SpecError(
        "Implementation requires its native Pi programmer", "native_required"
    )


def prepare_implementation(run, *, admitted_inputs=None):
    """Current domain selection; admitted feedback survives expected code edits only."""
    require_spec_review(run)
    pending = run.pending_gaps("implementation")
    if pending:
        return (
            None,
            (),
            {},
            (),
            run.response(
                "spec_incomplete",
                "Resolve prerequisite task gaps before implementation.",
                blockers=pending,
            ),
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
    allowed = set(change_scope(run.repository, run.target.id))
    grouped = {}
    for task in state["tasks"]:
        if task["target_id"] not in allowed:
            raise SpecError(
                "component is outside the Module's change scope", "permission_denied"
            )
        grouped.setdefault(task["target_id"], []).append(task)
    local = grouped.pop(run.target.id, [])
    needed, revisions = [], {}
    change = read_change(run.repository.root, required=True)
    for target_id, tasks in grouped.items():
        component = run.repository.module(target_id)
        child = change["targets"].get(target_id, {})
        if (
            child.get("task") != component_intent(tasks)
            or child.get("constraints", []) != run.task.get("constraints", [])
            or child.get("spec_digest") != target_revision(run.repository, component)
            or not child.get("tasks")
            or any(not t["complete"] for t in child["tasks"])
            or child.get("implementation_digest")
            != implementation_digest(run.repository, component)
        ):
            needed.append({"target_id": target_id, "task": component_intent(tasks)})
        else:
            revisions[target_id] = {
                "spec": target_revision(run.repository, component),
                "implementation": implementation_digest(run.repository, component),
            }
    if needed:
        return (
            state,
            local,
            revisions,
            (),
            run.response(
                "unsupported",
                "Complete separately selected component work, then retry: "
                + canonical(needed),
            ),
        )
    if (
        admitted_inputs is None
        and validate_repository(
            run.repository.root, package_root=run.host.package_root
        ).status
        != "success"
    ):
        raise SpecError(
            "reconcile all shared contracts before implementation",
            "incompatible_contracts",
        )
    if local and not run.target.files:
        raise SpecError(
            "implementation requires listed implementation files", "unsupported_target"
        )
    inputs = (
        typed("concorde-implementation-task", {"plan": state["plan"], "tasks": local}),
    )
    repair = state.get("repair_review")
    if repair:
        if admitted_inputs is None:
            inputs = (*inputs, repair_feedback(run, repair))
        else:
            # The descriptor binds the exact accepted target state/reference. Re-evaluating
            # feedback against intentionally changed code would falsely make repair stale.
            from ..harness.status_store import verify_record_artifacts

            verify_record_artifacts(run.repository.root, repair)
            inputs = tuple(admitted_inputs)
    return state, local, revisions, inputs, None


def validate_implementation(run, data, local):
    if data["tasks"] != [{**task, "complete": True} for task in local]:
        raise SpecError(
            "implementation must report every exact task complete", "incomplete_tasks"
        )
    missing = unconfirmed_files(run.repository, run.target)
    if missing:
        raise SpecError(
            "implementation did not materialize required listed files: "
            + ", ".join(missing),
            "incomplete_tasks",
        )


def persist_implementation(run, data, state, local, revisions):
    validate_implementation(run, data, local)
    state["tasks"] = [{**task, "complete": True} for task in state["tasks"]]
    state["implementation_digest"] = implementation_digest(run.repository, run.target)
    state["checks"] = []
    state.pop("repair_review", None)
    if revisions or state.get("coordination"):
        state["component_revisions"] = revisions
    state.update(phase="implementation", status="completed")
    save_target_state(run.repository.root, state)
    run.record_gaps("implementation", [])
    return run.response(answer=data["answer"])
