"""Reading traces: find a node, walk its subtree, roll its usage up, tell a lost run.

Nothing here writes. A node's children are the trace nodes in the folders below its own, the
nearest ones on each path; a task's ``workspace/`` folder, which Execution fills and which has no
record of its own, is shown as a ``workspace`` node. A node that says it runs is ``lost`` when it is
a run whose run lock nobody holds, or lies below such a run.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from . import layout, locks
from .node import USAGE_FIELDS, parse_time, read, seconds_between

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
    names = [
        item["metadata"].get("workspace")
        for item in children
        if item["metadata"].get("workspace")
    ]
    starts = [item["started_at"] for item in children if item["started_at"]]
    running = any(item["status"] in ("running", "lost") for item in children)
    ends = [item["ended_at"] for item in children if item["ended_at"]]
    return {
        "id": names[0] if names else folder.parent.name,
        "kind": "workspace",
        "started_at": min(starts) if starts else None,
        "ended_at": None if running or not ends else max(ends),
        "status": "running" if running else ("ok" if children else "unknown"),
        "outcome": None,
        "usage": {name: None for name in USAGE_FIELDS},
        "error": None,
        "metadata": {"workspace": names[0]} if names else {},
        "references": [],
    }


def _now() -> datetime:
    return datetime.now(UTC)


def view(
    folder: Path,
    concorde: Path,
    *,
    depth: int | None = None,
    lost: bool = False,
) -> dict:
    """The view of the node in ``folder`` and its subtree (contract.tracing.view).

    ``concorde`` is the ``.concorde`` whose ``locks/`` holds the run locks of the runs below.
    ``lost`` says an ancestor run was found lost, which makes every running node below lost too.
    """
    folder = Path(folder)
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


def roots(here: Path) -> list[Path]:
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


def _task_like(concorde: Path) -> list[Path]:
    """Every current task folder and history folder under ``concorde``."""
    found = []
    for parent in (layout.tasks_folder(concorde), layout.history_folder(concorde)):
        try:
            found.extend(sorted(item for item in parent.iterdir() if item.is_dir()))
        except OSError:
            continue
    return found


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


def _run_folders(concorde: Path) -> list[Path]:
    found: list[Path] = []
    for task in _task_like(concorde):
        found.extend(workspace_runs(layout.workspace_folder(task)))
    try:
        found.extend(
            sorted(
                item
                for item in layout.unbound_folder(concorde).iterdir()
                if item.is_dir()
            )
        )
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


def locate(
    address: str, searched: list[Path], extra: list[Path] | None = None
) -> tuple[Path, Path]:
    """The folder of the node ``address`` names and the ``.concorde`` it was found under.

    ``address`` is a task name, a history key, a run or worker run identity, or a folder. ``extra``
    are workspace folders to search for runs before the roots, such as the current binding's.
    """
    candidate = Path(address)
    if candidate.is_absolute() and candidate.is_dir():
        owner = next(
            (root for root in searched if _inside(candidate, root)),
            searched[0] if searched else candidate,
        )
        return candidate, owner
    for root in searched:
        joined = root / address
        if (
            address
            and not address.startswith("r-")
            and not address.startswith("w-")
            and joined.is_dir()
            and ((joined / layout.TRACE).is_file() or _is_workspace(joined))
        ):
            return joined, root
    if address.startswith("r-"):
        for workspace in extra or []:
            found = find_run(workspace, address)
            if found is not None:
                return found, _owner(found, searched)
        for root in searched:
            for folder in (
                layout.unbound_run_folder(root, address),
                layout.lobby_run_folder(root, address),
            ):
                if folder.is_dir():
                    return folder, root
            for task in _task_like(root):
                found = find_run(layout.workspace_folder(task), address)
                if found is not None:
                    return found, root
    elif address.startswith("w-"):
        for root in searched:
            runs = [
                *(r for w in (extra or []) for r in workspace_runs(w)),
                *_run_folders(root),
            ]
            for run in runs:
                worker = layout.worker_folder(run, address)
                if worker.is_dir():
                    return worker, root
    else:
        for root in searched:
            for parent in (layout.tasks_folder(root), layout.history_folder(root)):
                folder = parent / address
                if (folder / layout.TRACE).is_file():
                    return folder, root
    raise ReadError(
        "unknown_node",
        f"no trace node {address!r} was found; searched the current tasks, the history, the "
        "unbound runs and the lobby of "
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
    concorde: Path, *, history: bool = False, unbound: bool = False
) -> list[dict]:
    """The current tasks, and when asked the history and the unbound runs, without children."""
    folders: list[Path] = []
    parents = [layout.tasks_folder(concorde)]
    if history:
        parents.append(layout.history_folder(concorde))
    if unbound:
        parents.append(layout.unbound_folder(concorde))
    for parent in parents:
        try:
            folders.extend(
                sorted(
                    item for item in parent.iterdir() if (item / layout.TRACE).is_file()
                )
            )
        except OSError:
            continue
    return [_strip(view(folder, concorde), 0) for folder in folders]


def render(value: dict, indent: int = 0) -> str:
    """A view as an indented text tree."""
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
    lines = [" ".join(parts)]
    for child in value["children"]:
        lines.append(render(child, indent + 1))
    return "\n".join(lines)


__all__ = [
    "TOTALS",
    "ReadError",
    "find_run",
    "listing",
    "locate",
    "render",
    "roots",
    "run_alive",
    "view",
    "workspace_runs",
]
