"""Deterministic structural validation for Concorde Source Profile 1."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any, Iterable

from .diagnostics import finding_key
from .model import Finding, OperationResult, SourceDocument
from .repository import ProjectRepository, RepositoryError
from .validation.hierarchy import validate_hierarchy
from .validation.contracts import validate_contracts
from .validation.scenarios import validate_scenarios
from .validation.layout import validate_layout
from .validation.evidence import validate_evidence
from .validation.freshness import validate_freshness


EVIDENCE_STATES = {"unknown", "partial", "verified", "disagrees", "implemented"}
REQUIRED_CONTRACT_SECTIONS = ("Purpose", "Information", "Obligations", "Failure Semantics", "Compatibility", "Evidence")
FOCUSED_VALIDATORS = (
    validate_hierarchy,
    validate_layout,
    validate_contracts,
    validate_scenarios,
    validate_evidence,
    validate_freshness,
)


def _finding(rule: str, source: SourceDocument, message: str, remediation: str, severity: str = "error") -> Finding:
    return Finding(rule, severity, source.path, message, remediation, subject_id=source.identifier)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _cycles(edges: dict[str, list[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cyclic: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            position = trail.index(node) if node in trail else 0
            cyclic.update(trail[position:])
            return
        if node in visited:
            return
        visiting.add(node)
        trail.append(node)
        for neighbor in edges.get(node, []):
            if neighbor in edges:
                visit(neighbor, trail)
        trail.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(edges):
        visit(node, [])
    return cyclic


def _visible_scenario_ids(package: Any) -> set[str]:
    return {
        view.get("id")
        for architecture in package.views.values()
        for view in architecture.get("meta", {}).get("views", [])
        if isinstance(view, dict) and isinstance(view.get("id"), str)
    }


def _target_artifacts(package: Any, target: str | None) -> tuple[str, ...]:
    all_artifacts = sorted([source.path for source in package.sources] + list(package.views) + list(package.diagrams))
    if not target or target in {package.specification_root, "."}:
        return tuple(all_artifacts)
    matches = package.by_id.get(target, ())
    if len(matches) != 1:
        return tuple(all_artifacts)
    source = matches[0]
    module_id = source.identifier if source.kind == "module" else source.metadata.get("module")
    selected = [item.path for item in package.sources if item.identifier == target or item.metadata.get("module") == module_id]
    module = package.by_id.get(module_id, ())
    if len(module) == 1 and isinstance(module[0].metadata.get("view"), str):
        selected.append(module[0].metadata["view"])
    if source.kind == "feature":
        selected.extend(
            item.get("source")
            for item in source.metadata.get("diagrams", [])
            if isinstance(item, dict) and isinstance(item.get("source"), str)
        )
    return tuple(sorted(set(selected)))


def validate_project(project_root: str | Path, target: str | None = None) -> OperationResult:
    operation_target = target or "."
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        finding = Finding("CONCORDE-SOURCE-001", "error", ".concorde/config.json", str(error), "Correct the profile configuration or malformed source and retry.")
        return OperationResult("validate", operation_target, "invalid", findings=(finding,), result={"summary": {"errors": 1, "warnings": 0, "infos": 0}, "source_digest": "sha256:" + "0" * 64})
    findings: list[Finding] = []
    for validator in FOCUSED_VALIDATORS:
        findings.extend(validator(package))
    artifacts = _target_artifacts(package, target)
    if target and target not in {".", package.specification_root} and target not in package.by_id:
        findings.append(Finding("CONCORDE-TARGET-001", "error", ".concorde/config.json", f"Validation target '{target}' is unknown.", "Pass a configured package path or unique stable ID."))

    # Identity and reference resolution.
    for identifier, sources in package.by_id.items():
        if len(sources) > 1:
            for source in sources:
                findings.append(_finding("CONCORDE-ID-001", source, f"Stable ID '{identifier}' is declared {len(sources)} times.", "Assign one unique stable ID per maintained entity."))
    known = set(package.by_id)
    scenario_ids = _visible_scenario_ids(package)
    for source in package.sources:
        metadata = source.metadata
        references: list[tuple[str, str]] = []
        if source.kind == "module":
            if metadata.get("parent"):
                references.append(("parent module", metadata["parent"]))
            references += [("child module", item) for item in _as_list(metadata.get("children"))]
            references += [("owned feature", item) for item in _as_list(metadata.get("features"))]
        elif source.kind == "feature":
            references.append(("providing module", metadata.get("module")))
            references += [("refined feature", item) for item in _as_list(metadata.get("refines"))]
            for scenario in _as_list(metadata.get("scenarios")):
                if scenario not in known and scenario not in scenario_ids and not (isinstance(scenario, str) and scenario.startswith("scenario.")):
                    findings.append(_finding("CONCORDE-SCENARIO-001", source, f"Scenario reference '{scenario}' does not resolve in the current-level view.", "Add the scenario to the owning view or correct the reference."))
        elif source.kind == "contract":
            references.append(("owning module", metadata.get("module")))
            references += [("affected feature", item) for item in _as_list(metadata.get("features"))]
        contract_sets = metadata.get("contracts")
        if isinstance(contract_sets, dict):
            references += [("provided contract", item) for item in _as_list(contract_sets.get("provided"))]
            references += [("required contract", item) for item in _as_list(contract_sets.get("required"))]
        for label, identifier in references:
            if not isinstance(identifier, str) or identifier not in known:
                findings.append(_finding("CONCORDE-REF-001", source, f"{label.title()} reference '{identifier}' does not resolve.", f"Create the referenced entity or correct the {label} entry."))

    # Containment, ownership, and adjacent refinement.
    modules = {item.identifier: item for item in package.documents("module")}
    features = {item.identifier: item for item in package.documents("feature")}
    hierarchy_edges = {identifier: _as_list(source.metadata.get("children")) for identifier, source in modules.items()}
    for identifier in sorted(_cycles(hierarchy_edges)):
        findings.append(_finding("CONCORDE-HIER-001", modules[identifier], f"Module '{identifier}' participates in a containment cycle.", "Remove a child edge so module containment is acyclic."))
    for module_id, module in modules.items():
        for feature_id in _as_list(module.metadata.get("features")):
            feature = features.get(feature_id)
            if feature and feature.metadata.get("module") != module_id:
                findings.append(_finding("CONCORDE-OWN-001", feature, f"Feature is listed by '{module_id}' but declares provider '{feature.metadata.get('module')}'.", "Make the feature and module ownership declarations agree."))
    refinement_edges = {identifier: _as_list(source.metadata.get("refines")) for identifier, source in features.items()}
    for identifier in sorted(_cycles(refinement_edges)):
        findings.append(_finding("CONCORDE-REFINE-002", features[identifier], f"Feature '{identifier}' participates in a refinement cycle.", "Remove a refinement edge so the graph is acyclic."))
    for feature in features.values():
        module_id = feature.metadata.get("module")
        module = modules.get(module_id)
        refinements = _as_list(feature.metadata.get("refines"))
        if module and module.metadata.get("parent") and not refinements and not (feature.metadata.get("internal") and feature.metadata.get("internal_rationale")):
            findings.append(_finding("CONCORDE-REFINE-001", feature, "Lower-level feature has no adjacent parent refinement or internal rationale.", "Reference a feature owned by the parent module, or mark the feature internal with a rationale."))
        for parent_feature_id in refinements:
            parent_feature = features.get(parent_feature_id)
            if module and parent_feature and parent_feature.metadata.get("module") != module.metadata.get("parent"):
                findings.append(_finding("CONCORDE-REFINE-003", feature, f"Refinement '{parent_feature_id}' is not owned by the adjacent parent module.", "Refine a feature owned at the immediately adjacent parent level."))

    # Contract completeness and evidence.
    for source in package.sources:
        metadata = source.metadata
        if source.kind in {"module", "feature"}:
            contract_sets = metadata.get("contracts")
            if not isinstance(contract_sets, dict) or "provided" not in contract_sets or "required" not in contract_sets:
                findings.append(_finding("CONCORDE-CONTRACT-001", source, "Provided and required contract sets must both be explicit.", "Declare contracts.provided and contracts.required, using [] for an empty set."))
            elif source.kind == "feature" and not _as_list(contract_sets.get("provided")):
                findings.append(_finding("CONCORDE-CONTRACT-001", source, "A feature must expose at least one provided contract.", "Declare the provided boundary contract through which the feature is available."))
        if source.kind == "contract":
            for field in ("module", "role", "flow", "counterparties", "representation", "features", "evidence_status"):
                if field not in metadata:
                    findings.append(_finding("CONCORDE-CONTRACT-002", source, f"Contract field '{field}' is missing.", f"Document the contract's {field} explicitly."))
            if metadata.get("role") not in {"provided", "required"} or not _as_list(metadata.get("counterparties")):
                findings.append(_finding("CONCORDE-CONTRACT-002", source, "Contract role or counterparties are incomplete.", "Declare role as provided/required and at least one counterparty or audience."))
            representation = metadata.get("representation", {})
            if not isinstance(representation, dict) or representation.get("kind") not in {"standard", "custom"} or not all(representation.get(field) for field in ("format", "version", "definition")):
                findings.append(_finding("CONCORDE-CONTRACT-003", source, "Contract representation is incomplete.", "Name standard/custom kind, format, version, and authoritative definition."))
            elif representation.get("kind") == "custom" and not (
                _as_list(metadata.get("examples"))
                or representation.get("example")
                or representation.get("examples")
            ):
                findings.append(_finding("CONCORDE-CONTRACT-003", source, "Custom representation has no representative example.", "Reference at least one programmer-readable serialized example."))
            for heading in REQUIRED_CONTRACT_SECTIONS:
                if f"## {heading}" not in source.body:
                    findings.append(_finding("CONCORDE-CONTRACT-004", source, f"Required contract section '{heading}' is missing.", f"Add a ## {heading} section with observable semantics."))
        if source.kind in {"feature", "contract"} and metadata.get("evidence_status") not in EVIDENCE_STATES:
            findings.append(_finding("CONCORDE-EVIDENCE-001", source, f"Evidence status '{metadata.get('evidence_status')}' is not explicit or supported.", "Use unknown, partial, verified, or disagrees and link evidence separately."))

    # Current-level views.
    for module in modules.values():
        children = set(_as_list(module.metadata.get("children")))
        view_path = module.metadata.get("view")
        if children and (not isinstance(view_path, str) or view_path not in package.views):
            findings.append(_finding("CONCORDE-VIEW-001", module, "Non-leaf module does not resolve one architecture view.", "Declare a valid project-relative current-level Archify JSON view."))
            continue
        if isinstance(view_path, str) and view_path in package.views:
            architecture = package.views[view_path]
            components = {component.get("id") for component in architecture.get("components", []) if component.get("id")}
            for view in architecture.get("meta", {}).get("views", []):
                if not isinstance(view, dict):
                    continue
                unknown_focus = set(_as_list(view.get("focus"))) - components
                if unknown_focus:
                    findings.append(_finding("CONCORDE-SCENARIO-002", module, f"View scenario '{view.get('id')}' has unknown participants: {', '.join(sorted(unknown_focus))}.", "Use only component IDs visible at the current module level."))
            for connection in architecture.get("connections", []):
                endpoints = {connection.get("from"), connection.get("to")}
                if not endpoints.issubset(components):
                    findings.append(_finding("CONCORDE-VIEW-004", module, f"Connection '{connection.get('id')}' has an endpoint outside the current view.", "Correct the connection endpoints to visible participant IDs."))
            visible_modules: set[str] = set()
            for component in architecture.get("components", []):
                declared = component.get("module_id")
                if declared:
                    visible_modules.add(declared)
                    continue
                component_id = component.get("id")
                component_names = {str(component_id), str(component.get("label", ""))}
                normalized_components = {re.sub(r"[^a-z0-9]", "", name.lower()) for name in component_names}
                matches = [
                    child
                    for child in children
                    if re.sub(r"[^a-z0-9]", "", child.rsplit(".", 1)[-1].lower()) in normalized_components
                ]
                if len(matches) == 1:
                    visible_modules.add(matches[0])
            invalid = visible_modules - children
            if invalid:
                findings.append(_finding("CONCORDE-VIEW-002", module, f"View exposes non-immediate modules: {', '.join(sorted(invalid))}.", "Keep only immediate child modules in this level's view."))
            missing = children - visible_modules
            if missing:
                findings.append(_finding("CONCORDE-VIEW-003", module, f"View omits immediate modules: {', '.join(sorted(missing))}.", "Add every immediate child module and its I/O to the current-level view."))

    ordered = tuple(sorted(findings, key=finding_key))
    summary = Counter(item.severity for item in ordered)
    status = "invalid" if summary["error"] else "success"
    return OperationResult(
        "validate",
        operation_target,
        status,
        artifacts,
        ordered,
        {"summary": {"errors": summary["error"], "warnings": summary["warning"], "infos": summary["info"]}, "source_digest": package.source_digest},
    )
