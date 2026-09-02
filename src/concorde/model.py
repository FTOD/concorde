"""Immutable entities shared by Concorde Source Profile 7 operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


MODULE_DIAGRAMS_DIRECTORY = "diagrams"
MODULE_CHILDREN_DIRECTORY = "modules"


@dataclass(frozen=True)
class SourceDocument:
    path: str
    kind: str
    identifier: str
    metadata: Mapping[str, Any]
    body: str


@dataclass(frozen=True)
class ArchitectureEntity:
    identifier: str
    entity_type: str
    definition: str
    locator: str
    owner: str
    roles: tuple[str, ...] = ()
    source: str = ""


@dataclass(frozen=True)
class EntityRelationship:
    source_entity: str
    predicate: str
    target_entity: str
    description: str
    owner: str
    interface: str | None = None
    source: str = ""


@dataclass(frozen=True)
class Interaction:
    identifier: str
    trigger: str
    steps: tuple[str, ...]
    result: str
    owner: str
    interfaces: tuple[str, ...] = ()
    source: str = ""


@dataclass(frozen=True)
class FeatureInterface:
    identifier: str
    owner: str
    consumer: str
    direction: str
    entry_points: tuple[str, ...]
    inputs: str
    outputs: str
    obligations: str
    failures: str
    compatibility: str
    implementing_entities: tuple[str, ...]
    example: str | None = None
    role: str = "provided"
    provider: str | None = None
    source: str = ""


@dataclass(frozen=True)
class Module:
    identifier: str
    parent: str | None
    path: str
    responsibility: str
    boundary: str
    modules: tuple[str, ...]
    features: tuple[str, ...]
    entities: tuple[str, ...]
    relationships: tuple[EntityRelationship, ...]
    interactions: tuple[str, ...]
    diagrams: tuple[str, ...] = ()


@dataclass(frozen=True)
class Feature:
    identifier: str
    module: str
    path: str
    outcome: str
    related_features: tuple[str, ...]
    provided_interfaces: tuple[str, ...]
    required_interfaces: tuple[str, ...]
    architecture_zoom: tuple[str, ...]
    evidence_status: str


@dataclass(frozen=True)
class BoundedContext:
    requested_id: str
    current_module: Mapping[str, Any]
    children: tuple[Mapping[str, Any], ...]
    related_features: tuple[Mapping[str, Any], ...]
    deeper_references: tuple[str, ...]


@dataclass(frozen=True)
class ArchitecturePackage:
    project_root: Path
    specification_root: str
    root_module_id: str
    profile_version: int
    sources: tuple[SourceDocument, ...]
    views: Mapping[str, Mapping[str, Any]]
    diagrams: Mapping[str, Mapping[str, Any]]
    by_id: Mapping[str, tuple[SourceDocument, ...]]
    source_digest: str
    auxiliary: Mapping[str, str]
    receipts: Mapping[str, Mapping[str, Any]]
    modules: Mapping[str, Module] = field(default_factory=dict)
    features: Mapping[str, Feature] = field(default_factory=dict)
    entities: Mapping[str, ArchitectureEntity] = field(default_factory=dict)
    entities_by_id: Mapping[str, tuple[ArchitectureEntity, ...]] = field(default_factory=dict)
    relationships: tuple[EntityRelationship, ...] = ()
    interactions: Mapping[str, Interaction] = field(default_factory=dict)
    interactions_by_id: Mapping[str, tuple[Interaction, ...]] = field(default_factory=dict)
    interfaces: Mapping[str, FeatureInterface] = field(default_factory=dict)
    interfaces_by_id: Mapping[str, tuple[FeatureInterface, ...]] = field(default_factory=dict)
    required_interface_declarations: tuple[FeatureInterface, ...] = ()

    def documents(self, kind: str) -> tuple[SourceDocument, ...]:
        return tuple(source for source in self.sources if source.kind == kind)

    def module_diagrams(self, module: SourceDocument) -> dict[str, Mapping[str, Any]]:
        """Architecture-owned diagrams directly below ``<module>/diagrams/``."""
        directory = PurePosixPath(module.path).parent / MODULE_DIAGRAMS_DIRECTORY
        return {
            path: value
            for path, value in sorted(self.diagrams.items())
            if PurePosixPath(path).parent == directory
        }

    def module_views(self, module: SourceDocument) -> dict[str, Mapping[str, Any]]:
        return {
            path: value
            for path, value in self.module_diagrams(module).items()
            if value.get("diagram_type") == "architecture"
        }


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    source: str
    message: str
    remediation: str
    line: int | None = None
    column: int | None = None
    subject_id: str | None = None


@dataclass(frozen=True)
class ProposalFile:
    path: str
    content: str
    sha256: str


@dataclass(frozen=True)
class InitializationProposal:
    proposal_version: int
    project_root_id: str
    responsibility: str
    boundary: str
    children: tuple[Mapping[str, Any], ...] = ()
    files: tuple[ProposalFile, ...] = ()
    conflicts: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class OperationResult:
    operation: str
    target: str
    status: str
    artifacts: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    result: Mapping[str, Any] = field(default_factory=dict)
