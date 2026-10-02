"""Trace nodes: the uniform ``trace.json`` every level of work writes in its own folder.

A producer creates a ``Node`` for the folder its parent gave it, writes it with ``start`` before
the work begins, may ``update`` it while it runs and writes it a last time with ``finish``. Every
write is checked against the node contract (``contract.tracing.node``) and the producer's content
against the type it registered, and replaces the file atomically. A failed write of the file never
changes the work it records; a record that breaks its contract is a defect of its producer and
raises.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from ...spec.schema import ContractError, validate
from ...spec.typed_data import TypedDataError, typed, validate_typed
from . import layout

KINDS = (
    "task",
    "session",
    "merge",
    "merge-check",
    "workflow",
    "step",
    "run",
    "check",
    "worker-run",
    "worker-round",
)
STATUSES = ("running", "ok", "blocked", "failed", "unknown")
USAGE_FIELDS = (
    "tokens_in",
    "tokens_out",
    "tokens_cache_read",
    "tokens_cache_write",
    "cost_usd",
    "turns",
    "duration_seconds",
)
METADATA = (
    "task",
    "workspace",
    "modules",
    "branch",
    "base_commit",
    "commit",
    "operation",
    "command",
    "workflow",
    "mode",
    "task_type",
    "worker",
    "backend",
    "model",
    "reasoning",
    "context_identity",
    "grant_digest",
    "brief_digest",
    "settings_digest",
    "check",
    "module",
    "concorde_commit",
    "protocol_version",
)
RELATIONS = ("input", "cites", "commit", "found_commit")
_TEXT = {"$ref": "#/$defs/text"}
_COUNT = {"anyOf": [{"type": "null"}, {"type": "integer", "minimum": 0}]}
_AMOUNT = {"anyOf": [{"type": "null"}, {"type": "number", "minimum": 0}]}

# contract.tracing.node, version 3
NODE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "id",
        "kind",
        "started_at",
        "ended_at",
        "status",
        "outcome",
        "usage",
        "error",
        "metadata",
        "artifacts",
        "references",
        "content",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "id": {"type": "string", "minLength": 1},
        "kind": {"enum": list(KINDS)},
        "started_at": {"type": "string", "minLength": 1},
        "ended_at": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1}]},
        "status": {"enum": list(STATUSES)},
        "outcome": {
            "anyOf": [
                {"type": "null"},
                {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
            ]
        },
        "usage": {"$ref": "#/$defs/usage"},
        "error": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "metadata": {"$ref": "#/$defs/metadata"},
        "artifacts": {"type": "array", "items": {"$ref": "#/$defs/artifact"}},
        "references": {"type": "array", "items": {"$ref": "#/$defs/reference"}},
        "content": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/typed"}]},
    },
    "$defs": {
        "count": _COUNT,
        "amount": _AMOUNT,
        "usage": {
            "type": "object",
            "additionalProperties": False,
            "required": list(USAGE_FIELDS),
            "properties": {
                **{
                    name: {"$ref": "#/$defs/count"}
                    for name in USAGE_FIELDS
                    if name not in ("cost_usd", "duration_seconds")
                },
                "cost_usd": {"$ref": "#/$defs/amount"},
                "duration_seconds": {"$ref": "#/$defs/amount"},
            },
        },
        "text": {"type": "string", "minLength": 1},
        "metadata": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: (
                    {"type": "array", "items": _TEXT} if name == "modules" else _TEXT
                )
                for name in METADATA
            },
        },
        "artifact": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "path", "digest"],
            "properties": {
                "id": _TEXT,
                "path": {"type": "string", "minLength": 1, "format": "project-path"},
                "digest": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                    ]
                },
            },
        },
        "reference": {
            "type": "object",
            "additionalProperties": False,
            "required": ["relation", "target"],
            "properties": {"relation": {"enum": list(RELATIONS)}, "target": _TEXT},
        },
        "typed": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type_id", "schema_version", "data"],
            "properties": {
                "type_id": _TEXT,
                "schema_version": {"type": "integer", "minimum": 1},
                "data": {"type": "object"},
            },
        },
    },
}


class TraceError(Exception):
    """A node its producer asked to write that breaks the node contract or its content type."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now() -> str:
    """The UTC time with microseconds, so that nodes started within one second still sort."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_time(text: str | None) -> datetime | None:
    if not text:
        return None
    for pattern in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text, pattern).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def seconds_between(start: str | None, end: str | None) -> float | None:
    began, ended = parse_time(start), parse_time(end)
    if began is None or ended is None:
        return None
    return round(max(0.0, (ended - began).total_seconds()), 3)


def usage(**fields) -> dict:
    """A usage record: every field null unless given."""
    unknown = set(fields) - set(USAGE_FIELDS)
    if unknown:
        raise ValueError(f"unknown usage fields: {', '.join(sorted(unknown))}")
    return {name: fields.get(name) for name in USAGE_FIELDS}


def digest(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def artifact(
    folder: Path, identity: str, relative: str, *, measured: bool = True
) -> dict:
    """An artifact entry of ``folder``: ``relative`` names a file of it; its digest when
    ``measured`` and the file exists, else null."""
    return {
        "id": identity,
        "path": relative,
        "digest": digest(Path(folder) / relative) if measured else None,
    }


def read(folder: Path) -> dict | None:
    """The record of the node in ``folder``, or None when it has none or it cannot be read."""
    try:
        value = json.loads((Path(folder) / layout.TRACE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def check(record: dict) -> dict:
    """``record`` if it satisfies the node contract and its content its type; else TraceError."""
    try:
        validate(record, NODE_SCHEMA)
    except (ContractError, TypedDataError) as error:
        raise TraceError(
            "node_invalid",
            f"the trace node {record.get('kind')} {record.get('id')} breaks the node contract at "
            f"{getattr(error, 'field', '') or 'the top'}: {error}",
        ) from error
    if record["content"] is not None:
        try:
            validate_typed(record["content"], field="content")
        except TypedDataError as error:
            raise TraceError(
                "content_invalid",
                f"the content of trace node {record['kind']} {record['id']} breaks its type "
                f"{record['content'].get('type_id')}: {error}",
            ) from error
    return record


def write(folder: Path, record: dict) -> Path:
    """Check ``record`` and replace ``folder``'s ``trace.json`` with it atomically."""
    check(record)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / layout.TRACE
    handle, temporary = tempfile.mkstemp(dir=folder, prefix=".trace-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(
                json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            )
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


class Node:
    """One trace node its producer writes: at its start, while it runs and at its end."""

    def __init__(
        self,
        folder: Path,
        identity: str,
        kind: str,
        *,
        metadata: dict | None = None,
        references: list[dict] | None = None,
        content_type: str | None = None,
        content: dict | None = None,
        started_at: str | None = None,
    ):
        self.folder = Path(folder)
        self.content_type = content_type
        self.record = {
            "schema_version": 1,
            "id": identity,
            "kind": kind,
            "started_at": started_at or now(),
            "ended_at": None,
            "status": "running",
            "outcome": None,
            "usage": usage(),
            "error": None,
            "metadata": {},
            "artifacts": [],
            "references": list(references or []),
            "content": None,
        }
        self._artifacts: list[tuple[str, str]] = []
        self.set_metadata(**(metadata or {}))
        if content is not None:
            self.set_content(content)
        # The last error writing the file, which never changes the work recorded.
        self.failure: OSError | None = None

    @property
    def started_at(self) -> str:
        return self.record["started_at"]

    def set_metadata(self, **values) -> None:
        for name, value in values.items():
            if name not in METADATA:
                raise TraceError(
                    "node_invalid", f"{name} is no metadata dimension of a node"
                )
            if value is None or value == [] or value == "":
                self.record["metadata"].pop(name, None)
            else:
                self.record["metadata"][name] = (
                    list(value) if isinstance(value, (list, tuple)) else value
                )

    def set_content(self, data: dict) -> None:
        if self.content_type is None:
            raise TraceError(
                "node_invalid", "the node has no content type to hold its content"
            )
        try:
            self.record["content"] = typed(self.content_type, copy.deepcopy(data))
        except TypedDataError as error:
            raise TraceError(
                "content_invalid",
                f"the content of trace node {self.record['kind']} {self.record['id']} breaks "
                f"its type {self.content_type}: {error}",
            ) from error

    def refer(self, relation: str, target: str) -> None:
        reference = {"relation": relation, "target": target}
        if reference not in self.record["references"]:
            self.record["references"].append(reference)

    def keep(self, identity: str, relative: str, *, measured: bool = True) -> None:
        """Name a file of the folder as an artifact; its digest is taken when the node ends,
        unless ``measured`` is False for a file its writer completes only after that."""
        if all(item[0] != identity for item in self._artifacts):
            self._artifacts.append((identity, relative, measured))

    def _write(self, *, measured: bool) -> None:
        self.record["artifacts"] = [
            artifact(self.folder, identity, relative, measured=measured and own)
            for identity, relative, own in self._artifacts
            if (self.folder / relative).exists()
        ]
        try:
            write(self.folder, self.record)
            self.failure = None
        except OSError as error:
            self.failure = error

    def start(self) -> Node:
        self._write(measured=False)
        return self

    def update(self, *, content: dict | None = None, **metadata) -> None:
        if metadata:
            self.set_metadata(**metadata)
        if content is not None:
            self.set_content(content)
        self._write(measured=False)

    def finish(
        self,
        status: str,
        *,
        outcome: str | None = None,
        error: dict | None = None,
        used: dict | None = None,
        content: dict | None = None,
        ended_at: str | None = None,
        **metadata,
    ) -> dict:
        """Write the node's end; ``used`` holds the node's own usage fields."""
        if metadata:
            self.set_metadata(**metadata)
        if content is not None:
            self.set_content(content)
        ended = ended_at or now()
        own = usage(**(used or {}))
        if own["duration_seconds"] is None and status != "unknown":
            own["duration_seconds"] = seconds_between(self.record["started_at"], ended)
        self.record.update(
            ended_at=None if status == "unknown" else ended,
            status=status,
            outcome=outcome
            or (status if status in ("ok", "blocked", "failed") else None),
            usage=own,
            error=error if status in ("blocked", "failed") else None,
        )
        self._write(measured=True)
        return self.record


@lru_cache(maxsize=1)
def concorde_commit() -> str | None:
    """The commit of the Concorde code running: its Git checkout's ``HEAD``, or the commit its
    installation receipt records; None when neither is known."""
    package = Path(__file__).resolve().parents[2]
    try:
        found = subprocess.run(
            ["git", "-C", str(package), "rev-parse", "--verify", "--quiet", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    for parent in package.parents:
        receipt = parent / "install.json"
        if parent.name == layout.CONCORDE and receipt.is_file():
            try:
                commit = json.loads(receipt.read_text()).get("source_commit")
            except (OSError, ValueError):
                return None
            return commit if isinstance(commit, str) and commit else None
    return None


def protocol_version(worktree: Path) -> str | None:
    """The Spec Protocol version the project configuration of ``worktree`` binds, if readable."""
    try:
        config = json.loads(
            (layout.concorde_of(worktree) / "config.json").read_text(encoding="utf-8")
        )
        version = (config.get("protocol") or {}).get("version")
    except (OSError, ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and version else None


__all__ = [
    "KINDS",
    "METADATA",
    "NODE_SCHEMA",
    "STATUSES",
    "USAGE_FIELDS",
    "Node",
    "TraceError",
    "artifact",
    "check",
    "concorde_commit",
    "digest",
    "now",
    "parse_time",
    "protocol_version",
    "read",
    "seconds_between",
    "usage",
    "write",
]
