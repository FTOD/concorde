"""Initialize the Module/Implementation profile with an honest, self-contained Module stub."""
from __future__ import annotations

import json
from pathlib import Path

from ..host.typed_data import decode, typed, validate_typed, checked_path, canonical
from ..model import ToolResult
from .changes import file_change, apply_files
from .repository import SpecError, SpecRepository, identifier, digest, read_file
from .validation import validate_repository


TOPOLOGY_IGNORE_PATH = ".concorde/topology-proposals/.gitignore"
TOPOLOGY_IGNORE = "# Exact topology applications are local, developer-reviewed host artifacts.\n*\n!.gitignore\n"


def protocol_binding(package: Path) -> dict:
    from ..host.build import BuildError, verify_fresh
    try:
        verify_fresh(package)
    except BuildError as error:
        raise SpecError(str(error), error.code) from error
    raw = read_file(package, "protocol/manifest.json")
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def empty_target(target_id: str, kind: str, title: str, documents: list[str]) -> dict:
    return {"id": target_id, "kind": kind, "title": title, "documents": documents,
            "parent": None, "uses": [], "implementations": [],
            "features": [], "interfaces": [], "checks": [], "diagrams": []}


def initial_overview(name: str, output: str) -> dict:
    """An honest System overview of the known authoring boundary, not invented business design."""
    return {
        "schema_version": 1, "diagram_type": "architecture",
        "meta": {"title": name, "output": output, "quality_profile": "showcase",
                 "locale": "en", "viewBox": [1080, 520]},
        "components": [
            {"id": "developer", "type": "external", "label": "Project developer",
             "sublabel": "Supplies intended behavior", "pos": [40, 180], "size": [220, 80]},
            {"id": "project-spec", "type": "database", "label": "Project Spec",
             "sublabel": "Business model not yet supplied", "pos": [420, 180], "size": [220, 80]},
            {"id": "framework", "type": "external", "label": "Concorde Framework",
             "sublabel": "Checks Concorde Spec Protocol conformance", "pos": [800, 180], "size": [220, 80]}],
        "boundaries": [{"kind": "region", "label": "Known project-authoring scope",
                        "wraps": ["project-spec"], "pad": 30}],
        "connections": [{"from": "developer", "to": "project-spec", "label": "specifies"},
                        {"from": "project-spec", "to": "framework", "label": "validates"}],
        "cards": [{"dot": "amber", "title": "Unspecified business architecture",
                   "items": ["Only project identity and Spec authoring are known.",
                             "Define the Module's internal domain and external relationships before implementation."]}]}


def project_proposal(root: Path, package: Path, name: str, configuration: dict,
                     target_id: str = "module.project") -> dict:
    identifier(target_id)
    configuration = validate_typed(configuration, "concorde-capability-configuration")
    if not isinstance(name, str) or not name.strip():
        raise SpecError("project name is required", "invalid_input")
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError("project already configured; use configure to change settings", "already_initialized")
    path = "specs/modules/project/module.md"
    diagram_path = "specs/modules/project/diagrams/overview.architecture.json"
    target = empty_target(target_id, "module", name, [path])
    target["diagrams"] = [{"source": diagram_path, "kind": "architecture", "title": name,
                           "recipe": "system-overview"}]
    registry = {"schema_version": 2, "project_id": "project.initialized", "entry_target": target_id,
        "targets": [target], "implementations": [], "checks": []}
    config = {"profile_version": 9, "registry": ".concorde/specs.json",
        "protocol": protocol_binding(package), "capability_configuration": configuration}
    declaration = {"id": "document." + target_id, "targets": [target_id],
                   "main_visible": True}
    text = ("```concorde-document\n" + json.dumps(declaration, indent=2) + "\n```\n\n"
        f"# {name}\n\n[System overview](diagrams/overview.architecture.json)\n\n## Features and interfaces\n\nProduct capabilities and their usage interfaces are not yet specified.\n\n## Architecture\n\nThis Module describes the initialized project. Its current supported use is to\n"
        "identify the project and author its intended behavior. Business entities, rules, participating\n"
        "components, and product features have not yet been supplied. A task requiring those facts\n"
        "must report Spec incomplete and name the missing information. Initialization does not infer\n"
        "requirements from implementation code.\n\nThe project developer supplies intended behavior;\n"
        "Concorde Framework records it in explicitly registered Spec documents before planning implementation.\n\n"
        "The known entities are the Project Spec (a document collection), the Developer (its external\n"
        "author), and Concorde Framework (the external software that validates it). The Developer\n"
        "specifies intended behavior in the Project Spec; the Framework checks its Concorde Spec Protocol\n"
        "conformance. This authoring relationship is not the project's unknown business architecture.\n\n"
        "## Architecture overview\n\nThe declared System overview shows only this known authoring boundary.\n"
        "The docsite embeds it at the start of this main page, before the Module prose. Replace it with the Module's actual internal\n"
        "architecture and relevant external relationships when those facts have been supplied.\n")
    files = [file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
             file_change(root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"),
             file_change(root, path, text),
             file_change(root, diagram_path, json.dumps(initial_overview(name,
                 "../../../../generated/diagrams/project.html"), indent=2) + "\n")]
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
               *(p for target in registry["targets"] for p in target["documents"]),
               *(d["source"] for target in registry["targets"] for d in target["diagrams"])}
    if proposal["base_digest"] is not None or any(item["before_digest"] is not None for item in files):
        raise SpecError("initialization cannot replace existing files", "invalid_proposal")
    def verify():
        report = validate_repository(root, package_root=package)
        if report.status != "success":
            raise SpecError("target-state validation failed: " + "; ".join(f.message for f in report.findings))
    changed = apply_files(root, files, allowed, verify=verify)
    return {"action": proposal["action"], "status": "applied", "files": changed,
            "profile_version": 9, "protocol": protocol_binding(package)}
