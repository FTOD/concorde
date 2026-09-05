"""Normalized least-privilege policies and Codex/Claude native renderers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
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
class RuntimeBootstrapFile:
    """One host-attested client runtime file admitted outside task authority."""

    path: str
    sha256: str
    size: int
    mode: int
    owner: int | None
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
    runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]
    runtime_bootstrap_digest: str
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
    runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]
    runtime_bootstrap_digest: str
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
    workspace_receipt_json: str
    workspace_digest: str
    policy: NormalizedPolicy
    native_configuration: NativeLaunchConfiguration
    digest: str
    runtime_input_json: str | None = None
    operation_configuration_json: str | None = None
    invocation_id: str | None = None


@dataclass(frozen=True)
class EnforcementReceipt:
    requested_launch_digest: str
    launch_digest: str
    policy_digest: str
    config_digest: str
    integration: Literal["codex", "claude"]
    client_version: str
    enforcement: str
    exit_code: int
    status: Literal["success", "failed"]
    runtime_bootstrap_digest: str
    completion_schema_version: int
    completion_status: Literal["success", "failed"]
    limitations: str = "none"


@dataclass(frozen=True)
class CompletionGate:
    name: str
    status: Literal["passed", "failed"]
    evidence: str


@dataclass(frozen=True)
class CapabilityCompletion:
    schema_version: int
    operation: str
    stage: str
    occurrence: int
    capability: str
    launch_digest: str
    workspace_digest: str
    runtime_bootstrap_digest: str
    status: Literal["success", "failed"]
    output: str
    limitations: str
    gates: tuple[CompletionGate, ...]
    domain_output: dict[str, Any] | None = None
    invocation_id: str | None = None


@dataclass(frozen=True)
class OperationExecutionResult:
    output: str
    receipt: EnforcementReceipt
    completion: CapabilityCompletion
    domain_output: dict[str, Any] | None = None


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


def runtime_bootstrap_file(
    *,
    path: str,
    sha256: str,
    size: int,
    mode: int,
    owner: int | None,
) -> RuntimeBootstrapFile:
    """Create one immutable attestation whose digest covers every trusted property."""

    if not path or not isinstance(path, str):
        raise PermissionPolicyError("runtime bootstrap path must be a non-empty string")
    if (
        not isinstance(sha256, str)
        or not sha256.startswith("sha256:")
        or len(sha256) != 71
        or any(character not in "0123456789abcdef" for character in sha256[7:])
    ):
        raise PermissionPolicyError("runtime bootstrap sha256 must be canonical")
    if not isinstance(size, int) or size <= 0:
        raise PermissionPolicyError("runtime bootstrap size must be positive")
    if not isinstance(mode, int) or mode < 0:
        raise PermissionPolicyError("runtime bootstrap mode must be non-negative")
    if owner is not None and (not isinstance(owner, int) or owner < 0):
        raise PermissionPolicyError("runtime bootstrap owner must be a non-negative integer")
    payload = {"path": path, "sha256": sha256, "size": size, "mode": mode, "owner": owner}
    return RuntimeBootstrapFile(**payload, digest=_digest(payload))


def runtime_bootstrap_digest(files: tuple[RuntimeBootstrapFile, ...]) -> str:
    return _digest([asdict(item) for item in files])


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
    rules: dict[str, str] = {}
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
    if isinstance(value, str):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, Mapping):
        keys = tuple(value)
        if any(not isinstance(key, str) for key in keys):
            raise PermissionPolicyError("Codex permission-profile TOML keys must be strings")
        return "{" + ",".join(
            f"{_toml_value(key)}={_toml_value(value[key])}" for key in sorted(keys)
        ) + "}"
    raise PermissionPolicyError(
        f"unsupported Codex permission-profile TOML value: {type(value).__name__}"
    )


def _codex_argv(
    profile: str,
    profile_configuration: Mapping[str, Any],
    network: bool,
    *,
    executable: str = "codex",
) -> tuple[str, ...]:
    return (
        executable,
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "-c",
        f"default_permissions={_toml_value(profile)}",
        "-c",
        'approval_policy="never"',
        "-c",
        f"permissions.{profile}={_toml_value(profile_configuration)}",
        "-c",
        f"features.network_proxy={_toml_value(network)}",
        "-",
    )


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
    profile_configuration = {
        "workspace_roots": {".": True},
        "filesystem": {
            ":root": "deny",
            ":minimal": "read",
            ":tmpdir": "deny",
            ":slash_tmp": "deny",
            ":workspace_roots": _codex_rules(policy),
        },
        "network": {"enabled": policy.network_enabled, "domains": {}},
    }
    configuration = {
        "default_permissions": profile,
        "approval_policy": "never",
        "permissions": {profile: profile_configuration},
        "features": {"network_proxy": policy.network_enabled},
    }
    argv = (
        _codex_argv(profile, profile_configuration, policy.network_enabled)
        if native_enforcement
        else ("codex", "--ask-for-approval", "never", "exec", "--ephemeral", "--ignore-user-config", "--strict-config", "-")
    )
    bootstrap: tuple[RuntimeBootstrapFile, ...] = ()
    bootstrap_digest = runtime_bootstrap_digest(bootstrap)
    payload = {
        "integration": "codex",
        "profile": profile,
        "configuration": configuration if native_enforcement else {},
        "argv": argv,
        "policy_digest": policy.digest,
        "enforcement": "native" if native_enforcement else "outer",
        "outer_sandbox": outer_sandbox,
        "runtime_bootstrap": [],
        "runtime_bootstrap_digest": bootstrap_digest,
    }
    return CodexLaunchConfiguration(
        integration="codex",
        permission_profile=profile,
        approval_policy="never",
        strict_config=True,
        argv=argv,
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
        runtime_bootstrap=bootstrap,
        runtime_bootstrap_digest=bootstrap_digest,
        digest=_digest(payload),
    )


def finalize_codex_configuration(
    configuration: CodexLaunchConfiguration,
    runtime_bootstrap: tuple[RuntimeBootstrapFile, ...],
) -> CodexLaunchConfiguration:
    """Return the immutable native configuration after host runtime attestation."""

    if configuration.enforcement != "native":
        if runtime_bootstrap:
            raise PermissionPolicyError("outer Codex enforcement cannot add native runtime bootstrap files")
        return configuration
    if len(runtime_bootstrap) != 1:
        raise PermissionPolicyError("native Codex launch requires exactly one runtime bootstrap file")
    paths = [item.path for item in runtime_bootstrap]
    if len(paths) != len(set(paths)):
        raise PermissionPolicyError("Codex runtime bootstrap contains duplicate paths")
    profile = configuration.permission_profile
    source_profile = configuration.configuration.get("permissions", {}).get(profile)
    if not isinstance(source_profile, Mapping):
        raise PermissionPolicyError("Codex configuration has no matching named permission profile")
    profile_configuration = json.loads(json.dumps(source_profile))
    filesystem = profile_configuration.get("filesystem")
    if not isinstance(filesystem, dict):
        raise PermissionPolicyError("Codex permission profile has no filesystem table")
    for item in runtime_bootstrap:
        if item.path in filesystem and filesystem[item.path] != "read":
            raise PermissionPolicyError(f"runtime bootstrap conflicts with filesystem rule: {item.path}")
        filesystem[item.path] = "read"
    complete_configuration = json.loads(json.dumps(configuration.configuration))
    complete_configuration["permissions"][profile] = profile_configuration
    bootstrap_digest = runtime_bootstrap_digest(runtime_bootstrap)
    argv = _codex_argv(
        profile,
        profile_configuration,
        configuration.network_enabled,
        executable=runtime_bootstrap[0].path,
    )
    payload = {
        "integration": "codex",
        "profile": profile,
        "configuration": complete_configuration,
        "argv": argv,
        "policy_digest": configuration.policy_digest,
        "enforcement": configuration.enforcement,
        "outer_sandbox": configuration.outer_sandbox,
        "runtime_bootstrap": [asdict(item) for item in runtime_bootstrap],
        "runtime_bootstrap_digest": bootstrap_digest,
    }
    return replace(
        configuration,
        argv=argv,
        configuration=complete_configuration,
        runtime_bootstrap=runtime_bootstrap,
        runtime_bootstrap_digest=bootstrap_digest,
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
    bootstrap: tuple[RuntimeBootstrapFile, ...] = ()
    bootstrap_digest = runtime_bootstrap_digest(bootstrap)
    payload = {
        "integration": "claude",
        "settings": settings,
        "argv": argv,
        "policy_digest": policy.digest,
        "enforcement": "native" if native_enforcement else "outer",
        "outer_sandbox": outer_sandbox,
        "runtime_bootstrap": [],
        "runtime_bootstrap_digest": bootstrap_digest,
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
        runtime_bootstrap=bootstrap,
        runtime_bootstrap_digest=bootstrap_digest,
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
    workspace_receipt_json: str,
    workspace_digest: str,
    policy: NormalizedPolicy,
    native_configuration: NativeLaunchConfiguration,
    runtime_input_json: str | None = None,
    operation_configuration_json: str | None = None,
    invocation_id: str | None = None,
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
    try:
        workspace_receipt = json.loads(workspace_receipt_json)
    except json.JSONDecodeError as error:
        raise PermissionPolicyError("launch workspace receipt must be canonical JSON") from error
    if not isinstance(workspace_receipt, dict) or workspace_receipt.get("source_digest") != workspace_digest:
        raise PermissionPolicyError("launch workspace receipt does not match workspace digest")
    canonical_receipt = _canonical(workspace_receipt).decode("utf-8")
    if workspace_receipt_json != canonical_receipt:
        raise PermissionPolicyError("launch workspace receipt must use canonical serialization")
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
        "workspace_receipt": workspace_receipt,
        "workspace_digest": workspace_digest,
        "policy_digest": policy.digest,
        "config_digest": native_configuration.digest,
    }
    if (runtime_input_json is None) != (operation_configuration_json is None):
        raise PermissionPolicyError("structured launch requires both configuration and input")
    if runtime_input_json is not None:
        from .operation_data import canonical, decode, validate_typed

        runtime_input = validate_typed(decode(runtime_input_json))
        configuration = validate_typed(decode(operation_configuration_json), "concorde-operation-configuration")
        if runtime_input_json != canonical(runtime_input) or operation_configuration_json != canonical(configuration):
            raise PermissionPolicyError("structured launch data must use canonical serialization")
        if prior_results:
            raise PermissionPolicyError("structured launches cannot carry narrative prior results")
        if not isinstance(invocation_id, str) or not invocation_id:
            raise PermissionPolicyError("structured launch requires a host-issued invocation identity")
        payload["runtime_input"] = runtime_input
        payload["operation_configuration"] = configuration
        payload["invocation_id"] = invocation_id
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
        workspace_receipt_json=workspace_receipt_json,
        workspace_digest=workspace_digest,
        policy=policy,
        native_configuration=native_configuration,
        digest=_digest(payload),
        runtime_input_json=runtime_input_json,
        operation_configuration_json=operation_configuration_json,
        invocation_id=invocation_id,
    )


def finalize_launch_specification(
    specification: LaunchSpecification,
    runtime_bootstrap: tuple[RuntimeBootstrapFile, ...],
) -> LaunchSpecification:
    """Bind attested host bootstrap files into one final immutable launch."""

    native = specification.native_configuration
    if specification.integration == "codex":
        if not isinstance(native, CodexLaunchConfiguration):
            raise PermissionPolicyError("Codex launch has a non-Codex native configuration")
        native = finalize_codex_configuration(native, runtime_bootstrap)
    elif runtime_bootstrap:
        raise PermissionPolicyError("Claude launch cannot receive Codex runtime bootstrap files")
    return build_launch_specification(
        operation=specification.operation,
        stage=specification.stage,
        occurrence=specification.occurrence,
        capability=specification.capability,
        integration=specification.integration,
        agent=specification.agent,
        project_root=specification.project_root,
        request=specification.request,
        prompt=specification.prompt,
        prior_results=specification.prior_results,
        workspace_receipt_json=specification.workspace_receipt_json,
        workspace_digest=specification.workspace_digest,
        policy=specification.policy,
        native_configuration=native,
        runtime_input_json=specification.runtime_input_json,
        operation_configuration_json=specification.operation_configuration_json,
        invocation_id=specification.invocation_id,
    )
