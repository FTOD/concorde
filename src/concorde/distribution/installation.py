"""Supported receipt-owned installation service and its CLI boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

SCRIPT_ROOT = Path(__file__).resolve().parents[3]

from concorde.distribution import build as concorde_build
from concorde.distribution import protocol_guidance as guidance
from concorde.distribution.managed_runtime import (
    ManagedRuntimeError,
    load_runtime_spec,
    plan_runtime,
    provision_runtime,
)
from concorde.distribution.project_defaults import project_default_files
from concorde.views.docsite_template import (
    DocsiteTemplateError,
    template_files,
)

from ..harness.timing import timed

FRAMEWORK_ROOT = ".concorde/framework"
PROTOCOL_ROOT = ".concorde/protocol"
RECEIPT_PATH = ".concorde/install.json"
INSTALL_SCHEMA = 2
# Schema 1 used the same exact-byte output and bounded root-block ownership records.
# Only its client selection/delegation metadata is retired; never adopt CLI-owned files.
SUPPORTED_RECEIPT_SCHEMAS = {1, INSTALL_SCHEMA}
PACKAGE_ROOTS = [
    "operations",
    "docsite",
    "pi",
    "prompts",
    "protocol",
    "scripts",
    "src",
]

RUNTIME = {
    "launcher": "scripts/run-operation.py",
    "python": ">=3.11",
    "requirements": "scripts/requirements.lock",
    "venv": ".concorde/.venv",
}
LEGACY_SKILLS_NOTICE = (
    "Concorde now supports only Pi. Skills installed by the external Agent Skills CLI "
    "are not installer-owned and are left untouched, including skills-lock.json. "
    "Inspect .agents/skills and .claude/skills and manually remove only the retired "
    "Concorde entries you own; preserve unrelated Skills, links and user files. "
    "Do not delete either directory or the CLI lock wholesale."
)


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
    if (
        not value
        or candidate.is_absolute()
        or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(ord(char) < 32 for char in value)
    ):
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
        raise InstallError(
            f"Concorde package manifest must be one real file: {manifest_path}"
        )
    manifest = _read_json(manifest_path, "Concorde package manifest")
    required = {
        "schema_version",
        "name",
        "version",
        "architecture_profile",
        "workspace_protocol",
        "runtime",
        "client",
        "install",
    }
    if required - set(manifest):
        raise InstallError(
            f"Concorde manifest is missing fields: {sorted(required - set(manifest))}"
        )
    if manifest.get("schema_version") != 5 or manifest.get("name") != "concorde":
        raise InstallError(
            "Concorde manifest must declare schema_version 5 and name 'concorde'"
        )
    if (
        manifest.get("architecture_profile") != 15
        or manifest.get("workspace_protocol") != 16
    ):
        raise InstallError(
            "Concorde package must declare Architecture Profile 15 and Workspace Protocol 16"
        )
    if manifest.get("delivery_proposal") != 10:
        raise InstallError("Concorde package must declare Delivery Proposal 10")
    if "skill_namespace" in manifest or "integrations" in manifest:
        raise InstallError("retired multi-client package fields are not supported")
    if "templates" in manifest:
        raise InstallError("retired top-level template inventory is not supported")
    install = manifest.get("install")
    if (
        not isinstance(install, dict)
        or install.get("framework_root") != FRAMEWORK_ROOT
        or install.get("receipt") != RECEIPT_PATH
    ):
        raise InstallError(
            "Concorde manifest declares an unsupported installation layout"
        )
    if set(install) != {"framework_root", "receipt"}:
        raise InstallError(
            "Concorde install configuration must not select a Skills CLI"
        )
    if manifest.get("client") != "pi":
        raise InstallError("Concorde supports only the Pi client")
    if manifest.get("package_roots") != PACKAGE_ROOTS:
        raise InstallError(
            "Concorde manifest declares an unsupported root package inventory"
        )
    if manifest.get("runtime") != RUNTIME:
        raise InstallError(
            f"Concorde manifest must declare the exact managed runtime: {RUNTIME}"
        )
    for field in ("launcher", "requirements"):
        relative = _safe_relative(RUNTIME[field], f"runtime.{field}")
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise InstallError(f"Concorde runtime {field} is missing: {relative}")
    for required_root in PACKAGE_ROOTS:
        path = root / required_root
        if path.is_symlink() or not path.is_dir():
            raise InstallError(f"Concorde package root is missing: {required_root}")
    for legacy_root in ("commands", "examples"):
        if (root / legacy_root).exists() or (root / legacy_root).is_symlink():
            raise InstallError(
                f"Concorde package contains removed legacy root: {legacy_root}"
            )
    try:
        concorde_build.build(root, framework_prefix=FRAMEWORK_ROOT)
    except concorde_build.BuildError as error:
        raise InstallError(str(error)) from error
    license_path = root / "LICENSE"
    readme_path = root / "README.md"
    if (
        manifest.get("license") != "MIT"
        or manifest.get("license_file") != "LICENSE"
        or license_path.is_symlink()
        or not license_path.is_file()
    ):
        raise InstallError(
            "Concorde package must include its declared MIT LICENSE file"
        )
    if readme_path.is_symlink() or not readme_path.is_file():
        raise InstallError("Concorde package must include one real root README.md")
    try:
        load_runtime_spec(root, manifest)
    except ManagedRuntimeError as error:
        raise InstallError(str(error)) from error
    from concorde.distribution.package_validation import validate_package

    package = Package(root, manifest)
    if root.name == "framework" and root.parent.name == ".concorde":
        # Consumer packages deliberately omit the source project's Specs/registry.
        # Verify their receipt and exact deployment instead of validating a source checkout.
        _verify_owned(root.parent.parent, package)
    else:
        findings = validate_package(root)
        if findings:
            raise InstallError("; ".join(f.message for f in findings))
    return package


def _package_files(package: Package) -> dict[str, bytes]:
    desired: dict[str, bytes] = {}
    desired[f"{FRAMEWORK_ROOT}/concorde.json"] = (
        package.root / "concorde.json"
    ).read_bytes()
    desired[f"{FRAMEWORK_ROOT}/LICENSE"] = (package.root / "LICENSE").read_bytes()
    desired[f"{FRAMEWORK_ROOT}/README.md"] = (package.root / "README.md").read_bytes()
    for directory in (
        "operations",
        "pi",
        "prompts",
        "protocol",
        "src",
    ):
        source_root = package.root / directory
        for path in sorted(source_root.rglob("*")):
            relative = path.relative_to(package.root).as_posix()
            parts = PurePosixPath(relative).parts
            if (
                relative.startswith("prompts/outer/source/")
                or relative == "pi/extensions/concorde-maintenance.ts"
            ):
                continue  # Source coordination/maintenance never ships to consumers.
            if directory == "pi" and "node_modules" in parts:
                # A local install (`npm ci --prefix pi`) leaves node_modules below pi/. The managed
                # runtime provisions it from its package.json and lock separately, so a local
                # install is neither deployed nor inspected.
                continue
            if path.is_symlink():
                raise InstallError(
                    f"Concorde packages may not contain symlinks: {path}"
                )
            if path.is_file():
                if "__pycache__" in parts or path.suffix in {".pyc", ".pyo"}:
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
        "issues.py",
        "install-concorde.py",
        "requirements.lock",
        "run-operation.py",
    )
    for name in scripts:
        source = package.root / "scripts" / name
        if source.is_symlink() or not source.is_file():
            raise InstallError(f"Concorde package script is missing: scripts/{name}")
        desired[f"{FRAMEWORK_ROOT}/scripts/{name}"] = source.read_bytes()
    return desired


def desired_outputs(package: Package) -> dict[str, tuple[bytes, str]]:
    outputs = {
        path: (content, "framework")
        for path, content in _package_files(package).items()
    }
    # Consumer installation deploys the Pi shim and framework runtime projections only.
    # Authored Operation guidance remains a framework input, not a discoverable Skill.
    try:
        build_result = concorde_build.build(
            package.root, framework_prefix=FRAMEWORK_ROOT
        )
    except concorde_build.BuildError as error:
        raise InstallError(str(error)) from error
    for output in build_result.outputs:
        if output.path.startswith((".pi/extensions/", ".pi/agents/")):
            outputs[output.path] = (output.content, "extension")
        else:
            outputs[f"{FRAMEWORK_ROOT}/{output.path}"] = (output.content, "framework")
    outputs[f"{FRAMEWORK_ROOT}/generated/build-manifest.json"] = (
        build_result.manifest,
        "framework",
    )
    # The Protocol bundle the project is granted lives at a stable project path, .concorde/protocol/:
    # the tracked package manifest verbatim (its digest is what `.concorde/config.json` binds) and
    # the rendered assets it lists. The installer owns and updates these files; initialization
    # binds them and configuration accepts an updated bundle explicitly.
    outputs[f"{PROTOCOL_ROOT}/manifest.json"] = (
        (package.root / "protocol/manifest.json").read_bytes(),
        "protocol",
    )
    for output in build_result.outputs:
        if output.path.startswith("generated/protocol/"):
            outputs[
                f"{PROTOCOL_ROOT}/{output.path.removeprefix('generated/protocol/')}"
            ] = (output.content, "protocol")
    # Concorde-owned defaults a project starts from, seeded only when absent and never owned by
    # the receipt. Initialization creates none of them; it produces only the user's project files.
    for path, content in project_default_files(package.root).items():
        outputs[path] = (content, "project-default")
    outputs[guidance.FILE] = (guidance.entry(), guidance.ROLE)
    return dict(sorted(outputs.items()))


def _load_receipt(target: Path) -> dict[str, Any]:
    path = _check_parent(target, RECEIPT_PATH)
    if path.is_symlink():
        raise InstallError(
            f"Concorde installation receipt must not be a symlink: {path}"
        )
    if not path.exists():
        return {"schema_version": INSTALL_SCHEMA, "outputs": []}
    if path.is_symlink() or not path.is_file():
        raise InstallError(
            f"Concorde installation receipt must be one real file: {path}"
        )
    value = _read_json(path, "Concorde installation receipt")
    if (
        type(value.get("schema_version")) is not int
        or value["schema_version"] not in SUPPORTED_RECEIPT_SCHEMAS
        or not isinstance(value.get("outputs"), list)
    ):
        raise InstallError(f"unsupported Concorde installation receipt: {path}")
    return value


def _prior_outputs(receipt: Mapping[str, Any]) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for item in receipt.get("outputs", []):
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("sha256"), str)
        ):
            raise InstallError(
                "Concorde installation receipt contains an invalid output"
            )
        relative = _safe_relative(item["path"], "receipt output")
        if relative == "skills-lock.json":
            raise InstallError("external Skills CLI locks are never installer-owned")
        if relative in outputs:
            raise InstallError(
                f"Concorde installation receipt repeats output: {relative}"
            )
        if item.get("role") != guidance.ROLE:
            if relative in guidance.RECEIPT_FILES:
                raise InstallError("root guidance cannot be owned as a whole file")
            outputs[relative] = item["sha256"]
    return outputs


def _file_digest(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    return _sha256(path.read_bytes())


@timed("installation.plan")
def installation_plan(
    target: Path,
    package: Package,
    *,
    remove_protocol_guidance: bool = False,
    preserve_project: bool = False,
) -> tuple[list[dict[str, str]], dict[str, tuple[bytes, str]], dict[str, Any]]:
    target = target.resolve()
    receipt = _load_receipt(target)
    prior = _prior_outputs(receipt)
    if remove_protocol_guidance and preserve_project:
        raise InstallError(
            "preserve-project and guidance removal are mutually exclusive"
        )
    desired = {} if remove_protocol_guidance else desired_outputs(package)
    preserved_actions: list[dict[str, str]] = []
    if preserve_project:
        preserved_actions = _preserve_project(target, desired, receipt)
    # Owned root entries: the block digest and whether the installer created the file itself.
    prior_guidance: dict[str, tuple[str, bool]] = {}
    for item in receipt.get("outputs", []):
        if item.get("role") == guidance.ROLE:
            relative = item["path"]
            if relative not in guidance.RECEIPT_FILES or relative in prior_guidance:
                raise InstallError("invalid or duplicate Protocol guidance receipt")
            prior_guidance[relative] = (item["sha256"], item.get("created") is True)
    guidance_actions = []
    guidance_desired = {}
    roots = set(prior_guidance) | {
        p for p, (_, role) in desired.items() if role == guidance.ROLE
    }
    for relative in sorted(roots):
        if preserve_project and any(a["path"] == relative for a in preserved_actions):
            continue
        wanted = desired.pop(relative, (None, None))[0]
        prior_digest, prior_created = prior_guidance.get(relative, (None, False))
        try:
            item, merged = guidance.plan(
                target, relative, wanted, prior_digest, prior_created
            )
            guidance_desired[relative] = (merged, item["role"])
        except (guidance.GuidanceError, UnicodeError) as error:
            item = {
                "path": relative,
                "action": "conflict",
                "role": guidance.ROLE,
                "sha256": "",
                "reason": str(error),
            }
        guidance_actions.append(item)
    if remove_protocol_guidance:
        return guidance_actions, guidance_desired, receipt
    actions: list[dict[str, str]] = list(preserved_actions)
    preserved_paths = {item["path"] for item in preserved_actions}
    for relative, (content, role) in desired.items():
        if relative in preserved_paths:
            continue
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
            item["reason"] = (
                unsafe
                or "existing target is not the desired bytes or an unchanged owned output"
            )
        actions.append(item)
    for relative, digest in sorted(prior.items()):
        if relative in desired or relative in preserved_paths:
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
        item = {
            "path": relative,
            "action": action,
            "role": "superseded",
            "sha256": digest,
        }
        if action == "conflict":
            item["reason"] = (
                unsafe or "superseded owned output was modified and must be preserved"
            )
        actions.append(item)
    try:
        actions.append(
            plan_runtime(
                target, load_runtime_spec(package.root, package.manifest), receipt
            )
        )
    except ManagedRuntimeError as error:
        actions.append(
            {
                "path": RUNTIME["venv"],
                "action": "conflict",
                "role": "runtime",
                "sha256": "sha256:" + "0" * 64,
                "reason": str(error),
            }
        )
    actions.extend(guidance_actions)
    desired.update(guidance_desired)
    return sorted(actions, key=lambda item: item["path"]), desired, receipt


def _preserve_project(target, desired, receipt):
    """Preserve project bytes without transferring ownership from another worktree."""
    prior = {item["path"]: item for item in receipt.get("outputs", [])}
    preserved = []
    protocol = target / PROTOCOL_ROOT
    if protocol.exists() or protocol.is_symlink():
        manifest_path = _check_parent(target, PROTOCOL_ROOT + "/manifest.json")
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise InstallError("preserved Protocol manifest must be one real file")
        manifest = _read_json(manifest_path, "preserved Protocol manifest")
        assets = manifest.get("assets")
        if not isinstance(assets, list) or not assets:
            raise InstallError("preserved Protocol must have a complete asset manifest")
        paths = {PROTOCOL_ROOT + "/manifest.json"}
        for asset in assets:
            if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
                raise InstallError("invalid preserved Protocol asset")
            source = asset["path"]
            if not source.startswith("generated/protocol/"):
                raise InstallError("invalid preserved Protocol asset path")
            relative = PROTOCOL_ROOT + "/" + source.removeprefix("generated/protocol/")
            path = _check_parent(target, relative)
            if relative in paths or _file_digest(path) != asset.get("digest"):
                raise InstallError(
                    "preserved Protocol is partial or has changed assets"
                )
            paths.add(relative)
        # Do not complete a partial old bundle with files from the new version.
        for relative in list(desired):
            if relative.startswith(PROTOCOL_ROOT + "/"):
                desired.pop(relative)
        for relative in sorted(
            paths | {p for p in prior if p.startswith(PROTOCOL_ROOT + "/")}
        ):
            path = _check_parent(target, relative)
            observed = _file_digest(path)
            if observed is None:
                raise InstallError(
                    f"preserved Protocol file is missing or unsafe: {relative}"
                )
            owned = prior.get(relative)
            if owned and (owned["sha256"] != observed or owned["role"] != "protocol"):
                raise InstallError(f"modified owned Protocol file: {relative}")
            if owned:
                desired[relative] = (path.read_bytes(), "protocol")
            preserved.append(
                {
                    "path": relative,
                    "role": "protocol",
                    "action": "preserve",
                    "sha256": observed,
                    "owned": "yes" if owned else "no",
                }
            )
    else:
        config_path = _check_parent(target, ".concorde/config.json")
        if config_path.exists() or config_path.is_symlink():
            if config_path.is_symlink() or not config_path.is_file():
                raise InstallError("project configuration must be one real file")
            config = _read_json(config_path, "project configuration")
            supplied = desired.get(PROTOCOL_ROOT + "/manifest.json")
            if supplied is None:
                raise InstallError("accepted project Protocol is missing")
            manifest = json.loads(supplied[0])
            if config.get("protocol") != {
                "version": manifest["version"],
                "digest": _sha256(supplied[0]),
            }:
                raise InstallError(
                    "missing Protocol cannot be seeded over a different accepted binding"
                )
    for relative in sorted(guidance.RECEIPT_FILES):
        path = target / relative
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            raise InstallError(f"preserved guidance must be one real file: {relative}")
        content = path.read_bytes()
        owned = prior.get(relative)
        if owned:
            try:
                block = guidance.split(content)[1]
            except guidance.GuidanceError as error:
                raise InstallError(str(error)) from error
            if owned["role"] != guidance.ROLE or _sha256(block) != owned["sha256"]:
                raise InstallError(f"modified owned Protocol guidance: {relative}")
            desired[relative] = (content, guidance.ROLE)
        else:
            desired.pop(relative, None)
        preserved.append(
            {
                "path": relative,
                "role": guidance.ROLE,
                "action": "preserve",
                "sha256": _sha256(content),
                "owned": "yes" if owned else "no",
                "created": "yes" if owned and owned.get("created") else "no",
            }
        )
    return preserved


def package_identity(package: Package) -> dict[str, str]:
    """Identity of the exact distributable bytes, independent of source/installed location."""
    outputs = desired_outputs(package)
    inventory = {
        path: {"role": role, "sha256": _sha256(content)}
        for path, (content, role) in outputs.items()
    }
    return {
        "version": package.version,
        "digest": _sha256(
            json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
        ),
        "build_digest": _sha256(
            outputs[FRAMEWORK_ROOT + "/generated/build-manifest.json"][0]
        ),
    }


def _verify_owned(target: Path, package: Package) -> dict[str, Any]:
    receipt = _load_receipt(target)
    if receipt.get("schema_version") != INSTALL_SCHEMA or receipt.get("client") != "pi":
        raise InstallError(
            "local installation needs an explicit current installer apply"
        )
    _prior_outputs(receipt)
    expected = desired_outputs(package)
    records = {item["path"]: item for item in receipt["outputs"]}
    if len(records) != len(receipt["outputs"]):
        raise InstallError("installation receipt contains duplicate outputs")
    for relative, (content, role) in expected.items():
        if role not in {"framework", "extension"}:
            continue
        record = records.get(relative)
        if (
            not record
            or record.get("role") != role
            or record.get("sha256") != _sha256(content)
        ):
            raise InstallError(
                f"local installation is missing or stale: {relative}; explicitly install it"
            )
    for relative, record in records.items():
        path = _check_parent(target, relative)
        if record.get("role") == guidance.ROLE:
            if (
                relative not in guidance.RECEIPT_FILES
                or path.is_symlink()
                or not path.is_file()
            ):
                raise InstallError(f"unsafe owned guidance: {relative}")
            try:
                observed = _sha256(guidance.split(path.read_bytes())[1])
            except guidance.GuidanceError as error:
                raise InstallError(str(error)) from error
        else:
            observed = _file_digest(path)
        if observed != record["sha256"]:
            raise InstallError(f"local owned output is missing or modified: {relative}")
    if receipt.get("package") != package_identity(package):
        raise InstallError(
            "local package provenance is missing or stale; explicitly install it"
        )
    return receipt


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
            raise InstallError(
                f"installation path contains a symlink: {current.relative_to(target)}"
            )
        if current.exists() and not current.is_dir():
            raise InstallError(
                f"installation parent is not a directory: {current.relative_to(target)}"
            )
    return path


def _receipt(
    package: Package,
    desired: Mapping[str, tuple[bytes, str]],
    runtime: Mapping[str, Any],
    actions: Sequence[Mapping[str, str]],
    *,
    preserve_project: bool = False,
) -> bytes:
    # A root file the installer created for its entry alone is remembered, so removing the
    # entry later may remove the empty file it leaves; a developer's file is never removed.
    created_roots = {
        item["path"]
        for item in actions
        if item.get("role") == guidance.ROLE and item.get("created") == "yes"
    }
    value = {
        "schema_version": INSTALL_SCHEMA,
        "concorde_version": package.version,
        "client": "pi",
        "architecture_profile": package.manifest["architecture_profile"],
        "workspace_protocol": package.manifest["workspace_protocol"],
        "runtime": dict(runtime),
        "package": package_identity(package),
        "provider_root": str(package.root),
        "preserve_project": preserve_project,
        "preserved": [
            {"path": item["path"], "role": item["role"]}
            for item in actions
            if item.get("owned") == "no"
        ],
        "outputs": [
            {
                "path": path,
                "role": role,
                "sha256": _sha256(
                    guidance.split(content)[1] if role == guidance.ROLE else content
                ),
                **({"created": True} if path in created_roots else {}),
            }
            for path, (content, role) in sorted(desired.items())
            if role not in {"project-default", "protocol-guidance-cleanup"}
        ],
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


@timed("installation.apply")
def apply_plan(
    target: Path,
    package: Package,
    actions: Sequence[Mapping[str, str]],
    desired: Mapping[str, tuple[bytes, str]],
    *,
    remove_protocol_guidance: bool = False,
    preserve_project: bool = False,
) -> str:
    admitted_identity = package_identity(package)
    conflicts = [item for item in actions if item["action"] == "conflict"]
    if conflicts:
        raise InstallError("installation plan has ownership conflicts")
    # Recheck shared files immediately before any installation writes, including symlinks.
    for item in actions:
        if (
            item["role"].startswith("protocol-guidance")
            and item["action"] != "preserve"
        ):
            path = target / item["path"]
            if (
                path.is_symlink()
                or (path.exists() and not path.is_file())
                or ("yes" if path.exists() else "no") != item["before_exists"]
                or _sha256(path.read_bytes() if path.exists() else b"")
                != item["before_sha256"]
            ):
                raise InstallError(
                    "Protocol guidance changed since preview; create a fresh plan"
                )
    current_actions, current_desired, _ = installation_plan(
        target,
        package,
        remove_protocol_guidance=remove_protocol_guidance,
        preserve_project=preserve_project,
    )
    if list(actions) != current_actions or dict(desired) != current_desired:
        raise InstallError("installation changed since preview; create a fresh plan")
    if remove_protocol_guidance and not actions:
        return "unchanged"
    mutable = [
        item
        for item in actions
        if item["role"] != "runtime"
        and item["action"] in {"create", "update", "remove"}
    ]
    runtime_items = [item for item in actions if item["role"] == "runtime"]
    if not remove_protocol_guidance and len(runtime_items) != 1:
        raise InstallError(
            "installation plan must contain exactly one managed runtime action"
        )
    runtime_action = runtime_items[0] if runtime_items else {"action": "unchanged"}
    receipt_path = target / RECEIPT_PATH
    previous_receipt = (
        receipt_path.read_bytes()
        if receipt_path.is_file() and not receipt_path.is_symlink()
        else None
    )
    previous_receipt_mode = (
        receipt_path.stat().st_mode & 0o777 if previous_receipt is not None else None
    )
    backups: dict[str, tuple[bytes, int]] = {}
    created: list[str] = []
    created_directories: set[Path] = set()
    staged_files: set[Path] = set()
    runtime_created = False
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
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=".concorde-install-", delete=False
            ) as handle:
                staged = Path(handle.name)
                staged_files.add(staged)
                handle.write(content)
            staged.replace(path)
            staged_files.discard(staged)
            if relative.startswith(f"{FRAMEWORK_ROOT}/scripts/") and path.suffix in {
                ".py",
                ".sh",
            }:
                path.chmod(0o755)
            else:
                path.chmod(backups[relative][1] if relative in backups else 0o644)
        if remove_protocol_guidance:
            value = _load_receipt(target)
            value["outputs"] = [
                item for item in value["outputs"] if item.get("role") != guidance.ROLE
            ]
            receipt_content = (
                json.dumps(value, indent=2, sort_keys=True) + "\n"
            ).encode()
        else:
            try:
                runtime = provision_runtime(
                    target,
                    target / FRAMEWORK_ROOT,
                    load_runtime_spec(package.root, package.manifest),
                    runtime_action,
                )
            except ManagedRuntimeError as error:
                raise InstallError(str(error)) from error
            runtime_created = runtime_action["action"] == "create"
            if package_identity(package) != admitted_identity:
                raise InstallError(
                    "package changed during installation; create a fresh plan"
                )
            receipt_content = _receipt(
                package, desired, runtime, actions, preserve_project=preserve_project
            )
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=receipt_path.parent, prefix=".concorde-receipt-", delete=False
        ) as handle:
            staged_receipt = Path(handle.name)
            staged_files.add(staged_receipt)
            handle.write(receipt_content)
        staged_receipt.replace(receipt_path)
        staged_files.discard(staged_receipt)
        receipt_path.chmod(0o644)
    except Exception:
        for staged in staged_files:
            staged.unlink(missing_ok=True)
        if runtime_created:
            # A runtime this apply created is part of its failed installation; an existing
            # runtime (unchanged or rebuilt in place) stays, as provisioning documents.
            runtime_path = target / RUNTIME["venv"]
            if runtime_path.is_dir() and not runtime_path.is_symlink():
                shutil.rmtree(runtime_path)
        for relative in reversed(created):
            path = target / relative
            if path.is_symlink():
                continue
            if path.is_file():
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
        for directory in sorted(
            created_directories, key=lambda item: len(item.parts), reverse=True
        ):
            # Rollback preserves the original failure if another file now occupies the directory.
            with suppress(OSError):
                directory.rmdir()
        raise
    return (
        "unchanged"
        if not mutable
        and runtime_action["action"] == "unchanged"
        and previous_receipt == receipt_content
        else "installed"
    )


def _print_plan(
    package: Package,
    actions: Sequence[Mapping[str, str]],
    status: str,
) -> None:
    counts: dict[str, int] = {}
    for item in actions:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    print("Concorde installation plan")
    print(f"  version: {package.version}")
    print("  client: pi")
    print(f"  migration: {LEGACY_SKILLS_NOTICE}")
    print(f"  status: {status}")
    print(
        "  actions: "
        + ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    )
    for item in actions:
        if item["action"] == "conflict":
            print(f"  conflict: {item['path']} — {item['reason']}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-concorde")
    parser.add_argument("--target", required=True)
    parser.add_argument("--checkout", default=str(SCRIPT_ROOT))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--preview", action="store_true")
    parser.add_argument(
        "--remove-protocol-guidance",
        action="store_true",
        help="preview/remove only receipt-owned root Protocol entry blocks",
    )
    parser.add_argument(
        "--preserve-project",
        action="store_true",
        help="preserve existing project Protocol and root guidance without adopting ownership",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = create_parser().parse_args(argv)
    try:
        requested_target = Path(arguments.target).absolute()
        if requested_target != requested_target.resolve():
            raise InstallError(f"target must not contain a symlink: {requested_target}")
        target = requested_target.resolve()
        if (target / "concorde.json").exists() and (target / "src/concorde").exists():
            raise InstallError("cannot install into an active Concorde source checkout")
        _check_target(target)
        package = load_package(Path(arguments.checkout))
        actions, desired, _ = installation_plan(
            target,
            package,
            remove_protocol_guidance=arguments.remove_protocol_guidance,
            preserve_project=arguments.preserve_project,
        )
        conflicts = [item for item in actions if item["action"] == "conflict"]
        status = "conflict" if conflicts else "preview"
        if arguments.apply and not conflicts:
            from .local_installation import installation_lock

            with installation_lock(target):
                status = apply_plan(
                    target,
                    package,
                    actions,
                    desired,
                    remove_protocol_guidance=arguments.remove_protocol_guidance,
                    preserve_project=arguments.preserve_project,
                )
        result = {
            "schema_version": INSTALL_SCHEMA,
            "status": status,
            "version": package.version,
            "client": "pi",
            "migration_notes": [LEGACY_SKILLS_NOTICE],
            "target": str(target),
            "receipt": RECEIPT_PATH,
            "preserve_project": arguments.preserve_project,
            "package": package_identity(package),
            "actions": actions,
        }
        if arguments.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            _print_plan(package, actions, status)
            if not arguments.apply and not conflicts:
                print("  next: rerun with --apply to accept this exact ownership plan")
        return 2 if conflicts else 0
    except (InstallError, ManagedRuntimeError, OSError, UnicodeError) as error:
        if arguments.format == "json":
            print(
                json.dumps(
                    {
                        "schema_version": INSTALL_SCHEMA,
                        "status": "failed",
                        "error": str(error),
                    },
                    sort_keys=True,
                )
            )
        else:
            print(f"CONCORDE INSTALL FAILED: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
