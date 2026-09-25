"""The ``code_review`` Operation (see the Code review Module Spec).

The host computes the ``review-code`` grant, the diff from the base commit to the task worktree
(uncommitted and untracked files included) with contents only for paths the grant makes readable,
and the bound Modules' configured check results; a read-only reviewer reports every finding in one
pass; the host checks that every cited basis resolves in the bound Modules' Spec context and
derives the verdict. The reviewer is never resumed.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ..harness.checks import run_checks
from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    component,
    evidence,
    load_prompt,
)
from ..spec.grants import Grant, grant
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError, is_identity

LOG_TAIL = 8_000
DIFF_LIMIT = 300_000

CHECK_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["check", "module", "outcome", "exit_code", "log"],
    "properties": {
        "check": {"type": "string", "minLength": 1},
        "module": {"type": "string", "pattern": "^module\\."},
        "outcome": {"enum": ["passed", "failed", "timed_out", "not_started"]},
        "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "log": {"type": "string", "minLength": 1},
    },
}

_STRINGS = {"type": "array", "items": {"type": "string", "minLength": 1}}

FINDING_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "severity",
        "kind",
        "module",
        "basis",
        "locations",
        "description",
        "suggestion",
    ],
    "properties": {
        "id": {"type": "string", "pattern": "^F[0-9]+$"},
        "severity": {"enum": ["blocking", "advisory"]},
        "kind": {
            "enum": ["violation", "defect", "missing-test", "out-of-scope", "spec-gap"]
        },
        "module": {"type": "string", "pattern": "^module\\."},
        "basis": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "locations": _STRINGS,
        "description": {"type": "string", "minLength": 1},
        "suggestion": {"type": "string", "minLength": 1},
    },
}

# contract.code-review.review
REVIEW_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "base",
        "focus",
        "reviewed_paths",
        "named_only_paths",
        "checks",
        "summary",
        "findings",
        "verdict",
    ],
    "properties": {
        "base": {"type": "string", "minLength": 1},
        "focus": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "reviewed_paths": _STRINGS,
        "named_only_paths": _STRINGS,
        "checks": {"type": "array", "items": CHECK_SCHEMA},
        "summary": {"type": "string", "minLength": 1},
        "findings": {"type": "array", "items": FINDING_SCHEMA},
        "verdict": {"enum": ["clean", "changes_required"]},
    },
}

# The reviewer's part of its worker result (``output``); its ``summary`` is the top-level one.
REVIEWER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": FINDING_SCHEMA}},
}

OUTCOMES = {"passed": "passed", "failed": "failed", "timeout": "timed_out"}


def _git(worktree: Path, *arguments: str, check: bool = True):
    return subprocess.run(
        ["git", *arguments],
        cwd=worktree,
        check=check,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


# --- inputs ------------------------------------------------------------------------------------


def review_grant(ctx: RunContext) -> Grant | Stop:
    try:
        return grant(SpecRepository(ctx.worktree), ctx.modules, "review-code")
    except (SpecError, OSError, ValueError) as error:
        return ctx.grant_failure("review-code", ctx.modules, error)


def resolve_base(ctx: RunContext) -> str | Stop:
    reference = ctx.arguments.base or ctx.task.get("base_commit")
    if not reference:
        return ctx.fail(
            "failed",
            "no_base",
            "No base commit is known and no --base was given.",
            (
                f"the run without a task in {ctx.worktree} was given no --base"
                if ctx.project_scope
                else f"task {ctx.task.get('id')} records no base commit and --base was not given"
            )
            + ", so there is no diff to review",
            reason="input",
            explanation="the diff base comes from the task record or the caller",
            evidence=[evidence("base", "", "no base")],
            options=["pass --base with the commit the reviewed changes start from"],
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
            explanation="the diff base comes from the task record or the caller",
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


def host_checks(ctx: RunContext) -> list[dict] | Stop:
    try:
        return run_checks(
            ctx.worktree, modules=ctx.modules, log_directory=ctx.run_dir / "checks"
        )
    except (SpecError, OSError) as error:
        return ctx.checks_unavailable(error)


def check_results(primary: Path, results: list[dict]) -> list[dict]:
    shaped = []
    for item in results:
        log = Path(item["log"])
        try:
            log_text = log.relative_to(primary).as_posix()
        except ValueError:
            log_text = log.as_posix()
        outcome = OUTCOMES.get(item["status"], "failed")
        shaped.append(
            {
                "check": item["check_id"],
                "module": item["module"],
                "outcome": outcome,
                "exit_code": None if outcome == "timed_out" else item["exit_code"],
                "log": log_text,
            }
        )
    return shaped


def check_material(results: list[dict]) -> str:
    if not results:
        return "The bound Modules have no configured check.\n"
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


def instructions(
    ctx: RunContext,
    base: str,
    reviewed: list[str],
    named: list[str],
    diff: str,
    results: list[dict],
) -> str:
    focus = ctx.arguments.focus
    root = ctx.worktree.as_posix()
    if len(diff) > DIFF_LIMIT:
        diff = (
            diff[:DIFF_LIMIT]
            + "\n[diff truncated by the host: read the remaining changed files directly]\n"
        )
    listed = "".join(f"- {root}/{path}\n" for path in reviewed) or "- (none)\n"
    names = "".join(f"- {root}/{path}\n" for path in named) or "- (none)\n"
    return (
        load_prompt("review-code")
        + f"\n## Review input\n\nBound Modules: {', '.join(ctx.modules)}\n\n"
        + f"Base commit: {base}\n\n"
        + (
            f"Focus (look at this first; it does not narrow what you report):\n\n{focus}\n\n"
            if focus
            else ""
        )
        + f"Changed paths whose diff you receive:\n\n{listed}\n"
        + f"Changed paths you receive by name only (outside your read boundary):\n\n{names}\n"
        + f"### Diff\n\n```diff\n{diff}\n```\n\n"
        + "### Check results (run by the host)\n\n"
        + check_material(results)
    )


# --- verdict -----------------------------------------------------------------------------------


def unresolved_bases(
    worktree: Path, modules: list[str], findings: list[dict]
) -> list[tuple[str, str]]:
    """(finding id, basis) for every basis that does not resolve in the bound Modules' context.

    A basis is a stable identity whose defining document lies in the Spec context of a bound
    Module, or a document path of that context, optionally followed by ``#anchor``. A blocking
    finding without a basis is unresolved too.
    """
    repository = SpecRepository(worktree)
    documents: set[str] = set()
    for module in modules:
        documents.update(repository.spec_context(module).paths)
    problems = []
    for finding in findings:
        basis = finding.get("basis")
        if basis is None:
            if finding["severity"] == "blocking":
                problems.append((finding["id"], "(none)"))
            continue
        if is_identity(basis):
            document = repository.definer(basis)
            ok = document is not None and document in documents
        else:
            ok = basis.split("#", 1)[0] in documents
        if not ok:
            problems.append((finding["id"], basis))
    return problems


def review_step(ctx: RunContext):
    access = review_grant(ctx)
    if isinstance(access, Stop):
        return access
    base = resolve_base(ctx)
    if isinstance(base, Stop):
        return base
    changed = changed_paths(ctx.worktree, base)
    reviewed = [path for path in changed if readable(access, path)]
    named = [path for path in changed if not readable(access, path)]
    diff = diff_text(ctx.worktree, base, reviewed)
    found = [
        evidence("base", base, "diff base"),
        evidence(
            "diff",
            base,
            f"{len(reviewed)} path(s) with contents, {len(named)} by name only",
        ),
    ]
    results = host_checks(ctx)
    if isinstance(results, Stop):
        results.evidence[:0] = found
        return results
    found += [
        evidence(
            "check",
            item["check_id"],
            f"{item['status']}, exit {item['exit_code']}; log {item['log']}",
        )
        for item in results
    ]
    outcome = ctx.run_worker(
        instructions(ctx, base, reviewed, named, diff, results),
        task_type="review-code",
        output_schema=REVIEWER_OUTPUT,
        readable=(ctx.run_dir / "checks",),
    )
    outcome.evidence[:0] = found
    if isinstance(outcome, Stop):
        return outcome
    findings = list((outcome.output or {}).get("findings") or [])
    problems = unresolved_bases(ctx.worktree, ctx.modules, findings)
    if problems:
        return ctx.fail(
            "failed",
            "unresolved_basis",
            "A finding cites a basis the bound Modules' Spec context does not define.",
            "the reviewer's findings cite bases that the Spec context of "
            f"{', '.join(ctx.modules)} does not define, so the review is discarded: "
            + ", ".join(f"{finding} cites {basis}" for finding, basis in problems),
            reason="capability",
            explanation="the host checks every basis but never corrects a finding or "
            "relaunches the reviewer",
            evidence=[
                evidence("unresolved-basis", basis, finding)
                for finding, basis in problems
            ],
            host_evidence=outcome.evidence,
            options=[
                "run code_review again",
                "check the Spec context of the bound Modules",
            ],
        )
    blocking = any(item["severity"] == "blocking" for item in findings)
    return Continue(
        output={
            "base": base,
            "focus": ctx.arguments.focus or None,
            "reviewed_paths": reviewed,
            "named_only_paths": named,
            "checks": check_results(ctx.primary, results),
            "summary": (ctx.worker or {}).get("summary") or "reviewed",
            "findings": findings,
            "verdict": "changes_required" if blocking else "clean",
        },
        evidence=outcome.evidence,
    )


def review_arguments(parser) -> None:
    parser.add_argument("--base", default=None)
    parser.add_argument("--focus", default=None)


CODE_REVIEW = Provider(
    "code_review",
    "review-code",
    False,
    (review_step,),
    REVIEW_SCHEMA,
    review_arguments,
    task_scope="optional",
)


__all__ = ["CODE_REVIEW", "REVIEWER_OUTPUT", "REVIEW_SCHEMA", "unresolved_bases"]
