"""Initialize the two-part Module profile (Profile 13) with an honest, self-contained Module stub."""
from __future__ import annotations

import json
from pathlib import Path

from .typed_data import decode, typed, validate_typed, checked_path, canonical
from .model import ToolResult
from .changes import file_change, apply_files
from .repository import PROFILE_VERSION, REGISTRY_SCHEMA, SpecError, SpecRepository, identifier, digest, read_file
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
        raise SpecError("Concorde is not installed in this project: .concorde/protocol/ is missing; "
                        "run the installer first", "not_installed") from error
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def empty_target(target_id: str, kind: str, title: str, documents: list[str]) -> dict:
    return {"id": target_id, "kind": kind, "title": title, "documents": documents,
            "references": [], "parent": None, "uses": [], "files": [], "checks": []}


def initial_module_text(target_id: str, name: str) -> str:
    """An honest two-part stub of the known authoring boundary, not invented business design."""
    declaration = {"id": "document." + target_id, "owner": target_id, "main_visible": True}
    local = target_id.split(".")[-1]
    entities = [
        {"id": f"entity.{local}.project-spec", "title": "Project Spec", "kind": "document collection",
         "responsibility": "Records the intended behavior and architecture the developer supplies."},
        {"id": f"entity.{local}.developer", "title": "Developer", "kind": "external actor",
         "responsibility": "Supplies the intended behavior, entities and relationships."},
        {"id": f"entity.{local}.framework", "title": "Concorde Framework", "kind": "external software",
         "responsibility": "Checks the Project Spec for Concorde Spec Protocol conformance."},
    ]
    return ("```concorde-document\n" + json.dumps(declaration, indent=2) + "\n```\n\n"
        f"# {name}\n\n## Usage & Contract\n\n### Purpose\n\n"
        "This Module identifies the initialized project. Its only supported use is to identify the\n"
        "project and author its intended behavior; business purpose has not yet been supplied.\n\n"
        "### Usage\n\n"
        "Use this draft to supply the project's intended responsibility and its consumer-facing\n"
        "behavior before planning implementation. No business entry points, inputs, results, effects,\n"
        "errors, repeat, cancellation or compatibility behavior have been supplied. Do not infer them\n"
        "from this authoring example or from existing code.\n\n"
        "### Requirements\n\n"
        "No Module-level requirement has been supplied. Each requirement, once known, is one decidable\n"
        "SHALL statement in its own section; initialization does not infer requirements from\n"
        "implementation code.\n\n"
        "### Scenarios\n\n"
        "No business scenario has been supplied. A task that requires business behavior must report\n"
        "Spec incomplete and name the missing scenario. Tests, once written, declare the scenario they\n"
        "verify; no Spec section lists tests.\n\n"
        "## Architecture & Realization\n\n"
        "### Design\n\n"
        "Business responsibility decomposition, state, control/data flow, dependencies and internal\n"
        "constraints are unknown. The authoring boundary below explains only how the developer\n"
        "supplies a Spec and the Framework checks it; it is not an invented business design.\n\n"
        "### Entities\n\n"
        "The known entities are the Project Spec (a document collection), the Developer (its external\n"
        "author) and Concorde Framework (the external software that validates it). No entity lists\n"
        "implementation files yet.\n\n"
        "```concorde-entities\n" + json.dumps(entities, indent=2) + "\n```\n\n"
        "### Relationships\n\n"
        "The Developer specifies intended behavior in the Project Spec; the Framework checks its\n"
        "Concorde Spec Protocol conformance. This authoring relationship is not the project's unknown\n"
        "business architecture. Replace it with the Module's actual entities and relationships when\n"
        "those facts have been supplied.\n\n"
        "```mermaid\nflowchart TB\n"
        f"    accTitle: {name} authoring boundary\n"
        "    accDescr: The Developer specifies the Project Spec and Concorde Framework validates it. Business entities are not yet known.\n"
        "    developer[\"Developer\"]\n    spec[\"Project Spec\"]\n    framework[\"Concorde Framework\"]\n"
        "    developer -->|specifies| spec\n    framework -->|validates| spec\n```\n\n"
        "### Unresolved information\n\n"
        "Business scenarios, requirements, entities, relationships and implementation files remain\n"
        "unspecified until the developer supplies them.\n")


def project_proposal(root: Path, package: Path, name: str, configuration: dict,
                     target_id: str = "module.project") -> dict:
    identifier(target_id)
    configuration = validate_typed(configuration, "concorde-capability-configuration")
    if not isinstance(name, str) or not name.strip():
        raise SpecError("project name is required", "invalid_input")
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError("project already configured; use configure to change settings", "already_initialized")
    path = "specs/project/module.md"
    target = empty_target(target_id, "module", name, [path])
    registry = {"schema_version": REGISTRY_SCHEMA, "project_id": "project.initialized", "entry_target": target_id,
        "targets": [target], "checks": []}
    config = {"profile_version": PROFILE_VERSION, "registry": ".concorde/specs.json",
        "protocol": installed_protocol_binding(root), "capability_configuration": configuration}
    files = [file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
             file_change(root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"),
             file_change(root, path, initial_module_text(target_id, name))]
    # Initialization creates only what the user's project generates through Concorde. Everything
    # that exists because Concorde is installed (the Protocol copy, Reflection defaults, the
    # topology-artifact ignore file) is the installer's output.
    return {"type_id": "concorde-project-proposal", "schema_version": 1,
            "action": "initialize", "base_digest": None, "files": files}


def apply_project_proposal(root: Path, package: Path, proposal: dict) -> dict:
    if (set(proposal) != {"type_id", "schema_version", "action", "base_digest", "files"}
            or proposal["type_id"] != "concorde-project-proposal" or proposal["schema_version"] != 1
            or proposal["action"] not in {"initialize"}):
        raise SpecError("invalid project proposal envelope", "invalid_proposal")
    files = proposal["files"]
    proposed = {item["path"]: item for item in files}
    if ".concorde/config.json" not in proposed or ".concorde/specs.json" not in proposed:
        raise SpecError("project proposal must include configuration and registry", "invalid_proposal")
    config = decode(proposed[".concorde/config.json"]["content"])
    registry = decode(proposed[".concorde/specs.json"]["content"])
    if config.get("registry") != ".concorde/specs.json" or config.get("protocol") != installed_protocol_binding(root):
        raise SpecError("project proposal has a mismatched registry or Protocol binding", "invalid_proposal")
    allowed = {".concorde/config.json", ".concorde/specs.json",
               *(p for target in registry["targets"] for p in target["documents"])}
    if proposal["base_digest"] is not None or any(item["before_digest"] is not None for item in files):
        raise SpecError("initialization cannot replace existing files", "invalid_proposal")
    def verify():
        report = validate_repository(root, package_root=package)
        if report.status != "success":
            raise SpecError("target-state validation failed: " + "; ".join(f.message for f in report.findings))
    changed = apply_files(root, files, allowed, verify=verify)
    return {"action": proposal["action"], "status": "applied", "files": changed,
            "profile_version": PROFILE_VERSION, "protocol": installed_protocol_binding(root)}
