"""File transactions: whole-file writes, each bound to the bytes it replaces, restored on failure.

``apply_files`` writes a nonempty list of changes ``{path, before_digest, content}`` below a root,
each through a temporary file in its own directory that is flushed and renamed into place. A
malformed list, a path outside the allowed ones or a file that no longer matches its
``before_digest`` writes nothing. When a write or the final check fails, every file written so far
is restored, or removed when it did not exist; a restoration the operating system refuses is named
in a ``system_error``. A killed process restores nothing, and the caller excludes every other
writer of its files by holding the lock its records require
(``specs/concorde/kernel/contracts.md#file-transactions``).
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Callable

from .refusal import KernelError
from .schema import DIGEST_PATTERN, checked_path, digest


def _bytes_of(root: Path, relative: str) -> bytes | None:
    path = checked_path(root, relative, relative)
    if not path.exists():
        return None
    try:
        return path.read_bytes()
    except OSError as error:
        raise KernelError(
            "system_error",
            f"{relative} cannot be read: {error}",
            field=relative,
            causes=[error],
        ) from error


def file_change(root: Path, path: str, content: str) -> dict:
    """The change writing ``content`` to ``path`` below ``root``, bound to its current bytes."""
    before = _bytes_of(root, path)
    return {
        "path": path,
        "before_digest": None if before is None else digest(before),
        "content": content,
    }


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".concorde-write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _checked(
    root: Path, changes: list[dict], allowed: set[str]
) -> dict[str, bytes | None]:
    """The current bytes of every target, after refusing a malformed or stale list."""
    if not isinstance(changes, list) or not changes:
        raise KernelError(
            "invalid_proposal", "a file transaction needs at least one change"
        )
    paths = [item.get("path") if isinstance(item, dict) else None for item in changes]
    repeated = sorted({str(path) for path in paths if paths.count(path) > 1})
    if repeated:
        raise KernelError(
            "invalid_proposal",
            "a file transaction names each file once; repeated: " + ", ".join(repeated),
        )
    backups: dict[str, bytes | None] = {}
    for item in changes:
        if not isinstance(item, dict) or set(item) != {
            "path",
            "before_digest",
            "content",
        }:
            raise KernelError(
                "invalid_proposal",
                f"a change has exactly path, before_digest and content, not {item!r:.200}",
            )
        relative = item["path"]
        try:
            checked_path(root, relative, str(relative))
        except KernelError as error:
            raise KernelError(
                "invalid_proposal",
                f"the change's path is unusable: {error}",
                field=error.field,
            ) from None
        if not isinstance(item["content"], str):
            raise KernelError(
                "invalid_proposal",
                f"the new content of {relative} is a {type(item['content']).__name__}, not text",
                field=relative,
            )
        before = item["before_digest"]
        if before is not None and not (
            isinstance(before, str) and re.fullmatch(DIGEST_PATTERN[1:-1], before)
        ):
            raise KernelError(
                "invalid_proposal",
                f"the before_digest of {relative} is neither a sha256 digest nor null",
                field=relative,
            )
        if relative not in allowed:
            raise KernelError(
                "permission_denied",
                f"the change of {relative} lies outside the paths its caller allowed: "
                + ", ".join(sorted(allowed))[:600],
                field=relative,
            )
        current = _bytes_of(root, relative)
        observed = None if current is None else digest(current)
        if observed != before:
            raise KernelError(
                "stale_proposal",
                f"{relative} is now {observed or 'absent'}, but its change was computed from "
                f"{before or 'an absent file'}; nothing was written",
                field=relative,
            )
        backups[relative] = current
    return backups


def apply_files(
    root: Path,
    changes: list[dict],
    allowed: set[str],
    *,
    verify: Callable[[], object] | None = None,
) -> list[str]:
    """Apply the file transaction ``changes`` below ``root``; the written paths in order.

    ``allowed`` are the paths the caller allows; ``verify`` is the final check, run after the last
    write, whose own exception is raised unchanged once every file was restored. An interruption
    the process observes, such as ``KeyboardInterrupt`` or ``SystemExit``, restores the same way
    as any other failure.
    """
    root = Path(root)
    backups = _checked(root, changes, allowed)
    written: list[str] = []
    current: str | None = None
    try:
        for item in changes:
            current = item["path"]
            if _bytes_of(root, current) != backups[current]:
                raise KernelError(
                    "stale_proposal",
                    f"{current} changed while the transaction was being applied; every file "
                    "written so far was restored",
                    field=current,
                )
            _write(checked_path(root, current, current), item["content"].encode())
            written.append(current)
        current = None
        if verify is not None:
            verify()
    except BaseException as error:
        refused = _restore(root, written, backups)
        if refused:
            raise KernelError(
                "system_error",
                "a file transaction failed and the operating system refused to restore "
                + ", ".join(path for path, _ in refused)
                + "; each of those files still holds the transaction's new content, every other "
                "written file was restored",
                field=refused[0][0],
                causes=[error, *(problem for _, problem in refused)],
            ) from error
        if isinstance(error, OSError) and current is not None:
            raise KernelError(
                "system_error",
                f"writing {current} failed: {error}; every file written so far was restored",
                field=current,
                causes=[error],
            ) from error
        raise
    return written


def _restore(
    root: Path, written: list[str], backups: dict[str, bytes | None]
) -> list[tuple[str, OSError]]:
    """Restore every written file, newest first; each restoration refused, with its error."""
    refused = []
    for relative in reversed(written):
        path = checked_path(root, relative, relative)
        try:
            if backups[relative] is None:
                path.unlink()
            else:
                _write(path, backups[relative])
        except OSError as problem:
            refused.append((relative, problem))
    return refused


__all__ = ["apply_files", "file_change"]
