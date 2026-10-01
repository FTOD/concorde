"""Retention: which ended traces may be removed, by the Tracing configuration.

Only three things are ever removed: an unbound run, or a run of the lobby, that ended longer ago
than ``unbound_days`` and whose run lock nobody holds, whole; a history folder of a task closed longer ago than
``history_days``, whole; and, from a history folder of a task closed longer ago than
``conversation_days``, its conversation records, the transcripts of its task sessions and
worker runs and their event streams. Nothing runs in the background; ``prune`` runs when called,
by ``concorde trace prune`` and at the start of ``task open`` and ``task close``.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..spec.schema import ContractError, validate
from . import layout
from .node import parse_time, read
from .reader import run_alive

DEFAULTS = {"unbound_days": 7, "history_days": None, "conversation_days": 30}
# The conversation records of a history folder, by name at any depth: a transcript, the folder
# Claude Code keeps beside a session's transcript, and an event stream.
CONVERSATION_FILES = ("transcript.jsonl", "events.jsonl")
CONVERSATION_FOLDERS = ("transcript",)
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
    except ContractError as error:
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


def conversation_records(folder: Path) -> list[Path]:
    """The conversation records below a history folder, a folder counting once with its
    content."""
    found: list[Path] = []
    for path in sorted(Path(folder).rglob("*")):
        if any(path.is_relative_to(item) for item in found):
            continue
        if path.is_dir() and not path.is_symlink():
            if path.name in CONVERSATION_FOLDERS:
                found.append(path)
        elif path.name in CONVERSATION_FILES:
            found.append(path)
    return found


def removable(concorde: Path, moment: datetime | None = None) -> list[Path]:
    """What retention may remove now, oldest kinds first: unbound runs and runs of the lobby, then
    history folders, then the conversation records of the history folders it keeps."""
    moment = moment or datetime.now(UTC)
    periods = configuration(concorde)
    found: list[Path] = []
    for parent in (layout.unbound_folder(concorde), layout.lobby_folder(concorde)):
        for folder in sorted(parent.iterdir()) if parent.is_dir() else []:
            record = read(folder)
            if (
                record
                and record.get("ended_at")
                and not run_alive(concorde, record["id"])
                and _expired(record["ended_at"], periods["unbound_days"], moment)
            ):
                found.append(folder)
    history = layout.history_folder(concorde)
    kept = []
    for folder in sorted(history.iterdir()) if history.is_dir() else []:
        record = read(folder)
        if not record:
            continue
        if _expired(record.get("ended_at"), periods["history_days"], moment):
            found.append(folder)
        elif _expired(record.get("ended_at"), periods["conversation_days"], moment):
            kept.append(folder)
    for folder in kept:
        found.extend(conversation_records(folder))
    return found


def prune(
    concorde: Path, *, dry_run: bool = False, moment: datetime | None = None
) -> list[str]:
    """Remove what ``removable`` names, unless ``dry_run``; the removed paths."""
    removed = []
    for path in removable(concorde, moment):
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
