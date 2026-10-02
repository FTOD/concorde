"""The ``code_review`` Operation (see the Code review Module Spec).

A change review (``--scope change``, the default) judges the workspace's changes since a base
commit: the host computes the bound Modules' ``review-code`` grant and the diff from the base to the
worktree (uncommitted and untracked files included) with contents only for paths the grant makes
readable, and one reviewer judges it. A Module review (``--scope module``) judges each named
Module's whole code: one reviewer per Module, under that Module's grant alone, with no diff. Either
way the host runs the configured checks first, gives each reviewer its Modules' earlier Issues,
checks that every finding's Module, basis and locations hold, reports every finding as an Issue and
derives each Module's outcome and the verdict from the Issues that stand. No reviewer is resumed.

1. ``prepare``: the scope's arguments, the change review's grant, base and diff, and the checks.
2. ``review``: per reviewer, the earlier Issues, the standard worker sequence, the evidence check
   and the Issue reports.
3. ``derive_verdict``: each Module's outcome, the verdict, and the result.

Findings, tiers and resolutions are reviewer claims and travel only in the report; the host's own
facts (base, diff, checks, grants, audits, unresolved evidence, the Issues it reported to) are host
evidence.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    component,
    evidence,
)
from ..workers import grant_failure, operation, run_worker
from ...execution.checks.checks import checked_modules, run_checks
from ...execution.operations.provider import load_prompt
from ...spec.grants import Grant, grant
from ...spec.repository import SpecRepository
from ...spec.repository_base import SpecError, is_identity
from ...spec.schema import ContractError, validate
from ...spec.typed_data import TypedDataError, safe_path
from . import issues

TASK_TYPE = "review-code"
SCOPES = ("change", "module")
KINDS = [
    "violation",
    "defect",
    "missing-test",
    "out-of-scope",
    "spec-gap",
    "spec-challenge",
]
TIERS = list(issues.TIERS)
SEVERITIES = list(issues.SEVERITIES)
OUTCOMES = ["accepted", "changes_required", "incomplete"]
LOG_TAIL = 8_000
DIFF_LIMIT = 300_000

_STRING = {"type": "string", "minLength": 1}
_STRINGS = {"type": "array", "items": _STRING}
ISSUE_ID: dict = {"type": "string", "pattern": issues.ISSUE}
MODULE_ID: dict = {"type": "string", "pattern": "^module\\."}

CHECK_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["check", "module", "outcome", "exit_code", "log"],
    "properties": {
        "check": _STRING,
        "module": MODULE_ID,
        "outcome": {"enum": ["passed", "failed", "timed_out"]},
        "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "log": _STRING,
    },
}

# A finding as a reviewer returns it; the host adds ``issue`` and keeps ``earlier`` only for an
# earlier Issue it offered.
REVIEWER_FINDING: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "module",
        "kind",
        "severity",
        "tier",
        "title",
        "problem",
        "impact",
        "basis",
        "locations",
        "evidence",
        "suggestion",
    ],
    "properties": {
        "module": MODULE_ID,
        "kind": {"enum": KINDS},
        "severity": {"enum": SEVERITIES},
        "tier": {"enum": TIERS},
        "title": _STRING,
        "problem": _STRING,
        "impact": _STRING,
        "basis": _STRING,
        "locations": {"type": "array", "minItems": 1, "items": _STRING},
        "evidence": _STRING,
        "suggestion": _STRING,
        "earlier": _STRING,
    },
}
RESOLVED: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issue", "reason"],
    "properties": {"issue": _STRING, "reason": _STRING},
}
# The reviewer's part of its worker result (``output``); its ``summary`` is the top-level one.
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {"type": "array", "items": REVIEWER_FINDING},
        "resolved": {"type": "array", "items": RESOLVED},
    },
}

FINDING: dict = {
    **REVIEWER_FINDING,
    "required": [*REVIEWER_FINDING["required"], "issue"],
    "properties": {
        **REVIEWER_FINDING["properties"],
        "earlier": ISSUE_ID,
        "issue": {"anyOf": [ISSUE_ID, {"type": "null"}]},
    },
}
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
                            "title": _STRING,
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

# contract.code-review.review, version 4 (contracts.md); a test keeps the two equal.
REVIEW_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "scope",
        "base",
        "focus",
        "reviewed_paths",
        "named_only_paths",
        "checks",
        "verdict",
        "modules",
    ],
    "properties": {
        "scope": {"enum": list(SCOPES)},
        "base": {"anyOf": [_STRING, {"type": "null"}]},
        "focus": {"anyOf": [_STRING, {"type": "null"}]},
        "reviewed_paths": _STRINGS,
        "named_only_paths": _STRINGS,
        "checks": {"type": "array", "items": CHECK_SCHEMA},
        "verdict": {"enum": OUTCOMES},
        "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "module",
                    "outcome",
                    "context_identity",
                    "summary",
                    "findings",
                    "earlier_issues",
                ],
                "properties": {
                    "module": MODULE_ID,
                    "outcome": {"enum": OUTCOMES},
                    "context_identity": {
                        "anyOf": [
                            {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                            {"type": "null"},
                        ]
                    },
                    "summary": {"anyOf": [_STRING, {"type": "null"}]},
                    "findings": {"type": "array", "items": FINDING},
                    "earlier_issues": EARLIER_ISSUES,
                },
            },
        },
    },
}

OUTCOME_NAMES = {"passed": "passed", "failed": "failed", "timeout": "timed_out"}


@dataclass
class ModuleReview:
    """What the host knows about one reviewed Module; ``stop`` is set when it is incomplete."""

    module: str
    context_identity: str | None = None
    summary: str | None = None
    findings: list[dict] = field(default_factory=list)
    stop: Stop | None = None
    # The Module's earlier Issues as offered to its reviewer, and what the review did with them.
    earlier: list[dict] | None = None
    settled: dict | None = None

    def standing(self) -> list[dict]:
        """The Issues of a blocking tier that stand for the Module: reported now or carried."""
        return [
            item
            for item in [*self.findings, *(self.settled or {}).get("carried", [])]
            if issues.is_blocking(item["tier"])
        ]

    @property
    def outcome(self) -> str:
        if self.stop is not None:
            return "incomplete"
        return "changes_required" if self.standing() else "accepted"


@dataclass
class CodeReview:
    """The run's review state, kept on the run context between steps."""

    scope: str
    reviews: dict[str, ModuleReview]
    base: str | None = None
    access: Grant | None = None
    reviewed: list[str] = field(default_factory=list)
    named: list[str] = field(default_factory=list)
    diff: str = ""
    results: list[dict] = field(default_factory=list)


def _state(ctx: RunContext) -> CodeReview:
    return ctx.state.setdefault(
        "code_review",
        CodeReview(
            ctx.arguments.scope,
            {module: ModuleReview(module) for module in ctx.modules},
        ),
    )


def _git(worktree: Path, *arguments: str, check: bool = True):
    return subprocess.run(
        ["git", *arguments],
        cwd=worktree,
        check=check,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


# --- inputs ------------------------------------------------------------------------------------


def resolve_base(ctx: RunContext) -> str | Stop:
    reference = ctx.arguments.base or ctx.base_commit
    if not reference:
        return ctx.fail(
            "failed",
            "no_base",
            "No base commit is known and no --base was given.",
            (
                f"the unbound run in {ctx.worktree} was given no --base"
                if ctx.unbound
                else f"workspace {ctx.workspace_name} binds no base commit and --base was not "
                "given"
            )
            + ", so there is no diff to review",
            reason="input",
            explanation="the diff base comes from the workspace binding or the caller",
            evidence=[evidence("base", "", "no base")],
            options=[
                "pass --base with the commit the reviewed changes start from",
                "review the Modules whole with --scope module",
            ],
        )
    found = _git(
        ctx.worktree, "rev-parse", "--verify", f"{reference}^{{commit}}", check=False
    )
    if found.returncode != 0:
        stderr = found.stderr.decode("utf-8", "replace").strip()
        return ctx.fail(
            "failed",
            "unresolved_base",
            f"The base {reference} cannot be resolved.",
            f"the diff base {reference} does not name a commit in {ctx.worktree}: {stderr}",
            reason="input",
            explanation="the diff base comes from the workspace binding or the caller",
            evidence=[evidence("base", reference, stderr)],
            causes=[
                component(
                    "git rev-parse",
                    "git_failed",
                    f"git rev-parse --verify {reference}^{{commit}} exited "
                    f"{found.returncode}: {stderr}",
                    "input",
                    "Git cannot resolve a name that names no commit",
                )
            ],
            options=["pass --base with a commit of the task branch"],
        )
    return found.stdout.decode().strip()


def _paths(output: bytes) -> list[str]:
    return [
        item for item in output.decode("utf-8", "surrogateescape").split("\0") if item
    ]


def changed_paths(worktree: Path, base: str) -> list[str]:
    """Paths that differ between ``base`` and the worktree, untracked files included."""
    tracked = _paths(
        _git(worktree, "diff", "--name-only", "--no-renames", "-z", base).stdout
    )
    untracked = _paths(
        _git(worktree, "ls-files", "-z", "--others", "--exclude-standard").stdout
    )
    return sorted(set(tracked) | set(untracked))


def readable(access: Grant, path: str) -> bool:
    return access.level(path) in ("ro", "rw")


def diff_text(worktree: Path, base: str, paths: list[str]) -> str:
    """The diff of ``paths`` from ``base`` to the worktree; new untracked files in full."""
    if not paths:
        return ""
    untracked = set(
        _paths(
            _git(
                worktree,
                "ls-files",
                "-z",
                "--others",
                "--exclude-standard",
                "--",
                *paths,
            ).stdout
        )
    )
    tracked = [path for path in paths if path not in untracked]
    parts = []
    if tracked:
        parts.append(
            _git(worktree, "diff", "--no-renames", base, "--", *tracked).stdout.decode(
                "utf-8", "replace"
            )
        )
    for path in sorted(untracked):
        parts.append(
            _git(
                worktree, "diff", "--no-index", "--", "/dev/null", path, check=False
            ).stdout.decode("utf-8", "replace")
        )
    return "".join(parts)


def check_results(results: list[dict]) -> list[dict]:
    shaped = []
    for item in results:
        outcome = OUTCOME_NAMES[item["status"]]
        shaped.append(
            {
                "check": item["check_id"],
                "module": item["module"],
                "outcome": outcome,
                "exit_code": None if outcome == "timed_out" else item["exit_code"],
                "log": Path(item["log"]).as_posix(),
            }
        )
    return shaped


def check_material(results: list[dict]) -> str:
    if not results:
        return "The reviewed Modules have no configured check.\n"
    lines = [
        f"- {item['check_id']} ({item['module']}): {item['status']}, exit code "
        f"{item['exit_code']}, log {item['log']}\n"
        for item in results
    ]
    for item in results:
        if item["status"] != "passed":
            tail = Path(item["log"]).read_bytes()[-LOG_TAIL:].decode("utf-8", "replace")
            lines.append(
                f"\n### Log of {item['check_id']} (last part)\n\n```text\n{tail}\n```\n"
            )
    return "".join(lines)


def prepare(ctx: RunContext):
    """Step 1 and 2: the scope's inputs and the configured checks."""
    state = _state(ctx)
    found: list[dict] = [evidence("scope", state.scope, f"{state.scope} review")]
    if not ctx.modules:
        # No Module was named or bound: Spec core refuses the grant, which says why.
        try:
            grant(SpecRepository(ctx.worktree), ctx.modules, TASK_TYPE)
        except (SpecError, OSError, ValueError) as error:
            return grant_failure(ctx, TASK_TYPE, ctx.modules, error)
    if state.scope == "module":
        if ctx.arguments.base:
            return ctx.fail(
                "failed",
                "base_in_module_scope",
                "A Module review takes no --base.",
                f"--base {ctx.arguments.base} was given to a Module review, which judges each "
                "Module's whole code and has no diff",
                reason="input",
                explanation="the scope and the base come from the caller",
                evidence=[
                    evidence("base", ctx.arguments.base, "given in scope module")
                ],
                options=[
                    "leave out --base for a Module review",
                    "use --scope change to review the change since --base",
                ],
            )
        checked = list(ctx.modules)
    else:
        try:
            state.access = grant(SpecRepository(ctx.worktree), ctx.modules, TASK_TYPE)
        except (SpecError, OSError, ValueError) as error:
            stop = grant_failure(ctx, TASK_TYPE, ctx.modules, error)
            stop.evidence[:0] = found
            return stop
        base = resolve_base(ctx)
        if isinstance(base, Stop):
            base.evidence[:0] = found
            return base
        state.base = base
        changed = changed_paths(ctx.worktree, base)
        state.reviewed = [path for path in changed if readable(state.access, path)]
        state.named = [path for path in changed if not readable(state.access, path)]
        state.diff = diff_text(ctx.worktree, base, state.reviewed)
        found += [
            evidence("base", base, "diff base"),
            evidence(
                "diff",
                base,
                f"{len(state.reviewed)} path(s) with contents, {len(state.named)} by name "
                "only",
            ),
        ]
        checked = None
    try:
        repository = SpecRepository(ctx.worktree)
        modules = checked or checked_modules(repository, ctx.modules)
        state.results = run_checks(
            ctx.worktree, modules=modules, trace_directory=ctx.run_dir / "checks"
        )
    except (SpecError, OSError) as error:
        stop = ctx.checks_unavailable(error)
        stop.evidence[:0] = found
        return stop
    found += [
        evidence(
            "check",
            item["check_id"],
            f"{item['status']}, exit {item['exit_code']}; log {item['log']}",
        )
        for item in state.results
    ]
    return Continue(evidence=found)


# --- the reviewers -----------------------------------------------------------------------------


def _listing(root: str, paths) -> str:
    return "".join(f"- {root}/{path}\n" for path in paths) or "- (none)\n"


def instructions(
    ctx: RunContext, state: CodeReview, reviews: list[ModuleReview], results: list[dict]
) -> str:
    """The reviewer's brief: the Reviewer instructions and this review's material."""
    root = ctx.worktree.as_posix()
    focus = ctx.arguments.focus
    goal = ctx.goal.strip()
    names = ", ".join(f"`{review.module}`" for review in reviews)
    text = (
        load_prompt("review-code")
        + "\n## This review\n\n"
        + f"Scope: {state.scope}.\n\n"
        + (
            f"Reviewed Module: {names}.\n\n"
            if len(reviews) == 1
            else f"Reviewed Modules: {names}.\n\n"
        )
        + "The task's goal, for orientation only; judge the code against the Specs:\n\n"
        + f"{goal or '(none)'}\n\n"
        + (
            f"Focus (look at this first; it does not narrow what you report):\n\n{focus}\n\n"
            if focus
            else ""
        )
    )
    if state.scope == "module":
        module = SpecRepository(ctx.worktree).modules[reviews[0].module]
        text += (
            "Its own Spec documents (each has a metadata file with the same name plus "
            "`.json`):\n\n"
            + _listing(root, module.documents)
            + "\nIts code and tests, the entries of its realizations (a directory stands for "
            "every file below it):\n\n" + _listing(root, module.files) + "\n"
        )
    else:
        diff = state.diff
        if len(diff) > DIFF_LIMIT:
            diff = (
                diff[:DIFF_LIMIT]
                + "\n[diff truncated by the host: read the remaining changed files directly]\n"
            )
        text += (
            f"Base commit: {state.base}\n\n"
            + f"Changed paths whose diff you receive:\n\n{_listing(root, state.reviewed)}\n"
            + "Changed paths you receive by name only (outside your read boundary):\n\n"
            + f"{_listing(root, state.named)}\n"
            + f"### Diff\n\n```diff\n{diff}\n```\n\n"
        )
    earlier = [item for review in reviews for item in review.earlier or []]
    return (
        text
        + "### Check results (run by the host)\n\n"
        + check_material(results)
        + "\n"
        + issues.material(earlier)
    )


def _project_path(ctx: RunContext, path: str) -> str | None:
    """The path relative to the worktree, or None when it is not a project path."""
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
    if path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")
    try:
        safe_path(path, "path")
    except (ContractError, TypedDataError, ValueError):
        return None
    return path


def _line_count(path: Path) -> int:
    with path.open("rb") as stream:
        return sum(1 for _ in stream)


def check_evidence(
    ctx: RunContext, state: CodeReview, modules: list[str], findings: list[dict]
) -> tuple[list[dict], dict[str, str | None]]:
    """Every problem with the findings' Modules, bases and locations, as host evidence, and the
    document that defines each basis. Locations are rewritten relative to the worktree."""
    repository = SpecRepository(ctx.worktree)
    documents: set[str] = set()
    for module in modules:
        documents.update(repository.spec_context(module).paths)
    changed = set(state.reviewed) | set(state.named)
    defined: dict[str, str | None] = {}
    problems: list[dict] = []
    for position, finding in enumerate(findings, 1):
        label = f"finding {position} ({finding['module']})"
        if finding["module"] not in modules:
            problems.append(
                evidence(
                    "unresolved-module",
                    finding["module"],
                    f"{label} concerns a Module this reviewer did not review",
                )
            )
        basis = finding["basis"]
        if is_identity(basis):
            document = repository.definer(basis)
        else:
            document = basis.split("#", 1)[0]
        if document is None or document not in documents:
            problems.append(
                evidence(
                    "unresolved-basis",
                    basis,
                    f"{label} cites {basis}, which the reviewed Modules' Spec context does "
                    "not define",
                )
            )
        else:
            defined[basis] = document
        located = []
        for item in finding["locations"]:
            parsed = issues.location(item)
            path = _project_path(ctx, parsed[0]) if parsed else None
            problem = None
            if path is None:
                problem = "is not a path in the project"
            else:
                target = ctx.worktree / path
                first, last = parsed[1], parsed[2]
                if target.is_file():
                    if first is not None and (
                        first < 1 or last < first or last > _line_count(target)
                    ):
                        problem = "gives lines beyond the file's end"
                elif path not in changed or target.exists():
                    problem = "names no file of the worktree and no changed path"
                elif first is not None:
                    problem = "gives lines of a file the worktree no longer has"
            if problem:
                problems.append(
                    evidence(
                        "unresolved-location", item, f"{label}: {item!r} {problem}"
                    )
                )
                located.append(item)
            else:
                suffix = item.strip()[len(parsed[0]) :]
                located.append(path + suffix)
        finding["locations"] = located
    return problems, defined


def _identity(items: list[dict]) -> str | None:
    return next(
        (item["ref"] for item in items if item["kind"] == "context-identity"), None
    )


def _labelled(items: list[dict], label: str) -> list[dict]:
    return [
        {**item, "detail": f"{label}: {item['detail']}" if item["detail"] else label}
        for item in items
    ]


def _read_earlier(
    ctx: RunContext, reviews: list[ModuleReview]
) -> tuple[list, Stop | None]:
    found = []
    for review in reviews:
        try:
            review.earlier = issues.earlier_issues(ctx, review.module)
        except issues.issue_command.Refusal as refusal:
            return found, ctx.fail(
                "failed",
                "issues_unreadable",
                f"The earlier Issues of {review.module} cannot be read.",
                f"the project's Issues could not be read for {review.module}: {refusal}",
                reason="environment",
                explanation="a review builds on the Module's earlier Issues, which it must be "
                "able to read; a failure of the Issue system is never reported as an Issue",
                causes=[refusal.link],
                options=[
                    "repair the Issue records (issue_check), then run the review again"
                ],
            )
        listed = ", ".join(item["issue"] for item in review.earlier)
        found.append(
            evidence(
                "earlier-issues",
                review.module,
                f"{len(review.earlier)} earlier Issue(s) offered"
                + (f": {listed}" if listed else ""),
            )
        )
    return found, None


def _judge(
    ctx: RunContext, state: CodeReview, reviews: list[ModuleReview]
) -> list[dict]:
    """One reviewer of ``reviews``: steps 3 to 7. Returns the host evidence and sets each
    review's state; a stop of the reviewer makes every one of its Modules incomplete."""
    modules = [review.module for review in reviews]
    label = f"{', '.join(modules)} reviewer"

    def stop_all(stop: Stop) -> None:
        # An incomplete Module keeps what was obtained: its earlier Issues, once read, all
        # still stand, since the review settled none of them.
        for review in reviews:
            review.stop = stop
            if review.earlier is not None and review.settled is None:
                review.settled = issues.settle(review.earlier, [], [])

    found, stop = _read_earlier(ctx, reviews)
    if stop is not None:
        stop_all(stop)
        return found
    if state.scope == "module":
        own = set(modules)
        results = [item for item in state.results if item["module"] in own]
    else:
        results = state.results
    launched = len(ctx.worker_runs)
    outcome = run_worker(
        ctx,
        instructions(ctx, state, reviews, results),
        task_type=TASK_TYPE,
        output_schema=REVIEWER_OUTPUT,
        rounds=0,
        modules=modules,
        readable=(ctx.run_dir / "checks",),
    )
    found.extend(_labelled(outcome.evidence, label))
    if len(ctx.worker_runs) > launched:
        identity = _identity(outcome.evidence)
        summary = (ctx.worker or {}).get("summary") or None
        for review in reviews:
            review.context_identity = identity
            review.summary = summary
    if isinstance(outcome, Stop):
        outcome.error["actor"] += f", review of {', '.join(modules)}"
        stop_all(outcome)
        return found
    output = outcome.output or {}
    findings = list(output.get("findings") or [])
    problems, defined = check_evidence(ctx, state, modules, findings)
    for finding in findings:
        finding["issue"] = None
    for review in reviews:
        review.findings = [item for item in findings if item["module"] == review.module]
    # A finding about a Module nobody reviewed stays in the report, with the first Module's.
    reviews[0].findings += [item for item in findings if item["module"] not in modules]
    if problems:
        for finding in findings:
            finding.pop(
                "earlier", None
            )  # nothing is reported, so no Issue is appended to
        found.extend(problems)
        stop_all(
            ctx.fail(
                "failed",
                "unresolved_evidence",
                f"A finding about {', '.join(modules)} cites evidence that does not hold.",
                f"the reviewer of {', '.join(modules)} returned findings whose Module, basis or "
                "locations do not hold, so none of its findings is reported: "
                + "; ".join(item["detail"] for item in problems),
                reason="capability",
                explanation="the host checks every finding's evidence but never corrects a "
                "finding or relaunches the reviewer",
                evidence=problems,
                options=[
                    "run code_review again for these Modules",
                    "check the Spec context of the reviewed Modules",
                ],
            )
        )
        return found
    resolved = list(output.get("resolved") or [])
    offered = {item["issue"] for review in reviews for item in review.earlier or []}
    unoffered = [item for item in resolved if item["issue"] not in offered]
    for index, review in enumerate(reviews):
        mine = {item["issue"] for item in review.earlier or []}
        review.settled = issues.settle(
            review.earlier or [],
            review.findings,
            [item for item in resolved if item["issue"] in mine]
            + (unoffered if index == 0 else []),
        )
        reported, stop = issues.report(
            ctx,
            state.scope,
            review.module,
            review.findings,
            review.context_identity,
            defined,
        )
        found.extend(reported)
        if stop is not None:
            review.stop = stop
    return found


def review(ctx: RunContext):
    """Steps 3 to 7: one reviewer of every bound Module, or one per Module."""
    state = _state(ctx)
    reviews = list(state.reviews.values())
    found: list[dict] = []
    if state.scope == "module":
        for item in reviews:
            found.extend(_judge(ctx, state, [item]))
    else:
        found.extend(_judge(ctx, state, reviews))
    return Continue(evidence=found)


def derive_verdict(ctx: RunContext):
    """Step 8: each Module's outcome and the verdict, counted by the host, never by a worker."""
    state = _state(ctx)
    reviews = list(state.reviews.values())
    modules = [
        {
            "module": item.module,
            "outcome": item.outcome,
            "context_identity": item.context_identity,
            "summary": item.summary,
            "findings": item.findings,
            "earlier_issues": item.settled,
        }
        for item in reviews
    ]
    outcomes = {item["outcome"] for item in modules}
    verdict = next(value for value in reversed(OUTCOMES) if value in outcomes)
    payload = {
        "scope": state.scope,
        "base": state.base,
        "focus": ctx.arguments.focus or None,
        "reviewed_paths": state.reviewed,
        "named_only_paths": state.named,
        "checks": check_results(state.results),
        "verdict": verdict,
        "modules": modules,
    }
    validate(payload, REVIEW_SCHEMA)
    ctx.output = payload
    incomplete = [item for item in reviews if item.stop is not None]
    standing = sum(len(item.standing()) for item in reviews if item.stop is None)
    counts = f"{standing} blocking Issue(s) stand"
    if not incomplete:
        return Stop("ok", f"Code review ({state.scope}): {verdict}; {counts}.")
    status = (
        "failed"
        if any(item.stop.status == "failed" for item in incomplete)
        else "blocked"
    )
    causes, seen = [], set()
    for item in incomplete:
        if id(item.stop) not in seen:
            seen.add(id(item.stop))
            causes.append(item.stop.error)
    names = ", ".join(item.module for item in incomplete)
    reasons = "; ".join(f"{item.module}: {item.stop.summary}" for item in incomplete)
    return ctx.fail(
        status,
        "review_incomplete",
        f"Code review ({state.scope}): incomplete for {names}; {counts}.",
        f"the code review of {len(incomplete)} of {len(reviews)} Module(s) is incomplete, "
        f"each cause below: {reasons}; {counts} in the reviewed Modules",
        reason="decision",
        explanation="code_review reviews each Module once and never repairs or reruns; how to "
        "complete the review is the main agent's decision",
        causes=causes,
        options=["address each cause, then run code_review again for those Modules"],
    )


def review_arguments(parser) -> None:
    parser.add_argument(
        "--scope",
        choices=SCOPES,
        default="change",
        help="review the workspace's change (default) or each named Module's whole code",
    )
    parser.add_argument("--base", default=None)
    parser.add_argument("--focus", default=None)


CODE_REVIEW = operation(
    "code_review",
    TASK_TYPE,
    False,
    (prepare, review, derive_verdict),
    REVIEW_SCHEMA,
    review_arguments,
    binding="optional",
)


__all__ = [
    "CODE_REVIEW",
    "KINDS",
    "REVIEWER_OUTPUT",
    "REVIEW_SCHEMA",
    "check_evidence",
]
