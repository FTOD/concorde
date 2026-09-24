"""Digest-bound, rollback-safe document/configuration changes owned by the host."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .typed_data import checked_path
from .repository import SpecError, digest, read_file


def file_change(root: Path, path: str, content: str) -> dict:
    target = checked_path(root, path)
    before = digest(read_file(root, path)) if target.exists() else None
    return {"path": path, "before_digest": before, "content": content}


def apply_files(
    root: Path, changes: list[dict], allowed: set[str], *, verify=None
) -> list[str]:
    backups: dict[str, bytes | None] = {}
    paths = [x.get("path") for x in changes]
    if not changes or len(set(paths)) != len(changes):
        repeated = sorted({path for path in paths if paths.count(path) > 1})
        raise SpecError(
            "a change set must be nonempty with unique paths; "
            + (
                f"repeated: {', '.join(map(str, repeated))}"
                if repeated
                else "it is empty"
            ),
            "invalid_proposal",
        )
    for item in changes:
        if set(item) != {"path", "before_digest", "content"}:
            raise SpecError(
                f"the change of {item.get('path')!r} has fields {sorted(item)}; a change has "
                "exactly path, before_digest and content",
                "invalid_proposal",
                path=str(item.get("path")),
            )
        if item["path"] not in allowed:
            raise SpecError(
                f"the change of {item['path']} lies outside the paths its caller authorized: "
                + ", ".join(sorted(allowed))[:600],
                "permission_denied",
                path=item["path"],
            )
        if not isinstance(item["content"], str):
            raise SpecError(
                f"the new content of {item['path']} is a {type(item['content']).__name__}, "
                "not text",
                "invalid_proposal",
                path=item["path"],
                reason="Spec tooling writes documents and configuration as UTF-8 text",
            )
        path = checked_path(root, item["path"])
        before = read_file(root, item["path"]) if path.exists() else None
        observed = digest(before) if before is not None else None
        if observed != item["before_digest"]:
            raise SpecError(
                f"{item['path']} is now {observed or 'absent'}, but the change was computed "
                f"from {item['before_digest'] or 'an absent file'}",
                "stale_proposal",
                path=item["path"],
            )
        backups[item["path"]] = before
    changed = []

    def write(path: Path, data: bytes):
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".concorde-write-", dir=path.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    try:
        for item in changes:
            path = checked_path(root, item["path"])
            observed = read_file(root, item["path"]) if path.exists() else None
            if observed != backups[item["path"]]:
                raise SpecError(
                    f"{item['path']} changed while the change set was being applied; every "
                    "file written so far was restored",
                    "stale_proposal",
                    path=item["path"],
                )
            write(path, item["content"].encode())
            changed.append(item["path"])
        if verify:
            verify()
    except Exception:
        for relative in reversed(changed):
            path = checked_path(root, relative)
            original = backups[relative]
            if original is None:
                path.unlink()
            else:
                write(path, original)
        raise
    return changed


def confirm_pending_files(
    root: Path, package_root: Path | None = None
) -> tuple[list[dict], list[str]]:
    """Confirm existing entries in metadata without changing human reading."""
    from .content_changes import confirm_pending_units
    from .repository import SpecRepository

    return confirm_pending_units(SpecRepository(root, package_root))
