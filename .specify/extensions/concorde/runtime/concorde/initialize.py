"""Review-first initialization of a root Concorde specification hierarchy."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any

from .model import MODULE_DIAGRAMS_DIRECTORY, Finding, InitializationProposal, OperationResult, ProposalFile
from .projection import markdown_section
from .repository import PROFILE_VERSION, ProjectRepository, RepositoryError, safe_relative_path


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "project"


def _proposal_file(path: str, content: str) -> ProposalFile:
    normalized = content.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return ProposalFile(path, normalized, f"sha256:{digest}")


def _proposal_payload(proposal: InitializationProposal) -> dict[str, Any]:
    return asdict(proposal)


def _interaction_model() -> dict[str, Any]:
    """Describe the workflow mechanics without pretending they are product modules."""
    return {
        "user_interface": "skills",
        "deterministic_operations": "scripts",
        "workspace_state": "files",
        "file_lifetimes": {
            "durable": "module and feature sources outside attempt/",
            "temporal": "current delivery memory below the selected feature's attempt/",
            "generated": "disposable projections that never become source authority",
        },
    }


def _configured_architecture(project_root: Path) -> OperationResult | None:
    """Report an existing initialized hierarchy instead of proposing a starter overwrite."""
    config_path = project_root / ".concorde/config.json"
    if not config_path.exists():
        return None
    repository = ProjectRepository(project_root)
    try:
        package = repository.load()
        roots = package.by_id.get(package.root_module_id, ())
        if len(roots) != 1 or roots[0].kind != "module":
            raise RepositoryError("configured root_module_id does not resolve to exactly one module")
        module = roots[0]
        module_directory = PurePosixPath(module.path).parent
        design_path = f"{module_directory}/design.md"
        level_view = f"{module_directory}/{MODULE_DIAGRAMS_DIRECTORY}/level-view.json"
        for required in (design_path, level_view):
            target = repository.resolve(required)
            if target.is_symlink() or not target.is_file():
                raise RepositoryError(f"configured root package is incomplete: {required} is missing")
    except RepositoryError as error:
        finding = Finding(
            "CONCORDE-INIT-006",
            "error",
            ".concorde/config.json",
            f"A configured architecture already exists but cannot be treated as initialized: {error}",
            "Reconcile the existing configuration and root package; initialization never replaces or migrates it.",
        )
        return OperationResult(
            "init",
            ".",
            "conflict",
            findings=(finding,),
            result={"interaction_model": _interaction_model()},
        )

    contracts = module.metadata.get("contracts", {})
    if not isinstance(contracts, dict):
        contracts = {}
    artifacts = (".concorde/config.json", module.path, design_path, level_view)
    return OperationResult(
        "init",
        ".",
        "unchanged",
        artifacts=tuple(sorted(artifacts)),
        result={
            "architecture": {
                "root_module_id": package.root_module_id,
                "specification_root": package.specification_root,
                "module_summary": module.path,
                "module_design": design_path,
                "level_view": level_view,
                "responsibility": markdown_section(module.body, "Responsibility"),
                "boundary": markdown_section(module.body, "Boundary"),
                "children": tuple(module.metadata.get("children", [])),
                "features": tuple(module.metadata.get("features", [])),
                "provided_contracts": tuple(contracts.get("provided", [])),
                "required_contracts": tuple(contracts.get("required", [])),
            },
            "interaction_model": _interaction_model(),
        },
    )


def _create_proposal(project_root: Path, module_id: str | None, name: str | None) -> InitializationProposal:
    project_name = name or project_root.resolve().name
    derived_slug = _slug(module_id.split(".", 1)[1] if module_id and module_id.startswith("module.") else project_name)
    identifier = module_id or f"module.{derived_slug}"
    if not re.fullmatch(r"module\.[a-z0-9]+(?:[.-][a-z0-9-]+)*", identifier):
        raise ValueError("module ID must be a lowercase dotted module.<namespace> identifier")
    module_slug = identifier.split(".", 1)[1].replace(".", "-")
    specification_root = f"specs/{module_slug}"
    config = json.dumps(
        {"profile_version": PROFILE_VERSION, "root_module_id": identifier, "specification_root": specification_root},
        indent=2,
        sort_keys=True,
    )
    level_view = f"{specification_root}/{MODULE_DIAGRAMS_DIRECTORY}/level-view.json"
    module = f"""---
id: {identifier}
kind: module
parent: null
children: []
features: []
contracts:
  provided: []
  required: []
---

# {project_name}

## Responsibility

Describe and govern the project-level outcome provided by {project_name}.

## Boundary

Own the project-level outcome and delegate distinct product responsibilities only to explicitly
reviewed child modules. Concorde's Skills, Scripts, and Workspace Files are development-workflow
mechanisms, not product modules unless {project_name} exposes those things as product behavior.

## Structure

The level view is [level-view.json]({MODULE_DIAGRAMS_DIRECTORY}/level-view.json); it shows the root
boundary before any product decomposition has been accepted. Durable architecture lives in this
`module.md`, the adjacent [design reference](design.md), and `architecture/`; feature intent and
accepted realization will live under `features/`, while current delivery memory will live only below
the selected feature's `attempt/`. Add an immediate product module to the view and the inventory
together. Further diagrams of this level live beside the level view under
`{MODULE_DIAGRAMS_DIRECTORY}/`.

## Features

None.

## Contracts

None.

## Submodules

None.

## Representative Scenario

`scenario-{module_slug}-root-overview`: a maintainer reviews the durable root boundary and the empty
product-module inventory before adding a feature or child module through the installed skills.

## Design Rationale

The root starts without guessed product modules. Maintainers interact through Skills, those skills
invoke Scripts for deterministic operations, and both operate on explicit Workspace Files. Product
architecture remains separate from those workflow mechanics; implementation notes and decisions are
kept in the [design reference](design.md).
"""
    design = f"""# Design Reference: {project_name}

## Implementation Notes

No product implementation detail has been recorded for this module yet.

Concorde manages this architecture through three explicit mechanisms:

- **Skills** are the maintainer-facing workflow interface.
- **Scripts** provide workspace routing and deterministic proposal, context, validation, and
  acceptance behavior when a skill requires it.
- **Workspace Files** preserve durable architecture and feature intent outside `attempt/`, temporal
  delivery memory inside the selected feature's `attempt/`, and generated projections outside the
  maintained source hierarchy.

These mechanisms support development; they do not determine {project_name}'s product-module names.

## Design Rationale

The root is initialized without inferred product decomposition so maintainers can name modules after
observable product responsibilities rather than after framework or tooling internals.

## Alternatives Considered

- Inferring child modules from repository directories was rejected because source layout is not
  reliable evidence of product responsibility.
- Creating Skills, Scripts, or Workspace Files as product modules by default was rejected because
  those are Concorde workflow roles unless the project itself exposes them as product behavior.

## Decision Log

- Initialized the durable root module package and kept workflow mechanics separate from product architecture.
"""
    architecture = json.dumps(
        {
            "schema_version": 1,
            "diagram_type": "architecture",
            "meta": {
                "title": f"{project_name} — Root Module",
                "output": f"../../../../generated/architecture/{module_slug}-level-view.html",
                "quality_profile": "showcase",
                "legend": {"mode": "hidden"},
                "viewBox": [720, 520],
                "views": [
                    {
                        "id": f"scenario-{module_slug}-root-overview",
                        "label": "Root overview",
                        "focus": ["maintainer"],
                        "note": "Review the durable root boundary before adding product features or immediate modules.",
                    }
                ],
            },
            "components": [
                {
                    "id": "maintainer",
                    "type": "external",
                    "label": "Maintainer",
                    "sublabel": "Reviews the durable root boundary",
                    "pos": [250, 170],
                    "size": [220, 88],
                }
            ],
            "connections": [],
            "cards": [
                {
                    "dot": "cyan",
                    "title": "Concorde workflow mechanics",
                    "items": [
                        "Skills are the maintainer-facing interface",
                        "Scripts perform deterministic operations",
                        "Workspace Files separate durable intent from temporal attempts",
                    ],
                }
            ],
        },
        indent=2,
        sort_keys=True,
    )
    files = (
        _proposal_file(".concorde/config.json", config),
        _proposal_file(level_view, architecture),
        _proposal_file(f"{specification_root}/design.md", design),
        _proposal_file(f"{specification_root}/module.md", module),
    )
    conflicts = tuple(
        {"path": item.path, "reason": "target already exists"}
        for item in files
        if (project_root / item.path).exists()
    )
    return InitializationProposal(
        proposal_version=1,
        project_root_id=identifier,
        responsibility=f"Describe and govern the project-level outcome provided by {project_name}.",
        boundary="Keep product responsibilities explicit while treating Skills, Scripts, and Workspace Files as workflow mechanics.",
        provided_contracts=(),
        required_contracts=(),
        children=(),
        files=files,
        conflicts=conflicts,
    )


def propose_initialization(project_root: str | Path, module_id: str | None = None, name: str | None = None) -> OperationResult:
    root = Path(project_root).resolve()
    configured = _configured_architecture(root)
    if configured is not None:
        return configured
    try:
        proposal = _create_proposal(root, module_id, name)
    except ValueError as error:
        finding = Finding("CONCORDE-INIT-002", "error", ".concorde/config.json", str(error), "Use a lowercase stable module.<namespace> ID.")
        return OperationResult("init", ".", "invalid", findings=(finding,), result={"interaction_model": _interaction_model()})
    files = proposal.files
    existing = [(root / item.path).is_file() and (root / item.path).read_text(encoding="utf-8") == item.content for item in files]
    if all(existing):
        return OperationResult(
            "init",
            ".",
            "unchanged",
            tuple(item.path for item in files),
            result={"interaction_model": _interaction_model(), "proposal": _proposal_payload(proposal)},
        )
    return OperationResult(
        "init",
        ".",
        "proposal",
        result={"interaction_model": _interaction_model(), "proposal": _proposal_payload(proposal)},
    )


def _load_accepted(root: Path, proposal_path: str) -> InitializationProposal:
    relative = safe_relative_path(proposal_path)
    path = ProjectRepository(root).resolve(relative)
    value = json.loads(path.read_text(encoding="utf-8"))
    value = value.get("result", {}).get("proposal", value.get("proposal", value))
    if value.get("proposal_version") != 1:
        raise ValueError("unsupported or missing proposal_version")
    files: list[ProposalFile] = []
    for item in value.get("files", []):
        relative_target = safe_relative_path(item["path"])
        content = item["content"].replace("\r\n", "\n")
        expected = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        if item.get("sha256") != expected:
            raise ValueError(f"proposal content hash does not match for {relative_target}")
        files.append(ProposalFile(relative_target, content, expected))
    if not files:
        raise ValueError("proposal contains no files")
    required = {".concorde/config.json"}
    paths = {item.path for item in files}
    if (
        not required.issubset(paths)
        or not any(path.endswith("/module.md") for path in paths)
        or not any(path.endswith("/design.md") for path in paths)
        or not any(f"/{MODULE_DIAGRAMS_DIRECTORY}/" in path and path.endswith(".json") for path in paths)
    ):
        raise ValueError("proposal must contain configuration, root module summary, module design reference, and a level view under architecture/diagrams/")
    return InitializationProposal(
        proposal_version=1,
        project_root_id=value["project_root_id"],
        responsibility=value.get("responsibility", ""),
        boundary=value.get("boundary", ""),
        provided_contracts=tuple(value.get("provided_contracts", [])),
        required_contracts=tuple(value.get("required_contracts", [])),
        children=tuple(value.get("children", [])),
        files=tuple(files),
        conflicts=tuple(value.get("conflicts", [])),
    )


def apply_proposal(project_root: str | Path, proposal_path: str) -> OperationResult:
    root = Path(project_root).resolve()
    try:
        proposal = _load_accepted(root, proposal_path)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, RepositoryError) as error:
        finding = Finding("CONCORDE-INIT-003", "error", ".concorde/config.json", f"Accepted proposal is invalid: {error}", "Save the exact proposal JSON at a safe project-relative path and retry.")
        return OperationResult("init", ".", "invalid", findings=(finding,))
    expected = {item.path: item.content for item in proposal.files}
    states: dict[str, str] = {}
    for relative, content in expected.items():
        path = root / relative
        if not path.exists():
            states[relative] = "missing"
        elif path.is_file() and path.read_text(encoding="utf-8") == content:
            states[relative] = "exact"
        else:
            states[relative] = "changed"
    if all(state == "exact" for state in states.values()):
        return OperationResult("init", ".", "unchanged", tuple(sorted(expected)), result={"proposal": _proposal_payload(proposal)})
    if any(state != "missing" for state in states.values()):
        findings = tuple(
            Finding("CONCORDE-INIT-004", "error", path, f"Target is {state}; exact accepted content cannot be promoted.", "Move or reconcile the existing maintained source, then create and accept a new proposal.")
            for path, state in sorted(states.items())
            if state != "missing"
        )
        return OperationResult("init", ".", "conflict", findings=findings, result={"conflicts": [path for path, state in sorted(states.items()) if state != "missing"]})
    try:
        created = ProjectRepository(root).stage_and_promote(expected)
    except (OSError, RepositoryError) as error:
        finding = Finding("CONCORDE-INIT-005", "error", ".concorde/config.json", f"Staged promotion failed: {error}", "Resolve the filesystem failure; confirm no staged files remain; then retry the accepted proposal.")
        return OperationResult("init", ".", "failed", findings=(finding,))
    return OperationResult("init", ".", "success", tuple(created), result={"created": created, "project_root_id": proposal.project_root_id})
