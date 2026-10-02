"""The runs of a task's workspace, read through Execution's published formats.

Execution is an optional integration of Tasks: Tasks never imports it, and reads what its runs
recorded through the formats Execution's Spec and Tracing's define (contract.execution.run-result,
the run progress file, the run store's layout and Tracing's run lock). A bound run is a trace node
in the workspace folder its binding names, in ``runs/<run-id>/`` or ``run/`` of a workflow step's
node, once it holds its workspace's lock, and until then in the lobby ``lobby/<run-id>/`` of the
binding's ``.concorde``; its runner holds its run lock ``locks/runs/<run-id>.lock`` from before its
first progress file until after its result. Where the execution part is not installed none of these
exists, so a workspace simply has no run.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ...kernel.tracing import layout, locks, reader

# A run identity (contract.execution.run-result's run_id).
RUN_ID = re.compile(r"^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$")
# The lobby of a ``.concorde``, where a bound run lies until it holds its workspace's lock.
LOBBY = "lobby"


def _json(path: Path) -> dict | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def progress(folder: Path) -> dict | None:
    """A run's progress file, or None when it has none or it does not read."""
    return _json(Path(folder) / layout.PROGRESS)


def run_lock(concorde: Path, run_id: str) -> Path:
    return layout.lock_file(concorde, "run", run_id)


def runner_alive(concorde: Path, run_id: str) -> bool:
    """Whether the runner of ``run_id`` still holds its run lock, from any PID namespace."""
    return locks.held(run_lock(concorde, run_id))


def find(concorde: Path, workspace: Path, run_id: str) -> Path | None:
    """The folder of ``run_id`` in the workspace folder ``workspace``, or in the lobby; None when
    neither holds it."""
    if not run_id or not RUN_ID.match(run_id):
        return None
    found = reader.find_run(workspace, run_id)
    if found is not None:
        return found
    lobby = Path(concorde) / LOBBY / run_id
    if lobby.is_dir():
        return lobby
    # The run may have entered its workspace between the two reads.
    return reader.find_run(workspace, run_id)


def load_result(concorde: Path, workspace: Path, run_id: str) -> dict | None:
    """The saved result of ``run_id``, or None when it has none (yet) or it does not read."""
    folder = find(concorde, workspace, run_id)
    return _json(folder / layout.RESULT) if folder else None


def result_path(concorde: Path, workspace: Path, run_id: str) -> Path:
    """Where the result of ``run_id`` is, or would be for a run started directly."""
    folder = find(concorde, workspace, run_id) or layout.run_folder(workspace, run_id)
    return folder / layout.RESULT


def waiting(concorde: Path, name: str) -> list[Path]:
    """The lobby folders of the runs of the workspace ``name`` whose runner still runs: those
    waiting for its lock. A run refused before it held the lock never entered the workspace."""
    lobby = Path(concorde) / LOBBY
    try:
        folders = sorted(item for item in lobby.iterdir() if item.is_dir())
    except OSError:
        return []
    return [
        folder
        for folder in folders
        if RUN_ID.match(folder.name)
        and (progress(folder) or {}).get("workspace") == name
        and runner_alive(concorde, folder.name)
        and not (folder / layout.RESULT).exists()
    ]


def folders(concorde: Path, workspace: Path, name: str) -> list[Path]:
    """The folders of every run of the workspace ``name``, those waiting in the lobby included."""
    return [*reader.workspace_runs(workspace), *waiting(concorde, name)]


def _status(concorde: Path, workspace: Path, run_id: str) -> str:
    """``running`` or ``lost`` for a run without a result: the result is written before the run
    lock is released, so one whose lock nobody holds ended without writing it."""
    if runner_alive(concorde, run_id):
        return "running"
    result = load_result(concorde, workspace, run_id)
    return result["status"] if result and "status" in result else "lost"


def workspace_runs(concorde: Path, workspace: Path, name: str) -> list[dict]:
    """Every run recorded for the workspace ``name``, oldest first, with those waiting in the
    lobby for its lock: each its identity, kind, name, Modules, status (``running``, ``lost`` or
    its result's) and times, from its result when it has one, else from its progress file."""
    found = []
    for folder in folders(concorde, workspace, name):
        result = _json(folder / layout.RESULT)
        source = result or progress(folder)
        if not source or source.get("workspace") != name:
            continue
        run_id = source.get("run_id") or folder.name
        if not RUN_ID.match(str(run_id)):
            continue
        found.append(
            {
                "run_id": run_id,
                "kind": source.get("kind"),
                "name": source.get("name"),
                "modules": list(source.get("modules") or []),
                "status": result["status"]
                if result
                else _status(concorde, workspace, run_id),
                "started_at": source.get("started_at") or "",
                "finished_at": (result or {}).get("finished_at"),
            }
        )
    found.sort(key=lambda item: (item["started_at"], item["run_id"]))
    return found


__all__ = [
    "LOBBY",
    "RUN_ID",
    "find",
    "folders",
    "load_result",
    "progress",
    "result_path",
    "run_lock",
    "runner_alive",
    "waiting",
    "workspace_runs",
]
