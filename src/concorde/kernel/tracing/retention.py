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
) -> list[Path]:
    """What retention may remove now under ``concorde``: whole top folders, root by root, then the
    conversation records of the top folders it keeps. ``roots`` default to the registered ones."""
    moment = moment or datetime.now(UTC)
    periods = configuration(concorde)
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


def prune(
    concorde: Path,
    *,
    dry_run: bool = False,
    moment: datetime | None = None,
    roots: Iterable[TraceRoot] | None = None,
) -> list[str]:
    """Remove what ``removable`` names, unless ``dry_run``; the removed paths."""
    removed = []
    for path in removable(concorde, moment, roots):
        if not dry_run:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        removed.append(path.as_posix())
    return removed


__all__ = [
    "CONFIGURATION_SCHEMA",
    "DEFAULTS",
    "ConfigError",
    "configuration",
    "conversation_records",
    "prune",
    "removable",
]
