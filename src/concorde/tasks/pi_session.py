"""The pi task session: its boundary, its rounds and the supervisor that runs each round.

pi has neither background sessions nor messages between sessions, so a pi task session is a
sequence of session rounds on one pi session file. ``start`` writes the boundary into
``.concorde/tasks/<task>.session/`` (``boundary.ts`` with the session's policy embedded, beside the
path decisions it imports), records the session with its first round and lets a detached
supervisor run that round; ``answer`` starts the next round with the main agent's answer as its
prompt, and ``stop`` ends the running one.

The supervisor (``main``, run as its own process) runs ``pi -p --mode json --approve`` in the task
worktree with the developer's own pi configuration and the boundary loaded with ``-e``, keeps the
round's progress file ``status.json`` current, writes pi's event stream and standard error beside
it, and records the round's outcome in the task record: ``delivered`` or ``escalated`` only when the
record holds the delivery commit or the escalations the session report names, ``failed`` with an
error link otherwise, ``stopped`` after ``stop``. A round whose supervisor ended without recording
it is settled as ``failed`` the next time Tasks looks at the session.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from .. import errors
from ..harness import pi_backend
from ..harness.pi_backend import PiStream
from ..spec.schema import ContractError, validate
from . import session, store

HERE = Path(__file__).resolve().parent
PROMPT = "generated/main-session/task-session-pi.md"
BOUNDARY_SOURCE = HERE / "pi_session.ts"
DECISIONS_SOURCE = HERE / "pi_session_policy.ts"
PATHS_SOURCE = HERE.parent / "harness" / "pi_policy.ts"
POLICY_MARKER = "const POLICY: SessionPolicy = {} as SessionPolicy;"
REPORT_TOOL = "concorde_report"
GO = b"go\n"
STOP_WAIT = 15.0
TEXT = 160

STRING = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": STRING}
# contract.tasks.session-report (specs/concorde/tasks/contracts.md)
REPORT_SCHEMA = {
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "summary", "commit", "decisions", "open"],
            "properties": {
                "status": {"const": "delivered"},
                "summary": STRING,
                "commit": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$",
                },
                "decisions": STRINGS,
                "open": STRINGS,
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "summary", "escalations", "decisions", "open"],
            "properties": {
                "status": {"const": "escalated"},
                "summary": STRING,
                "escalations": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "integer", "minimum": 1},
                },
                "decisions": STRINGS,
                "open": STRINGS,
            },
        },
    ]
}
# The parameters concorde_report offers the model: one object, since model providers expect an
# object at the top; the extension's reportProblem and REPORT_SCHEMA hold it to the contract.
TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "decisions", "open"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["delivered", "escalated"],
            "description": "delivered when delivery committed the task; escalated when you "
            "cannot go further without the main agent",
        },
        "summary": {"type": "string", "description": "What this round did."},
        "commit": {
            "type": "string",
            "description": "For delivered only: the delivery commit, in full.",
        },
        "escalations": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "For escalated only: the numbers concorde task escalate "
            "--by task-session printed for your escalations.",
        },
        "decisions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Each decision you made without the main agent, with its reason.",
        },
        "open": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What is still open.",
        },
    },
}


def prerequisites(worktree: Path) -> tuple[dict, list[str]]:
    """The programs a pi round needs, and a description of each one that is missing."""
    missing = []
    pi = os.environ.get("CONCORDE_PI") or "pi"
    found = pi if os.path.isabs(pi) and os.access(pi, os.X_OK) else pi_backend.which(pi)
    if not found:
        missing.append(
            f"the pi command {pi!r} is not on PATH; install pi (npm install -g "
            "@earendil-works/pi-coding-agent) or set CONCORDE_PI to its path"
        )
    if platform.system() == "Linux":
        for name in ("bwrap", "socat"):
            if not pi_backend.which(name):
                missing.append(
                    f"{name} is not on PATH; the sandbox of the session's commands needs it "
                    "on Linux; install it with your package manager"
                )
    package = pi_backend.sandbox_runtime(
        SimpleNamespace(sandbox_runtime=None), worktree
    )
    if not (package / "dist/index.js").is_file():
        missing.append(
            f"the sandbox-runtime package is missing at {package} (no dist/index.js); install "
            f"it with `npm install --prefix {package.parent.parent.parent} "
            f"@anthropic-ai/sandbox-runtime@{pi_backend.RUNTIME_VERSION}`, or set "
            "CONCORDE_SANDBOX_RUNTIME to an installed @anthropic-ai/sandbox-runtime directory"
        )
    return {"pi": found or pi, "sandbox_runtime": package}, missing


def _real(path: Path | str) -> str:
    return Path(os.path.realpath(path)).as_posix()


def short_tmp(directory: Path) -> Path:
    """The session's ``TMPDIR``: a private directory with a short path, stable for the session.

    sandbox-runtime creates Unix sockets below ``TMPDIR``, whose paths must stay under the
    kernel's 108-byte limit, which a directory under the task's session directory may exceed.
    """
    digest = hashlib.sha256(_real(directory).encode()).hexdigest()[:12]
    base = Path("/tmp") if os.access("/tmp", os.W_OK) else Path(tempfile.gettempdir())
    path = base / f"concorde-ts-{digest}"
    path.mkdir(mode=0o700, exist_ok=True)
    owner = path.lstat()
    if path.is_symlink() or owner.st_uid != os.getuid():
        raise store.TaskError(
            "session_failed",
            f"the session's temporary directory {path} exists but is not a directory of this "
            "user; remove it and start the session again",
        )
    return path


def policy(primary: Path, record: dict, directory: Path, home: Path | None) -> dict:
    """The boundary's policy: the task's paths, the sandbox's writable paths, the report tool."""
    writable = set(session.writable(primary, record, home)) | {
        _real(short_tmp(directory))
    }
    return {
        "task": record["id"],
        "worktree": _real(record["worktree"]),
        "files": [_real(store.decision_log_path(primary, record["id"]))],
        "sandbox": {"allowWrite": sorted(writable)},
        "reportSchema": TOOL_SCHEMA,
    }


def write_boundary(directory: Path, value: dict, package: Path) -> Path:
    """``boundary.ts`` with the policy and sandbox-runtime embedded, beside what it imports."""
    source = BOUNDARY_SOURCE.read_text(encoding="utf-8")
    if POLICY_MARKER not in source or pi_backend.RUNTIME_MARKER not in source:
        raise ValueError(f"{BOUNDARY_SOURCE} lacks the policy or runtime marker")
    source = source.replace(
        POLICY_MARKER,
        "const POLICY: SessionPolicy = " + json.dumps(value, sort_keys=True) + ";",
        1,
    ).replace(
        pi_backend.RUNTIME_MARKER,
        json.dumps((package / "dist/index.js").as_posix()),
        1,
    )
    shutil.copy2(PATHS_SOURCE, directory / "pi_policy.ts")
    shutil.copy2(DECISIONS_SOURCE, directory / "pi_session_policy.ts")
    boundary = directory / "boundary.ts"
    boundary.write_text(source, encoding="utf-8")
    return boundary


def brief(primary: Path, record: dict, main: str | None) -> str:
    """The first round's prompt: the rendered pi task-session guidance and this task."""
    path = session.PACKAGE_ROOT / PROMPT
    if not path.is_file():
        raise store.TaskError(
            "session_failed",
            f"the pi task-session guidance {path} is missing; run the build "
            "(python3 scripts/concorde.py build) of the Concorde package",
        )
    lines = [
        "## This task",
        "",
        f"- Task: `{record['id']}` on branch `{record['branch']}`",
        f"- Goal: {record['goal']}",
        f"- Modules: {', '.join(record['modules'])}",
        f"- Worktree (your working directory): `{record['worktree']}`",
        f"- Decision log: `{store.decision_log_path(primary, record['id'])}`",
    ]
    if main:
        lines.append(f"- Main agent session: `{main}`")
    return path.read_text(encoding="utf-8").strip() + "\n\n" + "\n".join(lines) + "\n"


def answer_prompt(text: str) -> str:
    return (
        "## The main agent's answer\n\n"
        f"{text.strip()}\n\n"
        "Continue the task from here, and end this round with `concorde_report` as the guidance "
        "says.\n"
    )


def command(pi: str, directory: Path, session_id: str, model: str | None) -> list[str]:
    return [
        pi,
        "-p",
        "--mode",
        "json",
        "--approve",
        "-e",
        (directory / "boundary.ts").as_posix(),
        "--session-dir",
        (directory / "pi").as_posix(),
        "--session-id",
        session_id,
        *(["--model", model] if model else []),
    ]


def _write_json(path: Path, value: dict) -> None:
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def _alive(pid: int) -> bool:
    """Whether a process runs; one that ended but was not yet reaped (a zombie) does not."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return True
    return stat.rsplit(")", 1)[-1].split()[0] != "Z"


def latest(record: dict) -> dict | None:
    """The task's latest pi task session, if it has one."""
    found = [
        item for item in record.get("sessions") or [] if item.get("program") == "pi"
    ]
    return found[-1] if found else None


def running(found: dict | None) -> dict | None:
    if not found:
        return None
    return next((item for item in found["rounds"] if item["status"] == "running"), None)


def _actor(task_id: str, session_id: str, number: int) -> str:
    return (
        f"Tasks pi task-session supervisor (task {task_id}, session {session_id}, "
        f"round {number})"
    )


def settle(primary: Path, record: dict) -> dict:
    """Record as failed every running round whose supervisor process has ended."""
    for found in record.get("sessions") or []:
        if found.get("program") != "pi":
            continue
        for item in found["rounds"]:
            if item["status"] != "running" or _alive(item["supervisor_pid"]):
                continue
            error = errors.link(
                "component",
                _actor(record["id"], found["id"], item["round"]),
                "session_supervisor_lost",
                f"the supervisor (process {item['supervisor_pid']}) of round {item['round']} "
                f"ended without recording the round; its event stream is {item['events']} and "
                f"pi's standard error {item['stderr']}",
                reason="environment",
                explanation="the process that records the round is gone, so nothing records "
                "what the round did",
                evidence=[
                    errors.evidence("events", item["events"]),
                    errors.evidence("stderr", item["stderr"]),
                ],
                options=[
                    "read the event stream to see how far the round got",
                    "continue the session with concorde task session <task> --answer",
                ],
            )
            try:
                store.finish_round(
                    primary,
                    record["id"],
                    found["id"],
                    item["round"],
                    {"status": "failed", "error": error},
                )
            except store.TaskError as refused:
                if refused.code != "session_idle":
                    raise
    return store.load_task(primary, record["id"])


def _admitted(here: Path, task_id: str) -> tuple[Path, dict, Path]:
    primary = store.require_primary(here)
    record = store.load_task(primary, task_id)
    if record["state"] not in ("open", "active", "delivered"):
        raise store.TaskError(
            "task_closed",
            f"task {task_id} is {record['state']}; a session works only in an open task",
        )
    worktree = Path(record["worktree"])
    if not worktree.is_dir():
        raise store.TaskError(
            "missing_worktree",
            f"the worktree {worktree} of task {task_id} does not exist",
        )
    return primary, settle(primary, record), worktree


def _programs(worktree: Path) -> dict:
    programs, missing = prerequisites(worktree)
    if missing:
        raise store.TaskError(
            "session_failed",
            f"the pi task session cannot start on this machine: {'; '.join(missing)}",
        )
    return programs


def _round(number: int, directory: Path, pid: int, answer: str | None) -> dict:
    entry = {
        "round": number,
        "prompt": "task" if answer is None else "answer",
        "status": "running",
        "supervisor_pid": pid,
        "started_at": store.now(),
        "ended_at": None,
        "report": None,
        "error": None,
        "events": (directory / f"round-{number}.events.jsonl").as_posix(),
        "stderr": (directory / f"round-{number}.stderr.log").as_posix(),
    }
    if answer is not None:
        entry["answer"] = answer
    return entry


def _launch(
    primary: Path,
    task_id: str,
    session_id: str,
    number: int,
    directory: Path,
    prompt: str,
) -> subprocess.Popen:
    """Start the round's supervisor, held until ``_go`` once the round is recorded."""
    (directory / f"round-{number}.prompt.md").write_text(prompt, encoding="utf-8")
    source = session.PACKAGE_ROOT / "src"
    code = (
        f"import sys; sys.path.insert(0, {source.as_posix()!r}); "
        "from concorde.tasks.pi_session import main; sys.exit(main(sys.argv[1:]))"
    )
    log = (directory / f"round-{number}.supervisor.log").open("ab")
    try:
        return subprocess.Popen(
            [
                sys.executable,
                "-c",
                code,
                primary.as_posix(),
                task_id,
                session_id,
                str(number),
            ],
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
            cwd=directory,
            start_new_session=True,
        )
    except OSError as error:
        raise store.TaskError(
            "session_failed",
            f"the supervisor of round {number} of the task session of {task_id} could not "
            f"start: {error}",
        ) from error
    finally:
        log.close()


def _go(process: subprocess.Popen) -> None:
    assert process.stdin is not None
    process.stdin.write(GO)
    process.stdin.close()


def _progress(directory: Path, task_id: str, session_id: str, entry: dict) -> None:
    _write_json(
        directory / "status.json",
        {
            "kind": "task-session",
            "task": task_id,
            "session_id": session_id,
            "round": entry["round"],
            "phase": "running",
            "status": None,
            "summary": None,
            "supervisor_pid": entry["supervisor_pid"],
            "last_action": None,
            "started_at": entry["started_at"],
            "updated_at": entry["started_at"],
        },
    )


def _session_of(primary: Path, task_id: str, session_id: str) -> dict:
    record = store.load_task(primary, task_id)
    return next(item for item in record["sessions"] if item.get("id") == session_id)


def start(
    here: Path,
    task_id: str,
    main: str | None,
    *,
    model: str | None = None,
    dry_run: bool = False,
    home: Path | None = None,
) -> dict:
    """Write the boundary and, unless ``dry_run``, start a pi task session's first round."""
    primary, record, worktree = _admitted(here, task_id)
    busy = running(latest(record))
    if busy:
        raise store.TaskError(
            "session_busy",
            f"round {busy['round']} of the task session of {task_id} is still running "
            f"(supervisor process {busy['supervisor_pid']}); answer or stop it instead",
        )
    programs = _programs(worktree)
    directory = session.session_directory(primary, task_id)
    for name in ("", "pi"):
        (directory / name).mkdir(parents=True, exist_ok=True)
    value = policy(primary, record, directory, home)
    boundary = write_boundary(directory, value, programs["sandbox_runtime"])
    session_id = f"task-{task_id}-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
    shown = command(programs["pi"], directory, session_id, model)
    if dry_run:
        return {
            "command": shlex.join(shown),
            "cwd": worktree.as_posix(),
            "boundary": boundary.as_posix(),
        }
    session.create_writable(value["sandbox"]["allowWrite"])
    prompt = brief(primary, record, main)
    process = _launch(primary, task_id, session_id, 1, directory, prompt)
    entry = _round(1, directory, process.pid, None)
    recorded = {
        "program": "pi",
        "id": session_id,
        "name": session.session_name(task_id),
        "main": main or None,
        "directory": directory.as_posix(),
        "model": model,
        "started_at": entry["started_at"],
        "rounds": [entry],
    }
    try:
        store.record_session(primary, task_id, recorded)
        _progress(directory, task_id, session_id, entry)
    except BaseException:
        process.kill()
        raise
    _go(process)
    return recorded


def answer(here: Path, task_id: str, text: str, *, home: Path | None = None) -> dict:
    """Start the next round of the task's latest pi session with the main agent's answer."""
    if not text.strip():
        raise store.TaskError("invalid_input", "--answer needs the main agent's answer")
    primary, record, worktree = _admitted(here, task_id)
    found = latest(record)
    if found is None:
        raise store.TaskError(
            "no_session",
            f"task {task_id} has no pi task session; start one with concorde task session "
            f"{task_id}",
        )
    busy = running(found)
    if busy:
        raise store.TaskError(
            "session_busy",
            f"round {busy['round']} of the task session of {task_id} is still running "
            f"(supervisor process {busy['supervisor_pid']}); wait for its report or stop it",
        )
    programs = _programs(worktree)
    directory = Path(found["directory"])
    value = policy(primary, record, directory, home)
    write_boundary(directory, value, programs["sandbox_runtime"])
    session.create_writable(value["sandbox"]["allowWrite"])
    number = len(found["rounds"]) + 1
    process = _launch(
        primary, task_id, found["id"], number, directory, answer_prompt(text)
    )
    entry = _round(number, directory, process.pid, text)
    try:
        store.begin_round(primary, task_id, found["id"], entry)
        _progress(directory, task_id, found["id"], entry)
    except BaseException:
        process.kill()
        raise
    _go(process)
    return _session_of(primary, task_id, found["id"])


def stop(here: Path, task_id: str) -> dict:
    """End the running round of the task's latest pi session, which is recorded ``stopped``."""
    primary = store.require_primary(here)
    record = settle(primary, store.load_task(primary, task_id))
    found = latest(record)
    if found is None:
        raise store.TaskError("no_session", f"task {task_id} has no pi task session")
    busy = running(found)
    if busy is None:
        raise store.TaskError(
            "session_idle",
            f"no round of the task session of {task_id} is running",
        )
    try:
        os.kill(busy["supervisor_pid"], signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        current = _session_of(primary, task_id, found["id"])
        if current["rounds"][busy["round"] - 1]["status"] != "running":
            return current
        time.sleep(0.2)
    record = settle(primary, store.load_task(primary, task_id))
    return next(item for item in record["sessions"] if item.get("id") == found["id"])


# The supervisor ---------------------------------------------------------------------------------


def _target(arguments: dict) -> str:
    for key in ("path", "command", "pattern"):
        value = arguments.get(key)
        if isinstance(value, str) and value:
            text = " ".join(value.split())
            return text if len(text) <= TEXT else text[: TEXT - 1] + "…"
    return ""


def verify(report: dict, record: dict) -> list[str]:
    """What the task record contradicts in a session report; empty when it holds everything."""
    if report["status"] == "delivered":
        commits = [item["commit"] for item in record.get("deliveries") or []]
        if report["commit"] not in commits:
            return [
                f"the report names the delivery commit {report['commit']}, but the task's "
                f"deliveries are {', '.join(commits) or 'none'}"
            ]
        return []
    held = record.get("escalations") or []
    mismatches = []
    for number in report["escalations"]:
        if number > len(held):
            mismatches.append(
                f"escalation {number} does not exist: the task has {len(held)}"
            )
        elif held[number - 1]["error"].get("level") != "task-session":
            mismatches.append(
                f"escalation {number} was recorded at the level "
                f"{held[number - 1]['error'].get('level')}, not by the task session"
            )
    return mismatches


def outcome(
    task_id: str,
    session_id: str,
    entry: dict,
    stream: PiStream,
    exit_code: int | None,
    stopped: bool,
    record: dict,
) -> dict:
    """The fields a finished round records: its status, report and error."""
    actor = _actor(task_id, session_id, entry["round"])
    report = stream.result
    logs = [
        errors.evidence("events", entry["events"]),
        errors.evidence("stderr", entry["stderr"]),
    ]
    if stopped:
        return {"status": "stopped", "report": report, "error": None}
    if report is None:
        stderr = Path(entry["stderr"])
        tail = (
            stderr.read_text(encoding="utf-8", errors="replace")[-2000:].strip()
            if stderr.is_file()
            else ""
        )
        detail = (
            f"pi ended round {entry['round']} of the task session of {task_id} without "
            f"calling concorde_report: exit code {exit_code}, {stream.turns} turn(s), last "
            f"stop reason {stream.stop_reason or '(none)'}"
        )
        if stream.error_message:
            detail += f", error message: {stream.error_message[-2000:]}"
        if stream.final_text:
            detail += f"; its last message ends with: {stream.final_text[-1000:]}"
        detail += (
            f"; standard error ends with: {tail or '(empty)'}; the event stream is "
            f"{entry['events']}"
        )
        return {
            "status": "failed",
            "report": None,
            "error": errors.link(
                "component",
                actor,
                "session_no_report",
                detail,
                reason="environment",
                explanation="the supervisor records what pi did and cannot finish the round's "
                "work itself",
                evidence=logs,
                options=[
                    "read the event stream and standard error",
                    f"continue the session with concorde task session {task_id} --answer",
                    "carry the task out yourself",
                ],
            ),
        }
    try:
        validate(report, REPORT_SCHEMA)
    except ContractError as error:
        mismatches = [
            f"the report does not follow the session report contract: {error}"
        ]
    else:
        mismatches = verify(report, record)
    if mismatches:
        return {
            "status": "failed",
            "report": report,
            "error": errors.link(
                "component",
                actor,
                "session_report_unverified",
                f"round {entry['round']} of the task session of {task_id} reported "
                f"{report.get('status')}, which the task record does not bear out: "
                + "; ".join(mismatches),
                reason="decision",
                explanation="a round counts as delivered or escalated only when the task "
                "record holds what its report names; what to do next is the main agent's "
                "decision",
                evidence=logs,
                options=[
                    f"read the task record with concorde task show {task_id}",
                    f"answer the session with concorde task session {task_id} --answer",
                ],
            ),
        }
    return {"status": report["status"], "report": report, "error": None}


def supervise(primary: Path, task_id: str, session_id: str, number: int) -> int:
    """Run one round and record its outcome; the process's own work once released."""
    if sys.stdin.buffer.read(len(GO)) != GO:
        return 0
    directory = session.session_directory(primary, task_id)
    status_path = directory / "status.json"
    record = store.load_task(primary, task_id)
    found = next(item for item in record["sessions"] if item.get("id") == session_id)
    entry = found["rounds"][number - 1]
    progress = json.loads(status_path.read_text(encoding="utf-8"))
    state = {"stopped": False, "child": None}

    def terminate(_signum, _frame):
        state["stopped"] = True
        child = state["child"]
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGTERM, terminate)
    stream = PiStream(result_tool=REPORT_TOOL)
    try:
        worktree = Path(record["worktree"])
        programs, missing = prerequisites(worktree)
        if missing:
            raise RuntimeError("; ".join(missing))
        environment = dict(
            os.environ,
            CONCORDE_CLIENT="pi",
            CONCORDE_TASK_SESSION=task_id,
            TMPDIR=short_tmp(directory).as_posix(),
            # sandbox-runtime hands its commands this TMPDIR, else a /tmp/claude that may not exist.
            CLAUDE_CODE_TMPDIR=short_tmp(directory).as_posix(),
        )
        prompt = (directory / f"round-{number}.prompt.md").read_bytes()
        with (
            open(entry["events"], "wb") as events,
            open(entry["stderr"], "wb") as stderr,
        ):
            child = subprocess.Popen(
                command(programs["pi"], directory, session_id, found["model"]),
                cwd=worktree,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr,
                start_new_session=True,
            )
            state["child"] = child
            if state["stopped"]:
                terminate(None, None)
            assert child.stdin is not None and child.stdout is not None
            try:
                child.stdin.write(prompt)
                child.stdin.close()
            except BrokenPipeError:
                pass
            for raw in child.stdout:
                events.write(raw)
                events.flush()
                for tool, arguments in stream.feed(raw.decode("utf-8", "replace")):
                    progress["last_action"] = {
                        "tool": tool,
                        "target": _target(arguments),
                        "at": store.now(),
                    }
                    progress["updated_at"] = progress["last_action"]["at"]
                    _write_json(status_path, progress)
            exit_code = child.wait()
        fields = outcome(
            task_id,
            session_id,
            entry,
            stream,
            exit_code,
            state["stopped"],
            store.load_task(primary, task_id),
        )
    except Exception as error:  # noqa: BLE001 -- every failure is recorded with its detail
        fields = {
            "status": "stopped" if state["stopped"] else "failed",
            "report": stream.result,
            "error": None
            if state["stopped"]
            else errors.from_exception(
                _actor(task_id, session_id, number),
                error,
                code="session_failed",
                reason="environment",
                explanation="the supervisor could not run the round and records why",
                trace=directory / f"round-{number}.traceback.txt",
            ),
        }
    # One round runs at a time and the next recreates it, so nothing outlives the round.
    with contextlib.suppress(store.TaskError):
        shutil.rmtree(short_tmp(directory), ignore_errors=True)
    store.finish_round(primary, task_id, session_id, number, fields)
    report = fields.get("report") or {}
    progress.update(
        {
            "phase": "finished",
            "status": fields["status"],
            "summary": report.get("summary")
            or ((fields.get("error") or {}).get("detail") or "")[:TEXT],
            "updated_at": store.now(),
        }
    )
    _write_json(status_path, progress)
    return 0


def main(argv: list[str]) -> int:
    primary, task_id, session_id, number = argv
    return supervise(Path(primary), task_id, session_id, int(number))


__all__ = [
    "REPORT_SCHEMA",
    "TOOL_SCHEMA",
    "answer",
    "brief",
    "command",
    "main",
    "outcome",
    "policy",
    "prerequisites",
    "settle",
    "short_tmp",
    "start",
    "stop",
    "verify",
    "write_boundary",
]
