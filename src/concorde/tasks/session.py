"""``concorde task session``: start a task session, a background Claude Code session in one task.

The main agent starts one per task when it splits complex work into several tasks, and stays in
the primary worktree itself. A task session works only inside its task worktree: it may edit
directly or run Operations there with the worktree's own ``concorde``, keeps the task's decision
log, delivers the task, and reports to the main agent, which alone merges and closes tasks.

Its boundary is generated here, in the task's folder under ``.concorde/tasks/<task>/runtime/``,
which the close removes, and guards against mistakes, not a malicious session:

- a PreToolUse hook lets Edit and Write change only the task worktree and its decision log;
- the Bash sandbox lets commands write only the task worktree, the repository's Git directory
  (commits on the task branch), the task's own folder (the workspace folder its binding names,
  where its runs and workflow are traced, and its record and trace, for escalations),
  ``.concorde/locks/`` (the locks those runs take) and the user's package caches; reads and the network stay open, since the
  boundary guards against mistakes, not exfiltration (``allowedDomains`` is ``*``, so no command
  has to name the hosts it reaches);
- the session is given the project MCP server through ``--mcp-config`` (a background session in
  a folder it never trusted would not load the project's ``.mcp.json``), told that it has no
  channel (``CONCORDE_CHANNEL=0``): a live probe on 2026-09-29 (Claude Code 2.1.284) found that a
  ``claude --bg`` session started with ``--dangerously-load-development-channels`` is never woken
  by a channel event, so a task session waits with ``concorde task wait`` in background Bash,
  which ``register_wait`` returns to it; the server runs outside the Bash sandbox, as every MCP
  server does, and may change task records, which the developer accepted: it is a management
  tool, not a boundary;
- nobody answers permission prompts in a background session, so it runs in Claude Code's
  ``auto`` mode, where a classifier approves or refuses each action instead of asking; the hook
  and sandbox stay the boundary, and ``auto`` needs no one-time consent the way
  ``bypassPermissions`` does for a background session. A model without ``auto`` mode falls back
  to asking and stalls, so ``--model`` must name one that has it.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from ..spec.typed_data import type_version
from ..tracing import node as trace
from . import session_hook, store

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
PROMPT = "generated/main-session/task-session.md"
# Package caches outside the worktree that ordinary builds write, such as uv, pip and npm.
CACHES = (".cache", ".npm")
# Every host: the sandbox's proxy otherwise admits only hosts a command names.
ALL_HOSTS = ("*",)
# The project MCP server's name in the session's MCP configuration.
SERVER = "concorde"
STARTED = re.compile(r"backgrounded\s+·\s+(?P<id>[0-9A-Za-z-]+)\s+·")
# The terminal escapes (colour, dimming) Claude Code puts around parts of that line.
ESCAPES = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def session_name(task_id: str) -> str:
    return f"task-{task_id}"


def session_directory(primary: Path, task_id: str) -> Path:
    """The task's ``runtime/``: its task session's boundary configuration, which is no trace."""
    return store.task_folder(primary, task_id) / "runtime"


def writable(primary: Path, record: dict, home: Path | None = None) -> list[str]:
    """Every path the session's Bash commands may write."""
    home = Path(os.path.realpath(home or Path.home()))
    # The repository's Git directory, where commits on the task branch are written.
    common = Path(
        store._git(
            primary, "rev-parse", "--path-format=absolute", "--git-common-dir"
        ).stdout.strip()
    )
    paths = [
        Path(record["worktree"]),
        Path(os.path.realpath(common)),
        store.task_folder(primary, record["id"]),
        store.concorde(primary) / "locks",
        *(home / name for name in CACHES),
    ]
    return sorted({Path(os.path.realpath(path)).as_posix() for path in paths})


def create_writable(paths: list[str]) -> None:
    """Create the writable paths that do not exist yet, such as a first run's ``.concorde/locks``.

    A sandbox makes only existing paths writable, so a directory it lists but that is missing
    would stay read-only for the whole session.
    """
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def hook_source(primary: Path, record: dict) -> str:
    """The write hook with the task's allowed paths embedded."""
    data = {
        "task": record["id"],
        "worktree": Path(os.path.realpath(record["worktree"])).as_posix(),
        "files": [
            Path(
                os.path.realpath(store.decision_log_path(primary, record["id"]))
            ).as_posix()
        ],
    }
    source = Path(session_hook.__file__).read_text(encoding="utf-8")
    return source.replace(
        "ALLOWED: dict = {}", "ALLOWED: dict = " + json.dumps(data, sort_keys=True), 1
    )


def settings(
    primary: Path, record: dict, hook: Path, python: str, home: Path | None = None
) -> dict:
    """The complete ``settings.json`` of one task session."""
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit|NotebookEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{shlex.quote(python)} {shlex.quote(hook.as_posix())}",
                        }
                    ],
                }
            ]
        },
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {"allowWrite": writable(primary, record, home)},
            "network": {"allowedDomains": list(ALL_HOSTS)},
        },
    }


def mcp_config(python: str) -> dict:
    """The MCP configuration of one task session: the project MCP server, by this Python and this
    package, told that its background session has no channel, since Claude Code does not wake a
    background session with channel events."""
    return {
        "mcpServers": {
            SERVER: {
                "command": python,
                "args": [
                    (PACKAGE_ROOT / "scripts/concorde.py").as_posix(),
                    "project-mcp",
                ],
                "env": {"CONCORDE_CHANNEL": "0"},
            }
        }
    }


def brief(primary: Path, record: dict, main: str) -> str:
    """The session's first prompt: the rendered task-session guidance and this task."""
    path = PACKAGE_ROOT / PROMPT
    if not path.is_file():
        raise store.TaskError(
            "session_failed",
            f"the task-session guidance {path} is missing; run the build "
            "(python3 scripts/concorde.py build) of the Concorde package",
        )
    guidance = path.read_text(encoding="utf-8").strip()
    task = "\n".join(
        [
            "## This task",
            "",
            f"- Task: `{record['id']}` on branch `{record['branch']}`",
            f"- Goal: {record['goal']}",
            f"- Modules: {', '.join(record['modules'])}",
            f"- Worktree (your working directory): `{record['worktree']}`",
            f"- Decision log: `{store.decision_log_path(primary, record['id'])}`",
            f"- Main agent session when this session started: `{main}`; report to the "
            "`main` that `concorde task report` prints, which the main agent may have rebound "
            "since",
        ]
    )
    return f"{guidance}\n\n{task}\n"


def start(
    here: Path,
    task_id: str,
    main: str,
    *,
    model: str | None = None,
    dry_run: bool = False,
    run=None,
    home: Path | None = None,
) -> dict:
    """Write the session's boundary and, unless ``dry_run``, start it with ``claude --bg``."""
    run = run or subprocess.run
    primary = store.require_primary(here)
    record = store.load_unended(
        primary, task_id, "a session works only in an open task"
    )
    if not main or not main.strip():
        raise store.TaskError(
            "invalid_input",
            "--main must name the main agent's session, which the task session reports to",
        )
    worktree = Path(record["worktree"])
    if not worktree.is_dir():
        raise store.TaskError(
            "missing_worktree",
            f"the worktree {worktree} of task {task_id} does not exist",
        )
    directory = session_directory(primary, task_id)
    directory.mkdir(parents=True, exist_ok=True)
    hook = directory / "write_hook.py"
    hook.write_text(hook_source(primary, record), encoding="utf-8")
    path = directory / "settings.json"
    path.write_text(
        json.dumps(settings(primary, record, hook, sys.executable, home), indent=2)
        + "\n",
        encoding="utf-8",
    )
    servers = directory / "mcp.json"
    servers.write_text(
        json.dumps(mcp_config(sys.executable), indent=2) + "\n", encoding="utf-8"
    )
    name = session_name(task_id)
    command = [
        "claude",
        "--bg",
        "--name",
        name,
        "--settings",
        path.as_posix(),
        "--mcp-config",
        servers.as_posix(),
        "--permission-mode",
        "auto",
        *(["--model", model] if model else []),
        brief(primary, record, main.strip()),
    ]
    shown = shlex.join([*command[:-1], "<brief>"])
    if dry_run:
        return {
            "command": shown,
            "cwd": worktree.as_posix(),
            "settings": path.as_posix(),
            "mcp_config": servers.as_posix(),
        }
    create_writable(writable(primary, record, home))
    try:
        launched = run(
            command, cwd=worktree, capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise store.TaskError(
            "session_failed",
            f"{shown} could not be started in {worktree}: {error}",
        ) from error
    output = ESCAPES.sub("", f"{launched.stdout}\n{launched.stderr}").strip()
    found = STARTED.search(ESCAPES.sub("", launched.stdout or ""))
    if launched.returncode != 0 or found is None:
        raise store.TaskError(
            "session_failed",
            f"{shown} in {worktree} exited {launched.returncode} without starting a "
            f"background session; its output: {output[-2000:] or '(none)'}",
        )
    started_at = store.now()
    # The full session id names the transcript; when Claude Code does not tell it now, the end
    # of the task asks again, so the start does not fail for it.
    try:
        listed = claude_sessions(run).get(found["id"])
    except LookupError:
        listed = None
    session = {
        "id": found["id"],
        "reported_id": found["id"],
        "session_id": _session_id(listed),
        "name": name,
        "main": main.strip(),
        "model": model,
        "settings": path.as_posix(),
        "started_at": started_at,
    }
    store.record_session(primary, task_id, session)
    return session


# --- the end of a task: stopping, keeping and removing its Claude Code sessions -------------
#
# Task sessions matter to the developer only through their main session, and a finished
# background session left in Claude's session list is noise there. When the task ends, each of
# its Claude Code sessions' transcript is copied into its trace node, which moves to the history
# with the task's folder, the node is finished from Claude Code's own records, and the session is
# then removed with ``claude rm``, which kills a job that still runs, deletes its job state and
# removes only a worktree Claude Code created itself, never the task worktree the session was
# started in.

# The transcript's names in the session's trace node: the conversation, and the folder Claude Code
# keeps beside it (subagent transcripts, long tool results) when there is one.
TRANSCRIPT = "transcript.jsonl"
TRANSCRIPT_FILES = "transcript"
CLAUDE_TIMEOUT = 60
# Claude Code's list of every session it knows, finished ones included.
AGENTS = ("agents", "--json", "--all")
# The states of that list that tell how a session ended, as node statuses: ``done`` when it
# finished its last turn and waits for its next message, ``failed`` when it ended in an error.
# Claude Code judges a session by whether its process lives, which it sees only from the
# session's own process namespace: from inside a task session's sandbox a live session reads
# ``failed``, so only a close, which runs outside every task session, asks.
STATES = {"done": "ok", "failed": "failed"}
# A session id is a file name under ``projects/``: letters, digits and dashes only.
SESSION_ID = re.compile(r"^[0-9A-Za-z][0-9A-Za-z-]*$")
# An assistant record Claude Code writes itself, which no model produced.
SYNTHETIC = "<synthetic>"


def claude_directory() -> Path:
    """Claude Code's configuration folder, which holds ``projects/`` with every transcript."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def _short(session: dict) -> str:
    """The id Claude Code's commands take: the one ``claude --bg`` reported."""
    return session.get("reported_id") or session["id"]


def _claude(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["claude", *arguments],
        capture_output=True,
        text=True,
        timeout=CLAUDE_TIMEOUT,
        check=False,
    )


def _said(result: subprocess.CompletedProcess) -> str:
    return (
        ESCAPES.sub("", f"{result.stdout}\n{result.stderr}").strip()[-2000:]
        or "(no output)"
    )


def claude_sessions(run=None) -> dict[str, dict]:
    """Every session Claude Code lists, finished ones included, by the short id ``claude --bg``
    reported: ``claude agents --json --all``, whose entries give each session's full
    ``sessionId``, its ``cwd`` and its ``state``. ``LookupError`` says what Claude Code answered."""
    run = run or subprocess.run
    command = shlex.join(["claude", *AGENTS])
    try:
        result = run(
            ["claude", *AGENTS],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise LookupError(f"`{command}` could not run: {error}") from error
    if result.returncode != 0:
        raise LookupError(f"`{command}` exited {result.returncode}: {_said(result)}")
    try:
        listed = json.loads(result.stdout or "")
    except ValueError as error:
        raise LookupError(
            f"`{command}` printed no JSON ({error}): {_said(result)}"
        ) from error
    if not isinstance(listed, list):
        raise LookupError(f"`{command}` printed no JSON list: {_said(result)}")
    return {
        str(item["id"]): item
        for item in listed
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _session_id(listed: dict | None) -> str | None:
    """The full session id of a session's entry in Claude Code's list, when it is one."""
    found = (listed or {}).get("sessionId")
    return found if isinstance(found, str) and SESSION_ID.match(found) else None


def _gone(result: subprocess.CompletedProcess) -> bool:
    """Whether Claude Code answered that it has no such session, already removed."""
    return "No job matching" in f"{result.stdout}{result.stderr}"


def stop_sessions(primary: Path, task_id: str) -> list[str]:
    """Stop every Claude Code session of a task with ``claude stop``, before a close without a
    merge removes the worktree it works in; one already ended or removed counts as stopped.
    What was stopped, described; ``session_stop_failed`` when one cannot be confirmed stopped,
    before the close changed anything."""
    stopped = []
    for found in store.sessions(primary, task_id):
        short = _short(found)
        worktree = store.load_task(primary, task_id)["worktree"]
        command = f"claude stop {short}"
        try:
            result = _claude("stop", short)
        except (OSError, subprocess.SubprocessError) as error:
            problem = f"`{command}` could not run: {error}"
        else:
            if result.returncode == 0 or _gone(result):
                stopped.append(f"Claude Code task session {short}")
                continue
            problem = f"`{command}` exited {result.returncode}: {_said(result)}"
        raise store.TaskError(
            "session_stop_failed",
            f"the Claude Code task session {short} ({found['name']}) of task {task_id} could "
            f"not be confirmed stopped, so closing the task without a merge would remove the "
            f"worktree {worktree} under a session that may still work in it: {problem}; the "
            f"task is unchanged"
            + (f" ({', '.join(stopped)} already stopped)" if stopped else "")
            + f"; stop the session (`{command}`, or `claude agents`), then close the task "
            "again",
        )
    return stopped


def _project_folder(cwd: str) -> str:
    """The folder under ``projects/`` where Claude Code keeps the transcripts of ``cwd``."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def find_transcript(cwd: str, session_id: str, directory: Path | None = None) -> Path:
    """The transcript of the session ``session_id`` started in ``cwd``: ``<session_id>.jsonl``
    of the project folder of ``cwd``, else the one file of that name in any project folder.
    ``LookupError`` says where it looked."""
    projects = (directory or claude_directory()) / "projects"
    if not projects.is_dir():
        raise LookupError(f"Claude Code's projects folder {projects} does not exist")
    name = f"{session_id}.jsonl"
    derived = projects / _project_folder(cwd) / name
    if derived.is_file():
        return derived
    found = sorted(path for path in projects.glob(f"*/{name}") if path.is_file())
    if len(found) == 1:
        return found[0]
    if found:
        raise LookupError(
            f"{len(found)} project folders of {projects} hold a transcript {name}: "
            + ", ".join(path.as_posix() for path in found)
        )
    raise LookupError(
        f"no transcript {name} is in {derived.parent} or any other project folder of "
        f"{projects}"
    )


def _records(path: Path):
    """The JSON objects of a transcript's lines; a line that is not one is skipped."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for line in lines:
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            yield value


def _moment(text) -> datetime | None:
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment.astimezone(UTC) if moment.tzinfo else moment.replace(tzinfo=UTC)


def _count(value) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def transcript_figures(transcript: Path, subagents: list[Path]) -> dict:
    """What a session consumed and when it ended, from its transcript and the transcripts of its
    subagents, as Claude Code recorded them: each API message's tokens, counted once by its
    ``message.id`` since one message may span several records; the cost of the transcript's last
    ``cost-state`` record, when no assistant record follows it; the times of the transcript's
    first and last records. ``usage``, ``ended_at``, ``models`` and ``model_usage``."""
    messages: dict[str, tuple[str, dict]] = {}
    times: list[datetime] = []
    cost_state, stale = None, False
    for path in [transcript, *subagents]:
        main = path == transcript
        for number, record in enumerate(_records(path)):
            kind = record.get("type")
            if main:
                moment = _moment(record.get("timestamp"))
                if moment is not None:
                    times.append(moment)
                if kind == "cost-state":
                    cost_state, stale = record, False
            if kind != "assistant":
                continue
            stale = stale or (main and cost_state is not None)
            message = record.get("message")
            if not isinstance(message, dict) or not isinstance(
                message.get("usage"), dict
            ):
                continue
            model = message.get("model")
            if model == SYNTHETIC:
                continue
            key = message.get("id") or f"{path.name}:{record.get('uuid') or number}"
            messages[str(key)] = (str(model or "unknown"), message["usage"])
    models: dict[str, dict] = {}
    for model, used in messages.values():
        sums = models.setdefault(
            model,
            {
                "tokens_in": 0,
                "tokens_out": 0,
                "tokens_cache_read": 0,
                "tokens_cache_write": 0,
                "messages": 0,
            },
        )
        sums["tokens_in"] += _count(used.get("input_tokens"))
        sums["tokens_out"] += _count(used.get("output_tokens"))
        sums["tokens_cache_read"] += _count(used.get("cache_read_input_tokens"))
        sums["tokens_cache_write"] += _count(used.get("cache_creation_input_tokens"))
        sums["messages"] += 1
    reported = cost_state if cost_state is not None and not stale else None
    cost = (reported or {}).get("totalCostUSD")
    model_usage = (reported or {}).get("modelUsage")

    def total(field: str) -> int | None:
        return sum(item[field] for item in models.values()) if models else None

    return {
        "usage": trace.usage(
            tokens_in=total("tokens_in"),
            tokens_out=total("tokens_out"),
            tokens_cache_read=total("tokens_cache_read"),
            tokens_cache_write=total("tokens_cache_write"),
            cost_usd=(
                float(cost)
                if isinstance(cost, (int, float))
                and not isinstance(cost, bool)
                and cost >= 0
                else None
            ),
            turns=total("messages"),
            duration_seconds=(
                (max(times) - min(times)).total_seconds() if times else None
            ),
        ),
        "ended_at": (max(times).strftime("%Y-%m-%dT%H:%M:%S.%fZ") if times else None),
        "models": models,
        "model_usage": model_usage if isinstance(model_usage, dict) else None,
    }


def _outcome(state) -> str | None:
    """Claude Code's state of a session as a node outcome, snake_case."""
    if not isinstance(state, str):
        return None
    text = re.sub(r"[^a-z0-9]+", "_", state.lower()).strip("_")
    return text if re.match(r"^[a-z][a-z0-9_]*$", text) else None


def _kept(record: dict) -> bool:
    return any(item["id"] == "transcript" for item in record.get("artifacts") or [])


def _keep(folder: Path, source: Path) -> dict:
    """Copy a transcript and the folder beside it into a session's node; its figures."""
    shutil.copyfile(source, folder / TRANSCRIPT)
    beside = source.with_suffix("")
    if beside.is_dir():
        shutil.copytree(beside, folder / TRANSCRIPT_FILES, dirs_exist_ok=True)
    return transcript_figures(
        folder / TRANSCRIPT,
        sorted((folder / TRANSCRIPT_FILES / "subagents").glob("*.jsonl")),
    )


def _discard(folder: Path) -> None:
    (folder / TRANSCRIPT).unlink(missing_ok=True)
    shutil.rmtree(folder / TRANSCRIPT_FILES, ignore_errors=True)


def finish_sessions(primary: Path, task_id: str, run=None) -> list[str]:
    """Finish the trace node of every Claude Code session of an ending task from Claude Code's
    own records, before the task's folder moves to the history: its full session id and state
    from ``claude agents --json --all``, asked once, and its transcript, found by that id, copied
    as ``transcript.jsonl`` with the folder beside it as ``transcript/``, from which its usage and
    end are derived. A warning for each session whose transcript cannot be kept; such a session
    is then not removed, so nothing of it is lost, and its node still receives what Claude Code
    told of it."""
    worktree = store.load_task(primary, task_id)["worktree"]
    warnings = []
    listed: dict | None = None
    unlisted = ""
    for found in store.sessions(primary, task_id):
        short, folder = _short(found), Path(found["directory"])
        with store.task_locked(primary, task_id):
            record = trace.read(folder)
            if record is None or _kept(record):
                continue
            if listed is None:
                try:
                    listed = claude_sessions(run)
                except LookupError as error:
                    listed, unlisted = {}, f"; {error}"
            entry = listed.get(short)
            data = store.session_content(record["content"]["data"])
            data["session_id"] = data["session_id"] or _session_id(entry)
            state = (entry or {}).get("state")
            data["claude_state"] = state if isinstance(state, str) and state else None
            record["status"] = STATES.get(data["claude_state"], "unknown")
            record["outcome"] = _outcome(data["claude_state"])
            problem = None
            try:
                if data["session_id"] is None:
                    raise LookupError(
                        "Claude Code did not tell its full session id, which names its "
                        f"transcript: `{shlex.join(['claude', *AGENTS])}` lists no session "
                        f"{short}{unlisted}"
                    )
                cwd = (entry or {}).get("cwd")
                source = find_transcript(
                    cwd if isinstance(cwd, str) and cwd else worktree,
                    data["session_id"],
                )
                figures = _keep(folder, source)
                record["artifacts"] = [
                    *(record.get("artifacts") or []),
                    trace.artifact(folder, "transcript", TRANSCRIPT),
                ]
                record["usage"] = figures["usage"]
                record["ended_at"] = figures["ended_at"]
                data["models"] = figures["models"]
                data["model_usage"] = figures["model_usage"]
            except (LookupError, OSError) as error:
                _discard(folder)
                problem = error
            record["content"] = {
                "type_id": store.SESSION_TRACE,
                "schema_version": type_version(store.SESSION_TRACE),
                "data": data,
            }
            try:
                trace.write(folder, record)
            except trace.TraceError as error:
                _discard(folder)
                problem = error
            if problem is not None:
                warnings.append(
                    f"the transcript of the Claude Code task session {short} "
                    f"({found['name']}) of task {task_id} could not be kept in its trace node "
                    f"{folder}: {problem}; the session stays in Claude's session list so that "
                    f"its transcript is not lost: keep what you need of it, then remove it "
                    f"with `claude rm {short}`"
                )
    return warnings


def remove_sessions(primary: Path, task_id: str, folder: Path) -> list[str]:
    """Remove every Claude Code session of an ended task, whose folder is now ``folder`` in the
    history, from Claude's session list with ``claude rm``, once its transcript is kept there.
    Best effort: a warning for each session not removed, naming the reason and the command."""
    warnings = []
    for found in store.sessions(primary, task_id, folder):
        short = _short(found)
        if not _kept(trace.read(Path(found["directory"])) or {}):
            continue
        command = f"claude rm {short}"
        try:
            result = _claude("rm", short)
        except (OSError, subprocess.SubprocessError) as error:
            problem = f"`{command}` could not run: {error}"
        else:
            if result.returncode == 0 or _gone(result):
                continue
            problem = f"`{command}` exited {result.returncode}: {_said(result)}"
        warnings.append(
            f"the Claude Code task session {short} ({found['name']}) of task {task_id} was "
            f"not removed from Claude's session list: {problem}; its transcript is kept in "
            f"{Path(found['directory']) / TRANSCRIPT}; remove it by hand with `{command}`"
        )
    return warnings


__all__ = [
    "brief",
    "claude_sessions",
    "find_transcript",
    "finish_sessions",
    "hook_source",
    "mcp_config",
    "remove_sessions",
    "session_name",
    "settings",
    "start",
    "stop_sessions",
    "transcript_figures",
    "writable",
]
