#!/usr/bin/env python3
"""Preview or apply one standalone Concorde package to a project."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NamedTuple, Sequence


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT / "src"))

from concorde.agent_assets import AgentAssetError, render_projection  # noqa: E402
from concorde.docsite_template import DocsiteTemplateError, template_files  # noqa: E402
from concorde.skill_assets import SkillAssetError, render_capabilities  # noqa: E402


FRAMEWORK_ROOT = ".concorde/framework"
RECEIPT_PATH = ".concorde/install.json"
INSTALL_SCHEMA = 1
PACKAGE_ROOTS = ["agent-assets", "docsite", "operations", "scripts", "skills", "src", "templates"]
SKILLS = [
    "concorde-analyze",
    "concorde-checklist",
    "concorde-clarify",
    "concorde-ask",
    "concorde-context",
    "concorde-deliver",
    "concorde-init",
    "concorde-validate",
    "concorde-constitution",
    "concorde-converge",
    "concorde-fast-loop",
    "concorde-implement",
    "concorde-plan-context",
    "concorde-plan-author",
    "concorde-specify",
    "concorde-tasks",
    "concorde-taskstoissues",
]
OPERATIONS = [
    "concorde-standard-dev-loop",
    "concorde-reflections-triage",
    "concorde-plan",
]


class InstallError(ValueError):
    """The requested package or target cannot be installed safely."""


class Package(NamedTuple):
    root: Path
    manifest: Mapping[str, Any]

    @property
    def version(self) -> str:
        return str(self.manifest["version"])


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _safe_relative(value: str, field: str) -> str:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "\\" in value:
        raise InstallError(f"{field} must be a safe project-relative path: {value!r}")
    return candidate.as_posix()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InstallError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise InstallError(f"{label} must be a JSON object: {path}")
    return value


def load_package(root: Path) -> Package:
    root = root.resolve()
    manifest_path = root / "concorde.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise InstallError(f"Concorde package manifest must be one real file: {manifest_path}")
    manifest = _read_json(manifest_path, "Concorde package manifest")
    required = {
        "schema_version",
        "name",
        "version",
        "architecture_profile",
        "workspace_protocol",
        "skills",
        "operations",
        "templates",
        "integrations",
        "install",
    }
    if required - set(manifest):
        raise InstallError(f"Concorde manifest is missing fields: {sorted(required - set(manifest))}")
    if manifest.get("schema_version") != 2 or manifest.get("name") != "concorde":
        raise InstallError("Concorde manifest must declare schema_version 2 and name 'concorde'")
    if manifest.get("architecture_profile") != 7 or manifest.get("workspace_protocol") != 13:
        raise InstallError("Concorde package must declare Architecture Profile 7 and Workspace Protocol 13")
    if manifest.get("delivery_proposal") != 9 or manifest.get("skill_namespace") != "concorde":
        raise InstallError("Concorde package must declare Delivery Proposal 9 and the concorde Skill namespace")
    install = manifest.get("install")
    if not isinstance(install, dict) or install.get("framework_root") != FRAMEWORK_ROOT or install.get("receipt") != RECEIPT_PATH:
        raise InstallError("Concorde manifest declares an unsupported installation layout")
    integrations = manifest.get("integrations")
    if integrations != ["claude", "codex"]:
        raise InstallError("Concorde manifest must declare exactly claude and codex integrations")
    if manifest.get("package_roots") != PACKAGE_ROOTS:
        raise InstallError("Concorde manifest declares an unsupported root package inventory")
    skills = manifest.get("skills")
    if not isinstance(skills, list) or any(not isinstance(item, str) for item in skills):
        raise InstallError("Concorde manifest Skills must be a string list")
    if skills != SKILLS or len(skills) != len(set(skills)):
        raise InstallError(f"Concorde manifest must declare exactly these 17 leaf Skills: {SKILLS}")
    operations = manifest.get("operations")
    if operations != OPERATIONS:
        raise InstallError(f"Concorde manifest must declare exactly these Operations: {OPERATIONS}")
    if set(skills) & set(operations):
        raise InstallError("Concorde Skill and Operation names must be globally unique")
    templates = manifest.get("templates")
    if not isinstance(templates, list) or any(not isinstance(item, str) for item in templates):
        raise InstallError("Concorde manifest templates must be a string list")
    if len(templates) != len(set(templates)):
        raise InstallError("Concorde manifest template inventory contains duplicates")
    observed_templates = sorted(path.name for path in (root / "templates").glob("*.md"))
    if observed_templates != sorted(templates):
        raise InstallError("Concorde manifest template inventory differs from root templates/")
    for required_root in PACKAGE_ROOTS:
        path = root / required_root
        if path.is_symlink() or not path.is_dir():
            raise InstallError(f"Concorde package root is missing: {required_root}")
    for legacy_root in ("commands", "examples"):
        if (root / legacy_root).exists() or (root / legacy_root).is_symlink():
            raise InstallError(f"Concorde package contains removed legacy root: {legacy_root}")
    try:
        render_capabilities(root, "codex", FRAMEWORK_ROOT)
    except SkillAssetError as error:
        raise InstallError(str(error)) from error
    license_path = root / "LICENSE"
    readme_path = root / "README.md"
    if manifest.get("license") != "MIT" or manifest.get("license_file") != "LICENSE" or license_path.is_symlink() or not license_path.is_file():
        raise InstallError("Concorde package must include its declared MIT LICENSE file")
    if readme_path.is_symlink() or not readme_path.is_file():
        raise InstallError("Concorde package must include one real root README.md")
    return Package(root, manifest)


def _package_files(package: Package) -> dict[str, bytes]:
    desired: dict[str, bytes] = {}
    desired[f"{FRAMEWORK_ROOT}/concorde.json"] = (package.root / "concorde.json").read_bytes()
    desired[f"{FRAMEWORK_ROOT}/LICENSE"] = (package.root / "LICENSE").read_bytes()
    desired[f"{FRAMEWORK_ROOT}/README.md"] = (package.root / "README.md").read_bytes()
    for directory in ("agent-assets", "operations", "skills", "src", "templates"):
        source_root = package.root / directory
        for path in sorted(source_root.rglob("*")):
            if path.is_symlink():
                raise InstallError(f"Concorde packages may not contain symlinks: {path}")
            if path.is_file():
                relative = path.relative_to(package.root).as_posix()
                if "__pycache__" in PurePosixPath(relative).parts or path.suffix in {".pyc", ".pyo"}:
                    continue
                desired[f"{FRAMEWORK_ROOT}/{relative}"] = path.read_bytes()
    try:
        for relative, content in template_files(package.root).items():
            desired[f"{FRAMEWORK_ROOT}/{relative}"] = content
    except DocsiteTemplateError as error:
        raise InstallError(str(error)) from error
    scripts = (
        "concorde.py",
        "concorde.ps1",
        "concorde.sh",
        "reflections_queue.py",
        "render-capability-surfaces.py",
        "workspace.py",
    )
    for name in scripts:
        source = package.root / "scripts" / name
        if source.is_symlink() or not source.is_file():
            raise InstallError(f"Concorde package script is missing: scripts/{name}")
        desired[f"{FRAMEWORK_ROOT}/scripts/{name}"] = source.read_bytes()
    return desired


def desired_outputs(package: Package, integration: str) -> dict[str, tuple[bytes, str]]:
    if integration not in package.manifest["integrations"]:
        raise InstallError(f"unsupported integration: {integration}")
    outputs = {path: (content, "framework") for path, content in _package_files(package).items()}
    try:
        capabilities = render_capabilities(package.root, integration, FRAMEWORK_ROOT)
        reflections = render_projection(package.root / "agent-assets/reflections", integration)
    except (SkillAssetError, AgentAssetError) as error:
        raise InstallError(str(error)) from error
    operations = set(package.manifest["operations"])
    for path, content in capabilities.items():
        name = PurePosixPath(path).parent.name
        role = "operation" if name in operations else "skill"
        outputs[path] = (content.encode("utf-8"), role)
    for path, content in reflections.items():
        if path in outputs:
            raise InstallError(f"agent output collision: {path}")
        outputs[path] = (content.encode("utf-8"), "agent")
    defaults = {
        ".concorde/reflections/config.json": (
            package.root / "agent-assets/reflections/config.default.json"
        ).read_bytes(),
        ".concorde/reflections/.gitignore": b"plans/\nworktrees/\n",
    }
    for path, content in defaults.items():
        outputs[path] = (content, "project-default")
    return dict(sorted(outputs.items()))


def _load_receipt(target: Path) -> dict[str, Any]:
    path = target / RECEIPT_PATH
    if not path.exists():
        return {"schema_version": INSTALL_SCHEMA, "outputs": []}
    if path.is_symlink() or not path.is_file():
        raise InstallError(f"Concorde installation receipt must be one real file: {path}")
    value = _read_json(path, "Concorde installation receipt")
    if value.get("schema_version") != INSTALL_SCHEMA or not isinstance(value.get("outputs"), list):
        raise InstallError(f"unsupported Concorde installation receipt: {path}")
    return value


def _prior_outputs(receipt: Mapping[str, Any]) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for item in receipt.get("outputs", []):
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
            raise InstallError("Concorde installation receipt contains an invalid output")
        relative = _safe_relative(item["path"], "receipt output")
        if relative in outputs:
            raise InstallError(f"Concorde installation receipt repeats output: {relative}")
        outputs[relative] = item["sha256"]
    return outputs


def _file_digest(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    return _sha256(path.read_bytes())


def installation_plan(
    target: Path,
    package: Package,
    integration: str,
) -> tuple[list[dict[str, str]], dict[str, tuple[bytes, str]], dict[str, Any]]:
    target = target.resolve()
    receipt = _load_receipt(target)
    prior = _prior_outputs(receipt)
    desired = desired_outputs(package, integration)
    actions: list[dict[str, str]] = []
    for relative, (content, role) in desired.items():
        path = target / relative
        expected = _sha256(content)
        observed = _file_digest(path)
        try:
            _check_parent(target, relative)
            unsafe = None
        except InstallError as error:
            unsafe = str(error)
        if unsafe is not None:
            action = "conflict"
        elif role == "project-default" and path.exists() and observed is not None:
            action = "preserve"
        elif not path.exists() and not path.is_symlink():
            action = "create"
        elif observed == expected:
            action = "unchanged" if prior.get(relative) == expected else "adopt"
        elif prior.get(relative) == observed and observed is not None:
            action = "update"
        else:
            action = "conflict"
        item = {"path": relative, "action": action, "role": role, "sha256": expected}
        if action == "conflict":
            item["reason"] = unsafe or "existing target is not the desired bytes or an unchanged owned output"
        actions.append(item)
    for relative, digest in sorted(prior.items()):
        if relative in desired:
            continue
        path = target / relative
        observed = _file_digest(path)
        try:
            _check_parent(target, relative)
            unsafe = None
        except InstallError as error:
            unsafe = str(error)
        if unsafe is not None:
            action = "conflict"
        elif not path.exists() and not path.is_symlink():
            action = "drop-missing"
        elif observed == digest:
            action = "remove"
        else:
            action = "conflict"
        item = {"path": relative, "action": action, "role": "superseded", "sha256": digest}
        if action == "conflict":
            item["reason"] = unsafe or "superseded owned output was modified and must be preserved"
        actions.append(item)
    return sorted(actions, key=lambda item: item["path"]), desired, receipt


def _check_target(target: Path) -> None:
    if target.exists() and (target.is_symlink() or not target.is_dir()):
        raise InstallError(f"target must be a real directory: {target}")
    target.mkdir(parents=True, exist_ok=True)


def _check_parent(target: Path, relative: str) -> Path:
    relative = _safe_relative(relative, "installation output")
    path = target / relative
    current = target
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise InstallError(f"installation path contains a symlink: {current.relative_to(target)}")
        if current.exists() and not current.is_dir():
            raise InstallError(f"installation parent is not a directory: {current.relative_to(target)}")
    return path


def _receipt(package: Package, integration: str, desired: Mapping[str, tuple[bytes, str]]) -> bytes:
    value = {
        "schema_version": INSTALL_SCHEMA,
        "concorde_version": package.version,
        "integration": integration,
        "architecture_profile": package.manifest["architecture_profile"],
        "workspace_protocol": package.manifest["workspace_protocol"],
        "outputs": [
            {"path": path, "role": role, "sha256": _sha256(content)}
            for path, (content, role) in sorted(desired.items())
            if role != "project-default"
        ],
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def apply_plan(
    target: Path,
    package: Package,
    integration: str,
    actions: Sequence[Mapping[str, str]],
    desired: Mapping[str, tuple[bytes, str]],
) -> str:
    conflicts = [item for item in actions if item["action"] == "conflict"]
    if conflicts:
        raise InstallError("installation plan has ownership conflicts")
    mutable = [item for item in actions if item["action"] in {"create", "update", "remove"}]
    receipt_content = _receipt(package, integration, desired)
    receipt_path = target / RECEIPT_PATH
    previous_receipt = receipt_path.read_bytes() if receipt_path.is_file() and not receipt_path.is_symlink() else None
    previous_receipt_mode = receipt_path.stat().st_mode & 0o777 if previous_receipt is not None else None
    backups: dict[str, tuple[bytes, int]] = {}
    created: list[str] = []
    created_directories: set[Path] = set()
    staged_files: set[Path] = set()
    try:
        for item in mutable:
            relative = item["path"]
            path = _check_parent(target, relative)
            action = item["action"]
            if action in {"update", "remove"}:
                backups[relative] = (path.read_bytes(), path.stat().st_mode & 0o777)
            if action == "remove":
                path.unlink()
                continue
            content = desired[relative][0]
            current = path.parent
            missing: list[Path] = []
            while current != target and not current.exists():
                missing.append(current)
                current = current.parent
            path.parent.mkdir(parents=True, exist_ok=True)
            created_directories.update(missing)
            if action == "create":
                created.append(relative)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".concorde-install-", delete=False) as handle:
                staged = Path(handle.name)
                staged_files.add(staged)
                handle.write(content)
            staged.replace(path)
            staged_files.discard(staged)
            if relative.startswith(f"{FRAMEWORK_ROOT}/scripts/") and path.suffix in {".py", ".sh"}:
                path.chmod(0o755)
            else:
                path.chmod(0o644)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=receipt_path.parent, prefix=".concorde-receipt-", delete=False) as handle:
            staged_receipt = Path(handle.name)
            staged_files.add(staged_receipt)
            handle.write(receipt_content)
        staged_receipt.replace(receipt_path)
        staged_files.discard(staged_receipt)
        receipt_path.chmod(0o644)
    except Exception:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
        for relative in reversed(created):
            path = target / relative
            if path.exists() and not path.is_symlink() and path.is_file():
                path.unlink()
        for relative, (content, mode) in backups.items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(mode)
        if previous_receipt is None:
            receipt_path.unlink(missing_ok=True)
        else:
            receipt_path.write_bytes(previous_receipt)
            if previous_receipt_mode is not None:
                receipt_path.chmod(previous_receipt_mode)
        for directory in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return "unchanged" if not mutable and previous_receipt == receipt_content else "installed"


def _print_plan(package: Package, integration: str, actions: Sequence[Mapping[str, str]], status: str) -> None:
    counts: dict[str, int] = {}
    for item in actions:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    print("Concorde installation plan")
    print(f"  version: {package.version}")
    print(f"  integration: {integration}")
    print(f"  status: {status}")
    print("  actions: " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
    for item in actions:
        if item["action"] == "conflict":
            print(f"  conflict: {item['path']} — {item['reason']}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-concorde")
    parser.add_argument("--target", required=True)
    parser.add_argument("--integration", choices=["codex", "claude"], default="codex")
    parser.add_argument("--checkout", default=str(SCRIPT_ROOT))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--preview", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = create_parser().parse_args(argv)
    try:
        requested_target = Path(arguments.target).absolute()
        if requested_target.is_symlink():
            raise InstallError(f"target must not be a symlink: {requested_target}")
        target = requested_target.resolve()
        _check_target(target)
        package = load_package(Path(arguments.checkout))
        actions, desired, _ = installation_plan(target, package, arguments.integration)
        conflicts = [item for item in actions if item["action"] == "conflict"]
        status = "conflict" if conflicts else "preview"
        if arguments.apply and not conflicts:
            status = apply_plan(target, package, arguments.integration, actions, desired)
        result = {
            "schema_version": INSTALL_SCHEMA,
            "status": status,
            "version": package.version,
            "integration": arguments.integration,
            "target": str(target),
            "receipt": RECEIPT_PATH,
            "actions": actions,
        }
        if arguments.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            _print_plan(package, arguments.integration, actions, status)
            if not arguments.apply and not conflicts:
                print("  next: rerun with --apply to accept this exact ownership plan")
        return 2 if conflicts else 0
    except (InstallError, OSError, UnicodeError) as error:
        if arguments.format == "json":
            print(json.dumps({"schema_version": INSTALL_SCHEMA, "status": "failed", "error": str(error)}, sort_keys=True))
        else:
            print(f"CONCORDE INSTALL FAILED: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
