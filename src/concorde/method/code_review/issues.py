"""The code review's Issues: the earlier Issues a reviewer receives, and the findings the host reports.

The project's Issues, which the primary worktree keeps, are the review's memory. Before a reviewer
judges, the host reads each reviewed Module's earlier Issues: its open Issues one of whose reports a
``code_review`` run made. Reading, settling and reporting them are every review's, in
``method.review_issues``; this module adds what is the code review's own: the reviewer's view
of its earlier Issues and the Issue report of a code finding.
"""

from __future__ import annotations

import json
import re

from ...execution.context import RunContext, Stop
from .. import review_issues
from ..review_issues import SEVERITIES, TIERS, Refusal, is_blocking

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


def earlier_issues(ctx: RunContext, module: str) -> list[dict] | None:
    """The Module's open Issues a code review reported, each as its latest report states it;
    None where the issues part is not installed. Raises ``Refusal`` when the project's Issues
    cannot be read."""
    found = review_issues.earlier_issues(ctx, module, (OPERATION,))
    if found is None:
        return None
    return [{"issue": item["issue"], "module": module, **item} for item in found]


def material(earlier: list[dict] | None) -> str:
    """The reviewer's view of its Modules' earlier Issues."""
    if earlier is None:
        return (
            "## Earlier Issues\n\nThe project keeps no Issues (the issues part is not installed), "
            "so there are no earlier Issues: report every finding as new and resolve none.\n"
        )
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
        "stays open. If it still stands but you would state it differently, give it another "
        "severity or tier, or it has changed, report it as a finding of the same Module with "
        "`earlier` set to its identity. If the code no longer has the problem, list it in `resolved` with the reason. "
        "Only a problem none of them covers is a new finding.\n\n```json\n"
        + json.dumps(earlier, indent=2, ensure_ascii=False)
        + "\n```\n"
    )


def settle(earlier: list[dict], findings: list[dict], resolved: list[dict]) -> dict:
    """Which offered earlier Issue each finding of one Module names and which the review
    resolves, as ``review_issues.settle`` decides."""
    return review_issues.settle(
        earlier,
        findings,
        resolved,
        unoffered="a finding names no earlier Issue offered for its Module",
    )


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
        "severity": finding["severity"],
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
    earlier: list[dict] | None = None,
    settled: dict | None = None,
) -> tuple[list[dict], Stop | None]:
    """Report every finding of one Module; returns the host evidence and, when the Issue store
    refused a report, the Module's stop. Each finding gets its ``issue``. ``documents`` gives the
    document that defines each finding's basis; ``earlier`` and ``settled`` are the Module's
    earlier Issues offered and how the review settled them, which an unreported finding's earlier
    Issue joins as carried."""
    return review_issues.report(
        ctx,
        module,
        findings,
        identity,
        lambda position, finding: issue_report(
            ctx.run_id,
            scope,
            f"{module}/{position}",
            finding,
            documents.get(finding["basis"]),
        ),
        review="code review",
        earlier=earlier,
        settled=settled,
    )


__all__ = [
    "CLASSIFICATION",
    "ISSUE",
    "OPERATION",
    "SEVERITIES",
    "TIERS",
    "earlier_issues",
    "Refusal",
    "is_blocking",
    "issue_report",
    "location",
    "material",
    "report",
    "settle",
]
