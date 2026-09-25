"""The ``implement`` and ``test`` Operations (see the Implementation Module Spec).

``implement`` runs one ``implement`` worker through the standard worker sequence with the bound
Modules' configured checks, so Workers audits every round, runs the checks outside the worker and
resumes the same session only while a check fails. Once the worker was launched, the host removes
pre-created files that stayed empty, clears the pending marker of every pending entry of the bound
Modules that now exists, and composes the code change from the run record.

``test`` runs the configured checks on the host first, then a read-only ``test`` worker that
interprets the results; the host's check results are the only evidence of whether they passed.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from ..harness.checks import run_checks
from ..harness.runs import read_record
from ..operations.provider import (
    Continue,
    Provider,
    RunContext,
    Stop,
    evidence,
    load_prompt,
)
from ..spec.grants import grant
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError

LOG_TAIL = 8_000

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
        "pending_cleared",
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
        "pending_cleared": _STRINGS,
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


def check_results(primary: Path, results: list[dict]) -> list[dict]:
    """Check-service results in the contract's shape; logs relative to the primary when inside."""
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
        return ctx.grant_failure(task_type, ctx.modules, error)
    return None


def host_checks(ctx: RunContext) -> list[dict] | Stop:
    """Run the bound Modules' configured checks outside any worker, logs in the run directory."""
    try:
        return run_checks(
            ctx.worktree, modules=ctx.modules, log_directory=ctx.run_dir / "checks"
        )
    except (SpecError, OSError) as error:
        return ctx.checks_unavailable(error)


def _admitted(ctx: RunContext) -> str:
    if not ctx.inputs:
        return ""
    return (
        "\n## Task material\n\nOutputs of earlier runs of this task, admitted as material:\n\n"
        f"```json\n{json.dumps(ctx.inputs, indent=2, ensure_ascii=False)}\n```\n"
    )


# --- implement ---------------------------------------------------------------------------------


def _present(worktree: Path) -> set[str]:
    """Every tracked or untracked, not ignored, path of the worktree (read-only Git)."""
    output = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=worktree,
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout
    return {
        item for item in output.decode("utf-8", "surrogateescape").split("\0") if item
    }


def remove_unused(worktree: Path, record: dict) -> list[str]:
    """Remove pre-created files and directories that are still empty; return their entries."""
    removed = list(record.get("pending_removed") or [])
    for path in record.get("pending_created") or []:
        if path in removed:
            continue
        target = worktree / path.rstrip("/")
        if path.endswith("/"):
            if (
                target.is_dir()
                and not target.is_symlink()
                and not any(target.iterdir())
            ):
                target.rmdir()
                removed.append(path)
        elif (
            target.is_file() and not target.is_symlink() and target.stat().st_size == 0
        ):
            target.unlink()
            removed.append(path)
    return removed


def clear_pending(worktree: Path, modules: list[str]) -> list[str]:
    """Remove the pending marker of every pending entry of ``modules`` that now exists."""
    from ..spec.changes import apply_files
    from ..spec.content_changes import pending_changes

    repository = SpecRepository(worktree)
    changes, confirmed, _missing = pending_changes(repository)
    owners = {unit.metadata.path: unit.owner for unit in repository.units.values()}
    selected = [item for item in changes if owners.get(item["path"]) in modules]
    if selected:
        apply_files(worktree, selected, {item["path"] for item in selected})
    return sorted(item["path"] for item in confirmed if item["module"] in modules)


def _latest_checks(record: dict) -> list[dict]:
    for item in reversed(record.get("rounds") or []):
        if item.get("checks") is not None:
            return item["checks"]
    return []


def code_change(
    ctx: RunContext, record: dict, before: set[str], cleared: list[str], summary: str
) -> dict:
    rounds = record.get("rounds") or []
    audit = (rounds[-1].get("audit") if rounds else None) or {}
    changed = [
        path for path in audit.get("changed", []) if (ctx.worktree / path).exists()
    ]
    worker = record.get("worker_result") or {}
    output = worker.get("output") if isinstance(worker.get("output"), dict) else {}
    return {
        "goal": ctx.arguments.goal,
        "summary": worker.get("summary") or summary,
        "changed_files": [path for path in changed if path in before],
        "created_files": [path for path in changed if path not in before],
        "deleted_files": list(record.get("deleted") or []),
        "refused_deletions": list(record.get("deletions_refused") or []),
        "pending_cleared": cleared,
        "rounds": max(len(rounds), 1),
        "checks": check_results(ctx.primary, _latest_checks(record)),
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
        + _admitted(ctx)
    )
    launched = len(ctx.worker_runs)
    outcome = ctx.run_worker(
        instructions,
        task_type="implement",
        output_schema=IMPLEMENT_WORKER_OUTPUT,
        checks=True,
        rounds=ctx.arguments.rounds,
    )
    if len(ctx.worker_runs) == launched:
        return outcome  # no worker run: nothing was pre-created or changed
    record = read_record(ctx.primary, ctx.worker_runs[-1])
    extra: list[dict] = []
    removed = remove_unused(ctx.worktree, record)
    if removed:
        extra.append(evidence("pending-removed", ", ".join(removed), "empty, removed"))
    cleared: list[str] = []
    try:
        cleared = clear_pending(ctx.worktree, ctx.modules)
    except (SpecError, OSError) as error:
        extra.append(
            evidence("pending-markers", getattr(error, "code", "error"), str(error))
        )
    if cleared:
        extra.append(evidence("pending-cleared", ", ".join(cleared), "marker removed"))
    for path in record.get("deleted") or []:
        extra.append(evidence("deleted", path, "proposed by the worker, inside rw"))
    for path in record.get("deletions_refused") or []:
        extra.append(evidence("deletion-refused", path, "outside the writable paths"))
    if record.get("worker_result") is not None:
        summary = outcome.summary if isinstance(outcome, Stop) else "implemented"
        ctx.output = code_change(ctx, record, before, cleared, summary)
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


IMPLEMENT = Provider(
    "implement",
    "implement",
    True,
    (implement_step,),
    CODE_CHANGE_SCHEMA,
    implement_arguments,
)


# --- test --------------------------------------------------------------------------------------


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
        + "\n## Check results (run by the host)\n\n"
        + check_material(results)
    )
    # The worker interprets the checks, so it reads their full logs, passed ones included.
    outcome = ctx.run_worker(
        instructions,
        task_type="test",
        output_schema=TEST_WORKER_OUTPUT,
        readable=(ctx.run_dir / "checks",),
    )
    outcome.evidence[:0] = found
    if isinstance(outcome, Stop):
        return outcome
    output = outcome.output or {}
    return Continue(
        output={
            "focus": focus or None,
            "passed": all(item["status"] == "passed" for item in results),
            "checks": check_results(ctx.primary, results),
            "summary": (ctx.worker or {}).get("summary") or "tested",
            "failures": list(output.get("failures") or []),
            "notes": list(output.get("notes") or []),
        },
        evidence=outcome.evidence,
    )


def testing_arguments(parser) -> None:
    parser.add_argument("--focus", default=None)


TEST = Provider(
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
