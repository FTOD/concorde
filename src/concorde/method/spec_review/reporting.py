"""The review's Issues: the earlier Issues a worker receives, and the findings the host reports.

The project's Issues, which the primary worktree keeps, are the review's memory. Before its workers
judge a Module, the host reads the Module's earlier Issues: its open Issues one of whose reports a
review Operation made, and every worker receives them. Reading, settling and reporting them are
every review's, in ``method.review_issues``; this module adds what is the Spec review's own:
the workers' view of the earlier Issues, the consolidation of a Module's context findings and the
Issue report of a Spec finding.

A finding of dimension ``context`` says that the Module's declarations do not select something
its Specs rely on. Before the findings are settled, the host merges every blocking one of a Module
into one finding of the fixed title ``CONTEXT_TITLE``, which lists each missing selection. Thus a
run records at most one such Issue per Module, appended to the Module's open Issue of that title
when there is one, whichever review's phase made it.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from ...execution.context import RunContext
from .. import review_issues
from ..review_issues import SEVERITIES, TIERS, Refusal, is_blocking

# The reports that make an Issue one of a Module's earlier Issues for ``spec_panel``: its own, and
# those of the Spec panels and the architecture review of ``project_review``, by their phase.
REVIEW_SOURCES = {"spec_panel": None, "project_review": ("spec-panel", "architecture")}
ISSUE = r"^I-[0-9a-f]{32}$"
# The title of a Module's one Issue of its context findings, by which every Spec review finds it.
CONTEXT_TITLE = "The Module's declarations do not select everything its Specs rely on"


def earlier_issues(ctx: RunContext, module: str, sources=None) -> list[dict] | None:
    """The Module's open Issues one of ``sources`` reported, ``REVIEW_SOURCES`` by default, and
    its Issue of ``CONTEXT_TITLE`` whichever phase of those Operations reported it, each as its
    latest report states it; None where the issues part is not installed. Raises ``Refusal`` when
    the project's Issues cannot be read."""
    return review_issues.earlier_issues(
        ctx, module, sources or REVIEW_SOURCES, titles=(CONTEXT_TITLE,)
    )


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
        + json.dumps(review_issues.offered(earlier), indent=2, ensure_ascii=False)
        + "\n```\n"
    )


def settle(earlier: list[dict], findings: list[dict], resolved: list[dict]) -> dict:
    """Which offered earlier Issue each finding names and which the review resolves, as
    ``review_issues.settle`` decides."""
    return review_issues.settle(earlier, findings, resolved)


def _numbered(texts: list[str]) -> str:
    return "\n".join(f"{position}. {text}" for position, text in enumerate(texts, 1))


def _merged(module: str, parts: list[dict]) -> dict:
    """One finding of ``CONTEXT_TITLE`` that lists every missing selection of ``parts``, the
    Module's blocking context findings, with their highest tier and severity."""
    sources = [label for part in parts for label in part.get("sources") or []]
    related = [name for part in parts for name in part.get("related") or []]
    merged = {
        "module": module,
        "path": parts[0]["path"],
        "dimension": "context",
        "severity": min(
            (part["severity"] for part in parts), key=review_issues.SEVERITIES.index
        ),
        "tier": max((part["tier"] for part in parts), key=review_issues.TIERS.index),
        "title": CONTEXT_TITLE,
        "problem": f"The declarations of {module} do not select {len(parts)} "
        "contract(s), document(s) or concept(s) its Specs rely on, so a worker bound to it "
        "is not given them:\n\n"
        + _numbered(
            [f"{part['title']} ({_where(part)}): {part['problem']}" for part in parts]
        ),
        "impact": _numbered([part["impact"] for part in parts]),
        "evidence": _numbered([part["evidence"] for part in parts]),
        "suggestion": _numbered([part["suggestion"] for part in parts]),
        "issue": None,
    }
    if sources:
        merged["sources"] = list(dict.fromkeys(sources))
        merged["workers"] = len({label.split(".")[0] for label in merged["sources"]})
    if any(part.get("note") for part in parts):
        merged["note"] = (
            f"The host merged the panel's {len(parts)} context finding(s) of {module} into "
            "this one: "
            + " ".join(
                f"({position}) {part['note']}"
                for position, part in enumerate(parts, 1)
                if part.get("note")
            )
        )
    if related:
        merged["related"] = list(dict.fromkeys(related))
    return merged


def consolidate_context(
    ctx: RunContext, findings: list[dict], earlier: list[dict] | None, default: str
) -> tuple[list[dict], list[dict]]:
    """The findings with every Module's blocking findings of dimension ``context`` merged into
    one in the place of the first, and the earlier Issues the merged findings no longer name, as
    ``ignored`` entries.

    ``default`` is the Module of an earlier Issue that names none, the reviewed Module. A merged
    finding names, in this order: the Issue a merged finding of the same Module and run was
    reported as, whose missing selections it lists again; the Module's offered Issue of
    ``CONTEXT_TITLE``; the first Issue one of its parts named."""
    memory = ctx.__dict__.setdefault("context_findings", {})
    groups: dict[str, list[dict]] = {}
    for finding in findings:
        if finding["dimension"] == "context" and review_issues.is_blocking(
            finding["tier"]
        ):
            groups.setdefault(finding["module"], []).append(finding)
    if not groups:
        return findings, []
    ignored: list[dict] = []
    merged: dict[str, dict] = {}
    for module, parts in groups.items():
        before = memory.get(module)
        # A merged finding this run already reported is listed again in the report appended
        # to its Issue, which then states every missing selection the run found.
        prior = before["parts"] if before and before["issue"] else []
        finding = _merged(module, [*prior, *parts])
        names = [part["earlier"] for part in parts if part.get("earlier")]
        titled = [
            item["issue"]
            for item in earlier or []
            if item["title"] == CONTEXT_TITLE and item.get("module", default) == module
        ]
        chosen = next(
            iter([*([before["issue"]] if prior else []), *titled, *names]), None
        )
        if chosen:
            finding["earlier"] = chosen
        ignored.extend(
            {
                "issue": name,
                "reason": f"its missing selection is merged into the one context finding of "
                f"{module}, which names {chosen}",
            }
            for name in dict.fromkeys(names)
            if name != chosen
        )
        merged[module] = finding
        memory[module] = {"issue": None, "parts": [*prior, *parts], "finding": finding}
    parts = {id(part): module for module, items in groups.items() for part in items}
    result: list[dict] = []
    for finding in findings:
        module = parts.get(id(finding))
        if module is None:
            result.append(finding)
        elif merged[module] is not None:
            result.append(merged.pop(module))
            merged[module] = None
    return result, ignored


def remember_context(ctx: RunContext, findings: list[dict]) -> None:
    """Remember the Issue each merged context finding was reported as, for a later part of the
    same run that merges a context finding of the same Module."""
    memory = ctx.__dict__.setdefault("context_findings", {})
    for item in memory.values():
        if any(finding is item["finding"] for finding in findings):
            item["issue"] = item["finding"]["issue"]


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


def finding_phase(finding: dict) -> str:
    """The provenance phase of one chair finding of ``spec_panel``: ``architecture`` when every
    label it merges is an architect's, so that ``project_review``'s architecture review offers its
    Issue, and ``report`` when it merges a reviewer's."""
    sources = finding.get("sources") or []
    if sources and all(label.startswith("a") for label in sources):
        return "architecture"
    return "report"


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
    ctx: RunContext,
    module: str,
    findings: list[dict],
    identity: str | None,
    earlier: list[dict] | None = None,
    settled: dict | None = None,
    phase: str | Callable[[dict], str] = finding_phase,
) -> tuple[list[dict], object | None]:
    """Report every finding with the provenance ``phase``, by default each finding's
    ``finding_phase``; returns the host evidence and, when the
    Issue store refused a report, the Module's stop. Each finding gets its ``issue``; an
    unreported finding's earlier Issue joins ``settled``'s carried, in ``earlier``'s order."""
    return review_issues.report(
        ctx,
        module,
        findings,
        identity,
        lambda position, finding: issue_report(
            ctx.name, ctx.run_id, f"{module}/{position}", finding
        ),
        review="review",
        earlier=earlier,
        settled=settled,
        phase=phase,
    )


__all__ = [
    "ISSUE",
    "REVIEW_SOURCES",
    "SEVERITIES",
    "TIERS",
    "earlier_issues",
    "finding_phase",
    "Refusal",
    "is_blocking",
    "issue_report",
    "material",
    "report",
    "settle",
]
