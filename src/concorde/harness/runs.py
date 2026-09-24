"""Run directories and run records under the primary worktree's ``.concorde/runs/``."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

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


def create_run(worktree: Path, prefix: str = "w") -> tuple[str, RunPaths]:
    """A fresh run directory with its layout, in the primary worktree."""
    runs = primary_root(worktree) / ".concorde/runs"
    while True:
        run_id = new_run_id(prefix)
        root = runs / run_id
        try:
            root.mkdir(parents=True)
            break
        except FileExistsError:
            continue
    for name in ("control", "config", "home", "tmp", "work", "checks"):
        (root / name).mkdir()
    return run_id, RunPaths(root, _short_tmp(run_id))


def _short_tmp(run_id: str) -> Path:
    """A private directory with a short path, under ``/tmp`` or, where ``/tmp`` is read-only (a
    check boundary, say), under the system temporary directory."""
    prefix = f"concorde-{run_id[-6:]}-"
    try:
        return Path(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))
    except OSError:
        return Path(tempfile.mkdtemp(prefix=prefix))


def remove_short_tmp(paths: RunPaths) -> None:
    """Remove a run's short temporary directory once the worker has ended."""
    if paths.short_tmp is not None:
        shutil.rmtree(paths.short_tmp, ignore_errors=True)


def write_record(paths: RunPaths, record: dict) -> Path:
    target = paths.root / "record.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    temporary.replace(target)
    return target


def read_record(root: Path, run_id: str) -> dict:
    return json.loads((root / ".concorde/runs" / run_id / "record.json").read_text())


__all__ = [
    "create_run",
    "now",
    "primary_root",
    "read_record",
    "remove_short_tmp",
    "write_record",
]
