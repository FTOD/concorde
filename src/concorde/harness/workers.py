"""Run one worker: prepare its run directory, launch and resume ``claude -p``, audit and check.

``run_worker`` performs the standard sequence of the Workers Module: freeze the grant, pre-create
the pending files it makes writable, generate the settings, write hook, tool list and brief, launch
the worker in its own process group, audit the task worktree after every round, run the configured
checks outside the worker, resume the same session when a check fails, perform the deletions it
proposed, and write the run record. The returned record keeps the worker's answer verbatim and
apart from what the host observed itself.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import WORKER_ERROR_SCHEMA, evidence, link
from ..spec.repository_base import SpecError
from ..spec.schema import ContractError, validate
from .audit import audit, rw_allows, snapshot
from .runs import create_run, now, remove_short_tmp, write_record
from .settings import (
    TOOL_SETS,
    GrantView,
    SettingsError,
    worker_settings,
    write_hook_source,
)

TAIL = 20_000

WORKER_RESULT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "error", "proposed_deletions", "output"],
    "properties": {
        "status": {"enum": ["ok", "blocked", "failed"]},
        "summary": {"type": "string", "minLength": 1},
        "error": {"anyOf": [{"type": "null"}, WORKER_ERROR_SCHEMA]},
        "proposed_deletions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "output": {"type": "object"},
    },
}


def result_schema(output_schema: dict | None) -> dict:
    """The worker result schema with the Operation's own output schema at ``output``."""
    schema = copy.deepcopy(WORKER_RESULT_SCHEMA)
    if output_schema is not None:
        schema["properties"]["output"] = copy.deepcopy(output_schema)
    return schema


@dataclass
class WorkerRequest:
    worktree: Path
    task_type: str
    grant: dict
    instructions: str
    check_modules: list[str] | None = None
    runtime: tuple[Path, ...] = ()
    output_schema: dict | None = None
    rounds: int = 3
    timeout: float = 1800.0
    max_turns: int = 200
    max_budget_usd: float | None = None
    model: str | None = None
    home: Path | None = None
    claude: str | None = None
    credentials: Path | None = None
    extra: dict = field(default_factory=dict)


def claude_command(request: WorkerRequest) -> str:
    return request.claude or os.environ.get("CONCORDE_CLAUDE") or "claude"


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def brief(request: WorkerRequest, worktree: Path) -> str:
    """The worker's only instruction: the task, then its boundary as absolute paths."""
    view = GrantView(request.grant["entries"])

    def listing(level: str) -> str:
        paths = view.paths(level)
        if not paths:
            return "- (none)\n"
        return "".join(
            f"- {(worktree / path).as_posix()}{'/' if path.endswith('/') else ''}\n"
            for path in paths
        )

    return (
        f"# Concorde worker task ({request.task_type})\n\n"
        f"You are a Concorde worker. The task worktree is {worktree.as_posix()}; always use "
        "absolute paths. Your working directory is a private scratch directory outside it.\n\n"
        "## Task\n\n"
        f"{request.instructions.strip()}\n\n"
        "## Your boundary\n\n"
        "You may change only these paths (a path ending with / covers the files below it):\n\n"
        f"{listing('rw')}\n"
        "You may read these paths but not change them:\n\n"
        f"{listing('ro')}\n"
        "You may know that these files exist, but you may not read or change them:\n\n"
        f"{listing('names')}\n"
        "Every other path is hidden from you. A refused read or write means the path is outside "
        "your boundary: do not work around it. If you need it, stop and return `blocked`, naming "
        "the path and why you need it.\n\n"
        "## Rules\n\n"
        "- Never use Git and never try to read `.git`.\n"
        "- You cannot delete files. List files that should be deleted in `proposed_deletions`.\n"
        "- A file you create with Bash outside the writable paths is lost when you finish; "
        "create files with the Write tool instead.\n"
        "- When the Spec does not state a promise you need, do not infer it from code: return "
        "`blocked` and describe the missing promise.\n"
        "- End with the structured result. For `ok`, `error` is null. For `blocked` or `failed`, "
        "`error` is required and must let the host reason about it without asking you: a code, "
        "the complete detail (what failed, where, with the exact message or output), your "
        "evidence, everything you tried, why you could not handle it yourself (`unhandled`: "
        "`permission`, `decision`, `scope`, `capability`, `exhausted`, `environment` or `input`, "
        "with a specific explanation), the options you see and your recommendation.\n"
    )


def _precreate(worktree: Path, grant: dict) -> list[str]:
    """Create every ``rw`` path that does not exist yet: files empty, directories empty."""
    created = []
    for path in GrantView(grant["entries"]).paths("rw"):
        target = worktree / path.rstrip("/")
        if target.exists() or target.is_symlink():
            continue
        if path.endswith("/"):
            target.mkdir(parents=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        created.append(path)
    return created


def _credentials(request: WorkerRequest) -> Path | None:
    if request.credentials is not None:
        return request.credentials
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    candidate = (Path(base) if base else Path.home() / ".claude") / ".credentials.json"
    return candidate if candidate.is_file() else None


def _environment(request: WorkerRequest, paths) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "HOME": paths.home.as_posix(),
        "TMPDIR": paths.tmp.as_posix(),
        "CLAUDE_CONFIG_DIR": paths.config.as_posix(),
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }
    if os.environ.get("ANTHROPIC_API_KEY"):
        environment["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    return environment


def _command(request, paths, schema_text: str, session: str | None) -> list[str]:
    command = [
        claude_command(request),
        "-p",
        "--settings",
        (paths.control / "settings.json").as_posix(),
        "--tools",
        TOOL_SETS[request.task_type],
        "--json-schema",
        schema_text,
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
        "--allow-dangerously-skip-permissions",
        "--strict-mcp-config",
        "--max-turns",
        str(request.max_turns),
    ]
    if request.max_budget_usd is not None:
        command += ["--max-budget-usd", str(request.max_budget_usd)]
    if request.model:
        command += ["--model", request.model]
    if session:
        command += ["--resume", session]
    return command


def _launch(request, paths, command, prompt: str) -> dict:
    """One round: run the command in its own process group, always killing the group after."""
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=paths.work,
            env=_environment(request, paths),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        return {
            "error": "launch_failed",
            "detail": str(error),
            "stdout": b"",
            "stderr": b"",
        }
    timed_out = False
    try:
        stdout, stderr = process.communicate(prompt.encode(), timeout=request.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(process)
        stdout, stderr = process.communicate()
    finally:
        _kill_group(process)
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit": process.returncode,
        "timed_out": timed_out,
        "duration": round(time.monotonic() - started, 3),
    }


def _kill_group(process) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _envelope(stdout: bytes) -> dict | None:
    text = stdout.decode("utf-8", "replace").strip()
    for line in reversed(text.splitlines() or [""]):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and value.get("type") == "result":
            return value
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _transcript(paths, session: str | None) -> str | None:
    if not session:
        return None
    found = sorted((paths.config / "projects").glob(f"*/{session}.jsonl"))
    return found[0].as_posix() if found else None


def _resume_prompt(failures: list[dict]) -> str:
    parts = [
        "The host ran the configured checks after your last round and some failed. Fix the "
        "code within your boundary and end with a new structured result.\n"
    ]
    for item in failures:
        log = Path(item["log"]).read_bytes()[-TAIL:].decode("utf-8", "replace")
        parts.append(
            f"\n## {item['check_id']} ({item['status']}, exit code {item['exit_code']})\n\n"
            f"```text\n{log}\n```\n"
        )
    return "".join(parts)


def _tail(data: bytes, size: int = 4000) -> str:
    return data[-size:].decode("utf-8", "replace").strip()


def claude_failure(outcome: dict, envelope: dict | None) -> dict | None:
    """A component link when the Claude Code process itself reported an error, else ``None``."""
    actor = "Claude Code process (claude -p)"
    if envelope is None:
        return link(
            "component",
            actor,
            "no_result_envelope",
            f"the process exited with code {outcome.get('exit')} and printed no JSON result "
            f"envelope; standard output ends with: {_tail(outcome['stdout']) or '(empty)'}; "
            f"standard error ends with: {_tail(outcome['stderr']) or '(empty)'}",
            reason="environment",
            explanation="the process ended without a result; it cannot report more",
        )
    subtype = str(envelope.get("subtype") or "success")
    if subtype == "success" and not envelope.get("is_error"):
        return None
    text = envelope.get("result")
    detail = (
        f"the result envelope has subtype {subtype}, is_error {bool(envelope.get('is_error'))}, "
        f"{envelope.get('num_turns', '?')} turn(s), cost {envelope.get('total_cost_usd', '?')} "
        f"USD, exit code {outcome.get('exit')}"
    )
    if isinstance(text, str) and text.strip():
        detail += f"; its final text: {text.strip()[-2000:]}"
    if envelope.get("errors"):
        detail += f"; errors: {json.dumps(envelope['errors'])[-2000:]}"
    stderr = _tail(outcome["stderr"], 2000)
    if stderr:
        detail += f"; standard error ends with: {stderr}"
    exhausted = subtype in ("error_max_turns", "error_max_budget_usd")
    return link(
        "component",
        actor,
        "claude_" + "".join(c if c.isalnum() else "_" for c in subtype.lower()),
        detail,
        reason="exhausted" if exhausted else "environment",
        explanation=(
            "the session reached the turn or budget limit it was started with"
            if exhausted
            else "Claude Code reported an error of the model service or its own execution"
        ),
    )


def worker_link(record: dict, result: dict) -> dict | None:
    """The worker's own error as a link; its content is the worker's claim."""
    error = result.get("error")
    if not isinstance(error, dict):
        return None
    sessions = [item.get("session") for item in record["rounds"] if item.get("session")]
    return link(
        "worker",
        f"{record['task_type']} worker of {record['run_id']}"
        + (f" (session {sessions[-1]})" if sessions else ""),
        error["code"],
        error["detail"],
        reason=error["unhandled"]["reason"],
        explanation=error["unhandled"]["explanation"],
        evidence=error["evidence"],
        attempts=error["attempts"],
        options=error["options"],
        recommendation=error["recommendation"],
    )


def _consistency(result: dict) -> str | None:
    if result["status"] == "ok" and result.get("error") is not None:
        return (
            "the result has status ok but carries an error; an ok result has error null"
        )
    if result["status"] != "ok" and result.get("error") is None:
        return (
            f"the result has status {result['status']} but no error; a blocked or failed "
            "result must carry its error"
        )
    return None


def run_worker(request: WorkerRequest) -> dict:
    """Run one worker to its end and return its run record (also written to the run directory)."""
    from .checks import check_error

    worktree = Path(os.path.realpath(request.worktree))
    run_id, paths = create_run(worktree)
    actor = f"Workers run {run_id} ({request.task_type} worker)"
    record: dict = {
        "run_id": run_id,
        "task_type": request.task_type,
        "worktree": worktree.as_posix(),
        "context_identity": request.grant.get("context_identity"),
        "grant_digest": None,
        "settings_digest": None,
        "brief_digest": None,
        "tools": TOOL_SETS.get(request.task_type),
        "started_at": now(),
        "ended_at": None,
        "rounds": [],
        "transcript": None,
        "stderr_tail": "",
        "worker_result": None,
        "pending_created": [],
        "pending_removed": [],
        "deleted": [],
        "deletions_refused": [],
        "status": "failed",
        "error": None,
        "run_directory": paths.root.as_posix(),
        "tmp": paths.tmp.as_posix(),
    }

    def finish(status: str, error: dict | None = None) -> dict:
        remove_short_tmp(paths)
        _remove_unused_pending(worktree, record)
        record["status"] = status
        record["error"] = error
        record["ended_at"] = now()
        write_record(paths, record)
        return record

    def fail(code: str, detail: str, reason: str, explanation: str, **extra) -> dict:
        found = list(extra.pop("evidence", ()))
        if record["transcript"]:
            found.append(evidence("transcript", record["transcript"], ""))
        found.append(
            evidence("run-record", (paths.root / "record.json").as_posix(), "")
        )
        return finish(
            "failed",
            link(
                "harness",
                actor,
                code,
                detail,
                reason=reason,
                explanation=explanation,
                evidence=found,
                **extra,
            ),
        )

    if (
        request.task_type not in TOOL_SETS
        or not isinstance(request.grant, dict)
        or not request.grant.get("context_identity")
        or not isinstance(request.grant.get("entries"), list)
    ):
        missing = [
            name
            for name, present in (
                ("a known task type", request.task_type in TOOL_SETS),
                ("a grant object", isinstance(request.grant, dict)),
                (
                    "a context identity",
                    isinstance(request.grant, dict)
                    and bool(request.grant.get("context_identity")),
                ),
                (
                    "grant entries",
                    isinstance(request.grant, dict)
                    and isinstance(request.grant.get("entries"), list),
                ),
            )
            if not present
        ]
        return fail(
            "grant_unavailable",
            f"the worker request for task type {request.task_type!r} lacks "
            + ", ".join(missing),
            "input",
            "Workers launches only with a complete frozen grant, which its caller computes",
        )
    grant_file = paths.control / "grant.json"
    grant_file.write_text(json.dumps(request.grant, indent=2, sort_keys=True))
    record["grant_digest"] = _digest(grant_file)
    rw = GrantView(request.grant["entries"]).paths("rw")
    try:
        settings = worker_settings(
            worktree,
            request.grant,
            paths,
            python=sys.executable,
            runtime=request.runtime,
            home=request.home,
        )
    except SettingsError as error:
        return fail(
            error.code,
            f"the worker settings cannot be generated: {error}",
            "environment",
            "the settings follow from the grant and the file layout, which Workers cannot "
            "change",
        )
    settings_file = paths.control / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2, sort_keys=True))
    (paths.control / "write_hook.py").write_text(
        write_hook_source(worktree, request.grant)
    )
    brief_file = paths.control / "brief.md"
    brief_file.write_text(brief(request, worktree))
    schema = result_schema(request.output_schema)
    schema_text = json.dumps(schema, separators=(",", ":"))
    (paths.control / "result.schema.json").write_text(schema_text)
    record.update(
        settings_digest=_digest(settings_file), brief_digest=_digest(brief_file)
    )
    credentials = _credentials(request)
    if credentials is not None:
        shutil.copy2(credentials, paths.config / ".credentials.json")
        os.chmod(paths.config / ".credentials.json", 0o600)
    try:
        record["pending_created"] = _precreate(worktree, request.grant)
    except OSError as error:
        return fail(
            "pending_not_created",
            f"a pending file of the grant could not be pre-created in {worktree}: "
            f"{type(error).__name__}: {error}",
            "environment",
            "Workers cannot create files the file system refuses",
        )
    try:
        before = snapshot(worktree)
    except (OSError, subprocess.CalledProcessError) as error:
        from ..errors import exception_detail

        return fail(
            "snapshot_failed",
            f"the task worktree {worktree} cannot be snapshotted before the launch: "
            + exception_detail(error),
            "environment",
            "the audit needs a snapshot from read-only Git, which failed",
        )

    session: str | None = None
    attempts: list[str] = []
    prompt, kind = brief_file.read_text(), "initial"
    for number in range(1, request.rounds + 2):
        round_record: dict = {"round": number, "prompt": kind}
        record["rounds"].append(round_record)
        command = _command(request, paths, schema_text, session)
        outcome = _launch(request, paths, command, prompt)
        record["stderr_tail"] = outcome["stderr"][-TAIL:].decode("utf-8", "replace")
        round_record.update(exit=outcome.get("exit"), duration=outcome.get("duration"))
        if outcome.get("error"):
            return fail(
                outcome["error"],
                f"round {number}: the command {command[0]} could not be started: "
                f"{outcome.get('detail', '')}",
                "environment",
                "Workers cannot install or repair the claude command; set CONCORDE_CLAUDE "
                "or PATH",
                attempts=attempts,
            )
        envelope = _envelope(outcome["stdout"])
        if envelope and envelope.get("session_id"):
            session = envelope["session_id"]
        round_record["session"] = session
        if envelope:
            round_record["claude"] = {
                key: envelope.get(key)
                for key in ("subtype", "is_error", "num_turns", "total_cost_usd")
            }
        record["transcript"] = _transcript(paths, session)
        verdict = audit(worktree, before, rw)
        round_record["audit"] = verdict.record()
        # A write outside the grant is reported whatever else went wrong in the round.
        outside = (
            ""
            if verdict.clean
            else f"; the worker also changed {len(verdict.violations)} path(s) outside "
            f"the grant's writable paths: {', '.join(verdict.violations)}"
        )
        if outcome["timed_out"]:
            return fail(
                "worker_timeout",
                f"round {number} did not finish within {request.timeout}s; the process "
                f"group was killed{outside}",
                "exhausted",
                f"Workers stops every round at the configured timeout ({request.timeout}s, "
                "workers.timeout_seconds) and does not extend it",
                attempts=attempts,
            )
        failure = claude_failure(outcome, envelope)
        if failure is not None:
            exhausted = failure["unhandled"]["reason"] == "exhausted"
            return fail(
                "worker_limit_reached" if exhausted else "claude_failed",
                f"round {number}: the Claude Code process ended with an error "
                f"({failure['code']}) before a structured result{outside}",
                "exhausted" if exhausted else "environment",
                (
                    f"Workers does not raise the limits it was given (max_turns "
                    f"{request.max_turns}, max_budget_usd {request.max_budget_usd})"
                    if exhausted
                    else "Workers does not retry a failed Claude Code process"
                ),
                attempts=attempts,
                causes=[failure],
            )
        result = envelope.get("structured_output")
        invalid = None
        try:
            if result is None:
                text = str(envelope.get("result") or "").strip()
                raise ContractError(
                    "the worker ended without a structured result"
                    + (f"; its final text: {text[-2000:]}" if text else "")
                )
            validate(result, schema)
            invalid = _consistency(result)
        except ContractError as error:
            invalid = str(error)
        if invalid is None:
            record["worker_result"] = result
        if not verdict.clean:
            return fail(
                "audit_violation",
                f"round {number}: the worker changed {len(verdict.violations)} path(s) "
                f"outside the grant's writable paths: {', '.join(verdict.violations)}; "
                + (
                    f"its result was invalid: {invalid}"
                    if invalid
                    else f"the worker itself reported status {result['status']}"
                ),
                "permission",
                "Workers never accepts a write outside the grant and never widens it",
                evidence=[
                    evidence("audit", str(number), f"violation: {path}")
                    for path in verdict.violations
                ],
                attempts=attempts,
                causes=[None if invalid else worker_link(record, result)],
            )
        if invalid:
            return fail(
                "worker_result_invalid",
                f"round {number}: the worker's result does not satisfy its result "
                f"schema: {invalid}",
                "capability",
                "Workers cannot repair a worker's answer and does not relaunch a worker for "
                "an invalid one",
                evidence=[
                    evidence(
                        "result-schema",
                        (paths.control / "result.schema.json").as_posix(),
                        "",
                    )
                ],
                attempts=attempts,
            )
        if result["status"] != "ok":
            _finalize(worktree, record, result, clean=True)
            cause = worker_link(record, result)
            return finish(
                result["status"],
                link(
                    "harness",
                    actor,
                    f"worker_{result['status']}",
                    f"the {request.task_type} worker ended {result['status']} in round "
                    f"{number} with {cause['code']}: {cause['detail']}",
                    reason="capability",
                    explanation="Workers resumes a worker only to repair failing configured "
                    "checks; it returns every other blocker unchanged",
                    evidence=[
                        evidence("run-record", (paths.root / "record.json").as_posix()),
                    ]
                    + (
                        [evidence("transcript", record["transcript"])]
                        if record["transcript"]
                        else []
                    ),
                    attempts=attempts,
                    causes=[cause],
                ),
            )
        if request.check_modules is None:
            _finalize(worktree, record, result, clean=True)
            return finish("ok")
        try:
            from .checks import run_checks

            checks = run_checks(
                worktree,
                modules=request.check_modules,
                log_directory=paths.checks / str(number),
            )
        except (SpecError, OSError) as error:
            code = getattr(error, "code", None) or "checks_unavailable"
            return fail(
                "checks_unavailable",
                f"round {number}: the configured checks of "
                f"{', '.join(request.check_modules)} could not run ({code}): {error}",
                "environment",
                "Workers runs the checks through Check execution and cannot repair its "
                "configuration or sandbox",
                attempts=attempts,
                causes=[
                    link(
                        "component",
                        "Check execution",
                        code,
                        str(error),
                        reason="environment",
                        explanation="the check could not be run as configured",
                    )
                ],
            )
        round_record["checks"] = checks
        failures = [item for item in checks if item["status"] != "passed"]
        if not failures:
            _finalize(worktree, record, result, clean=True)
            return finish("ok")
        attempts.append(
            f"round {number}: the worker ended ok; failing: "
            + ", ".join(
                f"{item['check_id']} ({item['status']}, exit {item['exit_code']})"
                for item in failures
            )
        )
        if number > request.rounds:
            return fail(
                "checks_failed",
                f"{len(failures)} configured check(s) still fail after {number} round(s) "
                f"({request.rounds} resume round(s) allowed): "
                + ", ".join(item["check_id"] for item in failures),
                "exhausted",
                f"Workers resumes the worker at most {request.rounds} time(s) with the "
                "failures and does not extend that",
                attempts=attempts,
                causes=[check_error(item) for item in failures],
            )
        prompt, kind = _resume_prompt(failures), "check_failures"
    return fail(
        "checks_failed",
        "no rounds left",
        "exhausted",
        "Workers does not extend the configured rounds",
        attempts=attempts,
    )


def _remove_unused_pending(worktree: Path, record: dict) -> None:
    """Remove every pre-created pending path the worker left empty; runs on every exit path."""
    for path in record["pending_created"]:
        if path in record["pending_removed"]:
            continue
        target = worktree / path.rstrip("/")
        if path.endswith("/"):
            if target.is_dir() and not any(target.iterdir()):
                target.rmdir()
                record["pending_removed"].append(path)
        elif target.is_file() and target.stat().st_size == 0:
            target.unlink()
            record["pending_removed"].append(path)


def _finalize(worktree: Path, record: dict, result: dict, *, clean: bool) -> None:
    """Perform the proposed deletions after a clean audit."""
    rw = [
        entry["path"]
        for entry in json.loads(
            (Path(record["run_directory"]) / "control/grant.json").read_text()
        )["entries"]
        if entry["level"] == "rw"
    ]
    if not clean:
        return
    for proposed in result.get("proposed_deletions", []):
        absolute = Path(os.path.normpath(os.path.join(worktree, proposed)))
        try:
            relative = absolute.relative_to(worktree).as_posix()
        except ValueError:
            record["deletions_refused"].append(proposed)
            continue
        if rw_allows(rw, relative) and absolute.is_file():
            absolute.unlink()
            record["deleted"].append(relative)
        else:
            record["deletions_refused"].append(proposed)


__all__ = [
    "WORKER_RESULT_SCHEMA",
    "WorkerRequest",
    "brief",
    "result_schema",
    "run_worker",
]
