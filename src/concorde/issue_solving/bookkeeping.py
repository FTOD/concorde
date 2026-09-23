"""The binding step and the bookkeeping actions of ``concorde-issues``, and the journal check.

The binding step runs before admission chooses a worktree: it binds a selected Issue's owner and
revision, refuses a solve of an uncommitted Issue and finds an unfinished close. The bookkeeping
actions ``list``, ``show``, ``report`` and ``reopen``, and ``solve`` of an already closed Issue, are
Host services that run in place without a Workflow.
"""

from __future__ import annotations

from pathlib import Path

from ..harness.change_worktree import git, read_change, workspace_identity
from ..issues.store import (
    MAX_RECORD_BYTES,
    dispose_issue,
    issue_path,
    list_issues,
    parse,
    read_issue,
    validate_report,
)
from ..spec.repository import SpecError, SpecRepository, digest
from ..spec.typed_data import typed
from .records import solutions

MAX_DECISIONS = 6
DECISION_ROUTES = {
    "develop": "finish",
    "spec-repair": "finish",
    "verify": "verify",
    "resolved": "close",
    "duplicate": "close",
    "not-actionable": "close",
    "needs-decision": "finish",
}
JOURNAL_FIELDS = {
    "schema_version",
    "change_id",
    "issue_id",
    "before",
    "before_digest",
    "after",
    "after_digest",
}


def pending_disposition(change: dict | None, identifier: str) -> dict | None:
    """Validate a candidate-local write-ahead record before it can authorize any restoration."""
    solution = solutions(change).get(identifier) or {}
    if "pending_disposition" not in solution:
        return None
    journal = solution["pending_disposition"]
    try:
        if (
            not isinstance(journal, dict)
            or set(journal) != JOURNAL_FIELDS
            or type(journal["schema_version"]) is not int
            or journal["schema_version"] != 1
            or journal["change_id"] != (change or {}).get("change_id")
            or journal["issue_id"] != identifier
        ):
            raise ValueError("pending disposition identity is invalid")
        for name in ("before", "after"):
            text = journal[name]
            if (
                not isinstance(text, str)
                or len(text.encode()) > MAX_RECORD_BYTES
                or digest(text.encode()) != journal[name + "_digest"]
            ):
                raise ValueError("pending disposition bytes do not match their digest")
        before, after = (
            parse(journal["before"], identifier),
            parse(journal["after"], identifier),
        )
        if (
            before["status"] != "open"
            or after["status"] != "closed"
            or len(after["dispositions"]) != len(before["dispositions"]) + 1
            or {**after, "status": "open", "dispositions": after["dispositions"][:-1]}
            != before
            or after["dispositions"][-1]["actor"] != "concorde-issue-solver"
            or solution["revision"] != journal["before_digest"]
        ):
            raise ValueError(
                "pending disposition is not this solve's single closing write"
            )
    except (ValueError, KeyError, TypeError) as error:
        raise SpecError(
            f"invalid pending Issue disposition: {error}", "invalid_worktree_state"
        ) from error
    return journal


def prepare_request(root: Path, package: Path, task: dict) -> dict:
    """Bind the explicit selection before workspace creation, without mutating either worktree."""
    task = dict(task)
    action = task["action"]
    repository = SpecRepository(root, package)
    task["_issue_filter"] = task.get("target_id")
    if action in {"show", "solve", "reopen"}:
        if "issue_id" not in task:
            raise SpecError(
                "this action requires an explicit issue_id", "invalid_input"
            )
        record, revision = read_issue(root, task["issue_id"])
        change = read_change(root) if action == "solve" else None
        journal = pending_disposition(change, task["issue_id"])
        if journal is not None:
            versions = {journal["before_digest"], journal["after_digest"]}
            if (
                revision not in versions
                or task.get("expected_revision", revision) not in versions
            ):
                raise SpecError(
                    "Issue changed outside the pending disposition; preserve it for reconciliation",
                    "stale_issue",
                )
            task["_issue_recovery"] = True
            if change is None:
                raise SpecError(
                    "pending disposition requires its owning change",
                    "invalid_worktree_state",
                )
            for field in ("task", "constraints", "focus_id", "change_id"):
                if change.get(field) is not None:
                    task.setdefault(field, change[field])
        elif task.get("expected_revision", revision) != revision:
            raise SpecError("selected Issue has changed", "stale_issue")
        elif record["status"] == "closed" and change:
            solution = solutions(change).get(task["issue_id"]) or {}
            closing = record["dispositions"][-1]
            contexts = {item.get("context_id") for item in solution.get("history", [])}
            if (
                solution
                and solution.get("status") != "completed"
                and closing["actor"] == "concorde-issue-solver"
                and contexts.intersection(closing["evidence"])
            ):
                raise SpecError(
                    "unfinished Issue disposition has no recovery journal; reconcile it explicitly",
                    "invalid_worktree_state",
                )
        task["_issue_closed"] = record["status"] == "closed" and journal is None
        latest = record["reports"][-1]
        owner = latest["report"]["owner_target_id"] or latest["source"]["target_id"]
        if task.get("target_id", owner) != owner:
            raise SpecError(
                "Issue selection cannot grant another Module's authority",
                "permission_denied",
            )
        task["target_id"] = owner
        task["expected_revision"] = revision
        if action in {"solve", "reopen"}:
            # Only a registered owner can be solved or reopened; showing it needs none.
            repository.module(owner)
        task.setdefault(
            "task",
            f"Resolve Issue {record['id']}: {latest['report']['title']}\n"
            f"Problem: {latest['report']['description']}\nImpact: {latest['report']['impact']}",
        )
    elif action == "report":
        if "target_id" not in task or "report" not in task:
            raise SpecError(
                "report requires target_id and a classified report", "invalid_input"
            )
        validate_report(task["report"])
    if "report" in task and action != "report":
        raise SpecError("report is only accepted by its own action", "invalid_input")
    if action == "reopen" and not task.get("note", "").strip():
        raise SpecError("reopen requires a rationale", "invalid_input")
    task.setdefault("target_id", repository.root_module)
    task.setdefault("task", "Inspect project Issues")
    return task


def require_committed(root: Path, issue_id: str) -> None:
    """Refuse a solve of an Issue whose record is not committed, unchanged, at ``HEAD``."""
    _, current = workspace_identity(root)
    if current is None:
        return
    relative = issue_path(issue_id)
    committed = git(
        root, "rev-parse", "--verify", "--quiet", f"HEAD:{relative}", check=False
    )
    working = git(root, "hash-object", "--", relative, check=False)
    if (
        committed.returncode != 0
        or working.returncode != 0
        or committed.stdout.strip() != working.stdout.strip()
    ):
        raise SpecError(
            "only an Issue committed unchanged at HEAD can be solved; commit it first",
            "uncommitted_issue",
        )


def select_target(root: Path, package: Path, data: dict) -> tuple[dict, bool]:
    """Target selection hook of ``concorde-issues``: bind the Issue before a worktree is chosen.

    Returns the bound request and whether it mutates: only ``solve`` of an open Issue does.
    ``list`` and ``show`` need no registered Module, so an Issue of a removed Module can still
    be inspected.
    """
    from ..harness.admission import bind_module_target

    task = prepare_request(root, package, data)
    mutates = task["action"] == "solve" and not task.get("_issue_closed")
    if mutates and not task.get("_issue_recovery"):
        require_committed(root, task["issue_id"])
    if task["action"] in {"list", "show"}:
        return task, False
    return bind_module_target(root, package, task, mutates=mutates), mutates


def response(
    request, outcome="completed", answer="", records=(), decision=None
) -> dict:
    """The ``concorde-issues`` response of a request that runs no Workflow."""
    task = request.data
    change = read_change(request.host.project_root)
    return typed(
        "concorde-issues-response",
        {
            "target_id": task["target_id"],
            "focus_id": task.get("focus_id"),
            "change_id": task.get("change_id")
            or (change["change_id"] if change else None),
            "context_id": None,
            "outcome": outcome,
            "answer": answer,
            "blockers": [],
            "checks": [],
            "artifacts": [],
            "completed_operations": [],
            "issues": list(records),
            "decision": decision,
        },
    )


def _report(request) -> dict:
    """Save the developer's report through a reporting service bound to the reporting Module."""
    from ..issues.reporting import IssueReporter

    root, task = request.host.project_root, request.data
    repository = SpecRepository(root, request.host.package_root)
    target = repository.module(task["target_id"])
    context = repository.spec_context(target.id).value
    sources = context["sources"]
    change = read_change(root)
    service = IssueReporter(
        root,
        {
            "invocation_id": request.host.invocation_id,
            "agent": "developer",
            "operation": request.operation,
            "phase": "report",
            "target_id": target.id,
            "context_id": digest(context),
            "change_id": task.get("change_id")
            or (change["change_id"] if change else None),
            "head": None,
        },
        frozenset({target.id, *target.uses, *(item["owner"] for item in sources)}),
        frozenset(
            {*(item["path"] for item in sources), *repository.bound_files(target)}
        ),
        frozenset({task["report"]["issue_id"]})
        if "issue_id" in task["report"]
        else frozenset(),
    )
    return service(task["report"])


def serve(request) -> dict:
    """Serve a bookkeeping action, or the solve of an already closed Issue, in place."""
    root, task = request.host.project_root, request.data
    action = task["action"]
    if request.host.mode == "describe-policy":
        return response(
            request, "described", "Host bookkeeping only; no worker is launched."
        )
    if action == "solve":
        return response(
            request,
            answer="Issue is already disposed in this branch; no work was replayed.",
            records=[read_issue(root, task["issue_id"])[0]],
            decision="already-closed",
        )
    if action == "report":
        result = _report(request)
        return response(
            request,
            answer="Issue recorded without changing task execution.",
            records=[read_issue(root, result["receipt"]["issue_id"])[0]],
        )
    if action == "reopen":
        dispose_issue(
            root,
            task["issue_id"],
            task["expected_revision"],
            reason="reopened",
            note=task["note"],
            evidence=["Explicit developer request"],
            actor="developer",
        )
        return response(
            request,
            answer="Issue reopened in this branch.",
            records=[read_issue(root, task["issue_id"])[0]],
        )
    records = (
        [read_issue(root, task["issue_id"])[0]]
        if action == "show"
        else [
            read_issue(root, row["id"])[0]
            for row in list_issues(root, target_id=task["_issue_filter"])
        ]
    )
    return response(
        request,
        answer="Branch-local Issues; no repair or disposition was performed.",
        records=records,
    )
