"""Initialize Profile 8. Profile 7 projects are unsupported and have no migration path."""
from __future__ import annotations

import json
from pathlib import Path

from ..host.typed_data import decode, typed, validate_typed, checked_path, canonical
from ..model import ToolResult
from .changes import file_change, apply_files
from .repository import SpecError, SpecRepository, identifier, digest, read_file
from .validation import validate_repository


TOPOLOGY_IGNORE_PATH = ".concorde/topology-proposals/.gitignore"
TOPOLOGY_IGNORE = "# Exact topology applications are local, maintainer-reviewed host artifacts.\n*\n!.gitignore\n"


def protocol_binding(package: Path) -> dict:
    raw = read_file(package, "protocol/manifest.json")
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def empty_target(target_id: str, kind: str, title: str, documents: list[str]) -> dict:
    return {"id": target_id, "kind": kind, "title": title, "documents": documents,
            "scope_parent": None, "component_parent": None, "participates_in": [],
            "implementation": [], "features": [], "apis": [], "checks": [], "diagrams": []}


def project_proposal(root: Path, package: Path, name: str, configuration: dict,
                     target_id: str = "domain.project") -> dict:
    identifier(target_id)
    configuration = validate_typed(configuration, "concorde-operation-configuration")
    if not isinstance(name, str) or not name.strip():
        raise SpecError("project name is required", "invalid_input")
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError("project already configured; use configure to change settings", "already_initialized")
    path = "specs/project.md"
    registry = {"schema_version": 1, "project_id": "project.initialized", "entry_target": target_id,
        "targets": [empty_target(target_id, "domain", name, [path])], "checks": []}
    config = {"profile_version": 8, "registry": ".concorde/specs.json",
        "protocol": protocol_binding(package), "operation_configuration": configuration}
    declaration = {"id": "document." + target_id, "targets": [target_id],
                   "main_visible": True}
    text = ("```concorde-document\n" + json.dumps(declaration, indent=2) + "\n```\n\n"
        f"# {name}\n\nThis Domain scopes the initialized project. Its current supported use is to\n"
        "identify the project and author its intended behavior. Business entities, rules, participating\n"
        "components, and product features have not yet been supplied. A task requiring those facts\n"
        "must report Spec incomplete and name the missing information. Initialization does not infer\n"
        "requirements from implementation code.\n\nThe project maintainer supplies intended behavior;\n"
        "Concorde records it in explicitly registered Spec documents before planning implementation.\n")
    files = [file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
             file_change(root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"),
             file_change(root, path, text)]
    # Reflection defaults remain independently owned, and are never overwritten on init.
    index = ".concorde/reflections/index.json"
    if not checked_path(root, index).exists():
        files.append(file_change(root, index, json.dumps({"schema_version": 1, "high_water": "R-000"}, indent=2) + "\n"))
    settings = ".concorde/reflections/config.json"
    if not checked_path(root, settings).exists():
        files.append(file_change(root, settings, read_file(package, "src/concorde/reflections/config.default.json").decode()))
    if not checked_path(root, TOPOLOGY_IGNORE_PATH).exists():
        files.append(file_change(root, TOPOLOGY_IGNORE_PATH, TOPOLOGY_IGNORE))
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
    if config.get("registry") != ".concorde/specs.json" or config.get("protocol") != protocol_binding(package):
        raise SpecError("project proposal has a mismatched registry or Protocol binding", "invalid_proposal")
    allowed = {".concorde/config.json", ".concorde/specs.json", TOPOLOGY_IGNORE_PATH,
               ".concorde/reflections/index.json", ".concorde/reflections/config.json",
               *(p for target in registry["targets"] for p in target["documents"])}
    if proposal["base_digest"] is not None or any(item["before_digest"] is not None for item in files):
        raise SpecError("initialization cannot replace existing files", "invalid_proposal")
    def verify():
        report = validate_repository(root, package_root=package)
        if report.status != "success":
            raise SpecError("target-state validation failed: " + "; ".join(f.message for f in report.findings))
    changed = apply_files(root, files, allowed, verify=verify)
    return {"action": proposal["action"], "status": "applied", "files": changed,
            "profile_version": 8, "protocol": protocol_binding(package)}
