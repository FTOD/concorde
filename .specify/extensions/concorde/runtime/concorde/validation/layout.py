"""Durable feature-root and temporal attempt layout rules."""

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
        if feature.metadata.get("canonical_design") != feature.path:
            findings.append(Finding("CONCORDE-LAYOUT-002", "error", feature.path, "canonical_design does not equal this feature's own design.md path.", "Set canonical_design to the one durable feature design authority.", subject_id=feature.identifier))
        abstract = root / "abstract.md"
        implementation = root / "implementation.md"
        legacy_spec = root / "spec.md"
        legacy_tldr = root / "tldr.md"
        relative_root = Path(feature.path).parent.as_posix()
        if legacy_spec.exists() or legacy_tldr.exists():
            legacy_names = ", ".join(name for name, path in (("spec.md", legacy_spec), ("tldr.md", legacy_tldr)) if path.exists())
            findings.append(Finding("CONCORDE-LAYOUT-007", "error", relative_root, f"The feature root still uses legacy document names: {legacy_names}.", "Rename tldr.md to abstract.md, spec.md to design.md, and the former feature design.md to implementation.md.", subject_id=feature.identifier))
        if not implementation.is_file() or implementation.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-005", "error", f"{relative_root}/implementation.md", "The feature has no real durable implementation.md.", "Create implementation.md at the feature root from the implementation-template; before the first hardening, state that no realization has been hardened.", subject_id=feature.identifier))
        if not abstract.is_file() or abstract.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-009", "error", f"{relative_root}/abstract.md", "The feature has no real abstract.md.", "Author the feature abstract from the abstract-template with the sections Purpose, Functionality, Structure, Logic, and Read Next.", subject_id=feature.identifier))
        for name in FORBIDDEN_ROOT_FILES:
            path = root / name
            if path.exists():
                relative = path.relative_to(package.project_root).as_posix()
                findings.append(Finding("CONCORDE-LAYOUT-001", "error", relative, f"Temporal artifact '{name}' is stored at the durable feature root.", f"Move {name} below the feature's attempt/ directory and remove the root alias.", subject_id=feature.identifier))
        attempt = root / "attempt"
        if attempt.is_symlink():
            findings.append(Finding("CONCORDE-LAYOUT-003", "error", attempt.relative_to(package.project_root).as_posix(), "attempt/ may not be a symlink.", "Use one real project-contained temporal attempt directory.", subject_id=feature.identifier))
        legacy_attempt = root / "implementation"
        if legacy_attempt.exists():
            findings.append(Finding("CONCORDE-LAYOUT-008", "error", legacy_attempt.relative_to(package.project_root).as_posix(), "The feature root still uses the legacy implementation/ attempt directory.", "Rename implementation/ to attempt/.", subject_id=feature.identifier))
    selection = package.project_root / ".specify" / "feature.json"
    if selection.is_file():
        try:
            value = json.loads(selection.read_text(encoding="utf-8"))
            selected = safe_relative_path(value["feature_directory"])
            resolved = ProjectRepository(package.project_root).resolve(selected)
            classify_feature_root(selected, package.specification_root)
            if any((resolved / name).exists() for name in ("tldr.md", "spec.md", "implementation")):
                raise RepositoryError("selected root still uses legacy feature names")
            if not all((resolved / name).is_file() for name in ("abstract.md", "design.md", "implementation.md")):
                raise RepositoryError("selected root has no canonical abstract.md, design.md, and implementation.md trio")
            if not any(Path(feature.path).parent.as_posix() == selected for feature in package.documents("feature")):
                raise RepositoryError("selected root is not one discovered canonical lifecycle root")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, RepositoryError) as error:
            findings.append(Finding("CONCORDE-LAYOUT-004", "error", ".specify/feature.json", f"Selected feature workspace is invalid: {error}", "Select one existing safe canonical feature root."))
    return findings
