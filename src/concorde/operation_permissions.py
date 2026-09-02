"""Normalized least-privilege policies and Codex/Claude native renderers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Literal, Mapping

from .skill_assets import EffectDeclaration, PATH_ROLES


class PermissionPolicyError(ValueError):
    """A requested or effective agent policy would widen declared authority."""


@dataclass(frozen=True)
class PolicyBinding:
    operation: str
    stage: str
    occurrence: int
    capability: str
    agent: str
    read_roles: tuple[str, ...] | None = None
    write_roles: tuple[str, ...] | None = None
    network: bool | None = None
    credentials: Literal["none", "declared"] | None = None


@dataclass(frozen=True)
class NormalizedPolicy:
    operation: str
    stage: str
    occurrence: int
    capability: str
    agent: str
    read_paths: tuple[str, ...]
    write_paths: tuple[str, ...]
    deny_paths: tuple[str, ...]
    default_deny: bool
    network_enabled: bool
    credentials: Literal["none", "declared"]
    outer_sandbox_required: bool
    digest: str


@dataclass(frozen=True)
class CodexLaunchConfiguration:
    integration: Literal["codex"]
    permission_profile: str
    approval_policy: Literal["never"]
    strict_config: bool
    argv: tuple[str, ...]
    configuration: Mapping[str, Any]
    effective_read_paths: tuple[str, ...]
    effective_write_paths: tuple[str, ...]
    effective_deny_paths: tuple[str, ...]
    default_deny: bool
    network_enabled: bool
    credentials: Literal["none", "declared"]
    policy_digest: str
    enforcement: str
    outer_sandbox: str | None
    digest: str


@dataclass(frozen=True)
class ClaudeLaunchConfiguration:
    integration: Literal["claude"]
    settings_json: str
    permission_mode: Literal["dontAsk"]
    argv: tuple[str, ...]
    effective_read_paths: tuple[str, ...]
    effective_write_paths: tuple[str, ...]
    effective_deny_paths: tuple[str, ...]
    default_deny: bool
    network_enabled: bool
    credentials: Literal["none", "declared"]
    policy_digest: str
    enforcement: str
    outer_sandbox: str | None
    digest: str


NativeLaunchConfiguration = CodexLaunchConfiguration | ClaudeLaunchConfiguration


@dataclass(frozen=True)
class LaunchSpecification:
    operation: str
    stage: str
    occurrence: int
    capability: str
    integration: Literal["codex", "claude"]
    agent: str
    project_root: str
    request: str
    prompt: str
    prior_results: tuple[str, ...]
    workspace_digest: str
    policy: NormalizedPolicy
    native_configuration: NativeLaunchConfiguration
    digest: str


@dataclass(frozen=True)
class EnforcementReceipt:
    launch_digest: str
    policy_digest: str
    config_digest: str
    integration: Literal["codex", "claude"]
    client_version: str
    enforcement: str
    exit_code: int
    status: Literal["success", "failed"]
    limitations: str = "none"


@dataclass(frozen=True)
class OperationExecutionResult:
    output: str
    receipt: EnforcementReceipt


_CREDENTIAL_DENIES = (
    ".env",
    ".aws",
    ".config/gcloud",
    ".npmrc",
    ".pypirc",
    ".ssh",
)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PermissionPolicyError(f"policy path must be project-relative POSIX: {value!r}")
    candidate = PurePosixPath(value.rstrip("/"))
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise PermissionPolicyError(f"policy path must be project-relative POSIX: {value!r}")
    return candidate.as_posix()


def _paths(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(_path(value) for value in values)))


def _under(path: str, parent: str) -> bool:
    candidate = PurePosixPath(path)
    root = PurePosixPath(parent)
    return candidate == root or root in candidate.parents


def _role_selection(
    effect_roles: tuple[str, ...],
    requested: tuple[str, ...] | None,
    label: str,
) -> tuple[str, ...]:
    selected = effect_roles if requested is None else requested
    if len(selected) != len(set(selected)):
        raise PermissionPolicyError(f"binding {label} roles contain duplicates")
    unknown = sorted(set(selected) - PATH_ROLES)
    if unknown:
        raise PermissionPolicyError(f"binding {label} roles contain unknown path roles: {unknown}")
    widened = sorted(set(selected) - set(effect_roles))
    if widened:
        raise PermissionPolicyError(f"binding widens {label} roles beyond leaf effects: {widened}")
    return tuple(selected)


def compile_policy(
    effects: EffectDeclaration,
    binding: PolicyBinding,
    role_paths: Mapping[str, tuple[str, ...]],
    *,
    deny_paths: tuple[str, ...] = (),
    outer_sandbox_required: bool = False,
) -> NormalizedPolicy:
    """Compile one narrowing binding and concrete role map into a frozen policy."""

    reads = _role_selection(effects.reads, binding.read_roles, "read")
    writes = _role_selection(effects.writes, binding.write_roles, "write")
    if not set(writes).issubset(reads):
        raise PermissionPolicyError("binding write roles must also be selected read roles")
    required_roles = tuple(dict.fromkeys((*reads, *writes)))
    missing = [role for role in required_roles if role not in role_paths]
    if missing:
        raise PermissionPolicyError(f"unknown path role in permission context: {missing}")
    read_paths = _paths([path for role in reads for path in role_paths[role]])
    write_paths = _paths([path for role in writes for path in role_paths[role]])
    for writable in write_paths:
        if not any(_under(writable, readable) or _under(readable, writable) for readable in read_paths):
            raise PermissionPolicyError(f"write path is not covered by readable authority: {writable}")
    network = effects.network if binding.network is None else binding.network
    if network and not effects.network:
        raise PermissionPolicyError("binding network request widens leaf effects")
    credentials = effects.credentials if binding.credentials is None else binding.credentials
    if credentials == "declared" and effects.credentials == "none":
        raise PermissionPolicyError("binding credential request widens leaf effects")
    denied = _paths([*deny_paths, *_CREDENTIAL_DENIES])
    payload = {
        "binding": {
            "operation": binding.operation,
            "stage": binding.stage,
            "occurrence": binding.occurrence,
            "capability": binding.capability,
            "agent": binding.agent,
        },
        "read_paths": read_paths,
        "write_paths": write_paths,
        "deny_paths": denied,
        "default_deny": True,
        "network_enabled": network,
        "credentials": credentials,
        "outer_sandbox_required": outer_sandbox_required,
    }
    return NormalizedPolicy(
        operation=binding.operation,
        stage=binding.stage,
        occurrence=binding.occurrence,
        capability=binding.capability,
        agent=binding.agent,
        read_paths=read_paths,
        write_paths=write_paths,
        deny_paths=denied,
        default_deny=True,
        network_enabled=network,
        credentials=credentials,
        outer_sandbox_required=outer_sandbox_required,
        digest=_digest(payload),
    )


def verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None:
    """Reject native/managed/user configuration that widens the Operation policy."""

    if any(not any(_under(path, root) for root in declared.read_paths) for path in effective.read_paths):
        raise PermissionPolicyError("effective configuration widens readable paths")
    if any(not any(_under(path, root) for root in declared.write_paths) for path in effective.write_paths):
        raise PermissionPolicyError("effective configuration widens writable paths")
    if declared.default_deny and not effective.default_deny:
        raise PermissionPolicyError("effective configuration widens default-deny posture")
    if not set(declared.deny_paths).issubset(effective.deny_paths):
        raise PermissionPolicyError("effective configuration removes declared deny paths")
    if effective.network_enabled and not declared.network_enabled:
        raise PermissionPolicyError("effective configuration widens network access")
    if effective.credentials == "declared" and declared.credentials == "none":
        raise PermissionPolicyError("effective configuration widens credential access")


def _codex_rules(policy: NormalizedPolicy) -> dict[str, str]:
    rules: dict[str, str] = {":root": "deny", ":minimal": "read", ":tmpdir": "deny", ":slash_tmp": "deny"}
    for path in policy.read_paths:
        rules[path] = "read"
    for path in policy.write_paths:
        rules[path] = "write"
    for path in policy.deny_paths:
        rules[path] = "deny"
    return rules


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(value, separators=(",", ":"))


def render_codex_configuration(
    policy: NormalizedPolicy,
    *,
    native_enforcement: bool,
    outer_sandbox: str | None = None,
) -> CodexLaunchConfiguration:
    if not native_enforcement and not outer_sandbox:
        raise PermissionPolicyError(
            "Codex native permission-profile enforcement is unavailable and no outer enforcement was verified"
        )
    profile = "concorde-" + policy.digest.removeprefix("sha256:")[:16]
    configuration = {
        "default_permissions": profile,
        "approval_policy": "never",
        "permissions": {
            profile: {
                "workspace_roots": {".": True},
                "filesystem": {":workspace_roots": _codex_rules(policy)},
                "network": {"enabled": policy.network_enabled, "domains": {}},
            }
        },
        "features": {"network_proxy": policy.network_enabled},
    }
    argv: list[str] = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--ask-for-approval",
        "never",
    ]
    if native_enforcement:
        argv.extend(("-c", f"default_permissions={_toml_value(profile)}"))
        argv.extend(("-c", 'approval_policy="never"'))
        argv.extend(("-c", f'permissions.{profile}.workspace_roots."."=true'))
        for path, access in _codex_rules(policy).items():
            key = json.dumps(path)
            argv.extend(("-c", f'permissions.{profile}.filesystem.":workspace_roots".{key}={_toml_value(access)}'))
        argv.extend(("-c", f"permissions.{profile}.network.enabled={_toml_value(policy.network_enabled)}"))
    argv.append("-")
    payload = {
        "integration": "codex",
        "profile": profile,
        "configuration": configuration if native_enforcement else {},
        "argv": argv,
        "policy_digest": policy.digest,
        "enforcement": "native" if native_enforcement else "outer",
        "outer_sandbox": outer_sandbox,
    }
    return CodexLaunchConfiguration(
        integration="codex",
        permission_profile=profile,
        approval_policy="never",
        strict_config=True,
        argv=tuple(argv),
        configuration=configuration if native_enforcement else {},
        effective_read_paths=policy.read_paths,
        effective_write_paths=policy.write_paths,
        effective_deny_paths=policy.deny_paths,
        default_deny=policy.default_deny,
        network_enabled=policy.network_enabled,
        credentials=policy.credentials,
        policy_digest=policy.digest,
        enforcement="native" if native_enforcement else "outer",
        outer_sandbox=outer_sandbox,
        digest=_digest(payload),
    )


def _claude_rule(tool: str, path: str) -> str:
    return f"{tool}(./{path})"


def render_claude_configuration(
    policy: NormalizedPolicy,
    *,
    native_enforcement: bool,
    outer_sandbox: str | None = None,
) -> ClaudeLaunchConfiguration:
    if not native_enforcement and not outer_sandbox:
        raise PermissionPolicyError(
            "Claude native sandbox enforcement is unavailable and no outer enforcement was verified"
        )
    allow = [_claude_rule("Read", path) for path in policy.read_paths]
    for path in policy.write_paths:
        allow.extend((_claude_rule("Edit", path), _claude_rule("Write", path)))
    deny: list[str] = []
    for path in policy.deny_paths:
        deny.extend(
            (
                _claude_rule("Read", path),
                _claude_rule("Edit", path),
                _claude_rule("Write", path),
            )
        )
    if not policy.network_enabled:
        deny.extend(("WebFetch", "WebSearch"))
    settings = {
        "permissions": {
            "defaultMode": "dontAsk",
            "allow": sorted(dict.fromkeys(allow)),
            "ask": [],
            "deny": sorted(dict.fromkeys(deny)),
            "disableBypassPermissionsMode": "disable",
        },
        "sandbox": {
            "enabled": native_enforcement,
            "failIfUnavailable": native_enforcement,
            "autoAllowBashIfSandboxed": native_enforcement,
            "excludedCommands": [],
            "allowUnsandboxedCommands": False,
            "enableWeakerNestedSandbox": False,
            "filesystem": {
                "denyRead": ["/", "~", "."],
                "allowRead": list(policy.read_paths),
                "denyWrite": ["/", "~", ".", *policy.deny_paths],
                "allowWrite": list(policy.write_paths),
            },
            "network": {
                "allowedDomains": ["*"] if policy.network_enabled else [],
                "allowManagedDomainsOnly": not policy.network_enabled,
                "allowUnixSockets": [],
                "allowAllUnixSockets": False,
            },
        },
    }
    settings_json = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    argv = (
        "claude",
        "-p",
        "--restricted",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--settings",
        settings_json,
    )
    payload = {
        "integration": "claude",
        "settings": settings,
        "argv": argv,
        "policy_digest": policy.digest,
        "enforcement": "native" if native_enforcement else "outer",
        "outer_sandbox": outer_sandbox,
    }
    return ClaudeLaunchConfiguration(
        integration="claude",
        settings_json=settings_json,
        permission_mode="dontAsk",
        argv=argv,
        effective_read_paths=policy.read_paths,
        effective_write_paths=policy.write_paths,
        effective_deny_paths=policy.deny_paths,
        default_deny=policy.default_deny,
        network_enabled=policy.network_enabled,
        credentials=policy.credentials,
        policy_digest=policy.digest,
        enforcement="native" if native_enforcement else "outer",
        outer_sandbox=outer_sandbox,
        digest=_digest(payload),
    )


def compare_effective_boundaries(
    first: NativeLaunchConfiguration,
    second: NativeLaunchConfiguration,
) -> bool:
    return (
        first.effective_read_paths,
        first.effective_write_paths,
        first.effective_deny_paths,
        first.default_deny,
        first.network_enabled,
        first.credentials,
    ) == (
        second.effective_read_paths,
        second.effective_write_paths,
        second.effective_deny_paths,
        second.default_deny,
        second.network_enabled,
        second.credentials,
    )


def build_launch_specification(
    *,
    operation: str,
    stage: str,
    occurrence: int,
    capability: str,
    integration: Literal["codex", "claude"],
    agent: str,
    project_root: str,
    request: str,
    prompt: str,
    prior_results: tuple[str, ...],
    workspace_digest: str,
    policy: NormalizedPolicy,
    native_configuration: NativeLaunchConfiguration,
) -> LaunchSpecification:
    if native_configuration.integration != integration:
        raise PermissionPolicyError("native configuration integration differs from launch integration")
    if native_configuration.policy_digest != policy.digest:
        raise PermissionPolicyError("native configuration policy digest is stale")
    if (operation, stage, occurrence, capability, agent) != (
        policy.operation,
        policy.stage,
        policy.occurrence,
        policy.capability,
        policy.agent,
    ):
        raise PermissionPolicyError("launch identity differs from normalized policy binding")
    payload = {
        "operation": operation,
        "stage": stage,
        "occurrence": occurrence,
        "capability": capability,
        "integration": integration,
        "agent": agent,
        "project_root": project_root,
        "request": request,
        "prompt": prompt,
        "prior_results": prior_results,
        "workspace_digest": workspace_digest,
        "policy_digest": policy.digest,
        "config_digest": native_configuration.digest,
    }
    return LaunchSpecification(
        operation=operation,
        stage=stage,
        occurrence=occurrence,
        capability=capability,
        integration=integration,
        agent=agent,
        project_root=project_root,
        request=request,
        prompt=prompt,
        prior_results=prior_results,
        workspace_digest=workspace_digest,
        policy=policy,
        native_configuration=native_configuration,
        digest=_digest(payload),
    )
