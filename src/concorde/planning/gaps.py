"""Pending gaps: blockers an accepted step recorded, which stop later steps until repaired.

A pending gap is recorded per change, target Module, work scope, step and Issue, bound to the
step's revision. Preparing a plan, task or implementation step returns ``spec_incomplete`` while a
gap of the same step is bound to the current revision or a gap of an earlier step is open for the
same Module and work scope. The collaboration pre-check of the context assessor also lives here.
"""

from __future__ import annotations

from pathlib import Path

from ..harness.change_worktree import read_change, save_change
from ..harness.revisions import implementation_digest, target_revision
from ..review.records import recorded
from ..spec.repository import digest
from ..spec.validation import MISSING_PROMISES, module_dependency_findings
from .records import gap_history, planning_records, targets

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


def open_gaps(change: dict | None) -> list[dict]:
    """The open pending gaps of ``change``, in recording order."""
    return [item for item in gap_history(change) if item["status"] == "open"]


def blocker_scope(state: dict, target_id: str, task: str | None) -> str | None:
    """Bind a request to accepted candidate work, not an ID hashed from task wording.

    Root intent, evolving component intent and required consumer review intent all select the
    same durable Module work scope. A separately requested unrelated task cannot borrow it.
    """
    if task is None:
        return "module:" + target_id
    intents = []
    if state.get("target_id") == target_id:
        intents.append(state.get("task"))
    intents.append(targets(state).get(target_id, {}).get("task"))
    intents.append(recorded(state, "intents").get(target_id, {}).get("task"))
    for name in ("shared_spec_reviews", "shared_implementation_reviews"):
        for consumers in recorded(state, name).values():
            intents.append(consumers.get(target_id, {}).get("task"))
    if task in intents:
        return "module:" + target_id
    return next(
        (
            item["scope_id"]
            for item in gap_history(state)
            if item["target_id"] == target_id and item["task"] == task
        ),
        None,
    )


def record_task_gaps(
    root: Path,
    target_id: str,
    task: str,
    phase: str,
    blockers,
    spec_digest: str,
    *,
    review_input_digest: str | None = None,
    spec_resolution: dict | None = None,
    scope_id: str | None = None,
) -> None:
    """Retain Issue dependencies by change/Module/phase/Issue, never by task wording.

    A successful fresh assessment releases a dependency, not the referenced Issue. Reports and
    their immutable observations survive independently. Caller admission protects unrelated review
    intents; one candidate has one evolving work scope for each participating Module. Recording a
    blocker withdraws the change's ready state.
    """
    from ..issues.references import receipt, requires_contract_repair
    from ..issues.store import resolve_report

    state = read_change(root)
    if state is None:
        return
    history = planning_records(state)["gaps"]
    scope_id = scope_id or blocker_scope(state, target_id, task)
    if scope_id is None:
        if not blockers:
            return
        scope_id = (
            "independent:"
            + resolve_report(root, receipt(blockers[0]))["source"]["invocation_id"]
        )
    existing = {item["id"]: item for item in history}
    for blocker in blockers:
        observation = resolve_report(root, receipt(blocker))
        context_id = observation["source"]["context_id"]
        key = digest(
            {
                "change_id": state["change_id"],
                "target_id": target_id,
                "scope_id": scope_id,
                "phase": phase,
                "issue_id": blocker["issue_id"],
            }
        )
        if key not in existing:
            item = {
                "id": key,
                "target_id": target_id,
                "task": task,
                "phase": phase,
                "scope_id": scope_id,
                "blocker": dict(blocker),
                "status": "open",
                "contexts": [],
                "spec_digest": spec_digest,
            }
            history.append(item)
            existing[key] = item
        item = existing[key]
        item.update(
            blocker=dict(blocker), task=task, status="open", spec_digest=spec_digest
        )
        if spec_resolution is not None:
            evidence = {
                key: value for key, value in spec_resolution.items() if key != "sources"
            }
            evidence["sources"] = [
                {key: value for key, value in source.items() if key != "content"}
                for source in spec_resolution["sources"]
            ]
            item.setdefault("context_evidence", {})[context_id] = evidence
        if review_input_digest is not None:
            item["review_input_digest"] = review_input_digest
        if context_id not in item["contexts"]:
            item["contexts"].append(context_id)
    for item in history:
        if (
            item["target_id"] == target_id
            and item["scope_id"] == scope_id
            and item["status"] == "open"
            and item["phase"] == phase
            and not blockers
            and (
                item.get("spec_digest") != spec_digest
                or (
                    review_input_digest is not None
                    and item.get("review_input_digest") != review_input_digest
                )
                or (
                    phase in {"spec-review", "code-review"}
                    and not requires_contract_repair(root, [item["blocker"]])
                )
            )
        ):
            item["status"] = "resolved"
    if blockers and state["status"] == "ready":
        state.update(status="active", outcome=None)
    save_change(root, state)


def unchanged_task_gaps(
    root: Path,
    target_id: str,
    task: str,
    phase: str,
    spec_digest: str,
    *,
    review_input_digest: str | None = None,
) -> list[dict]:
    """The open gaps of ``phase`` for this Module and work scope bound to the current revision."""
    from ..issues.references import requires_contract_repair

    state = read_change(root)
    scope = blocker_scope(state or {}, target_id, task)
    return [
        dict(item["blocker"])
        for item in open_gaps(state)
        if item["target_id"] == target_id
        and item["scope_id"] == scope
        and item["phase"] == phase
        and item.get("spec_digest") == spec_digest
        and (
            phase != "code-review" or requires_contract_repair(root, [item["blocker"]])
        )
        and (
            review_input_digest is None
            or phase not in {"spec-review", "code-review"}
            or item.get("review_input_digest") == review_input_digest
        )
    ]


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
        and recorded(change, "requirements")
        .get(run.target.id, {})
        .get(phase.split("-")[0])
        and recorded(change, "intents").get(run.target.id) == intent
    )
    assessment_intent = False
    if phase == "context-solve" and change:
        records = [
            change if change.get("target_id") == run.target.id else {},
            targets(change).get(run.target.id, {}),
            recorded(change, "intents").get(run.target.id, {}),
        ]
        for name in ("shared_spec_reviews", "shared_implementation_reviews"):
            records.extend(
                consumers.get(run.target.id, {})
                for consumers in recorded(change, name).values()
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
    if assessment_intent or required_review or run.operation not in READ_ONLY_STAGES:
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
            for item in open_gaps(change)
            if item["target_id"] == run.target.id
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
