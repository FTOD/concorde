"""The review's Issues: the earlier Issues a worker receives, and the findings the host reports.

The project's Issues, which the primary worktree keeps, are the review's memory. Before its workers
judge a Module, the host reads the Module's earlier Issues: its open Issues one of whose reports a
review Operation made. Every worker receives them, reports only what is new or what changed in an
earlier Issue (naming it as ``earlier``) and lists the earlier Issues the Specs no longer have as
``resolved``; an earlier Issue it neither names nor resolves is carried and still stands. The host,
never a worker, then reports every finding that stands through the Issue store: a finding that
names an offered earlier Issue is appended to it at the revision read just before, any other
creates an Issue. It never closes an Issue, and a refusal of the store stops the Module's reporting
with the store's error link as the cause, never as an Issue.
"""

from __future__ import annotations

import json

from ..execution.context import RunContext, evidence
from ..issues import command as issue_command
from ..issues.shapes import BLOCKING, SEVERITIES, TIERS
from ..issues.store import list_issues, project_root, read_issue, report_issue

# The Operations whose reports make an Issue one of a Module's earlier Issues.
REVIEW_OPERATIONS = ("spec_review", "spec_panel")
ISSUE = r"^I-[0-9a-f]{32}$"


def is_blocking(tier: str | None) -> bool:
    return tier in BLOCKING


def earlier_issues(ctx: RunContext, module: str) -> list[dict]:
    """The Module's open Issues a review reported, each as its latest report states it; raises
    ``issue_command.Refusal`` when the project's Issues cannot be read."""
    root = issue_command.guarded(project_root, ctx.started_in)
    found = []
    for row in issue_command.guarded(
        list_issues, root, target_id=module, status="open"
    ):
        if (row["owner_target_id"] or row["target_id"]) != module:
            continue
        record, _ = issue_command.guarded(read_issue, root, row["id"])
        if not any(
            item["source"]["operation"] in REVIEW_OPERATIONS
            for item in record["reports"]
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


def material(earlier: list[dict]) -> str:
    """The workers' view of the earlier Issues."""
    if not earlier:
        return "## Earlier Issues\n\nNo earlier review left an open Issue for this Module.\n"
    return (
        "## Earlier Issues\n\n"
        "Earlier reviews recorded these open Issues for this Module. Before you report any "
        "finding as new, compare it with each of them: a finding about the same problem, the "
        "same passage or the same kind of defect in the same place, is that Issue, however you "
        "would word it now, never a new one. If an Issue still stands as recorded, leave it out: "
        "it stays open. If it still stands but you would state it differently, give it another "
        "severity or tier, or it has changed, report it as a finding with `earlier` set to its identity. If "
        "the Specs no longer have the problem, list it in `resolved` with the reason. Only a "
        "problem none of them covers is a new finding.\n\n```json\n"
        + json.dumps(earlier, indent=2, ensure_ascii=False)
        + "\n```\n"
    )


def settle(earlier: list[dict], findings: list[dict], resolved: list[dict]) -> dict:
    """Which offered earlier Issue each finding names and which the review resolves.

    A finding keeps ``earlier`` only when it names an offered Issue no other finding named and the
    checker did not dispute it; a resolution counts only for an offered Issue no finding named and
    none resolved before. Every other name is listed under ``ignored``; every offered Issue neither
    named nor resolved is carried."""
    offered = {item["issue"]: item for item in earlier}
    named: set[str] = set()
    ignored: list[dict] = []
    for finding in findings:
        name = finding.pop("earlier", None)
        if name is None:
            continue
        if (finding.get("check") or {}).get("status") == "disputed":
            continue  # a disputed finding is reported nowhere; the Issue it named is carried
        if name not in offered:
            ignored.append(
                {"issue": name, "reason": "a finding names no earlier Issue offered"}
            )
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


def _kind(dimension: str) -> tuple[str, str | None]:
    """The Issue type and subtype of a finding of ``dimension``."""
    if dimension == "context":
        return "gap", "missing-contract"
    if dimension == "consistency":
        return "gap", "spec-conflict"
    return "bug", None


def _where(finding: dict) -> str:
    place = finding["path"]
    if finding.get("anchor"):
        place += f" at {finding['anchor']}"
    if finding.get("line"):
        place += f", line {finding['line']}"
    return place


def issue_report(operation: str, run_id: str, key: str, finding: dict) -> dict:
    """The Issue report of one finding, without ``issue_id`` and ``expected_revision``."""
    kind, subtype = _kind(finding["dimension"])
    description = f"{finding['problem']}\n\nSuggested repair: {finding['suggestion']}"
    if finding.get("related"):
        description += "\n\nOther Modules concerned: " + ", ".join(finding["related"])
    basis = (
        f"{operation} run {run_id} judged {_where(finding)} by the {finding['dimension']} "
        f"criterion of the Protocol's Evaluating a Spec; the Specs read: "
        f"{finding['evidence']}"
    )
    if finding.get("note"):
        basis += (
            f"\n\nThe panel's chair merged {', '.join(finding['sources'])} and verified: "
            f"{finding['note']}"
        )
    anchor = finding.get("anchor") or (
        f"line {finding['line']}" if finding.get("line") else "the document"
    )
    return {
        "report_key": key,
        "tier": finding["tier"],
        "severity": finding["severity"],
        "type": kind,
        "subtype": subtype,
        "title": finding["title"],
        "description": description,
        "impact": finding["impact"],
        "basis": basis,
        "owner_target_id": finding["module"],
        "evidence": [
            {
                "path": finding["path"],
                "description": f"{anchor}, cited by the {finding['dimension']} finding",
            }
        ],
    }


def report(
    ctx: RunContext, module: str, findings: list[dict], identity: str | None
) -> tuple[list[dict], object | None]:
    """Report every finding the checker did not dispute; returns the host evidence and, when the
    Issue store refused a report, the Module's stop. Each finding gets its ``issue``."""
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
            if (finding.get("check") or {}).get("status") == "disputed":
                continue
            value = issue_report(ctx.name, ctx.run_id, f"{module}/{position}", finding)
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
        cause = refusal.link
        reported = sum(1 for finding in findings if finding["issue"])
        stop = ctx.fail(
            "failed",
            "issues_unreported",
            f"The Issues of {module}'s review could not all be written.",
            f"the Issue store refused a report of {module}'s review after {reported} of its "
            f"{len(findings)} finding(s) were reported, so the rest were not: {refusal}",
            reason="environment",
            explanation="a failure of the Issue system is never reported as an Issue, and the "
            "Operation does not retry it; the findings stay in the result",
            causes=[cause],
            options=[
                "carry this error chain in the task's decision log and escalation",
                "once the Issue store works again, run the review again",
            ],
        )
        return found, stop
    return found, None


__all__ = [
    "ISSUE",
    "REVIEW_OPERATIONS",
    "SEVERITIES",
    "TIERS",
    "earlier_issues",
    "is_blocking",
    "issue_report",
    "material",
    "report",
    "settle",
]
