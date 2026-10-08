"""The ``project_review`` Operation (see the Project review Module Spec).

One review of the whole project, unbound in the primary worktree or in a bound workspace, that
changes no Spec or code and reports what it finds as Issues:

1. ``check_worker_models`` (Method's admission of every worker).
2. ``prepare``: the whole project's structural validation (Spec review's first step), the identity
   of what each part of the review would judge, the review record and what the run skips. The
   admission does this work, so that it refuses with ``nothing_to_review`` a run whose every
   worker part would be skipped; the step returns what it found.
3. ``deterministic``: every configured check of the covered Modules, the scenarios no test
   verifies and the files bound to no Module, settled with their earlier Issues and reported.
4. ``review_architecture``: one project-wide architecture review, architects and a chair, run as
   a Spec panel graph without reviewers.
5. ``review_modules``: per covered Module, a Spec panel of reviewers and a chair and a Module-scope
   code review, each skipped when what it would judge is unchanged since it was last judged; at
   most ``--parallel`` of them at once.
6. ``publish_record``: the parts this run completed, merged into the review record on the primary
   branch.
7. ``derive_verdict``: each Module's outcome from the Issues that stand, the project verdict and
   the result.

Worker findings, merges, tiers, severities and resolutions are worker claims; the host's own facts
(validation, checks, coverage, unowned files, identities, skips, grants, audits, accounting, the
Issues it reported to, the record it published) are host evidence.
"""

from __future__ import annotations

import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ...execution.context import Continue, Refused, RunContext, Stop, evidence
from ...kernel.schema import digest
from ...spec.errors import SpecError
from ...spec.grants import grant
from ...spec.repository import SpecRepository
from ...spec.schema import validate
from ...spec.repository_base import read_file
from ...execution.checks.checks import CheckError
from .. import review_issues
from ..checks import run_module_checks
from ..code_review import operation as code_review
from ..prompts import load_prompt
from ..specs import admission
from ..spec_review import panel as spec_panel
from ..spec_review import review
from ..workers import grant_failure, operation
from . import findings, record

OUTCOMES = ["accepted", "changes_required", "incomplete"]
STATES = ["reviewed", "skipped", "not_run"]
DEFAULT_PARALLEL = 2
MAX_PARALLEL = 8
CODE_REVIEWER = "code_reviewer"
ARCHITECTURE_CHAIR = "arch_chair"
# The worker ids: the Spec panels' reviewer seats and chair, the architecture review's architects
# and chair, and the Module-scope code reviewer.
WORKERS = (
    *spec_panel.REVIEWERS,
    "chair",
    *spec_panel.ARCHITECTS,
    ARCHITECTURE_CHAIR,
    CODE_REVIEWER,
)
# The subject name of the architecture review, which reports for the whole project.
PROJECT = "project"
# The reports whose Issues each part offers as earlier Issues, by Operation and phase: the
# architects' findings of spec_panel, of its phase architecture, go to the architecture review,
# which has architects, rather than to the Module panels, which have none.
PANEL_SOURCES = {"spec_panel": ("report",), "project_review": ("spec-panel",)}
ARCHITECTURE_SOURCES = {
    "spec_panel": ("architecture",),
    "project_review": ("architecture",),
}
# The reviews whose open Issues decide what stands for a Module.
STANDING_SOURCES = ("spec_panel", "code_review", "project_review")
SEVERITY_KEYS = [*review_issues.SEVERITIES, "unrated"]
TIER_KEYS = [*review_issues.TIERS, "unrated"]

_STRING = {"type": "string", "minLength": 1}
_IDENTITY = {
    "anyOf": [{"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}, {"type": "null"}]
}
_ISSUE = {"type": "string", "pattern": "^I-[0-9a-f]{32}$"}
_STANDING = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issue", "severity", "tier", "title"],
    "properties": {
        "issue": _ISSUE,
        "severity": {
            "anyOf": [{"enum": list(review_issues.SEVERITIES)}, {"type": "null"}]
        },
        "tier": {"anyOf": [{"enum": list(review_issues.TIERS)}, {"type": "null"}]},
        "title": _STRING,
    },
}
_RESOLVED = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issue", "reason"],
    "properties": {"issue": _ISSUE, "reason": _STRING},
}
_PART = {
    "type": "object",
    "additionalProperties": False,
    "required": ["state", "review"],
    "properties": {"state": {"enum": STATES}, "review": {}},
}
_COUNTS = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issues", "blocking", "by_severity", "by_tier"],
    "properties": {
        "issues": {"type": "integer", "minimum": 0},
        "blocking": {"type": "integer", "minimum": 0},
        "by_severity": {
            "type": "object",
            "additionalProperties": False,
            "required": SEVERITY_KEYS,
            "properties": {
                key: {"type": "integer", "minimum": 0} for key in SEVERITY_KEYS
            },
        },
        "by_tier": {
            "type": "object",
            "additionalProperties": False,
            "required": TIER_KEYS,
            "properties": {key: {"type": "integer", "minimum": 0} for key in TIER_KEYS},
        },
    },
}

# contract.project-review.report, version 1 (contracts.md); a test keeps the two equal.
PAYLOAD_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "verdict",
        "full",
        "validation",
        "checks",
        "deterministic",
        "architecture",
        "modules",
        "standing",
        "record",
        "workflow",
    ],
    "properties": {
        "verdict": {"enum": OUTCOMES},
        "full": {"type": "boolean"},
        # The workflow object of the step output convention, whose own contract defines it.
        "workflow": {"type": "object"},
        "validation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["errors", "warnings"],
            "properties": {
                "errors": {"type": "integer", "minimum": 0},
                "warnings": {"type": "integer", "minimum": 0},
            },
        },
        "checks": {"type": "array", "items": code_review.CHECK_SCHEMA},
        "deterministic": {
            "type": "object",
            "additionalProperties": False,
            "required": ["complete", "findings", "unowned", "earlier_issues"],
            "properties": {
                "complete": {"type": "boolean"},
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "phase",
                            "module",
                            "title",
                            "tier",
                            "severity",
                            "subjects",
                            "issue",
                        ],
                        "properties": {
                            "phase": {"enum": list(findings.PHASES)},
                            "module": _STRING,
                            "title": _STRING,
                            "tier": {"enum": list(review_issues.TIERS)},
                            "severity": {"enum": list(review_issues.SEVERITIES)},
                            "subjects": {
                                "type": "array",
                                "minItems": 1,
                                "items": _STRING,
                            },
                            "issue": {"anyOf": [_ISSUE, {"type": "null"}]},
                            "earlier": _ISSUE,
                        },
                    },
                },
                "unowned": {"type": "array", "items": _STRING},
                "earlier_issues": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["carried", "resolved"],
                            "properties": {
                                "carried": {"type": "array", "items": _STANDING},
                                "resolved": {"type": "array", "items": _RESOLVED},
                            },
                        },
                    ]
                },
            },
        },
        "architecture": {
            "type": "object",
            "additionalProperties": False,
            "required": ["state", "complete", "context_identity", "review"],
            "properties": {
                "state": {"enum": ["reviewed", "skipped", "left_out"]},
                "complete": {"type": "boolean"},
                "context_identity": _IDENTITY,
                "review": {
                    "anyOf": [
                        {"type": "null"},
                        spec_panel.PAYLOAD_SCHEMA["properties"]["modules"]["items"],
                    ]
                },
            },
        },
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "module",
                    "outcome",
                    "identities",
                    "panel",
                    "code_review",
                    "standing",
                ],
                "properties": {
                    "module": _STRING,
                    "outcome": {"enum": OUTCOMES},
                    "identities": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["spec", "code", "code_digest"],
                        "properties": {
                            "spec": _IDENTITY,
                            "code": _IDENTITY,
                            "code_digest": _IDENTITY,
                        },
                    },
                    "panel": {
                        **_PART,
                        "properties": {
                            "state": {"enum": STATES},
                            "review": {
                                "anyOf": [
                                    {"type": "null"},
                                    spec_panel.PAYLOAD_SCHEMA["properties"]["modules"][
                                        "items"
                                    ],
                                ]
                            },
                        },
                    },
                    "code_review": {
                        **_PART,
                        "properties": {
                            "state": {"enum": STATES},
                            "review": {
                                "anyOf": [
                                    {"type": "null"},
                                    code_review.REVIEW_SCHEMA["properties"]["modules"][
                                        "items"
                                    ],
                                ]
                            },
                        },
                    },
                    "standing": {"type": "array", "items": _STANDING},
                },
            },
        },
        "standing": _COUNTS,
        "record": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "published", "commit", "modules", "architecture"],
            "properties": {
                "path": _STRING,
                "published": {"type": "boolean"},
                "commit": {"anyOf": [_STRING, {"type": "null"}]},
                "modules": {"type": "array", "items": _STRING},
                "architecture": {"type": "boolean"},
            },
        },
    },
    "$defs": copy.deepcopy(spec_panel.PAYLOAD_SCHEMA["$defs"]),
}


@dataclass
class Identities:
    """What each part of a Module's review would judge: the context identities of its
    ``review-spec`` and ``review-code`` grants and the digest of its bound files."""

    spec: str | None = None
    code: str | None = None
    code_digest: str | None = None


@dataclass
class ProjectReview:
    """The run's state, kept on the run context between steps."""

    repository: SpecRepository | None = None
    identities: dict[str, Identities] = field(default_factory=dict)
    architecture_identity: str | None = None
    # Whether the issues part is installed, and the review record read from the primary branch.
    issues: bool = False
    primary: Path | None = None
    judged: dict = field(default_factory=record.empty)
    record_problem: str | None = None
    # Step 2's outcome, which the admission computes.
    prepared: Continue | Stop | None = None
    # Per Module, the parts it reviews: "reviewed", "skipped" or "not_run".
    panel_state: dict[str, str] = field(default_factory=dict)
    code_state: dict[str, str] = field(default_factory=dict)
    architecture_state: str = "left_out"
    # The deterministic step.
    checks: list[dict] = field(default_factory=list)
    problems: list = field(default_factory=list)
    unowned: list[str] = field(default_factory=list)
    settlement: findings.Settlement | None = None
    deterministic_stops: list[Stop] = field(default_factory=list)
    # The Modules whose deterministic problems are not all known or written, or which an
    # architecture finding concerns that was not written: their outcome cannot come from Issues.
    unrecorded: set[str] = field(default_factory=set)
    # The reviews.
    architecture: review.ModuleReview | None = None
    architecture_panel: dict | None = None
    panels: dict[str, dict] = field(default_factory=dict)
    code: code_review.CodeReview | None = None
    # The record this run published.
    published: str | None = None
    recorded: list[str] = field(default_factory=list)
    recorded_architecture: bool = False
    record_stop: Stop | None = None


def _state(ctx: RunContext) -> ProjectReview:
    return ctx.state.setdefault("project_review", ProjectReview())


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- admission ---------------------------------------------------------------------------------


def admit(context: RunContext) -> None:
    """Method's admission of the named Modules, then every Module in the registry's order; without
    ``--modules``, every Module the examined worktree registers, bound or unbound, whatever the
    binding names. Then step 2's work, which decides the skips, so that a run whose every worker
    part would be skipped is refused with ``nothing_to_review`` before any step."""
    _admit_modules(context)
    state = _state(context)
    state.prepared = _prepare(context)
    if isinstance(state.prepared, Continue) and _nothing_to_review(context):
        raise Refused(
            "nothing_to_review",
            "every part this run covers was already judged: each covered Module's Spec panel "
            "and code review"
            + (
                " and the architecture review are"
                if state.architecture_state == "skipped"
                else " are"
            )
            + f" unchanged since the review record {record.PATH} recorded them, so no worker "
            "would run; their outcomes are the Issues that stand; run with --full to review "
            "them anyway",
            actor="Project review (admission)",
            reason="input",
            explanation="an Operation launches a worker in every run it does not refuse, and "
            "reviewing an unchanged part again is the caller's choice",
            options=[
                "run project_review --full to review every part anyway",
                "read the Issues that stand with issue_list",
            ],
        )


def _nothing_to_review(context: RunContext) -> bool:
    """Whether the record skips every worker part: each covered Module's Spec panel and code
    review, and the architecture review unless ``--architects 0`` leaves it out."""
    state = _state(context)
    parts = [*state.panel_state.values(), *state.code_state.values()]
    if state.architecture_state != "left_out":
        parts.append(state.architecture_state)
    return bool(parts) and all(value == "skipped" for value in parts)


def _admit_modules(context: RunContext) -> None:
    if context.modules_named:
        admission()(context)
    try:
        registered = list(SpecRepository(context.worktree).modules)
        context.modules = (
            [module for module in registered if module in context.modules]
            if context.modules_named
            else registered
        )
    except (SpecError, OSError, ValueError) as error:
        detail = error.describe() if isinstance(error, SpecError) else str(error)
        raise Refused(
            "specs_unloadable",
            f"the Specs of {context.worktree} cannot be loaded: {detail}",
            actor="Method (Module admission)",
            reason="scope",
            explanation="project_review reviews every Module the Specs register, which must "
            "load",
            options=["run concorde spec-validation to see why the Specs do not load"],
        ) from error


# --- step 2: prepare ---------------------------------------------------------------------------


def code_digest(repository: SpecRepository, module: str) -> str:
    """The digest of the paths and bytes of every file the Module binds."""
    return digest(
        [
            (path, digest(read_file(repository.root, path)))
            for path in repository.bound_files(module)
        ]
    )


def _identities(
    ctx: RunContext, repository: SpecRepository, subject
) -> Identities | None:
    module = subject.module
    try:
        return Identities(
            grant(repository, [module], spec_panel.TASK_TYPE).value["context_identity"],
            grant(repository, [module], code_review.TASK_TYPE).value[
                "context_identity"
            ],
            code_digest(repository, module),
        )
    except (SpecError, OSError, ValueError) as error:
        subject.stop = grant_failure(
            ctx, "review-spec and review-code", [module], error
        )
        return None


def _issues_installed(ctx: RunContext) -> bool:
    """Whether the issues part answers; ``Refusal`` passes when it cannot be read."""
    try:
        review_issues.call(ctx, "list", "--status", "open")
    except review_issues.Absent:
        return False
    return True


def prepare(ctx: RunContext):
    """Step 2: what the admission found when it validated the whole project, computed what each
    part would judge, read the review record and decided what this run skips."""
    return _state(ctx).prepared


def _prepare(ctx: RunContext) -> Continue | Stop:
    validated = review.validate_modules(ctx)
    if isinstance(validated, Stop):
        return validated
    found = list(validated.evidence)
    state = _state(ctx)
    subjects = review._state(ctx).reviews
    repository = state.repository = review._state(ctx).repository
    for module, subject in subjects.items():
        if subject.stop is None:
            identities = _identities(ctx, repository, subject)
            if identities is not None:
                state.identities[module] = identities
    full = ctx.arguments.full
    try:
        state.issues = _issues_installed(ctx)
    except review_issues.Refusal as refusal:
        return ctx.fail(
            "failed",
            "issues_unreadable",
            "The project's Issues cannot be read.",
            f"the project's Issues could not be read: {refusal}",
            reason="environment",
            explanation="a project review builds on and reports to the project's Issues; a "
            "failure of the Issue system is never reported as an Issue",
            evidence=found,
            causes=[refusal.link],
            options=["repair the Issue records (issue_check), then run again"],
        )
    if not state.issues:
        found.append(
            evidence(
                "skip",
                "all",
                "nothing is skipped and no review record is written: "
                + review_issues.NOT_RECORDED,
            )
        )
    else:
        try:
            state.primary = record.primary_of(ctx.started_in)
            if not full:
                state.judged = record.read(state.primary)
        except record.RecordError as error:
            state.record_problem = f"{error.code}: {error}"
            found.append(
                evidence(
                    "review-record",
                    record.PATH,
                    f"the review record cannot be read, so nothing is skipped ({error.code}: "
                    f"{error})",
                )
            )
    judged = state.judged["modules"]
    for module, subject in subjects.items():
        identities = state.identities.get(module)
        if subject.stop is not None or identities is None:
            state.panel_state[module] = state.code_state[module] = "not_run"
            continue
        last = judged.get(module, {}) if state.issues else {}
        panel = last.get("panel") or {}
        code = last.get("code_review") or {}
        state.panel_state[module] = (
            "skipped"
            if panel.get("context_identity") == identities.spec
            else "reviewed"
        )
        state.code_state[module] = (
            "skipped"
            if (code.get("context_identity"), code.get("code_digest"))
            == (identities.code, identities.code_digest)
            else "reviewed"
        )
        for part, value, entry in (
            ("panel", state.panel_state[module], panel),
            ("code_review", state.code_state[module], code),
        ):
            if value == "skipped":
                found.append(
                    evidence(
                        "skip",
                        module,
                        f"its {part} is skipped: what it would judge is unchanged since run "
                        f"{entry['run']} judged it at {entry.get('commit') or 'its worktree'}",
                    )
                )
    if ctx.arguments.architects:
        try:
            state.architecture_identity = grant(
                repository, list(repository.modules), spec_panel.ARCHITECTURE_TASK_TYPE
            ).value["context_identity"]
        except (SpecError, OSError, ValueError) as error:
            # The architecture review alone cannot run; every other part goes on.
            state.architecture_state = "reviewed"
            state.architecture = review.ModuleReview(PROJECT)
            state.architecture.stop = grant_failure(
                ctx, spec_panel.ARCHITECTURE_TASK_TYPE, list(repository.modules), error
            )
            found.extend(state.architecture.stop.evidence)
            return Continue(evidence=found)
        last = state.judged["architecture"] if state.issues else None
        if last and last["context_identity"] == state.architecture_identity:
            state.architecture_state = "skipped"
            found.append(
                evidence(
                    "skip",
                    PROJECT,
                    f"the architecture review is skipped: every Module's Specs are unchanged "
                    f"since run {last['run']} judged them",
                )
            )
        else:
            state.architecture_state = "reviewed"
    return Continue(evidence=found)


# --- step 3: the deterministic findings --------------------------------------------------------


def deterministic(ctx: RunContext):
    """Step 3: run every configured check of the covered Modules, find the scenarios no test
    verifies and the files bound to no Module, and report them as Issues."""
    state = _state(ctx)
    repository = state.repository
    covered = [module for module in ctx.modules if module in repository.modules]
    found: list[dict] = []
    examined: dict[str, set[str]] = {"coverage": set(covered)}
    try:
        state.checks = run_module_checks(
            ctx.worktree,
            covered,
            trace_directory=ctx.run_dir / "checks",
            repository=repository,
            report=ctx.evidence,
        )
        examined["check"] = set(covered)
    except (CheckError, SpecError, OSError) as error:
        stop = ctx.checks_unavailable(error, covered)
        state.deterministic_stops.append(stop)
        # Whether these Modules' checks pass is unknown, and so is their outcome.
        state.unrecorded.update(covered)
        found.extend(stop.evidence)
    found += [
        evidence(
            "check",
            item["check_id"],
            f"{item['status']}, exit {item['exit_code']}; log {item['log']}",
        )
        for item in state.checks
    ]
    identities = state.identities
    problems = findings.check_problems(
        ctx,
        state.checks,
        {module: item.code_digest for module, item in identities.items()},
    )
    problems += findings.coverage_problems(
        ctx,
        repository,
        covered,
        {module: item.spec for module, item in identities.items()},
    )
    root = repository.root_module
    unowned = findings.unowned_paths(repository)
    if unowned is None:
        # Git could not list the tracked files: no unowned problem is known, none resolved.
        found.append(
            evidence(
                "unowned",
                root,
                "the tracked files could not be listed, so the files bound to no Module "
                "were not examined",
            )
        )
    else:
        state.unowned = unowned
        examined["unowned"] = {root}
        problem = findings.unowned_problem(ctx, root, unowned)
        if problem is not None:
            problems.append(problem)
        found.append(
            evidence(
                "unowned", root, f"{len(unowned)} tracked file(s) bound to no Module"
            )
        )
    state.problems = problems
    reported, settlement, stop = findings.settle_and_report(ctx, problems, examined)
    found.extend(reported)
    state.settlement = settlement if state.issues else None
    if stop is not None:
        state.deterministic_stops.append(stop)
        # A Module whose problem was not written cannot take its outcome from its Issues.
        state.unrecorded.update(
            problem.module for problem in problems if problem.issue is None
        )
        found.extend(stop.evidence)
    return Continue(evidence=found)


# --- step 4: the architecture review -----------------------------------------------------------


def architecture_section(
    ctx: RunContext, subject: review.ModuleReview, role: str
) -> str:
    """What the architects and their chair review: every Module among the others."""
    repository = _state(ctx).repository
    listing = "".join(
        f"- `{identity}`: {(ctx.worktree / module.primary_document).as_posix()}\n"
        for identity, module in repository.modules.items()
    )
    goal = ctx.goal.strip()
    return (
        "## This review\n\n"
        f"Your role: {role}.\n\n"
        f"Reviewed Module: `{PROJECT}`, the whole project: every Module below is a reviewed "
        "Module, each with its entry document. Every Module's documents can carry a blocking "
        "finding; a finding's `module` is the Module whose document it cites.\n\n"
        f"{listing}\n"
        "The task's goal, for orientation only; judge the Specs as they are written:\n\n"
        f"{goal or '(none)'}\n"
    )


def review_architecture(ctx: RunContext):
    """Step 4: one project-wide architecture review, unless it is skipped or left out."""
    state = _state(ctx)
    if state.architecture_state != "reviewed" or state.architecture is not None:
        return Continue()
    repository = state.repository
    modules = list(repository.modules)
    subject = state.architecture = review.ModuleReview(
        PROJECT,
        tuple(
            path for module in modules for path in repository.modules[module].documents
        ),
    )
    found: list[dict] = []
    missing = spec_panel.langgraph_missing(ctx)
    if missing is not None:
        subject.stop = missing
        return Continue(evidence=missing.evidence)
    try:
        subject.earlier = review_issues.open_issues(ctx, ARCHITECTURE_SOURCES)
    except review_issues.Refusal as refusal:
        subject.stop = ctx.fail(
            "failed",
            "issues_unreadable",
            "The earlier Issues of the architecture review cannot be read.",
            f"the project's Issues could not be read for the architecture review: {refusal}",
            reason="environment",
            explanation="a review builds on its earlier Issues, which it must be able to read; "
            "a failure of the Issue system is never reported as an Issue",
            causes=[refusal.link],
            options=[
                "repair the Issue records (issue_check), then run the review again"
            ],
        )
        return Continue(evidence=subject.stop.evidence)
    found.append(
        evidence(
            "earlier-issues",
            PROJECT,
            f"{len(subject.earlier)} earlier architecture Issue(s) offered"
            if subject.earlier is not None
            else f"no earlier Issue offered: {review_issues.NOT_RECORDED}",
        )
    )
    panel = spec_panel.Panel(
        ctx,
        subject,
        load_prompt("panel-spec") + "\n" + load_prompt("project-architecture"),
        0,
        ctx.arguments.architects,
        chair_worker=ARCHITECTURE_CHAIR,
        modules=modules,
        section=architecture_section,
    )
    reported, final = spec_panel.run_panel(
        ctx, panel, phase="architecture", earlier=False
    )
    found.extend(reported)
    state.architecture_panel = final
    if subject.stop is not None and subject.settled and state.issues:
        # A refusal of the Issue store left these findings without their Issue.
        state.unrecorded.update(
            item["module"] for item in subject.findings if item.get("issue") is None
        )
    if final is not None:
        subject.context_identity = final["architecture_identity"]
    return Continue(evidence=found)


# --- step 5: the Modules' reviews --------------------------------------------------------------


def _panel_job(
    ctx: RunContext, subject: review.ModuleReview, prompt: str
) -> list[dict]:
    panel = spec_panel.Panel(ctx, subject, prompt, ctx.arguments.reviewers, 0)
    found, final = spec_panel.run_panel(
        ctx, panel, sources=PANEL_SOURCES, phase="spec-panel"
    )
    if final is not None:
        _state(ctx).panels[subject.module] = final
    return found


def _code_job(ctx: RunContext, module: str) -> list[dict]:
    state = _state(ctx)
    return code_review.judge(
        ctx,
        state.code,
        [state.code.reviews[module]],
        worker=CODE_REVIEWER,
        phase="code-review",
    )


def review_modules(ctx: RunContext):
    """Step 5: every covered Module's Spec panel and code review that is not skipped, at most
    ``--parallel`` at once."""
    state = _state(ctx)
    subjects = review._state(ctx).reviews
    state.code = code_review.CodeReview(
        "module",
        {
            module: code_review.ModuleReview(module)
            for module, value in state.code_state.items()
            if value == "reviewed"
        },
        results=state.checks,
    )
    jobs = []
    prompt = None
    for module, subject in subjects.items():
        if state.panel_state.get(module) == "reviewed":
            prompt = prompt or load_prompt("panel-spec")
            jobs.append((_panel_job, (ctx, subject, prompt)))
        if state.code_state.get(module) == "reviewed":
            jobs.append((_code_job, (ctx, module)))
    if not jobs:
        return Continue(evidence=[evidence("reviews", "", "no Module review to run")])
    if any(job is _panel_job for job, _ in jobs):
        missing = spec_panel.langgraph_missing(ctx)
        if missing is not None:
            # No Spec panel can run; the code reviews still do.
            for job, arguments in jobs:
                if job is _panel_job:
                    arguments[1].stop = missing
            jobs = [item for item in jobs if item[0] is not _panel_job]
    found: list[dict] = [
        evidence(
            "reviews",
            "",
            f"{len(jobs)} Module review(s), at most {ctx.arguments.parallel} at once",
        )
    ]
    with ThreadPoolExecutor(max_workers=ctx.arguments.parallel) as pool:
        futures = [pool.submit(job, *arguments) for job, arguments in jobs]
        for (job, arguments), future in zip(jobs, futures, strict=True):
            try:
                found.extend(future.result())
            except Exception as error:  # noqa: BLE001 -- a host defect in one review is that review's
                module = arguments[1] if job is _code_job else arguments[1].module
                stop = ctx.exception(
                    f"project_review {'code review' if job is _code_job else 'Spec panel'} "
                    f"({module})",
                    error,
                    "review_failed",
                    f"The review of {module} stopped on an unexpected error.",
                )
                if job is _code_job:
                    state.code.reviews[module].stop = stop
                else:
                    arguments[1].stop = stop
                found.extend(stop.evidence)
    return Continue(evidence=found)


# --- step 6: the review record -----------------------------------------------------------------


def _resolutions(
    summary: dict | None, earlier: list[dict] | None, revisions: dict[str, str]
) -> dict:
    """The record's ``resolved`` of a part: each earlier Issue it found resolved that is still
    open at the revision the part was offered, with that revision. An Issue that took a report
    after the part read it is left out: its resolution judged older content."""
    offered = {item["issue"]: item.get("revision") for item in earlier or []}
    found = [
        {"issue": item["issue"], "revision": offered[item["issue"]]}
        for item in (summary or {}).get("resolved", [])
        if offered.get(item["issue"])
        and revisions.get(item["issue"]) == offered[item["issue"]]
    ]
    return {"resolved": found} if found else {}


def _completed(ctx: RunContext, revisions: dict[str, str]) -> tuple[dict, dict | None]:
    """The panels and code reviews, by Module, and the architecture review this run completed
    with every Issue written, as record entries; ``revisions`` gives each open Issue's revision."""
    state = _state(ctx)
    judged = {"run": ctx.run_id, "commit": ctx.commit or None, "judged_at": _now()}
    entries: dict[str, dict] = {}
    for module, subject in review._state(ctx).reviews.items():
        identities = state.identities.get(module)
        if identities is None:
            continue
        if (
            state.panel_state.get(module) == "reviewed"
            and subject.stop is None
            and subject.settled
            and subject.context_identity == identities.spec
        ):
            entries.setdefault(module, {})["panel"] = {
                "context_identity": identities.spec,
                **judged,
                **_resolutions(subject.summary, subject.earlier, revisions),
            }
        coded = state.code.reviews.get(module) if state.code else None
        if (
            coded is not None
            and coded.stop is None
            and coded.context_identity == identities.code
        ):
            entries.setdefault(module, {})["code_review"] = {
                "context_identity": identities.code,
                "code_digest": identities.code_digest,
                **judged,
                **_resolutions(coded.settled, coded.earlier, revisions),
            }
    architecture = None
    subject = state.architecture
    if (
        subject is not None
        and subject.stop is None
        and subject.settled
        and state.architecture_identity is not None
    ):
        architecture = {
            "context_identity": state.architecture_identity,
            **judged,
            **_resolutions(subject.summary, subject.earlier, revisions),
        }
    return entries, architecture


def publish_record(ctx: RunContext):
    """Step 6: merge what this run completed into the review record on the primary branch."""
    state = _state(ctx)
    if not state.issues:
        return Continue()
    try:
        revisions = {
            row["id"]: row["revision"]
            for row in review_issues.call(ctx, "list", "--status", "open")["issues"]
        }
    except review_issues.Refusal as refusal:
        # Without the revisions no resolution can be recorded reliably, so nothing is.
        state.record_stop = ctx.fail(
            "failed",
            "record_unpublished",
            "The review record could not be published.",
            f"the open Issues could not be listed to record the resolutions of this run's "
            f"parts, so the review record {record.PATH} was not written: {refusal}",
            reason="environment",
            explanation="a part is recorded with the resolutions it found, which the host "
            "binds to the Issues' revisions; a failure of the Issue system is never reported "
            "as an Issue",
            causes=[refusal.link],
            options=[
                "repair the Issue records (issue_check), then run project_review again"
            ],
        )
        return Continue(evidence=state.record_stop.evidence)
    entries, architecture = _completed(ctx, revisions)

    def update(current: dict) -> dict:
        for module, parts in entries.items():
            current["modules"].setdefault(module, {}).update(parts)
        if architecture is not None:
            current["architecture"] = architecture
        return current

    try:
        primary = state.primary or record.primary_of(ctx.started_in)
        state.published = record.publish(
            primary,
            f"project_review {ctx.run_id} (review record)",
            update,
            f"concorde: record project_review {ctx.run_id}\n\n"
            + "".join(f"Reviewed: {module}\n" for module in entries),
        )
    except record.RecordError as error:
        state.record_stop = ctx.fail(
            "failed",
            "record_unpublished",
            "The review record could not be published.",
            f"the review record {record.PATH} could not be published in the primary worktree: "
            f"{error.code}: {error}; the reviews' Issues are written, but the next run reviews "
            "again what this one judged",
            reason=error.reason,
            explanation="the record is committed only on the primary branch under the merge "
            "lock, and the host neither retries nor repairs it",
            evidence=[evidence("review-record", record.PATH, f"{error.code}: {error}")],
            options=[
                "fix what the cause names in the primary worktree, then run project_review "
                "again"
            ],
        )
        return Continue(evidence=state.record_stop.evidence)
    state.recorded = sorted(entries) if state.published else []
    state.recorded_architecture = bool(state.published) and architecture is not None
    return Continue(
        evidence=[
            evidence(
                "review-record",
                state.published or record.PATH,
                f"recorded {len(entries)} Module(s)"
                + (" and the architecture" if architecture is not None else "")
                + ("" if state.published else "; the record was unchanged")
                if entries or architecture is not None
                else "nothing new to record; the record was checked",
            )
        ]
    )


# --- step 7: the verdict -----------------------------------------------------------------------


def _remembered(ctx: RunContext, revisions: dict[str, str]) -> set[str]:
    """The Issues the last judgment of each part this run skipped found resolved, which have not
    changed since: no review of this run judged them, so its resolution still holds."""
    state = _state(ctx)
    entries = []
    for module, parts in state.judged["modules"].items():
        if state.panel_state.get(module) == "skipped":
            entries.append(parts.get("panel") or {})
        if state.code_state.get(module) == "skipped":
            entries.append(parts.get("code_review") or {})
    if state.architecture_state == "skipped":
        entries.append(state.judged["architecture"] or {})
    return {
        item["issue"]
        for entry in entries
        for item in entry.get("resolved", [])
        if revisions.get(item["issue"]) == item["revision"]
    }


def _resolved(ctx: RunContext, revisions: dict[str, str]) -> set[str]:
    """Every earlier Issue a part of this run found resolved and that is unchanged since the
    part was offered it: a report appended meanwhile is content the part never judged."""
    state = _state(ctx)
    found: set[str] = set()
    parts = [
        (subject.summary, subject.earlier)
        for subject in review._state(ctx).reviews.values()
    ]
    if state.architecture is not None:
        parts.append((state.architecture.summary, state.architecture.earlier))
    if state.code is not None:
        parts += [(item.settled, item.earlier) for item in state.code.reviews.values()]
    for summary, earlier in parts:
        found.update(
            item["issue"]
            for item in _resolutions(summary, earlier, revisions).get("resolved", [])
        )
    if state.settlement is not None:
        found.update(item["issue"] for item in state.settlement.resolved)
    return found


def _standing_from_findings(ctx: RunContext) -> dict[str, list[dict]]:
    """Without the issues part: each Module's findings of this run, as the Issues they would
    become."""
    state = _state(ctx)
    standing: dict[str, list[dict]] = {}

    def add(module: str, item: dict) -> None:
        standing.setdefault(module, []).append(
            {
                "issue": None,
                "severity": item.get("severity"),
                "tier": item.get("tier"),
                "title": item["title"],
            }
        )

    for subject in review._state(ctx).reviews.values():
        for item in subject.findings:
            add(item["module"], item)
    if state.architecture is not None:
        for item in state.architecture.findings:
            add(item["module"], item)
    if state.code is not None:
        for coded in state.code.reviews.values():
            for item in coded.findings:
                add(item["module"], item)
    for problem in state.problems:
        add(
            problem.module,
            {
                "tier": problem.tier,
                "severity": problem.severity,
                "title": problem.title,
            },
        )
    return standing


def _counts(items: list[dict]) -> dict:
    severities = dict.fromkeys(SEVERITY_KEYS, 0)
    tiers = dict.fromkeys(TIER_KEYS, 0)
    for item in items:
        severities[item["severity"] or "unrated"] += 1
        tiers[item["tier"] or "unrated"] += 1
    return {
        "issues": len(items),
        "blocking": sum(1 for item in items if review_issues.is_blocking(item["tier"])),
        "by_severity": severities,
        "by_tier": tiers,
    }


def _part(value: str, payload: dict | None) -> dict:
    return {"state": value, "review": payload if value == "reviewed" else None}


def derive_verdict(ctx: RunContext):
    """Step 7: each Module's outcome from the Issues that stand, the project verdict and the
    result, all derived by the host."""
    state = _state(ctx)
    subjects = review._state(ctx).reviews
    stops: list[tuple[str, Stop]] = []
    standing_stop = None
    if state.issues:
        try:
            rows = review_issues.open_issues(ctx, STANDING_SOURCES) or []
        except review_issues.Refusal as refusal:
            rows = []
            standing_stop = ctx.fail(
                "failed",
                "issues_unreadable",
                "The Issues that stand cannot be read.",
                f"the project's Issues could not be read after the reviews: {refusal}",
                reason="environment",
                explanation="each Module's outcome comes from the Issues that stand, which the "
                "host must be able to read",
                causes=[refusal.link],
                options=["repair the Issue records (issue_check), then run again"],
            )
            stops.append(("standing Issues", standing_stop))
        revisions = {row["issue"]: row["revision"] for row in rows}
        resolved = _resolved(ctx, revisions) | _remembered(ctx, revisions)
        standing: dict[str, list[dict]] = {}
        for row in rows:
            if row["issue"] not in resolved and row["module"] in subjects:
                standing.setdefault(row["module"], []).append(
                    {key: row[key] for key in ("issue", "severity", "tier", "title")}
                )
    else:
        standing = {
            module: items
            for module, items in _standing_from_findings(ctx).items()
            if module in subjects
        }
    modules = []
    for module, subject in subjects.items():
        coded = state.code.reviews.get(module) if state.code else None
        identities = state.identities.get(module) or Identities()
        own = standing.get(module, [])
        incomplete = [
            (f"{module} {part}", stop)
            for part, stop in (
                ("Spec panel", subject.stop),
                ("code review", coded.stop if coded is not None else None),
            )
            if stop is not None
        ]
        for name, stop in incomplete:
            if all(stop is not other for _, other in stops):
                stops.append((name, stop))
        if incomplete or standing_stop is not None or module in state.unrecorded:
            outcome = "incomplete"
        elif any(review_issues.is_blocking(item["tier"]) for item in own):
            outcome = "changes_required"
        else:
            outcome = "accepted"
        panel_state = state.panel_state.get(module, "not_run")
        code_state = state.code_state.get(module, "not_run")
        modules.append(
            {
                "module": module,
                "outcome": outcome,
                "identities": {
                    "spec": identities.spec,
                    "code": identities.code,
                    "code_digest": identities.code_digest,
                },
                "panel": _part(
                    panel_state,
                    spec_panel.module_payload(subject, state.panels.get(module))
                    if panel_state == "reviewed"
                    else None,
                ),
                "code_review": _part(
                    code_state,
                    {
                        "module": module,
                        "outcome": coded.outcome,
                        "context_identity": coded.context_identity,
                        "summary": coded.summary,
                        "findings": coded.findings,
                        "rejected": coded.rejected,
                        "earlier_issues": coded.settled,
                    }
                    if coded is not None
                    else None,
                ),
                "standing": [item for item in own if item["issue"]],
            }
        )
    subject = state.architecture
    architecture_complete = subject is None or subject.stop is None
    if subject is not None and subject.stop is not None:
        stops.append(("the architecture review", subject.stop))
    for stop in state.deterministic_stops:
        stops.append(("the deterministic findings", stop))
    project_incomplete = not architecture_complete or bool(state.deterministic_stops)
    verdict = max(
        [item["outcome"] for item in modules]
        + (["incomplete"] if project_incomplete or standing_stop else ["accepted"]),
        key=OUTCOMES.index,
    )
    validation = review._state(ctx).validation
    summary_counts = validation.result.get("summary", {}) if validation else {}
    everything = [item for values in standing.values() for item in values]
    payload = {
        "verdict": verdict,
        "full": bool(ctx.arguments.full),
        "validation": {
            "errors": int(summary_counts.get("errors", 0)),
            "warnings": int(summary_counts.get("warnings", 0)),
        },
        "checks": code_review.check_results(state.checks),
        "deterministic": {
            "complete": not state.deterministic_stops,
            "findings": [problem.payload() for problem in state.problems],
            "unowned": state.unowned,
            "earlier_issues": None
            if state.settlement is None
            else {
                "carried": state.settlement.carried,
                "resolved": state.settlement.resolved,
            },
        },
        "architecture": {
            "state": state.architecture_state,
            "complete": architecture_complete,
            "context_identity": state.architecture_identity,
            "review": spec_panel.module_payload(subject, state.architecture_panel)
            if subject is not None
            else None,
        },
        "modules": modules,
        "standing": _counts(everything),
        "record": {
            "path": record.PATH,
            "published": state.published is not None,
            "commit": state.published,
            "modules": state.recorded,
            "architecture": state.recorded_architecture,
        },
        "workflow": review_issues.review_output(
            "project_review",
            verdict,
            [
                {
                    "module": item["module"],
                    "outcome": item["outcome"],
                    "blocking": sum(
                        1
                        for entry in item["standing"]
                        if review_issues.is_blocking(entry["tier"])
                    ),
                }
                for item in modules
            ],
        ),
    }
    validate(payload, PAYLOAD_SCHEMA)
    ctx.output = payload
    reviewed = sum(
        1
        for module in subjects
        for part in (state.panel_state, state.code_state)
        if part.get(module) == "reviewed"
    )
    skipped = sum(
        1
        for module in subjects
        for part in (state.panel_state, state.code_state)
        if part.get(module) == "skipped"
    )
    counts = (
        f"{len(modules)} Module(s), {reviewed} review(s) run and {skipped} skipped, "
        f"architecture {state.architecture_state}; {payload['standing']['blocking']} blocking "
        f"Issue(s) of {payload['standing']['issues']} stand{review_issues.statement(ctx)}"
    )
    if state.record_stop is not None:
        stops.append(("review record", state.record_stop))
    if not stops:
        return Stop("ok", f"Project review: {verdict}; {counts}.")
    status = (
        "failed" if any(stop.status == "failed" for _, stop in stops) else "blocked"
    )
    names = ", ".join(name for name, _ in stops)
    return ctx.fail(
        status,
        "review_incomplete",
        f"Project review: {verdict}, incomplete for {names}; {counts}.",
        f"the project review could not complete {len(stops)} part(s), each a cause below: "
        + "; ".join(f"{name}: {stop.summary}" for name, stop in stops)
        + f"; {counts}",
        reason="decision",
        explanation="project_review runs each part once and never repairs or reruns it; how to "
        "complete the review is the main agent's decision",
        causes=[stop.error for _, stop in stops],
        options=["address each cause, then run project_review again"],
    )


# --- the definition ----------------------------------------------------------------------------


def _count(name: str, low: int, high: int):
    def parse(value: str) -> int:
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"--{name} must be {low} to {high}")
        return number

    return parse


def add_arguments(parser) -> None:
    parser.add_argument(
        "--full",
        action="store_true",
        help="review every covered Module and the architecture, whatever the record says",
    )
    parser.add_argument(
        "--parallel",
        type=_count("parallel", 1, MAX_PARALLEL),
        default=DEFAULT_PARALLEL,
        help=f"the Module reviews run at once (1 to {MAX_PARALLEL}, default "
        f"{DEFAULT_PARALLEL})",
    )
    parser.add_argument(
        "--reviewers",
        type=_count("reviewers", 2, spec_panel.MAX_REVIEWERS),
        default=spec_panel.DEFAULT_REVIEWERS,
        help=f"the reviewers of each Module's Spec panel (2 to {spec_panel.MAX_REVIEWERS}, "
        f"default {spec_panel.DEFAULT_REVIEWERS})",
    )
    parser.add_argument(
        "--architects",
        type=_count("architects", 0, spec_panel.MAX_ARCHITECTS),
        default=spec_panel.DEFAULT_ARCHITECTS,
        help=f"the architects of the project-wide architecture review (0 leaves it out, at most "
        f"{spec_panel.MAX_ARCHITECTS}, default {spec_panel.DEFAULT_ARCHITECTS})",
    )


PROJECT_REVIEW = operation(
    "project_review",
    spec_panel.TASK_TYPE,
    False,
    (
        prepare,
        deterministic,
        review_architecture,
        review_modules,
        publish_record,
        derive_verdict,
    ),
    PAYLOAD_SCHEMA,
    add_arguments,
    admit=admit,
    binding="optional",
    workers=WORKERS,
)

__all__ = ["PAYLOAD_SCHEMA", "PROJECT_REVIEW", "WORKERS", "code_digest"]
