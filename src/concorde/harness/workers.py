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
    "required": [
        "status",
        "summary",
        "problem",
        "attempts",
        "evidence",
        "options",
        "recommendation",
        "blocking",
        "impact",
        "proposed_deletions",
        "output",
    ],
    "properties": {
        "status": {"enum": ["ok", "blocked", "failed"]},
        "summary": {"type": "string", "minLength": 1},
        "problem": {"type": "string"},
        "attempts": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "ref", "detail"],
                "properties": {
                    "kind": {"enum": ["file", "command", "output", "spec"]},
                    "ref": {"type": "string", "minLength": 1},
                    "detail": {"type": "string"},
                },
            },
        },
        "options": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "recommendation": {"type": "string"},
        "blocking": {"type": "boolean"},
        "impact": {"type": "string"},
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
        "- End with the structured result. For `blocked` or `failed`, fill in the problem, what "
        "you tried, your evidence, the options and your recommendation.\n"
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


def run_worker(request: WorkerRequest) -> dict:
    """Run one worker to its end and return its run record (also written to the run directory)."""
    worktree = Path(os.path.realpath(request.worktree))
    run_id, paths = create_run(worktree)
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
        "errors": [],
        "run_directory": paths.root.as_posix(),
        "tmp": paths.tmp.as_posix(),
    }

    def finish(status: str, error: str | None = None, detail: str = "") -> dict:
        remove_short_tmp(paths)
        record["status"] = status
        if error:
            record["errors"].append({"code": error, "detail": detail})
        record["ended_at"] = now()
        write_record(paths, record)
        return record

    if (
        request.task_type not in TOOL_SETS
        or not isinstance(request.grant, dict)
        or not request.grant.get("context_identity")
        or not isinstance(request.grant.get("entries"), list)
    ):
        return finish(
            "failed", "grant_unavailable", "missing grant, entries or context identity"
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
        return finish("failed", error.code, str(error))
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
    record["pending_created"] = _precreate(worktree, request.grant)
    try:
        before = snapshot(worktree)
    except (OSError, subprocess.CalledProcessError) as error:
        return finish(
            "failed", "launch_failed", f"cannot snapshot the worktree: {error}"
        )

    session: str | None = None
    prompt, kind = brief_file.read_text(), "initial"
    for number in range(1, request.rounds + 2):
        round_record: dict = {"round": number, "prompt": kind}
        record["rounds"].append(round_record)
        outcome = _launch(
            request, paths, _command(request, paths, schema_text, session), prompt
        )
        record["stderr_tail"] = outcome["stderr"][-TAIL:].decode("utf-8", "replace")
        round_record.update(exit=outcome.get("exit"), duration=outcome.get("duration"))
        if outcome.get("error"):
            return finish("failed", outcome["error"], outcome.get("detail", ""))
        envelope = _envelope(outcome["stdout"]) or {}
        if envelope.get("session_id"):
            session = envelope["session_id"]
        round_record["session"] = session
        record["transcript"] = _transcript(paths, session)
        verdict = audit(worktree, before, rw)
        round_record["audit"] = verdict.record()
        if outcome["timed_out"]:
            return finish(
                "failed",
                "worker_timeout",
                f"round {number} exceeded {request.timeout}s",
            )
        result = envelope.get("structured_output")
        try:
            if result is None:
                raise ContractError("no structured output")
            validate(result, schema)
        except ContractError as error:
            if not envelope:
                return finish(
                    "failed", "launch_failed", "the worker printed no JSON envelope"
                )
            return finish("failed", "worker_result_invalid", str(error))
        record["worker_result"] = result
        if not verdict.clean:
            return finish("failed", "audit_violation", ", ".join(verdict.violations))
        if result["status"] != "ok":
            _finalize(worktree, record, result, clean=True)
            return finish(result["status"])
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
            return finish("failed", "checks_unavailable", str(error))
        round_record["checks"] = checks
        failures = [item for item in checks if item["status"] != "passed"]
        if not failures:
            _finalize(worktree, record, result, clean=True)
            return finish("ok")
        if number > request.rounds:
            return finish(
                "failed",
                "checks_failed",
                ", ".join(item["check_id"] for item in failures),
            )
        prompt, kind = _resume_prompt(failures), "check_failures"
    return finish("failed", "checks_failed", "no rounds left")


def _finalize(worktree: Path, record: dict, result: dict, *, clean: bool) -> None:
    """Remove unused pre-created files and perform proposed deletions after a clean audit."""
    rw = [
        entry["path"]
        for entry in json.loads(
            (Path(record["run_directory"]) / "control/grant.json").read_text()
        )["entries"]
        if entry["level"] == "rw"
    ]
    for path in record["pending_created"]:
        target = worktree / path.rstrip("/")
        if path.endswith("/"):
            if target.is_dir() and not any(target.iterdir()):
                target.rmdir()
                record["pending_removed"].append(path)
        elif target.is_file() and target.stat().st_size == 0:
            target.unlink()
            record["pending_removed"].append(path)
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
