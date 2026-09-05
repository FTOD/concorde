"""Review-first initialization of a minimal Profile 7 root architecture and reflection index."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..model import Finding, InitializationProposal, ProposalFile, ToolResult
from ..projection import markdown_section
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


def _configured_architecture(project_root: Path) -> ToolResult | None:
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
        return ToolResult("init", ".", "conflict", findings=(finding,), result={"interaction_model": _interaction_model()})
    return ToolResult(
        "init",
        ".",
        "unchanged",
        artifacts=tuple(
            path
            for path in (
                ".concorde/config.json",
                ".concorde/reflections/index.json",
                ".concorde/reflections/config.json",
                module.path,
                *package.module_diagrams(module),
            )
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


def _create_proposal(project_root: Path, module_id: str | None, name: str | None,
                     operation_configuration: dict | None) -> InitializationProposal:
    from ..capabilities.operation_data import validate_typed

    configuration = validate_typed(operation_configuration, "concorde-operation-configuration", "/configuration")
    project_name = name or project_root.resolve().name
    derived = _slug(module_id.split(".", 1)[1] if module_id and module_id.startswith("module.") else project_name)
    identifier = module_id or f"module.{derived}"
    if not re.fullmatch(r"module\.[a-z0-9]+(?:[.-][a-z0-9-]+)*", identifier):
        raise ValueError("module ID must be a lowercase qualified module.<namespace> identity")
    module_slug = identifier.split(".", 1)[1].replace(".", "-")
    specification_root = f"specs/{module_slug}"
    config = json.dumps({"profile_version": PROFILE_VERSION, "root_module_id": identifier,
                         "specification_root": specification_root, "operation_configuration": configuration}, indent=2, sort_keys=True)
    diagram_output = f"generated/architecture/{module_slug}-system-overview.html"
    architecture = f"""---
id: {identifier}
kind: module
parent: null
modules: []
features: []
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: {diagram_output}
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
| `entity.{module_slug}.maintainer` | external-system | The maintainer who reviews and evolves the project architecture. | `external:{module_slug}.maintainer` |
| `entity.{module_slug}.project` | concept | The project outcome whose architecture this root governs. | `concept:{module_slug}.project` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `{identifier}` | owns_entity | `entity.{module_slug}.project` | The root module owns the project outcome boundary. |
| `entity.{module_slug}.maintainer` | reads_from | `entity.{module_slug}.project` | The maintainer reviews the governed outcome before decomposition. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.{module_slug}.review-root` | A maintainer reviews the project boundary. | `{identifier}` defines `entity.{module_slug}.project`. | The root responsibility and boundary are explicit before decomposition. | None |

## Modules

None.

## Features

None.

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- The starter does not guess child modules, features, contracts, or implementation narratives.
- Child modules, when added, follow business capability, use case, or axis of change, never an
  artifact type or a residual bucket.
"""
    diagram = json.dumps(
        {
            "schema_version": 1,
            "diagram_type": "architecture",
            "meta": {
                "title": f"{project_name} System Overview",
                "output": f"../../../{diagram_output}",
                "quality_profile": "showcase",
                "legend": {"mode": "hidden"},
                "viewBox": [760, 420],
            },
            "components": [
                {
                    "id": "maintainer",
                    "type": "external",
                    "label": "Maintainer",
                    "sublabel": "Architecture reviewer",
                    "pos": [40, 170],
                    "size": [160, 68],
                },
                {
                    "id": "root_module",
                    "type": "backend",
                    "label": project_name,
                    "sublabel": "Root module",
                    "pos": [300, 170],
                    "size": [170, 68],
                },
                {
                    "id": "project_outcome",
                    "type": "cloud",
                    "label": "Project Outcome",
                    "sublabel": "Governed boundary",
                    "pos": [570, 170],
                    "size": [160, 68],
                },
            ],
            "connections": [
                {
                    "id": "maintainer-reviews-outcome",
                    "from": "maintainer",
                    "to": "root_module",
                    "label": "reviews",
                    "variant": "emphasis",
                },
                {
                    "id": "module-owns-outcome",
                    "from": "root_module",
                    "to": "project_outcome",
                    "label": "owns boundary",
                },
            ],
        },
        indent=2,
    )
    reflection_index = json.dumps(
        {"schema_version": 1, "high_water": "R-000"}, indent=2, sort_keys=True
    )
    from ..capabilities.operation_data import checked_path, decode
    from ..reflections.configuration import validate_configuration

    settings_path = checked_path(project_root, ".concorde/reflections/config.json")
    reflection_settings = (settings_path.read_text(encoding="utf-8") if settings_path.is_file() else
                           (Path(__file__).resolve().parents[3] / "agent-assets/reflections/config.default.json").read_text(encoding="utf-8"))
    validate_configuration(decode(reflection_settings))
    files = (
        _proposal_file(".concorde/config.json", config),
        _proposal_file(".concorde/reflections/index.json", reflection_index),
        _proposal_file(".concorde/reflections/config.json", reflection_settings),
        _proposal_file(f"{specification_root}/architecture.md", architecture),
        _proposal_file(f"{specification_root}/diagrams/system-overview.json", diagram),
    )
    conflicts = tuple({"path": item.path, "reason": "target already exists"} for item in files
                      if (project_root / item.path).exists() and item.path != ".concorde/reflections/config.json")
    return InitializationProposal(
        proposal_version=4,
        project_root_id=identifier,
        responsibility=f"Describe and govern the project-level outcome provided by {project_name}.",
        boundary="Keep product responsibilities explicit and module-centered.",
        children=(),
        files=files,
        conflicts=conflicts,
    )


def propose_initialization(project_root: str | Path, module_id: str | None = None, name: str | None = None,
                           operation_configuration: dict | None = None) -> ToolResult:
    root = Path(project_root).resolve()
    configured = _configured_architecture(root)
    if configured is not None:
        if configured.status == "unchanged":
            from ..capabilities.operation_config import load_configuration

            try:
                load_configuration(root)
            except ValueError as error:
                return ToolResult("init", ".", "invalid", findings=(Finding(
                    "CONCORDE-INIT-007", "error", ".concorde/config.json", str(error),
                    "Preserve the existing architecture and apply an explicit configure proposal."),))
        return configured
    try:
        proposal = _create_proposal(root, module_id, name, operation_configuration)
    except ValueError as error:
        finding = Finding("CONCORDE-INIT-002", "error", ".concorde/config.json", str(error), "Provide a lowercase stable module.<namespace> ID and explicit concorde-operation-configuration@1 JSON.")
        return ToolResult("init", ".", "invalid", findings=(finding,), result={"interaction_model": _interaction_model()})
    exact = [(root / item.path).is_file() and (root / item.path).read_text(encoding="utf-8") == item.content for item in proposal.files]
    if all(exact):
        return ToolResult("init", ".", "unchanged", tuple(item.path for item in proposal.files), result={"interaction_model": _interaction_model(), "proposal": _payload(proposal)})
    return ToolResult("init", ".", "proposal", result={"interaction_model": _interaction_model(), "proposal": _payload(proposal)})


def _load_accepted(root: Path, proposal_path: str) -> InitializationProposal:
    path = ProjectRepository(root).resolve(safe_relative_path(proposal_path))
    value = json.loads(path.read_text(encoding="utf-8"))
    value = value.get("result", {}).get("proposal", value.get("proposal", value))
    if type(value.get("proposal_version")) is not int or value["proposal_version"] != 4:
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
        or ".concorde/reflections/index.json" not in paths
        or ".concorde/reflections/config.json" not in paths
        or not any(path.endswith("/architecture.md") for path in paths)
        or not any(path.endswith("/diagrams/system-overview.json") for path in paths)
        or len(paths) != 5
        or len(files) != 5
    ):
        raise ValueError(
            "proposal must contain exactly project configuration, reflection index and settings, one root architecture.md, and its system overview diagram"
        )
    from ..capabilities.operation_data import decode, validate_typed

    config = decode(next(item.content for item in files if item.path == ".concorde/config.json"))
    validate_typed(config.get("operation_configuration"), "concorde-operation-configuration", "/configuration")
    from ..reflections.configuration import validate_configuration

    validate_configuration(decode(next(item.content for item in files if item.path == ".concorde/reflections/config.json")))
    return InitializationProposal(
        proposal_version=4,
        project_root_id=value["project_root_id"],
        responsibility=value.get("responsibility", ""),
        boundary=value.get("boundary", ""),
        children=tuple(value.get("children", [])),
        files=tuple(files),
        conflicts=tuple(value.get("conflicts", [])),
    )


def apply_proposal(project_root: str | Path, proposal_path: str) -> ToolResult:
    root = Path(project_root).resolve()
    try:
        proposal = _load_accepted(root, proposal_path)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, RepositoryError) as error:
        finding = Finding("CONCORDE-INIT-003", "error", ".concorde/config.json", f"Accepted proposal is invalid: {error}", "Save the exact proposal JSON at a safe project-relative path and retry.")
        return ToolResult("init", ".", "invalid", findings=(finding,))
    expected = {item.path: item.content for item in proposal.files}
    try:
        resolved = {relative: ProjectRepository(root).resolve(relative) for relative in expected}
    except RepositoryError as error:
        return ToolResult("init", ".", "invalid", findings=(Finding(
            "CONCORDE-INIT-003", "error", ".concorde/config.json", str(error),
            "Use only real project-relative initialization paths."),))
    states = {
        relative: "missing" if not (path := resolved[relative]).exists() else "exact" if path.is_file() and path.read_text(encoding="utf-8") == content else "changed"
        for relative, content in expected.items()
    }
    if all(state == "exact" for state in states.values()):
        return ToolResult("init", ".", "unchanged", tuple(sorted(expected)), result={"proposal": _payload(proposal)})
    # Installation may have seeded project reflection settings before init. The
    # reviewed exact bytes are retained; every architecture/control target remains
    # create-only, and a changed settings file still rejects the whole apply.
    conflicts = [path for path, state in states.items() if state != "missing"
                 and not (path == ".concorde/reflections/config.json" and state == "exact")]
    if conflicts:
        findings = tuple(Finding("CONCORDE-INIT-004", "error", path, f"Target is {states[path]}; exact accepted content cannot be promoted.", "Move or reconcile the existing source, then accept a fresh proposal.") for path in sorted(conflicts))
        return ToolResult("init", ".", "conflict", findings=findings, result={"conflicts": sorted(conflicts)})
    try:
        created = ProjectRepository(root).stage_and_promote({path: content for path, content in expected.items() if states[path] == "missing"})
    except (OSError, RepositoryError) as error:
        finding = Finding("CONCORDE-INIT-005", "error", ".concorde/config.json", f"Staged promotion failed: {error}", "Resolve the filesystem failure and retry the accepted proposal.")
        return ToolResult("init", ".", "failed", findings=(finding,))
    return ToolResult("init", ".", "success", tuple(created), result={"created": created, "project_root_id": proposal.project_root_id})
