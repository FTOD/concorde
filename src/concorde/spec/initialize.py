"""Initialize a project with a Protocol 14 registry and an honest root Module stub."""

from __future__ import annotations

import json
from pathlib import Path

from .changes import apply_files, file_change
from .errors import from_finding, system_cause
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
    array,
    checked_path,
    decode,
    obj,
    register,
    typed,
)
from .validation import validate_repository

# Spec tooling's own typed value: the initialization proposal.
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
        "source_digest": DIGEST,
        "files": array(PROPOSAL_FILE),
    }
)
PROPOSAL_VERSION = 2
register("concorde-project-proposal", PROPOSAL_VERSION, PROPOSAL)


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
            f"Concorde is not installed in {root}: {PROTOCOL_MANIFEST_PATH} cannot be read",
            "not_installed",
            path=PROTOCOL_MANIFEST_PATH,
            causes=[error if isinstance(error, SpecError) else system_cause(error)],
        ) from error
    return {"version": decode(raw.decode())["version"], "digest": digest(raw)}


def initial_module_metadata(
    target_id: str,
    name: str,
    path: str,
    entries: list[str] | tuple[str, ...] = (),
    installed: list[str] | tuple[str, ...] = (),
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
    ) + (
        [
            {
                "id": f"realization.{local}.{INSTALLATION}",
                "type": "realization",
                "title": "Concorde installation",
                "meaning": f"#realization.{local}.{INSTALLATION}",
                "entries": list(installed),
            }
        ]
        if installed
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


def source_digest(root: Path, documents: set[str]) -> str:
    """The digest of the project state a proposal is computed from: the installed Protocol
    binding and the files the root Module's realizations bind."""
    return digest(
        {
            "protocol": installed_protocol_binding(root),
            "entries": existing_files(root, documents),
            "installed": installed_files(root),
        }
    )


# The realization of the files the Concorde installer placed outside ``.concorde/``.
INSTALLATION = "concorde-installation"


def installed_files(root: Path) -> list[str]:
    """The files the installer's receipt names that live outside ``.concorde/`` and exist:
    Concorde's own skill, workflows and pi files, never a file of the project it only amends."""
    from .repository_base import installed_files as listed

    return sorted(path for path in listed(root) if (root / path).is_file())


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
    installed = set(installed_files(root))
    entries: set[str] = set()
    for path in files:
        if (
            path in installed
            or path in documents
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
            and not any(
                member.startswith(directory) for member in (*documents, *installed)
            )
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


def initial_module_text(
    target_id: str, name: str, bound: bool = False, installed: bool = False
) -> str:
    local = target_id.split(".")[-1]
    realization = (
        f'<a id="realization.{local}.existing-files"></a>\n\n'
        "The files the project kept under version control when Concorde was initialized are bound\n"
        "to this Module as its existing project files. They are not yet assigned to any\n"
        "responsibility; binding them describes nothing about what they do.\n\n"
        if bound
        else "No realization binds implementation files yet.\n\n"
    ) + (
        f'<a id="realization.{local}.{INSTALLATION}"></a>\n\n'
        "The files the Concorde installer placed outside `.concorde/`, such as the agents' skill and\n"
        "workflows, are bound to this Module as its Concorde installation. They configure the\n"
        "agents that work on the project and are not the project's own code; the installer\n"
        "replaces them on every update, and no task may change them: a grant gives them at\n"
        "most read access.\n\n"
        if installed
        else ""
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
        "The project's parts and their collaborations are not specified yet. This Module contains,\n"
        "uses and includes nothing, and no requirement or scenario has been written.\n\n"
        + realization
    ).rstrip("\n") + "\n"


# Where a project's own environment usually is; the first that exists becomes `python`.
PROJECT_PYTHONS = (".venv/bin/python", "venv/bin/python")


def project_python(root: Path, python: str | None) -> str | None:
    """The project interpreter the configuration records: the one named, else a usual one."""
    if python is not None:
        if not isinstance(python, str) or not python.strip():
            raise SpecError(
                f"the project interpreter must be a nonblank path, not {python!r}",
                "invalid_input",
                "python",
            )
        return python
    return next((path for path in PROJECT_PYTHONS if (root / path).exists()), None)


def project_proposal(
    root: Path,
    package: Path,
    name: str,
    target_id: str = "module.project",
    python: str | None = None,
) -> dict:
    identifier(target_id)
    if not isinstance(name, str) or not name.strip():
        raise SpecError(
            f"initialization needs a nonblank project name, not {name!r}",
            "invalid_input",
            "name",
        )
    if checked_path(root, ".concorde/config.json").exists():
        raise SpecError(
            f"{root} already has .concorde/config.json, so it is initialized",
            "already_initialized",
            path=".concorde/config.json",
        )
    path = "specs/project/module.md"
    registry = initial_registry(target_id, name.strip(), path)
    entries = existing_files(root, {path, path + ".json"})
    installed = installed_files(root)
    config = {
        "profile_version": PROFILE_VERSION,
        "registry": ".concorde/specs.json",
        "protocol": installed_protocol_binding(root),
        "checks": [],
    }
    # The project's own interpreter, for its checks' {python}; Concorde runs in its own.
    interpreter = project_python(root, python)
    if interpreter is not None:
        config["python"] = interpreter
    files = [
        file_change(root, ".concorde/config.json", json.dumps(config, indent=2) + "\n"),
        file_change(
            root, ".concorde/specs.json", json.dumps(registry, indent=2) + "\n"
        ),
        file_change(
            root,
            path,
            initial_module_text(
                target_id, name.strip(), bool(entries), bool(installed)
            ),
        ),
        file_change(
            root,
            path + ".json",
            json.dumps(
                initial_module_metadata(
                    target_id, name.strip(), path, entries, installed
                ),
                indent=2,
            )
            + "\n",
        ),
    ]
    # Initialization creates only what the user's project generates through Concorde. Everything
    # that exists because Concorde is installed (the Protocol copy, the Framework runtime and the
    # main-session guidance) is the installer's output.
    return {
        "type_id": "concorde-project-proposal",
        "schema_version": PROPOSAL_VERSION,
        "action": "initialize",
        "base_digest": None,
        "source_digest": source_digest(root, {path, path + ".json"}),
        "files": files,
    }


def proposal_digest(proposal: dict) -> str:
    """The ``sha256:`` digest of the canonical JSON of a proposal typed value."""
    return digest(proposal)


def apply_project_proposal(root: Path, package: Path, proposal: dict) -> dict:
    if (
        set(proposal)
        != {
            "type_id",
            "schema_version",
            "action",
            "base_digest",
            "source_digest",
            "files",
        }
        or proposal["type_id"] != "concorde-project-proposal"
        or proposal["schema_version"] != PROPOSAL_VERSION
        or proposal["action"] not in {"initialize"}
    ):
        raise SpecError(
            "the project proposal's envelope is not a concorde-project-proposal of "
            f"schema_version {PROPOSAL_VERSION} with action initialize; its fields are "
            + (
                ", ".join(
                    f"{key}={proposal.get(key)!r}"
                    for key in ("type_id", "schema_version", "action")
                )
                if isinstance(proposal, dict)
                else f"a JSON {type(proposal).__name__}"
            ),
            "invalid_proposal",
            "/proposal",
        )
    files = proposal["files"]
    proposed = {item["path"]: item for item in files}
    if (
        ".concorde/config.json" not in proposed
        or ".concorde/specs.json" not in proposed
    ):
        raise SpecError(
            "the project proposal lacks "
            + " and ".join(
                path
                for path in (".concorde/config.json", ".concorde/specs.json")
                if path not in proposed
            )
            + f"; it proposes {', '.join(sorted(proposed))}",
            "invalid_proposal",
            "/proposal/files",
        )
    config = decode(proposed[".concorde/config.json"]["content"])
    registry = decode(proposed[".concorde/specs.json"]["content"])
    if config.get("registry") != ".concorde/specs.json" or config.get(
        "protocol"
    ) != installed_protocol_binding(root):
        raise SpecError(
            f"the proposed configuration names the registry {config.get('registry')!r} and "
            f"the Protocol {config.get('protocol')!r}, but initialization needs "
            "'.concorde/specs.json' and the installed Protocol copy "
            f"{installed_protocol_binding(root)!r}",
            "invalid_proposal",
            "/proposal/files",
            path=".concorde/config.json",
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
            f"the proposed registry is not a Protocol 14 registry: missing or malformed "
            f"{error}",
            "invalid_proposal",
            "/proposal/files",
            path=".concorde/specs.json",
        ) from error
    if proposal["base_digest"] is not None or any(
        item["before_digest"] is not None for item in files
    ):
        existing = [item["path"] for item in files if item["before_digest"] is not None]
        raise SpecError(
            "initialization would replace existing files: "
            + (", ".join(existing) or "the proposal has a base digest"),
            "invalid_proposal",
            "/proposal/files",
            reason="initialization only creates files; it never replaces one",
        )
    documents = allowed - {".concorde/config.json", ".concorde/specs.json"}
    if source_digest(root, documents) != proposal["source_digest"]:
        # The project's files changed since propose: it would now propose something else.
        raise SpecError(
            "the project's files changed since this proposal was made, so it would now "
            "propose something else",
            "stale_proposal",
            "/proposal/source_digest",
        )

    def verify():
        report = validate_repository(root, package_root=package)
        errors = [finding for finding in report.findings if finding.severity == "error"]
        if errors:
            raise SpecError(
                f"the initialized project would not validate: {len(errors)} error(s), each a "
                "cause; nothing was kept",
                "invalid_proposal",
                reason="initialization keeps only a project that validates",
                causes=[from_finding(item) for item in errors],
            )

    changed = apply_files(root, files, allowed, verify=verify)
    return {
        "action": proposal["action"],
        "status": "applied",
        "files": changed,
        "profile_version": PROFILE_VERSION,
        "protocol": installed_protocol_binding(root),
    }


def initialize(root: Path, package: Path, data: dict) -> dict:
    """Propose or apply the first Spec of a project; apply accepts only the exact proposal.

    ``data`` is ``{"action": "propose", "name": ..., "target_id"?: ..., "python"?: ...}`` or
    ``{"action": "apply", "proposal": ..., "proposal_digest": ...}``.
    """
    if data.get("action") == "apply":
        if not {"proposal", "proposal_digest"} <= set(data):
            raise SpecError(
                "apply requires the proposal and its proposal_digest",
                "invalid_input",
                "/proposal",
            )
        proposal = data["proposal"]
        # Apply accepts only the exact proposal propose returned, named by its digest.
        if proposal_digest(proposal) != data["proposal_digest"]:
            raise SpecError(
                "proposal_digest is not the digest of the given proposal",
                "invalid_proposal",
                "/proposal_digest",
            )
        value = apply_project_proposal(
            root,
            package,
            {
                "type_id": proposal["type_id"],
                "schema_version": proposal["schema_version"],
                **proposal["data"],
            },
        )
        return {
            "status": "applied",
            "proposal": None,
            "proposal_digest": None,
            "files": value["files"],
        }
    if data.get("action") != "propose" or "name" not in data:
        raise SpecError(
            f"initialization needs action propose with a name, or action apply; got action "
            f"{data.get('action')!r} with fields {sorted(data)}",
            "invalid_input",
        )
    value = project_proposal(
        root,
        package,
        data["name"],
        data.get("target_id", "module.project"),
        data.get("python"),
    )
    proposal = typed(
        "concorde-project-proposal",
        {
            key: value[key]
            for key in ("action", "base_digest", "source_digest", "files")
        },
    )
    return {
        "status": "proposed",
        "proposal": proposal,
        "proposal_digest": proposal_digest(proposal),
        "files": [item["path"] for item in value["files"]],
    }
