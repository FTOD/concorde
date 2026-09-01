"""Recursive module containment, inventory, and canonical-path rules."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from ..model import Finding, SourceDocument


def _finding(rule: str, source: SourceDocument, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source.path, message, remediation, subject_id=source.identifier)


def _as_ids(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return tuple(value)


def _cycles(edges: dict[str, tuple[str, ...]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cyclic: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            cyclic.update(trail[trail.index(node) :] if node in trail else trail)
            return
        if node in visited:
            return
        visiting.add(node)
        trail.append(node)
        for child in edges.get(node, ()):
            if child in edges:
                visit(child, trail)
        trail.pop()
        visiting.remove(node)
        visited.add(node)

    for identifier in sorted(edges):
        visit(identifier, [])
    return cyclic


def validate_hierarchy(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    module_sources = {source.identifier: source for source in package.documents("module")}
    feature_sources = {source.identifier: source for source in package.documents("feature")}
    edges: dict[str, tuple[str, ...]] = {}

    for module_id, source in module_sources.items():
        declared_modules = _as_ids(source.metadata.get("modules"))
        declared_features = _as_ids(source.metadata.get("features"))
        if declared_modules is None:
            findings.append(_finding("CONCORDE-MODULE-001", source, "modules must be an explicit ordered list of immediate module IDs.", "Use [] or list each physical child module once."))
            declared_modules = ()
        if declared_features is None:
            findings.append(_finding("CONCORDE-MODULE-001", source, "features must be an explicit ordered list of level-local feature IDs.", "Use [] or list each direct features/*.md file once."))
            declared_features = ()
        if len(declared_modules) != len(set(declared_modules)) or len(declared_features) != len(set(declared_features)):
            findings.append(_finding("CONCORDE-MODULE-002", source, "A module or feature inventory contains duplicate IDs.", "Keep each immediate child and level-local feature exactly once."))
        edges[module_id] = declared_modules

        module_dir = PurePosixPath(source.path).parent
        parent_id = source.metadata.get("parent")
        if parent_id is None:
            if module_id != package.root_module_id or module_dir.as_posix() != package.specification_root:
                findings.append(_finding("CONCORDE-HIER-002", source, "A parentless module is not the configured root architecture.", "Keep exactly one parentless root at <specification_root>/architecture.md."))
        elif not isinstance(parent_id, str) or parent_id not in module_sources:
            findings.append(_finding("CONCORDE-REF-001", source, f"Parent module reference '{parent_id}' does not resolve.", "Reference the physical parent module's stable ID."))
        else:
            parent = module_sources[parent_id]
            expected = PurePosixPath(parent.path).parent / "modules"
            if module_dir.parent != expected:
                findings.append(_finding("CONCORDE-HIER-003", source, f"Child module is not directly beneath '{expected}/'.", "Move it to the physical parent's modules/<name>/ directory."))
            parent_modules = _as_ids(parent.metadata.get("modules")) or ()
            if module_id not in parent_modules:
                findings.append(_finding("CONCORDE-HIER-004", source, f"Parent '{parent_id}' does not inventory this child.", "Add the child ID to the parent's modules list."))

        physical_modules = {
            candidate.identifier
            for candidate in module_sources.values()
            if PurePosixPath(candidate.path).parent.parent == module_dir / "modules"
        }
        physical_features = {
            candidate.identifier
            for candidate in feature_sources.values()
            if PurePosixPath(candidate.path).parent == module_dir / "features"
        }
        if set(declared_modules) != physical_modules:
            findings.append(_finding("CONCORDE-MODULE-003", source, "Declared module inventory does not match immediate physical modules; declared " + repr(sorted(declared_modules)) + ", physical " + repr(sorted(physical_modules)) + ".", "Reconcile modules with direct modules/*/architecture.md children."))
        if set(declared_features) != physical_features:
            findings.append(_finding("CONCORDE-MODULE-004", source, "Declared feature inventory does not match level-local feature files; declared " + repr(sorted(declared_features)) + ", physical " + repr(sorted(physical_features)) + ".", "Reconcile features with direct features/*.md files."))
        for feature_id in declared_features:
            feature = feature_sources.get(feature_id)
            if feature is None:
                findings.append(_finding("CONCORDE-REF-001", source, f"Owned feature reference '{feature_id}' does not resolve.", "Create or correct the level-local feature design."))
            elif feature.metadata.get("module") != module_id:
                findings.append(Finding("CONCORDE-OWN-001", "error", feature.path, f"Feature is inventoried by '{module_id}' but declares provider '{feature.metadata.get('module')}'.", "Make physical placement, module front matter, and provider identity agree.", subject_id=feature.identifier))

    for identifier in sorted(_cycles(edges)):
        findings.append(_finding("CONCORDE-HIER-001", module_sources[identifier], f"Module '{identifier}' participates in a containment cycle.", "Remove a modules edge so containment is rooted and acyclic."))
    return findings
