"""Normalize delegated Archify and generated-projection provenance receipts."""

from __future__ import annotations

from typing import Any

from ..diagnostics import digest_sources
from ..model import Finding
from ..repository import ProjectRepository, RepositoryError, safe_relative_path


def validate_freshness(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    repository = ProjectRepository(package.project_root)
    for receipt_path, receipt in package.receipts.items():
        producer = receipt.get("producer")
        sources = receipt.get("source_paths")
        expected = receipt.get("source_digest")
        output = receipt.get("output")
        try:
            if not isinstance(producer, str) or not isinstance(sources, list) or not all(isinstance(item, str) for item in sources) or not isinstance(expected, str) or not isinstance(output, str):
                raise RepositoryError("receipt requires producer, source_paths, source_digest, and output")
            safe_sources = [safe_relative_path(item) for item in sources]
            actual = digest_sources(package.project_root, safe_sources)
            output_path = repository.resolve(safe_relative_path(output))
        except (RepositoryError, OSError) as error:
            findings.append(Finding("CONCORDE-FRESHNESS-002", "error", receipt_path, f"Freshness receipt is invalid: {error}", "Regenerate a complete receipt with the owning deterministic tool."))
            continue
        if actual != expected or not output_path.is_file():
            findings.append(Finding("CONCORDE-FRESHNESS-001", "error", receipt_path, f"{producer} projection is stale or missing for source digest {actual}.", f"Run the owning {producer} validation/build and replace its provenance receipt."))
    return findings
