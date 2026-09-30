"""Where Tracing keeps every task, trace node and lock, relative to a ``.concorde`` directory.

The layout is Tracing's (``specs/concorde/tracing/contracts.md#layout``): one folder per current
task under ``tasks/``, the closed tasks under ``history/``, the unbound runs under ``unbound/`` and
every lock under ``locks/``. Producers ask here for the folders and lock files they need and never
spell a path of the layout themselves; a folder a parent hands its child is only ever joined below.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

CONCORDE = ".concorde"
TASKS = "tasks"
HISTORY = "history"
UNBOUND = "unbound"
LOCKS = "locks"
CONFIGURATION = "tracing.json"
# The file names of a node's own record and of the records that stay next to it.
TRACE = "trace.json"
PROGRESS = "status.json"
RESULT = "result.json"
# Every folder Git must ignore, relative to the project root.
IGNORED = tuple(f"{CONCORDE}/{name}/" for name in (TASKS, HISTORY, UNBOUND, LOCKS))
# The kinds of lock and the folder of ``locks/`` their files lie in; None: directly in it.
LOCK_KINDS = {
    "merge": None,
    "task": "tasks",
    "workspace": "workspaces",
    "workflow": "workflows",
    "run": "runs",
}
_UNSAFE = re.compile(r"[^a-z0-9.-]")
# The name a lock file carries: the identity itself, never a path.
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def concorde_of(worktree: Path) -> Path:
    """The ``.concorde`` directory of a worktree."""
    return Path(worktree) / CONCORDE


def primary_worktree(here: Path) -> Path | None:
    """The primary worktree of the repository ``here`` lies in, or None outside Git."""
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=here,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if common.returncode != 0:
        return None
    return Path(os.path.realpath(common.stdout.strip())).parent


def tasks_folder(concorde: Path) -> Path:
    return Path(concorde) / TASKS


def task_folder(concorde: Path, task: str) -> Path:
    return tasks_folder(concorde) / task


def history_folder(concorde: Path) -> Path:
    return Path(concorde) / HISTORY


def unbound_folder(concorde: Path) -> Path:
    return Path(concorde) / UNBOUND


def locks_folder(concorde: Path) -> Path:
    return Path(concorde) / LOCKS


def workspace_folder(task: Path) -> Path:
    """The workspace folder a task's binding names, inside the task's folder."""
    return Path(task) / "workspace"


def runs_folder(workspace: Path) -> Path:
    return Path(workspace) / "runs"


def run_folder(workspace: Path, run_id: str) -> Path:
    return runs_folder(workspace) / run_id


def unbound_run_folder(concorde: Path, run_id: str) -> Path:
    return unbound_folder(concorde) / run_id


def workflow_folder(workspace: Path) -> Path:
    return Path(workspace) / "workflow"


def safe(name: str) -> str:
    """A name as a folder name: every character but ``[a-z0-9.-]`` written as ``_``."""
    return _UNSAFE.sub("_", name)


def step_folder(workflow: Path, number: int, key: str) -> Path:
    return Path(workflow) / "steps" / f"{number}-{safe(key)}"


def worker_folder(run: Path, worker_run: str) -> Path:
    return Path(run) / "workers" / worker_run


def round_folder(parent: Path, number: int) -> Path:
    return Path(parent) / "rounds" / str(number)


def checks_folder(parent: Path) -> Path:
    return Path(parent) / "checks"


def check_folder(checks: Path, check_id: str) -> Path:
    return Path(checks) / safe(check_id)


def lock_file(concorde: Path, kind: str, name: str | None = None) -> Path:
    """The lock file of ``kind`` (see ``LOCK_KINDS``), named ``name`` for a per-thing lock."""
    folder = LOCK_KINDS[kind]
    base = locks_folder(concorde)
    if folder is None:
        return base / f"{kind}.lock"
    if not name or not _NAME.match(name):
        raise ValueError(
            f"a {kind} lock needs the name of what it locks, a task, workspace or run identity; "
            f"got {name!r}"
        )
    return base / folder / f"{name}.lock"


def history_key(concorde: Path, task: str, taken=None) -> str:
    """The history key a closing task gets: its name, or ``<task>.<n>`` from 2 when taken.

    A key is taken when the history holds a folder of that name or ``taken(key)`` says so, as
    for a key whose decision log is already committed.
    """
    history = history_folder(concorde)

    def used(key: str) -> bool:
        return (history / key).exists() or bool(taken and taken(key))

    if not used(task):
        return task
    number = 2
    while used(f"{task}.{number}"):
        number += 1
    return f"{task}.{number}"


def relative(folder: Path, path: Path) -> str:
    """``path`` relative to ``folder``, which must contain it, in POSIX spelling."""
    return Path(os.path.realpath(path)).relative_to(os.path.realpath(folder)).as_posix()


__all__ = [
    "CONCORDE",
    "CONFIGURATION",
    "HISTORY",
    "IGNORED",
    "LOCKS",
    "LOCK_KINDS",
    "PROGRESS",
    "RESULT",
    "TASKS",
    "TRACE",
    "UNBOUND",
    "check_folder",
    "checks_folder",
    "concorde_of",
    "history_folder",
    "history_key",
    "lock_file",
    "locks_folder",
    "primary_worktree",
    "relative",
    "round_folder",
    "run_folder",
    "runs_folder",
    "safe",
    "step_folder",
    "task_folder",
    "tasks_folder",
    "unbound_folder",
    "unbound_run_folder",
    "worker_folder",
    "workflow_folder",
    "workspace_folder",
]
