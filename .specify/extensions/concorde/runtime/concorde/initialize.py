"""Review-first initialization of a root Concorde specification hierarchy."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .model import MODULE_DIAGRAMS_DIRECTORY, Finding, InitializationProposal, OperationResult, ProposalFile
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

Provide the observable responsibility of {project_name}.

## Boundary

Own the project-level outcome while excluding responsibilities delegated to future submodules.

## Structure

The level view is [level-view.json]({MODULE_DIAGRAMS_DIRECTORY}/level-view.json); it shows the root
boundary and the maintainer. Add immediate submodules to the view before listing them below. Further
diagrams of this level live beside it under `{MODULE_DIAGRAMS_DIRECTORY}/` and are linked from this
summary or from the [design reference](design.md).

## Features

None.

## Contracts

None.

## Submodules

None.

## Representative Scenario

`scenario.{module_slug}.root-overview`: a maintainer reviews the root boundary before any
submodule or feature is added.

## Design Rationale

The root starts as one module so ownership is explicit before decomposition; implementation notes
and decisions are kept in the [design reference](design.md).
"""
    design = f"""# Design Reference: {project_name}

## Implementation Notes

No implementation detail has been recorded for this module yet.

## Design Rationale

No design rationale has been recorded for this module yet.

## Alternatives Considered

None recorded yet.

## Decision Log

- Initialized the root module package.
"""
    architecture = json.dumps(
        {
            "schema_version": 1,
            "diagram_type": "architecture",
            "meta": {
                "title": f"{project_name} — Root Module",
                "output": f"../../../../generated/architecture/{module_slug}-level-view.html",
                "views": [
                    {
                        "id": f"scenario.{module_slug}.root-overview",
                        "label": "Root overview",
                        "focus": ["maintainer"],
                        "note": "Review the root boundary before adding immediate submodules.",
                    }
                ],
            },
            "components": [
                {"id": "maintainer", "type": "external", "label": "Maintainer", "stable_id": "external.maintainer"}
            ],
            "connections": [],
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
        responsibility=f"Provide the observable responsibility of {project_name}.",
        boundary="Own the project-level outcome; delegate internal responsibilities to explicit submodules.",
        provided_contracts=(),
        required_contracts=(),
        children=(),
        files=files,
        conflicts=conflicts,
    )


def propose_initialization(project_root: str | Path, module_id: str | None = None, name: str | None = None) -> OperationResult:
    root = Path(project_root).resolve()
    try:
        proposal = _create_proposal(root, module_id, name)
    except ValueError as error:
        finding = Finding("CONCORDE-INIT-002", "error", ".concorde/config.json", str(error), "Use a lowercase stable module.<namespace> ID.")
        return OperationResult("init", ".", "invalid", findings=(finding,))
    files = proposal.files
    existing = [(root / item.path).is_file() and (root / item.path).read_text(encoding="utf-8") == item.content for item in files]
    if all(existing):
        return OperationResult("init", ".", "unchanged", tuple(item.path for item in files), result={"proposal": _proposal_payload(proposal)})
    return OperationResult("init", ".", "proposal", result={"proposal": _proposal_payload(proposal)})


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
