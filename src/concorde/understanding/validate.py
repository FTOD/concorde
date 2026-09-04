"""Deterministic structural validation for Concorde Source Profile 7."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..diagnostics import digest_sources, finding_key
from ..model import Finding, SourceDocument, ToolResult
from .repository import ProjectRepository, RepositoryError
from .validation.diagrams import validate_diagrams
from .validation.entities import validate_entities
from .validation.evidence import validate_evidence
from .validation.features import validate_features
from .validation.freshness import validate_freshness
from .validation.hierarchy import validate_hierarchy
from .validation.layout import validate_layout
from ..reflections.validation import validate_reflections
from ..capabilities.validation import capability_source_paths, validate_capabilities


FOCUSED_VALIDATORS = (
    validate_hierarchy,
    validate_entities,
    validate_features,
    validate_layout,
    validate_diagrams,
    validate_reflections,
    validate_evidence,
    validate_freshness,
    validate_capabilities,
)


def _finding(rule: str, source: SourceDocument, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source.path, message, remediation, subject_id=source.identifier)


def _target_artifacts(package, target: str | None) -> tuple[str, ...]:
    all_artifacts = sorted(
        [source.path for source in package.sources]
        + list(package.diagrams)
        + list(capability_source_paths(package.project_root))
    )
    if not target or target in {package.specification_root, "."}:
        return tuple(all_artifacts)
    matches = package.by_id.get(target, ())
    if len(matches) != 1:
        return tuple(all_artifacts)
    source = matches[0]
    module_id = source.identifier if source.kind == "module" else source.metadata.get("module")
    selected = [item.path for item in package.sources if item.identifier == target or item.metadata.get("module") == module_id]
    module = package.by_id.get(module_id, ())
    if len(module) == 1 and module[0].kind == "module":
        selected.extend(package.module_diagrams(module[0]))
    return tuple(sorted(set(selected)))


def validate_project(project_root: str | Path, target: str | None = None) -> ToolResult:
    tool_target = target or "."
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        finding = Finding("CONCORDE-SOURCE-001", "error", ".concorde/config.json", str(error), "Correct the Profile 7 configuration or malformed architecture/feature/control-state source and retry.")
        return ToolResult("validate", tool_target, "invalid", findings=(finding,), result={"summary": {"errors": 1, "warnings": 0, "infos": 0}, "source_digest": "sha256:" + "0" * 64})

    findings: list[Finding] = []
    for validator in FOCUSED_VALIDATORS:
        findings.extend(validator(package))
    artifacts = _target_artifacts(package, target)
    if target and target not in {".", package.specification_root} and target not in package.by_id:
        findings.append(Finding("CONCORDE-TARGET-001", "error", ".concorde/config.json", f"Validation target '{target}' is unknown.", "Pass the specification root or one unique module/feature stable ID."))

    for identifier, sources in package.by_id.items():
        if len(sources) > 1:
            for source in sources:
                findings.append(_finding("CONCORDE-ID-001", source, f"Stable ID '{identifier}' is declared {len(sources)} times.", "Keep one unique module or feature declaration per stable ID."))
    roots = [source for source in package.documents("module") if source.metadata.get("parent") is None]
    configured = package.by_id.get(package.root_module_id, ())
    if len(roots) != 1 or len(configured) != 1 or configured[0] not in roots:
        findings.append(Finding("CONCORDE-HIER-005", "error", f"{package.specification_root}/architecture.md", "Configured root_module_id does not identify the one parentless root architecture.", "Reconcile configuration, root front matter, and physical containment."))

    ordered = tuple(sorted(findings, key=finding_key))
    summary = Counter(item.severity for item in ordered)
    digest_paths = (
        [source.path for source in package.sources]
        + list(package.diagrams)
        + list(package.auxiliary)
        + list(capability_source_paths(package.project_root))
    )
    source_digest = digest_sources(package.project_root, digest_paths)
    return ToolResult(
        "validate",
        tool_target,
        "invalid" if summary["error"] else "success",
        artifacts,
        ordered,
        {"summary": {"errors": summary["error"], "warnings": summary["warning"], "infos": summary["info"]}, "source_digest": source_digest},
    )
