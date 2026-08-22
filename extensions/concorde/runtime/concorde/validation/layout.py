"""Durable feature-root and temporal implementation layout rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..model import Finding
from ..repository import ProjectRepository, RepositoryError, safe_relative_path


FORBIDDEN_ROOT_FILES = ("plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md", "validation.md")


def validate_layout(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for feature in package.documents("feature"):
        root = package.project_root / Path(feature.path).parent
        if feature.metadata.get("canonical_spec") != feature.path:
            findings.append(Finding("CONCORDE-LAYOUT-002", "error", feature.path, "canonical_spec does not equal this feature's own spec.md path.", "Set canonical_spec to the one durable feature specification.", subject_id=feature.identifier))
        for name in FORBIDDEN_ROOT_FILES:
            path = root / name
            if path.exists():
                relative = path.relative_to(package.project_root).as_posix()
                findings.append(Finding("CONCORDE-LAYOUT-001", "error", relative, f"Temporal artifact '{name}' is stored at the durable feature root.", f"Move {name} below the feature's implementation/ directory and remove the root alias.", subject_id=feature.identifier))
        implementation = root / "implementation"
        if implementation.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-003", "error", implementation.relative_to(package.project_root).as_posix(), "implementation/ may not be a symlink.", "Use one real project-contained temporal implementation directory.", subject_id=feature.identifier))
    selection = package.project_root / ".specify" / "feature.json"
    if selection.is_file():
        try:
            value = json.loads(selection.read_text(encoding="utf-8"))
            selected = safe_relative_path(value["feature_directory"])
            resolved = ProjectRepository(package.project_root).resolve(selected)
            if not (resolved / "spec.md").is_file():
                raise RepositoryError("selected root has no spec.md")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, RepositoryError) as error:
            findings.append(Finding("CONCORDE-LAYOUT-004", "error", ".specify/feature.json", f"Selected feature workspace is invalid: {error}", "Select one existing safe canonical feature root."))
    return findings
