"""Canonical Profile 7 specification and project-control layout rules."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from ..model import Finding
from ..repository import (
    FEATURE_ID,
    ProjectRepository,
    RepositoryError,
    classify_feature_path,
    safe_relative_path,
)


TEMPORAL_ROOT_FILES = (
    "plan.md",
    "tasks.md",
    "research.md",
    "data-model.md",
    "quickstart.md",
    "validation.md",
)
LEGACY_FILES = {
    "module.md": "replace it with the module's architecture.md",
    "design.md": "move the complete feature design to a direct features/<NNN-name>.md file",
    "abstract.md": "reconcile purpose and usage into the direct feature file, then remove it",
    "implementation.md": "use source code and tests as realization authority, then remove it",
    "contract.md": "embed the interface in its owning feature file",
    "spec.md": "use the direct feature file as the one feature specification",
    "tldr.md": "use the direct feature file directly",
    "reflections.md": "move each project reflection to .concorde/reflections/R-NNN.md",
}
LEGACY_DIRECTORIES = {
    "subfeatures": "flatten features into the providing module's features/ directory and use related_features",
    "contracts": "embed interfaces in the owning direct feature file",
    "attempts": "move temporal work to .concorde/attempts/<stable-feature-id>/",
}


def _relative(package: Any, path: Path) -> str:
    return path.relative_to(package.project_root).as_posix()


def _finding(
    package: Any,
    rule: str,
    path: Path,
    message: str,
    remediation: str,
    subject_id: str | None = None,
) -> Finding:
    return Finding(
        rule,
        "error",
        _relative(package, path),
        message,
        remediation,
        subject_id=subject_id,
    )


def _case_collisions(entries: Iterable[Path]) -> list[list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in entries:
        key = path.stem if path.is_file() or path.suffix == ".md" else path.name
        groups[key.casefold()].append(path)
    return [sorted(paths) for paths in groups.values() if len(paths) > 1]


def _symlink_findings(package: Any, attempt: Path, subject_id: str | None) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(attempt.rglob("*")):
        if path.is_symlink():
            findings.append(
                _finding(
                    package,
                    "CONCORDE-LAYOUT-003",
                    path,
                    "Attempt artifacts and directories may not be symlinks.",
                    "Replace the unsafe path with a real project-contained artifact.",
                    subject_id,
                )
            )
    return findings


def validate_layout(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    specification = package.project_root / package.specification_root

    for path in sorted(specification.rglob("*")):
        if path.name in LEGACY_FILES and path.is_file():
            findings.append(
                _finding(
                    package,
                    "CONCORDE-LAYOUT-LEGACY",
                    path,
                    f"Legacy durable artifact '{path.name}' remains in the Profile 7 specification tree.",
                    LEGACY_FILES[path.name],
                )
            )
        if path.name in LEGACY_DIRECTORIES and path.is_dir():
            findings.append(
                _finding(
                    package,
                    "CONCORDE-LAYOUT-LEGACY",
                    path,
                    f"Legacy specification directory '{path.name}/' remains in the Profile 7 tree.",
                    LEGACY_DIRECTORIES[path.name],
                )
            )

    modules = {source.identifier: source for source in package.documents("module")}
    module_directories = {
        PurePosixPath(source.path).parent.as_posix(): source for source in modules.values()
    }
    feature_sources = {source.path: source for source in package.documents("feature")}

    for relative, module in module_directories.items():
        root = package.project_root / relative
        allowed = {"architecture.md", "modules", "features", "diagrams"}
        for child in sorted(root.iterdir()):
            if child.name.startswith("."):
                continue
            if child.name in TEMPORAL_ROOT_FILES:
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-001",
                        child,
                        f"Temporal artifact '{child.name}' is stored at the durable module root.",
                        f"Move {child.name} below .concorde/attempts/<stable-feature-id>/.",
                        module.identifier,
                    )
                )
                continue
            if child.name in {"attempts", "reflections.md"}:
                if child.is_symlink():
                    findings.append(
                        _finding(
                            package,
                            "CONCORDE-LAYOUT-003",
                            child,
                            f"Legacy control-state entry '{child.name}' may not be a symlink.",
                            "Remove the legacy entry and use real project-contained .concorde control state.",
                            module.identifier,
                        )
                    )
                continue
            if child.name not in allowed:
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-010",
                        child,
                        f"Module root entry '{child.name}' is not part of Profile 7.",
                        "Keep architecture.md, immediate modules/, direct features/, and architecture-owned diagrams/ only.",
                        module.identifier,
                    )
                )
            elif child.is_symlink():
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-003",
                        child,
                        f"Module entry '{child.name}' may not be a symlink.",
                        "Replace the unsafe path with a real project-contained file or directory.",
                        module.identifier,
                    )
                )

        features_dir = root / "features"
        if features_dir.exists() or features_dir.is_symlink():
            if features_dir.is_symlink() or not features_dir.is_dir():
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-006",
                        features_dir,
                        "features/ must be one real module-local directory.",
                        "Replace it with a real directory containing only direct <NNN-name>.md files.",
                        module.identifier,
                    )
                )
            else:
                entries = [path for path in sorted(features_dir.iterdir()) if not path.name.startswith(".")]
                for collision in _case_collisions(entries):
                    names = ", ".join(path.name for path in collision)
                    for path in collision:
                        findings.append(
                            _finding(
                                package,
                                "CONCORDE-LAYOUT-013",
                                path,
                                f"Feature storage names collide after case normalization: {names}.",
                                "Choose one unique lowercase canonical feature basename.",
                                module.identifier,
                            )
                        )
                for path in entries:
                    relative_feature = _relative(package, path)
                    if path.is_symlink():
                        findings.append(
                            _finding(
                                package,
                                "CONCORDE-LAYOUT-003",
                                path,
                                "Feature files may not be symlinks.",
                                "Replace the symlink with one real direct Markdown file.",
                                module.identifier,
                            )
                        )
                        continue
                    if not path.is_file():
                        findings.append(
                            _finding(
                                package,
                                "CONCORDE-LAYOUT-006",
                                path,
                                "Feature wrapper directories are invalid in Profile 7.",
                                "Move the complete design to features/<NNN-name>.md and remove the wrapper.",
                                module.identifier,
                            )
                        )
                        continue
                    try:
                        _, physical_module = classify_feature_path(
                            relative_feature, package.specification_root
                        )
                        if physical_module != relative:
                            raise RepositoryError("feature is not owned by this physical module")
                    except RepositoryError as error:
                        findings.append(
                            _finding(
                                package,
                                "CONCORDE-LAYOUT-006",
                                path,
                                str(error),
                                "Use one direct lowercase <module>/features/<NNN-name>.md file.",
                                module.identifier,
                            )
                        )
                        continue
                    if relative_feature not in feature_sources:
                        findings.append(
                            _finding(
                                package,
                                "CONCORDE-LAYOUT-006",
                                path,
                                "Canonical feature file was not discovered as a valid feature source.",
                                "Correct its front matter and reload the Profile 7 project.",
                                module.identifier,
                            )
                        )

    reflection_directory = package.project_root / ".concorde" / "reflections"
    if reflection_directory.is_dir() and not reflection_directory.is_symlink():
        for path in sorted(reflection_directory.iterdir()):
            if path.name == "log.md":
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-LEGACY",
                        path,
                        "The single-file reflection log is obsolete.",
                        "Split each entry into .concorde/reflections/R-NNN.md and keep allocation state only in index.json.",
                    )
                )
            elif path.name.startswith("R-") and path.suffix == ".md" and not re.fullmatch(
                r"R-(?:\d{3}|[1-9]\d{3,})\.md", path.name
            ):
                findings.append(
                    _finding(
                        package,
                        "CONCORDE-LAYOUT-012",
                        path,
                        "Reflection filename is not a canonical R-NNN.md identity.",
                        "Use exactly the identifier returned by the allocation helper.",
                    )
                )

    feature_ids: dict[str, list[Any]] = defaultdict(list)
    for source in package.documents("feature"):
        feature_ids[source.identifier].append(source)
    attempts_dir = package.project_root / ".concorde" / "attempts"
    if attempts_dir.exists() or attempts_dir.is_symlink():
        if attempts_dir.is_symlink() or not attempts_dir.is_dir():
            findings.append(
                _finding(
                    package,
                    "CONCORDE-LAYOUT-003",
                    attempts_dir,
                    ".concorde/attempts must be one real project-control directory.",
                    "Replace it with a real directory containing only stable-feature-ID attempts.",
                )
            )
        else:
            entries = list(sorted(attempts_dir.iterdir()))
            visible_entries = [path for path in entries if not path.name.startswith(".")]
            for collision in _case_collisions(visible_entries):
                names = ", ".join(path.name for path in collision)
                for path in collision:
                    findings.append(
                        _finding(
                            package,
                            "CONCORDE-LAYOUT-013",
                            path,
                            f"Attempt stable IDs collide after case normalization: {names}.",
                            "Keep one exact lowercase attempt directory per stable feature ID.",
                        )
                    )
            for attempt in entries:
                if attempt.name.startswith("."):
                    findings.append(
                        _finding(
                            package,
                            "CONCORDE-LAYOUT-003",
                            attempt,
                            "A stale or unrecognized attempt recovery artifact exists.",
                            "Recover or remove the feature-specific tombstone before continuing.",
                        )
                    )
                    continue
                if attempt.is_symlink() or not attempt.is_dir():
                    reason = "may not be a symlink" if attempt.is_symlink() else "must be a directory"
                    findings.append(
                        _finding(
                            package,
                            "CONCORDE-LAYOUT-003",
                            attempt,
                            f"Each attempt {reason}; it must be one real directory.",
                            "Use one real .concorde/attempts/<stable-feature-id>/ directory.",
                        )
                    )
                    continue
                if not FEATURE_ID.fullmatch(attempt.name):
                    findings.append(
                        _finding(
                            package,
                            "CONCORDE-LAYOUT-012",
                            attempt,
                            "Attempt directory name is not a canonical stable feature ID.",
                            "Use the exact lowercase qualified feature.* identity.",
                        )
                    )
                matches = feature_ids.get(attempt.name, [])
                if len(matches) != 1:
                    case_match = next(
                        (identifier for identifier in feature_ids if identifier.casefold() == attempt.name.casefold()),
                        None,
                    )
                    rule = "CONCORDE-LAYOUT-013" if case_match else "CONCORDE-LAYOUT-012"
                    detail = (
                        f"Attempt stable ID differs in case from feature '{case_match}'."
                        if case_match
                        else "Attempt is orphaned because no unique feature has its exact stable ID."
                    )
                    findings.append(
                        _finding(
                            package,
                            rule,
                            attempt,
                            detail,
                            "Restore the exact feature identity or explicitly reconcile the stable-ID change and attempt together.",
                        )
                    )
                subject = matches[0].identifier if len(matches) == 1 else None
                findings.extend(_symlink_findings(package, attempt, subject))

    selection = package.project_root / ".concorde" / "feature.json"
    if selection.exists() or selection.is_symlink():
        try:
            if selection.is_symlink() or not selection.is_file():
                raise RepositoryError("selection must be one real JSON file")
            value = json.loads(selection.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or set(value) != {"feature_path"}:
                raise RepositoryError("selection must contain only feature_path")
            selected = safe_relative_path(value["feature_path"])
            resolved = ProjectRepository(package.project_root).resolve(selected)
            classify_feature_path(selected, package.specification_root)
            if resolved.is_symlink() or not resolved.is_file():
                raise RepositoryError("selected feature_path is not one real file")
            if selected not in feature_sources:
                raise RepositoryError("selected feature_path is not one discovered direct feature")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, RepositoryError) as error:
            findings.append(
                Finding(
                    "CONCORDE-LAYOUT-004",
                    "error",
                    ".concorde/feature.json",
                    f"Selected feature workspace is invalid: {error}",
                    "Select one existing safe Profile 7 feature_path.",
                )
            )
    return findings
