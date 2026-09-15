"""Owner-scoped proposals and pending confirmation for the staged document-unit backend.

These deterministic operations exercise the existing digest-bound file transaction. They do not
launch a worker, relax a code grant or activate a new project Protocol/profile implicitly.
"""
from __future__ import annotations

import json

from .changes import apply_files
from .content_model import metadata_path
from .content_repository import DocumentUnitRepository
from .repository import SpecError, SpecResolution, digest, entry_exists, read_file


def author_candidate(repository: DocumentUnitRepository, module_id: str, changes: list[dict], *,
                     baseline: SpecResolution) -> DocumentUnitRepository:
    """Validate all replacements together; referenced units stay read-only, either member may change."""
    if baseline.value["module_id"] != module_id:
        raise SpecError("author baseline belongs to a different Module", "permission_denied")
    admitted = repository.context_bytes(baseline)
    target = repository.select(module_id)
    allowed = {member for path in target.documents for member in (path, metadata_path(path))}
    if not isinstance(changes, list) or not changes or any(
            not isinstance(item, dict) or set(item) != {"path", "before_digest", "content"} for item in changes):
        raise SpecError("author proposal requires complete digest-bound file replacements", "invalid_proposal")
    overrides = dict(repository.document_overrides)
    seen = set()
    for item in changes:
        path = item["path"]
        if not isinstance(path, str) or path not in allowed or path in seen:
            raise SpecError("author proposal crosses ownership or repeats a source", "permission_denied")
        seen.add(path)
        if not isinstance(item["content"], str):
            raise SpecError("author source content must be UTF-8 text", "invalid_proposal")
        if item["before_digest"] != digest(admitted[path]):
            raise SpecError("author proposal has stale source bytes", "stale_proposal")
        overrides[path] = item["content"].encode("utf-8")
    candidate = DocumentUnitRepository(repository.root, registry_path=repository.registry_path,
        registry_bytes=repository.registry_bytes, document_overrides=overrides)
    for path in target.documents:
        if candidate.unit(path).document_id != repository.unit(path).document_id:
            raise SpecError("ordinary authoring cannot change document identity", "invalid_owner")
    candidate.validate()
    return candidate


def apply_author_changes(repository: DocumentUnitRepository, module_id: str, changes: list[dict], *,
                         baseline: SpecResolution) -> list[str]:
    """Apply one validated author proposal atomically, preserving both source roles on failure."""
    if repository.document_overrides or repository._registry_override is not None:
        raise SpecError("an overlay cannot be used as an on-disk application base", "invalid_proposal")
    candidate = author_candidate(repository, module_id, changes, baseline=baseline)
    expected = candidate.context_identities()
    repository.recheck_resolution(baseline)
    if read_file(repository.root, repository.registry_path) != repository.registry_bytes:
        raise SpecError("registry changed before author application", "stale_proposal")

    def verify():
        current = repository.fresh()
        current.validate()
        if current.registry_bytes != repository.registry_bytes or current.context_identities() != expected:
            raise SpecError("application inputs changed during author transaction", "stale_proposal")

    target = repository.select(module_id)
    allowed = {member for path in target.documents for member in (path, metadata_path(path))}
    return apply_files(repository.root, changes, allowed, verify=verify)


def pending_changes(repository: DocumentUnitRepository) -> tuple[list[dict], list[dict], list[str]]:
    """Plan metadata-only removal of confirmed pending markers; malformed units fail closed."""
    changes, confirmed, missing = [], [], []
    for target in repository.targets.values():
        repository.definitions(target)
    for path in sorted(repository.document_targets):
        unit = repository.unit(path)
        value = unit.declarations
        updated = False
        for entity in value["entities"]:
            pending = entity.get("pending", [])
            remaining = []
            for entry in pending:
                if entry_exists(repository.root, entry):
                    confirmed.append({"module": unit.owner, "entity": entity["id"], "path": entry})
                else:
                    remaining.append(entry)
                    missing.append(entry)
            if remaining != pending:
                updated = True
                if remaining:
                    entity["pending"] = remaining
                else:
                    entity.pop("pending")
        if updated:
            changes.append({"path": unit.metadata.path, "before_digest": unit.metadata.digest,
                            "content": json.dumps(value, indent=2) + "\n"})
    return changes, confirmed, sorted(set(missing))


def confirm_pending_units(repository: DocumentUnitRepository) -> tuple[list[dict], list[str]]:
    """Confirm materialized entries without editing reading prose or losing pending intentions."""
    if repository.document_overrides or repository._registry_override is not None:
        raise SpecError("pending confirmation requires an on-disk base", "invalid_proposal")
    changes, confirmed, missing = pending_changes(repository)
    if not changes:
        return confirmed, missing
    candidate = DocumentUnitRepository(repository.root, registry_path=repository.registry_path,
        registry_bytes=repository.registry_bytes,
        document_overrides={item["path"]: item["content"].encode("utf-8") for item in changes})
    candidate.validate()
    expected = candidate.context_identities()
    if repository.fresh().context_identities() != repository.context_identities():
        raise SpecError("context changed before pending confirmation", "stale_proposal")

    def verify():
        current = repository.fresh()
        current.validate()
        if current.registry_bytes != repository.registry_bytes or current.context_identities() != expected:
            raise SpecError("context changed during pending confirmation", "stale_proposal")

    apply_files(repository.root, changes, {metadata_path(path) for path in repository.document_targets}, verify=verify)
    return confirmed, missing
