"""Finite Issue bookkeeping, selection and journal predicates; native solve is separate."""

from __future__ import annotations

from pathlib import Path

from ..spec.changes import apply_files
from ..spec.repository import SpecError, SpecRepository, digest, read_file
from .store import (
    MAX_RECORD_BYTES,
    dispose_issue,
    issue_path,
    list_issues,
    parse,
    read_issue,
    validate_report,
)

END = "__end__"

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
NODES = (
    "select_operation",
    "inspect",
    "report",
    "reopen",
    "prepare",
    "decide",
    "verify",
    "close",
    "ready",
    "finish",
)


def pending_disposition(change: dict | None, identifier: str) -> dict | None:
    """Validate a candidate-local write-ahead record before it can authorize any restoration."""
    solution = (change or {}).get("issue_solutions", {}).get(identifier) or {}
    if "pending_disposition" not in solution:
        return None
    journal = solution["pending_disposition"]
    try:
        if (
            not isinstance(journal, dict)
            or set(journal)
            != {
                "schema_version",
                "change_id",
                "issue_id",
                "before",
                "before_digest",
                "after",
                "after_digest",
            }
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
        from ..harness.change_worktree import read_change

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
            solution = change.get("issue_solutions", {}).get(task["issue_id"]) or {}
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
    for field in ("report",):
        if field in task and action != field:
            raise SpecError(
                f"{field} is only accepted by its own action", "invalid_input"
            )
    if action == "reopen" and not task.get("note", "").strip():
        raise SpecError("reopen requires a rationale", "invalid_input")
    task.setdefault("target_id", repository.entry_target)
    repository.select(task["target_id"], task.get("focus_id"))
    task.setdefault("task", "Inspect project Issues")
    return task


def copy_selection(source: Path, destination: Path, task: dict) -> None:
    """Carry only the selected exact Issue into a host-created candidate, including uncommitted reports."""
    relative = issue_path(task["issue_id"])
    raw = read_file(source, relative)
    if digest(raw) != task["expected_revision"]:
        raise SpecError("Issue changed while preparing its candidate", "stale_issue")
    target = destination / relative
    before = digest(read_file(destination, relative)) if target.exists() else None
    apply_files(
        destination,
        [{"path": relative, "before_digest": before, "content": raw.decode()}],
        {relative},
    )


def issue_nodes(run):
    """Finite bookkeeping only. Solve preparation is a separate native service."""
    root, task = run.repository.root, run.task
    identifier = task.get("issue_id", "")

    def response(
        outcome="completed", answer="", disposition=None, records=(), **kwargs
    ):
        result = run.response(outcome, answer, **kwargs)
        result["data"].update(issues=list(records), decision=disposition)
        return result

    def select_operation(state):
        return {
            "route": {
                "list": "inspect",
                "show": "inspect",
                "report": "report",
                "reopen": "reopen",
                "solve": "prepare",
            }[task["action"]]
        }

    def inspect(state):
        records = (
            [read_issue(root, identifier)[0]]
            if identifier
            else [
                read_issue(root, row["id"])[0]
                for row in list_issues(root, target_id=task["_issue_filter"])
            ]
        )
        return {
            "output": response(
                answer="Branch-local Issues; no repair or disposition was performed.",
                records=records,
            )
        }

    def report(state):
        from .reporting import IssueReporter

        context = run.repository.spec_context(run.target.id).value
        sources = context["sources"]
        service = IssueReporter(
            root,
            {
                "invocation_id": run.host.invocation_id,
                "agent": "developer",
                "operation": run.operation,
                "phase": "report",
                "target_id": run.target.id,
                "context_id": digest(context),
                "change_id": run.change_id,
                "head": None,
            },
            frozenset(
                {run.target.id, *run.target.uses, *(item["owner"] for item in sources)}
            ),
            frozenset(
                {
                    *(item["path"] for item in sources),
                    *run.repository.implementation_files(run.target),
                }
            ),
            frozenset({task["report"]["issue_id"]})
            if "issue_id" in task["report"]
            else frozenset(),
        )
        result = service(task["report"])
        return {
            "output": response(
                answer="Issue recorded without changing task execution.",
                records=[read_issue(root, result["receipt"]["issue_id"])[0]],
            )
        }

    def reopen(state):
        dispose_issue(
            root,
            identifier,
            task["expected_revision"],
            reason="reopened",
            note=task["note"],
            evidence=["Explicit developer request"],
            actor="developer",
        )
        return {
            "output": response(
                answer="Issue reopened in this branch.",
                records=[read_issue(root, identifier)[0]],
            )
        }

    return {
        "select_operation": select_operation,
        "inspect": inspect,
        "report": report,
        "reopen": reopen,
    }
