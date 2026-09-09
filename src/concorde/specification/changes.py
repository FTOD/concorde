"""Digest-bound, rollback-safe document/configuration changes owned by the host."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ..host.typed_data import checked_path
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


def _rewrite_entities(text: str, confirmed: dict[str, set[str]]) -> str:
    """Drop confirmed paths from each named entity's ``pending`` list, changing nothing else."""
    import json
    from .repository import ENTITIES_BLOCK

    pieces: list[str] = []
    last = 0
    for match in ENTITIES_BLOCK.finditer(text):
        values = json.loads(match.group(1))
        changed = False
        for value in values:
            paths = confirmed.get(value.get("id"))
            if not paths or "pending" not in value:
                continue
            remaining = [path for path in value["pending"] if path not in paths]
            if remaining != value["pending"]:
                changed = True
                if remaining:
                    value["pending"] = remaining
                else:
                    value.pop("pending")
        if changed:
            pieces.append(text[last:match.start(1)])
            pieces.append(json.dumps(values, indent=2) + "\n")
            last = match.end(1)
    pieces.append(text[last:])
    return "".join(pieces)


def confirm_pending_files(root: Path, package_root: Path | None = None) -> tuple[list[dict], list[str]]:
    """Confirm declared-but-missing files that now exist, and report the ones still missing.

    ``pending`` records an author's intent, never evidence: the validator re-checks the file
    system on every run. Delivery is the one deterministic moment that clears a confirmed marker,
    so the delivered Spec no longer claims a file is still to be written.
    """
    from .repository import SpecError, SpecRepository, read_file

    repository = SpecRepository(root, package_root)
    confirmed: list[dict] = []
    still_pending: list[str] = []
    documents: dict[str, dict[str, set[str]]] = {}
    for target in repository.targets.values():
        try:
            entities = repository.entities(target)
        except (SpecError, ValueError, OSError, KeyError, TypeError):
            continue
        for entity in entities:
            for path in entity.pending:
                if checked_path(repository.root, path).is_file():
                    documents.setdefault(entity.document, {}).setdefault(entity.id, set()).add(path)
                    confirmed.append({"module": target.id, "entity": entity.id, "path": path})
                else:
                    still_pending.append(path)
    changes = []
    for document_path, entity_paths in sorted(documents.items()):
        before = read_file(repository.root, document_path).decode()
        after = _rewrite_entities(before, entity_paths)
        if after != before:
            changes.append(file_change(repository.root, document_path, after))
    if changes:
        apply_files(repository.root, changes, {change["path"] for change in changes})
    return confirmed, sorted(set(still_pending))
