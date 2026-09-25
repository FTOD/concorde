"""Run one worker: prepare its run directory, launch and resume it, audit and check.

``run_worker`` performs the standard sequence of the Workers Module on the backend the request
names, Claude Code or pi: freeze the grant, pre-create the pending files it makes writable, let the
backend generate its configuration from the grant, launch the worker in its own process group while
keeping the progress file current, audit the task worktree after every round, run the configured
checks outside the worker, resume the same session when a check fails, perform the deletions it
proposed, and write the run record. The returned record keeps the worker's answer verbatim and
apart from what the host observed itself.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import WORKER_ERROR_SCHEMA, evidence, link
from ..spec.repository_base import SpecError
from ..spec.schema import ContractError, validate
from .audit import audit, rw_allows, snapshot
from .claude_backend import BackendRefusal, ClaudeBackend
from .pi_backend import PiBackend
from .progress import Progress
from .runs import create_run, now, remove_short_tmp, write_record
from .settings import TOOL_SETS, GrantView

BACKENDS = {"claude": ClaudeBackend, "pi": PiBackend}

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
    backend: str = "claude"
    # The reasoning level: Claude Code's --effort, pi's --thinking.
    reasoning: str | None = None
    # The Operation and worker role the model was chosen for, recorded only.
    operation: str | None = None
    role: str | None = None
    pi: str | None = None
    pi_config: Path | None = None
    sandbox_runtime: Path | None = None
    extra: dict = field(default_factory=dict)


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def brief(request: WorkerRequest, worktree: Path) -> str:
    """The worker's only instruction: the task, then its boundary as absolute paths."""
    view = GrantView(request.grant["entries"])
    pi = request.backend == "pi"
    shell, writer = ("bash", "write tool") if pi else ("Bash", "Write tool")
    ending = (
        "- End by calling the `concorde_result` tool exactly once with the structured result; "
        "it ends your session."
        if pi
        else "- End with the structured result."
    )

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
        f"- A file you create with {shell} outside the writable paths is lost when you finish; "
        f"create files with the {writer} instead.\n"
        "- When the Spec does not state a promise you need, do not infer it from code: return "
        "`blocked` and describe the missing promise.\n"
        f"{ending} For `ok`, `error` is null. For `blocked` or `failed`, "
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


def _launch(request, paths, command, environment, prompt: str, on_line) -> dict:
    """One round: run the command in its own process group, reading standard output as it
    arrives, and always kill the group after."""
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=paths.work,
            env=environment,
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
    stdout: list[bytes] = []
    stderr: list[bytes] = []

    def feed() -> None:
        try:
            process.stdin.write(prompt.encode())
            process.stdin.close()
        except OSError:
            pass

    def read_stdout() -> None:
        for line in process.stdout:
            stdout.append(line)
            try:
                on_line(line.decode("utf-8", "replace"))
            except Exception:  # noqa: BLE001 -- progress never changes the run
                pass

    def read_stderr() -> None:
        for chunk in iter(lambda: process.stderr.read(65536), b""):
            stderr.append(chunk)

    threads = [
        threading.Thread(target=target, daemon=True)
        for target in (feed, read_stdout, read_stderr)
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=request.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        _kill_group(process)
    process.wait()
    for thread in threads:
        thread.join(timeout=10)
    return {
        "stdout": b"".join(stdout),
        "stderr": b"".join(stderr)[-4 * TAIL :],
        "exit": process.returncode,
        "timed_out": timed_out,
        "duration": round(time.monotonic() - started, 3),
    }


def _kill_group(process) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


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
    backend = BACKENDS[request.backend]() if request.backend in BACKENDS else None
    progress = Progress(
        paths.root,
        run_id=run_id,
        task_type=request.task_type,
        backend=request.backend,
        worktree=worktree.as_posix(),
    )
    record: dict = {
        "run_id": run_id,
        "task_type": request.task_type,
        "backend": request.backend,
        "operation": request.operation,
        "role": request.role,
        "model": request.model,
        "reasoning": request.reasoning,
        "worktree": worktree.as_posix(),
        "context_identity": request.grant.get("context_identity")
        if isinstance(request.grant, dict)
        else None,
        "grant_digest": None,
        "settings_digest": None,
        "brief_digest": None,
        "tools": backend.tools(request.task_type)
        if backend and request.task_type in TOOL_SETS
        else None,
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
        progress.finish(status)
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

    if backend is None:
        return fail(
            "unknown_backend",
            f"the worker request names the backend {request.backend!r}; Workers knows "
            + ", ".join(sorted(BACKENDS)),
            "input",
            "the backend is the main session's agent program, which the Operation host "
            "names and Workers does not choose",
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
    schema = result_schema(request.output_schema)
    schema_text = json.dumps(schema, separators=(",", ":"))
    (paths.control / "result.schema.json").write_text(schema_text)
    try:
        configuration = backend.prepare(request, worktree, paths, schema)
    except BackendRefusal as refusal:
        return fail(refusal.code, refusal.detail, refusal.reason, refusal.explanation)
    brief_file = paths.control / "brief.md"
    brief_file.write_text(brief(request, worktree))
    record.update(
        settings_digest=_digest(configuration), brief_digest=_digest(brief_file)
    )
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
    environment = backend.environment(request, paths)
    prompt, kind = brief_file.read_text(), "initial"
    for number in range(1, request.rounds + 2):
        round_record: dict = {"round": number, "prompt": kind}
        record["rounds"].append(round_record)
        command = backend.command(request, paths, schema_text, session)
        stream = backend.stream()

        def on_line(line: str, stream=stream) -> None:
            for tool, arguments in stream.feed(line):
                progress.action(tool, arguments)

        progress.phase("worker", round=number)
        outcome = _launch(request, paths, command, environment, prompt, on_line)
        record["stderr_tail"] = outcome["stderr"][-TAIL:].decode("utf-8", "replace")
        round_record.update(exit=outcome.get("exit"), duration=outcome.get("duration"))
        if outcome.get("error"):
            return fail(
                outcome["error"],
                f"round {number}: the command {command[0]} could not be started: "
                f"{outcome.get('detail', '')}",
                "environment",
                backend.missing_command,
                attempts=attempts,
            )
        concluded = stream.conclude(outcome)
        if concluded.session:
            session = concluded.session
        round_record["session"] = session
        round_record.update(concluded.info)
        record["transcript"] = backend.transcript(paths, session)
        progress.phase("audit")
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
        failure = concluded.failure
        if failure is not None:
            exhausted = concluded.exhausted
            return fail(
                "worker_limit_reached" if exhausted else backend.failure_code,
                f"round {number}: the {backend.process} process ended with an error "
                f"({failure['code']}) before a structured result{outside}",
                "exhausted" if exhausted else "environment",
                (
                    f"Workers does not raise the limits it was given (max_turns "
                    f"{request.max_turns}, max_budget_usd {request.max_budget_usd})"
                    if exhausted
                    else f"Workers does not retry a failed {backend.process} process"
                ),
                attempts=attempts,
                causes=[failure],
            )
        result = concluded.result
        invalid = None
        try:
            if result is None:
                text = concluded.final_text
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
        progress.phase("checks")
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
