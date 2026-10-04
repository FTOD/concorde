"""Reading traces: find a node, walk its subtree, roll its usage up, tell a lost run.

Nothing here writes. Nodes are found and listed only among the registered trace roots
(``roots``), or the roots a caller passes. A node's children are the trace nodes in the folders
below its own, the nearest ones on each path; a task's ``workspace/`` folder, which Execution fills and which has no
record of its own, is shown as a ``workspace`` node. A node that says it runs is ``lost`` when it is
a run whose run lock nobody holds, or lies below such a run, however it was addressed.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from . import layout, locks
from .node import USAGE_FIELDS, parse_time, read, seconds_between
from .roots import LISTINGS, TraceRoot, registered

TOTALS = (
    "tokens_in",
    "tokens_out",
    "tokens_cache_read",
    "tokens_cache_write",
    "cost_usd",
    "turns",
)
# Folders below a node that never hold a node of their own.
NOT_NODES = {"answers", "reports", "runtime", "__pycache__"}


class ReadError(Exception):
    """A node the reader cannot find or read; ``code`` names why."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _run_lock(concorde: Path, run_id: str) -> Path:
    return layout.lock_file(concorde, "run", run_id)


def run_alive(concorde: Path, run_id: str) -> bool:
    """Whether the runner of ``run_id``, whose locks lie under ``concorde``, still runs."""
    return locks.held(_run_lock(concorde, run_id))


def _children_folders(folder: Path) -> list[Path]:
    """The folders of the nearest nodes below ``folder``, and a task's workspace folder."""
    found: list[Path] = []
    try:
        entries = sorted(
            item for item in folder.iterdir() if item.is_dir() and not item.is_symlink()
        )
    except OSError:
        return found
    for entry in entries:
        if entry.name in NOT_NODES or entry.name.startswith("."):
            continue
        if (entry / layout.TRACE).is_file() or _is_workspace(entry):
            found.append(entry)
        else:
            found.extend(_children_folders(entry))
    return found


def _is_workspace(folder: Path) -> bool:
    """A workspace folder: ``workspace/`` of a task node, holding runs or a workflow."""
    return (
        folder.name == "workspace"
        and (folder.parent / layout.TRACE).is_file()
        and not (folder / layout.TRACE).exists()
    )


def _workspace_record(folder: Path, children: list[dict]) -> dict:
    """The record a workspace folder is shown with: ``running`` while any child runs, otherwise
    the status of its most recently started child, ``unknown`` without children."""
    names = [
        item["metadata"].get("workspace")
        for item in children
        if item["metadata"].get("workspace")
    ]
    starts = [item["started_at"] for item in children if item["started_at"]]
    running = any(item["status"] == "running" for item in children)
    ends = [item["ended_at"] for item in children if item["ended_at"]]
    # The children are sorted by start, so the last is the most recently started.
    status = (
        "running" if running else (children[-1]["status"] if children else "unknown")
    )
    return {
        "id": names[0] if names else folder.parent.name,
        "kind": "workspace",
        "started_at": min(starts) if starts else None,
        "ended_at": None if status in ("running", "lost") or not ends else max(ends),
        "status": status,
        "outcome": None,
        "usage": {name: None for name in USAGE_FIELDS},
        "error": None,
        "metadata": {"workspace": names[0]} if names else {},
        "references": [],
    }


def _now() -> datetime:
    return datetime.now(UTC)


def _below_lost_run(folder: Path, concorde: Path) -> bool:
    """Whether a run above ``folder`` says it runs while nobody holds its run lock. The search
    goes up to ``concorde`` when the folder lies in it, else to the worktree or filesystem root."""
    top = Path(os.path.realpath(concorde))
    current = Path(os.path.realpath(folder))
    inside = current.is_relative_to(top)
    while current != current.parent and current != top:
        current = current.parent
        if not inside and (current / ".git").exists():
            break
        record = read(current)
        if (
            record
            and record.get("kind") == "run"
            and record.get("status") == "running"
            and isinstance(record.get("id"), str)
            and not run_alive(concorde, record["id"])
        ):
            return True
    return False


def view(
    folder: Path,
    concorde: Path,
    *,
    depth: int | None = None,
    lost: bool | None = None,
) -> dict:
    """The view of the node in ``folder`` and its subtree (contract.tracing.view).

    ``concorde`` is the ``.concorde`` whose ``locks/`` holds the run locks of the runs below.
    ``lost`` says an ancestor run was found lost, which makes every running node below lost too;
    None looks for such a run above ``folder`` first, as for a node addressed directly.
    """
    folder = Path(folder)
    if lost is None:
        lost = _below_lost_run(folder, concorde)
    record = read(folder)
    # A workspace folder has no record of its own: below a task's node, or any folder a binding
    # names that holds runs or a workflow, whoever prepared the workspace.
    is_workspace = record is None and (
        _is_workspace(folder)
        or (folder / "runs").is_dir()
        or (folder / "workflow").is_dir()
    )
    if record is None and not is_workspace:
        raise ReadError("node_unreadable", f"{folder} holds no readable {layout.TRACE}")
    if record is not None:
        status = record.get("status")
        if status == "running" and (
            lost
            or (record.get("kind") == "run" and not run_alive(concorde, record["id"]))
        ):
            status = "lost"
        lost_below = lost or status == "lost"
    else:
        lost_below = lost
    children = [
        view(
            child, concorde, depth=None if depth is None else depth - 1, lost=lost_below
        )
        for child in _children_folders(folder)
    ]
    children.sort(key=lambda item: (item["started_at"] or "", item["id"]))
    if is_workspace:
        record = _workspace_record(folder, children)
        status = record["status"]
    own = {name: (record.get("usage") or {}).get(name) for name in USAGE_FIELDS}
    rolled = {name: 0 for name in TOTALS}
    for name in TOTALS:
        value = own.get(name) or 0
        rolled[name] = value
    for child in children:
        for name in TOTALS:
            rolled[name] += child["rolled_up"][name]
    rolled["cost_usd"] = round(float(rolled["cost_usd"]), 6)
    ended = record.get("ended_at")
    duration = own.get("duration_seconds")
    if duration is None:
        started = parse_time(record.get("started_at"))
        if ended:
            duration = seconds_between(record.get("started_at"), ended)
        elif started is not None and status in ("running", "lost"):
            duration = round((_now() - started).total_seconds(), 3)
    return {
        "id": record["id"],
        "kind": record["kind"],
        "path": Path(os.path.realpath(folder)).as_posix(),
        "status": status,
        "outcome": record.get("outcome"),
        "started_at": record.get("started_at"),
        "ended_at": ended,
        "duration_seconds": duration,
        "usage": own,
        "rolled_up": rolled,
        "metadata": record.get("metadata") or {},
        "references": record.get("references") or [],
        "error": record.get("error"),
        "children": [] if depth is not None and depth <= 0 else children,
    }


def _strip(value: dict, depth: int | None) -> dict:
    if depth is not None and depth <= 0:
        return {**value, "children": []}
    return {
        **value,
        "children": [
            _strip(child, None if depth is None else depth - 1)
            for child in value["children"]
        ],
    }


def concorde_directories(here: Path) -> list[Path]:
    """The ``.concorde`` directories a reader looks in from ``here``: the worktree's own, the one
    its workspace binding names, and the primary worktree's, without repetition."""
    found: list[Path] = []
    worktree = _toplevel(here)
    candidates: list[Path] = []
    if worktree is not None:
        candidates.append(layout.concorde_of(worktree))
        binding = _binding(worktree)
        if binding and isinstance(binding.get("concorde"), str):
            candidates.append(Path(binding["concorde"]))
    primary = layout.primary_worktree(here)
    if primary is not None:
        candidates.append(layout.concorde_of(primary))
    for candidate in candidates:
        real = Path(os.path.realpath(candidate))
        if real not in found:
            found.append(real)
    return found


def _toplevel(here: Path) -> Path | None:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return Path(os.path.realpath(result.stdout.strip()))


def _binding(worktree: Path) -> dict | None:
    try:
        value = json.loads(
            (layout.concorde_of(worktree) / "workspace.json").read_text()
        )
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _roots(roots: Iterable[TraceRoot] | None) -> tuple[TraceRoot, ...]:
    return registered() if roots is None else tuple(roots)


def _placed(roots: tuple[TraceRoot, ...], concorde: Path) -> tuple[TraceRoot, ...]:
    """The roots that lie under ``concorde`` by the place each was registered with: a root of
    the primary worktree's ``.concorde`` never lies under a linked worktree's, whose ``.git`` is a
    file; a root of the worktree a node started in lies under any."""
    linked = (Path(concorde).parent / ".git").is_file()
    return tuple(root for root in roots if not (linked and root.place == "primary"))


def workspace_runs(workspace: Path) -> list[Path]:
    """The folders of every run of a workspace folder: started directly and by workflow steps."""
    found: list[Path] = []
    runs = layout.runs_folder(workspace)
    try:
        found.extend(sorted(item for item in runs.iterdir() if item.is_dir()))
    except OSError:
        pass
    steps = layout.workflow_folder(workspace) / "steps"
    try:
        for step in sorted(steps.iterdir()):
            if (step / "run").is_dir():
                found.append(step / "run")
    except OSError:
        pass
    return found


def find_run(workspace: Path, run_id: str) -> Path | None:
    """The folder of run ``run_id`` in a workspace folder, directly or in a workflow step."""
    direct = layout.run_folder(workspace, run_id)
    if direct.is_dir():
        return direct
    for folder in workspace_runs(workspace):
        if folder.name == "run" and (read(folder) or {}).get("id") == run_id:
            return folder
    return None


def _node_folder(folder: Path) -> bool:
    """Whether ``folder`` is a node's: it holds its ``trace.json``, or, before its producer wrote
    that, its progress file or result."""
    return not folder.is_symlink() and any(
        (folder / record).is_file()
        for record in (layout.TRACE, layout.PROGRESS, layout.RESULT)
    )


def find_below(folder: Path, identity: str) -> Path | None:
    """The folder of the node ``identity`` at any depth below ``folder``: a folder named after
    it, or a step's ``run/`` folder whose node has that identity."""
    for current, names, _ in os.walk(folder):
        names[:] = sorted(
            name for name in names if name not in NOT_NODES and not name.startswith(".")
        )
        for name in names:
            candidate = Path(current) / name
            if not _node_folder(candidate):
                continue
            if name == identity or (
                name == "run" and (read(candidate) or {}).get("id") == identity
            ):
                return candidate
    return None


def locate(
    address: str,
    searched: list[Path],
    extra: list[Path] | None = None,
    roots: Iterable[TraceRoot] | None = None,
) -> tuple[Path, Path]:
    """The folder of the node ``address`` names and the ``.concorde`` it was found under.

    ``address`` is a node's folder, absolute or relative to a ``.concorde`` directory, the name of
    a root's top node (in Concorde a task name, a history key or an unbound or lobby run), or the
    identity of a node below one, such as a run or worker run. ``searched`` are the ``.concorde``
    directories to look in, ``extra`` workspace folders to search first for a node below a top
    node, such as the current binding's, and ``roots`` the trace roots (default: the registered).
    """
    roots = _roots(roots)
    candidate = Path(address)
    if candidate.is_absolute() and candidate.is_dir():
        owner = next(
            (root for root in searched if _inside(candidate, root)),
            searched[0] if searched else candidate,
        )
        return candidate, owner
    if address and address not in (".", ".."):
        if "/" in address:
            for concorde in searched:
                joined = concorde / address
                if joined.is_dir() and (
                    (joined / layout.TRACE).is_file() or _is_workspace(joined)
                ):
                    return joined, concorde
        else:
            for concorde in searched:
                for root in _placed(roots, concorde):
                    folder = root.path(concorde) / address
                    if _node_folder(folder):
                        return folder, concorde
            for workspace in extra or []:
                found = find_below(workspace, address)
                if found is not None:
                    return found, _owner(found, searched)
            for concorde in searched:
                for root in _placed(roots, concorde):
                    found = find_below(root.path(concorde), address)
                    if found is not None:
                        return found, concorde
    raise ReadError(
        "unknown_node",
        f"no trace node {address!r} was found; searched the trace roots "
        + (
            ", ".join(f"{root.name} ({root.folder}/)" for root in roots)
            or "(none registered)"
        )
        + " of "
        + ", ".join(root.as_posix() for root in searched)
        + (
            " and the workspace folders " + ", ".join(w.as_posix() for w in extra)
            if extra
            else ""
        ),
    )


def _inside(path: Path, root: Path) -> bool:
    try:
        Path(os.path.realpath(path)).relative_to(os.path.realpath(root))
        return True
    except ValueError:
        return False


def _owner(folder: Path, searched: list[Path]) -> Path:
    return next((root for root in searched if _inside(folder, root)), searched[0])


def listing(
    concorde: Path | Iterable[Path],
    *,
    history: bool = False,
    unbound: bool = False,
    roots: Iterable[TraceRoot] | None = None,
) -> list[dict]:
    """The top nodes of the roots listed always, and with ``history`` or ``unbound`` also of the
    roots listed with that option, under one ``.concorde`` directory or several, without children
    and each once: the roots listed always first, then those of ``--history``, then those of
    ``--unbound``, and within each option the directories in the order given."""
    directories = [concorde] if isinstance(concorde, (str, Path)) else list(concorde)
    wanted = {"always"} | ({"history"} if history else set())
    if unbound:
        wanted.add("unbound")
    found: list[tuple[int, int, Path, Path]] = []
    seen: set[str] = set()
    for position, directory in enumerate(directories):
        for root in _placed(_roots(roots), Path(directory)):
            if root.listed not in wanted:
                continue
            for item in root.top_folders(Path(directory)):
                real = os.path.realpath(item)
                if (item / layout.TRACE).is_file() and real not in seen:
                    seen.add(real)
                    found.append(
                        (LISTINGS.index(root.listed), position, item, Path(directory))
                    )
    found.sort(key=lambda entry: entry[:2])
    return [
        _strip(view(folder, directory, lost=False), 0)
        for _, _, folder, directory in found
    ]


def render(value: dict, indent: int = 0) -> str:
    """A view summarized as an indented text tree: one line per node with its kind, identity,
    status, outcome, duration, rolled-up cost and tokens, what ran and its error's code."""
    rolled = value["rolled_up"]
    parts = [
        f"{'  ' * indent}{value['kind']} {value['id']}: {value['status']}",
    ]
    if value.get("outcome") and value["outcome"] != value["status"]:
        parts.append(f"({value['outcome']})")
    if value.get("duration_seconds") is not None:
        parts.append(f"{value['duration_seconds']:.1f}s")
    if rolled["cost_usd"] or rolled["tokens_in"] or rolled["tokens_out"]:
        parts.append(
            f"cost ${rolled['cost_usd']:.4f}, tokens {rolled['tokens_in']} in / "
            f"{rolled['tokens_out']} out / {rolled['tokens_cache_read']} cache read, "
            f"{rolled['turns']} turns"
        )
    meta = value.get("metadata") or {}
    detail = ", ".join(
        f"{key}={meta[key]}"
        for key in (
            "operation",
            "command",
            "workflow",
            "task_type",
            "worker",
            "model",
            "check",
        )
        if key in meta
    )
    if detail:
        parts.append(f"[{detail}]")
    if value.get("error"):
        parts.append(f"error {value['error'].get('code')}")
    lines = [" ".join(parts)]
    for child in value["children"]:
        lines.append(render(child, indent + 1))
    return "\n".join(lines)


__all__ = [
    "TOTALS",
    "ReadError",
    "concorde_directories",
    "find_below",
    "find_run",
    "listing",
    "locate",
    "render",
    "run_alive",
    "view",
    "workspace_runs",
]
