"""The ``spec_review`` Operation (see the Spec review Operation Spec).

For each named Module the host validates the task worktree's Specs, reads the Module's earlier
Issues, launches one ``review-spec`` reviewer under that Module's grant, optionally a checker of the
reviewer's findings under the same grant, reports every finding that stands as an Issue and derives
the Module's outcome and the verdict itself from the Issues that stand:

1. ``validate_modules``: load and validate the task worktree's Specs; a loading error fails the
   run, a structural error attributed to a Module makes that Module ``incomplete``.
2. ``review_modules``: per remaining Module, the earlier Issues, the standard worker sequence for
   the reviewer and, with ``--check-findings``, for the checker (grant, settings, brief, launch,
   audit, run record), then the Issue reports.
3. ``derive_verdict``: each Module's outcome, the verdict, and the result.

Reviewer findings, tiers, resolutions and checker statuses are worker claims and travel only in the
payload; the host's own facts (structural findings, grants, audits, scope corrections, the Issues it
reported to) are host evidence.
"""

from __future__ import annotations

import json
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
from ..workers import operation, run_worker
from ..prompts import (
    PROTOCOL_GUIDE,
    load_prompt,
)
from ...spec.repository import SpecRepository
from ...spec.repository_base import SpecError
from ...spec.schema import ContractError, validate
from ...spec.typed_data import TypedDataError, safe_path
from ...spec.validation import validate_repository
from .. import review_issues
from ..review_issues import review_output
from . import reporting

TASK_TYPE = "review-spec"
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
OUTCOMES = ["accepted", "changes_required", "incomplete"]
LOAD_ERROR = "CONCORDE-SOURCE-008"
ISSUE_ID: dict = {"type": "string", "pattern": reporting.ISSUE}

# A finding as a reviewer returns it; the host adds ``check`` and ``issue`` and normalizes ``path``.
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
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {"type": "array", "items": REVIEWER_FINDING},
        "resolved": {"type": "array", "items": RESOLVED},
    },
}
CHECK_STATUS: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "reason"],
    "properties": {
        "status": {"enum": ["confirmed", "disputed"]},
        "reason": {"type": "string", "minLength": 1},
    },
}
CHECKER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["checks"],
    "properties": {
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["finding", "status", "reason"],
                "properties": {
                    "finding": {"type": "integer", "minimum": 1},
                    **CHECK_STATUS["properties"],
                },
            },
        }
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

# A payload finding: the reviewer's finding with its path normalized, ``earlier`` only when the
# host appended it to that earlier Issue, the checker's status and the Issue it was reported to.
FINDING: dict = {
    **REVIEWER_FINDING,
    "required": [*REVIEWER_FINDING["required"], "check", "issue"],
    "properties": {
        **REVIEWER_FINDING["properties"],
        "path": {"type": "string", "format": "project-path"},
        "earlier": ISSUE_ID,
        "check": {"anyOf": [{"type": "null"}, CHECK_STATUS]},
        "issue": {"anyOf": [{"type": "null"}, ISSUE_ID]},
    },
}

# contract.spec-review.payload, version 7 (operation.md); a test keeps the two equal.
PAYLOAD_SCHEMA: dict = {
    "type": "object",
    "required": ["verdict", "modules", "workflow"],
    "additionalProperties": False,
    "properties": {
        "verdict": {"enum": OUTCOMES},
        # The workflow object of the step output convention, whose own contract defines it.
        "workflow": {"type": "object"},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "module",
                    "outcome",
                    "context_identity",
                    "findings",
                    "rejected",
                    "earlier_issues",
                ],
                "additionalProperties": False,
                "properties": {
                    "module": {"type": "string", "minLength": 1},
                    "outcome": {"enum": OUTCOMES},
                    "context_identity": {
                        "anyOf": [
                            {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                            {"type": "null"},
                        ]
                    },
                    "findings": {"type": "array", "items": FINDING},
                    "rejected": {"type": "array", "items": REJECTED},
                    "earlier_issues": EARLIER_ISSUES,
                },
            },
        },
    },
}


@dataclass
class ModuleReview:
    """What the host knows about one reviewed Module; ``stop`` is set when it is incomplete."""

    module: str
    documents: tuple[str, ...] = ()
    context_identity: str | None = None
    findings: list[dict] = field(default_factory=list)
    # The reviewer's findings whose path did not hold, never reported.
    rejected: list[dict] = field(default_factory=list)
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
        reported = any(
            reporting.is_blocking(item["tier"])
            and (item.get("check") or {}).get("status") != "disputed"
            for item in self.findings
        )
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
            for item in [
                *(
                    finding
                    for finding in self.findings
                    if (finding.get("check") or {}).get("status") != "disputed"
                ),
                *(self.summary or {}).get("carried", []),
            ]
            if reporting.is_blocking(item["tier"])
        )


@dataclass
class ReviewRun:
    """The run's review state, kept on the run context between steps."""

    reviews: dict[str, ModuleReview]
    repository: SpecRepository | None = None


def _state(ctx: RunContext) -> ReviewRun:
    return ctx.__dict__.setdefault(
        "spec_review",
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
            explanation="spec_review reviews loadable Specs and never repairs them",
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
            recommendation="repair the structural errors, then run spec_review again",
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
            "check": None,
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


def _checker_material(findings: list[dict]) -> str:
    lines = ["## Findings to check\n"]
    for position, item in enumerate(findings, 1):
        lines.append(f"\nFinding {position}:\n\n```json\n")
        lines.append(
            json.dumps(
                {
                    key: value
                    for key, value in item.items()
                    if key not in ("check", "issue")
                },
                indent=2,
            )
        )
        lines.append("\n```\n")
    return "".join(lines)


def read_earlier(ctx: RunContext, review: ModuleReview) -> list[dict]:
    """The Module's earlier Issues, or its stop when the project's Issues cannot be read; returns
    the host evidence."""
    try:
        review.earlier = reporting.earlier_issues(ctx, review.module)
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
    ctx: RunContext, review: ModuleReview, resolved: list[dict], identity: str | None
) -> list[dict]:
    """Settle the earlier Issues and report the findings as Issues; returns the host evidence."""
    review.summary = reporting.settle(review.earlier or [], review.findings, resolved)
    review.settled = True
    if review.earlier is None:
        # No earlier Issue was read, so none is carried or resolved.
        review.summary = None
    found, stop = reporting.report(
        ctx, review.module, review.findings, identity, review.earlier, review.summary
    )
    if stop is not None:
        review.stop = stop
    return found


def _review(ctx: RunContext, review: ModuleReview, prompt: str) -> list[dict]:
    """Steps 2 to 9 for one Module; returns the host evidence and sets the review's state."""
    found = read_earlier(ctx, review)
    if review.stop is not None:
        return found
    launched = len(ctx.worker_runs)
    outcome = run_worker(
        ctx,
        prompt
        + "\n"
        + _task_section(ctx, review, "reviewer")
        + "\n"
        + reporting.material(review.earlier)
        + criteria(ctx.worktree),
        task_type=TASK_TYPE,
        output_schema=REVIEWER_OUTPUT,
        rounds=review_issues.CITATION_ROUNDS,
        modules=[review.module],
        worker="reviewer",
        validate=lambda result: path_repair(ctx, result),
    )
    found.extend(_labelled(outcome.evidence, f"{review.module} reviewer"))
    if len(ctx.worker_runs) > launched:
        review.context_identity = _identity(outcome.evidence)
    if isinstance(outcome, Stop):
        outcome.error["actor"] += f", review of {review.module}"
        review.stop = outcome
        return found
    findings, corrections, rejected = _normalize(
        ctx, review, (outcome.output or {}).get("findings", [])
    )
    found.extend(corrections)
    review.rejected = rejected
    findings = [item for item in findings if item is not None]
    review.findings = findings
    resolved = list((outcome.output or {}).get("resolved") or [])
    if ctx.arguments.check_findings and findings:
        found.extend(_check(ctx, review, prompt, findings))
        if review.stop is not None:
            return found
    found.extend(report_findings(ctx, review, resolved, review.context_identity))
    return found


def _check(ctx: RunContext, review: ModuleReview, prompt: str, findings: list[dict]):
    """The checker of one Module's findings; sets their ``check`` or the review's stop."""
    found: list[dict] = []
    outcome = run_worker(
        ctx,
        prompt
        + "\n"
        + _task_section(ctx, review, "checker")
        + "\n"
        + reporting.material(review.earlier)
        + "\n"
        + _checker_material(findings)
        + criteria(ctx.worktree),
        task_type=TASK_TYPE,
        output_schema=CHECKER_OUTPUT,
        rounds=0,
        modules=[review.module],
        worker="checker",
    )
    found.extend(_labelled(outcome.evidence, f"{review.module} checker"))
    if isinstance(outcome, Stop):
        outcome.error["actor"] += f", review of {review.module}"
        review.stop = outcome
        return found
    for item in (outcome.output or {}).get("checks", []):
        position = item["finding"]
        if 1 <= position <= len(findings) and findings[position - 1]["check"] is None:
            findings[position - 1]["check"] = {
                "status": item["status"],
                "reason": item["reason"],
            }
    return found


def review_modules(ctx: RunContext):
    """Steps 2 to 6 and 8: one reviewer, and optionally one checker, per reviewable Module."""
    prompt = load_prompt("review-spec")
    found: list[dict] = []
    for review in _state(ctx).reviews.values():
        if review.stop is None:
            found.extend(_review(ctx, review, prompt))
    return Continue(evidence=found)


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
                and (finding.get("check") or {}).get("status") != "disputed"
            ),
        }
        for item in modules
    ]


def unsettled(review: ModuleReview) -> list[dict]:
    """The findings of a Module that stopped before the host settled them, without the earlier
    Issue each claimed: a payload finding names only an offered Issue it was appended to."""
    return [
        {key: value for key, value in finding.items() if key != "earlier"}
        for finding in review.findings
    ]


def derive_verdict(ctx: RunContext):
    """Step 7 and the verdict: counted by the host from the findings, never taken from a worker."""
    reviews = list(_state(ctx).reviews.values())
    modules = [
        {
            "module": review.module,
            "outcome": review.outcome,
            "context_identity": review.context_identity,
            "findings": review.findings if review.settled else unsettled(review),
            "rejected": review.rejected,
            "earlier_issues": review.summary,
        }
        for review in reviews
    ]
    outcomes = {item["outcome"] for item in modules}
    verdict = next(value for value in reversed(OUTCOMES) if value in outcomes)
    payload = {
        "verdict": verdict,
        "modules": modules,
        "workflow": review_output("spec_review", verdict, blocking_counts(modules)),
    }
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    incomplete = [review for review in reviews if review.stop is not None]
    standing = sum(review.standing for review in reviews if review.stop is None)
    counts = f"{standing} blocking Issue(s) stand{review_issues.statement(ctx)}"
    if not incomplete:
        return Stop("ok", f"Spec review: {verdict}; {counts}.")
    status = (
        "failed" if any(r.stop.status == "failed" for r in incomplete) else "blocked"
    )
    names = ", ".join(review.module for review in incomplete)
    reasons = "; ".join(f"{r.module}: {r.stop.summary}" for r in incomplete)
    return ctx.fail(
        status,
        "review_incomplete",
        f"Spec review: incomplete for {names} ({reasons}); {counts}.",
        f"the review of {len(incomplete)} of {len(reviews)} Module(s) is incomplete, each a "
        f"cause below: {reasons}; {counts} in the reviewed Modules",
        reason="decision",
        explanation="spec_review reviews each Module once and never repairs or reruns; how "
        "to complete the review is the main agent's decision",
        causes=[review.stop.error for review in incomplete],
        options=["address each cause, then run spec_review again for those Modules"],
    )


def add_arguments(parser) -> None:
    parser.add_argument(
        "--check-findings",
        action="store_true",
        help="launch a checker that confirms or disputes each finding",
    )


SPEC_REVIEW = operation(
    "spec_review",
    TASK_TYPE,
    False,
    (validate_modules, review_modules, derive_verdict),
    PAYLOAD_SCHEMA,
    add_arguments,
    binding="optional",
    workers=("reviewer", "checker"),
)

__all__ = [
    "ARCHITECTURE_DIMENSIONS",
    "CHECKER_OUTPUT",
    "DIMENSIONS",
    "PAYLOAD_SCHEMA",
    "REVIEWER_OUTPUT",
    "SPEC_REVIEW",
]
