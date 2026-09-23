"""Deterministic validation of a candidate and the readiness gates that consume its evidence."""

from __future__ import annotations

from ..harness.change_worktree import (
    progress,
    read_change,
    save_change,
    snapshot_tree,
    workspace_identity,
)
from ..harness.checks import check_revision, configured_checks
from ..harness.admission import bind_module_target
from ..harness.invocation import Invocation, bind
from ..harness.revisions import (
    impact_revisions,
    implementation_digest,
    target_revision,
)
from ..planning.gaps import blocker_scope, open_gaps
from ..planning.records import save_target_state, target_state, targets
from ..spec.impact import binding_modules
from ..spec.repository import SpecError, SpecRepository
from ..spec.validation import validate_repository
from .records import direct_evidence, validation_records


def edited_modules(repository, paths) -> tuple[str, ...]:
    """Modules whose write sets hold a changed path: the owner of a changed Spec document member
    and every Module that binds a changed file. Paths in no write set concern no Module."""
    result: set[str] = set()
    for path in paths:
        reading = repository.source_documents.get(path)
        if reading is not None and reading in repository.units:
            result.add(repository.units[reading].owner)
        result.update(repository.implemented_by(path))
    return tuple(sorted(result & set(repository.modules)))


def checked_modules(repository, target, *, direct: bool = False) -> tuple:
    """The Modules whose configured checks and revisions a validation of ``target`` covers.

    A direct candidate covers every Module. The Module a managed change is about covers every
    Module the candidate edits since the change's base commit, the owners of changed Spec
    documents and the binders of changed files, so the one candidate is validated as one
    multi-Module change. Every covered Module brings each Module that binds one of its files.
    """
    if direct:
        return tuple(repository.modules.values())
    edited = {target.id}
    change = read_change(repository.root)
    if change and change.get("target_id") == target.id and change.get("base_commit"):
        from ..review.review import changed_paths

        edited.update(
            edited_modules(
                repository, changed_paths(repository.root, change["base_commit"])
            )
        )
    covered = {
        module_id for item in edited for module_id in binding_modules(repository, item)
    }
    return tuple(
        module for module in repository.modules.values() if module.id in covered
    )


def select_target(root, package, data: dict) -> tuple[dict, bool]:
    """Target selection hook of ``concorde-validate``: validation needs an existing change.

    In a linked worktree the request validates that worktree's change, and a linked worktree
    without one is refused with ``missing_change``. Started in the primary worktree or outside
    Git, a request that names no ``change_id`` is refused the same way unless a change is
    registered there, so validation never creates an empty candidate or change; an unknown
    ``change_id`` is refused when the workspace is bound.
    """
    data = bind_module_target(root, package, data, mutates=True)
    primary, current = workspace_identity(root)
    linked = (
        current is not None
        and primary is not None
        and current["path"] != primary["path"]
    )
    if (linked or data.get("change_id") is None) and read_change(root) is None:
        raise SpecError(
            "validation needs an existing change; name its change_id or run it in the change's candidate",
            "missing_change",
            "/change_id",
        )
    return data, True


def run(request) -> dict:
    """Entry point of ``concorde-validate``."""
    invocation = bind(request)
    if request.host.mode == "describe-policy":
        return invocation.response("described")
    return validate(invocation, request.data.get("run_checks", True))


def _withdraw_readiness(run) -> None:
    """Step 1: the change enters ``validate`` and loses any earlier ready state and tree."""
    progress(run.repository.root, phase="validate", status="active")
    change = read_change(run.repository.root)
    if change is not None:
        validation_records(change).update(validated_tree=None, evidence=None)
        save_change(run.repository.root, change)


def _failed(run, outcome: str, answer: str, state: dict | None, results=()) -> dict:
    """A failed validation marks the change, and a planned target's entry, ``blocked``."""
    if state is not None:
        state["status"] = "blocked"
        save_target_state(run.repository.root, state)
    progress(run.repository.root, status="blocked", outcome=outcome)
    # Admission records the request's final lifecycle position from these values.
    run.host.lifecycle.update(status="blocked", outcome=outcome)
    return run.response("failed", answer, checks=list(results))


def validate(run, run_checks: bool = True) -> dict:
    owner = run.owns_change()
    if owner:
        _withdraw_readiness(run)
    change = read_change(run.repository.root)
    if change is not None:
        # A pending entry is removed once its file exists (Protocol 12, CHK.binds.pending-subset).
        # In a candidate the host confirms created files before validating, as delivery does.
        from ..spec.changes import confirm_pending_files

        confirmed, _ = confirm_pending_files(run.repository.root, run.host.package_root)
        if confirmed:
            run.repository = SpecRepository(run.repository.root, run.host.package_root)
            run.target = run.repository.module(run.target.id)
    before_tree = snapshot_tree(run.repository.root) if run.work_directory else None
    direct_candidate = bool(change is not None and not targets(change) and owner)
    planned = change is not None and run.target.id in targets(change)
    state = (
        target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
        if planned
        else None
    )
    report = validate_repository(
        run.repository.root, run.target.id, run.host.package_root
    )
    if report.status != "success":
        # Every structural error is listed; a check-input error names its check, Module and path.
        errors = [
            f"{finding.rule_id} {finding.source}: {finding.message}"
            for finding in report.findings
            if finding.severity == "error"
        ]
        return _failed(
            run,
            "invalid_spec",
            "Spec structure or shared contracts failed deterministic validation."
            + (" " + "; ".join(errors) if errors else ""),
            state,
        )
    checked_targets = checked_modules(
        run.repository, run.target, direct=direct_candidate
    )
    impacts = impact_revisions(run.repository, checked_targets)
    results = (
        [
            result
            for target in checked_targets
            for result in configured_checks(
                run.repository, target, run.host.invocation_id
            )
        ]
        if run_checks
        else []
    )
    if state is not None:
        state.update(
            checks=results,
            implementation_impacts=impacts,
            validation_spec_digest=report.result["source_digest"],
            phase="validate",
            status="active",
        )
        save_target_state(run.repository.root, state)
    run.completed.append("concorde-validate")
    if any(item["status"] != "passed" for item in results):
        return _failed(
            run, "failed_checks", "Deterministic validation failed.", state, results
        )
    if run.work_directory and snapshot_tree(run.repository.root) != before_tree:
        raise SpecError(
            "candidate files changed while checks were running", "stale_evidence"
        )
    current_repository = SpecRepository(run.repository.root, run.host.package_root)
    current_target = current_repository.module(run.target.id)
    current_targets = checked_modules(
        current_repository, current_target, direct=direct_candidate
    )
    if impact_revisions(current_repository, current_targets) != impacts:
        raise SpecError(
            "a using Module or shared implementation changed during validation",
            "stale_evidence",
        )
    run.repository, run.target = current_repository, current_target
    if direct_candidate:
        change = read_change(run.repository.root, required=True)
        validation_records(change)["evidence"] = {
            "target_id": run.target.id,
            "focus_id": run.task.get("focus_id"),
            "task": run.task["task"],
            "constraints": run.task.get("constraints", []),
            "spec_digest": target_revision(run.repository, run.target),
            "source_digest": report.result["source_digest"],
            "checks": results,
        }
        save_change(run.repository.root, change)
        return mark_ready(run)
    if state and state["tasks"] and all(task["complete"] for task in state["tasks"]):
        return mark_ready(run)
    return run.response(
        answer="Deterministic validation passed; semantic completeness is not proven.",
        checks=results,
    )


def mark_ready(run) -> dict:
    before_tree = snapshot_tree(run.repository.root)
    evidence = verify_completion(run)
    if snapshot_tree(run.repository.root) != before_tree:
        raise SpecError(
            "candidate changed during completion verification", "stale_evidence"
        )
    if run.target.id in targets(read_change(run.repository.root, required=True)):
        state = target_state(
            run.repository.root, run.target.id, run.task.get("focus_id")
        )
        state.update(phase="ready", status="ready")
        save_target_state(run.repository.root, state)
    if run.owns_change():
        change = read_change(run.repository.root, required=True)
        change.update(phase="ready", status="ready", outcome="ready")
        validation_records(change)["validated_tree"] = before_tree
        save_change(run.repository.root, change)
    return run.response(
        "ready",
        "Candidate verified. Request delivery from this source or the destination worktree.",
        checks=evidence.get("checks", []),
    )


def verify_completion(run) -> dict:
    """Read current target evidence; delivery remains a separate top-level action."""
    from ..review.review import verify_required

    verify_required(run)
    change = read_change(run.repository.root, required=True)
    if any(
        item["target_id"] == run.target.id
        and item["scope_id"] == blocker_scope(change, run.target.id, run.task["task"])
        for item in open_gaps(change)
    ):
        raise SpecError(
            "current task still has unresolved contract gaps", "spec_incomplete"
        )
    if not targets(change):
        validation = direct_evidence(change)
        if (
            not validation
            or validation["target_id"] != run.target.id
            or validation["focus_id"] != run.task.get("focus_id")
            or validation["task"] != run.task["task"]
            or validation["constraints"] != run.task.get("constraints", [])
        ):
            raise SpecError(
                "direct candidate has no bound validation evidence",
                "stale_evidence",
            )
        report = validate_repository(
            run.repository.root, package_root=run.host.package_root
        )
        if (
            report.status != "success"
            or validation["source_digest"] != report.result["source_digest"]
            or validation["spec_digest"] != target_revision(run.repository, run.target)
        ):
            raise SpecError(
                "direct candidate Spec validation is stale", "stale_evidence"
            )
        required = {
            check_id
            for target in run.repository.modules.values()
            for check_id in target.checks
        }
        if {item["check_id"] for item in validation["checks"]} != required or any(
            item["status"] != "passed"
            or item["source_digest"]
            != check_revision(run.repository, run.repository.module(item["target_id"]))
            for item in validation["checks"]
        ):
            raise SpecError(
                "direct candidate checks are missing, failed, or stale",
                "stale_evidence",
            )
        return validation
    state = target_state(run.repository.root, run.target.id, run.task.get("focus_id"))
    run.check_state(state)
    for target_id, revision in state.get("component_revisions", {}).items():
        component = run.repository.module(target_id)
        if revision != {
            "spec": target_revision(run.repository, component),
            "implementation": implementation_digest(run.repository, component),
        }:
            raise SpecError(
                "a completed component changed before coordinated delivery",
                "stale_evidence",
            )
        component_state = target_state(run.repository.root, target_id, None)
        payload = {
            "target_id": target_id,
            "task": component_state["task"],
            "constraints": component_state.get("constraints", []),
            "change_id": run.change_id,
        }
        verify_completion(
            Invocation("concorde-validate", run.configuration, payload, run.host)
        )
    if not state["tasks"] or any(not task["complete"] for task in state["tasks"]):
        raise SpecError("delivery requires completed tasks", "incomplete_change")
    if state["implementation_digest"] != implementation_digest(
        run.repository, run.target
    ):
        raise SpecError("implementation changed since completion", "stale_evidence")
    report = validate_repository(
        run.repository.root, run.target.id, run.host.package_root
    )
    if (
        report.status != "success"
        or state.get("validation_spec_digest") != report.result["source_digest"]
    ):
        raise SpecError("Spec validation is missing or stale", "stale_evidence")
    affected = checked_modules(run.repository, run.target)
    if state.get("implementation_impacts") != impact_revisions(
        run.repository, affected
    ):
        raise SpecError(
            "shared implementation consumer evidence is missing or stale",
            "stale_evidence",
        )
    required_checks = {key for target in affected for key in target.checks}
    if {item["check_id"] for item in state["checks"]} != required_checks or any(
        item["status"] != "passed"
        or item["source_digest"]
        != check_revision(run.repository, run.repository.module(item["target_id"]))
        for item in state["checks"]
    ):
        raise SpecError(
            "required implementation checks are missing, failed, or stale",
            "stale_evidence",
        )
    return state
