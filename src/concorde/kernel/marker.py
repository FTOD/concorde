"""The unfinished-merge marker: the Kernel state that says the primary branch is not to be built on.

A part that changes the primary branch in steps the merge lock alone cannot keep together, as
Tasks' merge does between its merge commit and the checks that decide whether it stays, writes
``.concorde/unfinished-merge.json`` of the primary worktree under the merge lock before it changes
anything, and removes it once the change is decided. Since the operating system releases the merge
lock however its holder ends, the marker is what a crash leaves behind. Every part that commits on
the primary branch under the merge lock reads it and refuses while it is present or cannot be read
(``contract.kernel.unfinished-merge``). Only the part the marker names replaces or removes it.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from .refusal import KernelError
from .schema import validate

# The marker's file name in the primary worktree's ``.concorde``, which Git ignores.
NAME = "unfinished-merge.json"
TEXT = {"type": "string", "minLength": 1}
COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}

# contract.kernel.unfinished-merge, version 1
MARKER_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "part",
        "by",
        "pid",
        "since",
        "branch",
        "before",
        "merging",
        "after",
        "finish",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "part": {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"},
        "by": TEXT,
        "pid": {"type": "integer", "minimum": 1},
        "since": TEXT,
        "branch": TEXT,
        "before": COMMIT,
        "merging": COMMIT,
        "after": {"anyOf": [COMMIT, {"type": "null"}]},
        "finish": {"type": "array", "minItems": 1, "items": TEXT},
    },
}


def marker_path(concorde: Path) -> Path:
    """The unfinished-merge marker of the ``.concorde`` directory of a primary worktree."""
    return Path(concorde) / NAME


def _invalid(path: Path, error: KernelError) -> KernelError:
    return KernelError(
        "marker_invalid",
        f"the unfinished-merge marker {path} breaks its contract at "
        f"{error.field or 'its top'}: {error}",
        field=str(path),
    )


def read_marker(concorde: Path) -> dict | None:
    """The unfinished-merge marker of the primary worktree whose ``.concorde`` this is, or None
    when there is none.

    Refused with ``marker_unreadable`` when the file cannot be read or is no JSON and with
    ``marker_invalid`` when it breaks its contract; a reader takes either as an unfinished merge
    it cannot describe, never as none.
    """
    path = marker_path(concorde)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise KernelError(
            "marker_unreadable",
            f"the unfinished-merge marker {path} cannot be read: {error}",
            field=str(path),
            causes=[error] if isinstance(error, OSError) else [],
        ) from error
    try:
        value = json.loads(text)
    except ValueError as error:
        raise KernelError(
            "marker_unreadable",
            f"the unfinished-merge marker {path} is no JSON: {error}",
            field=str(path),
        ) from error
    try:
        validate(value, MARKER_SCHEMA)
    except KernelError as error:
        raise _invalid(path, error) from error
    return value


def write_marker(concorde: Path, value: dict) -> Path:
    """Write the marker in one rename, replacing any marker there; its writer holds the merge
    lock. Refused with ``marker_invalid`` for a marker that breaks its contract and
    ``system_error`` naming the file when the operating system refuses the write."""
    path = marker_path(concorde)
    try:
        validate(value, MARKER_SCHEMA)
    except KernelError as error:
        raise _invalid(path, error) from error
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".concorde-write-", dir=path.parent
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        raise KernelError(
            "system_error",
            f"the unfinished-merge marker {path} cannot be written: {error}",
            field=str(path),
            causes=[error],
        ) from error
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return path


def remove_marker(concorde: Path) -> bool:
    """Remove the marker; whether there was one. Refused with ``system_error`` naming the file
    when the operating system refuses the removal."""
    path = marker_path(concorde)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise KernelError(
            "system_error",
            f"the unfinished-merge marker {path} cannot be removed: {error}",
            field=str(path),
            causes=[error],
        ) from error
    return True


def _head(worktree: Path) -> str | None:
    try:
        done = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "HEAD^{commit}"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def describe(concorde: Path, value: dict) -> str:
    """The account of the unfinished merge the marker ``value`` describes: who was merging what
    into which branch, where that branch's worktree is now and the commands that finish it."""
    worktree = Path(concorde).parent
    head = _head(worktree)
    after = value["after"]
    if head is None:
        where = "at a commit Git does not name"
    elif after and head == after:
        where = f"at {head}, the merge commit"
    elif head == value["before"]:
        where = f"back at {head}, the commit before the merge"
    else:
        where = (
            f"at {head}, which is neither the commit before the merge nor the merge commit "
            f"{after or '(not made yet)'}"
        )
    finish = " or ".join(f"`{command}`" for command in value["finish"])
    return (
        f"a merge into the primary branch is unfinished: {value['by']} (process "
        f"{value['pid']}, begun {value['since']}) was merging {value['merging']} into "
        f"{value['branch']} of {worktree}, which was at {value['before']}, and ended before it "
        f"decided whether the merge stays; the primary worktree is now {where}; nothing is "
        f"committed on the primary branch until {finish} finishes it"
    )


__all__ = [
    "MARKER_SCHEMA",
    "NAME",
    "describe",
    "marker_path",
    "read_marker",
    "remove_marker",
    "write_marker",
]
