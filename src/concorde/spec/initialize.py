"""Initialize the document-unit profile (Profile 14) with an honest, self-contained Module stub."""

from __future__ import annotations

import json
from pathlib import Path

from .typed_data import decode, typed, validate_typed, checked_path, canonical
from .model import ToolResult
from .changes import file_change, apply_files
from .repository import (
    PROFILE_VERSION,
    REGISTRY_SCHEMA,
    SpecError,
    SpecRepository,
    identifier,
    digest,
    read_file,
)
from .validation import validate_repository


def protocol_binding(package: Path) -> dict:
    from ..distribution.build import BuildError, verify_fresh

    try:
        verify_fresh(package)
    except BuildError as error:
        raise SpecError(str(error), error.code) from error
    raw = read_file(package, "protocol/manifest.json")
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def installed_protocol_binding(root: Path) -> dict:
    """The binding of the Protocol copy the installer placed under ``.concorde/protocol/``.

    Initialization and explicit acceptance bind this copy; neither creates it. A project without it
    has not had Concorde installed.
    """
    from ..distribution.project_defaults import PROTOCOL_MANIFEST_PATH

    try:
        raw = read_file(root, PROTOCOL_MANIFEST_PATH)
    except (SpecError, OSError) as error:
        raise SpecError(
            "Concorde is not installed in this project: .concorde/protocol/ is missing; "
            "run the installer first",
            "not_installed",
        ) from error
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def empty_target(target_id: str, kind: str, title: str, documents: list[str]) -> dict:
    return {
        "id": target_id,
        "kind": kind,
        "title": title,
        "documents": documents,
        "references": [],
        "parent": None,
        "uses": [],
        "files": [],
        "checks": [],
    }


def initial_module_metadata(target_id: str) -> dict:
    local = target_id.split(".")[-1]
    return {
        "schema_version": 2,
        "document": {
            "id": "document." + target_id,
            "owner": target_id,
            "role": "module",
        },
        "entities": [
            {
                "id": f"entity.{local}.project-spec",
                "title": "Project Spec",
                "kind": "document collection",
                "meaning": f"#entity.{local}.project-spec",
            },
            {
                "id": f"entity.{local}.developer",
                "title": "Developer",
                "kind": "external actor",
                "meaning": f"#entity.{local}.developer",
            },
            {
                "id": f"entity.{local}.framework",
                "title": "Concorde Framework",
                "kind": "external software",
                "meaning": f"#entity.{local}.framework",
            },
        ],
        "dependencies": [],
        "bindings": [],
    }


def initial_module_text(target_id: str, name: str) -> str:
    local = target_id.split(".")[-1]
    return (
        f"# {name}\n\n## Purpose\n\n"
        "This Module identifies the initialized project. Its business purpose has not yet been supplied.\n\n"
        "## Terminology\n\n| Term | Meaning / definition |\n| --- | --- |\n"
        "| Project Spec | The documents describing the project's intended responsibilities and behavior. |\n"
        "| Draft | An initial description with explicit unknowns, not an invented business contract. |\n\n"
        "## Usage\n\nUse this draft to supply intended responsibility before planning implementation.\n"
        "Business entry points, inputs, results, effects, errors, repeat, cancellation and compatibility\n"
        "behavior are unknown; do not infer them from existing code or this authoring example.\n\n"
        "## Design\n\nBusiness responsibility decomposition, state, flow, dependencies and internal constraints\n"
        "remain unknown. The known authoring boundary is not an invented business design.\n\n"
        f'<a id="entity.{local}.project-spec"></a><a id="entity.{local}.developer"></a><a id="entity.{local}.framework"></a>\n\n'
        "The Developer supplies intended behavior in the Project Spec; Concorde Framework checks its\n"
        "Protocol conformance. No entity binds implementation files yet.\n\n"
        "## Relationships\n\nThis diagram covers authoring only, not the project's unknown business architecture.\n\n"
        "```mermaid\nflowchart TB\n"
        f"    accTitle: {name} authoring boundary\n"
        "    accDescr: The Developer specifies the Project Spec and Concorde Framework validates it. Business entities remain unknown.\n"
        '    developer["Developer"]\n    spec["Project Spec"]\n    framework["Concorde Framework"]\n'
        "    developer -->|specifies| spec\n    framework -->|validates| spec\n```\n\n"
        "## Precise specifications\n\nNo business requirements or scenarios have been supplied.\n"
        "Author them in registered implementation-role companions owned by this Module, not in this entry.\n"
        "A task needing that behavior reports Spec incomplete; initialization invents no acceptance cases.\n\n"
        "## Unresolved information\n\nBusiness scenarios, requirements, design and implementation remain unspecified.\n"
    )


def project_proposal(
    root: Path,
    package: Path,
    name: str,
    configuration: dict,
    target_id: str = "module.project",
) -> dict:
    identifier(target_id)
    configuration = validate_typed(configuration, "concorde-capability-configuration")
    if not isinstance(name, str) or not name.strip():
        raise SpecError("project name is required", "invalid_input")
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError(
            "project already configured; use configure to change settings",
            "already_initialized",
        )
    path = "specs/project/module.md"
    target = empty_target(target_id, "module", name, [path])
    registry = {
        "schema_version": REGISTRY_SCHEMA,
        "project_id": "project.initialized",
        "entry_target": target_id,
        "targets": [target],
        "checks": [],
    }
    config = {
        "profile_version": PROFILE_VERSION,
        "registry": ".concorde/specs.json",
        "protocol": installed_protocol_binding(root),
        "capability_configuration": configuration,
    }
    files = [
        file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
        file_change(
            root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"
        ),
        file_change(root, path, initial_module_text(target_id, name)),
        file_change(
            root,
            path + ".json",
            json.dumps(initial_module_metadata(target_id), indent=2) + "\n",
        ),
    ]
    # Initialization creates only what the user's project generates through Concorde. Everything
    # that exists because Concorde is installed (the Protocol copy, Reflection defaults, the
    # topology-artifact ignore file) is the installer's output.
    return {
        "type_id": "concorde-project-proposal",
        "schema_version": 1,
        "action": "initialize",
        "base_digest": None,
        "files": files,
    }


def apply_project_proposal(root: Path, package: Path, proposal: dict) -> dict:
    if (
        set(proposal) != {"type_id", "schema_version", "action", "base_digest", "files"}
        or proposal["type_id"] != "concorde-project-proposal"
        or proposal["schema_version"] != 1
        or proposal["action"] not in {"initialize"}
    ):
        raise SpecError("invalid project proposal envelope", "invalid_proposal")
    files = proposal["files"]
    proposed = {item["path"]: item for item in files}
    if (
        ".concorde/config.json" not in proposed
        or ".concorde/specs.json" not in proposed
    ):
        raise SpecError(
            "project proposal must include configuration and registry",
            "invalid_proposal",
        )
    config = decode(proposed[".concorde/config.json"]["content"])
    registry = decode(proposed[".concorde/specs.json"]["content"])
    if config.get("registry") != ".concorde/specs.json" or config.get(
        "protocol"
    ) != installed_protocol_binding(root):
        raise SpecError(
            "project proposal has a mismatched registry or Protocol binding",
            "invalid_proposal",
        )
    allowed = {
        ".concorde/config.json",
        ".concorde/specs.json",
        *(
            member
            for target in registry["targets"]
            for p in target["documents"]
            for member in (p, p + ".json")
        ),
    }
    if proposal["base_digest"] is not None or any(
        item["before_digest"] is not None for item in files
    ):
        raise SpecError(
            "initialization cannot replace existing files", "invalid_proposal"
        )

    def verify():
        report = validate_repository(root, package_root=package)
        if report.status != "success":
            raise SpecError(
                "target-state validation failed: "
                + "; ".join(f.message for f in report.findings)
            )

    changed = apply_files(root, files, allowed, verify=verify)
    return {
        "action": proposal["action"],
        "status": "applied",
        "files": changed,
        "profile_version": PROFILE_VERSION,
        "protocol": installed_protocol_binding(root),
    }
