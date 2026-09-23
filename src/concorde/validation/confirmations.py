"""Pending realization entries whose files exist: finding them, and clearing them for Delivery.

``plan`` lists every pending entry whose file exists as a confirmation, together with the
metadata document declaring it and that document's digest, and the metadata content with those
markers cleared. ``apply`` clears exactly the listed markers in one file transaction bound to the
recorded digests, then validates the structure of the Specs and rolls back if an error remains.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..spec.changes import apply_files
from ..spec.repository import SpecRepository
from ..spec.repository_base import SpecError, entry_exists
from ..spec.validation import validate_repository


class ConfirmationRefused(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _serialize(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def plan(repository: SpecRepository) -> tuple[list[dict], dict[str, bytes]]:
    """Every confirmation of the loaded Specs and the confirmed metadata bytes per document."""
    confirmations: list[dict] = []
    contents: dict[str, bytes] = {}
    for path in sorted(repository.units):
        unit = repository.units[path]
        value = unit.declarations
        changed = False
        for record in value.get("defines", []) if isinstance(value, dict) else []:
            if not isinstance(record, dict) or record.get("type") != "realization":
                continue
            pending = record.get("pending") or []
            remaining = []
            for entry in pending:
                if entry in (record.get("entries") or []) and entry_exists(
                    repository.root, entry
                ):
                    confirmations.append(
                        {
                            "module": unit.owner,
                            "realization": record["id"],
                            "entry": entry,
                            "metadata": unit.metadata.path,
                            "metadata_digest": unit.metadata.digest,
                        }
                    )
                else:
                    remaining.append(entry)
            if remaining != pending:
                changed = True
                if remaining:
                    record["pending"] = remaining
                else:
                    record.pop("pending")
        if changed:
            contents[unit.metadata.path] = _serialize(value).encode()
    return confirmations, contents


def apply(worktree: Path, confirmations: list[dict]) -> dict[str, bytes]:
    """Clear exactly the listed markers; return the replaced metadata bytes by path.

    Refused, with every document left as it was, when a declaring document no longer has the
    recorded digest, a listed entry is no longer pending or its file is missing, or the confirmed
    Specs have a structural error.
    """
    worktree = Path(worktree)
    if not confirmations:
        return {}
    try:
        repository = SpecRepository(worktree)
    except (SpecError, OSError, ValueError) as error:
        raise ConfirmationRefused("specs_unloadable", str(error)) from error
    units = {unit.metadata.path: unit for unit in repository.units.values()}
    grouped: dict[str, list[dict]] = {}
    for item in confirmations:
        grouped.setdefault(item["metadata"], []).append(item)
    changes, backups = [], {}
    for path, items in sorted(grouped.items()):
        unit = units.get(path)
        if unit is None:
            raise ConfirmationRefused(
                "stale_confirmation", f"{path} is no longer a registered document"
            )
        if any(item["metadata_digest"] != unit.metadata.digest for item in items):
            raise ConfirmationRefused(
                "stale_confirmation",
                f"{path} no longer has the digest the readiness recorded",
            )
        value = unit.declarations
        records = {
            record.get("id"): record
            for record in value.get("defines", [])
            if isinstance(record, dict) and record.get("type") == "realization"
        }
        for item in items:
            record = records.get(item["realization"])
            if record is None or item["entry"] not in (record.get("pending") or []):
                raise ConfirmationRefused(
                    "stale_confirmation",
                    f"{item['entry']} is not pending in {item['realization']}",
                )
            if not entry_exists(worktree, item["entry"]):
                raise ConfirmationRefused(
                    "stale_confirmation", f"{item['entry']} does not exist"
                )
            record["pending"] = [
                entry for entry in record["pending"] if entry != item["entry"]
            ]
            if not record["pending"]:
                record.pop("pending")
        backups[path] = unit.metadata.content
        changes.append(
            {
                "path": path,
                "before_digest": unit.metadata.digest,
                "content": _serialize(value),
            }
        )

    def verify():
        result = validate_repository(worktree)
        errors = [item for item in result.findings if item.severity == "error"]
        if errors:
            first = errors[0]
            raise ConfirmationRefused(
                "invalid_after_confirmation",
                f"{len(errors)} structural error(s) after confirmation, first "
                f"{first.rule_id} {first.source}: {first.message}",
            )

    try:
        apply_files(worktree, changes, set(grouped), verify=verify)
    except SpecError as error:
        raise ConfirmationRefused(error.code, str(error)) from error
    return backups


def restore(worktree: Path, backups: dict[str, bytes]) -> None:
    """Write back the metadata bytes ``apply`` replaced."""
    for path, data in backups.items():
        (Path(worktree) / path).write_bytes(data)


__all__ = ["ConfirmationRefused", "apply", "plan", "restore"]
