#!/usr/bin/env python3
"""Review-first development installation of Concorde into its own checkout.

This bootstrap deliberately lives outside the Concorde extension: first installation
must work before any Concorde command is available.  Mutation is delegated to the
public Specify CLI component lifecycle; this file owns only review, verification,
scoped recovery, and machine-local evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


TARGET = "feature.concorde.self-host-framework"
PROPOSAL_PATH = ".specify/self-hosting-proposal.json"
RECEIPT_PATH = ".specify/self-hosting.json"
SUPPORTED_SPECKIT = "0.16.4"
PRESET_ID = "concorde-core"
EXTENSION_ID = "concorde"
BUNDLE_ID = "concorde-bundle"
PRIORITY = 10

PRESET_COMMANDS = (
    "speckit.specify",
    "speckit.clarify",
    "speckit.checklist",
    "speckit.plan",
    "speckit.tasks",
    "speckit.implement",
    "speckit.analyze",
    "speckit.converge",
    "speckit.taskstoissues",
)
EXTENSION_COMMANDS = (
    "speckit.concorde.init",
    "speckit.concorde.feature-harden",
    "speckit.concorde.context",
    "speckit.concorde.validate",
    "speckit.concorde.ask",
)
TEMPLATE_SURFACES = (
    ".specify/templates/spec-template.md",
    ".specify/templates/plan-template.md",
    ".specify/templates/tasks-template.md",
)
PRESERVED = (
    "project-authored .concorde configuration",
    "specifications, designs, contracts, diagrams, and temporal implementation work",
    "documentation, source code, tests, and generated evidence",
    "unrelated integration and agent assets",
    "authoritative preset, extension, and bundle sources",
)
FAILURE_ENV = "CONCORDE_SELF_HOST_FAIL_STAGE"


class SelfHostError(RuntimeError):
    def __init__(self, code: str, stage: str, path: str, message: str, remediation: str):
        super().__init__(message)
        self.finding = finding(code, "error", stage, path, message, remediation)


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def finding(
    code: str,
    severity: str,
    stage: str,
    path: str,
    message: str,
    remediation: str,
    *,
    expected: object | None = None,
    observed: object | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "code": code,
        "severity": severity,
        "stage": stage,
        "path": path,
        "message": message,
        "remediation": remediation,
    }
    if expected is not None:
        result["expected"] = expected
    if observed is not None:
        result["observed"] = observed
    return result


def safe_relative(value: str) -> Path:
    if not value or "\\" in value or value.endswith("/"):
        raise ValueError(f"unsafe project-relative path: {value!r}")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe project-relative path: {value!r}")
    return candidate


def resolve_project_path(root: Path, value: str, *, reject_symlink: bool = True) -> Path:
    relative = safe_relative(value)
    root = root.resolve()
    candidate = root / relative
    current = root
    for part in relative.parts:
        current = current / part
        if reject_symlink and current.is_symlink():
            raise ValueError(f"symlink traversal is not allowed: {value}")
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError(f"path escapes project root: {value}")
    return candidate


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(canonical_json(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def source_files(root: Path, relative: str) -> list[Path]:
    directory = resolve_project_path(root, relative)
    if not directory.is_dir():
        raise SelfHostError(
            "CONCORDE-SELF-HOST-001",
            "source",
            relative,
            "Required framework source directory is missing.",
            "Restore the maintained Concorde component source and retry.",
        )
    files: list[Path] = []
    for path in sorted(directory.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise SelfHostError(
                "CONCORDE-SELF-HOST-002",
                "source",
                rel,
                "Framework sources may not contain symlinks.",
                "Replace the symlink with a checked-in regular file or directory.",
            )
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            files.append(path)
    return files


def inventory_digest(root: Path, groups: Iterable[tuple[str, Iterable[Path]]]) -> str:
    digest = hashlib.sha256()
    for group, paths in sorted((name, list(items)) for name, items in groups):
        for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix()
            digest.update(group.encode() + b"\0")
            digest.update(relative.encode() + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def tree_digest(root: Path, entries: Iterable[tuple[str, Path]]) -> str | None:
    groups: list[tuple[str, list[Path]]] = []
    for label, path in entries:
        if not path.exists() or path.is_symlink():
            return None
        files = [item for item in sorted(path.rglob("*")) if item.is_file() and "__pycache__" not in item.parts and item.suffix not in {".pyc", ".pyo"}]
        groups.append((label, files))
    return inventory_digest(root, groups)


def component_content_digest(preset_root: Path, extension_root: Path) -> str | None:
    digest = hashlib.sha256()
    for label, directory in (("preset", preset_root), ("extension", extension_root)):
        if not directory.is_dir() or directory.is_symlink():
            return None
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                return None
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if ".specify-dev" in path.parts:
                # Spec Kit's dev-install cache (per-integration rendered commands) is host metadata, not component content.
                continue
            digest.update(label.encode() + b"\0")
            digest.update(path.relative_to(directory).as_posix().encode() + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def yaml_scalar(path: Path, section: str, key: str) -> str:
    in_section = False
    section_indent = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if stripped == f"{section}:":
            in_section = True
            section_indent = indent
            continue
        if in_section and indent <= section_indent:
            in_section = False
        if in_section:
            match = re.match(rf"{re.escape(key)}:\s*[\"']?([^\"'#]+?)[\"']?\s*$", stripped)
            if match:
                return match.group(1).strip()
    raise SelfHostError(
        "CONCORDE-SELF-HOST-003",
        "source",
        path.as_posix(),
        f"Manifest does not declare {section}.{key}.",
        "Correct the maintained component manifest.",
    )


def integration_state(root: Path) -> tuple[str, str]:
    path = resolve_project_path(root, ".specify/integration.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        integration = data["integration"]
        version = data["version"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-004",
            "source",
            ".specify/integration.json",
            f"Active Spec Kit integration metadata is invalid: {error}",
            "Initialize the checkout with a supported Spec Kit integration.",
        ) from error
    if integration != "codex":
        raise SelfHostError(
            "CONCORDE-SELF-HOST-005",
            "source",
            ".specify/integration.json",
            f"Integration {integration!r} has no self-hosting surface evidence in protocol v1.",
            "Use the validated Codex integration or add isolated evidence before extending support.",
        )
    if version != SUPPORTED_SPECKIT:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-006",
            "source",
            ".specify/integration.json",
            f"Spec Kit {version!r} is outside the supported >=0.16.4,<0.16.5 range.",
            "Use Spec Kit 0.16.4 or update compatibility evidence and manifests.",
        )
    return integration, version


def component_model(root: Path) -> tuple[list[dict[str, object]], str, str]:
    integration, _ = integration_state(root)
    manifests = {
        "preset": resolve_project_path(root, "presets/concorde-core/preset.yml"),
        "extension": resolve_project_path(root, "extensions/concorde/extension.yml"),
        "bundle": resolve_project_path(root, "bundles/concorde-bundle/bundle.yml"),
    }
    expected = {
        "preset": (PRESET_ID, "preset"),
        "extension": (EXTENSION_ID, "extension"),
        "bundle": (BUNDLE_ID, "bundle"),
    }
    components: list[dict[str, object]] = []
    for kind in ("preset", "extension", "bundle"):
        identity = yaml_scalar(manifests[kind], kind, "id")
        version = yaml_scalar(manifests[kind], kind, "version")
        if identity != expected[kind][0]:
            raise SelfHostError(
                "CONCORDE-SELF-HOST-007",
                "source",
                manifests[kind].relative_to(root).as_posix(),
                f"Expected {kind} identity {expected[kind][0]!r}, observed {identity!r}.",
                "Restore the supported Concorde component identities.",
            )
        item: dict[str, object] = {
            "id": identity,
            "kind": kind,
            "version": version,
            "source": manifests[kind].parent.relative_to(root).as_posix(),
        }
        if kind in {"preset", "extension"}:
            item["priority"] = PRIORITY
        components.append(item)
    versions = {str(item["version"]) for item in components}
    bundle_text = manifests["bundle"].read_text(encoding="utf-8")
    if len(versions) != 1 or PRESET_ID not in bundle_text or EXTENSION_ID not in bundle_text:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-008",
            "source",
            "bundles/concorde-bundle/bundle.yml",
            "Bundle composition does not pin the same local preset and extension versions.",
            "Align the bundle recipe with the maintained preset and extension manifests.",
        )
    groups = [
        ("preset", source_files(root, "presets/concorde-core")),
        ("extension", source_files(root, "extensions/concorde")),
        ("bundle", source_files(root, "bundles/concorde-bundle")),
    ]
    return components, inventory_digest(root, groups), integration


def skill_path(command: str) -> str:
    return f".agents/skills/{command.replace('.', '-')}/SKILL.md"


def owned_paths() -> tuple[str, ...]:
    skill_directories = [str(Path(skill_path(command)).parent.as_posix()) for command in PRESET_COMMANDS + EXTENSION_COMMANDS]
    return tuple(sorted({
        ".specify/presets/concorde-core",
        ".specify/extensions/concorde",
        ".specify/presets/.registry",
        ".specify/extensions/.registry",
        ".specify/extensions.yml",
        *TEMPLATE_SURFACES,
        *skill_directories,
        RECEIPT_PATH,
    }))


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def registry_entries(root: Path) -> dict[str, object] | None:
    preset = read_json(root / ".specify/presets/.registry")
    extension = read_json(root / ".specify/extensions/.registry")
    if preset is None or extension is None:
        return None
    preset_entry = preset.get("presets", {}).get(PRESET_ID) if isinstance(preset.get("presets"), dict) else None
    extension_entry = extension.get("extensions", {}).get(EXTENSION_ID) if isinstance(extension.get("extensions"), dict) else None
    if not isinstance(preset_entry, dict) or not isinstance(extension_entry, dict):
        return None
    return {"preset": preset_entry, "extension": extension_entry}


def extension_command_collisions(root: Path) -> list[tuple[str, str]]:
    registry = read_json(root / ".specify/extensions/.registry")
    if registry is None or not isinstance(registry.get("extensions"), dict):
        return []
    expected = set(EXTENSION_COMMANDS)
    collisions: list[tuple[str, str]] = []
    for component_id, entry in registry["extensions"].items():
        if component_id == EXTENSION_ID or not isinstance(entry, dict):
            continue
        commands = entry.get("registered_commands", {})
        if not isinstance(commands, dict):
            continue
        for command in commands.get("codex", []):
            if command in expected:
                collisions.append((str(component_id), str(command)))
    return sorted(collisions)


def change_action(root: Path, relative: str, registered: bool) -> str:
    path = resolve_project_path(root, relative, reject_symlink=False)
    if not path.exists() and not path.is_symlink():
        return "create"
    return "update" if registered else "adopt"


def build_proposal(root: Path) -> dict[str, object]:
    components, source_digest, integration = component_model(root)
    collisions = extension_command_collisions(root)
    if collisions:
        owner, command = collisions[0]
        raise SelfHostError(
            "CONCORDE-SELF-HOST-022",
            "proposal",
            ".specify/extensions/.registry",
            f"Extension command {command!r} is already registered by {owner!r}.",
            "Resolve extension command ownership explicitly before generating a new proposal.",
        )
    registered = registry_entries(root) is not None
    changes = [
        {
            "path": relative,
            "action": change_action(root, relative, registered),
            "meaning": "Concorde-owned Spec Kit development materialization or provenance evidence",
        }
        for relative in owned_paths()
    ]
    return {
        "proposal_version": 1,
        "operation": "self-host.apply",
        "target": TARGET,
        "status": "eligible",
        "source_digest": source_digest,
        "integration": integration,
        "components": components,
        "changes": changes,
        "preserved": list(PRESERVED),
        "activation": "reload_required",
        "proposal_path": PROPOSAL_PATH,
        "findings": [],
    }


def propose(root: Path) -> dict[str, object]:
    try:
        proposal = build_proposal(root)
    except SelfHostError as error:
        proposal = {
            "proposal_version": 1,
            "operation": "self-host.apply",
            "target": TARGET,
            "status": "invalid",
            "source_digest": digest_bytes(b"invalid"),
            "integration": "unknown",
            "components": [],
            "changes": [],
            "preserved": list(PRESERVED),
            "activation": "reload_required",
            "proposal_path": PROPOSAL_PATH,
            "findings": [error.finding],
        }
    atomic_json(resolve_project_path(root, PROPOSAL_PATH), proposal)
    return proposal


def run_specify(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    environment["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        ["specify", *arguments],
        cwd=root,
        text=True,
        capture_output=True,
        env=environment,
    )
    if completed.returncode:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-009",
            "apply",
            ".specify",
            f"Specify lifecycle command failed: {' '.join(arguments)}: {(completed.stderr or completed.stdout).strip()}",
            "Resolve the reported Spec Kit compatibility or ownership problem and generate a new proposal.",
        )
    return completed


def inject(stage: str) -> None:
    active = {item.strip() for item in os.environ.get(FAILURE_ENV, "").split(",") if item.strip()}
    if stage in active:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-010",
            "apply",
            ".specify",
            f"Injected self-hosting failure at {stage}.",
            "Remove the test-only failure injection and retry from a new proposal.",
        )


def preflight(root: Path, integration: str) -> None:
    active = {item.strip() for item in os.environ.get(FAILURE_ENV, "").split(",") if item.strip()}
    if "preflight" in active:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-010",
            "preflight",
            ".specify",
            "Injected self-hosting failure during isolated preflight.",
            "Remove the test-only failure injection and retry from a new proposal.",
        )
    with tempfile.TemporaryDirectory(prefix="concorde-self-host-") as temporary:
        target = Path(temporary)
        run_specify(target, ["init", "--here", "--force", "--ignore-agent-tools", "--integration", integration, "--integration-options=--skills", "--script", "sh"])
        run_specify(target, ["preset", "add", "--dev", str(root / "presets/concorde-core"), "--priority", str(PRIORITY)])
        run_specify(target, ["extension", "add", str(root / "extensions/concorde"), "--dev", "--priority", str(PRIORITY)])
        verify_materialization(target, expected_source=root)


def copy_source_digest(root: Path, expected_source: Path | None = None) -> str | None:
    base = expected_source or root
    installed = installed_component_digest(root)
    if installed is None:
        return None
    source_files(base, "presets/concorde-core")
    source_files(base, "extensions/concorde")
    source = component_content_digest(
        base / "presets/concorde-core",
        base / "extensions/concorde",
    )
    return installed if installed == source else None


def installed_component_digest(root: Path) -> str | None:
    return component_content_digest(
        root / ".specify/presets/concorde-core",
        root / ".specify/extensions/concorde",
    )


def normalized_registry(root: Path) -> dict[str, object] | None:
    entries = registry_entries(root)
    if entries is None:
        return None
    preset = entries["preset"]
    extension = entries["extension"]
    assert isinstance(preset, dict) and isinstance(extension, dict)
    normalized = {
        "preset": {
            "version": preset.get("version"),
            "source": preset.get("source"),
            "enabled": preset.get("enabled"),
            "priority": preset.get("priority"),
            "commands": preset.get("registered_commands", {}).get("codex", []),
            "skills": preset.get("registered_skills", {}).get("codex", []),
        },
        "extension": {
            "version": extension.get("version"),
            "source": extension.get("source"),
            "enabled": extension.get("enabled"),
            "priority": extension.get("priority"),
            "commands": extension.get("registered_commands", {}).get("codex", []),
        },
    }
    return normalized


def expected_registry(components: list[dict[str, object]]) -> dict[str, object]:
    versions = {str(item["kind"]): str(item["version"]) for item in components}
    return {
        "preset": {
            "version": versions["preset"],
            "source": "local",
            "enabled": True,
            "priority": PRIORITY,
            "commands": list(PRESET_COMMANDS),
            "skills": [command.replace(".", "-") for command in PRESET_COMMANDS],
        },
        "extension": {
            "version": versions["extension"],
            "source": "local",
            "enabled": True,
            "priority": PRIORITY,
            "commands": list(EXTENSION_COMMANDS),
        },
    }


def surface_inventory(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    surfaces: list[dict[str, str]] = []
    missing: list[str] = []
    for relative in sorted((*TEMPLATE_SURFACES, *(skill_path(command) for command in PRESET_COMMANDS + EXTENSION_COMMANDS))):
        path = resolve_project_path(root, relative, reject_symlink=False)
        if not path.is_file() or path.is_symlink():
            missing.append(relative)
        else:
            surfaces.append({"path": relative, "digest": digest_bytes(path.read_bytes())})
    return surfaces, missing


def extra_owned_surfaces(root: Path) -> list[str]:
    directory = root / ".agents/skills"
    expected = {Path(skill_path(command)).parent.name for command in PRESET_COMMANDS + EXTENSION_COMMANDS}
    if not directory.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in directory.glob("speckit-concorde-*/SKILL.md")
        if path.parent.name not in expected
    )


def verify_materialization(root: Path, expected_source: Path | None = None) -> tuple[str, str, str, list[dict[str, str]]]:
    components, _, _ = component_model(expected_source or root)
    installed = copy_source_digest(root, expected_source)
    if installed is None:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-011",
            "verify",
            ".specify",
            "Installed preset or extension bytes do not match authoritative sources.",
            "Restore the prior scoped state and retry from a fresh proposal.",
        )
    registry = normalized_registry(root)
    expected = expected_registry(components)
    if registry != expected:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-012",
            "verify",
            ".specify",
            "Spec Kit registry entries do not match the accepted local composition.",
            "Inspect component ownership and retry after resolving collisions.",
        )
    surfaces, missing = surface_inventory(root)
    if missing:
        raise SelfHostError(
            "CONCORDE-SELF-HOST-013",
            "verify",
            missing[0],
            f"Expected materialized surfaces are missing: {', '.join(missing)}",
            "Re-run the public Spec Kit materialization after resolving integration errors.",
        )
    installed_digest = installed
    registry_digest = digest_bytes(canonical_json(registry).encode())
    surface_digest = digest_bytes(canonical_json(surfaces).encode())
    return installed_digest, registry_digest, surface_digest, surfaces


def snapshot(root: Path, paths: Iterable[str], backup: Path) -> dict[str, bool]:
    state: dict[str, bool] = {}
    for relative in sorted(set(paths)):
        source = resolve_project_path(root, relative, reject_symlink=False)
        state[relative] = source.exists() or source.is_symlink()
        if not state[relative]:
            continue
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir() and not source.is_symlink():
            shutil.copytree(source, destination, symlinks=True)
        elif source.is_symlink():
            destination.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, destination)
    return state


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def restore(root: Path, paths: Iterable[str], backup: Path, state: dict[str, bool]) -> list[str]:
    residual: list[str] = []
    active = {item.strip() for item in os.environ.get(FAILURE_ENV, "").split(",") if item.strip()}
    if "rollback" in active:
        return [sorted(state)[0]]
    for relative in reversed(sorted(set(paths))):
        target = resolve_project_path(root, relative, reject_symlink=False)
        try:
            remove_path(target)
            if state.get(relative):
                source = backup / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir() and not source.is_symlink():
                    shutil.copytree(source, target, symlinks=True)
                elif source.is_symlink():
                    target.symlink_to(os.readlink(source))
                else:
                    shutil.copy2(source, target)
        except OSError:
            residual.append(relative)
    return sorted(residual)


def current_receipt(root: Path) -> dict[str, Any] | None:
    return read_json(root / RECEIPT_PATH)


def refresh_components(root: Path) -> None:
    entries = registry_entries(root)
    if entries is not None:
        run_specify(root, ["preset", "remove", PRESET_ID])
    inject("preset")
    run_specify(root, ["preset", "add", "--dev", str(root / "presets/concorde-core"), "--priority", str(PRIORITY)])
    inject("extension")
    arguments = ["extension", "add", str(root / "extensions/concorde"), "--dev", "--priority", str(PRIORITY), "--force"]
    run_specify(root, arguments)


def status(root: Path) -> dict[str, object]:
    try:
        components, source_digest, integration = component_model(root)
    except SelfHostError as error:
        return {
            "schema_version": 1,
            "operation": "self-host.status",
            "target": TARGET,
            "status": "unknown",
            "source_digest": digest_bytes(b"invalid"),
            "integration": "unknown",
            "dimensions": {name: {"status": "unknown", "message": "Source or host metadata is invalid."} for name in ("source", "installed", "registry", "surfaces", "activation")},
            "findings": [error.finding],
        }
    receipt = current_receipt(root)
    if receipt is None:
        return {
            "schema_version": 1,
            "operation": "self-host.status",
            "target": TARGET,
            "status": "absent",
            "source_digest": source_digest,
            "integration": integration,
            "dimensions": {
                "source": {"status": "unknown", "message": "No self-hosting receipt exists."},
                "installed": {"status": "unknown", "message": "Installed copies are not bound to an accepted receipt."},
                "registry": {"status": "unknown", "message": "Registrations are not bound to an accepted receipt."},
                "surfaces": {"status": "unknown", "message": "Agent surfaces are not bound to an accepted receipt."},
                "activation": {"status": "unknown", "message": "No activation evidence exists."},
            },
            "findings": [],
        }
    findings: list[dict[str, object]] = []
    source_ok = receipt.get("source_digest") == source_digest
    installed_digest = installed_component_digest(root)
    installed_ok = copy_source_digest(root) is not None and installed_digest == receipt.get("installed_digest")
    registry = normalized_registry(root)
    registry_digest = digest_bytes(canonical_json(registry).encode()) if registry is not None else None
    registry_ok = registry == expected_registry(components) and registry_digest == receipt.get("registry_digest")
    surfaces, missing = surface_inventory(root)
    extras = extra_owned_surfaces(root)
    surface_digest = digest_bytes(canonical_json(surfaces).encode())
    surface_ok = not missing and not extras and surface_digest == receipt.get("surface_digest")
    for ok, code, stage, path, message in (
        (source_ok, "CONCORDE-SELF-HOST-014", "source", "presets/concorde-core", "Authoritative framework sources changed after the accepted receipt."),
        (installed_ok, "CONCORDE-SELF-HOST-015", "verify", ".specify", "Installed component copies differ from authoritative sources or receipt."),
        (registry_ok, "CONCORDE-SELF-HOST-016", "verify", ".specify", "Concorde component registrations differ from the accepted receipt."),
        (surface_ok, "CONCORDE-SELF-HOST-017", "verify", ".agents/skills", "Declared agent/template surfaces are missing, altered, or include unexpected Concorde-owned entries."),
    ):
        if not ok:
            findings.append(finding(code, "error", stage, path, message, "Generate and review a fresh proposal, then refresh the self-hosted installation."))
    dimensions = {
        "source": {"status": "matching" if source_ok else "changed", "message": "Authoritative source digest compared with receipt."},
        "installed": {"status": "matching" if installed_ok else ("missing" if installed_digest is None else "drift"), "message": "Installed component bytes compared with source and receipt."},
        "registry": {"status": "matching" if registry_ok else ("missing" if registry is None else "drift"), "message": "Normalized Spec Kit registrations compared with expected ownership."},
        "surfaces": {"status": "matching" if surface_ok else ("extra_owned" if extras else ("missing" if missing else "drift")), "message": "Declared active-integration surfaces compared with receipt."},
        "activation": {"status": "reload_required", "message": "On-disk equality does not prove that the running agent reloaded these instructions."},
    }
    return {
        "schema_version": 1,
        "operation": "self-host.status",
        "target": TARGET,
        "status": "current" if all((source_ok, installed_ok, registry_ok, surface_ok)) else "drift",
        "source_digest": source_digest,
        "integration": integration,
        "dimensions": dimensions,
        "findings": findings,
    }


def invalid_result(root: Path, error: SelfHostError, source_digest: str | None = None, integration: str = "unknown") -> dict[str, object]:
    return {
        "schema_version": 1,
        "operation": "self-host.apply",
        "target": TARGET,
        "status": "invalid",
        "source_digest": source_digest or digest_bytes(b"invalid"),
        "integration": integration,
        "activation": "unknown",
        "changes": [],
        "receipt_path": RECEIPT_PATH,
        "findings": [error.finding],
    }


def failed_result(error: SelfHostError, status_value: str = "failed") -> dict[str, object]:
    return {
        "schema_version": 1,
        "operation": "self-host.apply",
        "target": TARGET,
        "status": status_value,
        "source_digest": digest_bytes(b"unapplied"),
        "integration": "unknown",
        "activation": "unknown",
        "changes": [],
        "receipt_path": RECEIPT_PATH,
        "findings": [error.finding],
    }


def apply(root: Path, proposal_argument: str) -> dict[str, object]:
    try:
        if proposal_argument != PROPOSAL_PATH:
            raise SelfHostError(
                "CONCORDE-SELF-HOST-018",
                "proposal",
                proposal_argument or ".specify",
                "Apply accepts only the canonical self-hosting proposal path.",
                f"Review and pass {PROPOSAL_PATH} exactly.",
            )
        proposal_path = resolve_project_path(root, proposal_argument)
        reviewed = read_json(proposal_path)
        fresh = build_proposal(root)
        if reviewed is None or canonical_json(reviewed) != canonical_json(fresh):
            raise SelfHostError(
                "CONCORDE-SELF-HOST-019",
                "proposal",
                PROPOSAL_PATH,
                "The reviewed proposal is malformed or stale relative to current source and owned state.",
                "Run propose again and explicitly review the complete replacement proposal.",
            )
        if reviewed.get("status") != "eligible":
            raise SelfHostError(
                "CONCORDE-SELF-HOST-020",
                "proposal",
                PROPOSAL_PATH,
                "Only an eligible reviewed proposal may be applied.",
                "Resolve proposal findings and generate a new proposal.",
            )
        prior_status = status(root)
        if prior_status["status"] == "current" and current_receipt(root) is not None:
            return {
                "schema_version": 1,
                "operation": "self-host.apply",
                "target": TARGET,
                "status": "unchanged",
                "source_digest": fresh["source_digest"],
                "integration": fresh["integration"],
                "activation": "reload_required",
                "changes": [],
                "receipt_path": RECEIPT_PATH,
                "findings": [],
            }
        preflight(root, str(fresh["integration"]))
    except SelfHostError as error:
        if error.finding["stage"] in {"preflight", "apply", "verify"}:
            return failed_result(error)
        return invalid_result(root, error)

    paths = owned_paths()
    with tempfile.TemporaryDirectory(prefix="concorde-self-host-backup-") as temporary:
        backup = Path(temporary)
        state = snapshot(root, paths, backup)
        try:
            refresh_components(root)
            inject("verify")
            installed_digest, registry_digest, surface_digest, surfaces = verify_materialization(root)
            receipt = {
                "receipt_version": 1,
                "target": TARGET,
                "source_digest": fresh["source_digest"],
                "installed_digest": installed_digest,
                "registry_digest": registry_digest,
                "surface_digest": surface_digest,
                "integration": fresh["integration"],
                "components": fresh["components"],
                "surfaces": surfaces,
                "activation": "reload_required",
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }
            atomic_json(root / RECEIPT_PATH, receipt)
            return {
                "schema_version": 1,
                "operation": "self-host.apply",
                "target": TARGET,
                "status": "applied",
                "source_digest": fresh["source_digest"],
                "integration": fresh["integration"],
                "activation": "reload_required",
                "changes": fresh["changes"],
                "receipt_path": RECEIPT_PATH,
                "installed_digest": installed_digest,
                "registry_digest": registry_digest,
                "surface_digest": surface_digest,
                "findings": [],
            }
        except SelfHostError as error:
            residual = restore(root, paths, backup, state)
            findings = [error.finding]
            for relative in residual:
                findings.append(finding(
                    "CONCORDE-SELF-HOST-021",
                    "error",
                    "rollback",
                    relative,
                    "Scoped rollback could not restore this path exactly.",
                    "Restore the named path from version control or the prior component installation before retrying.",
                ))
            return {
                "schema_version": 1,
                "operation": "self-host.apply",
                "target": TARGET,
                "status": "failed" if residual else "rolled_back",
                "source_digest": fresh["source_digest"],
                "integration": fresh["integration"],
                "activation": "unknown",
                "changes": fresh["changes"],
                "receipt_path": RECEIPT_PATH,
                "findings": findings,
            }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="self-host-concorde")
    parser.add_argument("--project-root", default=".")
    commands = parser.add_subparsers(dest="operation", required=True)
    propose_parser = commands.add_parser("propose")
    propose_parser.add_argument("--format", choices=["json"], default="json")
    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("--proposal", required=True)
    apply_parser.add_argument("--format", choices=["json"], default="json")
    status_parser = commands.add_parser("status")
    status_parser.add_argument("--format", choices=["json"], default="json")
    status_parser.add_argument("--require-current", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = create_parser().parse_args(argv)
    root = Path(arguments.project_root).resolve()
    if arguments.operation == "propose":
        result = propose(root)
        code = 0 if result["status"] == "eligible" else 2
    elif arguments.operation == "apply":
        result = apply(root, arguments.proposal)
        code = 0 if result["status"] in {"applied", "unchanged"} else 2
    else:
        result = status(root)
        code = 0 if not arguments.require_current or result["status"] == "current" else 2
    sys.stdout.write(canonical_json(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
