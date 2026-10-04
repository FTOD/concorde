"""The workspace binding: the one file through which the parts that work in a workspace learn it.

Whoever prepares a workspace (in Concorde, Tasks for a task worktree) writes
``.concorde/workspace.json`` at the worktree's root; every part that works in the workspace reads it
and never writes it. It names the workspace, its root, goal, Modules, branch and base commit, the
workspace folder where the work done in it is traced and the ``.concorde`` whose ``locks/`` holds
its locks (``contract.kernel.workspace-binding``). A binding that breaks its contract, names a root
that is not an absolute real path, a relative folder or a workspace folder that does not exist, or
names another worktree as its root is refused whole, by its reader and by its writer alike.
"""

from __future__ import annotations

import json
import os
import subprocess
from contextlib import suppress
from pathlib import Path

from .refusal import KernelError
from .schema import validate

BINDING = ".concorde/workspace.json"
NAME_PATTERN = "^[a-z0-9][a-z0-9-]{0,47}$"
TEXT = {"type": "string", "minLength": 1}
MODULE_ID = {
    "type": "string",
    "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$",
}

# contract.kernel.workspace-binding, version 2
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
        "traces",
        "concorde",
    ],
    "properties": {
        "schema_version": {"const": 2},
        "workspace": {"type": "string", "pattern": NAME_PATTERN},
        "root": TEXT,
        "branch": TEXT,
        "base_commit": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
        "goal": TEXT,
        "modules": {"type": "array", "minItems": 1, "items": MODULE_ID},
        "traces": TEXT,
        "concorde": TEXT,
    },
}


def toplevel(here: Path) -> Path:
    """The real root of the Git worktree ``here`` lies in; ``not_a_worktree`` outside one."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise KernelError(
            "not_a_worktree",
            f"git rev-parse could not run in {here}: {error}",
            field=str(here),
            causes=[error],
        ) from error
    if result.returncode != 0:
        raise KernelError(
            "not_a_worktree",
            f"{here} is not inside a Git worktree: {result.stderr.strip() or 'git refused'}",
            field=str(here),
        )
    return Path(os.path.realpath(result.stdout.strip()))


def path_of(root: Path) -> Path:
    """Where the binding of the worktree ``root`` lies."""
    return Path(root) / BINDING


def _invalid(path: Path, message: str) -> KernelError:
    return KernelError(
        "binding_invalid", f"the workspace binding {path} {message}", field=str(path)
    )


def load(root: Path) -> dict | None:
    """The binding of the worktree ``root``, or None when it has none.

    Refused with ``binding_unreadable`` when the file cannot be read or is no JSON,
    ``binding_invalid`` when it breaks its contract, names a root that is not an absolute real path,
    a relative folder or a workspace folder that does not exist, and ``binding_misplaced`` when its
    root is another worktree (a copied binding would bind the wrong workspace).
    """
    path = path_of(root)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise KernelError(
            "binding_unreadable",
            f"the workspace binding {path} cannot be read: {error}",
            field=str(path),
        ) from error
    _check(path, value, root, misplaced="binding_misplaced")
    return value


def _check(path: Path, value: object, root: Path, *, misplaced: str) -> None:
    """Refuse a binding of the worktree ``root`` that breaks its contract's schema or semantics;
    ``misplaced`` is the code of a root that is another worktree."""
    try:
        validate(value, BINDING_SCHEMA)
    except KernelError as error:
        raise _invalid(
            path, f"breaks its contract at {error.field or 'its top'}: {error}"
        ) from error
    declared = value["root"]
    if not os.path.isabs(declared) or os.path.realpath(declared) != declared:
        raise _invalid(
            path, f"names the root {declared}, which is not an absolute real path"
        )
    if declared != os.path.realpath(root):
        raise KernelError(
            misplaced,
            f"the workspace binding {path} names the root {declared}, not the worktree "
            f"{root} it lies in; it was copied from another workspace",
            field=str(path),
        )
    for field in ("traces", "concorde"):
        if not os.path.isabs(value[field]):
            raise _invalid(
                path,
                f"names the {field} folder {value[field]}, which is not an absolute path",
            )
    if not Path(value["traces"]).is_dir():
        raise _invalid(
            path,
            f"names the workspace folder {value['traces']}, which does not exist; whoever "
            "prepared the workspace removed it, as closing a task does",
        )


def write(root: Path, value: dict) -> Path:
    """Write the binding of ``root`` atomically after checking it as ``load`` does.

    Refused with ``binding_invalid`` for a binding ``load`` would refuse, and ``system_error``
    naming the file when the operating system refuses the write.
    """
    path = path_of(root)
    _check(path, value, root, misplaced="binding_invalid")
    temporary = path.with_suffix(".json.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        temporary.replace(path)
    except OSError as error:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise KernelError(
            "system_error",
            f"the workspace binding {path} cannot be written: {error}",
            field=str(path),
            causes=[error],
        ) from error
    return path


__all__ = ["BINDING", "BINDING_SCHEMA", "load", "path_of", "toplevel", "write"]
