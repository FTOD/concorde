"""Direct feature, embedded-interface, and architecture-zoom rules for Profile 7."""

from __future__ import annotations

import re
from typing import Any

from ...model import Finding, SourceDocument
from ..repository import FEATURE_ID, architecture_zoom_rows
from .entities import visible_entity_ids


INTERFACE_ID = re.compile(r"^(?:interface|contract)\.[a-z0-9][a-z0-9.-]*$")
EVIDENCE_STATES = frozenset({"unknown", "partial", "verified", "disagrees"})
REQUIRED_SECTIONS = ("Outcome and Scope", "Architecture Zoom", "Interfaces", "Usage Scenarios", "Requirements", "Edge Cases")


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _section_at_any_level(body: str, heading: str) -> str:
    match = re.search(rf"^#{{2,3}} {re.escape(heading)}\s*$\n(.*?)(?=^#{{2,3}} |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _finding(rule: str, source: SourceDocument | str, message: str, remediation: str, subject: str | None = None) -> Finding:
    if isinstance(source, SourceDocument):
        return Finding(rule, "error", source.path, message, remediation, subject_id=subject or source.identifier)
    return Finding(rule, "error", source, message, remediation, subject_id=subject)


def validate_features(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    sources = {source.identifier: source for source in package.documents("feature")}

    for feature_id, source in sources.items():
        feature = package.features[feature_id]
        if not FEATURE_ID.fullmatch(feature_id):
            findings.append(_finding("CONCORDE-FEATURE-001", source, f"Feature ID '{feature_id}' is not a qualified feature.* identity.", "Use one stable feature ID owned by the providing module."))
        if feature.evidence_status not in EVIDENCE_STATES:
            findings.append(_finding("CONCORDE-EVIDENCE-001", source, f"Evidence status '{feature.evidence_status}' is not supported.", "Use unknown, partial, verified, or disagrees."))
        for heading in REQUIRED_SECTIONS:
            present = _section(source.body, heading)
            if heading == "Usage Scenarios":
                present = present or _section(source.body, "User Scenarios & Testing")
            elif heading == "Edge Cases":
                present = present or _section_at_any_level(source.body, heading)
            if not present:
                findings.append(_finding("CONCORDE-FEATURE-002", source, f"Feature section '## {heading}' is missing or empty.", f"Add the complete {heading} section to the single durable feature file."))
        related = source.metadata.get("related_features")
        if not isinstance(related, list) or not all(isinstance(item, str) for item in related):
            findings.append(_finding("CONCORDE-FEATURE-003", source, "related_features must be an explicit list of stable feature IDs.", "Use [] or list each related feature once and explain its relationship in the design."))
        elif len(related) != len(set(related)):
            findings.append(_finding("CONCORDE-FEATURE-003", source, "related_features contains a duplicate ID.", "Keep each related feature once."))
        else:
            for related_id in related:
                if related_id not in package.features:
                    findings.append(_finding("CONCORDE-FEATURE-004", source, f"Related feature '{related_id}' does not resolve.", "Correct the stable ID or add the level-local feature design."))
        if feature.module not in package.modules:
            findings.append(_finding("CONCORDE-FEATURE-005", source, f"Providing module '{feature.module}' does not resolve.", "Set module to the stable ID of the physical providing module."))

        interface_sets = source.metadata.get("interfaces")
        if not isinstance(interface_sets, dict) or not isinstance(interface_sets.get("provided"), list) or not isinstance(interface_sets.get("required"), list):
            findings.append(_finding("CONCORDE-INTERFACE-001", source, "interfaces.provided and interfaces.required must both be explicit lists.", "Declare both sets, using [] for an empty set."))
            provided: tuple[str, ...] = ()
            required: tuple[str, ...] = ()
        else:
            provided = tuple(interface_sets["provided"])
            required = tuple(interface_sets["required"])
        if not provided:
            findings.append(_finding("CONCORDE-INTERFACE-002", source, "The feature exposes no provided interface.", "Name at least one interface embedded in ## Interfaces."))
        for interface_id in (*provided, *required):
            if not isinstance(interface_id, str) or not INTERFACE_ID.fullmatch(interface_id):
                findings.append(_finding("CONCORDE-INTERFACE-003", source, f"Interface identity '{interface_id}' is not a qualified interface.* or preserved contract.* ID.", "Use a stable qualified interface identity."))
        embedded = {identifier for identifier, interface in package.interfaces.items() if interface.owner == feature_id}
        missing = sorted(set(provided) - embedded)
        extra = sorted(embedded - set(provided))
        if missing:
            findings.append(_finding("CONCORDE-INTERFACE-004", source, "Provided interfaces lack an embedded H3 definition: " + ", ".join(missing) + ".", "Define each provided interface completely inside this feature design."))
        if extra:
            findings.append(_finding("CONCORDE-INTERFACE-005", source, "Embedded interfaces are not registered in interfaces.provided: " + ", ".join(extra) + ".", "Register each interface owned by this feature exactly once."))
        required_blocks = {
            interface.identifier: interface
            for interface in package.required_interface_declarations
            if interface.owner == feature_id
        }
        for required_id in required:
            if required_id in package.interfaces:
                continue
            declaration = required_blocks.get(required_id)
            if declaration is None or not declaration.provider or not declaration.provider.startswith("external:"):
                findings.append(_finding("CONCORDE-INTERFACE-011", source, f"Required interface '{required_id}' has no project provider or explicit external provider declaration.", "Add an H3 block for this required ID with `**Provider**: external:<stable-name>` and its consumer-side semantics, or correct it to an internally provided interface."))

        visible = visible_entity_ids(package, feature.module)
        rows = architecture_zoom_rows(source)
        if _section(source.body, "Architecture Zoom") and not rows:
            findings.append(_finding("CONCORDE-ZOOM-001", source, "Architecture Zoom has no parseable Entity/Role table.", "Use Entity (or Entity ID) and Role columns; Type is optional and must agree with architecture."))
        for row in rows:
            entity_id = row.get("entity_id") or row.get("entity") or ""
            role = row.get("role", "") or next((value for key, value in row.items() if key.startswith("role_")), "")
            if entity_id not in visible:
                findings.append(_finding("CONCORDE-ZOOM-002", source, f"Architecture Zoom entity '{entity_id}' is not visible in '{feature.module}' or its ancestry.", "Reference an entity defined by the providing module or permitted ancestor."))
            if not role:
                findings.append(_finding("CONCORDE-ZOOM-003", source, f"Architecture Zoom entity '{entity_id}' has no feature-specific role.", "Explain how the existing entity participates without redefining it."))
            declared_type = row.get("type")
            entity = package.entities.get(entity_id)
            if declared_type and entity and declared_type != entity.entity_type:
                findings.append(_finding("CONCORDE-ZOOM-004", source, f"Architecture Zoom redefines '{entity_id}' as '{declared_type}' instead of architecture type '{entity.entity_type}'.", "Remove the Type column or copy the owning architecture type exactly."))

    for identifier, declarations in package.interfaces_by_id.items():
        if len(declarations) > 1:
            for interface in declarations:
                findings.append(_finding("CONCORDE-INTERFACE-006", interface.source, f"Interface '{identifier}' is defined by {len(declarations)} features.", "Keep one owning feature definition and list it as required elsewhere.", identifier))
    all_declarations = [interface for declarations in package.interfaces_by_id.values() for interface in declarations]
    all_declarations.extend(package.required_interface_declarations)
    for interface in all_declarations:
        identifier = interface.identifier
        missing_fields = [
            name
            for name, value in (
                ("Consumer", interface.consumer),
                ("Direction", interface.direction),
                ("Entry points", interface.entry_points),
                ("Inputs", interface.inputs),
                ("Outputs", interface.outputs),
                ("Obligations", interface.obligations),
                ("Failures", interface.failures),
                ("Compatibility", interface.compatibility),
                ("Implementing entities", interface.implementing_entities if interface.role == "provided" else True),
            )
            if not value
        ]
        if missing_fields:
            findings.append(_finding("CONCORDE-INTERFACE-007", interface.source, f"Interface '{identifier}' is incomplete: {', '.join(missing_fields)}.", "Complete every human-readable interface field in its owning H3 block.", identifier))
        owner_feature = package.features.get(interface.owner)
        visible = visible_entity_ids(package, owner_feature.module) if owner_feature else set()
        for entity_id in interface.implementing_entities:
            if entity_id not in visible:
                findings.append(_finding("CONCORDE-INTERFACE-009", interface.source, f"Implementing entity '{entity_id}' for interface '{identifier}' is not visible to its feature.", "Reference an entity from the providing module architecture or permitted ancestry.", identifier))
        for entry_point in interface.entry_points:
            if entry_point.startswith(("entity.", "module.")) and entry_point not in visible:
                findings.append(_finding("CONCORDE-INTERFACE-010", interface.source, f"Entry point '{entry_point}' for interface '{identifier}' does not resolve.", "Reference a visible architecture entity or describe an explicit human workflow entry point.", identifier))

    return findings
