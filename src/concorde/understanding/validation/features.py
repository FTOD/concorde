"""Direct feature, embedded-interface, and architecture-zoom rules for Profile 7."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from ...model import DIRECTIONAL_RELATIONS, FEATURE_RELATIONS, INVERSE_RELATIONS, Finding, SourceDocument
from ..repository import FEATURE_ID, architecture_zoom_rows
from .entities import visible_entity_ids


INTERFACE_ID = re.compile(r"^(?:interface|contract)\.[a-z0-9][a-z0-9.-]*$")
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


def _is_well_formed_relation_entry(item: Any) -> bool:
    """A related_features entry is a plain ID or an {id, relation} mapping of exactly those keys."""
    if isinstance(item, str):
        return True
    return (
        isinstance(item, dict)
        and set(item) == {"id", "relation"}
        and isinstance(item.get("id"), str)
        and isinstance(item.get("relation"), str)
    )


def _directional_edges(package: Any) -> dict[str, set[tuple[str, str]]]:
    """Directed feature-to-feature edges per family, normalized to their forward relation."""
    edges: dict[str, set[tuple[str, str]]] = {name: set() for name in DIRECTIONAL_RELATIONS}
    for feature in package.features.values():
        for relation in feature.relations:
            if relation.relation in DIRECTIONAL_RELATIONS:
                family, source_id, target_id = relation.relation, feature.identifier, relation.target
            elif relation.relation in INVERSE_RELATIONS:
                family, source_id, target_id = INVERSE_RELATIONS[relation.relation], relation.target, feature.identifier
            else:
                continue
            if source_id == target_id or target_id not in package.features:
                continue
            edges[family].add((source_id, target_id))

    requires: set[tuple[str, str]] = set()
    for feature in package.features.values():
        for interface_id in feature.required_interfaces:
            provider = package.interfaces.get(interface_id)
            if provider is None:
                continue
            owner = provider.owner
            if owner and owner != feature.identifier and owner in package.features:
                requires.add((feature.identifier, owner))
    edges["requires"] = requires
    return edges


def _cycle_groups(edges: set[tuple[str, str]]) -> list[frozenset[str]]:
    """Every maximal set of mutually reachable nodes (size > 1) in a directed edge set."""
    graph: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for source_id, target_id in edges:
        graph[source_id].add(target_id)
        nodes.add(source_id)
        nodes.add(target_id)

    def reachable(start: str) -> set[str]:
        seen: set[str] = set()
        stack = list(graph.get(start, ()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(graph.get(current, ()))
        return seen

    reach = {node: reachable(node) for node in nodes}
    seen_groups: set[frozenset[str]] = set()
    groups: list[frozenset[str]] = []
    for node in sorted(nodes):
        if node in reach[node]:
            component = frozenset(other for other in nodes if other in reach[node] and node in reach[other])
            if component not in seen_groups:
                seen_groups.add(component)
                groups.append(component)
    return groups


def validate_features(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    sources = {source.identifier: source for source in package.documents("feature")}

    for feature_id, source in sources.items():
        feature = package.features[feature_id]
        if not FEATURE_ID.fullmatch(feature_id):
            findings.append(_finding("CONCORDE-FEATURE-001", source, f"Feature ID '{feature_id}' is not a qualified feature.* identity.", "Use one stable feature ID owned by the providing module."))
        for heading in REQUIRED_SECTIONS:
            present = _section(source.body, heading)
            if heading == "Usage Scenarios":
                present = present or _section(source.body, "User Scenarios & Testing")
            elif heading == "Edge Cases":
                present = present or _section_at_any_level(source.body, heading)
            if not present:
                findings.append(_finding("CONCORDE-FEATURE-002", source, f"Feature section '## {heading}' is missing or empty.", f"Add the complete {heading} section to the single durable feature file."))
        related = source.metadata.get("related_features")
        if not isinstance(related, list) or not all(_is_well_formed_relation_entry(item) for item in related):
            findings.append(_finding(
                "CONCORDE-FEATURE-003",
                source,
                "related_features must be an explicit list of stable feature IDs or {id, relation} mappings with exactly those two string keys.",
                "Use [] or list each related feature once as a plain ID or {id, relation}.",
            ))
        else:
            targets = [relation.target for relation in feature.relations]
            if len(targets) != len(set(targets)):
                findings.append(_finding("CONCORDE-FEATURE-003", source, "related_features contains a duplicate target ID.", "Keep each related feature once."))
            else:
                for relation in feature.relations:
                    if relation.target not in package.features:
                        findings.append(_finding("CONCORDE-FEATURE-004", source, f"Related feature '{relation.target}' does not resolve.", "Correct the stable ID or add the level-local feature design."))
                    if relation.relation not in FEATURE_RELATIONS:
                        findings.append(_finding(
                            "CONCORDE-FEATURE-006",
                            source,
                            f"Related feature relation '{relation.relation}' for '{relation.target}' is not in the supported vocabulary.",
                            "Use composes, refines, depends_on, composed_by, refined_by, depended_on_by, or relates_to.",
                        ))
                    if relation.target == feature_id:
                        findings.append(_finding(
                            "CONCORDE-FEATURE-006",
                            source,
                            f"Feature '{feature_id}' declares a related-feature relation to itself.",
                            "Remove the self-reference or point the relation to a different feature.",
                        ))
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

    for family, family_edges in _directional_edges(package).items():
        for group in _cycle_groups(family_edges):
            members = sorted(group)
            for member in members:
                member_source = sources.get(member)
                if member_source is None:
                    continue
                findings.append(_finding(
                    "CONCORDE-FEATURE-007",
                    member_source,
                    f"Feature '{member}' is on a {family} cycle: {', '.join(members)}.",
                    f"Break the {family} cycle by removing or redirecting one relation among {', '.join(members)}.",
                    subject=member,
                ))

    return findings
