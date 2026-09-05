"""Injectable real Codex/Claude process handoff with enforcement receipts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .operation_permissions import (
    CapabilityCompletion,
    CompletionGate,
    EnforcementReceipt,
    LaunchSpecification,
    OperationExecutionResult,
    RuntimeBootstrapFile,
    finalize_launch_specification,
    runtime_bootstrap_file,
)


class OperationExecutionError(RuntimeError):
    """Agent process preflight or execution failed without a permissive retry."""

    def __init__(self, message: str, receipt: EnforcementReceipt | None = None):
        super().__init__(message)
        self.receipt = receipt


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
VersionProbe = Callable[[str, str], str]
RuntimeBootstrapResolver = Callable[[str, str, str, Mapping[str, str]], tuple[RuntimeBootstrapFile, ...]]
RuntimeBootstrapVerifier = Callable[[tuple[RuntimeBootstrapFile, ...]], None]

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


def _completion_version(specification: LaunchSpecification) -> int:
    return 2 if specification.runtime_input_json is not None else 1


def _domain_type(specification: LaunchSpecification) -> str | None:
    if (specification.runtime_input_json is not None
            and specification.operation == "concorde-reflections-triage"
            and specification.capability == "concorde-analyze"):
        return "concorde-reflection-investigation-result"
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _is_native_executable(path: Path) -> bool:
    """Distinguish a self-contained native client from a script/package shim."""

    with path.open("rb") as stream:
        magic = stream.read(4)
    return (
        magic.startswith(b"\x7fELF")
        or magic.startswith(b"MZ")
        or magic
        in {
            b"\xfe\xed\xfa\xce",
            b"\xfe\xed\xfa\xcf",
            b"\xce\xfa\xed\xfe",
            b"\xcf\xfa\xed\xfe",
            b"\xca\xfe\xba\xbe",
            b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf",
            b"\xbf\xba\xfe\xca",
        }
    )


def resolve_runtime_bootstrap(
    integration: str,
    executable: str,
    project_root: str,
    environment: Mapping[str, str],
) -> tuple[RuntimeBootstrapFile, ...]:
    """Attest the selected native Codex binary without granting its package directory."""

    if integration != "codex":
        return ()
    selected = shutil.which(executable, path=environment.get("PATH"))
    if not selected:
        raise OperationExecutionError("Codex runtime bootstrap could not resolve the selected executable")
    try:
        path = Path(selected).resolve(strict=True)
        project = Path(project_root).resolve(strict=True)
        metadata = path.stat()
    except OSError as error:
        raise OperationExecutionError(f"Codex runtime bootstrap resolution failed: {error}") from error
    if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK):
        raise OperationExecutionError("Codex runtime bootstrap is not one executable regular file")
    try:
        native_executable = _is_native_executable(path)
    except OSError as error:
        raise OperationExecutionError(f"Codex runtime bootstrap inspection failed: {error}") from error
    if not native_executable:
        raise OperationExecutionError(
            "Codex runtime bootstrap must be a native executable, not a script or package shim"
        )
    if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise OperationExecutionError("Codex runtime bootstrap is group- or world-writable")
    current_owner = os.geteuid() if hasattr(os, "geteuid") else None
    if current_owner is not None and metadata.st_uid not in {0, current_owner}:
        raise OperationExecutionError("Codex runtime bootstrap has an untrusted owner")
    try:
        path.relative_to(project)
    except ValueError:
        pass
    else:
        raise OperationExecutionError("Codex runtime bootstrap must remain outside project authority")
    return (
        runtime_bootstrap_file(
            path=str(path),
            sha256=_file_sha256(path),
            size=metadata.st_size,
            mode=stat.S_IMODE(metadata.st_mode),
            owner=metadata.st_uid if hasattr(metadata, "st_uid") else None,
        ),
    )


def verify_runtime_bootstrap(files: tuple[RuntimeBootstrapFile, ...]) -> None:
    """Recheck attested native files immediately before host use."""

    for expected in files:
        try:
            path = Path(expected.path).resolve(strict=True)
            metadata = path.stat()
            native_executable = _is_native_executable(path)
            actual = runtime_bootstrap_file(
                path=str(path),
                sha256=_file_sha256(path),
                size=metadata.st_size,
                mode=stat.S_IMODE(metadata.st_mode),
                owner=metadata.st_uid if hasattr(metadata, "st_uid") else None,
            )
        except (OSError, ValueError) as error:
            raise OperationExecutionError(f"Codex runtime bootstrap recheck failed: {error}") from error
        if actual != expected:
            raise OperationExecutionError("Codex runtime bootstrap changed after attestation")
        if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK) or not native_executable:
            raise OperationExecutionError("Codex runtime bootstrap is no longer a native executable")
        if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise OperationExecutionError("Codex runtime bootstrap became group- or world-writable")
        current_owner = os.geteuid() if hasattr(os, "geteuid") else None
        if current_owner is not None and metadata.st_uid not in {0, current_owner}:
            raise OperationExecutionError("Codex runtime bootstrap now has an untrusted owner")


def _completion_schema(specification: LaunchSpecification) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "schema_version": {"type": "integer", "const": _completion_version(specification)},
        "operation": {"type": "string", "const": specification.operation},
        "stage": {"type": "string", "const": specification.stage},
        "occurrence": {"type": "integer", "const": specification.occurrence},
        "capability": {"type": "string", "const": specification.capability},
        "launch_digest": {"type": "string", "const": specification.digest},
        "workspace_digest": {"type": "string", "const": specification.workspace_digest},
        "runtime_bootstrap_digest": {
            "type": "string",
            "const": specification.native_configuration.runtime_bootstrap_digest,
        },
        "status": {"enum": ["success", "failed"]},
        "output": {"type": "string"},
        "limitations": {"type": "string"},
        "gates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "status": {"enum": ["passed", "failed"]},
                    "evidence": {"type": "string", "minLength": 1},
                },
                "required": ["name", "status", "evidence"],
                "additionalProperties": False,
            },
        },
    }
    definitions = {}
    if _completion_version(specification) == 2:
        properties["invocation_id"] = {"const": specification.invocation_id}
        domain_type = _domain_type(specification)
        if domain_type is not None:
            from .operation_data import json_schema

            domain = json_schema(domain_type)
            definitions = domain.pop("$defs")
            domain.pop("$schema")
            properties["domain_output"] = {"anyOf": [domain, {"type": "null"}]}
        else:
            properties["domain_output"] = {"type": "null"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
        **({"$defs": definitions} if definitions else {}),
    }


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


def _json_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _codex_envelope(stdout: str) -> dict[str, Any]:
    final_message: str | None = None
    completed = False
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = _json_object(json.loads(line), f"Codex JSONL line {line_number}")
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"invalid Codex JSONL output: {error}") from error
        event_type = event.get("type")
        if event_type in {"turn.failed", "error"}:
            raise ValueError(f"Codex lifecycle reported {event_type}")
        if event_type == "turn.completed":
            completed = True
        item = event.get("item")
        if event_type == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                final_message = text
    if not completed:
        raise ValueError("Codex JSONL omitted turn.completed")
    if final_message is None:
        raise ValueError("Codex JSONL omitted a final agent message")
    try:
        return _json_object(json.loads(final_message), "Codex completion envelope")
    except json.JSONDecodeError as error:
        raise ValueError(f"Codex final message is not JSON: {error}") from error


def _claude_envelope(stdout: str) -> dict[str, Any]:
    try:
        result = _json_object(json.loads(stdout), "Claude JSON output")
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid Claude JSON output: {error}") from error
    if result.get("is_error") is True or result.get("subtype") in {"error", "failed"}:
        raise ValueError("Claude lifecycle reported failure")
    structured = result.get("structured_output")
    if isinstance(structured, dict):
        return structured
    raw = result.get("result")
    if isinstance(raw, str):
        try:
            return _json_object(json.loads(raw), "Claude completion envelope")
        except json.JSONDecodeError as error:
            raise ValueError(f"Claude result is not structured JSON: {error}") from error
    return result


def _validate_completion(payload: dict[str, Any], specification: LaunchSpecification) -> CapabilityCompletion:
    expected_keys = {
        "schema_version", "operation", "stage", "occurrence", "capability", "launch_digest",
        "workspace_digest", "runtime_bootstrap_digest",
        "status", "output", "limitations", "gates",
    }
    version = _completion_version(specification)
    if version == 2:
        expected_keys.add("domain_output")
        expected_keys.add("invocation_id")
    if set(payload) != expected_keys:
        raise ValueError(f"completion envelope fields do not match schema {version}")
    expected_identity = {
        "schema_version": version,
        "operation": specification.operation,
        "stage": specification.stage,
        "occurrence": specification.occurrence,
        "capability": specification.capability,
        "launch_digest": specification.digest,
        "workspace_digest": specification.workspace_digest,
        "runtime_bootstrap_digest": specification.native_configuration.runtime_bootstrap_digest,
    }
    if version == 2:
        expected_identity["invocation_id"] = specification.invocation_id
    for key, expected in expected_identity.items():
        if payload.get(key) != expected or type(payload.get(key)) is not type(expected):
            raise ValueError(f"completion envelope {key} does not match launch")
    status_value = payload.get("status")
    if status_value not in {"success", "failed"}:
        raise ValueError("completion envelope has invalid status")
    output = payload.get("output")
    limitations = payload.get("limitations")
    if not isinstance(output, str) or not isinstance(limitations, str):
        raise ValueError("completion output and limitations must be strings")
    raw_gates = payload.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise ValueError("completion envelope requires at least one gate")
    gates: list[CompletionGate] = []
    names: set[str] = set()
    for raw in raw_gates:
        gate = _json_object(raw, "completion gate")
        if set(gate) != {"name", "status", "evidence"}:
            raise ValueError("completion gate fields do not match schema 1")
        name, gate_status, evidence = gate.get("name"), gate.get("status"), gate.get("evidence")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("completion gate names must be unique and non-empty")
        if gate_status not in {"passed", "failed"}:
            raise ValueError("completion gate has invalid status")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("completion gate evidence must be non-empty")
        names.add(name)
        gates.append(CompletionGate(name=name, status=gate_status, evidence=evidence))
    failed_gates = [gate for gate in gates if gate.status == "failed"]
    if status_value == "success":
        if limitations != "none" or failed_gates:
            raise ValueError("successful completion must have no limitations or failed gates")
    elif not limitations.strip() or limitations == "none" or not failed_gates:
        raise ValueError("failed completion requires limitations and a failed gate")
    domain_output = payload.get("domain_output")
    expected_domain = _domain_type(specification)
    if status_value == "success" and expected_domain:
        from .operation_data import validate_typed

        domain_output = validate_typed(domain_output, expected_domain, "/domain_output")
    elif domain_output is not None:
        raise ValueError("this completion must have null domain_output")
    return CapabilityCompletion(
        schema_version=version,
        operation=specification.operation,
        stage=specification.stage,
        occurrence=specification.occurrence,
        capability=specification.capability,
        launch_digest=specification.digest,
        workspace_digest=specification.workspace_digest,
        runtime_bootstrap_digest=specification.native_configuration.runtime_bootstrap_digest,
        status=status_value,
        output=output,
        limitations=limitations,
        gates=tuple(gates),
        domain_output=domain_output,
        invocation_id=payload.get("invocation_id"),
    )


def _completion(stdout: str, specification: LaunchSpecification) -> CapabilityCompletion:
    payload = _codex_envelope(stdout) if specification.integration == "codex" else _claude_envelope(stdout)
    return _validate_completion(payload, specification)


def _prompt(specification: LaunchSpecification) -> str:
    prior = "\n".join(
        f"{index + 1}. {result}" for index, result in enumerate(specification.prior_results)
    ) or "(none)"
    data_input = (
        "Operation configuration (project snapshot):\n"
        f"{specification.operation_configuration_json}\n\n"
        "Typed runtime input (consume only these contracted fields):\n"
        f"{specification.runtime_input_json}\n\n"
        "Your completion output is an audit summary, not a downstream data channel. "
        "Return domain_output matching the supplied schema when it requests a typed value; "
        "otherwise return null and the host derives domain results from verified workspace state.\n\n"
        if specification.runtime_input_json is not None
        else f"Request:\n{specification.request}\n\nPrior results:\n{prior}\n\n"
    )
    investigation = (
        "Reflection investigation contract:\n"
        "Read each selected reflection and its existing plan from the supplied ArtifactRefs. "
        "Reproduce its Observed behavior against the exact supplied HEAD before proposing changes. "
        "Return one concorde-reflection-investigation-result@1 finding per selected ID in input order. "
        "Include verified_commit, the concrete verification method/outcome, root-cause analysis, resolution, "
        "implementation steps, validation, risks, scope files, effort, route, human intervention and its rationale. "
        "Set protocol_change when the proposal changes normative Concorde Protocol semantics. "
        "If the problem does not reproduce, choose dismiss and require a maintainer decision. "
        "Use plain paragraphs/lists inside section fields, without level-one or level-two headings. "
        "Do not write files: the parent validates and persists the typed result, preserving user comments and disposition.\n\n"
        if _domain_type(specification) is not None else ""
    )
    return (
        f"Operation: {specification.operation}\n"
        f"Stage: {specification.stage}\n"
        f"Capability: {specification.capability}\n"
        f"{data_input}"
        "Operation workspace receipt (trusted host result):\n"
        f"{specification.workspace_receipt_json}\n\n"
        f"Canonical capability prompt:\n{specification.prompt}\n\n"
        f"{investigation}"
        "Operation gate override:\n"
        "This Operation-composed invocation has already satisfied the canonical Protocol 13 workspace "
        "gate through the trusted receipt above. Use only its bounded paths and do not rerun the "
        "workspace resolver or reopen broader project context. The complete canonical Skill body is "
        "supplied inline and its source file need not be readable. An attempt_state of 'absent' is a "
        "validated no-attempt state, not missing evidence; evaluate only attempt artifacts that the "
        "receipt reports as present.\n\n"
        "Completion contract:\n"
        f"Return only Capability Completion Envelope {_completion_version(specification)} matching the supplied schema. "
        "Report every mandatory prerequisite or phase gate you relied on. Set status=failed when any "
        "mandatory gate, required tool, authority check, or requested outcome did not complete; include "
        "a non-empty limitation and at least one failed gate. Set status=success only when every reported "
        "gate passed, limitations is exactly 'none', and output is safe for the next Operation stage. "
        f"Bind the envelope to launch_digest {specification.digest}."
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
    runtime_bootstrap_resolver: RuntimeBootstrapResolver = resolve_runtime_bootstrap
    runtime_bootstrap_verifier: RuntimeBootstrapVerifier = verify_runtime_bootstrap
    environment: Mapping[str, str] | None = None

    def _preflight(
        self,
        specification: LaunchSpecification,
        environment: Mapping[str, str],
    ) -> tuple[str, LaunchSpecification]:
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
            bootstrap = (
                ()
                if config.enforcement == "outer"
                else self.runtime_bootstrap_resolver(
                    specification.integration,
                    executable,
                    specification.project_root,
                    environment,
                )
            )
            finalized = finalize_launch_specification(specification, bootstrap)
            self.runtime_bootstrap_verifier(finalized.native_configuration.runtime_bootstrap)
        except OperationExecutionError:
            raise
        except Exception as error:
            raise OperationExecutionError(f"runtime bootstrap preflight failed: {error}") from error
        if not _exact_effective_boundary(finalized):
            raise OperationExecutionError("final native effective boundary differs from normalized policy")
        finalized_executable = finalized.native_configuration.argv[0]
        try:
            version = self.version_probe(specification.integration, finalized_executable).strip()
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
        return version, finalized

    def __call__(self, specification: LaunchSpecification) -> OperationExecutionResult:
        source_environment = os.environ if self.environment is None else self.environment
        environment = {
            key: value
            for key, value in sorted(source_environment.items())
            if key in _SAFE_ENVIRONMENT and isinstance(value, str)
        }
        version, finalized = self._preflight(specification, environment)
        config = finalized.native_configuration
        prompt = _prompt(finalized)
        argv = config.argv
        schema = _completion_schema(finalized)
        schema_json = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        try:
            with tempfile.TemporaryDirectory(prefix="concorde-completion-") as temporary:
                if finalized.integration == "codex":
                    schema_path = Path(temporary) / "capability-completion.schema.json"
                    schema_path.write_text(schema_json + "\n", encoding="utf-8")
                    argv = (*argv[:-1], "--json", "--output-schema", str(schema_path), argv[-1])
                else:
                    argv = (
                        *argv,
                        "--output-format",
                        "json",
                        "--json-schema",
                        schema_json,
                        "Execute the complete bounded request supplied on stdin.",
                    )
                self.runtime_bootstrap_verifier(config.runtime_bootstrap)
                completed = self.runner(
                    tuple(argv),
                    cwd=finalized.project_root,
                    env=environment,
                    input_text=prompt,
                )
        except Exception as error:
            raise OperationExecutionError(f"agent process launch failed: {error}") from error
        if not isinstance(completed, subprocess.CompletedProcess):
            raise OperationExecutionError("agent process runner returned an invalid result")
        bootstrap_digest = config.runtime_bootstrap_digest

        def receipt(status: Literal["success", "failed"], limitations: str) -> EnforcementReceipt:
            return EnforcementReceipt(
                requested_launch_digest=specification.digest,
                launch_digest=finalized.digest,
                policy_digest=finalized.policy.digest,
                config_digest=config.digest,
                integration=finalized.integration,
                client_version=version,
                enforcement=config.enforcement,
                exit_code=completed.returncode,
                status=status,
                runtime_bootstrap_digest=bootstrap_digest,
                completion_schema_version=_completion_version(finalized),
                completion_status=status,
                limitations=limitations,
            )
        if completed.returncode:
            limitations = (completed.stderr or completed.stdout or "process failed without diagnostics").strip()
            failed_receipt = receipt("failed", limitations)
            raise OperationExecutionError(
                f"{finalized.integration} process exited with exit {completed.returncode}: {limitations}",
                failed_receipt,
            )
        try:
            completion = _completion((completed.stdout or "").strip(), finalized)
        except ValueError as error:
            limitations = f"invalid capability completion: {error}"
            raise OperationExecutionError(limitations, receipt("failed", limitations)) from error
        if completion.status == "failed":
            raise OperationExecutionError(
                f"{finalized.capability} reported failed completion: {completion.limitations}",
                receipt("failed", completion.limitations),
            )
        success_receipt = receipt("success", "none")
        return OperationExecutionResult(
            output=completion.output,
            receipt=success_receipt,
            completion=completion,
        )
