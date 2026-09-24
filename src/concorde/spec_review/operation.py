"""The ``spec_review`` Operation (see the Spec review Operation Spec).

For each named Module the host validates the task worktree's Specs, launches one ``review-spec``
reviewer under that Module's grant, optionally a checker of the reviewer's findings under the same
grant, and derives the Module's outcome and the verdict itself from the findings:

1. ``validate_modules``: load and validate the task worktree's Specs; a loading error fails the
   run, a structural error attributed to a Module makes that Module ``incomplete``.
2. ``review_modules``: per remaining Module, the standard worker sequence for the reviewer and,
   with ``--check-findings``, for the checker (grant, settings, brief, launch, audit, run record).
3. ``derive_verdict``: each Module's outcome, the verdict, and the result.

Reviewer findings and checker statuses are worker claims and travel only in the payload; the
host's own facts (structural findings, grants, audits, scope corrections) are host evidence.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    spec_cause,
    evidence,
    load_prompt,
    spec_finding,
)
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError
from ..spec.schema import ContractError, validate
from ..spec.typed_data import TypedDataError, safe_path
from ..spec.validation import validate_repository

TASK_TYPE = "review-spec"
DIMENSIONS = ["readability", "obligations", "design", "views", "terminology", "context"]
OUTCOMES = ["accepted", "changes_required", "incomplete"]
LOAD_ERROR = "CONCORDE-SOURCE-008"

# A finding as a reviewer returns it; the host adds ``check`` and normalizes ``path``.
REVIEWER_FINDING: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "module",
        "path",
        "dimension",
        "severity",
        "problem",
        "evidence",
        "suggestion",
    ],
    "properties": {
        "module": {"type": "string", "minLength": 1},
        "path": {"type": "string", "minLength": 1},
        "anchor": {"type": "string", "minLength": 1},
        "line": {"type": "integer", "minimum": 1},
        "dimension": {"enum": DIMENSIONS},
        "severity": {"enum": ["blocking", "advisory"]},
        "problem": {"type": "string", "minLength": 1},
        "evidence": {"type": "string", "minLength": 1},
        "suggestion": {"type": "string", "minLength": 1},
    },
}
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": REVIEWER_FINDING}},
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

# contract.spec-review.payload, version 1 (operation.md); a test keeps the two equal.
PAYLOAD_SCHEMA: dict = {
    "type": "object",
    "required": ["verdict", "modules"],
    "additionalProperties": False,
    "properties": {
        "verdict": {"enum": OUTCOMES},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["module", "outcome", "context_identity", "findings"],
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
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [
                                "module",
                                "path",
                                "dimension",
                                "severity",
                                "problem",
                                "evidence",
                                "suggestion",
                                "check",
                            ],
                            "additionalProperties": False,
                            "properties": {
                                "module": {"type": "string", "minLength": 1},
                                "path": {"type": "string", "format": "project-path"},
                                "anchor": {"type": "string", "minLength": 1},
                                "line": {"type": "integer", "minimum": 1},
                                "dimension": {"enum": DIMENSIONS},
                                "severity": {"enum": ["blocking", "advisory"]},
                                "problem": {"type": "string", "minLength": 1},
                                "evidence": {"type": "string", "minLength": 1},
                                "suggestion": {"type": "string", "minLength": 1},
                                "check": {"anyOf": [{"type": "null"}, CHECK_STATUS]},
                            },
                        },
                    },
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
    stop: Stop | None = None

    @property
    def outcome(self) -> str:
        if self.stop is not None:
            return "incomplete"
        standing = [
            item
            for item in self.findings
            if item["severity"] == "blocking"
            and (item["check"] is None or item["check"]["status"] != "disputed")
        ]
        return "changes_required" if standing else "accepted"


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
            if item.severity == "error" and _attributed(repository, module, item)
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
            options=["repair the Specs with specify", "run validate for details"],
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
    goal = str(ctx.task.get("goal") or "").strip()
    return (
        f"## This review\n\n"
        f"Your role: {role}.\n\n"
        f"Reviewed Module: `{review.module}`. Its own documents, the only ones that can carry "
        f"a blocking finding (each has a metadata file with the same name plus `.json`):\n\n"
        f"{documents}\n"
        "The task's goal, for orientation only; judge the Specs as they are written:\n\n"
        f"{goal or '(none)'}\n"
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
    """The payload findings and the host's scope corrections, or None for an unusable path."""
    repository = _state(ctx).repository
    own = {member for path in review.documents for member in (path, path + ".json")}
    findings, corrections = [], []
    for position, item in enumerate(claimed, 1):
        path = _project_path(ctx, item["path"])
        if path is None:
            return None, [
                evidence(
                    "invalid-output",
                    review.module,
                    f"finding {position} names {item['path']!r}, which is not a path in the "
                    "task worktree",
                )
            ]
        finding = {**item, "path": path, "check": None}
        owners = repository.document_targets.get(path.removesuffix(".json"))
        if owners:
            finding["module"] = owners[0]
        if finding["severity"] == "blocking" and path not in own:
            finding["severity"] = "advisory"
            corrections.append(
                evidence(
                    "finding-scope",
                    f"{review.module} finding {position}",
                    f"{path} is not a document of {review.module}; the blocking finding "
                    "counts as advisory",
                )
            )
        findings.append(finding)
    return findings, corrections


def _checker_material(findings: list[dict]) -> str:
    lines = ["## Findings to check\n"]
    for position, item in enumerate(findings, 1):
        lines.append(f"\nFinding {position}:\n\n```json\n")
        lines.append(
            json.dumps(
                {key: value for key, value in item.items() if key != "check"}, indent=2
            )
        )
        lines.append("\n```\n")
    return "".join(lines)


def _review(ctx: RunContext, review: ModuleReview, prompt: str) -> list[dict]:
    """Steps 2 to 6 for one Module; returns the host evidence and sets the review's state."""
    found: list[dict] = []
    launched = len(ctx.worker_runs)
    outcome = ctx.run_worker(
        prompt + "\n" + _task_section(ctx, review, "reviewer"),
        task_type=TASK_TYPE,
        output_schema=REVIEWER_OUTPUT,
        rounds=0,
        modules=[review.module],
    )
    found.extend(_labelled(outcome.evidence, f"{review.module} reviewer"))
    if len(ctx.worker_runs) > launched:
        review.context_identity = _identity(outcome.evidence)
    if isinstance(outcome, Stop):
        outcome.error["actor"] += f", review of {review.module}"
        review.stop = outcome
        return found
    findings, corrections = _normalize(
        ctx, review, (outcome.output or {}).get("findings", [])
    )
    found.extend(corrections)
    if findings is None:
        review.stop = ctx.fail(
            "failed",
            "unusable_finding",
            f"The reviewer of {review.module} returned an unusable finding.",
            f"the reviewer of {review.module} named a path outside the task worktree: "
            + "; ".join(item["detail"] for item in corrections),
            reason="capability",
            explanation="the host checks every finding's path but never corrects a finding "
            "or relaunches the reviewer",
            evidence=corrections,
            options=["run spec_review again"],
        )
        return found
    review.findings = findings
    if not ctx.arguments.check_findings or not findings:
        return found
    outcome = ctx.run_worker(
        prompt
        + "\n"
        + _task_section(ctx, review, "checker")
        + "\n"
        + _checker_material(findings),
        task_type=TASK_TYPE,
        output_schema=CHECKER_OUTPUT,
        rounds=0,
        modules=[review.module],
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


def derive_verdict(ctx: RunContext):
    """Step 7 and the verdict: counted by the host from the findings, never taken from a worker."""
    reviews = list(_state(ctx).reviews.values())
    modules = [
        {
            "module": review.module,
            "outcome": review.outcome,
            "context_identity": review.context_identity,
            "findings": review.findings,
        }
        for review in reviews
    ]
    outcomes = {item["outcome"] for item in modules}
    verdict = next(value for value in reversed(OUTCOMES) if value in outcomes)
    payload = {"verdict": verdict, "modules": modules}
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    incomplete = [review for review in reviews if review.stop is not None]
    standing = sum(
        1
        for item in modules
        for finding in item["findings"]
        if finding["severity"] == "blocking"
        and (finding["check"] is None or finding["check"]["status"] != "disputed")
    )
    counts = f"{standing} blocking finding(s) stand"
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


SPEC_REVIEW = Provider(
    "spec_review",
    TASK_TYPE,
    False,
    (validate_modules, review_modules, derive_verdict),
    PAYLOAD_SCHEMA,
    add_arguments,
)

__all__ = [
    "CHECKER_OUTPUT",
    "PAYLOAD_SCHEMA",
    "REVIEWER_OUTPUT",
    "SPEC_REVIEW",
]
