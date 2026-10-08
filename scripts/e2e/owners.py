"""The owners case: several live main sessions on one test project, and only a run's owner woken.

Concorde promises that every run has at most one owner main session, the one whose own tool
started it, and that only the owner is woken when the run ends, while every other main session
may see the run's state and is never woken by it. This case checks that promise with real
sessions: it keeps Claude Code main sessions running at once in the test project's primary
worktree (two by default), each a live session (``live.py``) whose wakes are its program's own,
and plays two phases on the project's open task:

1. **unowned**: the case itself starts ``concorde task-validation`` in the task worktree, a run of
   nobody's tool, which must wake no session;
2. **owned by Claude Code**: the first session starts it in background Bash.

Each run is held back by the case, which holds the task's workspace lock until the run is in the
run store, waiting in its lobby, so that the run outlives its launch and its end is a wake rather
than the launching tool's own answer. The case holds the lock at most ``limit`` seconds from the
launch, and the run waits for it twice as long (``--wait``), so its wait never expires while the
case holds the lock. Once the run has written its result, the case observes for a bounded window:
until the owner has been woken and ended its turn, but at most ``wake`` seconds, and then a grace
period more. The window ends whether or not the owner was woken, so an owner never woken is a
problem of the verdict, not an error. In it the owner must have been woken and every other session
must not have begun a turn or received a notification. Then each other session, into which nothing
is pushed, is asked to run ``concorde task show <task>`` and must find the run with its status.
"""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import subprocess
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from common import E2EError
from live import LiveSession
from sessions import records_of

GRACE_SECONDS = 20.0
WAKE_SECONDS = 180.0
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


def queue_wait(limit: float) -> int:
    """The ``--wait`` of a run the case launches: twice the case's ``limit``, which bounds how long
    the case holds the workspace lock after the launch, so the run's wait outlasts every hold."""
    return int(2 * limit)


def _run_folders(records: Path) -> list[Path]:
    """Every run folder under the ``.concorde`` ``records``: the current tasks' workspace
    folders, their workflow steps, the unbound runs, and the lobby, where a bound run waits for
    its workspace lock (Tracing's layout)."""
    return [
        *sorted(records.glob("tasks/*/workspace/runs/r-*")),
        *sorted(records.glob("tasks/*/workspace/workflow/steps/*/run")),
        *sorted(records.glob("unbound/r-*")),
        *sorted(records.glob("lobby/r-*")),
    ]


def _run_id(directory: Path) -> str | None:
    try:
        state = json.loads((directory / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return state.get("run_id") or directory.name


def parent_of(pid: int) -> int | None:
    """The parent of the process ``pid`` in this PID namespace, from Linux's ``/proc``; None when
    the process is gone or cannot be read."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    # The command name, in parentheses, may hold spaces: the fields follow its last ``)``.
    fields = stat[stat.rfind(")") + 2 :].split()
    try:
        return int(fields[1])
    except (IndexError, ValueError):
        return None


def descends(pid: object, ancestor: int) -> bool:
    """Whether the process ``pid`` is ``ancestor`` or one of its descendants."""
    if not isinstance(pid, int) or isinstance(pid, bool):
        return False
    seen = set()
    while pid and pid not in seen:
        if pid == ancestor:
            return True
        seen.add(pid)
        pid = parent_of(pid)
    return False


def new_run(
    records: Path, workspace: str, known: set[str], launcher: int
) -> str | None:
    """The run of ``workspace`` in the run store that ``known`` does not name and whose runner,
    the progress file's ``host_pid``, descends from the process ``launcher``, if any: the run the
    case launched, never a competing one."""
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
            and descends(state.get("host_pid"), launcher)
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


def refused_busy(result: dict) -> bool:
    """Whether ``result`` is Execution's refusal of a run whose wait for the workspace lock
    expired."""
    return "workspace_busy" in [
        item.get("ref") for item in result.get("host_evidence") or []
    ]


def until(condition, limit: float, what: str, poll: float = 0.5, **evidence) -> None:
    deadline = time.monotonic() + limit
    while not condition():
        if time.monotonic() > deadline:
            raise E2EError("live_timeout", f"{what} within {limit:.0f}s", **evidence)
        time.sleep(poll)


def observe(condition, limit: float, poll: float = 0.5) -> bool:
    """Whether ``condition`` held within ``limit`` seconds: a window of the case that ends at its
    deadline without an error, unlike ``until``."""
    deadline = time.monotonic() + limit
    while not condition():
        if time.monotonic() > deadline:
            return False
        time.sleep(poll)
    return True


def owner_prompt(worktree: Path, limit: float) -> str:
    wait = str(queue_wait(limit))
    return (
        "Run this command with the Bash tool in the background (run_in_background true), then "
        "end your turn at once, replying only STARTED:\n"
        f"cd {shlex.quote(str(worktree))} && .concorde/bin/concorde task-validation "
        f"--wait {wait}\n"
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


def turn_end(session: LiveSession, moment: float) -> float:
    """When the first turn that ended since ``moment`` ended: the time its ``result`` event was
    read."""
    return min(
        at
        for at, event in list(session.events)
        if at >= moment and event.get("type") == "result"
    )


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
                event.get("subtype") for event in session.notifications(moment, end)
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
    wake: float,
    limit: float,
) -> dict:
    """One phase: a run held back until it is in the run store, released, ended, observed for a
    bounded window, judged, and then looked up by every session that does not own it."""
    known = known_runs(records)
    with workspace_held(records, task, limit):
        started = time.time()
        # The owner's launching turn and the run's appearance share one deadline, so the case
        # holds the lock at most ``limit`` seconds after the launch.
        hold = time.monotonic() + limit
        if owner is None:
            command = [
                str(worktree / ".concorde/bin/concorde"),
                "task-validation",
                "--wait",
                str(queue_wait(limit)),
            ]
            log = (directory / f"{name}-run.log").open("w")
            try:
                launcher = subprocess.Popen(
                    command,
                    cwd=worktree,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                ).pid
            except OSError as error:
                raise E2EError(
                    "command_failed",
                    f"`{' '.join(command)}` in {worktree} could not be started: {error}",
                ) from error
            finally:
                log.close()
            baseline = started
        else:
            prompted = owner.send(owner_prompt(worktree, limit))
            owner.wait_settled(prompted, max(hold - time.monotonic(), 0.0))
            # The judged time starts when the launching turn ended, as its result event was
            # read, not when the case noticed it.
            baseline = turn_end(owner, prompted)
            launcher = owner.process.pid
        # An owner that ended leaves its run without the launcher it descends from: that stops
        # the case as a session that ended, never as a run that did not appear.
        until(
            lambda: (
                new_run(records, task, known, launcher) is not None
                or (
                    owner is not None
                    and owner.require_running(f"before its run of the phase {name}")
                )
            ),
            max(hold - time.monotonic(), 0.0),
            f"no run of {task} launched by process {launcher} appeared in the run store of "
            f"{records} for the phase {name}; a launcher whose commands run in another PID "
            "namespace, such as a sandbox's, is never found",
            log=str(owner.log) if owner else None,
        )
        run_id = new_run(records, task, known, launcher)
    released = time.time()
    # The result is read once and judged as read: a later read may miss it while the run
    # rewrites its progress file, which names its folder.
    written = {}

    def ended() -> bool:
        written["result"] = result_of(records, run_id)
        return written["result"] is not None

    # The run may still queue for the lock after the release, for at most its wait: waiting that
    # long, the case sees a refusal for a busy workspace rather than its own deadline.
    until(
        ended,
        queue_wait(limit),
        f"run {run_id} wrote no result",
        progress=str(run_folder(records, run_id) / "status.json"),
    )
    result = written["result"]
    if refused_busy(result):
        # The run did no work: another run took the lock after the case released it and held it
        # past the run's wait, so there is no run end to judge.
        raise E2EError(
            "workspace_busy",
            f"run {run_id} of the phase {name} was refused with workspace_busy: another run held "
            f"the workspace lock of {task} after the case released it",
            result=str(run_folder(records, run_id) / "result.json"),
        )
    if owner is not None:
        # An owner not woken by the deadline is judged below, as a problem of the verdict; an
        # owner that ended before it was woken stops the case.
        observe(
            lambda: (
                (owner.woken(released) and owner.settled(released))
                or owner.require_running(f"before the run of the phase {name} woke it")
            ),
            wake,
        )
    time.sleep(grace)
    end = time.time()
    # A session that ended can no longer be woken: that is no verdict but a failure of the case.
    for session in sessions:
        session.require_running(f"while the case observed the phase {name}")
    verdicts, problems = judge(sessions, owner, baseline, end)
    status = result.get("status")
    seen = []
    for session in sessions:
        if session is owner:
            continue
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
    task: str = "t1",
    claude_model: str | None = None,
    grace: float = GRACE_SECONDS,
    wake: float = WAKE_SECONDS,
    limit: float = LIMIT_SECONDS,
    claude_program: str | None = None,
) -> dict:
    """Run the owners case in ``project``, keeping every session's events under ``directory``."""
    project = project.resolve()
    if claude < 2:
        raise E2EError(
            "invalid_input", "the owners case needs at least two main sessions"
        )
    record_path = project / ".concorde/tasks" / task / "task.json"
    try:
        worktree = Path(json.loads(record_path.read_text(encoding="utf-8"))["worktree"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise E2EError(
            "no_task",
            f"{project} has no open task {task} with a worktree ({error}); prepare the project "
            "with a task first",
        ) from error
    if not worktree.is_dir():
        raise E2EError(
            "no_task",
            f"the worktree {worktree} of the task {task} of {project} does not exist; prepare "
            "the project with a task first",
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
                    project,
                    directory,
                    model=claude_model,
                    program=claude_program,
                )
            )
        for session in sessions:
            asked = session.send(READY)
            session.wait_settled(asked, limit)
        options = {
            "project": project,
            "worktree": worktree,
            "records": records,
            "task": task,
            "directory": directory,
            "grace": grace,
            "wake": wake,
            "limit": limit,
        }
        phases.append(phase("unowned", sessions, None, **options))
        phases.append(phase("owned-by-claude", sessions, sessions[0], **options))
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
