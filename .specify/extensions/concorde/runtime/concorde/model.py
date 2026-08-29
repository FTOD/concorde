"""Immutable entities shared by Concorde operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


MODULE_DIAGRAMS_DIRECTORY = "architecture/diagrams"
MODULE_CONTRACTS_DIRECTORY = "architecture/contracts"
MODULE_CHILDREN_DIRECTORY = "architecture/modules"


@dataclass(frozen=True)
class SourceDocument:
    path: str
    kind: str
    identifier: str
    metadata: Mapping[str, Any]
    body: str


@dataclass(frozen=True)
class Module:
    identifier: str
    parent: str | None
    responsibility: str
    boundary: str
    children: tuple[str, ...]
    features: tuple[str, ...]
    provided_contracts: tuple[str, ...]
    required_contracts: tuple[str, ...]
    view: str | None = None


@dataclass(frozen=True)
class Feature:
    identifier: str
    module: str
    outcome: str
    refines: tuple[str, ...]
    scenarios: tuple[str, ...]
    provided_contracts: tuple[str, ...]
    required_contracts: tuple[str, ...]
    evidence_status: str
    canonical_design: str


@dataclass(frozen=True)
class Contract:
    identifier: str
    module: str
    role: str
    flow: str
    counterparties: tuple[str, ...]
    representation: Mapping[str, Any]
    evidence_status: str


@dataclass(frozen=True)
class Scenario:
    identifier: str
    module: str
    participants: tuple[str, ...]
    interactions: tuple[Mapping[str, Any], ...]
    prose_only: bool = False


@dataclass(frozen=True)
class ArchitectureView:
    path: str
    current_module: str
    components: tuple[Mapping[str, Any], ...]
    connections: tuple[Mapping[str, Any], ...]
    scenarios: tuple[str, ...]


@dataclass(frozen=True)
class BoundedContext:
    requested_id: str
    current_module: Mapping[str, Any]
    children: tuple[Mapping[str, Any], ...]
    externals: tuple[str, ...]
    scenarios: tuple[str, ...]
    refinement_links: tuple[Mapping[str, str], ...]
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

    def documents(self, kind: str) -> tuple[SourceDocument, ...]:
        return tuple(source for source in self.sources if source.kind == kind)

    def module_diagrams(self, module: SourceDocument) -> dict[str, Mapping[str, Any]]:
        """Every module-owned Archify diagram under `<module>/architecture/diagrams/`, keyed by path."""
        directory = PurePosixPath(module.path).parent / MODULE_DIAGRAMS_DIRECTORY
        return {path: value for path, value in sorted(self.views.items()) if PurePosixPath(path).parent == directory}

    def module_views(self, module: SourceDocument) -> dict[str, Mapping[str, Any]]:
        """The module's level views: its `architecture`-kind diagrams, keyed by path."""
        return {path: value for path, value in self.module_diagrams(module).items() if value.get("diagram_type") == "architecture"}


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
    provided_contracts: tuple[str, ...] = ()
    required_contracts: tuple[str, ...] = ()
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
