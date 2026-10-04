"""Retention: which ended traces may be removed, root by root, by the Tracing configuration.

Only the registered trace roots are pruned, each by the periods registered with it: a top folder
whose node ended longer ago than the root's ``period`` and that nobody still writes is removed
whole; from one that ended longer ago than its ``conversation_period`` only its conversation
records go. In Concorde that removes the unbound runs and the runs of the lobby after
``unbound_days``, the history folders after ``history_days`` and their transcripts after
``conversation_days``. Nothing runs in the background; ``prune`` runs when called, by
``concorde trace prune`` and by a part that registers a root, as Tasks does at the start of
``task open`` and ``task close``. A current root without periods is never pruned.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable

from ..refusal import KernelError
from ..schema import validate
from . import layout, locks
from .node import parse_time, read
from .roots import TraceRoot, registered

DEFAULTS = {"unbound_days": 7, "history_days": None, "conversation_days": 30}
_DAYS = {"anyOf": [{"type": "null"}, {"type": "integer", "minimum": 0}]}

# contract.tracing.configuration, version 3
CONFIGURATION_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "retention"],
    "properties": {
        "schema_version": {"const": 1},
        "retention": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unbound_days", "history_days"],
            "properties": {
                "unbound_days": _DAYS,
                "history_days": _DAYS,
                "conversation_days": _DAYS,
            },
        },
    },
}


class ConfigError(Exception):
    """A Tracing configuration that cannot be read or breaks its contract."""

    def __init__(self, message: str, field: str = ""):
        super().__init__(message)
        self.code = "config_invalid"
        self.field = field


def configuration(concorde: Path) -> dict:
    """The retention periods of ``concorde/tracing.json``, each period it leaves out, or all of
    them without the file, by default."""
    path = Path(concorde) / layout.CONFIGURATION
    if not path.exists():
        return dict(DEFAULTS)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigError(
            f"the Tracing configuration {path} cannot be read: {error}"
        ) from error
    try:
        validate(value, CONFIGURATION_SCHEMA)
    except KernelError as error:
        raise ConfigError(
            f"the Tracing configuration {path} breaks its contract at "
            f"{error.field or 'the top'}: {error}",
            error.field,
        ) from error
    return {**DEFAULTS, **value["retention"]}


def _expired(ended: str | None, days: int | None, moment: datetime) -> bool:
    if days is None:
        return False
    when = parse_time(ended)
    return when is not None and moment - when > timedelta(days=days)


def conversation_records(folder: Path, root: TraceRoot) -> list[Path]:
    """The conversation records below a top folder of ``root``, a folder counting once with its
    content."""
    found: list[Path] = []
    for path in sorted(Path(folder).rglob("*")):
        if any(path.is_relative_to(item) for item in found):
            continue
        if path.is_dir() and not path.is_symlink():
            if path.name in root.conversation_folders:
                found.append(path)
        elif path.name in root.conversation_files:
            found.append(path)
    return found


def removable(
    concorde: Path,
    moment: datetime | None = None,
    roots: Iterable[TraceRoot] | None = None,
    periods: dict | None = None,
) -> list[Path]:
    """What retention may remove now under ``concorde``: whole top folders, root by root, then the
    conversation records of the top folders it keeps. ``roots`` default to the registered ones,
    ``periods`` to the configuration of ``concorde``."""
    moment = moment or datetime.now(UTC)
    periods = configuration(concorde) if periods is None else periods
    found: list[Path] = []
    kept: list[tuple[TraceRoot, Path]] = []
    for root in registered() if roots is None else roots:
        for folder in root.top_folders(concorde):
            record = read(folder)
            if not record:
                continue
            ended = record.get(root.ended)
            if root.alive_lock and (
                not isinstance(record.get("id"), str)
                or locks.held(layout.lock_file(concorde, root.alive_lock, record["id"]))
            ):
                continue
            if root.period and _expired(ended, periods[root.period], moment):
                found.append(folder)
            elif root.conversation_period and _expired(
                ended, periods[root.conversation_period], moment
            ):
                kept.append((root, folder))
    for root, folder in kept:
        found.extend(conversation_records(folder, root))
    return found


def _remove(path: Path) -> str | None:
    """Remove ``path``, a folder with its content; what the operating system refused, if any.

    A folder's own ``trace.json`` goes last, so that a folder not removed wholly is still a node
    the next prune finds and tries again.
    """
    refused: list[str] = []

    def failed(function, name, problem) -> None:
        error = problem[1] if isinstance(problem, tuple) else problem
        refused.append(f"{name}: {error}")

    def remove(target: Path) -> None:
        try:
            if target.is_dir() and not target.is_symlink():
                if sys.version_info >= (3, 12):
                    shutil.rmtree(target, onexc=failed)
                else:
                    shutil.rmtree(target, onerror=failed)
            else:
                target.unlink(missing_ok=True)
        except OSError as error:
            refused.append(f"{target}: {error}")

    if path.is_dir() and not path.is_symlink():
        try:
            entries = sorted(path.iterdir())
        except OSError as error:
            entries = []
            refused.append(f"{path}: {error}")
        for entry in entries:
            if entry.name != layout.TRACE:
                remove(entry)
    if not refused:
        remove(path)
    if not refused:
        return None
    more = f" and {len(refused) - 1} more" if len(refused) > 1 else ""
    return refused[0] + more


def prune(
    concorde: Path,
    *,
    dry_run: bool = False,
    moment: datetime | None = None,
    roots: Iterable[TraceRoot] | None = None,
    periods: dict | None = None,
) -> dict:
    """Remove what ``removable`` names, unless ``dry_run``: ``{"removed": [<path>…], "failed":
    [{"path", "error"}…]}``, a path the operating system did not let go wholly being failed, and
    tried again at the next prune."""
    removed: list[str] = []
    failed: list[dict] = []
    for path in removable(concorde, moment, roots, periods):
        problem = None if dry_run else _remove(path)
        if problem is None:
            removed.append(path.as_posix())
        else:
            failed.append({"path": path.as_posix(), "error": problem})
    return {"removed": removed, "failed": failed}


__all__ = [
    "CONFIGURATION_SCHEMA",
    "DEFAULTS",
    "ConfigError",
    "configuration",
    "conversation_records",
    "prune",
    "removable",
]
