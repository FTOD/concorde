"""Explicit evidence-reference validation without correctness inference."""

from __future__ import annotations

import hashlib
from typing import Any

from ...model import Finding
from ..repository import ProjectRepository, RepositoryError, safe_relative_path


KINDS = {"implementation", "test", "validation", "generated"}
STATES = {"unknown", "partial", "verified", "disagrees"}


def validate_evidence(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    repository = ProjectRepository(package.project_root)
    for source in package.sources:
        references = source.metadata.get("evidence", [])
        if not isinstance(references, list):
            references = []
        for reference in references:
            if not isinstance(reference, dict):
                findings.append(Finding("CONCORDE-EVIDENCE-003", "error", source.path, "Evidence reference must be a structured mapping.", "Declare kind, target, status, and producer for each evidence reference.", subject_id=source.identifier))
                continue
            kind, status, target = reference.get("kind"), reference.get("status"), reference.get("target")
            if kind not in KINDS or status not in STATES or not isinstance(target, str):
                findings.append(Finding("CONCORDE-EVIDENCE-003", "error", source.path, "Evidence kind, target, or status is incomplete.", "Use a supported kind/status and one safe reviewable target.", subject_id=source.identifier))
                continue
            try:
                path = repository.resolve(safe_relative_path(target))
            except RepositoryError as error:
                findings.append(Finding("CONCORDE-EVIDENCE-003", "error", source.path, f"Evidence target is unsafe: {error}", "Use a project-relative confined evidence target.", subject_id=source.identifier))
                continue
            if status == "verified" and not path.is_file():
                findings.append(Finding("CONCORDE-EVIDENCE-002", "error", source.path, f"Verified evidence target '{target}' is missing.", "Restore the evidence, or mark its status unknown/disagrees until it is reviewable.", subject_id=source.identifier))
                continue
            expected = reference.get("source_digest")
            if status == "verified" and isinstance(expected, str) and path.is_file():
                actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != expected:
                    findings.append(Finding("CONCORDE-EVIDENCE-002", "error", source.path, f"Verified evidence target '{target}' disagrees with digest {expected}.", "Regenerate/review the evidence and record its actual digest or mark disagreement.", subject_id=source.identifier))
    return findings
