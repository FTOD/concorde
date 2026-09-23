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
                for path in repository.bound_files(target)
            ],
        }
    )


def unconfirmed_files(repository: SpecRepository, target) -> list[str]:
    """Realization entries that neither exist nor are declared pending by their realization."""
    realizations = repository.realization_entries(target)
    return sorted(
        entry
        for entry in repository.missing_entries(target)
        if entry not in realizations or entry not in realizations[entry].pending
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
