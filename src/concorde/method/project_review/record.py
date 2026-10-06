"""The review record: what the last ``project_review`` judged of each Module and of the project
(see the Project review Module Spec, "The review record").

The record is one JSON file, ``.concorde/reviews/record.json``, committed on the primary branch so
that every worktree and collaborator of the project shares it. It is read from the primary
worktree's last commit, never from its files or from the examined checkout. Only the host of a
``project_review`` run writes it: under the primary worktree's merge lock it merges the parts the
run judged into the committed record, publishes the file and commits that one file on the primary
branch before it answers, as an Issue write commits its record. A valid record left uncommitted by
a write that was interrupted is put back to its committed version first. It refuses, changing
nothing, while the file holds any other change no commit holds and when the committed record is
not a valid one. When anything fails after the file was published, it puts the file back to its
committed version before it refuses. It reads no task record: an Operation never does
(``req.concorde.halves-apart``).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from ...kernel import locking
from ...kernel.files import apply_files
from ...kernel.refusal import KernelError
from ...kernel.schema import digest
from ...kernel.tracing import layout
from ...spec.schema import ContractError, validate

PATH = ".concorde/reviews/record.json"
SCHEMA_VERSION = 1
ACTOR = "Project review (review record)"

_IDENTITY = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
_JUDGED = {
    "run": {"type": "string", "minLength": 1},
    "commit": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
    "judged_at": {"type": "string", "minLength": 1},
}


# The earlier Issues a part found resolved, each at the revision it had once the run ended.
_RESOLVED = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["issue", "revision"],
        "properties": {
            "issue": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
            "revision": _IDENTITY,
        },
    },
}


def _entry(*identities: str) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [*identities, *_JUDGED],
        "properties": {
            **{name: _IDENTITY for name in identities},
            **_JUDGED,
            "resolved": _RESOLVED,
        },
    }


# contract.project-review.record, version 1 (contracts.md); a test keeps the two equal.
SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "architecture", "modules"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "architecture": {"anyOf": [{"type": "null"}, _entry("context_identity")]},
        "modules": {
            # Keyed by Module identity, which the host checks, since the schema language has no
            # keyword for keys.
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "panel": _entry("context_identity"),
                    "code_review": _entry("context_identity", "code_digest"),
                },
            },
        },
    },
}


def empty() -> dict:
    return {"schema_version": SCHEMA_VERSION, "architecture": None, "modules": {}}


class RecordError(Exception):
    """A refusal of the review record: its ``code`` and the reason the host cannot handle it."""

    def __init__(self, code: str, message: str, reason: str = "environment"):
        super().__init__(message)
        self.code, self.reason = code, reason


def _git(root: Path, *arguments: str, stdin: str | None = None):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _output(done) -> str:
    return ((done.stdout or "") + (done.stderr or "")).strip()[-2000:] or "(no output)"


def primary_of(started_in: Path) -> Path:
    """The primary worktree of the repository the run started in, which keeps the record."""
    primary = layout.primary_worktree(Path(started_in))
    if primary is None:
        raise RecordError(
            "record_unavailable",
            f"{started_in} lies in no Git repository, whose primary branch keeps the review "
            "record",
        )
    return primary


def _committed(primary: Path) -> bytes | None:
    """The record's bytes in the primary worktree's last commit, or None when it holds none."""
    head = _git(primary, "rev-parse", "-q", "--verify", "HEAD^{commit}")
    if head.returncode != 0:
        return None
    listed = _git(primary, "ls-tree", head.stdout.strip(), "--", PATH)
    if listed.returncode != 0:
        raise RecordError(
            "record_unreadable",
            f"git ls-tree of {PATH} in {primary} exited {listed.returncode}: "
            f"{_output(listed)}",
        )
    if not listed.stdout.strip():
        return None
    mode = listed.stdout.split()[0]
    if mode not in ("100644", "100755"):
        raise RecordError(
            "record_invalid",
            f"{PATH} is committed in {primary} as mode {mode}, not as a regular file",
            "input",
        )
    shown = subprocess.run(
        ["git", "show", f"HEAD:{PATH}"],
        cwd=primary,
        capture_output=True,
        check=False,
    )
    if shown.returncode != 0:
        raise RecordError(
            "record_unreadable",
            f"git show HEAD:{PATH} in {primary} exited {shown.returncode}: "
            f"{shown.stderr.decode(errors='replace').strip()[-2000:]}",
        )
    return shown.stdout


def _parsed(raw: bytes | None) -> dict:
    if raw is None:
        return empty()
    try:
        value = json.loads(raw.decode("utf-8"))
        validate(value, SCHEMA)
        strange = [key for key in value["modules"] if not key.startswith("module.")]
        if strange:
            raise ValueError(f"{', '.join(strange)} name no Module")
    except (UnicodeError, ValueError, ContractError) as error:
        raise RecordError(
            "record_invalid",
            f"the committed {PATH} is not a valid review record: {error}",
            "input",
        ) from None
    return value


def read(primary: Path) -> dict:
    """The review record committed on the primary branch, empty when none is committed."""
    return _parsed(_committed(primary))


def text(record: dict) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _put_back(primary: Path) -> str | None:
    """Put the record file back to its committed version, or remove it when none is committed;
    what went wrong, or None."""
    if _git(primary, "cat-file", "-e", f"HEAD:{PATH}").returncode == 0:
        done = _git(primary, "checkout", "-q", "HEAD", "--", PATH)
        return None if done.returncode == 0 else _output(done)
    done = _git(primary, "rm", "-q", "--cached", "--ignore-unmatch", "--", PATH)
    if done.returncode != 0:
        return _output(done)
    try:
        (primary / PATH).unlink(missing_ok=True)
    except OSError as error:
        return str(error)
    return None


def publish(
    primary: Path,
    holder: str,
    update: Callable[[dict], dict],
    message: str,
    *,
    wait: float = locking.MERGE_WAIT,
) -> str | None:
    """Merge a run's judgments into the committed record and commit it alone on the primary
    branch, holding the merge lock; ``update`` returns the new record from the committed one. The
    new commit, or None when the record did not change. Raises ``RecordError``."""
    try:
        with locking.merge_lock(layout.concorde_of(primary), holder, wait=wait):
            return _publish(primary, update, message)
    except locking.LockRefused as busy:
        raise RecordError(
            "merge_busy",
            f"the review record waited {wait:g} s for the merge lock {busy.path} of the "
            f"primary worktree {primary}, still held by {busy.holder}, and wrote nothing",
        ) from None
    except KernelError as error:
        raise RecordError(
            error.code,
            f"the merge lock of {primary} could not be taken: {error}",
        ) from None


def _leftover(primary: Path) -> bool:
    """Whether the record file holds a valid record no commit holds, as a write interrupted after
    publishing it leaves it."""
    try:
        _parsed((primary / PATH).read_bytes())
    except (OSError, RecordError):
        return False
    return True


def _publish(primary: Path, update: Callable[[dict], dict], message: str) -> str | None:
    branch = _git(primary, "symbolic-ref", "-q", "--short", "HEAD")
    if branch.returncode != 0:
        raise RecordError(
            "commit_failed",
            f"the primary worktree {primary} has a detached HEAD, so there is no branch to "
            "commit the review record on",
        )
    status = _git(
        primary,
        "--no-optional-locks",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
        "--",
        PATH,
    )
    if status.returncode == 0 and status.stdout.strip() and _leftover(primary):
        left = _put_back(primary)
        if left is not None:
            raise RecordError(
                "recovery_failed",
                f"{PATH} of the primary worktree {primary} holds a record an interrupted write "
                f"left uncommitted, and putting it back failed: {left}",
            )
        status = _git(
            primary,
            "--no-optional-locks",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored",
            "--",
            PATH,
        )
    if status.returncode != 0 or status.stdout.strip():
        raise RecordError(
            "uncommitted_change",
            f"{PATH} of the primary worktree {primary} differs from its committed version "
            f"({_output(status)}), and the review record neither overwrites nor discards a "
            "change it did not commit",
            "input",
        )
    raw = _committed(primary)
    current = _parsed(raw)
    updated = update(json.loads(json.dumps(current)))
    validate(updated, SCHEMA)
    if updated == current:
        return None
    try:
        apply_files(
            primary,
            [
                {
                    "path": PATH,
                    "before_digest": None if raw is None else digest(raw),
                    "content": text(updated),
                }
            ],
            {PATH},
        )
    except KernelError as error:
        raise RecordError(
            "record_unwritten",
            f"publishing {PATH} in {primary} failed: {error.code}: {error}",
        ) from None
    added = _git(primary, "add", "-f", "--", PATH)
    done = (
        _git(primary, "commit", "-q", "--only", "-F", "-", "--", PATH, stdin=message)
        if added.returncode == 0
        else added
    )
    if done.returncode != 0:
        left = _put_back(primary)
        raise RecordError(
            "commit_failed" if left is None else "recovery_failed",
            f"committing {PATH} on {branch.stdout.strip()} of {primary} failed: "
            f"{_output(done)}"
            + (
                "; the file is back as it was"
                if left is None
                else f"; putting the file back failed too: {left}; revert it with "
                f"`git checkout HEAD -- {PATH}` in the primary worktree"
            ),
        )
    return _git(primary, "rev-parse", "HEAD").stdout.strip()


__all__ = [
    "PATH",
    "SCHEMA",
    "RecordError",
    "empty",
    "primary_of",
    "publish",
    "read",
]
