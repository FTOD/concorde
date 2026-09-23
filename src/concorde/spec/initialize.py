"""Initialize a project with a Protocol 11 registry and an honest root Module stub."""

from __future__ import annotations

import json
from pathlib import Path

from .changes import apply_files, file_change
from .repository import (
    PROFILE_VERSION,
    PROTOCOL_MANIFEST_PATH,
    REGISTRY_SCHEMA,
    SpecError,
    digest,
    identifier,
    read_file,
)
from .typed_data import (
    DIGEST,
    PATH,
    STRING,
    array,
    checked_path,
    decode,
    obj,
    register,
    typed,
    typed_schema,
)
from .validation import validate_repository

# Spec tooling's own typed values: the concorde-init request and response and the proposal they
# carry. The worker configuration is Request admission's type, referred to by name only.
PROPOSAL_FILE = obj(
    {
        "path": PATH,
        "before_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "content": {"type": "string"},
    }
)
PROPOSAL = obj(
    {
        "action": {"enum": ["initialize"]},
        "base_digest": {"anyOf": [DIGEST, {"type": "null"}]},
        "files": array(PROPOSAL_FILE),
    }
)
INIT_REQUEST = obj(
    {
        "action": {"enum": ["propose", "apply"]},
        "name": STRING,
        "target_id": STRING,
        "configuration": typed_schema("concorde-operation-configuration"),
        "proposal": typed_schema("concorde-project-proposal"),
        "run_in_primary": {"type": "boolean"},
    },
    ("name", "target_id", "configuration", "proposal", "run_in_primary"),
)
INIT_REQUEST_VERSION = 3
INIT_RESPONSE = obj(
    {
        "status": {"enum": ["proposed", "applied"]},
        "proposal": {
            "anyOf": [typed_schema("concorde-project-proposal"), {"type": "null"}]
        },
        "files": array(PATH),
    }
)
INIT_RESPONSE_VERSION = 1

register("concorde-project-proposal", 1, PROPOSAL)
register("concorde-init-request", INIT_REQUEST_VERSION, INIT_REQUEST)
register("concorde-init-response", INIT_RESPONSE_VERSION, INIT_RESPONSE)


def protocol_binding(package: Path) -> dict:
    """The binding of the running package's Protocol manifest."""
    raw = read_file(package, "protocol/manifest.json")
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def installed_protocol_binding(root: Path) -> dict:
    """The binding of the Protocol copy the installer placed under ``.concorde/protocol/``.

    Initialization and explicit acceptance bind this copy; neither creates it. A project without it
    has not had Concorde installed.
    """
    try:
        raw = read_file(root, PROTOCOL_MANIFEST_PATH)
    except (SpecError, OSError) as error:
        raise SpecError(
            "Concorde is not installed in this project: .concorde/protocol/ is missing; "
            "run the installer first",
            "not_installed",
        ) from error
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def initial_module_metadata(
    target_id: str, name: str, path: str, entries: list[str] | tuple[str, ...] = ()
) -> dict:
    local = target_id.split(".")[-1]
    defines = (
        [
            {
                "id": f"realization.{local}.existing-files",
                "type": "realization",
                "title": "Existing project files",
                "meaning": f"#realization.{local}.existing-files",
                "entries": list(entries),
            }
        ]
        if entries
        else []
    )
    return {
        "schema_version": 3,
        "document": {
            "id": f"document.{local}.module",
            "owner": target_id,
            "role": "module",
        },
        "module": {
            "title": name,
            "owns": [path],
            "contains": [],
            "uses": [],
            "includes": [],
            "participates": [],
        },
        "defines": defines,
        "relations": [],
    }


def existing_files(root: Path, documents: set[str]) -> list[str]:
    """Realization entries covering every file the project already keeps under version control.

    Every version-controlled file must be bound by some Module (CHK.binds.unbound). Until the
    project's Specs decompose it, the root Module binds the existing files: a top-level file
    exactly, a top-level directory by its prefix, and exactly the files a directory entry cannot
    bind (files the exclusion rule skips, and files next to a document member).
    """
    from .repository_base import bound_by, control_path
    from .validation import build_path, generated, generated_outputs, version_controlled

    tracked = version_controlled(root, untracked=True)
    if tracked is None:
        return []
    files, links = tracked
    outputs = generated_outputs(root)
    entries: set[str] = set()
    for path in files:
        if (
            path in documents
            or control_path(path)
            or generated(path, outputs)
            or build_path(path)
            or any(path == link or path.startswith(link + "/") for link in links)
            or not (root / path).is_file()
        ):
            continue
        top, _, rest = path.partition("/")
        directory = top + "/"
        if (
            rest
            and bound_by(directory, path)
            and not any(member.startswith(directory) for member in documents)
        ):
            entries.add(directory)
        else:
            entries.add(path)
    return sorted(entries)


def initial_registry(target_id: str, name: str, path: str) -> dict:
    block = initial_module_metadata(target_id, name, path)["module"]
    return {
        "schema_version": REGISTRY_SCHEMA,
        "modules": [
            {
                "id": target_id,
                "title": name,
                "entry": path,
                **{
                    key: block[key]
                    for key in ("owns", "contains", "uses", "includes", "participates")
                },
            }
        ],
    }


def initial_module_text(target_id: str, name: str, bound: bool = False) -> str:
    local = target_id.split(".")[-1]
    realization = (
        f'<a id="realization.{local}.existing-files"></a>\n\n'
        "The files the project kept under version control when Concorde was initialized are bound\n"
        "to this Module as its existing project files. They are not yet assigned to any\n"
        "responsibility; binding them describes nothing about what they do.\n\n"
        if bound
        else "No realization binds implementation files yet.\n\n"
    )
    return (
        f"# {name}\n\n## Purpose\n\n"
        f"This Module is the root of the {name} project. The project's purpose, its users and the\n"
        "limits of its promises have not been specified yet.\n\n"
        "## Terminology\n\n"
        "No terms have been defined yet.\n\n"
        "## Usage\n\n"
        "How the project is used is not specified yet: its entry points, inputs, results, effects,\n"
        "errors and repeat behaviour are unknown. Do not infer them from existing code.\n\n"
        "## Design\n\n"
        "The project's decomposition, state, control flow and design reasons are not specified yet.\n\n"
        + realization
        + "## Relationships\n\n"
        "The project's parts and their collaborations are not specified yet. This Module contains,\n"
        "uses and includes nothing, and no requirement or scenario has been written.\n"
    )


def project_proposal(
    root: Path,
    package: Path,
    name: str,
    configuration: dict,
    target_id: str = "module.project",
) -> dict:
    identifier(target_id)
    # The worker configuration is Request admission's typed value; it is stored unchanged.
    if (
        not isinstance(configuration, dict)
        or configuration.get("type_id") != "concorde-operation-configuration"
    ):
        raise SpecError(
            "configuration must be a concorde-operation-configuration value",
            "invalid_input",
        )
    if not isinstance(name, str) or not name.strip():
        raise SpecError("project name is required", "invalid_input")
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError(
            "project already configured; use configure to change settings",
            "already_initialized",
        )
    path = "specs/project/module.md"
    registry = initial_registry(target_id, name.strip(), path)
    entries = existing_files(root, {path, path + ".json"})
    config = {
        "profile_version": PROFILE_VERSION,
        "registry": ".concorde/specs.json",
        "protocol": installed_protocol_binding(root),
        "operation_configuration": configuration,
        "checks": [],
    }
    files = [
        file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
        file_change(
            root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"
        ),
        file_change(
            root, path, initial_module_text(target_id, name.strip(), bool(entries))
        ),
        file_change(
            root,
            path + ".json",
            json.dumps(
                initial_module_metadata(target_id, name.strip(), path, entries),
                indent=2,
            )
            + "\n",
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
    try:
        allowed = {
            ".concorde/config.json",
            ".concorde/specs.json",
            *(
                member
                for record in registry["modules"]
                for p in record["owns"]
                for member in (p, p + ".json")
            ),
        }
    except (KeyError, TypeError) as error:
        raise SpecError(
            "project proposal registry is not a Protocol 11 registry",
            "invalid_proposal",
        ) from error
    if proposal["base_digest"] is not None or any(
        item["before_digest"] is not None for item in files
    ):
        raise SpecError(
            "initialization cannot replace existing files", "invalid_proposal"
        )

    def verify():
        report = validate_repository(root, package_root=package)
        errors = [finding for finding in report.findings if finding.severity == "error"]
        if errors:
            raise SpecError(
                "target-state validation failed: "
                + "; ".join(f"{f.rule_id}: {f.message}" for f in errors)
            )

    changed = apply_files(root, files, allowed, verify=verify)
    return {
        "action": proposal["action"],
        "status": "applied",
        "files": changed,
        "profile_version": PROFILE_VERSION,
        "protocol": installed_protocol_binding(root),
    }


def run(request) -> dict:
    """Entry point of ``concorde-init``: propose or apply the first Spec of a project."""
    host, data = request.host, request.data
    if host.mode == "describe-policy":
        raise SpecError(
            "the initialization proposal is the preview of concorde-init",
            "use_proposal",
        )
    if data["action"] == "apply":
        if "proposal" not in data:
            raise SpecError(
                "apply requires the complete typed proposal", "invalid_input"
            )
        proposal = data["proposal"]
        value = apply_project_proposal(
            host.project_root,
            host.package_root,
            {
                "type_id": proposal["type_id"],
                "schema_version": proposal["schema_version"],
                **proposal["data"],
            },
        )
        return typed(
            "concorde-init-response",
            {"status": "applied", "proposal": None, "files": value["files"]},
        )
    if not {"name", "configuration"} <= set(data):
        raise SpecError(
            "initialization proposal requires name and configuration", "invalid_input"
        )
    value = project_proposal(
        host.project_root,
        host.package_root,
        data["name"],
        data["configuration"],
        data.get("target_id", "module.project"),
    )
    proposal = typed(
        "concorde-project-proposal",
        {key: value[key] for key in ("action", "base_digest", "files")},
    )
    return typed(
        "concorde-init-response",
        {
            "status": "proposed",
            "proposal": proposal,
            "files": [item["path"] for item in value["files"]],
        },
    )
