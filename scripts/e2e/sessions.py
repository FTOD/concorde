"""Headless sessions: drive a real Claude Code or pi main session in a project without a person.

A headless ``claude -p`` differs from the interactive session a developer uses in ways that are
testing conditions, not what users get, so they are handled here and never in the main-session
guidance:

- nobody answers a question, and the project may be untrusted, so the tools the session needs are
  granted on the command line;
- a task session's SendMessage report would find no receiver, since the process of a round ends
  with its turn, so a Claude Code main session works its tasks itself inside their task worktrees,
  a test-only exception to the rule that the main agent never works inside a task worktree, and is
  granted EnterWorktree and ExitWorktree for it (a pi main session still delegates);
- a command left running in the background is stopped when the turn ends, and nothing wakes the
  session when a run ends: the session is told so in an appended system prompt, and when a round
  ends with an Operation run still running or stopped by the turn's end, or with a round of a pi
  task session still running, the tool waits for it and resumes the same session with the
  notification an interactive session would have received;
- resuming replays the stopped background command as an empty turn, whose result is not the
  session's answer.

A pi session is ``pi -p --mode json --approve`` with a session identity the tool chooses, so
every round continues the same session file; the prompt goes on standard input, and pi's own
note says that its process ends with the turn while a run started with ``concorde_run`` or a
task-session round started with ``concorde_task_session`` goes on.

Each round's output (``stream-json`` for Claude Code, pi's JSON events for pi) is kept under the
session directory, with ``session.json`` summarizing the rounds, the wakes and the end.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from common import E2EError

# Keeps a background workflow of `claude -p` alive past ten idle minutes.
WAIT_VARIABLE = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"
# The tools a main agent uses, granted on the command line because an untrusted project's allow
# rules are ignored. The worktree tools serve the test-only exception the note states: a headless
# Claude Code main session works its tasks itself inside their task worktrees.
MAIN_AGENT_TOOLS = (
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Skill",
    "TodoWrite",
    "EnterWorktree",
    "ExitWorktree",
)
NOTE = (
    "This session is run headless by Concorde's end-to-end tool. Nobody answers questions during "
    "it. A command you leave running in the background is stopped when your turn ends, and "
    "nothing wakes you when it ends, so run Concorde commands in the foreground. When a round "
    "ends while an Operation run is still running, the tool waits for it and resumes this session "
    "with the notification you would otherwise have received. For the same reason a task session "
    "could not report to you: your process ends with each turn, so its SendMessage report would "
    "find no receiver. Follow the test procedure below instead of starting task sessions."
)
# The procedure of a headless Claude Code main session, a session of the tests alone: it works its
# tasks itself, since a task session's report would have no receiver. Appended after NOTE to a
# main session's rounds only; a headless workflow run already works as a task session.
MAIN_PROCEDURE = """Test procedure of this headless main session.

This session exists only in Concorde's end-to-end tests. For this test session only, this \
procedure overrides the concorde skill's rule to hand every task to a task session: you carry \
each task out yourself, as follows.

1. Open the task from the primary worktree with `concorde task open`, as the skill says, and \
record its brief in its decision log.
2. Enter the task worktree with EnterWorktree, giving its path.
3. Work the task there with that worktree's own `concorde`, running every Concorde command in \
the foreground: change Specs and code directly or through Operations, and commit each verified \
step on the task branch.
4. Validate and deliver the task there with `concorde task-validation` and `concorde delivery`.
5. Leave the task worktree with ExitWorktree with action "keep", so its worktree and branch stay.
6. Merge the task from the primary worktree with `concorde task merge <task>`.

Nobody answers questions during this session. Wherever you would ask the developer or escalate a \
decision, decide it yourself and record it in the task's decision log with your reason and the \
options you weighed, and give it in your final answer."""
# pi has no permission prompts to answer, and a detached `concorde_run` or task-session round
# outlives the process.
PI_NOTE = (
    "This session is run headless by Concorde's end-to-end tool. Nobody answers questions during "
    "it. Your process ends when your turn ends; an Operation you started with concorde_run and a "
    "task-session round you started with concorde_task_session keep running, and when one ends "
    "the tool resumes this session with its result or outcome, as the run view would have woken "
    "you. So end your turn when you would otherwise wait for a run or a round."
)
CLIENTS = ("claude", "pi")
# A cancelled run whose result was written this close to the end of a round was stopped by that
# end, not by the session.
TURN_END_SECONDS = 30.0
ROUNDS = 4
WAIT_SECONDS = 3600.0


def stamp(moment: float | None = None) -> str:
    """The UTC time format of Concorde's progress files, which compares as text."""
    return datetime.fromtimestamp(
        time.time() if moment is None else moment, UTC
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def command(
    prompt: str,
    tools: tuple[str, ...] | list[str] = MAIN_AGENT_TOOLS,
    *,
    resume: str | None = None,
    note: str | None = NOTE,
    claude: str = "claude",
    procedure: str | None = MAIN_PROCEDURE,
) -> list[str]:
    """The ``claude -p`` argument list of one round; a main session's rounds carry the test
    procedure after the note, a workflow run's (``procedure`` None) only the note."""
    appended = "\n\n".join(part for part in (note, procedure) if part)
    return [
        claude,
        "-p",
        prompt,
        *(["--resume", resume] if resume else []),
        *(["--append-system-prompt", appended] if appended else []),
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowedTools",
        *tools,
    ]


def pi_command(
    session_id: str,
    session_dir: Path,
    *,
    note: str | None = PI_NOTE,
    pi: str = "pi",
    model: str | None = None,
) -> list[str]:
    """The ``pi -p`` argument list of one round; the prompt goes on standard input. The same
    identity and directory make every round continue one session file."""
    return [
        pi,
        "-p",
        "--mode",
        "json",
        "--approve",
        "--session-dir",
        str(session_dir),
        "--session-id",
        session_id,
        *(["--append-system-prompt", note] if note else []),
        *(["--model", model] if model else []),
    ]


def environment(extra: dict | None = None) -> dict:
    return {**os.environ, WAIT_VARIABLE: "0", **(extra or {})}


def read_log(path: Path) -> dict:
    """One round's log: its session, every tool call and text, and the round's own result."""
    session = None
    actions: list[dict] = []
    texts: list[str] = []
    result = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        session = event.get("session_id") or session
        if event.get("type") == "assistant":
            for block in (event.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    data = block.get("input") or {}
                    target = (
                        data.get("command")
                        or data.get("file_path")
                        or data.get("path")
                        or data.get("skill")
                        or ""
                    )
                    actions.append(
                        {"tool": block.get("name"), "target": str(target)[:500]}
                    )
                elif block.get("type") == "text" and block.get("text", "").strip():
                    texts.append(block["text"])
        elif event.get("type") == "result":
            # A resume first replays a stopped background command as a turn of its own, with no
            # model turn; the round's answer is the last result that has one.
            if event.get("num_turns") or result is None:
                result = event
    return {
        "session_id": session,
        "actions": actions,
        "texts": texts,
        "result": None
        if result is None
        else {
            "subtype": result.get("subtype"),
            "turns": result.get("num_turns"),
            "cost_usd": result.get("total_cost_usd"),
            "text": result.get("result"),
        },
    }


def read_pi_log(path: Path) -> dict:
    """One pi round's JSON events: its session, every tool call and text, and the round's result,
    its turns, its cost and its final text."""
    session = None
    actions: list[dict] = []
    texts: list[str] = []
    turns = 0
    cost = 0.0
    stop = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "session":
            session = event.get("id") or session
        elif kind == "tool_execution_start":
            data = event.get("args") or {}
            target = (
                data.get("command") or data.get("path") or data.get("file_path") or ""
            )
            if not target and data:
                target = json.dumps(data)
            actions.append({"tool": event.get("toolName"), "target": str(target)[:500]})
        elif kind == "turn_end":
            turns += 1
        elif kind == "message_end":
            message = event.get("message") or {}
            if message.get("role") != "assistant":
                continue
            stop = message.get("stopReason") or stop
            spent = ((message.get("usage") or {}).get("cost") or {}).get("total")
            if isinstance(spent, (int, float)):
                cost += spent
            text = "\n".join(
                block.get("text", "")
                for block in message.get("content") or []
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
            if text:
                texts.append(text)
    return {
        "session_id": session,
        "actions": actions,
        "texts": texts,
        "result": None
        if not turns and not texts
        else {
            "subtype": stop,
            "turns": turns,
            "cost_usd": round(cost, 6),
            "text": texts[-1] if texts else None,
        },
    }


def _alive(project: Path, run_id: str) -> bool:
    """Whether the runner of ``run_id`` still holds its run lock ``locks/runs/<run>.lock``, a
    ``flock`` it removes as it exits; its recorded process identifier is only meaningful in the
    PID namespace it ran in."""
    try:
        descriptor = os.open(
            records_of(project) / "locks/runs" / f"{run_id}.lock", os.O_RDONLY
        )
    except OSError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    except OSError:
        return False
    finally:
        os.close(descriptor)
    return False


def records_of(project: Path) -> Path:
    """The ``.concorde`` of ``project`` that holds its tasks, unbound runs and locks: the one its
    workspace binding names, or its own when it is unbound."""
    try:
        binding = json.loads(
            (project / ".concorde/workspace.json").read_text(encoding="utf-8")
        )
        return Path(binding["concorde"])
    except (OSError, ValueError, KeyError, TypeError):
        return project / ".concorde"


def run_folders(project: Path) -> list[Path]:
    """The folder of every run of the project's current tasks, started directly or by a
    workflow step, and of its unbound runs (Tracing's layout)."""
    base = records_of(project)
    found: list[Path] = []
    for task in sorted((base / "tasks").glob("*")):
        workspace = task / "workspace"
        found += sorted(
            item for item in (workspace / "runs").glob("r-*") if item.is_dir()
        )
        found += sorted(
            item
            for item in (workspace / "workflow/steps").glob("*/run")
            if item.is_dir()
        )
    found += sorted(item for item in (base / "unbound").glob("r-*") if item.is_dir())
    return found


def run_folder(project: Path, run_id: str) -> Path:
    for folder in run_folders(project):
        if folder.name == run_id or (_state(folder) or {}).get("run_id") == run_id:
            return folder
    return records_of(project) / "unbound" / run_id


def _state(directory: Path) -> dict | None:
    """The progress file of an Operation or execution command run; None for a worker's."""
    try:
        value = json.loads((directory / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if isinstance(value, dict) and value.get("kind") in ("operation", "command"):
        return value
    return None


def _result(directory: Path) -> dict | None:
    try:
        return json.loads((directory / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _pid_alive(pid) -> bool:
    """Whether the process ``pid`` runs; one that ended but was not yet reaped does not."""
    if not isinstance(pid, int) or pid <= 0:
        return False
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


def round_key(task: str, session: str, number: int) -> str:
    return f"{task}:{session}:{number}"


def _json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _round_entry(node: dict) -> dict:
    data = (node.get("content") or {}).get("data") or {}
    return {
        "round": data.get("round"),
        "status": data.get("outcome"),
        "supervisor_pid": data.get("supervisor_pid"),
        "started_at": node.get("started_at"),
        "report": data.get("report"),
        "error": node.get("error"),
    }


def _pi_rounds(project: Path) -> list[tuple[str, str, str | None, dict]]:
    """Every round of every pi task session of the current tasks: (task, session, the session's
    owner ``main``, round)."""
    found = []
    for session in sorted((records_of(project) / "tasks").glob("*/sessions/*")):
        node = _json(session / "trace.json") or {}
        data = (node.get("content") or {}).get("data") or {}
        if data.get("program") != "pi":
            continue
        for folder in sorted(
            (session / "rounds").glob("*"),
            key=lambda p: int(p.name) if p.name.isdigit() else 0,
        ):
            round_node = _json(folder / "trace.json")
            if round_node is not None:
                found.append(
                    (
                        session.parent.parent.name,
                        session.name,
                        data.get("main"),
                        _round_entry(round_node),
                    )
                )
    return found


def _recorded_round(project: Path, item: dict) -> dict | None:
    """The round ``item`` names, as its node now records it."""
    node = _json(
        records_of(project)
        / "tasks"
        / item["task"]
        / "sessions"
        / item["session"]
        / "rounds"
        / str(item["number"])
        / "trace.json"
    )
    return _round_entry(node) if node is not None else None


def unsettled_rounds(
    project: Path, since: str, known: set[str] = frozenset(), owner: str | None = None
) -> list[dict]:
    """The rounds of pi task sessions begun since ``since`` that are still running: their task
    round's node holds them ``running`` and their supervisor lives. ``known`` rounds were reported
    already. With ``owner``, only the rounds of task sessions started for that main session,
    whose session node names it as their ``main``, since only the owner is woken."""
    found = []
    for task, session, main, entry in _pi_rounds(project):
        if owner is not None and main != owner:
            continue
        key = round_key(task, session, entry.get("round"))
        if key in known or str(entry.get("started_at") or "") < since:
            continue
        if entry.get("status") == "running" and _pid_alive(entry.get("supervisor_pid")):
            found.append(
                {
                    "round": key,
                    "task": task,
                    "session": session,
                    "number": entry.get("round"),
                    "why": "running",
                }
            )
    return found


def unsettled_runs(
    project: Path,
    since: str,
    round_end: float,
    known: set[str] = frozenset(),
    owned: set[str] | None = None,
) -> list[dict]:
    """The runs started since ``since`` that the round left unsettled: still running, or
    cancelled by the end of the round. ``known`` runs were reported already. With ``owned``,
    only those runs, the ones the session owns."""
    found = []
    for directory in run_folders(project):
        state = _state(directory)
        if state is None:
            continue
        run_id = state.get("run_id") or directory.name
        if owned is not None and run_id not in owned:
            continue
        if run_id in known or str(state.get("started_at") or "") < since:
            continue
        if state.get("phase") != "finished":
            if _alive(project, run_id):
                found.append({"run": run_id, "why": "running"})
            continue
        result = _result(directory)
        code = ((result or {}).get("error") or {}).get("code")
        written = (directory / "result.json").stat().st_mtime if result else 0.0
        if code == "cancelled" and abs(written - round_end) <= TURN_END_SECONDS:
            found.append({"run": run_id, "why": "stopped_with_turn"})
    return found


def pi_owned_runs(session_dir: Path, session_id: str) -> set[str]:
    """The runs a pi session owns: those its run view recorded as started by its
    ``concorde_run``, custom ``concorde-owned-run`` entries of its session file."""
    owned = set()
    for path in session_dir.rglob(f"*{session_id}*.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(entry, dict)
                and entry.get("type") == "custom"
                and entry.get("customType") == "concorde-owned-run"
                and isinstance((entry.get("data") or {}).get("id"), str)
            ):
                owned.add(entry["data"]["id"])
    return owned


def _ended(project: Path, item: dict) -> bool:
    """Whether a running run has finished or lost its runner, or a running task-session round
    has been recorded or lost its supervisor."""
    if "round" in item:
        entry = _recorded_round(project, item) or {}
        return entry.get("status") != "running" or not _pid_alive(
            entry.get("supervisor_pid")
        )
    directory = run_folder(project, item["run"])
    state = _state(directory) or {}
    return state.get("phase") == "finished" or not _alive(project, item["run"])


def _progress_of(project: Path, item: dict) -> Path:
    if "round" in item:
        return (
            records_of(project)
            / "tasks"
            / item["task"]
            / "sessions"
            / item["session"]
            / "status.json"
        )
    return run_folder(project, item["run"]) / "status.json"


def wait_for(
    project: Path, runs: list[dict], limit: float = WAIT_SECONDS, poll: float = 2.0
) -> None:
    """Wait until every running run has finished or its host has gone, and every running
    task-session round has ended or its supervisor has gone."""
    deadline = time.monotonic() + limit
    for item in runs:
        while item["why"] == "running" and not _ended(project, item):
            if time.monotonic() > deadline:
                what = (
                    f"round {item['number']} of the task session of {item['task']}"
                    if "round" in item
                    else f"run {item['run']}"
                )
                raise E2EError(
                    "wait_exceeded",
                    f"{what} of {project} was still running after {limit:.0f}s",
                    progress=str(_progress_of(project, item)),
                )
            time.sleep(poll)


def _chain_text(link: dict, depth: int = 0) -> list[str]:
    """An error link and its causes as indented lines, as the run view shows them."""
    unhandled = link.get("unhandled") or {}
    lines = [
        f"{'  ' * depth}{link.get('actor')}: {link.get('code')}: {link.get('detail')}"
        + (f" (not handled: {unhandled.get('explanation')})" if unhandled else "")
    ]
    lines += [
        f"{'  ' * (depth + 1)}option: {option}" for option in link.get("options") or []
    ]
    for cause in link.get("causes") or []:
        lines += _chain_text(cause, depth + 1)
    return lines


def round_text(project: Path, item: dict) -> str:
    """What the run view tells the main agent when a task-session round ends: the outcome its
    round's node holds."""
    head = f"Task session of {item['task']}, round {item['number']}"
    entry = _recorded_round(project, item)
    record = (
        records_of(project)
        / "tasks"
        / item["task"]
        / "sessions"
        / item["session"]
        / "rounds"
        / str(item["number"])
    )
    if not entry or entry.get("status") == "running":
        return (
            f"{head} ended without recording its outcome (its supervisor is gone). Run "
            f"concorde task show {item['task']}; the next concorde task session command "
            "records the round as failed with its logs."
        )
    report = entry.get("report") or {}
    lines = [f"{head} ended {entry.get('status')}."]
    if report.get("summary"):
        lines.append(f"Summary: {report['summary']}")
    for key, title in (("decisions", "Decisions it made"), ("open", "Still open")):
        if report.get(key):
            lines.append(f"{title}:\n" + "\n".join(f"- {text}" for text in report[key]))
    if entry.get("status") == "delivered":
        lines.append(
            f"Delivery commit: {report.get('commit')}. Merge it with concorde task merge "
            f"{item['task']} when the work is complete."
        )
    if entry.get("status") == "escalated":
        numbers = ", ".join(str(number) for number in report.get("escalations") or [])
        lines.append(
            f"Escalations: {numbers}; read their chains with concorde task show "
            f"{item['task']}. Answer with concorde_task_session (answer), or escalate to the "
            "developer with your own link on top."
        )
    if entry.get("status") == "failed" and entry.get("error"):
        lines.append("Error chain:\n" + "\n".join(_chain_text(entry["error"])))
    if entry.get("status") == "stopped":
        lines.append("The round was stopped.")
    lines.append(f"Round node: {record}")
    return "\n".join(lines)


def wake_message(project: Path, runs: list[dict]) -> str:
    """The notification an interactive session would have received for each run and each
    task-session round."""
    lines = [
        "Notification from the end-to-end tool, standing in for the ones an interactive "
        "session receives:"
    ]
    for item in runs:
        if "round" in item:
            lines.append("- " + round_text(project, item).replace("\n", "\n  "))
            continue
        directory = run_folder(project, item["run"])
        result = _result(directory) or {}
        state = _state(directory) or {}
        ended = (
            f"ended {result.get('status')}: {result.get('summary')}"
            if result
            else "ended without writing a result (its host is gone)"
        )
        cause = (
            " It was stopped because your turn ended while it ran in the background."
            if item["why"] == "stopped_with_turn"
            else ""
        )
        lines.append(
            f"- {state.get('kind') or 'Operation'} run {item['run']} ({state.get('name')}, "
            f"workspace {state.get('workspace') or 'none'}) {ended} Result: "
            f"{directory / 'result.json'}.{cause}"
        )
    return "\n".join(lines)


def start(
    project: Path,
    prompt: str,
    directory: Path,
    *,
    tools: tuple[str, ...] | list[str] = MAIN_AGENT_TOOLS,
    rounds: int = ROUNDS,
    extra_environment: dict | None = None,
    note: str | None = None,
    claude: str = "claude",
    wait_limit: float = WAIT_SECONDS,
    poll: float = 2.0,
    client: str = "claude",
    pi: str = "pi",
    model: str | None = None,
    procedure: str | None = MAIN_PROCEDURE,
) -> dict:
    """Run a headless session in ``project`` until it ends with nothing left to wake it for."""
    if client not in CLIENTS:
        raise E2EError(
            "unknown_client",
            f"a headless session runs on {' or '.join(CLIENTS)}, not {client!r}",
        )
    directory.mkdir(parents=True, exist_ok=True)
    began = stamp()
    # A pi session is named by the tool, so its first round already continues nothing and every
    # later one continues it; Claude Code names its session in its first round's output.
    session = str(uuid.uuid4()) if client == "pi" else None
    pi_sessions = directory / "pi"
    message = prompt
    known: set[str] = set()
    history = []
    end = "rounds_exhausted"

    def save(ended: str, **extra) -> dict:
        """Write ``session.json`` for the session as it ended."""
        final = next(
            (item["result"] for item in reversed(history) if item["result"]), None
        )
        if client == "pi":
            # pi reports each round's own spending; Claude Code's result carries the session's
            # total.
            spent = [(item["result"] or {}).get("cost_usd") or 0.0 for item in history]
            cost = round(sum(spent), 6)
        else:
            cost = (final or {}).get("cost_usd")
        record = {
            "project": str(project),
            "client": client,
            "session_id": session,
            "prompt": prompt,
            "started_at": began,
            "ended_at": stamp(),
            "end": ended,
            **extra,
            "rounds": history,
            "cost_usd": cost,
            "final": (final or {}).get("text"),
        }
        (directory / "session.json").write_text(json.dumps(record, indent=2) + "\n")
        return record

    for number in range(1, rounds + 1):
        log = directory / f"round-{number}.jsonl"
        errors = directory / f"round-{number}.err"
        if client == "pi":
            argv = pi_command(
                session,
                pi_sessions,
                note=PI_NOTE if note is None else note,
                pi=pi,
                model=model,
            )
            given = message
        else:
            argv = command(
                message,
                tools,
                resume=session,
                note=NOTE if note is None else note,
                claude=claude,
                procedure=procedure,
            )
            given = None
        with log.open("w") as out, errors.open("w") as err:
            completed = subprocess.run(
                argv,
                cwd=project,
                env=environment(extra_environment),
                input=given,
                stdout=out,
                stderr=err,
                text=True,
                check=False,
            )
        round_end = time.time()
        summary = read_pi_log(log) if client == "pi" else read_log(log)
        session = summary["session_id"] or session
        entry = {
            "round": number,
            "log": str(log),
            "exit": completed.returncode,
            "result": summary["result"],
            "actions": len(summary["actions"]),
            "woke_for": [],
        }
        history.append(entry)
        if completed.returncode != 0:
            end = "exited"
            entry["stderr"] = errors.read_text(errors="replace")[-3000:]
            break
        if session is None:
            end = "no_session"
            break
        # A pi session is woken only for what it owns, as its run view would: the runs its
        # concorde_run started and the rounds of the task sessions started for it. A Claude Code
        # round's runs are its own background commands, which the round's end stopped.
        if client == "pi":
            runs = unsettled_runs(
                project, began, round_end, known, pi_owned_runs(pi_sessions, session)
            ) + unsettled_rounds(project, began, known, session)
        else:
            runs = unsettled_runs(project, began, round_end, known) + unsettled_rounds(
                project, began, known
            )
        if not runs:
            end = "idle"
            break
        try:
            wait_for(project, runs, wait_limit, poll)
        except E2EError as error:
            # The session is kept like any other before the failure goes up, naming the run
            # that outlived the wait.
            save(error.code, progress=error.evidence.get("progress"))
            error.evidence["session"] = str(directory / "session.json")
            raise
        entry["woke_for"] = [item.get("run") or item["round"] for item in runs]
        known.update(entry["woke_for"])
        message = wake_message(project, runs)
    return save(end)


def show(directory: Path) -> dict:
    """A session's record with every round's tool calls and texts, read from its logs."""
    try:
        record = json.loads((directory / "session.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise E2EError(
            "no_session", f"{directory} holds no readable session.json ({error})"
        ) from error
    reader = read_pi_log if record.get("client") == "pi" else read_log
    return {
        **record,
        "rounds": [{**item, **reader(Path(item["log"]))} for item in record["rounds"]],
    }
