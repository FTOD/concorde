"""The review's Issues: the earlier Issues a worker receives, and the findings the host reports.

The project's Issues, which the primary worktree keeps, are the review's memory. Before its workers
judge a Module, the host reads the Module's earlier Issues: its open Issues one of whose reports a
review Operation made, and every worker receives them. Reading, settling and reporting them are
every review's, in ``method.review_issues``; this module adds what is the Spec review's own:
the workers' view of the earlier Issues, the disputed findings it reports nowhere and the Issue
report of a Spec finding.
"""

from __future__ import annotations

import json

from ...execution.context import RunContext
from .. import review_issues
from ..review_issues import SEVERITIES, TIERS, Refusal, is_blocking

# The Operations whose reports make an Issue one of a Module's earlier Issues.
REVIEW_OPERATIONS = ("spec_review", "spec_panel")
ISSUE = r"^I-[0-9a-f]{32}$"


def earlier_issues(ctx: RunContext, module: str) -> list[dict] | None:
    """The Module's open Issues a review reported, each as its latest report states it; None
    where the issues part is not installed. Raises ``Refusal`` when the project's Issues cannot be
    read."""
    return review_issues.earlier_issues(ctx, module, REVIEW_OPERATIONS)


def material(earlier: list[dict] | None) -> str:
    """The workers' view of the earlier Issues."""
    if earlier is None:
        return (
            "## Earlier Issues\n\nThe project keeps no Issues (the issues part is not installed), "
            "so there are no earlier Issues: report every finding as new and resolve none.\n"
        )
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


def _disputed(finding: dict) -> bool:
    """A finding the checker disputed, which is reported nowhere."""
    return (finding.get("check") or {}).get("status") == "disputed"


def settle(earlier: list[dict], findings: list[dict], resolved: list[dict]) -> dict:
    """Which offered earlier Issue each finding names and which the review resolves, as
    ``review_issues.settle`` decides; a disputed finding names none, so the Issue it named is
    carried."""
    return review_issues.settle(earlier, findings, resolved, skipped=_disputed)


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
    return review_issues.report(
        ctx,
        module,
        findings,
        identity,
        lambda position, finding: issue_report(
            ctx.name, ctx.run_id, f"{module}/{position}", finding
        ),
        review="review",
        skipped=_disputed,
    )


__all__ = [
    "ISSUE",
    "REVIEW_OPERATIONS",
    "SEVERITIES",
    "TIERS",
    "earlier_issues",
    "Refusal",
    "is_blocking",
    "issue_report",
    "material",
    "report",
    "settle",
]
