"""Pending gaps: blockers an accepted step recorded, which stop later steps until repaired.

A pending gap is recorded per change, target Module, work scope, step and Issue, bound to the
step's revision. Preparing a plan, task or implementation step returns ``spec_incomplete`` while a
gap of the same step is bound to the current revision or a gap of an earlier step is open for the
same Module and work scope. The collaboration pre-check of the context assessor also lives here.
"""

from __future__ import annotations

from ..harness.change_worktree import (
    blocker_scope,
    read_change,
    record_task_gaps,
    unchanged_task_gaps,
)
from ..harness.revisions import implementation_digest, target_revision
from ..spec.repository import digest
from ..spec.validation import MISSING_PROMISES, module_dependency_findings

# The steps in order; a gap of an earlier step blocks every later one.
STEPS = (
    "spec-review",
    "context-solve",
    "plan",
    "tasks",
    "implementation",
    "code-review",
)
# The capabilities whose own gaps are recorded only for a tracked or required step.
READ_ONLY_STAGES = frozenset(
    {"concorde-context-solve", "concorde-spec-review", "concorde-code-review"}
)


def blocker_revision(run, phase: str) -> str:
    """The revision a gap of ``phase`` is bound to."""
    spec = target_revision(run.repository, run.target)
    return (
        digest(
            {"spec": spec, "code": implementation_digest(run.repository, run.target)}
        )
        if phase in {"implementation", "code-review"}
        else spec
    )


def _intent(run) -> dict:
    return {
        "task": run.task["task"],
        "focus_id": run.task.get("focus_id"),
        "constraints": run.task.get("constraints", []),
    }


def record_gaps(run, phase: str, blockers, *, review_input_digest=None) -> None:
    """Record an accepted step's blockers as open gaps and resolve the step's outdated ones."""
    if run.host.mode != "execute":
        return
    change = read_change(run.repository.root)
    intent = _intent(run)
    required_review = bool(
        phase in {"spec-review", "code-review"}
        and change
        and change.get("review_requirements", {})
        .get(run.target.id, {})
        .get(phase.split("-")[0])
        and change.get("review_intents", {}).get(run.target.id) == intent
    )
    assessment_intent = False
    if phase == "context-solve" and change:
        records = [
            change if change.get("target_id") == run.target.id else {},
            change.get("targets", {}).get(run.target.id, {}),
            change.get("review_intents", {}).get(run.target.id, {}),
        ]
        for name in ("shared_spec_reviews", "shared_implementation_reviews"):
            records.extend(
                consumers.get(run.target.id, {})
                for consumers in change.get(name, {}).values()
            )
        assessment_intent = any(
            {
                key: record.get(key, [] if key == "constraints" else None)
                for key in intent
            }
            == intent
            for record in records
        )
        if not assessment_intent:
            return
    if (
        run.host.track_gaps
        or assessment_intent
        or required_review
        or run.operation not in READ_ONLY_STAGES
    ):
        record_task_gaps(
            run.repository.root,
            run.target.id,
            run.task["task"],
            phase,
            blockers,
            blocker_revision(run, phase),
            review_input_digest=review_input_digest,
            spec_resolution=run.repository.spec_context(run.target.id).value,
        )


def pending_gaps(
    run, phase: str, *, include_prerequisites=True, review_input_digest=None
) -> list[dict]:
    """The blockers that stop ``phase`` for this request, in execute mode."""
    if run.host.mode != "execute":
        return []
    blockers = unchanged_task_gaps(
        run.repository.root,
        run.target.id,
        run.task["task"],
        phase,
        blocker_revision(run, phase),
        review_input_digest=review_input_digest,
    )
    if include_prerequisites:
        prerequisites = set(STEPS[: STEPS.index(phase)]) if phase in STEPS else set()
        change = read_change(run.repository.root)
        blockers.extend(
            dict(item["blocker"])
            for item in (change or {}).get("issue_blockers", [])
            if item["status"] == "open"
            and item["target_id"] == run.target.id
            and item["scope_id"]
            == blocker_scope(change or {}, run.target.id, run.task["task"])
            and item["phase"] in prerequisites
        )
    return blockers


def assessment_dependencies(run, snapshot, operation="concorde-context-solve"):
    """The collaboration pre-check of the context assessor, before any model runs.

    A collaboration whose promises do not resolve records a gap Issue per finding and stops with
    ``spec_incomplete``; any other structural finding about the Module's own relations stops with
    ``conflicting``. Returns the stage result that ends the step, or None.
    """
    findings = module_dependency_findings(run.repository, run.target.id)
    if not findings:
        return None
    run.completed.append(operation)
    conflicts = [
        finding
        for finding in findings
        if not finding.message.startswith(MISSING_PROMISES)
    ]
    if conflicts:
        return {
            "context_id": snapshot.id,
            "outcome": "conflicting",
            "answer": "Module dependency promises conflicts with its registered topology: "
            + "; ".join(finding.message for finding in conflicts),
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
        }
    from ..issues.store import report_issue

    blockers = []
    for finding in findings:
        receipt = report_issue(
            run.repository.root,
            {
                "report_key": digest([run.target.id, finding.rule_id, finding.message]),
                "type": "gap",
                "subtype": "missing-contract",
                "title": "Missing dependency promise",
                "description": finding.message,
                "impact": "Context assessment cannot admit planning.",
                "basis": finding.remediation,
                "owner_target_id": run.target.id,
                "evidence": [],
            },
            {
                "invocation_id": run.host.invocation_id,
                "agent": "host",
                "operation": operation,
                "phase": "context-solve",
                "target_id": run.target.id,
                "context_id": snapshot.id,
                "change_id": run.change_id,
                "head": None,
            },
        )
        blockers.append(
            {
                **receipt,
                "blocked_step": "Assess context sufficiency before Module planning",
            }
        )
    record_gaps(run, "context-solve", blockers)
    return {
        "context_id": snapshot.id,
        "outcome": "spec_incomplete",
        "answer": "Module dependency promises is incomplete or inconsistent.",
        "blockers": blockers,
        "documents": [],
        "plan": "",
        "tasks": [],
    }
