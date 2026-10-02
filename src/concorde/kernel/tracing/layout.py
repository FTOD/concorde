"""Where Tracing keeps trace nodes and locks, relative to a ``.concorde`` directory.

The layout is Tracing's (``specs/concorde/kernel/tracing/contracts.md#layout``): every lock under
``locks/``, the Tracing configuration ``tracing.json``, and below each node the folders its
children lie in. The trace roots, the folders the top nodes lie in, are the parts' own and
registered with Tracing (``roots``). Producers ask here for the folders and lock files they need
and never spell a path of the layout themselves; a folder a parent hands its child is only ever
joined below.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

CONCORDE = ".concorde"
LOCKS = "locks"
CONFIGURATION = "tracing.json"
# The file names of a node's own record and of the records that stay next to it.
TRACE = "trace.json"
PROGRESS = "status.json"
RESULT = "result.json"
# The kinds of lock and the folder of ``locks/`` their files lie in; None: directly in it.
LOCK_KINDS = {
    "merge": None,
    "task": "tasks",
    "workspace": "workspaces",
    "workflow": "workflows",
    "run": "runs",
    "attempt": "attempts",
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


def locks_folder(concorde: Path) -> Path:
    return Path(concorde) / LOCKS


def runs_folder(workspace: Path) -> Path:
    return Path(workspace) / "runs"


def run_folder(workspace: Path, run_id: str) -> Path:
    return runs_folder(workspace) / run_id


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


def relative(folder: Path, path: Path) -> str:
    """``path`` relative to ``folder``, which must contain it, in POSIX spelling."""
    return Path(os.path.realpath(path)).relative_to(os.path.realpath(folder)).as_posix()


__all__ = [
    "CONCORDE",
    "CONFIGURATION",
    "LOCKS",
    "LOCK_KINDS",
    "PROGRESS",
    "RESULT",
    "TRACE",
    "check_folder",
    "checks_folder",
    "concorde_of",
    "lock_file",
    "locks_folder",
    "primary_worktree",
    "relative",
    "round_folder",
    "run_folder",
    "runs_folder",
    "safe",
    "step_folder",
    "worker_folder",
    "workflow_folder",
]
