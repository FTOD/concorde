"""The Kernel's two locks, taken through Tracing's lock library.

The **workspace lock** ``locks/workspaces/<workspace>.lock`` of the ``.concorde`` a workspace's
binding names keeps a workspace doing one thing at a time: a run of the workspace holds it from
before its admission until after its result, and whoever prepared the workspace takes it to merge
or retire it. The **merge lock** ``locks/merge.lock`` of the primary worktree's ``.concorde`` keeps
the changes Concorde makes to the primary branch from interleaving: a task's merge, open and close
and every Issue write. Both are ``flock`` locks whose holder line names the holder; a taker that
gives up waiting is refused naming it (``specs/concorde/kernel/module.md#concept.merge-lock``).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .refusal import KernelError
from .tracing import layout, locks

# How long a taker of the merge lock waits for it by default, in seconds.
MERGE_WAIT = 300.0


class LockRefused(KernelError):
    """A lock that stayed held for the whole wait, or a workspace retired while it was awaited:
    ``holder`` describes who held it, ``entry`` is its holder line as an object when it reads as
    one, and ``waited`` the seconds spent waiting."""

    def __init__(
        self,
        code: str,
        message: str,
        path: Path,
        *,
        holder: str | None = None,
        entry: dict | None = None,
        waited: float = 0.0,
    ):
        super().__init__(code, message, field=str(path))
        self.path = path
        self.holder = holder
        self.entry = entry
        self.waited = waited


def merge_lock_path(concorde: Path) -> Path:
    """The merge lock of the ``.concorde`` directory of a primary worktree."""
    return layout.lock_file(concorde, "merge")


@contextmanager
def merge_lock(
    concorde: Path,
    holder: str,
    *,
    wait: float | None = MERGE_WAIT,
    task: str | None = None,
):
    """Hold the merge lock for the block, waiting up to ``wait`` seconds (None: as long as it
    takes); yield the seconds spent waiting. Refused with ``merge_busy`` naming the holder.

    ``holder`` and ``task`` are written into the holder line; a lock this process was handed is
    adopted without waiting.
    """
    path = merge_lock_path(concorde)
    try:
        with locks.hold(path, holder, wait=wait, task=task) as waited:
            yield waited
    except locks.LockBusy as busy:
        raise LockRefused(
            "merge_busy",
            f"the merge lock {path} is still held by {busy.holder} after a wait of "
            f"{busy.waited:.0f} s",
            path,
            holder=busy.holder,
            entry=busy.entry,
            waited=busy.waited,
        ) from None


def merge_lock_holder(concorde: Path) -> str | None:
    """Who holds the merge lock now, or None when nobody does."""
    return locks.holder(merge_lock_path(concorde))


def workspace_lock_path(concorde: Path, workspace: str) -> Path:
    """The lock of ``workspace`` under the ``.concorde`` its binding names."""
    return layout.lock_file(concorde, "workspace", workspace)


@contextmanager
def workspace_lock(
    concorde: Path,
    workspace: str,
    holder: str,
    *,
    wait: float | None = 0.0,
    waiting: Callable[[str], None] | None = None,
    task: str | None = None,
    retake: bool = True,
):
    """Hold the lock of ``workspace`` for the block; yield the seconds spent waiting for it.

    A held lock is waited for up to ``wait`` seconds inside this process (None: as long as it
    takes), ``waiting`` being told the holder when the wait begins; then it is refused with
    ``workspace_busy`` naming the holder. With ``retake`` False, a lock file its holder removed
    while this process waited, as the close that retires a workspace does, is refused with
    ``workspace_retired`` instead of being taken again.
    """
    path = workspace_lock_path(concorde, workspace)
    try:
        with locks.hold(
            path, holder, wait=wait, waiting=waiting, task=task, retake=retake
        ) as waited:
            yield waited
    except locks.LockGone as gone:
        raise LockRefused(
            "workspace_retired",
            f"the workspace {workspace} was retired while this process waited {gone.waited:.0f} s "
            f"for its lock: its holder removed the lock file {path}, as the close that retires a "
            "workspace does, so the lock this process took is no longer the workspace's",
            path,
            waited=gone.waited,
        ) from None
    except locks.LockBusy as busy:
        after = f" after waiting {busy.waited:.0f} s" if wait else ""
        raise LockRefused(
            "workspace_busy",
            f"the workspace {workspace} is busy{after}: {busy.holder} holds its lock {path}; "
            "one workspace does one thing at a time",
            path,
            holder=busy.holder,
            entry=busy.entry,
            waited=busy.waited,
        ) from None


def workspace_lock_holder(concorde: Path, workspace: str) -> str | None:
    """Who holds the lock of ``workspace`` now, or None when nobody does."""
    return locks.holder(workspace_lock_path(concorde, workspace))


__all__ = [
    "MERGE_WAIT",
    "LockRefused",
    "merge_lock",
    "merge_lock_holder",
    "merge_lock_path",
    "workspace_lock",
    "workspace_lock_holder",
    "workspace_lock_path",
]
