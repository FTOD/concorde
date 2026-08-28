"""Durable feature-root and temporal implementation layout rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..model import Finding
from ..repository import ProjectRepository, RepositoryError, classify_feature_root, safe_relative_path


FORBIDDEN_ROOT_FILES = ("plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md", "validation.md")


def validate_layout(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for feature in package.documents("feature"):
        root = package.project_root / Path(feature.path).parent
        try:
            level, parent_root = classify_feature_root(Path(feature.path).parent.as_posix(), package.specification_root)
        except RepositoryError as error:
            findings.append(Finding("CONCORDE-LAYOUT-006", "error", feature.path, str(error), "Use exactly one canonical feature or immediate sub-feature root.", subject_id=feature.identifier))
            level, parent_root = "invalid", None
        if level == "feature" and feature.metadata.get("parent_feature"):
            findings.append(Finding("CONCORDE-LAYOUT-006", "error", feature.path, "Top-level canonical path declares parent_feature.", "Remove parent_feature or move the source beneath its parent's subfeatures/ directory.", subject_id=feature.identifier))
        if level == "subfeature" and not feature.metadata.get("parent_feature"):
            findings.append(Finding("CONCORDE-LAYOUT-006", "error", feature.path, "Sub-feature canonical path has no parent_feature.", "Declare the immediate parent feature ID.", subject_id=feature.identifier))
        if feature.metadata.get("canonical_spec") != feature.path:
            findings.append(Finding("CONCORDE-LAYOUT-002", "error", feature.path, "canonical_spec does not equal this feature's own spec.md path.", "Set canonical_spec to the one durable feature specification.", subject_id=feature.identifier))
        design = root / "design.md"
        tldr = root / "tldr.md"
        legacy = root / "implementation.md"
        relative_root = Path(feature.path).parent.as_posix()
        if legacy.exists() and design.exists():
            findings.append(Finding("CONCORDE-LAYOUT-008", "error", f"{relative_root}/implementation.md", "The feature root holds both implementation.md and design.md; the accepted realization is ambiguous.", "Merge any remaining content into design.md and remove the legacy implementation.md.", subject_id=feature.identifier))
        elif legacy.exists():
            findings.append(Finding("CONCORDE-LAYOUT-007", "error", f"{relative_root}/implementation.md", "The feature root uses the legacy accepted-realization name implementation.md.", "Rename implementation.md to design.md; design.md is the design reference at every level.", subject_id=feature.identifier))
        elif not design.is_file() or design.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-005", "error", f"{relative_root}/design.md", "The feature has no real durable design.md.", "Create design.md at the feature root from the design-template; before the first hardening, state that no realization has been hardened.", subject_id=feature.identifier))
        if not tldr.is_file() or tldr.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-009", "error", f"{relative_root}/tldr.md", "The feature has no real tldr.md.", "Author the feature TL;DR from the tldr-template with the sections Purpose, Functionality, Structure, Logic, and Read Next.", subject_id=feature.identifier))
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
            classify_feature_root(selected, package.specification_root)
            if (resolved / "implementation.md").exists():
                raise RepositoryError("selected root still holds a legacy implementation.md; rename it to design.md")
            if not all((resolved / name).is_file() for name in ("tldr.md", "spec.md", "design.md")):
                raise RepositoryError("selected root has no canonical tldr.md, spec.md, and design.md trio")
            if not any(Path(feature.path).parent.as_posix() == selected for feature in package.documents("feature")):
                raise RepositoryError("selected root is not one discovered canonical lifecycle root")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, RepositoryError) as error:
            findings.append(Finding("CONCORDE-LAYOUT-004", "error", ".specify/feature.json", f"Selected feature workspace is invalid: {error}", "Select one existing safe canonical feature root."))
    return findings
