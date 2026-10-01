"""The code review's Issues: the earlier Issues a reviewer receives, and the findings the host reports.

The project's Issues, which the primary worktree keeps, are the review's memory. Before a reviewer
judges, the host reads each reviewed Module's earlier Issues: its open Issues one of whose reports a
``code_review`` run made. The reviewer reports only what is new or what changed in an earlier Issue
(naming it as ``earlier``) and lists the earlier Issues the code no longer has as ``resolved``; an
earlier Issue it neither names nor resolves is carried and still stands. The host, never the
reviewer, then reports every finding through the Issue store: a finding that names an offered
earlier Issue is appended to it at the revision read just before, any other creates an Issue. It
never closes an Issue, and a refusal of the store stops the Module's reporting with the store's
error link as the cause, never as an Issue.
"""

from __future__ import annotations

import json
import re

from ..execution.context import RunContext, Stop, evidence
from ..issues import command as issue_command
from ..issues.shapes import BLOCKING, TIERS
from ..issues.store import list_issues, project_root, read_issue, report_issue

OPERATION = "code_review"
ISSUE = r"^I-[0-9a-f]{32}$"
# The Issue type and subtype of each kind of finding.
CLASSIFICATION = {
    "violation": ("gap", "implementation-spec-mismatch"),
    "missing-test": ("gap", "implementation-spec-mismatch"),
    "spec-challenge": ("gap", "implementation-spec-mismatch"),
    "spec-gap": ("gap", "missing-contract"),
    "defect": ("bug", None),
    "out-of-scope": ("bug", None),
}
LOCATION = re.compile(r"^(?P<path>.+?)(?::(?P<first>[0-9]+)(?:-(?P<last>[0-9]+))?)?$")


def is_blocking(tier: str | None) -> bool:
    return tier in BLOCKING


def earlier_issues(ctx: RunContext, module: str) -> list[dict]:
    """The Module's open Issues a code review reported, each as its latest report states it;
    raises ``issue_command.Refusal`` when the project's Issues cannot be read."""
    root = issue_command.guarded(project_root, ctx.started_in)
    found = []
    for row in issue_command.guarded(
        list_issues, root, target_id=module, status="open"
    ):
        if (row["owner_target_id"] or row["target_id"]) != module:
            continue
        record, _ = issue_command.guarded(read_issue, root, row["id"])
        if not any(
            item["source"]["operation"] == OPERATION for item in record["reports"]
        ):
            continue
        latest = record["reports"][-1]["report"]
        found.append(
            {
                "issue": record["id"],
                "module": module,
                "tier": latest.get("tier"),
                "title": latest["title"],
                "description": latest["description"],
                "evidence": latest["evidence"],
            }
        )
    return found


def material(earlier: list[dict]) -> str:
    """The reviewer's view of its Modules' earlier Issues."""
    if not earlier:
        return (
            "## Earlier Issues\n\nNo earlier code review left an open Issue for the reviewed "
            "Modules.\n"
        )
    return (
        "## Earlier Issues\n\n"
        "Earlier code reviews recorded these open Issues for the reviewed Modules. Before you "
        "report any finding as new, compare it with each of them: a finding about the same "
        "problem, in the same code or against the same promise, is that Issue, however you would "
        "word it now, never a new one. If an Issue still stands as recorded, leave it out: it "
        "stays open. If it still stands but you would state it differently, give it another tier, "
        "or it has changed, report it as a finding of the same Module with `earlier` set to its "
        "identity. If the code no longer has the problem, list it in `resolved` with the reason. "
        "Only a problem none of them covers is a new finding.\n\n```json\n"
        + json.dumps(earlier, indent=2, ensure_ascii=False)
        + "\n```\n"
    )


def settle(earlier: list[dict], findings: list[dict], resolved: list[dict]) -> dict:
    """Which offered earlier Issue each finding of one Module names and which the review resolves.

    A finding keeps ``earlier`` only when it names an offered Issue no other finding named; a
    resolution counts only for an offered Issue no finding named and none resolved before. Every
    other name is listed under ``ignored``; every offered Issue neither named nor resolved is
    carried."""
    offered = {item["issue"]: item for item in earlier}
    named: set[str] = set()
    ignored: list[dict] = []
    for finding in findings:
        name = finding.pop("earlier", None)
        if name is None:
            continue
        if name not in offered:
            ignored.append(
                {
                    "issue": name,
                    "reason": "a finding names no earlier Issue offered for its Module",
                }
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
        {"issue": item["issue"], "tier": item["tier"], "title": item["title"]}
        for item in earlier
        if item["issue"] not in closed
    ]
    return {"carried": carried, "resolved": done, "ignored": ignored}


def location(text: str) -> tuple[str, int | None, int | None] | None:
    """A location's path and its first and last line, or None when it is not one."""
    match = LOCATION.match(text.strip())
    if match is None:
        return None
    first = int(match["first"]) if match["first"] else None
    last = int(match["last"]) if match["last"] else first
    return match["path"], first, last


def issue_report(
    run_id: str, scope: str, key: str, finding: dict, basis_document: str | None
) -> dict:
    """The Issue report of one finding, without ``issue_id`` and ``expected_revision``."""
    kind, subtype = CLASSIFICATION[finding["kind"]]
    places = ", ".join(finding["locations"])
    evidence_items = []
    for item in finding["locations"]:
        path, first, last = location(item)
        lines = (
            f"lines {first}-{last}"
            if first and last != first
            else f"line {first}"
            if first
            else "the file"
        )
        evidence_items.append(
            {
                "path": path,
                "description": f"{lines}, shown by the {finding['kind']} finding",
            }
        )
    if basis_document:
        evidence_items.append(
            {
                "path": basis_document,
                "description": f"defines {finding['basis']}, the finding's basis",
            }
        )
    return {
        "report_key": key,
        "tier": finding["tier"],
        "type": kind,
        "subtype": subtype,
        "title": finding["title"],
        "description": f"{finding['problem']}\n\nSuggested repair: {finding['suggestion']}",
        "impact": finding["impact"],
        "basis": (
            f"{OPERATION} run {run_id} ({scope} review) judged {places} against "
            f"{finding['basis']} and reported a {finding['kind']}: {finding['evidence']}"
        ),
        "owner_target_id": finding["module"],
        "evidence": evidence_items,
    }


def report(
    ctx: RunContext,
    scope: str,
    module: str,
    findings: list[dict],
    identity: str,
    documents: dict[str, str | None],
) -> tuple[list[dict], Stop | None]:
    """Report every finding of one Module; returns the host evidence and, when the Issue store
    refused a report, the Module's stop. Each finding gets its ``issue``. ``documents`` gives the
    document that defines each finding's basis."""
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
            value = issue_report(
                ctx.run_id,
                scope,
                f"{module}/{position}",
                finding,
                documents.get(finding["basis"]),
            )
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
            f"The Issues of {module}'s code review could not all be written.",
            f"the Issue store refused a report of {module}'s code review after {reported} of "
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


__all__ = [
    "CLASSIFICATION",
    "ISSUE",
    "OPERATION",
    "TIERS",
    "earlier_issues",
    "is_blocking",
    "issue_report",
    "location",
    "material",
    "report",
    "settle",
]
