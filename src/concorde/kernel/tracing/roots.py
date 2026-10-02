"""Trace roots: the folders under a ``.concorde`` directory in which the parts keep their traces.

A part that keeps the top nodes of traces registers each root here as plain data when its code
loads, as it registers its typed value types: in Concorde, Coordination's Tasks registers the
current tasks and the history, Execution the unbound runs and the lobby. Tracing searches, lists
and prunes only the registered roots, each by the rules registered with it, and so never learns
what a task or a run is (``specs/concorde/kernel/tracing/contracts.md#trace-roots``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PLACES = ("primary", "worktree")
STATES = ("current", "closed")
# Which option of ``concorde trace list`` lists a root's top nodes: always, with ``--history``,
# with ``--unbound``, or never (they are still found by their identity).
LISTINGS = ("always", "history", "unbound", "never")
# The retention periods of the Tracing configuration a root may name.
PERIODS = ("unbound_days", "history_days", "conversation_days")


class RootError(Exception):
    """A trace root registered with another definition under a name already registered, or a
    definition that is not one."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TraceRoot:
    """One registered trace root.

    ``folder`` is relative to a ``.concorde`` directory, ``place`` says whether that directory is
    the primary worktree's or the one of the worktree a node started in, ``kind`` is the kind of
    its top nodes and ``state`` whether its folders are still written (``current``) or never
    changed again (``closed``). ``ended`` is the field of a top node's ``trace.json`` that dates its
    end; ``period`` the configuration's period after which a whole top folder that ended is
    removed, and ``conversation_period`` the one after which its conversation records are, the
    files named ``conversation_files`` and folders named ``conversation_folders`` at any depth.
    ``alive_lock`` is the kind of lock, named after the top node's identity, whose holder says the
    node is still being written, so that retention never removes it. ``listed`` says which option
    of ``concorde trace list`` lists it.
    """

    name: str
    folder: str
    place: str
    kind: str
    state: str
    listed: str
    ended: str = "ended_at"
    period: str | None = None
    conversation_period: str | None = None
    conversation_files: tuple[str, ...] = ()
    conversation_folders: tuple[str, ...] = ()
    alive_lock: str | None = None

    def path(self, concorde: Path) -> Path:
        """The root's folder under the ``.concorde`` directory ``concorde``."""
        return Path(concorde) / self.folder

    def top_folders(self, concorde: Path) -> list[Path]:
        """The folders of the root's top nodes under ``concorde``, by name."""
        try:
            return sorted(
                item
                for item in self.path(concorde).iterdir()
                if item.is_dir() and not item.is_symlink()
            )
        except OSError:
            return []


_ROOTS: dict[str, TraceRoot] = {}


def register(root: TraceRoot) -> None:
    """Register ``root``; registering an equal root again changes nothing, another root under the
    same name or folder is refused with ``duplicate_root``."""
    if (
        not isinstance(root, TraceRoot)
        or not root.name
        or not root.folder
        or "/" in root.folder
        or root.folder in (".", "..")
        or root.place not in PLACES
        or root.state not in STATES
        or root.listed not in LISTINGS
        or any(
            period is not None and period not in PERIODS
            for period in (root.period, root.conversation_period)
        )
    ):
        raise RootError("invalid_root", f"{root!r} is no trace root definition")
    for existing in _ROOTS.values():
        if existing == root:
            return
        if existing.name == root.name or existing.folder == root.folder:
            raise RootError(
                "duplicate_root",
                f"the trace root {root.name} ({root.folder}/) clashes with the registered root "
                f"{existing.name} ({existing.folder}/)",
            )
    _ROOTS[root.name] = root


def registered() -> tuple[TraceRoot, ...]:
    """Every registered root, in the order registered."""
    return tuple(_ROOTS.values())


__all__ = [
    "LISTINGS",
    "PERIODS",
    "PLACES",
    "STATES",
    "RootError",
    "TraceRoot",
    "register",
    "registered",
]
