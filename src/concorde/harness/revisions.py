"""Revision identities of one Module's Spec, implementation and dependent evidence."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..spec.repository import SpecRepository, digest, read_file


def issues_revision(root: Path) -> str:
    from ..issues.store import list_issues

    return digest([(item["id"], item["revision"]) for item in list_issues(root)])


def implementation_digest(repository: SpecRepository, target) -> str:
    """Digest the declared listing entries and the bytes of every file they currently bind."""
    return digest(
        {
            "listed": list(target.files),
            "files": [
                (path, digest(read_file(repository.root, path)))
                for path in repository.implementation_files(target)
            ],
        }
    )


def implementation_users(repository: SpecRepository, target) -> tuple:
    """Every Module whose entries cover one of these entries or bound files, with no context union."""
    affected = {
        target.id,
        *(module.id for module in repository.covering_modules(target)),
    }
    return tuple(
        module for module in repository.targets.values() if module.id in affected
    )


def unconfirmed_files(repository: SpecRepository, target) -> list[str]:
    """Listed entries that neither exist nor are explicitly declared pending by their entity."""
    entities = repository.entity_files(target)
    return sorted(
        entry
        for entry in repository.missing_entries(target)
        if entry not in entities or entry not in entities[entry].pending
    )


def impact_revisions(repository: SpecRepository, targets) -> list[dict]:
    return [
        {
            "target_id": target.id,
            "spec_digest": target_revision(repository, target),
            "implementation_digest": implementation_digest(repository, target),
        }
        for target in targets
    ]


def target_revision(repository: SpecRepository, target) -> str:
    return digest(
        {
            "target": asdict(target),
            "protocol": repository.config["protocol"],
            "spec_resolution": repository.spec_context(target.id).value,
        }
    )
