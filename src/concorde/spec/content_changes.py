"""Confirmation of pending realization entries once their files exist.

A ``pending`` entry records where a file may be created before any code is written. Delivery
confirms entries that now exist by removing them from ``pending``; only the affected metadata
members change, in one digest-bound file transaction.
"""

from __future__ import annotations

import json

from .changes import apply_files
from .content_model import metadata_path
from .content_repository import DocumentUnitRepository
from .repository_base import SpecError, entry_exists


def pending_changes(
    repository: DocumentUnitRepository,
) -> tuple[list[dict], list[dict], list[str]]:
    """Plan metadata-only removal of confirmed pending markers."""
    changes, confirmed, missing = [], [], []
    for path in sorted(repository.units):
        unit = repository.units[path]
        value = unit.declarations
        updated = False
        for record in value.get("defines", []):
            if not isinstance(record, dict) or record.get("type") != "realization":
                continue
            pending = record.get("pending", [])
            remaining = []
            for entry in pending:
                if entry_exists(repository.root, entry):
                    confirmed.append(
                        {
                            "module": unit.owner,
                            "realization": record["id"],
                            "path": entry,
                        }
                    )
                else:
                    remaining.append(entry)
                    missing.append(entry)
            if remaining != pending:
                updated = True
                record["pending"] = remaining
        if updated:
            changes.append(
                {
                    "path": unit.metadata.path,
                    "before_digest": unit.metadata.digest,
                    "content": json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                }
            )
    return changes, confirmed, sorted(set(missing))


def confirm_pending_units(
    repository: DocumentUnitRepository,
) -> tuple[list[dict], list[str]]:
    """Confirm materialized entries without editing reading prose or losing pending intentions."""
    if repository.document_overrides or repository._registry_override is not None:
        raise SpecError(
            "pending confirmation requires an on-disk base", "invalid_proposal"
        )
    changes, confirmed, missing = pending_changes(repository)
    if not changes:
        return confirmed, missing
    written = {item["path"] for item in changes}
    before = {
        member.path: member.digest
        for unit in repository.units.values()
        for member in unit.sources
        if member.path not in written
    }

    def verify():
        current = repository.fresh()
        observed = {
            member.path: member.digest
            for unit in current.units.values()
            for member in unit.sources
            if member.path not in written
        }
        if current.registry_bytes != repository.registry_bytes or observed != before:
            raise SpecError(
                "Spec sources changed during pending confirmation", "stale_proposal"
            )

    apply_files(
        repository.root,
        changes,
        {metadata_path(path) for path in repository.document_targets},
        verify=verify,
    )
    return confirmed, missing
