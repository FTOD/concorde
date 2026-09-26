"""Headless sessions: drive a real Claude Code or pi main session in a project without a person.

A headless ``claude -p`` differs from the interactive session a developer uses in ways that are
testing conditions, not what users get, so they are handled here and never in the main-session
guidance:

- nobody answers a question, and the project may be untrusted, so the tools the session needs are
  granted on the command line;
- a command left running in the background is stopped when the turn ends, and nothing wakes the
  session when a run ends: the session is told so in an appended system prompt, and when a round
  ends with an Operation run still running or stopped by the turn's end, the tool waits for it
  and resumes the same session with the notification an interactive session would have received;
- resuming replays the stopped background command as an empty turn, whose result is not the
  session's answer.

A pi session is ``pi -p --mode json --approve`` with a session identity the tool chooses, so
every round continues the same session file; the prompt goes on standard input, and pi's own
note says that its process ends with the turn while a run started with ``concorde_run`` goes on.

Each round's output (``stream-json`` for Claude Code, pi's JSON events for pi) is kept under the
session directory, with ``session.json`` summarizing the rounds, the wakes and the end.
"""

from __future__ import annotations

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
# rules are ignored.
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
    "with the notification you would otherwise have received."
)
# pi has no permission prompts to answer, and a detached `concorde_run` outlives the process.
PI_NOTE = (
    "This session is run headless by Concorde's end-to-end tool. Nobody answers questions during "
    "it. Your process ends when your turn ends; an Operation you started with concorde_run keeps "
    "running, and when it ends the tool resumes this session with its result, as the run view "
    "would have woken you. So end your turn when you would otherwise wait for a run."
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
) -> list[str]:
    """The ``claude -p`` argument list of one round."""
    return [
        claude,
        "-p",
        prompt,
        *(["--resume", resume] if resume else []),
        *(["--append-system-prompt", note] if note else []),
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


def _alive(pid: int) -> bool:
    if pid < 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        state = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return True
    return state.rsplit(")", 1)[-1].split()[0] != "Z"


def _state(directory: Path) -> dict | None:
    try:
        value = json.loads((directory / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return (
        value if isinstance(value, dict) and value.get("kind") == "operation" else None
    )


def _result(directory: Path) -> dict | None:
    try:
        return json.loads((directory / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def unsettled_runs(
    project: Path, since: str, round_end: float, known: set[str] = frozenset()
) -> list[dict]:
    """The Operation runs started since ``since`` that the round left unsettled: still running,
    or cancelled by the end of the round. ``known`` runs were reported already."""
    found = []
    for directory in sorted((project / ".concorde/runs").glob("r-*")):
        state = _state(directory)
        if state is None or directory.name in known:
            continue
        if str(state.get("started_at") or "") < since:
            continue
        if state.get("phase") != "finished":
            if _alive(int(state.get("host_pid") or 0)):
                found.append({"run": directory.name, "why": "running"})
            continue
        result = _result(directory)
        code = ((result or {}).get("error") or {}).get("code")
        written = (directory / "result.json").stat().st_mtime if result else 0.0
        if code == "cancelled" and abs(written - round_end) <= TURN_END_SECONDS:
            found.append({"run": directory.name, "why": "stopped_with_turn"})
    return found


def wait_for(
    project: Path, runs: list[dict], limit: float = WAIT_SECONDS, poll: float = 2.0
) -> None:
    """Wait until every running run has finished or its host has gone."""
    deadline = time.monotonic() + limit
    for item in runs:
        directory = project / ".concorde/runs" / item["run"]
        while item["why"] == "running":
            state = _state(directory) or {}
            if state.get("phase") == "finished" or not _alive(
                int(state.get("host_pid") or 0)
            ):
                break
            if time.monotonic() > deadline:
                raise E2EError(
                    "wait_exceeded",
                    f"run {item['run']} of {project} was still running after {limit:.0f}s",
                    progress=str(directory / "status.json"),
                )
            time.sleep(poll)


def wake_message(project: Path, runs: list[dict]) -> str:
    """The notification an interactive session would have received for each run."""
    lines = [
        "Notification from the end-to-end tool, standing in for the ones an interactive "
        "session receives:"
    ]
    for item in runs:
        directory = project / ".concorde/runs" / item["run"]
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
            f"- Operation run {item['run']} ({state.get('operation')}, task "
            f"{state.get('task')}) {ended} Result: {directory / 'result.json'}.{cause}"
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
        runs = unsettled_runs(project, began, round_end, known)
        if not runs:
            end = "idle"
            break
        wait_for(project, runs, wait_limit, poll)
        entry["woke_for"] = [item["run"] for item in runs]
        known.update(entry["woke_for"])
        message = wake_message(project, runs)
    final = next((item["result"] for item in reversed(history) if item["result"]), None)
    if client == "pi":
        # pi reports each round's own spending; Claude Code's result carries the session's total.
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
        "end": end,
        "rounds": history,
        "cost_usd": cost,
        "final": (final or {}).get("text"),
    }
    (directory / "session.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


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
