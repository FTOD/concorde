"""Injectable real Codex/Claude process handoff with enforcement receipts."""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .operation_permissions import (
    EnforcementReceipt,
    LaunchSpecification,
    OperationExecutionResult,
)


class OperationExecutionError(RuntimeError):
    """Agent process preflight or execution failed without a permissive retry."""

    def __init__(self, message: str, receipt: EnforcementReceipt | None = None):
        super().__init__(message)
        self.receipt = receipt


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
VersionProbe = Callable[[str, str], str]

_SAFE_ENVIRONMENT = frozenset(
    {
        "COMSPEC",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USER",
        "WINDIR",
    }
)
_VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?")


def _default_runner(
    argv: tuple[str, ...],
    *,
    cwd: str,
    env: Mapping[str, str],
    input_text: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=dict(env),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _default_version_probe(integration: str, executable: str) -> str:
    result = subprocess.run(
        (executable, "--version"),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return ""
    return (result.stdout or result.stderr).strip()


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = _VERSION.search(value)
    if match is None:
        return None
    return tuple(int(item or 0) for item in match.groups())  # type: ignore[return-value]


def _prompt(specification: LaunchSpecification) -> str:
    prior = "\n".join(
        f"{index + 1}. {result}" for index, result in enumerate(specification.prior_results)
    ) or "(none)"
    return (
        f"Operation: {specification.operation}\n"
        f"Stage: {specification.stage}\n"
        f"Capability: {specification.capability}\n"
        f"Request:\n{specification.request}\n\n"
        f"Prior results:\n{prior}\n\n"
        f"Canonical capability prompt:\n{specification.prompt}"
    )


def _exact_effective_boundary(specification: LaunchSpecification) -> bool:
    config = specification.native_configuration
    policy = specification.policy
    return (
        config.effective_read_paths,
        config.effective_write_paths,
        config.effective_deny_paths,
        config.default_deny,
        config.network_enabled,
        config.credentials,
    ) == (
        policy.read_paths,
        policy.write_paths,
        policy.deny_paths,
        policy.default_deny,
        policy.network_enabled,
        policy.credentials,
    )


@dataclass(frozen=True)
class AgentProcessExecutor:
    """Execute one immutable launch specification through an injected subprocess runner."""

    runner: ProcessRunner = _default_runner
    version_probe: VersionProbe = _default_version_probe
    environment: Mapping[str, str] | None = None

    def _preflight(self, specification: LaunchSpecification) -> str:
        config = specification.native_configuration
        if config.integration != specification.integration:
            raise OperationExecutionError("launch integration differs from native configuration")
        if config.policy_digest != specification.policy.digest:
            raise OperationExecutionError("native configuration policy digest is stale")
        if config.enforcement not in {"native", "outer"}:
            raise OperationExecutionError("launch has no verified enforcement boundary")
        if config.enforcement == "outer" and not config.outer_sandbox:
            raise OperationExecutionError("outer enforcement receipt has no provider identity")
        if not _exact_effective_boundary(specification):
            raise OperationExecutionError("native effective boundary differs from normalized policy")
        executable = config.argv[0] if config.argv else ""
        expected = "codex" if specification.integration == "codex" else "claude"
        if executable != expected:
            raise OperationExecutionError(
                f"native executable {executable!r} does not match {specification.integration}"
            )
        try:
            version = self.version_probe(specification.integration, executable).strip()
        except Exception as error:  # pragma: no cover - exact probe backend is host-owned
            raise OperationExecutionError(f"client version preflight failed: {error}") from error
        if not version:
            raise OperationExecutionError("client version preflight returned no supported version")
        parsed = _version_tuple(version)
        if config.enforcement == "native" and parsed is not None:
            minimum = (0, 138, 0) if specification.integration == "codex" else (2, 1, 248)
            if parsed < minimum:
                raise OperationExecutionError(
                    f"client version preflight requires {expected}>={'.'.join(map(str, minimum))}"
                )
        return version

    def __call__(self, specification: LaunchSpecification) -> OperationExecutionResult:
        version = self._preflight(specification)
        config = specification.native_configuration
        source_environment = os.environ if self.environment is None else self.environment
        environment = {
            key: value
            for key, value in sorted(source_environment.items())
            if key in _SAFE_ENVIRONMENT and isinstance(value, str)
        }
        prompt = _prompt(specification)
        argv = config.argv
        if specification.integration == "claude":
            argv = (*argv, "Execute the complete bounded request supplied on stdin.")
        try:
            completed = self.runner(
                tuple(argv),
                cwd=specification.project_root,
                env=environment,
                input_text=prompt,
            )
        except Exception as error:
            raise OperationExecutionError(f"agent process launch failed: {error}") from error
        if not isinstance(completed, subprocess.CompletedProcess):
            raise OperationExecutionError("agent process runner returned an invalid result")
        status = "success" if completed.returncode == 0 else "failed"
        limitations = (
            "none"
            if completed.returncode == 0
            else (completed.stderr or completed.stdout or "process failed without diagnostics").strip()
        )
        receipt = EnforcementReceipt(
            launch_digest=specification.digest,
            policy_digest=specification.policy.digest,
            config_digest=config.digest,
            integration=specification.integration,
            client_version=version,
            enforcement=config.enforcement,
            exit_code=completed.returncode,
            status=status,
            limitations=limitations,
        )
        if completed.returncode:
            raise OperationExecutionError(
                f"{specification.integration} process exited with exit {completed.returncode}: {limitations}",
                receipt,
            )
        return OperationExecutionResult(
            output=(completed.stdout or "").strip(),
            receipt=receipt,
        )
