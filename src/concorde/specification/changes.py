"""Digest-bound, rollback-safe document/configuration changes owned by the host."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ..capabilities.operation_data import checked_path
from .repository import SpecError, digest, read_file


def file_change(root: Path, path: str, content: str) -> dict:
    target = checked_path(root, path)
    before = digest(read_file(root, path)) if target.exists() else None
    return {"path": path, "before_digest": before, "content": content}


def apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]:
    backups: dict[str, bytes | None] = {}
    if not changes or len({x["path"] for x in changes}) != len(changes):
        raise SpecError("change set must be nonempty with unique paths", "invalid_proposal")
    for item in changes:
        if set(item) != {"path", "before_digest", "content"} or item["path"] not in allowed:
            raise SpecError("change is outside its host-authorized boundary", "permission_denied")
        if not isinstance(item["content"], str):
            raise SpecError("document content must be UTF-8 text", "invalid_proposal")
        path = checked_path(root, item["path"])
        before = read_file(root, item["path"]) if path.exists() else None
        if (digest(before) if before is not None else None) != item["before_digest"]:
            raise SpecError(f"stale change input: {item['path']}", "stale_proposal")
        backups[item["path"]] = before
    changed = []
    def write(path: Path, data: bytes):
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
    try:
        for item in changes:
            path = checked_path(root, item["path"])
            observed=read_file(root,item["path"]) if path.exists() else None
            if observed!=backups[item["path"]]:raise SpecError("source changed during apply","stale_proposal")
            write(path, item["content"].encode())
            changed.append(item["path"])
        if verify:
            verify()
    except Exception:
        for relative in reversed(changed):
            path = checked_path(root, relative)
            if backups[relative] is None:
                path.unlink()
            else:
                write(path, backups[relative])
        raise
    return changed
