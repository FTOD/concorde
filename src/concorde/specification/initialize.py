"""Initialize Profile 8 or explicitly migrate authored replacements from Profile 7."""
from __future__ import annotations

import json
from pathlib import Path

from ..capabilities.operation_data import decode, typed, validate_typed, checked_path, canonical
from ..model import ToolResult
from .changes import file_change, apply_files
from .repository import SpecError, SpecRepository, identifier, digest, read_file
from .validation import validate_repository


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
        raise SpecError("project already configured; use configure or an explicit migration", "already_initialized")
    path = "specs/project.md"
    registry = {"schema_version": 1, "project_id": "project.initialized", "entry_target": target_id,
        "targets": [empty_target(target_id, "domain", name, [path])], "checks": []}
    config = {"profile_version": 8, "registry": ".concorde/specs.json",
        "protocol": protocol_binding(package), "operation_configuration": configuration}
    text = (f"# {name}\n\nThis Domain scopes the initialized project. Its current supported use is to\n"
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
        files.append(file_change(root, settings, read_file(package, "agent-assets/reflections/config.default.json").decode()))
    return {"type_id": "concorde-project-proposal", "schema_version": 1,
            "action": "initialize", "base_digest": None, "files": files}


def migration_proposal(root: Path, package: Path, registry: dict, documents: list[dict],
                       configuration: dict | None = None) -> dict:
    old = read_file(root, ".concorde/config.json")
    previous = decode(old.decode())
    if previous.get("profile_version") != 7:
        raise SpecError("migration requires Profile 7; runtime never interprets it as Profile 8", "invalid_migration")
    attempts = checked_path(root, ".concorde/attempts")
    if attempts.exists() and any(attempts.iterdir()):
        raise SpecError("finish active attempts before migrating", "active_attempt")
    # Classification and self-contained replacements are authored inputs. A deterministic migration
    # cannot infer business scopes or claim that old ancestor-dependent prose is complete.
    configuration = validate_typed(configuration or previous.get("operation_configuration"), "concorde-operation-configuration")
    config = {"profile_version": 8, "registry": ".concorde/specs.json",
              "protocol": protocol_binding(package), "operation_configuration": configuration}
    allowed = {path for target in registry["targets"] for path in target["documents"]}
    files = [file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
             file_change(root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n")]
    for item in documents:
        if set(item) != {"path", "content"} or item["path"] not in allowed:
            raise SpecError("migration documents must belong to the proposed registry", "invalid_migration")
        files.append(file_change(root, item["path"], item["content"]))
    return {"type_id": "concorde-project-proposal", "schema_version": 1,
            "action": "migrate", "base_digest": digest(old), "files": files}


def apply_project_proposal(root: Path, package: Path, proposal: dict) -> dict:
    if (set(proposal) != {"type_id", "schema_version", "action", "base_digest", "files"}
            or proposal["type_id"] != "concorde-project-proposal" or proposal["schema_version"] != 1
            or proposal["action"] not in {"initialize", "migrate"}):
        raise SpecError("invalid project proposal envelope", "invalid_proposal")
    files = proposal["files"]
    proposed = {item["path"]: item for item in files}
    if ".concorde/config.json" not in proposed or ".concorde/specs.json" not in proposed:
        raise SpecError("project proposal must include configuration and registry", "invalid_proposal")
    config = decode(proposed[".concorde/config.json"]["content"])
    registry = decode(proposed[".concorde/specs.json"]["content"])
    if config.get("registry") != ".concorde/specs.json" or config.get("protocol") != protocol_binding(package):
        raise SpecError("project proposal has a mismatched registry or Protocol binding", "invalid_proposal")
    allowed = {".concorde/config.json", ".concorde/specs.json",
               *(p for target in registry["targets"] for p in target["documents"])}
    if proposal["action"] == "initialize":
        allowed.update({".concorde/reflections/index.json", ".concorde/reflections/config.json"})
        if proposal["base_digest"] is not None or any(item["before_digest"] is not None for item in files):
            raise SpecError("initialization cannot replace existing files", "invalid_proposal")
    else:
        old = read_file(root, ".concorde/config.json")
        if digest(old) != proposal["base_digest"] or decode(old.decode()).get("profile_version") != 7:
            raise SpecError("migration base changed", "stale_proposal")
        attempts = checked_path(root, ".concorde/attempts")
        if attempts.exists() and any(attempts.iterdir()):
            raise SpecError("migration cannot import an active attempt", "active_attempt")
    def verify():
        report = validate_repository(root, package_root=package)
        if report.status != "success":
            raise SpecError("target-state validation failed: " + "; ".join(f.message for f in report.findings))
    changed = apply_files(root, files, allowed, verify=verify)
    return {"action": proposal["action"], "status": "applied", "files": changed,
            "profile_version": 8, "protocol": protocol_binding(package)}
