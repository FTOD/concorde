"""What every Spec review Operation shares (see the Spec panel document of Spec review).

For each named Module the host validates the worktree's Specs, reads the Module's earlier Issues,
launches its workers under the Module's grants, normalizes their findings, reports every finding
that stands as an Issue and derives the Module's outcome itself from the Issues that stand. This
module holds the parts of that sequence that do not depend on how the workers are arranged:

- ``validate_modules``: load and validate the worktree's Specs; a loading error fails the run, a
  structural error attributed to a Module makes that Module ``incomplete``.
- the review section and the Protocol's criteria of every worker's brief;
- the normalization of the findings and the repair of the paths that do not hold;
- ``read_earlier`` and ``report_findings``: the Module's earlier Issues and the Issue reports;
- ``blocking_counts``: each Module's outcome with its blocking findings, for the step output.

Worker findings, tiers and resolutions are worker claims and travel only in the payload; the
host's own facts (structural findings, grants, audits, scope corrections, the Issues it reported
to) are host evidence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    evidence,
)
from ..specs import spec_cause, spec_finding
from ..prompts import PROTOCOL_GUIDE
from ...spec.repository import SpecRepository
from ...spec.repository_base import SpecError
from ...spec.schema import ContractError
from ...spec.typed_data import TypedDataError, safe_path
from ...spec.validation import validate_repository
from .. import review_issues
from . import reporting

# The Protocol's Module quality dimensions, and its architecture quality dimensions with ``context``.
DIMENSIONS = ["readability", "obligations", "design", "views", "terminology", "context"]
ARCHITECTURE_DIMENSIONS = [
    "responsibilities",
    "ownership",
    "interfaces",
    "dependencies",
    "failure-containment",
    "consistency",
    "context",
]
TIERS = list(reporting.TIERS)
SEVERITIES = list(reporting.SEVERITIES)
LOAD_ERROR = "CONCORDE-SOURCE-008"
ISSUE_ID: dict = {"type": "string", "pattern": reporting.ISSUE}

# A finding as a reviewer returns it; the host adds ``issue`` and normalizes ``path``.
REVIEWER_FINDING: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "module",
        "path",
        "dimension",
        "severity",
        "tier",
        "title",
        "problem",
        "impact",
        "evidence",
        "suggestion",
    ],
    "properties": {
        "module": {"type": "string", "minLength": 1},
        "path": {"type": "string", "minLength": 1},
        "anchor": {"type": "string", "minLength": 1},
        "line": {"type": "integer", "minimum": 1},
        "dimension": {"enum": DIMENSIONS},
        "severity": {"enum": SEVERITIES},
        "tier": {"enum": TIERS},
        "title": {"type": "string", "minLength": 1},
        "problem": {"type": "string", "minLength": 1},
        "impact": {"type": "string", "minLength": 1},
        "evidence": {"type": "string", "minLength": 1},
        "suggestion": {"type": "string", "minLength": 1},
        # The earlier Issue this finding is the problem of; the host checks it was offered, and
        # an empty one names none.
        "earlier": {"type": "string"},
    },
}
RESOLVED: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issue", "reason"],
    "properties": {
        "issue": {"type": "string", "minLength": 1},
        "reason": {"type": "string", "minLength": 1},
    },
}
# A worker's finding the host did not report since its path does not hold, as the worker returned
# it but for the earlier Issue it named, with the host's reason.
REJECTED: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["finding", "reason"],
    "properties": {
        "finding": {
            **REVIEWER_FINDING,
            "properties": {
                key: value
                for key, value in REVIEWER_FINDING["properties"].items()
                if key != "earlier"
            },
        },
        "reason": {"type": "string", "minLength": 1},
    },
}

# What the payload says of a Module's earlier Issues; null when they were never read.
EARLIER_ISSUES: dict = {
    "anyOf": [
        {"type": "null"},
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["carried", "resolved", "ignored"],
            "properties": {
                "carried": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["issue", "severity", "tier", "title"],
                        "properties": {
                            "issue": ISSUE_ID,
                            "severity": {
                                "anyOf": [{"enum": SEVERITIES}, {"type": "null"}]
                            },
                            "tier": {"anyOf": [{"enum": TIERS}, {"type": "null"}]},
                            "title": {"type": "string", "minLength": 1},
                        },
                    },
                },
                "resolved": {
                    "type": "array",
                    "items": {
                        **RESOLVED,
                        "properties": {**RESOLVED["properties"], "issue": ISSUE_ID},
                    },
                },
                "ignored": {"type": "array", "items": RESOLVED},
            },
        },
    ]
}


@dataclass
class ModuleReview:
    """What the host knows about one reviewed Module; ``stop`` is set when it is incomplete."""

    module: str
    documents: tuple[str, ...] = ()
    context_identity: str | None = None
    findings: list[dict] = field(default_factory=list)
    stop: Stop | None = None
    # The Module's earlier Issues as offered to its workers, and what the review did with them.
    earlier: list[dict] | None = None
    summary: dict | None = None
    # Whether the host settled and reported the findings, with or without the issues part.
    settled: bool = False

    @property
    def outcome(self) -> str:
        if self.stop is not None:
            return "incomplete"
        # Every Issue of a blocking tier that stands: reported now, or carried from before.
        reported = any(reporting.is_blocking(item["tier"]) for item in self.findings)
        carried = any(
            reporting.is_blocking(item["tier"])
            for item in (self.summary or {}).get("carried", [])
        )
        return "changes_required" if reported or carried else "accepted"

    @property
    def standing(self) -> int:
        """The Issues of a blocking tier that stand for the Module."""
        return sum(
            1
            for item in [*self.findings, *(self.summary or {}).get("carried", [])]
            if reporting.is_blocking(item["tier"])
        )


@dataclass
class ReviewRun:
    """The run's review state, kept on the run context between steps."""

    reviews: dict[str, ModuleReview]
    repository: SpecRepository | None = None
    # The whole project's structural validation, as the first step found it.
    validation: object | None = None


def _state(ctx: RunContext) -> ReviewRun:
    return ctx.__dict__.setdefault(
        "spec_review_state",
        ReviewRun({module: ModuleReview(module) for module in ctx.modules}),
    )


def _attributed(repository, module: str, finding) -> bool:
    """Whether a structural finding concerns the Module's own Specs."""
    if finding.subject_id == module:
        return True
    declared = repository.modules[module]
    if finding.source in declared.sources:
        return True
    if finding.subject_id:
        document = repository.definer(finding.subject_id)
        return document is not None and document in declared.documents
    return False


def validate_modules(ctx: RunContext):
    """Step 1: load the task worktree's Specs and stop the review of structurally invalid Modules."""
    state = _state(ctx)
    reviews = state.reviews
    result = validate_repository(ctx.worktree)
    load = [item for item in result.findings if item.rule_id == LOAD_ERROR]
    repository = None
    if not load:
        try:
            repository = SpecRepository(ctx.worktree)
        except (SpecError, TypedDataError, OSError) as error:
            load = [error]
    if load:
        detail = "; ".join(getattr(item, "message", str(item)) for item in load)
        return ctx.fail(
            "failed",
            "specs_unloadable",
            "The task worktree's Specs could not be loaded.",
            f"the Specs of {ctx.worktree} could not be loaded, so no Module can be reviewed: "
            f"{detail}",
            reason="scope",
            explanation=f"{ctx.name} reviews loadable Specs and never repairs them",
            evidence=[evidence("structural", ".concorde/config.json", detail)],
            causes=[
                spec_cause(item)
                if isinstance(item, BaseException)
                else spec_finding(
                    item.rule_id,
                    item.source,
                    item.line,
                    item.message,
                    "Specs that do not load cannot be validated or granted",
                )
                for item in load
            ],
            options=["repair the configuration, registry or Protocol binding"],
        )
    state.repository = repository
    state.validation = result
    found = []
    for module, review in reviews.items():
        if module not in repository.modules:
            item = evidence(
                "structural", module, "not a registered Module of the task worktree"
            )
            found.append(item)
            review.stop = ctx.fail(
                "failed",
                "unknown_module",
                f"{module} is not a registered Module.",
                f"{module} is not a registered Module of {ctx.worktree}, so it cannot be "
                "reviewed",
                reason="input",
                explanation="the reviewed Modules come from the command line or the task",
                evidence=[item],
                options=["name registered Modules in --modules"],
            )
            continue
        review.documents = repository.modules[module].documents
        errors = [
            item
            for item in result.findings
            if item.strictness == "error" and _attributed(repository, module, item)
        ]
        if not errors:
            continue
        items = [
            evidence(
                "structural",
                f"{item.source}:{item.line}" if item.line else item.source,
                f"{module}: {item.rule_id}: {item.message}",
            )
            for item in errors
        ]
        found.extend(items)
        review.stop = ctx.fail(
            "blocked",
            "structural_errors",
            f"{module} fails structural validation.",
            f"{module} fails {len(errors)} structural check(s), so no reviewer was launched "
            "for it",
            reason="decision",
            explanation="a reviewer judges only structurally valid Specs; repairing them is a "
            "specify task the main agent chooses",
            evidence=items,
            causes=[
                spec_finding(
                    item.rule_id,
                    item.source,
                    item.line,
                    item.message,
                    "validation diagnoses the Specs; it does not change them",
                )
                for item in errors
            ],
            options=[
                "repair the Specs with specify",
                "run concorde spec-validation for details",
            ],
            recommendation=f"repair the structural errors, then run {ctx.name} again",
        )
    return Continue(evidence=found)


def _labelled(items: list[dict], label: str) -> list[dict]:
    return [
        {**item, "detail": f"{label}: {item['detail']}" if item["detail"] else label}
        for item in items
    ]


def _identity(items: list[dict]) -> str | None:
    return next(
        (item["ref"] for item in items if item["kind"] == "context-identity"), None
    )


def _task_section(ctx: RunContext, review: ModuleReview, role: str) -> str:
    documents = "".join(
        f"- {(ctx.worktree / path).as_posix()} (`{path}`)\n"
        for path in review.documents
    )
    goal = ctx.goal.strip()
    return (
        f"## This review\n\n"
        f"Your role: {role}.\n\n"
        f"Reviewed Module: `{review.module}`. Its own documents, the only ones that can carry "
        f"a blocking finding (each has a metadata file with the same name plus `.json`):\n\n"
        f"{documents}\n"
        "The task's goal, for orientation only; judge the Specs as they are written:\n\n"
        f"{goal or '(none)'}\n"
    )


# The parts of the Protocol's writing guide a review worker judges by.
CRITERIA = ("Writing guidance", "Sentence style", "Evaluating a Spec")


def criteria(worktree: Path) -> str:
    """The Protocol's Writing guidance, Sentence style and Evaluating a Spec, from the project's
    Protocol copy, as the last part of every review worker's brief, or a note that the copy cannot
    be read."""
    path = worktree / PROTOCOL_GUIDE
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return (
            f"\n## The Protocol's criteria\n\n(The project's Protocol copy {PROTOCOL_GUIDE} "
            f"cannot be read: {error}; judge by the rules above and say so in your summary.)\n"
        )
    kept, keep, fenced = [], False, False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("# "):
            keep = line[2:].strip() in CRITERIA
        if keep:
            kept.append(line)
    return (
        f"\n## The Protocol's criteria\n\nFrom the project's Protocol copy ({PROTOCOL_GUIDE}):"
        "\n\n" + "\n".join(kept).strip() + "\n"
    )


def _project_path(ctx: RunContext, path: str) -> str | None:
    """The path relative to the task worktree, or None when it is not a project path."""
    if os.path.isabs(path):
        try:
            path = (
                Path(os.path.realpath(path))
                .relative_to(os.path.realpath(ctx.worktree))
                .as_posix()
            )
        except ValueError:
            return None
    path = path.removeprefix("./")
    try:
        safe_path(path, "path")
    except (ContractError, TypedDataError, ValueError):
        return None
    return path


def _normalize(ctx: RunContext, review: ModuleReview, claimed: list[dict]):
    """The payload findings, in the order claimed with None for each rejected one, the host's
    scope corrections and the rejected findings, each with its reason: a finding whose path is
    not one of the task worktree is rejected alone, never reported."""
    repository = _state(ctx).repository
    own = {member for path in review.documents for member in (path, path + ".json")}
    findings, corrections, rejected = [], [], []
    for position, item in enumerate(claimed, 1):
        path = _project_path(ctx, item["path"])
        if path is None:
            reason = (
                f"finding {position} names {item['path']!r}, which is not a path in the "
                "task worktree"
            )
            corrections.append(evidence("invalid-output", review.module, reason))
            rejected.append(
                {
                    "finding": {
                        key: value for key, value in item.items() if key != "earlier"
                    },
                    "reason": reason,
                }
            )
            findings.append(None)
            continue
        finding = {
            **review_issues.without_blank_earlier(item),
            "path": path,
            "issue": None,
        }
        owners = repository.document_targets.get(path.removesuffix(".json"))
        if owners:
            finding["module"] = owners[0]
        if reporting.is_blocking(finding["tier"]) and path not in own:
            finding["tier"] = "suggestion"
            corrections.append(
                evidence(
                    "finding-scope",
                    f"{review.module} finding {position}",
                    f"{path} is not a document of {review.module}; the finding of tier "
                    f"{item['tier']} counts as a suggestion",
                )
            )
        findings.append(finding)
    return findings, corrections, rejected


def path_repair(ctx: RunContext, result: dict) -> str | None:
    """The repair that resumes a reviewing worker once with every finding whose path is not one
    of the task worktree, or None when every path holds."""
    return review_issues.citation_repair(
        [
            f"finding {position} (titled {item.get('title')!r}) names {item['path']!r}, which is "
            "not a path in the task worktree"
            for position, item in enumerate(
                (result.get("output") or {}).get("findings") or [], 1
            )
            if _project_path(ctx, item["path"]) is None
        ]
    )


def read_earlier(ctx: RunContext, review: ModuleReview, sources=None) -> list[dict]:
    """The Module's earlier Issues, of ``sources`` or else ``spec_panel``'s, or its stop when the
    project's Issues cannot be read; returns the host evidence."""
    try:
        review.earlier = reporting.earlier_issues(ctx, review.module, sources)
    except reporting.Refusal as refusal:
        review.stop = ctx.fail(
            "failed",
            "issues_unreadable",
            f"The earlier Issues of {review.module} cannot be read.",
            f"the project's Issues could not be read for {review.module}: {refusal}",
            reason="environment",
            explanation="a review builds on the Module's earlier Issues, which it must be able "
            "to read; a failure of the Issue system is never reported as an Issue",
            causes=[refusal.link],
            options=[
                "repair the Issue records (issue_check), then run the review again"
            ],
        )
        return []
    if review.earlier is None:
        return [
            evidence(
                "earlier-issues",
                review.module,
                f"no earlier Issue offered: {review_issues.NOT_RECORDED}",
            )
        ]
    names = ", ".join(item["issue"] for item in review.earlier)
    return [
        evidence(
            "earlier-issues",
            review.module,
            f"{len(review.earlier)} earlier Issue(s) offered{': ' + names if names else ''}",
        )
    ]


def report_findings(
    ctx: RunContext,
    review: ModuleReview,
    resolved: list[dict],
    identity: str | None,
    phase: str = "report",
) -> list[dict]:
    """Settle the earlier Issues and report the findings as Issues with the provenance ``phase``;
    returns the host evidence."""
    review.summary = reporting.settle(review.earlier or [], review.findings, resolved)
    review.settled = True
    if review.earlier is None:
        # No earlier Issue was read, so none is carried or resolved.
        review.summary = None
    found, stop = reporting.report(
        ctx,
        review.module,
        review.findings,
        identity,
        review.earlier,
        review.summary,
        phase=phase,
    )
    if stop is not None:
        review.stop = stop
    return found


def blocking_counts(modules: list[dict]) -> list[dict]:
    """Each reviewed Module's outcome with the count of its blocking findings that stand."""
    return [
        {
            "module": item["module"],
            "outcome": item["outcome"],
            "blocking": sum(
                1
                for finding in item["findings"]
                if reporting.is_blocking(finding["tier"])
            ),
        }
        for item in modules
    ]
