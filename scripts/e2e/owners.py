"""The owners case: several live main sessions on one test project, and only a run's owner woken.

Concorde promises that every run has at most one owner main session, the one whose own tool
started it, and that only the owner is woken when the run ends, while every other main session,
Claude Code or pi, may see the run's state and is never woken by it. This case checks that promise
with real sessions: it keeps Claude Code and pi main sessions running at once in the test
project's primary worktree (two of each by default), each a live session (``live.py``) whose
wakes are its program's own, and plays three phases on the project's open task:

1. **unowned**: the case itself starts ``concorde task-validation`` in the task worktree, a run of
   nobody's tool, which must wake no session;
2. **owned by pi**: the first pi session starts ``task-validation`` with its ``concorde_run`` tool;
3. **owned by Claude Code**: the first Claude Code session starts it in background Bash.

Each run is held back by the case, which holds the task's workspace lock until every pi session's
run view shows the run running, so that the run outlives its launch and its end is a wake rather
than the launching tool's own answer. Once the run has ended and a grace period has passed, the
owner must have been woken and every other session must not have begun a turn or received a
notification. Then each other session is shown to see the run: a pi session's ``/concorde``
listing names it, and a Claude Code session, into which nothing is pushed, asked to run
``concorde task show <task>``, finds it with its status.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from common import E2EError
from live import LiveSession
from sessions import records_of

GRACE_SECONDS = 20.0
LIMIT_SECONDS = 600.0
READY = "Reply with the single word READY and nothing else."


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


@contextmanager
def workspace_held(records: Path, workspace: str, limit: float = LIMIT_SECONDS):
    """Hold the workspace lock of ``workspace``, as Execution's runs do, so that a run started
    meanwhile with ``--wait`` waits for it; waits first for a run that still holds it."""
    path = records / "locks" / "workspaces" / f"{workspace}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        deadline = time.monotonic() + limit
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise E2EError(
                        "workspace_busy",
                        f"the workspace lock {path} stayed held for {limit:.0f}s",
                    ) from None
                time.sleep(0.5)
        stream.seek(0)
        stream.truncate()
        stream.write(f"the end-to-end owners case (process {os.getpid()})\n")
        stream.flush()
        yield path
    finally:
        try:
            stream.seek(0)
            stream.truncate()
            stream.flush()
            fcntl.flock(stream, fcntl.LOCK_UN)
        finally:
            stream.close()


def _run_folders(records: Path) -> list[Path]:
    """Every run folder under the ``.concorde`` ``records``: the current tasks' workspace
    folders, their workflow steps, and the unbound runs (Tracing's layout)."""
    return [
        *sorted(records.glob("tasks/*/workspace/runs/r-*")),
        *sorted(records.glob("tasks/*/workspace/workflow/steps/*/run")),
        *sorted(records.glob("unbound/r-*")),
    ]


def _run_id(directory: Path) -> str | None:
    try:
        state = json.loads((directory / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return state.get("run_id") or directory.name


def new_run(records: Path, workspace: str, known: set[str]) -> str | None:
    """The one run of ``workspace`` in the run store that ``known`` does not name, if any."""
    for directory in _run_folders(records):
        try:
            state = json.loads((directory / "status.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        run_id = state.get("run_id") or directory.name
        if run_id in known:
            continue
        if (
            state.get("kind") in ("operation", "command")
            and state.get("workspace") == workspace
        ):
            return run_id
    return None


def known_runs(records: Path) -> set[str]:
    return {run_id for folder in _run_folders(records) if (run_id := _run_id(folder))}


def run_folder(records: Path, run_id: str) -> Path:
    for folder in _run_folders(records):
        if _run_id(folder) == run_id:
            return folder
    return records / "unbound" / run_id


def result_of(records: Path, run_id: str) -> dict | None:
    try:
        return json.loads(
            (run_folder(records, run_id) / "result.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None


def until(condition, limit: float, what: str, poll: float = 0.5, **evidence) -> None:
    deadline = time.monotonic() + limit
    while not condition():
        if time.monotonic() > deadline:
            raise E2EError("live_timeout", f"{what} within {limit:.0f}s", **evidence)
        time.sleep(poll)


def shows_running(session: LiveSession, moment: float) -> bool:
    """Whether a pi session's run view has shown a running run since ``moment``."""
    return any("running" in text for text in session.statuses(moment))


def owner_prompt(client: str, task: str, worktree: Path, limit: float) -> str:
    wait = str(int(limit))
    if client == "pi":
        return (
            f'Call the concorde_run tool with operation "task-validation", task "{task}" and '
            f'arguments ["--wait", "{wait}"]. Then end your turn at once, replying only STARTED. '
            "When you later receive the run's result, reply only DONE followed by its status."
        )
    return (
        "Run this command with the Bash tool in the background (run_in_background true), then "
        "end your turn at once, replying only STARTED:\n"
        f"cd {worktree} && .concorde/bin/concorde task-validation --wait {wait}\n"
        "When you are later notified that it finished, reply only DONE followed by the status "
        "its output names."
    )


def query_prompt(task: str, run_id: str) -> str:
    return (
        f"Run `.concorde/bin/concorde task show {task}` with the Bash tool in the foreground and "
        f"reply only with the status it lists for the run {run_id}."
    )


def listed_status(output: str, run_id: str) -> str | None:
    """The status that the output of ``concorde task show`` lists for ``run_id``, or None when
    the output holds no such listing."""
    decoder = json.JSONDecoder()
    start = output.find("{")
    while start != -1:
        try:
            value, _ = decoder.raw_decode(output, start)
        except ValueError:
            start = output.find("{", start + 1)
            continue
        if isinstance(value, dict) and isinstance(value.get("runs"), list):
            for run in value["runs"]:
                if isinstance(run, dict) and run.get("run_id") == run_id:
                    return run.get("status")
        start = output.find("{", start + 1)
    return None


def judge(
    sessions: list[LiveSession], owner: LiveSession | None, moment: float, end: float
) -> tuple[list[dict], list[str]]:
    """Who was woken between ``moment`` and ``end``, and what contradicts the promise: the owner
    not woken, or any other session woken."""
    verdicts, problems = [], []
    for session in sessions:
        woken = session.woken(moment, end)
        verdict = {
            "session": session.name,
            "owner": session is owner,
            "woken": woken,
            "turns": len(session.turns(moment, end)),
            "notifications": [
                event.get("subtype") or (event.get("message") or {}).get("customType")
                for event in session.notifications(moment, end)
            ],
        }
        verdicts.append(verdict)
        if session is owner and not woken:
            problems.append(
                f"the owner {session.name} was not woken when its run ended"
            )
        if session is not owner and woken:
            problems.append(
                f"{session.name} was woken by a run it does not own "
                f"({verdict['turns']} turn(s), notifications {verdict['notifications']})"
            )
    return verdicts, problems


def phase(
    name: str,
    sessions: list[LiveSession],
    owner: LiveSession | None,
    *,
    project: Path,
    worktree: Path,
    records: Path,
    task: str,
    directory: Path,
    grace: float,
    limit: float,
) -> dict:
    """One phase: a run held back until every pi session shows it, released, ended, judged, and
    then looked up by every session that does not own it."""
    known = known_runs(records)
    started = time.time()
    with workspace_held(records, task, limit):
        if owner is None:
            log = (directory / f"{name}-run.log").open("w")
            subprocess.Popen(
                [
                    str(worktree / ".concorde/bin/concorde"),
                    "task-validation",
                    "--wait",
                    str(int(limit)),
                ],
                cwd=worktree,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            baseline = started
        else:
            prompted = owner.send(owner_prompt(owner.client, task, worktree, limit))
            owner.wait_settled(prompted, limit)
            refused = owner.client == "pi" and owner.refusal(prompted)
            if refused:
                raise E2EError(
                    "session_failed", f"{owner.name} refused its prompt: {refused}"
                )
            baseline = time.time()
        until(
            lambda: new_run(records, task, known) is not None,
            limit,
            f"no run of {task} appeared in the run store of {records} for the phase {name}",
            log=str(owner.log) if owner else None,
        )
        run_id = new_run(records, task, known)
        pis = [session for session in sessions if session.client == "pi"]
        until(
            lambda: all(shows_running(session, started) for session in pis),
            60.0,
            f"not every pi session's run view showed run {run_id} running",
            sessions=[
                session.name for session in pis if not shows_running(session, started)
            ],
        )
    released = time.time()
    until(
        lambda: result_of(records, run_id) is not None,
        limit,
        f"run {run_id} wrote no result",
        progress=str(run_folder(records, run_id) / "status.json"),
    )
    if owner is not None:
        until(
            lambda: owner.woken(released) and owner.settled(released),
            limit,
            f"the owner {owner.name} was not woken with the end of run {run_id}",
            log=str(owner.log),
        )
    time.sleep(grace)
    end = time.time()
    verdicts, problems = judge(sessions, owner, baseline, end)
    result = result_of(records, run_id) or {}
    status = result.get("status")
    seen = []
    for session in sessions:
        if session is owner:
            continue
        if session.client == "pi":
            asked = session.send("/concorde")
            until(
                lambda session=session, asked=asked: any(
                    run_id in text for text in session.notices(asked)
                ),
                30.0,
                f"{session.name}'s /concorde listing did not name run {run_id}",
                log=str(session.log),
            )
            listing = next(text for text in session.notices(asked) if run_id in text)
            line = next(item for item in listing.splitlines() if run_id in item)
            shown = not line.startswith("running")
            # A pi session saw the run running and then ended through its status bar too.
            seen.append(
                {
                    "session": session.name,
                    "how": "/concorde",
                    "line": line,
                    "ok": shown and shows_running(session, started),
                }
            )
            if not shown:
                problems.append(f"{session.name} still lists run {run_id} as running")
            # The listing is an extension command: it must not begin a turn either.
            if session.turns(asked):
                problems.append(f"{session.name} began a turn for /concorde")
        else:
            asked = session.send(query_prompt(task, run_id))
            session.wait_settled(asked, limit)
            found_it = listed_status(session.tool_output(asked), run_id) == status
            seen.append(
                {
                    "session": session.name,
                    "how": f"concorde task show {task}",
                    "ok": found_it,
                }
            )
            if not found_it:
                problems.append(
                    f"{session.name}'s concorde task show {task} did not list run {run_id} "
                    f"with the status {status}"
                )
    return {
        "phase": name,
        "owner": owner.name if owner else None,
        "run": run_id,
        "status": status,
        "verdicts": verdicts,
        "seen": seen,
        "problems": problems,
    }


def owners(
    project: Path,
    directory: Path | None = None,
    *,
    claude: int = 2,
    pi: int = 2,
    task: str = "t1",
    claude_model: str | None = None,
    pi_model: str | None = None,
    grace: float = GRACE_SECONDS,
    limit: float = LIMIT_SECONDS,
    claude_program: str | None = None,
    pi_program: str | None = None,
) -> dict:
    """Run the owners case in ``project``, keeping every session's events under ``directory``."""
    project = project.resolve()
    if claude < 0 or pi < 0 or claude + pi < 2:
        raise E2EError(
            "invalid_input", "the owners case needs at least two main sessions in all"
        )
    record_path = project / ".concorde/tasks" / task / "task.json"
    try:
        worktree = Path(json.loads(record_path.read_text(encoding="utf-8"))["worktree"])
    except (OSError, ValueError, KeyError) as error:
        raise E2EError(
            "no_task",
            f"{project} has no open task {task} with a worktree ({error}); prepare the project "
            "with a task first",
        ) from error
    if pi and not (project / ".pi/extensions").is_dir():
        raise E2EError(
            "pi_not_installed",
            f"{project} has no Concorde pi extension; prepare it with --pi, or run "
            "install-concorde.py --update --pi on it",
        )
    records = records_of(worktree)
    directory = directory or project / ".concorde/runs/e2e/owners" / _stamp()
    directory.mkdir(parents=True, exist_ok=True)
    sessions: list[LiveSession] = []
    phases: list[dict] = []
    problems: list[str] = []
    try:
        for number in range(1, claude + 1):
            sessions.append(
                LiveSession(
                    f"claude-{number}",
                    "claude",
                    project,
                    directory,
                    model=claude_model,
                    program=claude_program,
                )
            )
        for number in range(1, pi + 1):
            sessions.append(
                LiveSession(
                    f"pi-{number}",
                    "pi",
                    project,
                    directory,
                    model=pi_model,
                    program=pi_program,
                )
            )
        for session in sessions:
            asked = session.send(READY)
            session.wait_settled(asked, limit)
            refused = session.client == "pi" and session.refusal(asked)
            if refused:
                raise E2EError(
                    "session_failed",
                    f"{session.name} refused its first prompt: {refused}",
                    stderr=session.stderr(),
                )
        options = {
            "project": project,
            "worktree": worktree,
            "records": records,
            "task": task,
            "directory": directory,
            "grace": grace,
            "limit": limit,
        }
        phases.append(phase("unowned", sessions, None, **options))
        for client in ("pi", "claude"):
            owner = next((item for item in sessions if item.client == client), None)
            if owner is not None:
                phases.append(phase(f"owned-by-{client}", sessions, owner, **options))
    finally:
        for session in sessions:
            session.close()
    for item in phases:
        problems += [f"{item['phase']}: {text}" for text in item["problems"]]
    value = {
        "project": str(project),
        "task": task,
        "directory": str(directory),
        "status": "passed" if not problems else "failed",
        "sessions": [session.record() for session in sessions],
        "phases": phases,
        "problems": problems,
    }
    (directory / "owners.json").write_text(json.dumps(value, indent=2) + "\n")
    return value
