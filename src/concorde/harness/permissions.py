"""Least-privilege policy compilation for worker invocations.

``compile_policy`` intersects an WorkerProfile contract's declared effects with a host-issued, narrowing
binding and the concrete role paths the host supplies, producing one digest-bound
``NormalizedPolicy``. The Pi worker runtime enforces that policy's read and write grants through
the Concorde worker extension (see ``pi_worker``); nothing here launches a process.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Literal

from .effects import PATH_ROLES, EffectDeclaration


class PermissionPolicyError(ValueError):
    """A requested or effective policy would widen declared authority."""


# Read roles a policy map may omit, meaning the invocation declares no such paths.
OPTIONAL_ROLES = frozenset({"references"})


@dataclass(frozen=True)
class PolicyBinding:
    operation: str
    stage: str
    occurrence: int
    role: str
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
    role: str
    agent: str
    read_paths: tuple[str, ...]
    write_paths: tuple[str, ...]
    deny_paths: tuple[str, ...]
    default_deny: bool
    network_enabled: bool
    credentials: Literal["none", "declared"]
    outer_sandbox_required: bool
    digest: str


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
        raise PermissionPolicyError(
            f"policy path must be project-relative POSIX: {value!r}"
        )
    candidate = PurePosixPath(value.rstrip("/"))
    if candidate.is_absolute() or any(
        part in {"", ".", ".."} for part in candidate.parts
    ):
        raise PermissionPolicyError(
            f"policy path must be project-relative POSIX: {value!r}"
        )
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
        raise PermissionPolicyError(
            f"binding {label} roles contain unknown path roles: {unknown}"
        )
    widened = sorted(set(selected) - set(effect_roles))
    if widened:
        raise PermissionPolicyError(
            f"binding widens {label} roles beyond leaf effects: {widened}"
        )
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
        raise PermissionPolicyError(
            "binding write roles must also be selected read roles"
        )
    required_roles = tuple(dict.fromkeys((*reads, *writes)))
    # ``references`` is the one role whose absence from the map means "none declared": a contract
    # may read external references, but a Module need not declare any. Every other selected role
    # must be supplied explicitly.
    missing = [
        role
        for role in required_roles
        if role not in role_paths and role not in OPTIONAL_ROLES
    ]
    if missing:
        raise PermissionPolicyError(
            f"unknown path role in permission context: {missing}"
        )
    read_paths = _paths([path for role in reads for path in role_paths.get(role, ())])
    write_paths = _paths([path for role in writes for path in role_paths.get(role, ())])
    for writable in write_paths:
        if not any(
            _under(writable, readable) or _under(readable, writable)
            for readable in read_paths
        ):
            raise PermissionPolicyError(
                f"write path is not covered by readable authority: {writable}"
            )
    network = effects.network if binding.network is None else binding.network
    if network and not effects.network:
        raise PermissionPolicyError("binding network request widens leaf effects")
    credentials = (
        effects.credentials if binding.credentials is None else binding.credentials
    )
    if credentials == "declared" and effects.credentials == "none":
        raise PermissionPolicyError("binding credential request widens leaf effects")
    denied = _paths([*deny_paths, *_CREDENTIAL_DENIES])
    payload = {
        "binding": {
            "operation": binding.operation,
            "stage": binding.stage,
            "occurrence": binding.occurrence,
            "role": binding.role,
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
        role=binding.role,
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


def verify_effective_subset(
    declared: NormalizedPolicy, effective: NormalizedPolicy
) -> None:
    """Reject an effective policy that widens the declared one."""

    if any(
        not any(_under(path, root) for root in declared.read_paths)
        for path in effective.read_paths
    ):
        raise PermissionPolicyError("effective configuration widens readable paths")
    if any(
        not any(_under(path, root) for root in declared.write_paths)
        for path in effective.write_paths
    ):
        raise PermissionPolicyError("effective configuration widens writable paths")
    if declared.default_deny and not effective.default_deny:
        raise PermissionPolicyError(
            "effective configuration widens default-deny posture"
        )
    if not set(declared.deny_paths).issubset(effective.deny_paths):
        raise PermissionPolicyError(
            "effective configuration removes declared deny paths"
        )
    if effective.network_enabled and not declared.network_enabled:
        raise PermissionPolicyError("effective configuration widens network access")
    if effective.credentials == "declared" and declared.credentials == "none":
        raise PermissionPolicyError("effective configuration widens credential access")
