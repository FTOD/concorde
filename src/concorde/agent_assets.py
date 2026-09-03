"""Deterministic rendering and ownership of installed reflection-triage agent assets."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .model import Finding, ToolResult


RECEIPT_PATH = ".concorde/agent-assets.json"
CONFIG_PATH = ".concorde/reflections/config.json"
IGNORE_PATH = ".concorde/reflections/.gitignore"
LEGACY_CONFIG = ".claude/reflections.config.json"
LEGACY_PLANS = ".claude/reflection-plans"
LEGACY_CONFIG_ARCHIVE_PATH = ".concorde/reflections/legacy-claude-config.json"
LEGACY_CONFIG_SCHEMA_KEYS = frozenset(
    {"_doc", "log", "features_root", "plans_dir", "order", "investigators", "implementers", "require_approval", "skip"}
)


class AgentAssetError(ValueError):
    pass


def _safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or value.endswith("/"):
        raise AgentAssetError(f"{field} must be a safe project-relative path: {value!r}")
    return path.as_posix()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentAssetError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise AgentAssetError(f"{label} must be a JSON object: {path}")
    return value


def _manifest(asset_root: Path) -> dict[str, Any]:
    value = _read_json(asset_root / "manifest.json", "agent-asset manifest")
    if value.get("schema_version") != 1 or value.get("protocol") != "reflection-triage/v5":
        raise AgentAssetError("agent-asset manifest must declare schema_version 1 and reflection-triage/v5")
    integrations = value.get("integrations")
    if not isinstance(integrations, dict) or set(integrations) != {"claude", "codex"}:
        raise AgentAssetError("agent-asset manifest must declare exactly claude and codex integrations")
    return value


def _source_path(asset_root: Path, relative: str, field: str) -> Path:
    safe = _safe_relative(relative, field)
    path = asset_root / safe
    if path.is_symlink() or not path.is_file():
        raise AgentAssetError(f"{field} does not name a regular canonical asset: {safe}")
    return path


def source_digest(asset_root: Path) -> str:
    digest = hashlib.sha256()
    files = [path for path in sorted(asset_root.rglob("*")) if path.is_file()]
    if not files or any(path.is_symlink() for path in files):
        raise AgentAssetError("canonical agent assets must be regular files")
    for path in files:
        relative = path.relative_to(asset_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def render_projection(asset_root: Path, integration: str) -> dict[str, str]:
    manifest = _manifest(asset_root)
    definition = manifest["integrations"].get(integration)
    if not isinstance(definition, dict) or not isinstance(definition.get("outputs"), list):
        raise AgentAssetError(f"unsupported agent integration: {integration}")
    rendered: dict[str, str] = {}
    for item in definition["outputs"]:
        if not isinstance(item, dict):
            raise AgentAssetError(f"invalid {integration} projection entry")
        target = _safe_relative(str(item.get("target", "")), "projection target")
        if target in rendered:
            raise AgentAssetError(f"duplicate projection target: {target}")
        template = _source_path(asset_root, str(item.get("template", "")), "projection template")
        body = _source_path(asset_root, str(item.get("body", "")), "projection body")
        template_text = template.read_text(encoding="utf-8").replace("\r\n", "\n")
        body_text = body.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
        if template_text.count("{{BODY}}") != 1:
            raise AgentAssetError(f"projection template must contain exactly one {{{{BODY}}}} token: {template}")
        if integration == "codex" and '"""' in body_text:
            raise AgentAssetError(f"Codex developer instructions cannot contain a TOML triple-quote: {body}")
        rendered[target] = template_text.replace("{{BODY}}", body_text).rstrip() + "\n"
    return dict(sorted(rendered.items()))


def projection_roles(asset_root: Path, integration: str) -> dict[str, str]:
    """Return exact owned target→specialist-role transitions for one integration."""

    manifest = _manifest(asset_root)
    roles = {
        _safe_relative(str(item["target"]), "projection target"): str(item["role"])
        for item in manifest["integrations"][integration]["outputs"]
    }
    if set(roles.values()) != {"investigator", "implementer"}:
        raise AgentAssetError(
            f"{integration} reflection projection must retain investigator/implementer roles"
        )
    return roles


def _empty_receipt() -> dict[str, Any]:
    return {"schema_version": 1, "integrations": {}}


def _load_receipt(project_root: Path) -> dict[str, Any]:
    path = project_root / RECEIPT_PATH
    if not path.exists():
        return _empty_receipt()
    value = _read_json(path, "agent-asset receipt")
    if value.get("schema_version") != 1 or not isinstance(value.get("integrations"), dict):
        raise AgentAssetError(f"unsupported agent-asset receipt: {path}")
    return value


def _prior_outputs(receipt: Mapping[str, Any], integration: str) -> dict[str, str]:
    record = receipt.get("integrations", {}).get(integration, {})
    outputs = record.get("outputs", []) if isinstance(record, Mapping) else []
    result: dict[str, str] = {}
    for item in outputs:
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
            raise AgentAssetError(f"invalid {integration} output in agent-asset receipt")
        result[_safe_relative(item["path"], "receipt output")] = item["sha256"]
    return result


def _validate_legacy_config_value(key: str, value: Any) -> None:
    """Validate one legacy field with the same rules ``reflections_queue.load_config`` enforces."""

    if key == "order":
        if value not in {"newest-first", "oldest-first"}:
            raise AgentAssetError("legacy config order must be newest-first or oldest-first")
    elif key in {"investigators", "implementers"}:
        if not isinstance(value, int) or value < 1:
            raise AgentAssetError(f"legacy config {key} must be a positive integer")
    elif key == "require_approval":
        if not isinstance(value, bool):
            raise AgentAssetError("legacy config require_approval must be boolean")
    elif key == "skip":
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value) or len(value) != len(set(value)):
            raise AgentAssetError("legacy config skip must be a unique string list")


def _convert_legacy_config(value: Mapping[str, Any], default: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a v4 ``.claude/reflections.config.json`` payload to the canonical schema.

    ``plans_dir``/``worktrees_dir`` are always the canonical defaults: legacy ``plans_dir`` names
    v4 plan scratch and is never mapped onto the canonical layout.
    """

    unsupported = sorted(set(value) - LEGACY_CONFIG_SCHEMA_KEYS)
    if unsupported:
        raise AgentAssetError(f"legacy reflection config has unsupported key(s): {', '.join(unsupported)}")
    converted: dict[str, Any] = {"schema_version": 1}
    for key in ("order", "investigators", "implementers", "require_approval", "skip"):
        if key in value:
            _validate_legacy_config_value(key, value[key])
            converted[key] = value[key]
        else:
            converted[key] = default[key]
    converted["plans_dir"] = default["plans_dir"]
    converted["worktrees_dir"] = default["worktrees_dir"]
    return converted


def _legacy_config_action(project_root: Path, asset_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Return legacy-related preview actions and, if adoption applies, the converted config.

    Returns at most one action: a single ``conflict`` describing why legacy state cannot be
    resolved automatically, or a single ``adopt-legacy-config`` action naming the digest-bound
    conversion that ``sync_agent_assets`` will apply.
    """

    plans = project_root / LEGACY_PLANS
    legacy = project_root / LEGACY_CONFIG
    canonical = project_root / CONFIG_PATH
    legacy_present = legacy.exists() or legacy.is_symlink()

    if canonical.exists():
        # Exactly as today: once the canonical config exists, legacy plan scratch is ignored
        # entirely. The one new case is dual authority, which must now conflict explicitly.
        if legacy_present:
            return (
                [
                    {
                        "path": CONFIG_PATH,
                        "action": "conflict",
                        "reason": (
                            f"legacy config exists at {LEGACY_CONFIG} and canonical config exists at {CONFIG_PATH}; "
                            "remove or archive the legacy file explicitly"
                        ),
                    }
                ],
                None,
            )
        return [], None
    if plans.exists() or plans.is_symlink():
        return (
            [
                {
                    "path": CONFIG_PATH,
                    "action": "conflict",
                    "reason": f"legacy state exists at {LEGACY_PLANS}; adopt or migrate it explicitly",
                }
            ],
            None,
        )
    if not legacy_present:
        return [], None
    if legacy.is_symlink() or not legacy.is_file():
        return (
            [{"path": CONFIG_PATH, "action": "conflict", "reason": f"legacy config is not a regular file: {LEGACY_CONFIG}"}],
            None,
        )
    archive = project_root / LEGACY_CONFIG_ARCHIVE_PATH
    if archive.exists() or archive.is_symlink():
        return (
            [
                {
                    "path": CONFIG_PATH,
                    "action": "conflict",
                    "reason": f"legacy config archive path already exists: {LEGACY_CONFIG_ARCHIVE_PATH}",
                }
            ],
            None,
        )
    raw = legacy.read_bytes()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        return (
            [{"path": CONFIG_PATH, "action": "conflict", "reason": f"legacy reflection config is not valid JSON: {error}"}],
            None,
        )
    if not isinstance(parsed, dict):
        return (
            [{"path": CONFIG_PATH, "action": "conflict", "reason": f"legacy reflection config must be a JSON object: {LEGACY_CONFIG}"}],
            None,
        )
    default = _read_json(asset_root / "config.default.json", "reflection-triage default config")
    try:
        converted = _convert_legacy_config(parsed, default)
    except AgentAssetError as error:
        return ([{"path": CONFIG_PATH, "action": "conflict", "reason": str(error)}], None)
    content = json.dumps(converted, indent=2, sort_keys=True) + "\n"
    return (
        [
            {
                "path": CONFIG_PATH,
                "action": "adopt-legacy-config",
                "source": LEGACY_CONFIG,
                "archive": LEGACY_CONFIG_ARCHIVE_PATH,
                "source_sha256": "sha256:" + _sha256_bytes(raw),
                "content_sha256": "sha256:" + _sha256_bytes(content.encode("utf-8")),
            }
        ],
        converted,
    )


def _projection_actions(
    project_root: Path,
    desired: Mapping[str, str],
    prior: Mapping[str, str],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for relative, content in desired.items():
        path = project_root / relative
        desired_digest = _sha256_bytes(content.encode("utf-8"))
        if path.is_symlink():
            actions.append({"path": relative, "action": "conflict", "reason": "target is a symlink"})
            continue
        if not path.exists():
            actions.append({"path": relative, "action": "create", "sha256": desired_digest})
            continue
        if not path.is_file():
            actions.append({"path": relative, "action": "conflict", "reason": "target is not a regular file"})
            continue
        observed = _sha256_file(path)
        if observed == desired_digest:
            action = "unchanged" if prior.get(relative) == observed else "adopt"
            actions.append({"path": relative, "action": action, "sha256": observed})
        elif prior.get(relative) == observed:
            actions.append({"path": relative, "action": "update", "sha256": desired_digest})
        else:
            actions.append(
                {
                    "path": relative,
                    "action": "conflict",
                    "reason": "existing bytes are not the desired projection or a matching owned output",
                }
            )
    for relative, digest in sorted(prior.items()):
        if relative in desired:
            continue
        path = project_root / relative
        if not path.exists():
            actions.append({"path": relative, "action": "drop-missing", "sha256": digest})
        elif path.is_file() and not path.is_symlink() and _sha256_file(path) == digest:
            actions.append({"path": relative, "action": "remove", "sha256": digest})
        else:
            actions.append(
                {
                    "path": relative,
                    "action": "conflict",
                    "reason": "superseded owned output was modified and must be preserved",
                }
            )
    return sorted(actions, key=lambda item: item["path"])


def preview_agent_assets(
    project_root: Path,
    asset_root: Path,
    integration: str,
    concorde_version: str = "source",
) -> ToolResult:
    try:
        desired = render_projection(asset_root, integration)
        receipt = _load_receipt(project_root)
        actions = _projection_actions(project_root, desired, _prior_outputs(receipt, integration))
        legacy_actions, adopted_config = _legacy_config_action(project_root, asset_root)
        actions.extend(legacy_actions)
        conflicts = [item for item in actions if item["action"] == "conflict"]
        result: dict[str, Any] = {
            "integration": integration,
            "concorde_version": concorde_version,
            "source_digest": source_digest(asset_root),
            "outputs": sorted(desired),
            "actions": actions,
        }
        if adopted_config is not None:
            result["adopted_config"] = adopted_config
        return ToolResult(
            "agent-assets.preview",
            integration,
            "conflict" if conflicts else "proposal",
            result=result,
            findings=tuple(
                Finding(
                    "CONCORDE-AGENT-ASSET-001",
                    "error",
                    item["path"],
                    item["reason"],
                    "Preserve the file, or explicitly adopt/migrate it before retrying projection sync.",
                )
                for item in conflicts
            ),
        )
    except AgentAssetError as error:
        return ToolResult(
            "agent-assets.preview",
            integration,
            "invalid",
            findings=(
                Finding(
                    "CONCORDE-AGENT-ASSET-002",
                    "error",
                    "agent-assets/reflections",
                    str(error),
                    "Repair the installed canonical agent assets or choose a supported integration.",
                ),
            ),
        )


def _write_receipt(project_root: Path, receipt: Mapping[str, Any]) -> None:
    path = project_root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sync_agent_assets(
    project_root: Path,
    asset_root: Path,
    integration: str,
    concorde_version: str = "source",
) -> ToolResult:
    preview = preview_agent_assets(project_root, asset_root, integration, concorde_version)
    if preview.status in {"conflict", "invalid", "failed"}:
        return ToolResult(
            "agent-assets.sync",
            integration,
            preview.status,
            findings=preview.findings,
            result=preview.result,
        )
    desired = render_projection(asset_root, integration)
    actions = list(preview.result["actions"])
    for item in actions:
        relative = item["path"]
        action = item["action"]
        path = project_root / relative
        if action in {"create", "update"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(desired[relative], encoding="utf-8", newline="\n")
        elif action == "remove":
            path.unlink()

    config_path = project_root / CONFIG_PATH
    config_created = False
    config_adopted = False
    adopt_action = next((item for item in actions if item["action"] == "adopt-legacy-config"), None)
    if adopt_action is not None:
        legacy_path = project_root / adopt_action["source"]
        archive_path = project_root / adopt_action["archive"]
        observed_source = (
            "sha256:" + _sha256_file(legacy_path)
            if legacy_path.is_file() and not legacy_path.is_symlink()
            else None
        )
        if observed_source != adopt_action["source_sha256"]:
            return ToolResult(
                "agent-assets.sync",
                integration,
                "conflict",
                findings=(
                    Finding(
                        "CONCORDE-AGENT-ASSET-001",
                        "error",
                        adopt_action["source"],
                        "legacy reflection config changed or disappeared since preview",
                        "Re-run agent-asset preview to recompute the adoption before syncing.",
                    ),
                ),
                result=preview.result,
            )
        content = json.dumps(preview.result["adopted_config"], indent=2, sort_keys=True) + "\n"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=config_path.parent, prefix=".agent-assets-config-", delete=False) as handle:
            staged = Path(handle.name)
            handle.write(content.encode("utf-8"))
        staged.chmod(0o644)
        os.replace(staged, config_path)
        try:
            os.replace(legacy_path, archive_path)
        except OSError as error:
            config_path.unlink(missing_ok=True)
            return ToolResult(
                "agent-assets.sync",
                integration,
                "invalid",
                findings=(
                    Finding(
                        "CONCORDE-AGENT-ASSET-001",
                        "error",
                        adopt_action["archive"],
                        f"could not archive legacy reflection config: {error}",
                        "Resolve the archive path conflict and re-run agent-asset sync.",
                    ),
                ),
                result=preview.result,
            )
        config_adopted = True
    elif not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        default = _read_json(asset_root / "config.default.json", "reflection-triage default config")
        config_path.write_text(json.dumps(default, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        config_created = True
    ignore_path = project_root / IGNORE_PATH
    ignore_created = False
    if not ignore_path.exists():
        ignore_path.parent.mkdir(parents=True, exist_ok=True)
        ignore_path.write_text("plans/\nworktrees/\nlegacy-*\n", encoding="utf-8")
        ignore_created = True

    receipt = _load_receipt(project_root)
    roles = projection_roles(asset_root, integration)
    receipt["integrations"][integration] = {
        "concorde_version": concorde_version,
        "source_digest": source_digest(asset_root),
        "outputs": [
            {
                "path": relative,
                "sha256": _sha256_file(project_root / relative),
                "role": roles[relative],
            }
            for relative in sorted(desired)
        ],
    }
    _write_receipt(project_root, receipt)
    changed = (
        config_created
        or config_adopted
        or ignore_created
        or any(item["action"] not in {"unchanged"} for item in actions)
    )
    return ToolResult(
        "agent-assets.sync",
        integration,
        "success" if changed else "unchanged",
        artifacts=tuple(sorted({*desired, CONFIG_PATH, IGNORE_PATH, RECEIPT_PATH})),
        result={
            **preview.result,
            "config_created": config_created,
            "config_adopted": config_adopted,
            "ignore_created": ignore_created,
        },
    )


def verify_agent_assets(project_root: Path, asset_root: Path, integration: str) -> ToolResult:
    try:
        desired = render_projection(asset_root, integration)
        receipt = _load_receipt(project_root)
        prior = _prior_outputs(receipt, integration)
        findings: list[Finding] = []
        for relative, content in desired.items():
            expected = _sha256_bytes(content.encode("utf-8"))
            path = project_root / relative
            if not path.is_file() or path.is_symlink() or _sha256_file(path) != expected or prior.get(relative) != expected:
                findings.append(
                    Finding(
                        "CONCORDE-AGENT-ASSET-003",
                        "error",
                        relative,
                        "Projected agent asset is missing, modified, stale, or unowned.",
                        "Run agent-assets sync after resolving any ownership conflict.",
                    )
                )
        if not (project_root / CONFIG_PATH).is_file():
            findings.append(
                Finding(
                    "CONCORDE-AGENT-ASSET-004",
                    "error",
                    CONFIG_PATH,
                    "Shared reflection-triage configuration is missing.",
                    "Run agent-assets sync to seed the default configuration.",
                )
            )
        return ToolResult(
            "agent-assets.verify",
            integration,
            "invalid" if findings else "success",
            artifacts=tuple(sorted(desired)),
            findings=tuple(findings),
            result={"integration": integration, "outputs": sorted(desired)},
        )
    except AgentAssetError as error:
        return ToolResult(
            "agent-assets.verify",
            integration,
            "invalid",
            findings=(Finding("CONCORDE-AGENT-ASSET-002", "error", RECEIPT_PATH, str(error), "Repair the receipt or canonical assets."),),
        )


def remove_agent_assets(project_root: Path, integration: str) -> ToolResult:
    try:
        receipt = _load_receipt(project_root)
        prior = _prior_outputs(receipt, integration)
        actions = _projection_actions(project_root, {}, prior)
        conflicts = [item for item in actions if item["action"] == "conflict"]
        if conflicts:
            return ToolResult(
                "agent-assets.remove",
                integration,
                "conflict",
                findings=tuple(
                    Finding(
                        "CONCORDE-AGENT-ASSET-001",
                        "error",
                        item["path"],
                        item["reason"],
                        "Preserve or explicitly resolve the modified file before removal.",
                    )
                    for item in conflicts
                ),
                result={"integration": integration, "actions": actions},
            )
        for item in actions:
            if item["action"] == "remove":
                (project_root / item["path"]).unlink()
        receipt["integrations"].pop(integration, None)
        _write_receipt(project_root, receipt)
        return ToolResult(
            "agent-assets.remove",
            integration,
            "success" if prior else "unchanged",
            artifacts=(RECEIPT_PATH,),
            result={"integration": integration, "actions": actions},
        )
    except AgentAssetError as error:
        return ToolResult(
            "agent-assets.remove",
            integration,
            "invalid",
            findings=(Finding("CONCORDE-AGENT-ASSET-002", "error", RECEIPT_PATH, str(error), "Repair the receipt before removal."),),
        )
