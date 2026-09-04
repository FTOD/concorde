"""Typed architecture-entity, relationship, and interaction rules for Profile 7."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from ...model import ArchitectureEntity, Finding, SourceDocument
from ..repository import RepositoryError, safe_relative_path


PREFERRED_ENTITY_TYPES = frozenset(
    {
        "module",
        "package",
        "directory",
        "file",
        "script",
        "program",
        "function",
        "method",
        "class",
        "interface",
        "type",
        "configuration",
        "schema",
        "endpoint",
        "command",
        "service",
        "pipeline",
        "resource",
        "data-store",
        "event",
        "test",
        "document",
        "external-system",
        "concept",
    }
)

PREFERRED_RELATIONSHIPS = frozenset(
    {
        "contains_module",
        "owns_entity",
        "registers_feature",
        "contains",
        "declares",
        "defines",
        "composed_of",
        "has_entry_point",
        "imports",
        "exports",
        "calls",
        "inherits",
        "implements",
        "depends_on",
        "provides",
        "requires",
        "serves",
        "routes_to",
        "publishes",
        "subscribes_to",
        "reads_from",
        "writes_to",
        "transforms",
        "validates",
        "triggers",
        "configures",
        "documents",
        "tested_by",
        "generates",
        "realizes",
    }
)

ENTITY_ID = re.compile(r"^entity\.[a-z0-9][a-z0-9.-]*$")
MODULE_ID = re.compile(r"^module\.[a-z0-9][a-z0-9.-]*$")
INTERACTION_ID = re.compile(r"^interaction\.[a-z0-9][a-z0-9.-]*$")
_H2 = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)*\s*\|?\s*$")


def _finding(rule: str, source: str | SourceDocument, message: str, remediation: str, subject: str | None = None) -> Finding:
    if isinstance(source, SourceDocument):
        return Finding(rule, "error", source.path, message, remediation, subject_id=subject or source.identifier)
    return Finding(rule, "error", source, message, remediation, subject_id=subject)


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _declared_types(body: str, heading: str) -> set[str]:
    section = _section(body, heading)
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if not line.startswith("|") or not _TABLE_SEPARATOR.fullmatch(lines[index + 1]):
            continue
        result: set[str] = set()
        for row in lines[index + 2 :]:
            if not row.startswith("|"):
                break
            cells = [cell.strip().strip("`") for cell in row.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[1]:
                result.add(cells[0])
        return result
    return set()


def module_ancestry(package: Any, module_id: str) -> tuple[str, ...]:
    """Return root-to-parent module IDs, stopping safely when hierarchy is malformed."""
    result: list[str] = []
    seen: set[str] = set()
    current = package.modules.get(module_id)
    while current is not None and current.parent and current.parent not in seen:
        seen.add(current.parent)
        result.append(current.parent)
        current = package.modules.get(current.parent)
    return tuple(reversed(result))


def visible_entity_ids(package: Any, module_id: str) -> set[str]:
    owners = {*module_ancestry(package, module_id), module_id}
    visible = {
        identifier
        for identifier, declarations in package.entities_by_id.items()
        if any(entity.owner in owners for entity in declarations)
    }
    visible.update(owners)
    return visible


def _validate_locator(package: Any, entity: ArchitectureEntity) -> str | None:
    locator = entity.locator.strip()
    if not locator:
        return "locator is empty"
    if locator.startswith("external:"):
        return None if locator.split(":", 1)[1].strip() else "external locator is empty"
    if locator.startswith("concept:"):
        return None if locator.split(":", 1)[1].strip() else "concept locator is empty"
    relative = locator.split("#", 1)[0]
    try:
        safe = safe_relative_path(relative)
    except RepositoryError as error:
        return str(error)
    path = package.project_root / safe
    if not path.exists() or path.is_symlink():
        return f"project locator '{relative}' does not resolve to a real path"
    return None


def validate_entities(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    module_sources = {source.identifier: source for source in package.documents("module")}

    for module_id, source in module_sources.items():
        entities_section = _section(source.body, "Entities")
        relationships_section = _section(source.body, "Relationships")
        interactions_section = _section(source.body, "Interactions")
        if not entities_section:
            findings.append(_finding("CONCORDE-ENTITY-001", source, "The module has no non-empty ## Entities section.", "Add the Entity ID, Type, Definition, Locator table."))
        if entities_section and not package.modules.get(module_id, None).entities:
            findings.append(_finding("CONCORDE-ENTITY-002", source, "The Entities section does not contain a parseable Entity ID, Type, Definition, Locator table.", "Use the canonical four-column entity table; an optional Roles column may follow."))
        if not relationships_section:
            findings.append(_finding("CONCORDE-RELATIONSHIP-001", source, "The module has no non-empty ## Relationships section.", "Add the Source, Predicate, Target, Description table."))
        if relationships_section and not package.modules.get(module_id, None).relationships:
            findings.append(_finding("CONCORDE-RELATIONSHIP-002", source, "The Relationships section has no parseable directed relationship rows.", "Use Source, Predicate, Target, Description and optional Interface columns."))
        if not interactions_section:
            findings.append(_finding("CONCORDE-INTERACTION-001", source, "The module has no non-empty ## Interactions section.", "Describe at least one representative interaction using the canonical table or typed H3 block."))
        if interactions_section and not package.modules.get(module_id, None).interactions:
            findings.append(_finding("CONCORDE-INTERACTION-002", source, "The Interactions section has no normalized interaction.* declaration.", "Use Interaction ID, Trigger, Steps, Result, Interfaces columns or an interaction.* H3 block with those fields."))

    for identifier, declarations in package.entities_by_id.items():
        if len(declarations) > 1:
            for entity in declarations:
                findings.append(_finding("CONCORDE-ENTITY-003", entity.source, f"Architecture entity '{identifier}' is defined {len(declarations)} times.", "Keep one owning module definition for every stable entity ID.", identifier))
        for entity in declarations:
            owner_source = module_sources.get(entity.owner)
            if not (ENTITY_ID.fullmatch(identifier) or MODULE_ID.fullmatch(identifier)):
                findings.append(_finding("CONCORDE-ENTITY-004", entity.source, f"Entity ID '{identifier}' is not a qualified entity.* or child module.* identity.", "Use a stable qualified ID independent of its locator.", identifier))
            custom_types = _declared_types(owner_source.body, "Entity Types") if owner_source else set()
            if entity.entity_type not in PREFERRED_ENTITY_TYPES and entity.entity_type not in custom_types:
                findings.append(_finding("CONCORDE-ENTITY-005", entity.source, f"Entity '{identifier}' uses undeclared type '{entity.entity_type}'.", "Use a preferred Profile 7 type or define the custom type and meaning in ## Entity Types.", identifier))
            if not entity.definition.strip():
                findings.append(_finding("CONCORDE-ENTITY-006", entity.source, f"Entity '{identifier}' has no definition.", "State its non-circular role at this module level.", identifier))
            locator_problem = _validate_locator(package, entity)
            if locator_problem:
                findings.append(_finding("CONCORDE-ENTITY-007", entity.source, f"Entity '{identifier}' {locator_problem}.", "Use an existing project-relative path with optional #symbol, external:<locator>, or concept:<qualified-name>.", identifier))

    for module_id, module in package.modules.items():
        declarations = {entity.identifier: entity for entity in package.entities.values() if entity.owner == module_id}
        for child_id in module.modules:
            child = package.modules.get(child_id)
            entity = declarations.get(child_id)
            if child is not None and (entity is None or entity.entity_type != "module" or entity.locator != child.path):
                findings.append(_finding("CONCORDE-ENTITY-008", module.path, f"Immediate child '{child_id}' is not exposed as a module entity with locator '{child.path}'.", "Add one child-module entity row without duplicating the child's internals.", child_id))

    for relationship in package.relationships:
        visible = visible_entity_ids(package, relationship.owner)
        for endpoint, label in ((relationship.source_entity, "source"), (relationship.target_entity, "target")):
            if endpoint not in visible:
                findings.append(_finding("CONCORDE-RELATIONSHIP-003", relationship.source, f"Relationship {label} '{endpoint}' is not visible in module '{relationship.owner}' or its ancestry.", "Reference a locally defined entity, child module entity, or permitted ancestor entity.", relationship.owner))
        owner = module_sources.get(relationship.owner)
        custom = _declared_types(owner.body, "Relationship Types") if owner else set()
        if relationship.predicate not in PREFERRED_RELATIONSHIPS and relationship.predicate not in custom:
            findings.append(_finding("CONCORDE-RELATIONSHIP-004", relationship.source, f"Relationship predicate '{relationship.predicate}' is not preferred or locally defined.", "Use a preferred directed predicate or define its direction and meaning in ## Relationship Types.", relationship.owner))
        if not relationship.description.strip():
            findings.append(_finding("CONCORDE-RELATIONSHIP-005", relationship.source, "A relationship has no description of what the edge carries or constrains.", "Add a concise non-empty relationship description.", relationship.owner))
        if relationship.interface and relationship.interface not in package.interfaces:
            declared_required = {
                interface
                for feature in package.features.values()
                if feature.module == relationship.owner
                for interface in feature.required_interfaces
            }
            if relationship.interface not in declared_required:
                findings.append(_finding("CONCORDE-RELATIONSHIP-006", relationship.source, f"Governing interface '{relationship.interface}' is not embedded or declared as a required external interface.", "Define the interface in its owning feature design or declare it required at this module level.", relationship.owner))

    for identifier, declarations in package.interactions_by_id.items():
        if len(declarations) > 1:
            for interaction in declarations:
                findings.append(_finding("CONCORDE-INTERACTION-003", interaction.source, f"Interaction '{identifier}' is declared {len(declarations)} times.", "Keep one stable interaction declaration in its owning module.", identifier))
        for interaction in declarations:
            if not INTERACTION_ID.fullmatch(identifier):
                findings.append(_finding("CONCORDE-INTERACTION-004", interaction.source, f"Interaction ID '{identifier}' is not a qualified interaction.* identity.", "Use a stable module-qualified interaction ID.", identifier))
            if not interaction.trigger or not interaction.steps or not interaction.result:
                findings.append(_finding("CONCORDE-INTERACTION-005", interaction.source, f"Interaction '{identifier}' lacks a trigger, ordered steps, or result.", "Complete all three fields and reference visible entities in the steps.", identifier))
            visible = visible_entity_ids(package, interaction.owner)
            mentioned = {
                candidate
                for step in interaction.steps
                for candidate in re.findall(r"(?:entity|module)\.[a-z0-9][a-z0-9.-]*", step)
            }
            unknown = sorted(mentioned - visible)
            if unknown:
                findings.append(_finding("CONCORDE-INTERACTION-006", interaction.source, f"Interaction '{identifier}' names entities not visible at this module: {', '.join(unknown)}.", "Use visible entity IDs or describe the cross-boundary participant in the owning architecture.", identifier))

    return findings
