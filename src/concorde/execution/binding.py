"""The workspace binding: the one file through which the execution core learns its workspace.

Whoever prepares a workspace (Tasks, for a task worktree) writes ``.concorde/workspace.json`` at
the workspace's root; every Operation, recorded command and workflow started there reads it and
never writes it. A worktree without the file is unbound: its runs work on that worktree alone,
record no workspace and may only read.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from ..spec.schema import ContractError, validate

BINDING = ".concorde/workspace.json"
NAME_PATTERN = "^[a-z0-9][a-z0-9-]{0,47}$"
TEXT = {"type": "string", "minLength": 1}
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}

# contract.execution.workspace-binding, version 1
BINDING_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "workspace",
        "root",
        "branch",
        "base_commit",
        "goal",
        "modules",
        "records",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "workspace": {"type": "string", "pattern": NAME_PATTERN},
        "root": TEXT,
        "branch": TEXT,
        "base_commit": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
        "goal": TEXT,
        "modules": {"type": "array", "minItems": 1, "items": MODULE_ID},
        "records": TEXT,
    },
}


class BindingError(Exception):
    """A workspace binding that cannot be read or trusted; ``code`` names why."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def toplevel(here: Path) -> Path:
    """The root of the worktree ``here`` lies in; ``BindingError`` outside a Git worktree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise BindingError(
            "not_a_worktree", f"git rev-parse could not run in {here}: {error}"
        ) from error
    if result.returncode != 0:
        raise BindingError(
            "not_a_worktree",
            f"{here} is not inside a Git worktree: {result.stderr.strip() or 'git refused'}",
        )
    return Path(os.path.realpath(result.stdout.strip()))


def path_of(root: Path) -> Path:
    return root / BINDING


def load(root: Path) -> dict | None:
    """The binding of the worktree ``root``, or None when it has none.

    ``BindingError`` when the file exists but cannot be read, breaks its contract or names
    another worktree than the one it lies in (a copied binding would bind the wrong workspace).
    """
    path = path_of(root)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BindingError(
            "binding_unreadable",
            f"the workspace binding {path} cannot be read: {error}",
        ) from error
    try:
        validate(value, BINDING_SCHEMA)
    except ContractError as error:
        raise BindingError(
            "binding_invalid",
            f"the workspace binding {path} breaks its contract at {error.field}: {error}",
        ) from error
    if Path(os.path.realpath(value["root"])) != Path(os.path.realpath(root)):
        raise BindingError(
            "binding_misplaced",
            f"the workspace binding {path} names the root {value['root']}, not the worktree "
            f"{root} it lies in; it was copied from another workspace",
        )
    return value


def write(root: Path, value: dict) -> Path:
    """Write the binding of ``root`` atomically after checking it against its contract."""
    validate(value, BINDING_SCHEMA)
    path = path_of(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)
    return path


def records_of(root: Path, bound: dict | None) -> Path:
    """Where runs and workflows of ``root`` are recorded: the binding's records directory, or
    the worktree's own ``.concorde`` for an unbound worktree."""
    return Path(bound["records"]) if bound else root / ".concorde"


__all__ = [
    "BINDING",
    "BINDING_SCHEMA",
    "BindingError",
    "load",
    "path_of",
    "records_of",
    "toplevel",
    "write",
]
