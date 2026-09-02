"""Deterministic rendering and ownership of installed reflection-triage agent assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .model import Finding, OperationResult


RECEIPT_PATH = ".specify/concorde-agent-assets.json"
CONFIG_PATH = ".concorde/reflections/config.json"
IGNORE_PATH = ".concorde/reflections/.gitignore"
LEGACY_CONFIG = ".claude/reflections.config.json"
LEGACY_PLANS = ".claude/reflection-plans"


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
    if value.get("schema_version") != 1 or value.get("protocol") != "reflection-triage/v3":
        raise AgentAssetError("agent-asset manifest must declare schema_version 1 and reflection-triage/v3")
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


def _roles(asset_root: Path, integration: str) -> dict[str, str]:
    manifest = _manifest(asset_root)
    return {
        _safe_relative(str(item["target"]), "projection target"): str(item["role"])
        for item in manifest["integrations"][integration]["outputs"]
    }


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


def _legacy_conflicts(project_root: Path) -> list[dict[str, str]]:
    if (project_root / CONFIG_PATH).exists():
        return []
    conflicts = []
    for relative in (LEGACY_CONFIG, LEGACY_PLANS):
        if (project_root / relative).exists():
            conflicts.append(
                {
                    "path": CONFIG_PATH,
                    "action": "conflict",
                    "reason": f"legacy state exists at {relative}; adopt or migrate it explicitly",
                }
            )
    return conflicts[:1]


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
) -> OperationResult:
    try:
        desired = render_projection(asset_root, integration)
        receipt = _load_receipt(project_root)
        actions = _projection_actions(project_root, desired, _prior_outputs(receipt, integration))
        actions.extend(_legacy_conflicts(project_root))
        conflicts = [item for item in actions if item["action"] == "conflict"]
        return OperationResult(
            "agent-assets.preview",
            integration,
            "conflict" if conflicts else "proposal",
            result={
                "integration": integration,
                "concorde_version": concorde_version,
                "source_digest": source_digest(asset_root),
                "outputs": sorted(desired),
                "actions": actions,
            },
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
        return OperationResult(
            "agent-assets.preview",
            integration,
            "invalid",
            findings=(
                Finding(
                    "CONCORDE-AGENT-ASSET-002",
                    "error",
                    "extensions/concorde/agent-assets/reflections",
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
) -> OperationResult:
    preview = preview_agent_assets(project_root, asset_root, integration, concorde_version)
    if preview.status in {"conflict", "invalid", "failed"}:
        return OperationResult(
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
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        default = _read_json(asset_root / "config.default.json", "reflection-triage default config")
        config_path.write_text(json.dumps(default, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        config_created = True
    ignore_path = project_root / IGNORE_PATH
    ignore_created = False
    if not ignore_path.exists():
        ignore_path.parent.mkdir(parents=True, exist_ok=True)
        ignore_path.write_text("plans/\nworktrees/\n", encoding="utf-8")
        ignore_created = True

    receipt = _load_receipt(project_root)
    roles = _roles(asset_root, integration)
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
    changed = config_created or ignore_created or any(item["action"] not in {"unchanged"} for item in actions)
    return OperationResult(
        "agent-assets.sync",
        integration,
        "success" if changed else "unchanged",
        artifacts=tuple(sorted({*desired, CONFIG_PATH, IGNORE_PATH, RECEIPT_PATH})),
        result={**preview.result, "config_created": config_created, "ignore_created": ignore_created},
    )


def verify_agent_assets(project_root: Path, asset_root: Path, integration: str) -> OperationResult:
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
        return OperationResult(
            "agent-assets.verify",
            integration,
            "invalid" if findings else "success",
            artifacts=tuple(sorted(desired)),
            findings=tuple(findings),
            result={"integration": integration, "outputs": sorted(desired)},
        )
    except AgentAssetError as error:
        return OperationResult(
            "agent-assets.verify",
            integration,
            "invalid",
            findings=(Finding("CONCORDE-AGENT-ASSET-002", "error", RECEIPT_PATH, str(error), "Repair the receipt or canonical assets."),),
        )


def remove_agent_assets(project_root: Path, integration: str) -> OperationResult:
    try:
        receipt = _load_receipt(project_root)
        prior = _prior_outputs(receipt, integration)
        actions = _projection_actions(project_root, {}, prior)
        conflicts = [item for item in actions if item["action"] == "conflict"]
        if conflicts:
            return OperationResult(
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
        return OperationResult(
            "agent-assets.remove",
            integration,
            "success" if prior else "unchanged",
            artifacts=(RECEIPT_PATH,),
            result={"integration": integration, "actions": actions},
        )
    except AgentAssetError as error:
        return OperationResult(
            "agent-assets.remove",
            integration,
            "invalid",
            findings=(Finding("CONCORDE-AGENT-ASSET-002", "error", RECEIPT_PATH, str(error), "Repair the receipt before removal."),),
        )
