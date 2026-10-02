"""What every review provider does with the project's Issues, the review's memory.

Before a review judges a Module, the host reads the Module's earlier Issues: its open Issues one of
whose reports one of the review's Operations made. The review reports only what is new or what
changed in an earlier Issue (naming it as ``earlier``) and lists the earlier Issues the Module no
longer has as ``resolved``; an earlier Issue it neither names nor resolves is carried and still
stands. The host, never a worker, then reports every finding through the Issue store: a finding
that names an offered earlier Issue is appended to it at the revision read just before, any other
creates an Issue. It never closes an Issue, and a refusal of the store stops the Module's reporting
with the store's error link as the cause, never as an Issue.

Each review supplies only what differs: which Operations made its earlier Issues, which findings
it reports nowhere, and the Issue report of one finding.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from ..execution.context import RunContext, Stop, evidence
from ..issues import command as issue_command
from ..issues.store import list_issues, project_root, read_issue, report_issue

# A finding the review reports nowhere, such as one its checker disputed.
Skipped = Callable[[dict], bool]


def _never(finding: dict) -> bool:
    return False


def earlier_issues(
    ctx: RunContext, module: str, operations: Iterable[str]
) -> list[dict]:
    """The Module's open Issues one of ``operations`` reported, each as its latest report states
    it; raises ``issue_command.Refusal`` when the project's Issues cannot be read."""
    operations = set(operations)
    root = issue_command.guarded(project_root, ctx.started_in)
    found = []
    for row in issue_command.guarded(
        list_issues, root, target_id=module, status="open"
    ):
        if (row["owner_target_id"] or row["target_id"]) != module:
            continue
        record, _ = issue_command.guarded(read_issue, root, row["id"])
        if not any(
            item["source"]["operation"] in operations for item in record["reports"]
        ):
            continue
        latest = record["reports"][-1]["report"]
        found.append(
            {
                "issue": record["id"],
                "severity": latest.get("severity"),
                "tier": latest.get("tier"),
                "title": latest["title"],
                "description": latest["description"],
                "evidence": latest["evidence"],
            }
        )
    return found


def settle(
    earlier: list[dict],
    findings: list[dict],
    resolved: list[dict],
    *,
    skipped: Skipped = _never,
    unoffered: str = "a finding names no earlier Issue offered",
) -> dict:
    """Which offered earlier Issue each finding names and which the review resolves.

    A finding keeps ``earlier`` only when it names an offered Issue no other finding named and it
    is not ``skipped``, whose Issue is carried; a resolution counts only for an offered Issue no
    finding named and none resolved before. Every other name is listed under ``ignored``, a
    finding's unoffered one with the reason ``unoffered``; every offered Issue neither named nor
    resolved is carried."""
    offered = {item["issue"]: item for item in earlier}
    named: set[str] = set()
    ignored: list[dict] = []
    for finding in findings:
        name = finding.pop("earlier", None)
        if name is None or skipped(finding):
            continue
        if name not in offered:
            ignored.append({"issue": name, "reason": unoffered})
        elif name in named:
            ignored.append(
                {"issue": name, "reason": "another finding already names this Issue"}
            )
        else:
            finding["earlier"] = name
            named.add(name)
    done: list[dict] = []
    for item in resolved:
        name = item["issue"]
        if name not in offered:
            reason = "resolves no earlier Issue offered"
        elif name in named:
            reason = "a finding of this review names this Issue"
        elif any(entry["issue"] == name for entry in done):
            reason = "already resolved by this review"
        else:
            done.append({"issue": name, "reason": item["reason"]})
            continue
        ignored.append({"issue": name, "reason": reason})
    closed = named | {entry["issue"] for entry in done}
    carried = [
        {key: item[key] for key in ("issue", "severity", "tier", "title")}
        for item in earlier
        if item["issue"] not in closed
    ]
    return {"carried": carried, "resolved": done, "ignored": ignored}


def report(
    ctx: RunContext,
    module: str,
    findings: list[dict],
    identity: str | None,
    issue_report: Callable[[int, dict], dict],
    *,
    review: str,
    skipped: Skipped = _never,
) -> tuple[list[dict], Stop | None]:
    """Report every finding of one Module that is not ``skipped``; returns the host evidence and,
    when the Issue store refused a report, the Module's stop. Each finding gets its ``issue``.

    ``issue_report`` gives the Issue report of the finding at a position, counted from 1, without
    ``issue_id`` and ``expected_revision``; ``review`` names the review in the stop, such as
    ``code review``."""
    for finding in findings:
        finding["issue"] = None
    found: list[dict] = []
    try:
        root = issue_command.guarded(project_root, ctx.started_in)
        source = {
            "invocation_id": ctx.run_id,
            "agent": "operation",
            "operation": ctx.name,
            "phase": "report",
            "target_id": module,
            "context_id": identity,
            "change_id": ctx.workspace_name,
            "head": ctx.commit or issue_command.head(ctx.worktree),
        }
        for position, finding in enumerate(findings, 1):
            if skipped(finding):
                continue
            value = issue_report(position, finding)
            earlier = finding.get("earlier")
            if earlier:
                _, revision = issue_command.guarded(read_issue, root, earlier)
                value.update(issue_id=earlier, expected_revision=revision)
            receipt = issue_command.guarded(report_issue, root, value, source)
            finding["issue"] = receipt["issue_id"]
            found.append(
                evidence(
                    "issue",
                    receipt["issue_id"],
                    f"{module} finding {position}: "
                    f"{'appended to' if earlier else 'created'} the Issue, report "
                    f"{receipt['report_id']}",
                )
            )
    except issue_command.Refusal as refusal:
        reported = sum(1 for finding in findings if finding["issue"])
        stop = ctx.fail(
            "failed",
            "issues_unreported",
            f"The Issues of {module}'s {review} could not all be written.",
            f"the Issue store refused a report of {module}'s {review} after {reported} of "
            f"its {len(findings)} finding(s) were reported, so the rest were not: {refusal}",
            reason="environment",
            explanation="a failure of the Issue system is never reported as an Issue, and the "
            "Operation does not retry it; the findings stay in the result",
            causes=[refusal.link],
            options=[
                "carry this error chain in the task's decision log and escalation",
                "once the Issue store works again, run the review again",
            ],
        )
        return found, stop
    return found, None


__all__ = ["earlier_issues", "report", "settle"]
