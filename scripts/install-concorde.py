#!/usr/bin/env python3
"""Install Concorde through Spec Kit's native bundle lifecycle."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlparse

import yaml


SPECIFY_VERSION = "0.16.4"
BUNDLE_ID = "concorde-bundle"
MANAGED_CATALOG = "concorde"
CURRENT_RELEASE_URL = "https://github.com/FTOD/concorde/releases/latest/download/release.json"

EXIT_OK = 0
EXIT_REQUEST = 2
EXIT_RELEASE = 3
EXIT_SPECIFY = 4


class InstallationError(Exception):
    """A staged installer failure with stable exit and remediation information."""

    def __init__(
        self,
        exit_code: int,
        stage: str,
        message: str,
        remediation: str,
        residual_state: str = "target unchanged",
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stage = stage
        self.remediation = remediation
        self.residual_state = residual_state


class ReleaseDescriptor(NamedTuple):
    version: str
    tag: str
    speckit_version: str
    bundle_id: str
    catalogs: dict[str, str]
    source: str


class InstallResult(NamedTuple):
    outcome: str
    record: Mapping[str, Any]
    integration: str
    reload_required: bool
    agent_assets: Mapping[str, Any] | None = None


def normalize_version(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("v"):
        normalized = normalized[1:]
    if not normalized or any(character.isspace() for character in normalized):
        raise InstallationError(
            EXIT_REQUEST,
            "request-validation",
            f"Invalid Concorde version: {value!r}.",
            "Pass a release version such as 0.6.0.",
        )
    return normalized


def release_pointer_url(version: str | None) -> str:
    if version is None:
        return CURRENT_RELEASE_URL
    normalized = normalize_version(version)
    return f"https://github.com/FTOD/concorde/releases/download/v{normalized}/release.json"


def _release_error(message: str) -> InstallationError:
    return InstallationError(
        EXIT_RELEASE,
        "release-validation",
        message,
        "Select a published Concorde release whose release.json follows schema 1.x and supports Spec Kit 0.16.4.",
    )


def _catalog_url_allowed(url: str, allow_local: bool) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    if parsed.scheme == "https" and hostname:
        return True
    return bool(
        allow_local
        and parsed.scheme == "http"
        and hostname in {"127.0.0.1", "localhost", "::1"}
    )


def validate_release_pointer(
    payload: object,
    *,
    expected_version: str | None = None,
    allow_local: bool = False,
    source: str = "release.json",
) -> ReleaseDescriptor:
    if not isinstance(payload, Mapping):
        raise _release_error("release.json must contain a JSON object.")
    schema = str(payload.get("schema_version", "")).strip()
    if schema.split(".", 1)[0] != "1":
        raise _release_error(f"Unsupported release.json schema {schema or '<missing>'!r}.")
    version = str(payload.get("version", "")).strip()
    tag = str(payload.get("tag", "")).strip()
    if not version or tag != f"v{version}":
        raise _release_error("release.json version and tag are missing or inconsistent.")
    if expected_version is not None and version != normalize_version(expected_version):
        raise _release_error(
            f"Requested Concorde {normalize_version(expected_version)} but release.json declares {version}."
        )
    bundle_id = str(payload.get("bundle_id", "")).strip()
    if bundle_id != BUNDLE_ID:
        raise _release_error(
            f"release.json names bundle {bundle_id or '<missing>'!r}; expected {BUNDLE_ID!r}."
        )
    speckit_version = str(payload.get("speckit_version", "")).replace(" ", "")
    if speckit_version != ">=0.16.4,<0.16.5":
        raise _release_error(
            f"Release {version} declares unsupported Spec Kit range {speckit_version or '<missing>'!r}."
        )
    raw_catalogs = payload.get("catalogs")
    if not isinstance(raw_catalogs, Mapping):
        raise _release_error("release.json must name extension, preset, and bundle catalogs.")
    catalogs: dict[str, str] = {}
    for kind in ("extensions", "presets", "bundles"):
        value = raw_catalogs.get(kind)
        if not isinstance(value, str) or not _catalog_url_allowed(value, allow_local):
            raise _release_error(
                f"release.json catalog {kind!r} must be an HTTPS URL"
                + (" or loopback HTTP URL." if allow_local else ".")
            )
        catalogs[kind] = value
    return ReleaseDescriptor(
        version=version,
        tag=tag,
        speckit_version=speckit_version,
        bundle_id=bundle_id,
        catalogs=catalogs,
        source=source,
    )


def classify_target(path: Path) -> str:
    if not path.exists():
        return "absent"
    if not path.is_dir():
        return "non-project"
    if (path / ".specify").is_dir():
        return "project"
    try:
        next(path.iterdir())
    except StopIteration:
        return "empty"
    return "non-project"


def catalog_state(
    kind: str,
    config: object,
    desired_url: str,
    managed_catalog: str = MANAGED_CATALOG,
) -> str:
    if kind not in {"extension", "preset", "bundle"}:
        raise ValueError(f"unsupported catalog kind: {kind}")
    if not isinstance(config, Mapping):
        return "missing"
    entries = config.get("catalogs", [])
    if not isinstance(entries, list):
        return "missing"
    identity_key = "id" if kind == "bundle" else "name"
    policy_key = "install_policy" if kind == "bundle" else "install_allowed"
    expected_policy: object = "install-allowed" if kind == "bundle" else True
    for entry in entries:
        if not isinstance(entry, Mapping) or entry.get(identity_key) != managed_catalog:
            continue
        if entry.get("url") == desired_url and entry.get(policy_key) == expected_policy:
            return "current"
        return "replace"
    return "missing"


def select_action(installed_version: str | None, resolved_version: str) -> str:
    if installed_version is None:
        return "install"
    if installed_version == resolved_version:
        return "already-current"
    return "update"


def installed_bundle_version(payload: object) -> str | None:
    if not isinstance(payload, list):
        raise InstallationError(
            EXIT_SPECIFY,
            "bundle-state",
            "Spec Kit returned an invalid installed-bundle list.",
            "Run `specify bundle list --json` and repair the reported registry problem.",
            "existing project was not changed",
        )
    matches = [
        item
        for item in payload
        if isinstance(item, Mapping) and item.get("bundle_id") == BUNDLE_ID
    ]
    if not matches:
        return None
    if len(matches) != 1 or not isinstance(matches[0].get("version"), str):
        raise InstallationError(
            EXIT_SPECIFY,
            "bundle-state",
            f"Spec Kit reported ambiguous or invalid state for {BUNDLE_ID}.",
            "Run `specify bundle list --json` and resolve duplicate or corrupt records.",
            "existing project was not changed",
        )
    return str(matches[0]["version"])


def render_failure(error: InstallationError) -> str:
    return "\n".join(
        [
            f"CONCORDE INSTALL FAILED [{error.stage}]",
            str(error),
            f"Remediation: {error.remediation}",
            f"Residual state: {error.residual_state}",
        ]
    )


class SpecifyRunner:
    """Invoke the public Spec Kit CLI while preserving its diagnostics."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("specify") or "specify"

    def verify(self, cwd: Path) -> None:
        try:
            result = subprocess.run(
                [self.executable, "--version"],
                cwd=cwd,
                text=True,
                capture_output=True,
            )
        except OSError as error:
            raise InstallationError(
                EXIT_REQUEST,
                "specify-cli",
                f"Cannot run the pinned Spec Kit CLI: {error}",
                f"Run this installer through `uvx --from specify-cli=={SPECIFY_VERSION} python`.",
            ) from error
        observed = (result.stdout or result.stderr).strip()
        if result.returncode or observed != f"specify {SPECIFY_VERSION}":
            raise InstallationError(
                EXIT_REQUEST,
                "specify-cli",
                f"Expected specify {SPECIFY_VERSION}; observed {observed or '<no version>'}.",
                f"Run this installer through `uvx --from specify-cli=={SPECIFY_VERSION} python`.",
            )

    def run(
        self,
        *arguments: str,
        cwd: Path,
        stage: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        result = subprocess.run(
            [self.executable, *arguments],
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
        )
        if result.stdout:
            print(result.stdout, end="", file=sys.stdout)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if check and result.returncode:
            raise InstallationError(
                EXIT_SPECIFY,
                stage,
                f"Spec Kit command failed ({result.returncode}): specify {' '.join(arguments)}",
                "Review the native Spec Kit diagnostic above, correct the project or source, and retry.",
                "inspect the target with `specify bundle list --json` before retrying",
            )
        return result

    def json(self, *arguments: str, cwd: Path, stage: str) -> Any:
        environment = os.environ.copy()
        environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        result = subprocess.run(
            [self.executable, *arguments],
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            if result.stdout:
                print(result.stdout, end="", file=sys.stdout)
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            raise InstallationError(
                EXIT_SPECIFY,
                stage,
                f"Spec Kit command failed ({result.returncode}): specify {' '.join(arguments)}",
                "Review the native Spec Kit diagnostic above, correct the project or source, and retry.",
                "target state is unchanged by this read-only command",
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise InstallationError(
                EXIT_SPECIFY,
                stage,
                f"Spec Kit returned invalid JSON: {error}",
                "Run the same command manually with --json and verify Spec Kit 0.16.4 is active.",
                "target state is unchanged by this read-only command",
            ) from error


def load_yaml(path: Path) -> object:
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise InstallationError(
            EXIT_SPECIFY,
            "catalog-state",
            f"Cannot read catalog state at {path}: {error}",
            "Repair the malformed project catalog configuration and retry.",
            "existing project was not changed",
        ) from error


def fetch_release(version: str | None) -> ReleaseDescriptor:
    url = release_pointer_url(version)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "concorde-installer"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise InstallationError(
            EXIT_RELEASE,
            "release-discovery",
            f"Cannot read {url}: {error}",
            "Check network access and the requested release version, then retry or use --checkout.",
        ) from error
    return validate_release_pointer(
        payload,
        expected_version=version,
        source=url,
    )


def _catalog_config_path(target: Path, kind: str) -> Path:
    names = {
        "extension": "extension-catalogs.yml",
        "preset": "preset-catalogs.yml",
        "bundle": "bundle-catalogs.yml",
    }
    return target / ".specify" / names[kind]


def catalog_states(
    target: Path,
    release: ReleaseDescriptor,
    managed_catalog: str = MANAGED_CATALOG,
) -> dict[str, str]:
    catalog_urls = {
        "extension": release.catalogs["extensions"],
        "preset": release.catalogs["presets"],
        "bundle": release.catalogs["bundles"],
    }
    return {
        kind: catalog_state(
            kind,
            load_yaml(_catalog_config_path(target, kind)),
            url,
            managed_catalog,
        )
        for kind, url in catalog_urls.items()
    }


def reconcile_catalogs(
    target: Path,
    release: ReleaseDescriptor,
    runner: SpecifyRunner,
    managed_catalog: str = MANAGED_CATALOG,
) -> dict[str, str]:
    urls = {
        "extension": release.catalogs["extensions"],
        "preset": release.catalogs["presets"],
        "bundle": release.catalogs["bundles"],
    }
    states = catalog_states(target, release, managed_catalog)
    for kind in ("extension", "preset", "bundle"):
        state = states[kind]
        if state == "current":
            continue
        if state == "replace":
            runner.run(
                kind, "catalog", "remove", managed_catalog,
                cwd=target,
                stage=f"{kind}-catalog-remove",
            )
        if kind == "extension":
            arguments = (
                "extension", "catalog", "add", urls[kind],
                "--name", managed_catalog, "--install-allowed",
            )
        elif kind == "preset":
            arguments = (
                "preset", "catalog", "add", urls[kind],
                "--name", managed_catalog, "--install-allowed",
            )
        else:
            arguments = (
                "bundle", "catalog", "add", urls[kind],
                "--id", managed_catalog, "--policy", "install-allowed",
            )
        runner.run(*arguments, cwd=target, stage=f"{kind}-catalog-add")
    return states


def _catalog_identity_present(target: Path, kind: str, identity: str) -> bool:
    config = load_yaml(_catalog_config_path(target, kind))
    if not isinstance(config, Mapping) or not isinstance(config.get("catalogs"), list):
        return False
    key = "id" if kind == "bundle" else "name"
    return any(
        isinstance(entry, Mapping) and entry.get(key) == identity
        for entry in config["catalogs"]
    )


def remove_managed_catalogs(
    target: Path,
    runner: SpecifyRunner,
    managed_catalog: str,
) -> None:
    if classify_target(target) != "project":
        return
    for kind in ("extension", "preset", "bundle"):
        if _catalog_identity_present(target, kind, managed_catalog):
            runner.run(
                kind, "catalog", "remove", managed_catalog,
                cwd=target,
                stage=f"{kind}-catalog-cleanup",
            )


def _project_integration(target: Path, runner: SpecifyRunner) -> str:
    status = runner.json("integration", "status", "--json", cwd=target, stage="integration-status")
    if not isinstance(status, Mapping) or not isinstance(status.get("default_integration"), str):
        raise InstallationError(
            EXIT_REQUEST,
            "integration-status",
            "The existing Spec Kit project has no readable default integration.",
            "Run `specify integration status --json`, repair its integration state, and retry.",
            "existing project was not changed",
        )
    return str(status["default_integration"])


def prepare_target(
    target: Path,
    requested_integration: str | None,
    integration_options: str | None,
    runner: SpecifyRunner,
) -> tuple[str, bool]:
    target_kind = classify_target(target)
    if target_kind == "non-project":
        raise InstallationError(
            EXIT_REQUEST,
            "target-validation",
            f"{target} is not an empty directory or an existing Spec Kit project.",
            "Choose an empty directory, initialize it manually, or run from an existing Spec Kit project.",
        )
    if target_kind == "project":
        integration = _project_integration(target, runner)
        if requested_integration and requested_integration != integration:
            raise InstallationError(
                EXIT_REQUEST,
                "integration-conflict",
                f"The project uses integration {integration!r}, not {requested_integration!r}.",
                f"Omit --integration or pass --integration {integration}.",
                "existing project was not changed",
            )
        return integration, False
    if not requested_integration:
        raise InstallationError(
            EXIT_REQUEST,
            "request-validation",
            "--integration is required for a fresh target.",
            "Pass the coding-agent integration, for example --integration codex.",
        )
    target.mkdir(parents=True, exist_ok=True)
    arguments = [
        "init", "--here", "--force", "--ignore-agent-tools", "--integration", requested_integration,
    ]
    options = integration_options
    if options is None and requested_integration == "codex":
        options = "--skills"
    if options:
        arguments.append(f"--integration-options={options}")
    runner.run(*arguments, cwd=target, stage="project-initialization")
    return requested_integration, True


def _print_plan(
    release: ReleaseDescriptor,
    integration: str,
    catalog_plan: Mapping[str, str],
    bundle_info: object,
    action: str,
    agent_plan: Mapping[str, Any] | None = None,
) -> None:
    print("\nConcorde installation plan")
    print(f"  release: {release.version} ({release.source})")
    print(f"  Spec Kit: {SPECIFY_VERSION} ({release.speckit_version})")
    print(f"  integration: {integration}")
    for kind in ("extension", "preset", "bundle"):
        print(f"  {kind} catalog: {catalog_plan[kind]}")
    print(f"  action: {action}")
    print("\nNative expanded bundle information:")
    print(json.dumps(bundle_info, indent=2, sort_keys=True))
    if agent_plan is not None:
        print("\nNative reflection-agent projection plan:")
        print(json.dumps(agent_plan, indent=2, sort_keys=True))


def _bundle_record(payload: object) -> Mapping[str, Any]:
    if not isinstance(payload, list):
        raise InstallationError(
            EXIT_SPECIFY,
            "final-verification",
            "Spec Kit returned an invalid installed-bundle list.",
            "Run `specify bundle list --json` and inspect the installation.",
            "installation result is unknown",
        )
    for item in payload:
        if isinstance(item, Mapping) and item.get("bundle_id") == BUNDLE_ID:
            return item
    raise InstallationError(
        EXIT_SPECIFY,
        "final-verification",
        f"Spec Kit did not report {BUNDLE_ID} after installation.",
        "Run `specify bundle list --json` and inspect the native lifecycle diagnostics.",
        "project is initialized and catalogs are registered; bundle state is unknown",
    )


def _print_success(
    outcome: str,
    record: Mapping[str, Any],
    integration: str,
    reload_required: bool,
    agent_assets: Mapping[str, Any] | None = None,
) -> None:
    components = record.get("contributed_components", [])
    print("\nCONCORDE INSTALL SUCCESS")
    print(f"  outcome: {outcome}")
    print(f"  bundle: {record.get('bundle_id')}@{record.get('version')}")
    if isinstance(components, list):
        for component in components:
            if isinstance(component, Mapping):
                print(f"  {component.get('kind')}: {component.get('id')}@{component.get('version')}")
    print(f"  integration: {integration}")
    if agent_assets:
        verify = agent_assets.get("verify", {})
        result = verify.get("result", {}) if isinstance(verify, Mapping) else {}
        outputs = result.get("outputs", []) if isinstance(result, Mapping) else []
        print(f"  agent projection: {verify.get('status', 'unknown') if isinstance(verify, Mapping) else 'unknown'}")
        print(f"  agent outputs: {len(outputs) if isinstance(outputs, list) else 0}")
        print("  agent receipt: .specify/concorde-agent-assets.json")
    print(f"  agent reload required: {'yes' if reload_required else 'no'}")
    print("  next: start a new agent session if required, then run speckit-concorde-init")


def run_agent_assets(
    project_root: Path,
    integration: str,
    operation: str,
    concorde_version: str,
    *,
    source_project: Path | None = None,
    allow_conflict: bool = False,
) -> Mapping[str, Any]:
    """Invoke only the projector shipped in an installed Concorde extension."""
    source = source_project or project_root
    launcher = source / ".specify/extensions/concorde/scripts/python/concorde.py"
    if not launcher.is_file():
        raise InstallationError(
            EXIT_SPECIFY,
            f"agent-projection-{operation}",
            f"Installed Concorde agent projector is missing: {launcher}",
            "Repair or reinstall extension:concorde, then retry.",
            "component state may be installed; agent projections were not verified",
        )
    arguments = [
        sys.executable,
        str(launcher),
        "--project-root",
        str(project_root),
        "agent-assets",
        operation,
        "--integration",
        integration,
        "--concorde-version",
        concorde_version,
    ]
    if source_project is not None and source_project != project_root:
        arguments.extend(
            [
                "--source-root",
                str(source / ".specify/extensions/concorde/agent-assets/reflections"),
            ]
        )
    environment = os.environ.copy()
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        arguments,
        cwd=source,
        env=environment,
        text=True,
        capture_output=True,
    )
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise InstallationError(
            EXIT_SPECIFY,
            f"agent-projection-{operation}",
            f"Installed agent projector returned invalid JSON: {error}",
            "Run the installed concorde.py agent-assets command directly and inspect its diagnostic.",
            "component state may be installed; agent projection state is unknown",
        ) from error
    status = payload.get("status") if isinstance(payload, Mapping) else None
    allowed = {"proposal", "success", "unchanged"}
    if allow_conflict:
        allowed.add("conflict")
    acceptable_nonzero = allow_conflict and status == "conflict"
    if (completed.returncode and not acceptable_nonzero) or status not in allowed:
        findings = payload.get("findings", []) if isinstance(payload, Mapping) else []
        messages = [str(item.get("message")) for item in findings if isinstance(item, Mapping)]
        raise InstallationError(
            EXIT_SPECIFY,
            f"agent-projection-{operation}",
            "; ".join(messages) or f"Agent projection {operation} failed with status {status!r}.",
            "Resolve the named ownership or installed-asset problem, then retry.",
            "component state may be installed; conflicting or failed agent projections were preserved",
        )
    return payload


def execute_install(
    target: Path,
    release: ReleaseDescriptor,
    requested_integration: str | None,
    integration_options: str | None,
    runner: SpecifyRunner,
    managed_catalog: str = MANAGED_CATALOG,
    announce: bool = True,
) -> InstallResult:
    integration, initialized = prepare_target(
        target,
        requested_integration,
        integration_options,
        runner,
    )
    before = runner.json("bundle", "list", "--json", cwd=target, stage="bundle-state")
    installed_version = installed_bundle_version(before)
    catalog_plan = catalog_states(target, release, managed_catalog)
    reconcile_catalogs(target, release, runner, managed_catalog)
    bundle_info = runner.json(
        "bundle", "info", release.bundle_id, "--json",
        cwd=target,
        stage="bundle-preview",
    )
    action = select_action(installed_version, release.version)
    _print_plan(release, integration, catalog_plan, bundle_info, action)
    if action == "install":
        runner.run("bundle", "install", release.bundle_id, cwd=target, stage="bundle-install")
        outcome = "installed"
    elif action == "update":
        runner.run("bundle", "update", release.bundle_id, cwd=target, stage="bundle-update")
        outcome = "updated"
    else:
        outcome = action
    after = runner.json("bundle", "list", "--json", cwd=target, stage="final-verification")
    record = _bundle_record(after)
    if record.get("version") != release.version:
        raise InstallationError(
            EXIT_SPECIFY,
            "final-verification",
            f"Installed bundle version {record.get('version')!r} does not match planned {release.version!r}.",
            "Review `specify bundle list --json` and the registered Concorde catalogs.",
            "project is initialized; installed component state disagrees with the plan",
        )
    agent_preview = run_agent_assets(target, integration, "preview", release.version)
    agent_sync = run_agent_assets(target, integration, "sync", release.version)
    agent_verify = run_agent_assets(target, integration, "verify", release.version)
    agent_assets = {"preview": agent_preview, "sync": agent_sync, "verify": agent_verify}
    result = InstallResult(
        outcome=outcome,
        record=record,
        integration=integration,
        reload_required=(
            initialized
            or action in {"install", "update"}
            or agent_sync.get("status") == "success"
        ),
        agent_assets=agent_assets,
    )
    if announce:
        _print_success(*result)
    return result


def inspect_target(
    target: Path,
    release: ReleaseDescriptor,
    requested_integration: str | None,
    runner: SpecifyRunner,
    managed_catalog: str = MANAGED_CATALOG,
) -> tuple[str, str | None, dict[str, str]]:
    target_kind = classify_target(target)
    if target_kind == "non-project":
        raise InstallationError(
            EXIT_REQUEST,
            "target-validation",
            f"{target} is not an empty directory or an existing Spec Kit project.",
            "Choose an empty directory, initialize it manually, or preview an existing Spec Kit project.",
        )
    if target_kind == "project":
        integration = _project_integration(target, runner)
        if requested_integration and requested_integration != integration:
            raise InstallationError(
                EXIT_REQUEST,
                "integration-conflict",
                f"The project uses integration {integration!r}, not {requested_integration!r}.",
                f"Omit --integration or pass --integration {integration}.",
                "existing project was not changed",
            )
        bundles = runner.json("bundle", "list", "--json", cwd=target, stage="bundle-state")
        return (
            integration,
            installed_bundle_version(bundles),
            catalog_states(target, release, managed_catalog),
        )
    if not requested_integration:
        raise InstallationError(
            EXIT_REQUEST,
            "request-validation",
            "--integration is required for a fresh target.",
            "Pass the coding-agent integration, for example --integration codex.",
        )
    return requested_integration, None, {kind: "missing" for kind in ("extension", "preset", "bundle")}


def execute_preview(
    target: Path,
    release: ReleaseDescriptor,
    requested_integration: str | None,
    integration_options: str | None,
    runner: SpecifyRunner,
    managed_catalog: str = MANAGED_CATALOG,
) -> str:
    integration, installed_version, target_catalogs = inspect_target(
        target,
        release,
        requested_integration,
        runner,
        managed_catalog,
    )
    with tempfile.TemporaryDirectory(prefix="concorde-preview-") as temporary:
        preview_root = Path(temporary)
        prepare_target(preview_root, integration, integration_options, runner)
        reconcile_catalogs(preview_root, release, runner, managed_catalog)
        bundle_info = runner.json(
            "bundle", "info", release.bundle_id, "--json",
            cwd=preview_root,
            stage="bundle-preview",
        )
        runner.run("bundle", "install", release.bundle_id, cwd=preview_root, stage="preview-bundle-install")
        agent_plan = run_agent_assets(
            target,
            integration,
            "preview",
            release.version,
            source_project=preview_root,
            allow_conflict=True,
        )
    action = select_action(installed_version, release.version)
    _print_plan(release, integration, target_catalogs, bundle_info, action, agent_plan)
    print("\nCONCORDE INSTALL PREVIEW COMPLETE")
    print("  outcome: preview")
    print(f"  planned action: {action}")
    print("  target changed: no")
    return "preview"


class _QuietCatalogHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *arguments: object) -> None:
        return


class LoopbackCatalogServer:
    def __init__(self, directory: Path) -> None:
        handler = functools.partial(_QuietCatalogHandler, directory=str(directory.resolve()))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.started = False

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def start(self) -> None:
        self.thread.start()
        self.started = True

    def close(self) -> None:
        if self.started:
            self.server.shutdown()
        self.server.server_close()
        if self.started:
            self.thread.join(timeout=5)


def _run_release_script(checkout: Path, script: Path, *arguments: str, stage: str) -> None:
    environment = os.environ.copy()
    environment.pop("SPECIFY_FEATURE_DIRECTORY", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=checkout,
        env=environment,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise InstallationError(
            EXIT_RELEASE,
            stage,
            f"Local release command failed ({result.returncode}): {script.name}",
            "Fix the named checkout release validation, then retry development mode.",
            "target unchanged; temporary release data will be removed",
        )


@contextlib.contextmanager
def local_release(checkout_value: str):
    checkout = Path(checkout_value).expanduser().resolve()
    build_script = checkout / "scripts/release/build-components.py"
    verify_script = checkout / "scripts/release/verify-release.py"
    manifests = [
        checkout / "bundles/concorde-bundle/bundle.yml",
        checkout / "presets/concorde/preset.yml",
        checkout / "extensions/concorde/extension.yml",
    ]
    missing = [path for path in [build_script, verify_script, *manifests] if not path.is_file()]
    if missing:
        joined = ", ".join(str(path.relative_to(checkout)) for path in missing) if checkout.is_dir() else str(checkout)
        raise InstallationError(
            EXIT_RELEASE,
            "checkout-validation",
            f"The local Concorde checkout is incomplete: {joined}.",
            "Pass the root of a Concorde checkout containing the release scripts and all three manifests.",
        )
    with tempfile.TemporaryDirectory(prefix="concorde-release-") as temporary:
        dist = Path(temporary)
        server = LoopbackCatalogServer(dist)
        try:
            _run_release_script(
                checkout,
                build_script,
                "--output", str(dist),
                "--base-url", server.base_url,
                stage="checkout-build",
            )
            _run_release_script(
                checkout,
                verify_script,
                "--dist", str(dist),
                "--expect-base-url", server.base_url,
                stage="checkout-verification",
            )
            try:
                bundle_catalog = json.loads((dist / "bundles.json").read_text(encoding="utf-8"))
                bundle = bundle_catalog["bundles"][BUNDLE_ID]
                version = str(bundle["version"])
                speckit_version = str(bundle["requires"]["speckit_version"])
            except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
                raise InstallationError(
                    EXIT_RELEASE,
                    "checkout-verification",
                    f"The verified local bundle catalog cannot be read: {error}",
                    "Re-run the checkout release verifier and repair its generated catalogs.",
                ) from error
            release = validate_release_pointer(
                {
                    "schema_version": "1.0",
                    "version": version,
                    "tag": f"v{version}",
                    "speckit_version": speckit_version,
                    "bundle_id": BUNDLE_ID,
                    "catalogs": {
                        "extensions": f"{server.base_url}/extensions.json",
                        "presets": f"{server.base_url}/presets.json",
                        "bundles": f"{server.base_url}/bundles.json",
                    },
                },
                expected_version=version,
                allow_local=True,
                source=f"local checkout {checkout} via {server.base_url}",
            )
            server.start()
            yield release
        finally:
            server.close()


def _operate(
    arguments: argparse.Namespace,
    target: Path,
    release: ReleaseDescriptor,
    runner: SpecifyRunner,
    *,
    development: bool = False,
) -> None:
    managed_catalog = "concorde-dev" if development else MANAGED_CATALOG
    if arguments.preview:
        execute_preview(
            target,
            release,
            arguments.integration,
            arguments.integration_options,
            runner,
            managed_catalog,
        )
    else:
        if development:
            result: InstallResult | None = None
            try:
                result = execute_install(
                    target,
                    release,
                    arguments.integration,
                    arguments.integration_options,
                    runner,
                    managed_catalog,
                    announce=False,
                )
            finally:
                remove_managed_catalogs(target, runner, managed_catalog)
            if result is not None:
                _print_success(*result)
        else:
            execute_install(
                target,
                release,
                arguments.integration,
                arguments.integration_options,
                runner,
                managed_catalog,
            )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--target", default=".", help="Target project directory (default: current directory)")
    result.add_argument("--integration", help="Coding-agent integration; required for a fresh target")
    result.add_argument("--integration-options", help="Options forwarded to `specify init`")
    source = result.add_mutually_exclusive_group()
    source.add_argument("--version", help="Published Concorde version (for example 0.6.0)")
    source.add_argument("--checkout", help="Local Concorde checkout to build, verify, and install")
    result.add_argument("--preview", action="store_true", help="Print the exact plan without changing the target")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    target = Path(arguments.target).expanduser().resolve()
    runner = SpecifyRunner()
    try:
        runner.verify(Path.cwd())
        if arguments.checkout:
            with local_release(arguments.checkout) as release:
                _operate(arguments, target, release, runner, development=True)
        else:
            release = fetch_release(arguments.version)
            _operate(arguments, target, release, runner)
    except InstallationError as error:
        print(render_failure(error), file=sys.stderr)
        return error.exit_code
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
