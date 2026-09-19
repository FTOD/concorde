#!/usr/bin/env python3
"""Preview or apply one standalone Concorde package to a project."""

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
from collections.abc import Mapping, Sequence
from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT / "src"))

from concorde.distribution import build as concorde_build  # noqa: E402
from concorde.distribution import protocol_guidance as guidance  # noqa: E402
from concorde.distribution.managed_runtime import (  # noqa: E402
    ManagedRuntimeError,
    load_runtime_spec,
    plan_runtime,
    provision_runtime,
)
from concorde.distribution.project_defaults import project_default_files  # noqa: E402
from concorde.views.docsite_template import (  # noqa: E402
    DocsiteTemplateError,
    template_files,
)

FRAMEWORK_ROOT = ".concorde/framework"
PROTOCOL_ROOT = ".concorde/protocol"
RECEIPT_PATH = ".concorde/install.json"
INSTALL_SCHEMA = 1
PACKAGE_ROOTS = [
    "operations",
    "docsite",
    "pi",
    "prompts",
    "protocol",
    "scripts",
    "skills",
    "src",
    "templates",
]

RUNTIME = {
    "launcher": "scripts/run-operation.py",
    "python": ">=3.11",
    "requirements": "scripts/requirements.lock",
    "venv": ".concorde/.venv",
}
# The Agent Skills CLI (`npx skills`) places the published Skills for these clients; the installer
# never copies a Skill itself. It reads them from the deployed framework copy, so the CLI's
# `skills-lock.json` names a source inside the project and a later `npx skills update` re-reads
# the installed version's Skills, wherever the source checkout has moved meanwhile.
SKILLS_CLI_AGENTS = {"claude": "claude-code", "codex": "codex"}
SKILLS_CLI_SOURCE = f"./{FRAMEWORK_ROOT}"
SKILLS_CLI_PIN = re.compile(r"^skills@[0-9]+\.[0-9]+\.[0-9]+$")
SKILL_PROJECTION_ROOTS = (".claude/skills/", ".agents/skills/")


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
        "templates",
        "integrations",
        "install",
    }
    if required - set(manifest):
        raise InstallError(
            f"Concorde manifest is missing fields: {sorted(required - set(manifest))}"
        )
    if manifest.get("schema_version") != 3 or manifest.get("name") != "concorde":
        raise InstallError(
            "Concorde manifest must declare schema_version 3 and name 'concorde'"
        )
    if (
        manifest.get("architecture_profile") != 15
        or manifest.get("workspace_protocol") != 16
    ):
        raise InstallError(
            "Concorde package must declare Architecture Profile 15 and Workspace Protocol 16"
        )
    if (
        manifest.get("delivery_proposal") != 10
        or manifest.get("skill_namespace") != "concorde"
    ):
        raise InstallError(
            "Concorde package must declare Delivery Proposal 10 and the concorde Skill namespace"
        )
    install = manifest.get("install")
    if (
        not isinstance(install, dict)
        or install.get("framework_root") != FRAMEWORK_ROOT
        or install.get("receipt") != RECEIPT_PATH
    ):
        raise InstallError(
            "Concorde manifest declares an unsupported installation layout"
        )
    skills_cli = install.get("skills_cli")
    if not isinstance(skills_cli, str) or SKILLS_CLI_PIN.fullmatch(skills_cli) is None:
        raise InstallError(
            "Concorde manifest must pin the Agent Skills CLI as install.skills_cli = skills@<version>"
        )
    integrations = manifest.get("integrations")
    if integrations != ["claude", "codex", "pi"]:
        raise InstallError(
            "Concorde manifest must declare exactly the claude, codex and pi integrations"
        )
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
    templates = manifest.get("templates")
    if not isinstance(templates, list) or any(
        not isinstance(item, str) for item in templates
    ):
        raise InstallError("Concorde manifest templates must be a string list")
    if len(templates) != len(set(templates)):
        raise InstallError("Concorde manifest template inventory contains duplicates")
    observed_templates = sorted(path.name for path in (root / "templates").glob("*.md"))
    if observed_templates != sorted(templates):
        raise InstallError(
            "Concorde manifest template inventory differs from root templates/"
        )
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
        concorde_build.build(root, "all", framework_prefix=FRAMEWORK_ROOT)
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

    findings = validate_package(root)
    if findings:
        raise InstallError("; ".join(f.message for f in findings))
    return Package(root, manifest)


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
        "skills",
        "src",
        "templates",
    ):
        source_root = package.root / directory
        for path in sorted(source_root.rglob("*")):
            relative = path.relative_to(package.root).as_posix()
            parts = PurePosixPath(relative).parts
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
        "requirements.lock",
        "run-operation.py",
    )
    for name in scripts:
        source = package.root / "scripts" / name
        if source.is_symlink() or not source.is_file():
            raise InstallError(f"Concorde package script is missing: scripts/{name}")
        desired[f"{FRAMEWORK_ROOT}/scripts/{name}"] = source.read_bytes()
    return desired


def selected_integrations(package: Package, integrations: Sequence[str]) -> list[str]:
    """The distinct requested clients, in request order; a project may carry several."""
    selected: list[str] = []
    for integration in integrations:
        if integration not in package.manifest["integrations"]:
            raise InstallError(f"unsupported integration: {integration}")
        if integration not in selected:
            selected.append(integration)
    if not selected:
        raise InstallError("select at least one integration")
    return selected


def skill_agents(package: Package, integrations: Sequence[str]) -> list[str]:
    """The Agent Skills CLI agent names of the selected clients that read Skills."""
    return [
        SKILLS_CLI_AGENTS[integration]
        for integration in selected_integrations(package, integrations)
        if integration in SKILLS_CLI_AGENTS
    ]


def desired_outputs(
    package: Package, integrations: Sequence[str]
) -> dict[str, tuple[bytes, str]]:
    selected = selected_integrations(package, integrations)
    outputs = {
        path: (content, "framework")
        for path, content in _package_files(package).items()
    }
    # The build is the only instruction source: it renders the framework's generated/** (role
    # bodies, the build manifest, the Studio graph list) and, for a Pi client, the session
    # extension shim. Claude Code and Codex receive no rendered Skill from the build: the Agent
    # Skills CLI installs the package's tracked published skills/, deployed below the framework
    # root, when the plan is applied. Consumers never run this build themselves.
    try:
        build_result = concorde_build.build(
            package.root, "all", framework_prefix=FRAMEWORK_ROOT
        )
    except concorde_build.BuildError as error:
        raise InstallError(str(error)) from error
    for output in build_result.outputs:
        if output.path.startswith(f"{concorde_build.INTEGRATION_ROOTS['pi']}/"):
            if "pi" in selected:
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
    # One root entry per selected client's instruction file; Codex and Pi share AGENTS.md.
    for integration in selected:
        outputs[guidance.FILES[integration]] = (
            guidance.entry(integration),
            guidance.ROLE,
        )
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
    if value.get("schema_version") != INSTALL_SCHEMA or not isinstance(
        value.get("outputs"), list
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
        if relative in outputs:
            raise InstallError(
                f"Concorde installation receipt repeats output: {relative}"
            )
        if item.get("role") != guidance.ROLE:
            if relative in guidance.FILES.values():
                raise InstallError("root guidance cannot be owned as a whole file")
            outputs[relative] = item["sha256"]
    return outputs


def _file_digest(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    return _sha256(path.read_bytes())


def installation_plan(
    target: Path,
    package: Package,
    integrations: Sequence[str],
    *,
    remove_protocol_guidance: bool = False,
) -> tuple[list[dict[str, str]], dict[str, tuple[bytes, str]], dict[str, Any]]:
    target = target.resolve()
    receipt = _load_receipt(target)
    prior = _prior_outputs(receipt)
    desired = {} if remove_protocol_guidance else desired_outputs(package, integrations)
    prior_guidance = {}
    for item in receipt.get("outputs", []):
        if item.get("role") == guidance.ROLE:
            relative = item["path"]
            if relative not in guidance.FILES.values() or relative in prior_guidance:
                raise InstallError("invalid or duplicate Protocol guidance receipt")
            prior_guidance[relative] = item["sha256"]
    guidance_actions = []
    guidance_desired = {}
    roots = set(prior_guidance) | {
        p for p, (_, role) in desired.items() if role == guidance.ROLE
    }
    for relative in sorted(roots):
        wanted = desired.pop(relative, (None, None))[0]
        try:
            item, merged = guidance.plan(
                target, relative, wanted, prior_guidance.get(relative)
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
            item["reason"] = (
                unsafe
                or "existing target is not the desired bytes or an unchanged owned output"
            )
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
    agents = skill_agents(package, integrations)
    if agents:
        # Not an owned output: the Agent Skills CLI places the published Skills and keeps its
        # own record, skills-lock.json, at the project root. The plan names the delegation so a
        # preview shows it; applying runs the CLI after the framework copy it reads is in place.
        actions.append(
            {
                "path": "skills-lock.json",
                "action": "delegate",
                "role": "skills",
                "sha256": "",
                "cli": package.manifest["install"]["skills_cli"],
                "source": SKILLS_CLI_SOURCE,
                "agents": ",".join(agents),
            }
        )
    actions.extend(guidance_actions)
    desired.update(guidance_desired)
    return sorted(actions, key=lambda item: item["path"]), desired, receipt


def _install_skills(target: Path, item: Mapping[str, str]) -> dict[str, Any]:
    """Run the pinned Agent Skills CLI so it installs the deployed framework's published Skills."""
    agents = item["agents"].split(",")
    command = ["npx", "-y", item["cli"], "add", item["source"]]
    for agent in agents:
        command.extend(["-a", agent])
    command.append("-y")
    environment = os.environ.copy()
    environment.update(
        {
            "NPM_CONFIG_AUDIT": "false",
            "NPM_CONFIG_FUND": "false",
            "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        }
    )
    try:
        result = subprocess.run(
            command,
            cwd=target,
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
    except OSError as error:
        raise InstallError(
            f"cannot run the Agent Skills CLI ({' '.join(command)}): {error}"
        ) from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        raise InstallError(
            f"Agent Skills CLI failed with exit {result.returncode}: {detail}"
        )
    return {"cli": item["cli"], "source": item["source"], "agents": agents}


def _prune_skill_directories(target: Path, path: Path) -> None:
    """Remove the directories a superseded Skill projection leaves empty, up to its root.

    Earlier installers owned `.claude/skills/concorde-*/SKILL.md` and `.agents/skills/...`;
    removing those files must not leave empty `concorde-*` directories where the Agent Skills
    CLI is about to place its own copies and links."""
    current = path.parent
    while current != target and current.is_dir() and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


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
    integrations: Sequence[str],
    desired: Mapping[str, tuple[bytes, str]],
    runtime: Mapping[str, Any],
    skills: Mapping[str, Any] | None,
) -> bytes:
    value = {
        "schema_version": INSTALL_SCHEMA,
        "concorde_version": package.version,
        "integrations": list(selected_integrations(package, integrations)),
        "architecture_profile": package.manifest["architecture_profile"],
        "workspace_protocol": package.manifest["workspace_protocol"],
        "runtime": dict(runtime),
        # The Skills the Agent Skills CLI placed are not owned outputs; the receipt records the
        # delegation (pinned CLI, in-project source and agents) rather than their bytes.
        "skills": dict(skills) if skills is not None else None,
        "outputs": [
            {
                "path": path,
                "role": role,
                "sha256": _sha256(
                    guidance.split(content)[1] if role == guidance.ROLE else content
                ),
            }
            for path, (content, role) in sorted(desired.items())
            if role not in {"project-default", "protocol-guidance-cleanup"}
        ],
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def apply_plan(
    target: Path,
    package: Package,
    integrations: Sequence[str],
    actions: Sequence[Mapping[str, str]],
    desired: Mapping[str, tuple[bytes, str]],
    *,
    remove_protocol_guidance: bool = False,
) -> str:
    conflicts = [item for item in actions if item["action"] == "conflict"]
    if conflicts:
        raise InstallError("installation plan has ownership conflicts")
    # Recheck shared files immediately before any installation writes, including symlinks.
    for item in actions:
        if item["role"].startswith("protocol-guidance"):
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
                if relative.startswith(SKILL_PROJECTION_ROOTS):
                    _prune_skill_directories(target, path)
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
            # The CLI reads the framework copy written above, so it runs after every owned
            # output is in place; its failure rolls those outputs back like any other failure.
            skills_item = next(
                (item for item in actions if item["role"] == "skills"), None
            )
            skills = _install_skills(target, skills_item) if skills_item else None
            receipt_content = _receipt(package, integrations, desired, runtime, skills)
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
    integrations: Sequence[str],
    actions: Sequence[Mapping[str, str]],
    status: str,
) -> None:
    counts: dict[str, int] = {}
    for item in actions:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    print("Concorde installation plan")
    print(f"  version: {package.version}")
    print(f"  integrations: {', '.join(integrations)}")
    print(f"  status: {status}")
    print(
        "  actions: "
        + ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    )
    for item in actions:
        if item["role"] == "skills":
            print(
                f"  skills: `npx -y {item['cli']} add {item['source']}` places the published "
                f"Skills for {item['agents'].replace(',', ', ')}"
            )
        if item["action"] == "conflict":
            print(f"  conflict: {item['path']} — {item['reason']}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="install-concorde")
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--integration",
        action="append",
        choices=["codex", "claude", "pi"],
        help="a client to install for; repeat for several (default: codex)",
    )
    parser.add_argument("--checkout", default=str(SCRIPT_ROOT))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--preview", action="store_true")
    parser.add_argument(
        "--remove-protocol-guidance",
        action="store_true",
        help="preview/remove only receipt-owned root Protocol entry blocks",
    )
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
        integrations = selected_integrations(
            package, arguments.integration or ["codex"]
        )
        actions, desired, _ = installation_plan(
            target,
            package,
            integrations,
            remove_protocol_guidance=arguments.remove_protocol_guidance,
        )
        conflicts = [item for item in actions if item["action"] == "conflict"]
        status = "conflict" if conflicts else "preview"
        if arguments.apply and not conflicts:
            status = apply_plan(
                target,
                package,
                integrations,
                actions,
                desired,
                remove_protocol_guidance=arguments.remove_protocol_guidance,
            )
        result = {
            "schema_version": INSTALL_SCHEMA,
            "status": status,
            "version": package.version,
            "integrations": integrations,
            "target": str(target),
            "receipt": RECEIPT_PATH,
            "actions": actions,
        }
        if arguments.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            _print_plan(package, integrations, actions, status)
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
