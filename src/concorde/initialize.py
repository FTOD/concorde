"""Review-first initialization of a minimal Profile 7 root architecture and reflection log."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .model import Finding, InitializationProposal, OperationResult, ProposalFile
from .projection import markdown_section
from .repository import PROFILE_VERSION, ProjectRepository, RepositoryError, safe_relative_path


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"


def _proposal_file(path: str, content: str) -> ProposalFile:
    normalized = content.replace("\r\n", "\n").rstrip() + "\n"
    return ProposalFile(path, normalized, "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest())


def _payload(proposal: InitializationProposal) -> dict[str, Any]:
    return asdict(proposal)


def _interaction_model() -> dict[str, Any]:
    return {
        "user_interface": "skills",
        "deterministic_operations": "scripts",
        "workspace_state": "files",
        "file_lifetimes": {
            "durable": "module architecture.md and direct features/*.md",
            "temporal": ".concorde/attempts/<stable-feature-id>/",
            "generated": "disposable projections",
        },
    }


def _configured_architecture(project_root: Path) -> OperationResult | None:
    config = project_root / ".concorde/config.json"
    if not config.exists():
        return None
    try:
        package = ProjectRepository(project_root).load()
        roots = package.by_id.get(package.root_module_id, ())
        if len(roots) != 1 or roots[0].kind != "module":
            raise RepositoryError("configured root_module_id does not resolve to exactly one module")
        module = roots[0]
    except RepositoryError as error:
        finding = Finding("CONCORDE-INIT-006", "error", ".concorde/config.json", f"A configured architecture exists but is incomplete: {error}", "Reconcile the existing Profile 7 configuration, root architecture, and control state; initialization never overwrites them.")
        return OperationResult("init", ".", "conflict", findings=(finding,), result={"interaction_model": _interaction_model()})
    return OperationResult(
        "init",
        ".",
        "unchanged",
        artifacts=tuple(
            path
            for path in (".concorde/config.json", ".concorde/reflections/log.md", module.path)
            if (project_root / path).is_file()
        ),
        result={
            "architecture": {
                "root_module_id": package.root_module_id,
                "specification_root": package.specification_root,
                "module_architecture": module.path,
                "responsibility": markdown_section(module.body, "Responsibility"),
                "boundary": markdown_section(module.body, "Boundary"),
                "modules": list(package.modules[module.identifier].modules),
                "features": list(package.modules[module.identifier].features),
            },
            "interaction_model": _interaction_model(),
        },
    )


def _create_proposal(project_root: Path, module_id: str | None, name: str | None) -> InitializationProposal:
    project_name = name or project_root.resolve().name
    derived = _slug(module_id.split(".", 1)[1] if module_id and module_id.startswith("module.") else project_name)
    identifier = module_id or f"module.{derived}"
    if not re.fullmatch(r"module\.[a-z0-9]+(?:[.-][a-z0-9-]+)*", identifier):
        raise ValueError("module ID must be a lowercase qualified module.<namespace> identity")
    module_slug = identifier.split(".", 1)[1].replace(".", "-")
    specification_root = f"specs/{module_slug}"
    config = json.dumps({"profile_version": PROFILE_VERSION, "root_module_id": identifier, "specification_root": specification_root}, indent=2, sort_keys=True)
    architecture = f"""---
id: {identifier}
kind: module
parent: null
modules: []
features: []
---

# Architecture: {project_name}

## Responsibility

Describe and govern the project-level outcome provided by {project_name}.

## Boundary

Own the project-level outcome. Add only reviewed child modules and architecture-significant entities;
do not infer product boundaries from repository directories.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.{module_slug}.project` | concept | The project outcome whose architecture this root governs. | `concept:{module_slug}.project` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `{identifier}` | owns_entity | `entity.{module_slug}.project` | The root module owns the project outcome boundary. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.{module_slug}.review-root` | A maintainer reviews the project boundary. | `{identifier}` defines `entity.{module_slug}.project`. | The root responsibility and boundary are explicit before decomposition. | None |

## Modules

None.

## Features

None.

## Decisions

- The starter does not guess child modules, features, contracts, or implementation narratives.
"""
    reflections = f"""# Reflections: {project_name}

<!-- concorde-reflection-high-water: R-000 -->

Project-wide process memory for difficult choices, workarounds, deferrals, and blockers encountered
while changing a selected feature. Entries use the installed Concorde Reflection Log v1 grammar.
"""
    files = (
        _proposal_file(".concorde/config.json", config),
        _proposal_file(".concorde/reflections/log.md", reflections),
        _proposal_file(f"{specification_root}/architecture.md", architecture),
    )
    conflicts = tuple({"path": item.path, "reason": "target already exists"} for item in files if (project_root / item.path).exists())
    return InitializationProposal(
        proposal_version=2,
        project_root_id=identifier,
        responsibility=f"Describe and govern the project-level outcome provided by {project_name}.",
        boundary="Keep product responsibilities explicit and module-centered.",
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
    exact = [(root / item.path).is_file() and (root / item.path).read_text(encoding="utf-8") == item.content for item in proposal.files]
    if all(exact):
        return OperationResult("init", ".", "unchanged", tuple(item.path for item in proposal.files), result={"interaction_model": _interaction_model(), "proposal": _payload(proposal)})
    return OperationResult("init", ".", "proposal", result={"interaction_model": _interaction_model(), "proposal": _payload(proposal)})


def _load_accepted(root: Path, proposal_path: str) -> InitializationProposal:
    path = ProjectRepository(root).resolve(safe_relative_path(proposal_path))
    value = json.loads(path.read_text(encoding="utf-8"))
    value = value.get("result", {}).get("proposal", value.get("proposal", value))
    if value.get("proposal_version") != 2:
        raise ValueError("unsupported or missing proposal_version")
    files: list[ProposalFile] = []
    for item in value.get("files", []):
        relative = safe_relative_path(item["path"])
        content = item["content"].replace("\r\n", "\n")
        expected = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        if item.get("sha256") != expected:
            raise ValueError(f"proposal content hash does not match for {relative}")
        files.append(ProposalFile(relative, content, expected))
    paths = {item.path for item in files}
    if (
        ".concorde/config.json" not in paths
        or ".concorde/reflections/log.md" not in paths
        or not any(path.endswith("/architecture.md") for path in paths)
        or len(paths) != 3
    ):
        raise ValueError(
            "proposal must contain exactly configuration, reflection log, and one root architecture.md"
        )
    return InitializationProposal(
        proposal_version=2,
        project_root_id=value["project_root_id"],
        responsibility=value.get("responsibility", ""),
        boundary=value.get("boundary", ""),
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
    states = {
        relative: "missing" if not (path := root / relative).exists() else "exact" if path.is_file() and path.read_text(encoding="utf-8") == content else "changed"
        for relative, content in expected.items()
    }
    if all(state == "exact" for state in states.values()):
        return OperationResult("init", ".", "unchanged", tuple(sorted(expected)), result={"proposal": _payload(proposal)})
    if any(state != "missing" for state in states.values()):
        findings = tuple(Finding("CONCORDE-INIT-004", "error", path, f"Target is {state}; exact accepted content cannot be promoted.", "Move or reconcile the existing source, then accept a fresh proposal.") for path, state in sorted(states.items()) if state != "missing")
        return OperationResult("init", ".", "conflict", findings=findings, result={"conflicts": [path for path, state in sorted(states.items()) if state != "missing"]})
    try:
        created = ProjectRepository(root).stage_and_promote(expected)
    except (OSError, RepositoryError) as error:
        finding = Finding("CONCORDE-INIT-005", "error", ".concorde/config.json", f"Staged promotion failed: {error}", "Resolve the filesystem failure and retry the accepted proposal.")
        return OperationResult("init", ".", "failed", findings=(finding,))
    return OperationResult("init", ".", "success", tuple(created), result={"created": created, "project_root_id": proposal.project_root_id})
