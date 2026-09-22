"""Deterministic validation of a candidate and the readiness gates that consume its evidence."""

from __future__ import annotations

from dataclasses import replace

from ..harness.change_worktree import (
    blocker_scope,
    progress,
    read_change,
    save_change,
    save_target_state,
    snapshot_tree,
    target_state,
)
from ..harness.checks import check_revision, configured_checks
from ..harness.invocation import Invocation
from ..harness.revisions import (
    impact_revisions,
    implementation_digest,
    implementation_users,
    issues_revision,
    target_revision,
)
from ..spec.repository import SpecError, SpecRepository
from ..spec.validation import validate_repository


def validate(run, run_checks: bool = True) -> dict:
    if not run.host.coordinated:
        progress(
            run.repository.root, phase="validate", status="active", invalidate=True
        )
    change = read_change(run.repository.root)
    if change is not None:
        # A pending entry is removed once its file exists (Protocol 11, CHK.binds.pending-subset).
        # In a candidate the host confirms created files before validating, as delivery does.
        from ..spec.changes import confirm_pending_files

        confirmed, _ = confirm_pending_files(run.repository.root, run.host.package_root)
        if confirmed:
            run.repository = SpecRepository(run.repository.root, run.host.package_root)
            run.target = run.repository.select(run.target.id)
    before_tree = snapshot_tree(run.repository.root) if run.work_directory else None
    direct_candidate = bool(
        change is not None and not change["targets"] and not run.host.coordinated
    )
    report = validate_repository(
        run.repository.root, run.target.id, run.host.package_root
    )
    if report.status != "success":
        progress(run.repository.root, status="blocked", outcome="invalid_spec")
        input_errors = [
            finding.message
            for finding in report.findings
            if finding.rule_id == "CONCORDE-CHECK-001"
        ]
        return run.response(
            "failed",
            "Spec structure or shared contracts failed deterministic validation."
            + (" " + "; ".join(input_errors) if input_errors else ""),
        )
    checked_targets = (
        tuple(run.repository.targets.values())
        if direct_candidate
        else implementation_users(run.repository, run.target)
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
    state = None
    if change and run.target.id in change["targets"]:
        state = target_state(
            run.repository.root, run.target.id, run.task.get("focus_id")
        )
        state.update(
            checks=results,
            implementation_impacts=impacts,
            validation_spec_digest=report.result["source_digest"],
            validation_issue_digest=issues_revision(run.repository.root),
            phase="validate",
            status="active",
        )
        save_target_state(run.repository.root, state)
    run.completed.append("concorde-validate")
    failed = any(item["status"] != "passed" for item in results)
    if failed:
        if state is not None:
            state["status"] = "blocked"
            save_target_state(run.repository.root, state)
        return run.response(
            "failed", "Deterministic validation failed.", checks=results
        )
    if run.work_directory and snapshot_tree(run.repository.root) != before_tree:
        raise SpecError(
            "candidate files changed while checks were running", "stale_evidence"
        )
    current_repository = SpecRepository(run.repository.root, run.host.package_root)
    current_target = current_repository.select(run.target.id)
    current_targets = (
        tuple(current_repository.targets.values())
        if direct_candidate
        else implementation_users(current_repository, current_target)
    )
    if impact_revisions(current_repository, current_targets) != impacts:
        raise SpecError(
            "a using Module or shared implementation changed during validation",
            "stale_evidence",
        )
    run.repository, run.target = current_repository, current_target
    if direct_candidate:
        change = read_change(run.repository.root, required=True)
        change["validation"] = {
            "target_id": run.target.id,
            "focus_id": run.task.get("focus_id"),
            "task": run.task["task"],
            "constraints": run.task.get("constraints", []),
            "spec_digest": target_revision(run.repository, run.target),
            "source_digest": report.result["source_digest"],
            "checks": results,
        }
        save_change(run.repository.root, change)
        if run.host.defer_ready:
            return run.response(
                answer="Deterministic checks completed; required review precedes readiness.",
                checks=results,
            )
        return mark_ready(run)
    if state and state["tasks"] and all(task["complete"] for task in state["tasks"]):
        if run.host.defer_ready:
            return run.response(
                answer="Deterministic checks completed; required review precedes readiness.",
                checks=results,
            )
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
    change = read_change(run.repository.root, required=True)
    if run.target.id in change["targets"]:
        change["targets"][run.target.id].update(phase="ready", status="ready")
    if not run.host.coordinated:
        change.update(
            phase="ready",
            status="ready",
            outcome="ready",
            validated_tree=before_tree,
        )
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
        item["status"] == "open"
        and item["target_id"] == run.target.id
        and item["scope_id"] == blocker_scope(change, run.target.id, run.task["task"])
        for item in change.get("issue_blockers", [])
    ):
        raise SpecError(
            "current task still has unresolved contract gaps", "spec_incomplete"
        )
    if not change["targets"]:
        validation = change.get("validation")
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
            for target in run.repository.targets.values()
            for check_id in target.checks
        }
        if {item["check_id"] for item in validation["checks"]} != required or any(
            item["status"] != "passed"
            or item["source_digest"]
            != check_revision(run.repository, run.repository.select(item["target_id"]))
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
        component = run.repository.select(target_id)
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
            Invocation(
                "concorde-validate",
                run.configuration,
                payload,
                replace(run.host, coordinated=True),
            )
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
    affected = implementation_users(run.repository, run.target)
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
        != check_revision(run.repository, run.repository.select(item["target_id"]))
        for item in state["checks"]
    ):
        raise SpecError(
            "required implementation checks are missing, failed, or stale",
            "stale_evidence",
        )
    return state
