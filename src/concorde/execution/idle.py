"""The execution part's idle check, which its part registration names: the runs still running.

The installer asks it before it replaces the Framework copy, since replacing it under a running
Operation or execution command would change the code that run executes halfway through. A run is
running while its runner holds its run lock; the runs are described with their run progress files,
wherever the run store keeps them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..kernel.tracing import layout, locks


def _run_progress(concorde: Path, run_ids: set[str]) -> dict[str, tuple[Path, dict]]:
    """The progress file of each run of ``run_ids`` found below ``concorde``, wherever the run
    store placed its node, with what it holds, by run identity. The run's node folder is named
    after it or, for a run a workflow step started, is the step's ``run/``."""
    found: dict[str, tuple[Path, dict]] = {}
    for current, names, files in os.walk(concorde):
        names[:] = sorted(name for name in names if name != layout.LOCKS)
        folder = Path(current)
        if layout.PROGRESS not in files:
            continue
        if folder.name not in run_ids and folder.name != "run":
            continue
        progress = folder / layout.PROGRESS
        try:
            state = json.loads(progress.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(state, dict) and state.get("kind") in ("operation", "command"):
            identity = str(state.get("run_id") or folder.name)
            if identity in run_ids:
                found[identity] = (progress, state)
    return found


def active_runs(project) -> list[str]:
    """Every run in ``project`` whose runner still holds its run lock, described for a refusal
    with its progress file."""
    project = Path(project)
    found = []
    concorde = project / layout.CONCORDE
    runs = layout.locks_folder(concorde) / layout.LOCK_KINDS["run"]
    held = []
    for path in sorted(runs.glob("*.lock")) if runs.is_dir() else []:
        # The run lock, not a process identifier, which a runner in another PID namespace
        # records meaninglessly.
        holder = locks.holder(path)
        if holder is not None:
            held.append((path, holder))
    progress = _run_progress(concorde, {path.stem for path, _ in held}) if held else {}
    for path, holder in held:
        lock = path.relative_to(project).as_posix()
        known = progress.get(path.stem)
        if known is None:
            found.append(f"run {path.stem} (held by {holder}, run lock {lock})")
            continue
        file, state = known
        found.append(
            f"{state.get('kind')} run {path.stem} ({state.get('name')}, workspace "
            f"{state.get('workspace') or 'none'}, held by {holder}, run lock {lock}, "
            f"progress {file.relative_to(project).as_posix()})"
        )
    return found


__all__ = ["active_runs"]
