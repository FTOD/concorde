"""``concorde task session``: start a task session, a background Claude Code session in one task.

The main agent starts one per task when it splits complex work into several tasks, and stays in
the primary worktree itself. A task session works only inside its task worktree: it may edit
directly or run Operations there with the worktree's own ``concorde``, keeps the task's decision
log, delivers the task, and reports to the main agent, which alone merges and closes tasks.

Its boundary is generated here, next to the task record in
``.concorde/tasks/<task>.session/``, and guards against mistakes, not a malicious session:

- a PreToolUse hook lets Edit and Write change only the task worktree and its decision log;
- the Bash sandbox lets commands write only the task worktree, the repository's Git directory
  (commits on the task branch), ``.concorde/runs/`` and ``.concorde/tasks/`` (Operation runs and
  task records) and the user's package caches; reads stay open, and a command reaches the
  network only through hosts it names, which the ``auto`` classifier reviews with it;
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
import subprocess
import sys
from pathlib import Path

from . import session_hook, store

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
PROMPT = "generated/main-session/task-session.md"
# Package caches outside the worktree that ordinary builds write, such as uv, pip and npm.
CACHES = (".cache", ".npm")
STARTED = re.compile(r"backgrounded\s+·\s+(?P<id>[0-9A-Za-z-]+)\s+·")


def session_name(task_id: str) -> str:
    return f"task-{task_id}"


def session_directory(primary: Path, task_id: str) -> Path:
    return store.tasks_directory(primary) / f"{task_id}.session"


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
        primary / ".concorde/runs",
        store.tasks_directory(primary),
        *(home / name for name in CACHES),
    ]
    return sorted({Path(os.path.realpath(path)).as_posix() for path in paths})


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
        },
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
            f"- Main agent session to report to: `{main}`",
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
    record = store.load_task(primary, task_id)
    if record["state"] not in ("open", "active", "delivered"):
        raise store.TaskError(
            "task_closed",
            f"task {task_id} is {record['state']}; a session works only in an open task",
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
    name = session_name(task_id)
    command = [
        "claude",
        "--bg",
        "--name",
        name,
        "--settings",
        path.as_posix(),
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
        }
    try:
        launched = run(
            command, cwd=worktree, capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise store.TaskError(
            "session_failed",
            f"{shown} could not be started in {worktree}: {error}",
        ) from error
    output = f"{launched.stdout}\n{launched.stderr}".strip()
    found = STARTED.search(launched.stdout or "")
    if launched.returncode != 0 or found is None:
        raise store.TaskError(
            "session_failed",
            f"{shown} in {worktree} exited {launched.returncode} without starting a "
            f"background session; its output: {output[-2000:] or '(none)'}",
        )
    session = {
        "id": found["id"],
        "name": name,
        "main": main.strip(),
        "settings": path.as_posix(),
        "started_at": store.now(),
    }
    store.record_session(primary, task_id, session)
    return session


__all__ = ["brief", "hook_source", "session_name", "settings", "start", "writable"]
