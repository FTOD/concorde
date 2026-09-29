"""Worker run directories and runtime directories.

A worker run's run directory is its trace node ``workers/<run-id>/`` inside the trace node of the
run that launched it; its runtime directory is a short private directory under ``/tmp`` holding
what the worker needs only while it runs, removed when the run ends.
"""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..tracing import layout
from .settings import RunPaths


def primary_root(worktree: Path) -> Path:
    """The primary worktree of the repository ``worktree`` belongs to."""
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(os.path.realpath(common)).parent


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def new_run_id(prefix: str = "w") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{prefix}-{stamp}-{secrets.token_hex(3)}"


def create_run(parent: Path, prefix: str = "w") -> tuple[str, RunPaths]:
    """A fresh run directory ``workers/<run-id>/`` below the trace node ``parent``, and a fresh
    runtime directory with its layout."""
    while True:
        run_id = new_run_id(prefix)
        trace = layout.worker_folder(parent, run_id)
        try:
            trace.mkdir(parents=True)
            break
        except FileExistsError:
            continue
    root = _runtime(run_id)
    for name in ("control", "config", "home", "tmp", "work"):
        (root / name).mkdir()
    return run_id, RunPaths(root, trace, run_id)


def _runtime(run_id: str) -> Path:
    """A private directory with a short path, under ``/tmp`` or, where ``/tmp`` is read-only (a
    check boundary, say), under the system temporary directory."""
    prefix = f"concorde-{run_id[-6:]}-"
    try:
        return Path(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))
    except OSError:
        return Path(tempfile.mkdtemp(prefix=prefix))


def read_record(root: Path, run_id: str) -> dict:
    """The run record of worker run ``run_id`` as ``run_worker`` returned it, rebuilt from its
    trace node and its rounds' nodes, found below the ``.concorde`` or run folder ``root``.

    ``FileNotFoundError`` when no such worker run is traced there.
    """
    from ..tracing import node as trace
    from ..tracing import reader

    root = Path(root)
    folder = next(iter(root.glob(f"**/workers/{run_id}")), None)
    if folder is None:
        try:
            folder, _ = reader.locate(run_id, [root])
        except reader.ReadError as error:
            raise FileNotFoundError(str(error)) from error
    node = trace.read(folder)
    if node is None:
        raise FileNotFoundError(f"{folder} holds no trace node of worker run {run_id}")
    data = node["content"]["data"]
    meta = node["metadata"]
    rounds = []
    for item in sorted(
        (folder / "rounds").glob("*"),
        key=lambda path: int(path.name) if path.name.isdigit() else 0,
    ):
        round_node = trace.read(item)
        if round_node is None:
            continue
        content = round_node["content"]["data"]
        entry = {
            "round": content["round"],
            "prompt": content["prompt"],
            "session": content["session"],
            "exit": content["exit"],
            "duration": round_node["usage"]["duration_seconds"],
            "usage": round_node["usage"],
            **content["agent"],
        }
        if content["audit"] is not None:
            entry["audit"] = content["audit"]
        if content["checks"]:
            entry["checks"] = [
                {**check, "log": (item / check["log"]).as_posix()}
                for check in content["checks"]
            ]
        if content["validation"] is not None:
            entry["validation"] = content["validation"]
        rounds.append(entry)
    return {
        "run_id": node["id"],
        "task_type": data["task_type"],
        "backend": meta.get("backend"),
        "backend_source": data["backend_source"],
        "operation": meta.get("operation"),
        "worker": meta.get("worker"),
        "model": meta.get("model"),
        "reasoning": meta.get("reasoning"),
        "context_identity": meta.get("context_identity"),
        "grant_digest": meta.get("grant_digest"),
        "settings_digest": meta.get("settings_digest"),
        "brief_digest": meta.get("brief_digest"),
        "tools": ",".join(data["tools"]) if data["tools"] is not None else None,
        "started_at": node["started_at"],
        "ended_at": node["ended_at"],
        "rounds": rounds,
        "transcript": (folder / data["transcript"]).as_posix()
        if data["transcript"]
        else None,
        "worker_result": data["worker_result"],
        "pending_created": data["pending_created"],
        "pending_removed": data["pending_removed"],
        "deleted": data["deleted"],
        "deletions_refused": data["deletions_refused"],
        "status": node["status"],
        "error": node["error"],
        "run_directory": folder.as_posix(),
    }


def remove_runtime(paths: RunPaths) -> None:
    """Remove a run's runtime directory, with its credential copies, once the worker has ended."""
    shutil.rmtree(paths.root, ignore_errors=True)


__all__ = [
    "create_run",
    "new_run_id",
    "now",
    "primary_root",
    "read_record",
    "remove_runtime",
]
