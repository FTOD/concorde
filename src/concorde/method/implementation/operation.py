"""The ``implement`` and ``test`` Operations (see the Implementation Module Spec).

``implement`` runs one ``implement`` worker through the standard worker sequence with the bound
Modules' configured checks, so Workers audits every round, runs the checks outside the worker and
resumes the same session only while a check fails. Once the worker was launched, the host composes
the code change from the run record.

``test`` runs the configured checks on the host first, then a read-only ``test`` worker that
interprets the results; the host's check results are the only evidence of whether they passed.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from ...execution.checks.checks import CheckError
from ..checks import checked_modules, run_module_checks
from ...execution.context import (
    Continue,
    RunContext,
    Stop,
    evidence,
)
from ..workers import grant_failure, operation, run_worker
from ..prompts import (
    load_prompt,
)
from ...spec.grants import grant
from ...spec.repository import SpecRepository
from ...spec.repository_base import SpecError

LOG_TAIL = 8_000

CHECK_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["check", "module", "outcome", "exit_code", "log"],
    "properties": {
        "check": {"type": "string", "minLength": 1},
        "module": {"type": "string", "pattern": "^module\\."},
        "outcome": {"enum": ["passed", "failed", "timed_out"]},
        "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "log": {"type": "string", "minLength": 1},
    },
}

_STRINGS = {"type": "array", "items": {"type": "string", "minLength": 1}}

# contract.implementation.code-change
CODE_CHANGE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "goal",
        "summary",
        "changed_files",
        "created_files",
        "deleted_files",
        "refused_deletions",
        "rounds",
        "checks",
        "addresses",
    ],
    "properties": {
        "goal": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "changed_files": _STRINGS,
        "created_files": _STRINGS,
        "deleted_files": _STRINGS,
        "refused_deletions": _STRINGS,
        "rounds": {"type": "integer", "minimum": 1},
        "checks": {"type": "array", "items": {"$ref": "#/$defs/check"}},
        "addresses": _STRINGS,
    },
    "$defs": {"check": CHECK_SCHEMA},
}

FAILURE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["check", "concerns", "cause", "fault", "locations"],
    "properties": {
        "check": {"type": "string", "minLength": 1},
        "concerns": _STRINGS,
        "cause": {"type": "string", "minLength": 1},
        "fault": {"enum": ["code", "test", "spec", "environment", "unknown"]},
        "locations": _STRINGS,
    },
}

# contract.implementation.test-report
TEST_REPORT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["focus", "passed", "checks", "summary", "failures", "notes"],
    "properties": {
        "focus": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "passed": {"type": "boolean"},
        "checks": {"type": "array", "items": CHECK_SCHEMA},
        "summary": {"type": "string", "minLength": 1},
        "failures": {"type": "array", "items": FAILURE_SCHEMA},
        "notes": _STRINGS,
    },
}

# The Operation-specific part of each worker result (``output``); the worker's ``summary`` is the
# top-level summary of its result.
IMPLEMENT_WORKER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["addresses"],
    "properties": {"addresses": _STRINGS},
}
TEST_WORKER_OUTPUT: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["failures", "notes"],
    "properties": {
        "failures": {"type": "array", "items": FAILURE_SCHEMA},
        "notes": _STRINGS,
    },
}

OUTCOMES = {"passed": "passed", "failed": "failed", "timeout": "timed_out"}


# --- shared host helpers -----------------------------------------------------------------------


def check_results(results: list[dict]) -> list[dict]:
    """Check-service results in the contract's shape, each with the absolute path of its log."""
    shaped = []
    for item in results:
        log_text = Path(item["log"]).as_posix()
        outcome = OUTCOMES[item["status"]]
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


def check_evidence(results: list[dict]) -> list[dict]:
    return [
        evidence(
            "check",
            item["check_id"],
            f"{item['status']}, exit {item['exit_code']}; log {item['log']}",
        )
        for item in results
    ]


def check_material(results: list[dict]) -> str:
    """The check results as task material: one line per check, the log tail of each failure."""
    if not results:
        return "The bound Modules have no configured check.\n"
    lines = []
    for item in results:
        lines.append(
            f"- {item['check_id']} ({item['module']}): {item['status']}, exit code "
            f"{item['exit_code']}, log {item['log']}\n"
        )
    for item in results:
        if item["status"] == "passed":
            continue
        tail = Path(item["log"]).read_bytes()[-LOG_TAIL:].decode("utf-8", "replace")
        lines.append(
            f"\n### Log of {item['check_id']} (last part)\n\n```text\n{tail}\n```\n"
        )
    return "".join(lines)


def preflight(ctx: RunContext, task_type: str) -> Stop | None:
    """Stop ``failed`` when the grant of ``task_type`` cannot be computed for the bound Modules."""
    try:
        grant(SpecRepository(ctx.worktree), ctx.modules, task_type)
    except (SpecError, OSError, ValueError) as error:
        return grant_failure(ctx, task_type, ctx.modules, error)
    return None


def host_checks(ctx: RunContext) -> list[dict] | Stop:
    """Run the bound Modules' configured checks outside any worker, logs in the run directory."""
    try:
        repository = SpecRepository(ctx.worktree)
        return run_module_checks(
            ctx.worktree,
            checked_modules(repository, ctx.modules),
            trace_directory=ctx.run_dir / "checks",
            repository=repository,
            report=ctx.evidence,
        )
    except (CheckError, SpecError, OSError) as error:
        return ctx.checks_unavailable(error)


def _workspace_goal(ctx: RunContext) -> str:
    """The workspace's goal, as context beside the run's own arguments."""
    return (
        "\n## The workspace's goal\n\n"
        "Context for this run, which may serve only part of it:\n\n"
        f"{ctx.goal or '(none)'}\n"
    )


def _admitted(ctx: RunContext) -> str:
    if not ctx.inputs:
        return ""
    return (
        "\n## Task material\n\nOutputs of earlier runs of this task, admitted as material:\n\n"
        f"```json\n{json.dumps(ctx.inputs, indent=2, ensure_ascii=False)}\n```\n"
    )


# --- implement ---------------------------------------------------------------------------------


def _exists(worktree: Path, path: str) -> bool:
    """Whether ``path`` is in the worktree, a symbolic link counting whatever it points to."""
    return os.path.lexists(worktree / path)


def _present(worktree: Path) -> set[str]:
    """Every tracked or untracked, not ignored, path the worktree holds (read-only Git): a
    tracked path already deleted in the worktree is not present."""
    output = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=worktree,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout
    return {
        item
        for item in output.decode("utf-8", "surrogateescape").split("\0")
        if item and _exists(worktree, item)
    }


def _latest_checks(record: dict) -> list[dict]:
    """The check results of the last round that ran checks; a later round whose validation
    ran none, such as one that could not validate, hides nothing."""
    for item in reversed(record.get("rounds") or []):
        checks = [check for check in item.get("evidence") or [] if "check_id" in check]
        if checks:
            return checks
    return []


def code_change(ctx: RunContext, record: dict, before: set[str], summary: str) -> dict:
    """The code change of the run: its files as the net change from ``before``, the paths the
    worktree held before the run, to the worktree now, over every path the last audit saw
    changed, which spans every round, and every deletion Workers performed after it."""
    rounds = record.get("rounds") or []
    audit = (rounds[-1].get("audit") if rounds else None) or {}
    touched = sorted({*audit.get("changed", []), *(record.get("deleted") or [])})
    present = {path for path in touched if _exists(ctx.worktree, path)}
    worker = record.get("worker_result") or {}
    output = worker.get("output") if isinstance(worker.get("output"), dict) else {}
    return {
        "goal": ctx.arguments.goal,
        "summary": worker.get("summary") or summary,
        "changed_files": [
            path for path in touched if path in before and path in present
        ],
        "created_files": [
            path for path in touched if path not in before and path in present
        ],
        "deleted_files": [
            path for path in touched if path in before and path not in present
        ],
        "refused_deletions": list(record.get("deletions_refused") or []),
        "rounds": max(len(rounds), 1),
        "checks": check_results(_latest_checks(record)),
        "addresses": list(output.get("addresses") or []),
    }


def implement_step(ctx: RunContext):
    if ctx.arguments.rounds is not None and ctx.arguments.rounds < 0:
        return ctx.fail(
            "failed",
            "invalid_argument",
            "--rounds must not be negative.",
            f"--rounds is {ctx.arguments.rounds}; it must be zero or more",
            reason="input",
            explanation="the number of resume rounds comes from the caller",
            evidence=[
                evidence("invalid-argument", "--rounds", str(ctx.arguments.rounds))
            ],
            options=["run implement again with --rounds 0 or more"],
        )
    before = _present(ctx.worktree)
    instructions = (
        load_prompt("implement")
        + f"\n## Goal\n\n{ctx.arguments.goal}\n"
        + _workspace_goal(ctx)
        + _admitted(ctx)
    )
    launched = len(ctx.worker_runs)
    outcome = run_worker(
        ctx,
        instructions,
        task_type="implement",
        output_schema=IMPLEMENT_WORKER_OUTPUT,
        checks=True,
        rounds=ctx.arguments.rounds,
    )
    if len(ctx.worker_runs) == launched:
        return outcome  # no worker run: nothing was changed
    record = ctx.last_record
    extra: list[dict] = []
    for path in record.get("deleted") or []:
        extra.append(evidence("deleted", path, "proposed by the worker, inside rw"))
    for path in record.get("deletions_refused") or []:
        extra.append(evidence("deletion-refused", path, "outside the writable paths"))
    if record.get("worker_result") is not None:
        summary = outcome.summary if isinstance(outcome, Stop) else "implemented"
        ctx.output = code_change(ctx, record, before, summary)
    if isinstance(outcome, Continue):
        if not _latest_checks(record):
            extra.append(
                evidence(
                    "checks",
                    ", ".join(ctx.modules),
                    "no configured check: the result carries no check evidence",
                )
            )
        return Continue(output=ctx.output, evidence=outcome.evidence + extra)
    outcome.evidence.extend(extra)
    return outcome


def implement_arguments(parser) -> None:
    parser.add_argument("--goal", required=True)
    parser.add_argument("--rounds", type=int, default=None)


IMPLEMENT = operation(
    "implement",
    "implement",
    True,
    (implement_step,),
    CODE_CHANGE_SCHEMA,
    implement_arguments,
)


# --- test --------------------------------------------------------------------------------------

# The resume rounds a test worker gets to make its failures interpret exactly the failed checks.
FAILURE_ROUNDS = 1


def failure_problems(results: list[dict], failures: list[dict]) -> list[str]:
    """Every way ``failures`` is not exactly one entry per check of ``results`` that did not
    pass."""
    failed = Counter(item["check_id"] for item in results if item["status"] != "passed")
    ran = {item["check_id"] for item in results}
    given = Counter(item["check"] for item in failures)
    problems = [
        f"check {check} did not pass and has {given[check]} failures entries instead of "
        + ("one" if count == 1 else str(count))
        for check, count in sorted(failed.items())
        if given[check] != count
    ]
    problems += [
        f"a failures entry names {check}, "
        + ("which passed" if check in ran else "which the host did not run")
        for check in sorted(set(given) - set(failed))
    ]
    return problems


def failure_repair(problems: list[str]) -> str | None:
    """The repair text that resumes a test worker with every way its failures do not match the
    host's check results, or None when they match."""
    if not problems:
        return None
    return (
        "The host compared your `failures` with its check results. It needs exactly one entry "
        "per check that did not pass, named by that check's identity, and none for a check "
        "that passed; these do not hold:\n\n"
        + "".join(f"- {problem}\n" for problem in problems)
        + "\nCorrect them from the check results and logs you were given. Then end again with "
        "your complete structured result, since it replaces your previous result.\n"
    )


def testing_step(ctx: RunContext):
    stopped = preflight(ctx, "test")
    if stopped is not None:
        return stopped
    results = host_checks(ctx)
    if isinstance(results, Stop):
        return results
    found = check_evidence(results)
    focus = ctx.arguments.focus
    instructions = (
        load_prompt("test")
        + (f"\n## Focus\n\n{focus}\n" if focus else "")
        + _workspace_goal(ctx)
        + "\n## Check results (run by the host)\n\n"
        + check_material(results)
    )

    def accounted(result: dict) -> str | None:
        # The worker is resumed once with every way its failures miss the failed checks.
        output = result.get("output") or {}
        return failure_repair(failure_problems(results, output.get("failures") or []))

    # The worker interprets the checks, so it reads their full logs, passed ones included.
    outcome = run_worker(
        ctx,
        instructions,
        task_type="test",
        output_schema=TEST_WORKER_OUTPUT,
        readable=(ctx.run_dir / "checks",),
        rounds=FAILURE_ROUNDS,
        validate=accounted,
    )
    outcome.evidence[:0] = found
    if isinstance(outcome, Stop):
        return outcome
    output = outcome.output or {}
    problems = failure_problems(results, output.get("failures") or [])
    if problems:
        return ctx.fail(
            "failed",
            "failures_unaccounted",
            "The test worker's failures do not interpret exactly the checks that did not pass.",
            "the test worker's failures must hold exactly one entry per check that did not "
            f"pass, and still did not after {FAILURE_ROUNDS} resume round(s), so its report "
            "is discarded: " + "; ".join(problems),
            reason="capability",
            explanation="the host checks the worker's interpretation against its own check "
            "results but never corrects it, and resumes the worker only "
            f"{FAILURE_ROUNDS} time(s)",
            evidence=[
                evidence("failures-unaccounted", "", problem) for problem in problems
            ],
            host_evidence=outcome.evidence,
            options=[
                "run test again",
                "read the check results and logs in the host evidence",
            ],
        )
    return Continue(
        output={
            "focus": focus or None,
            "passed": all(item["status"] == "passed" for item in results),
            "checks": check_results(results),
            "summary": (ctx.worker or {}).get("summary") or "tested",
            "failures": list(output.get("failures") or []),
            "notes": list(output.get("notes") or []),
        },
        evidence=outcome.evidence,
    )


def testing_arguments(parser) -> None:
    parser.add_argument("--focus", default=None)


TEST = operation(
    "test", "test", False, (testing_step,), TEST_REPORT_SCHEMA, testing_arguments
)


__all__ = [
    "CODE_CHANGE_SCHEMA",
    "IMPLEMENT",
    "IMPLEMENT_WORKER_OUTPUT",
    "TEST",
    "TEST_REPORT_SCHEMA",
    "TEST_WORKER_OUTPUT",
    "check_results",
]
