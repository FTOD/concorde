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

from . import agent_model
from .harness import HARNESSES, SAFE_ENVIRONMENT
from .permissions import (
    CapabilityCompletion,
    CompletionGate,
    EnforcementReceipt,
    LaunchSpecification,
    CapabilityExecutionResult,
    RuntimeBootstrapFile,
    finalize_launch_specification,
    runtime_bootstrap_file,
)


class CapabilityExecutionError(RuntimeError):
    """Agent process preflight or execution failed without a permissive retry.

    ``outcome`` classifies why: ``failed`` (default) for a nonzero exit or a launch/preflight
    failure, ``cancelled`` when the runner raised ``KeyboardInterrupt``, ``limit_exhausted`` when
    the runner raised ``subprocess.TimeoutExpired`` (the Agent's Harness loop timeout), and
    ``invalid_completion`` when a zero-exit process returned an invalid or domain-failed
    completion. The host maps these to distinct result error codes; none retries automatically."""

    def __init__(
        self,
        message: str,
        receipt: EnforcementReceipt | None = None,
        outcome: Literal["failed", "cancelled", "limit_exhausted", "invalid_completion"] = "failed",
    ):
        super().__init__(message)
        self.receipt = receipt
        self.outcome = outcome


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
VersionProbe = Callable[[str, str], str]
RuntimeBootstrapResolver = Callable[[str, str, str, Mapping[str, str]], tuple[RuntimeBootstrapFile, ...]]
RuntimeBootstrapVerifier = Callable[[tuple[RuntimeBootstrapFile, ...]], None]

# Alias retained for existing internal references; the canonical definition is harness.SAFE_ENVIRONMENT.
_SAFE_ENVIRONMENT = frozenset(SAFE_ENVIRONMENT)
_VERSION = re.compile(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?")


def _completion_version(specification: LaunchSpecification) -> int:
    return 3 if specification.runtime_input_json is not None else 1


def _domain_type(specification: LaunchSpecification) -> str | None:
    runtime_type = (json.loads(specification.runtime_input_json).get("type_id")
                    if specification.runtime_input_json is not None else None)
    if runtime_type == "concorde-agent-loop-context":
        return "concorde-agent-loop-step"
    if runtime_type == "concorde-agent-stage-context":
        return "concorde-agent-stage-result"
    if runtime_type == "concorde-review-stage-context":
        return "concorde-review-stage-result"
    if runtime_type == "concorde-main-stage-context":
        return "concorde-main-stage-result"
    if runtime_type == "concorde-topology-author-context":
        return "concorde-topology-author-result"
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
        raise CapabilityExecutionError("Codex runtime bootstrap could not resolve the selected executable")
    try:
        path = Path(selected).resolve(strict=True)
        project = Path(project_root).resolve(strict=True)
        metadata = path.stat()
    except OSError as error:
        raise CapabilityExecutionError(f"Codex runtime bootstrap resolution failed: {error}") from error
    if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK):
        raise CapabilityExecutionError("Codex runtime bootstrap is not one executable regular file")
    try:
        native_executable = _is_native_executable(path)
    except OSError as error:
        raise CapabilityExecutionError(f"Codex runtime bootstrap inspection failed: {error}") from error
    if not native_executable:
        raise CapabilityExecutionError(
            "Codex runtime bootstrap must be a native executable, not a script or package shim"
        )
    if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise CapabilityExecutionError("Codex runtime bootstrap is group- or world-writable")
    current_owner = os.geteuid() if hasattr(os, "geteuid") else None
    if current_owner is not None and metadata.st_uid not in {0, current_owner}:
        raise CapabilityExecutionError("Codex runtime bootstrap has an untrusted owner")
    try:
        path.relative_to(project)
    except ValueError:
        pass
    else:
        raise CapabilityExecutionError("Codex runtime bootstrap must remain outside project authority")
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
            raise CapabilityExecutionError(f"Codex runtime bootstrap recheck failed: {error}") from error
        if actual != expected:
            raise CapabilityExecutionError("Codex runtime bootstrap changed after attestation")
        if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK) or not native_executable:
            raise CapabilityExecutionError("Codex runtime bootstrap is no longer a native executable")
        if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise CapabilityExecutionError("Codex runtime bootstrap became group- or world-writable")
        current_owner = os.geteuid() if hasattr(os, "geteuid") else None
        if current_owner is not None and metadata.st_uid not in {0, current_owner}:
            raise CapabilityExecutionError("Codex runtime bootstrap now has an untrusted owner")


def _completion_schema(specification: LaunchSpecification) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "schema_version": {"type": "integer", "const": _completion_version(specification)},
        "capability": {"type": "string", "const": specification.capability},
        "stage": {"type": "string", "const": specification.stage},
        "occurrence": {"type": "integer", "const": specification.occurrence},
        "role": {"type": "string", "const": specification.role},
        "launch_digest": {"type": "string", "const": specification.digest},
        "workspace_digest": {"type": "string", "const": specification.workspace_digest},
        "runtime_bootstrap_digest": {
            "type": "string",
            "const": specification.native_configuration.runtime_bootstrap_digest,
        },
        "status": {"enum": ["success", "failed"]},
        "output": {"type": "string"},
        "limitations": {
            "type": "string",
            "minLength": 1,
            "description": (
                "For status=success, use exactly the lowercase string 'none', never an empty string. "
                "For status=failed, explain the execution failure with a nonempty string other than 'none'. "
                "A valid bounded gap assessment belongs in domain_output, not in limitations."
            ),
        },
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
    if _completion_version(specification) == 3:
        properties["invocation_id"] = {"const": specification.invocation_id}
        domain_type = _domain_type(specification)
        if domain_type is not None:
            from .typed_data import json_schema

            domain = json_schema(domain_type)
            definitions = domain.pop("$defs")
            domain.pop("$schema")
            properties["domain_output"] = {"anyOf": [domain, {"type": "null"}]}
            if domain_type == "concorde-review-stage-result":
                admitted = json.loads(specification.runtime_input_json)["data"]
                snapshot = admitted["snapshot"]["data"]
                review = admitted["review"]["data"]
                fields = definitions[domain_type]["properties"]
                for key, value in {"context_id": snapshot["context_id"],
                        "input_digest": review["input_digest"], "review_mode": review["review_mode"]}.items():
                    fields[key] = {"type": "string", "const": value}
                finding = fields["findings"]["items"]["properties"]
                finding["document"] = {"type": "string", "enum": snapshot["document_order"]}
                finding["target_id"] = {"type": "string", "const": snapshot["target_id"]}
                paths = [*snapshot["document_order"],
                    *(item["path"] for item in snapshot["implementation_artifacts"]),
                    *(item["path"] for item in review["changes"])]
                finding["location"]["properties"]["path"] = {"type": "string", "enum": sorted(set(paths))}
                for key in ("target_id", "context_id"):
                    fields["gaps"]["items"]["properties"][key] = {"type": "string", "const": snapshot[key]}
        else:
            properties["domain_output"] = {"type": "null"}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
        **({"$defs": definitions} if definitions else {}),
    }
    if specification.integration == "codex":
        # Native Structured Outputs requires every declared object property.
        # The provider also rejects uniqueItems. Adapt generation only; the host
        # still validates the original contracts, including array uniqueness.
        def require_properties(value):
            if isinstance(value, dict):
                value.pop("uniqueItems", None)
                if "type" not in value and ("const" in value or "enum" in value):
                    literals = [value["const"]] if "const" in value else value["enum"]
                    kinds = {type(None): "null", str: "string", bool: "boolean", int: "integer",
                             float: "number", list: "array", dict: "object"}
                    types = sorted({kinds[type(item)] for item in literals})
                    value["type"] = types[0] if len(types) == 1 else types
                if "properties" in value:
                    value["required"] = list(value["properties"])
                for child in value.values():
                    require_properties(child)
            elif isinstance(value, list):
                for child in value:
                    require_properties(child)
        require_properties(schema)
    else:
        # Claude's native schema compiler does not register the 2020-12 meta-schema.
        # Omit the dialect declaration only in generation; host validation is unchanged.
        schema.pop("$schema", None)
    return schema


def _default_runner(
    argv: tuple[str, ...],
    *,
    cwd: str,
    env: Mapping[str, str],
    input_text: str,
    timeout: float | None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=dict(env),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
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
        "schema_version", "capability", "stage", "occurrence", "role", "launch_digest",
        "workspace_digest", "runtime_bootstrap_digest",
        "status", "output", "limitations", "gates",
    }
    version = _completion_version(specification)
    if version == 3:
        expected_keys.add("domain_output")
        expected_keys.add("invocation_id")
    if set(payload) != expected_keys:
        raise ValueError(f"completion envelope fields do not match schema {version}")
    expected_identity = {
        "schema_version": version,
        "capability": specification.capability,
        "stage": specification.stage,
        "occurrence": specification.occurrence,
        "role": specification.role,
        "launch_digest": specification.digest,
        "workspace_digest": specification.workspace_digest,
        "runtime_bootstrap_digest": specification.native_configuration.runtime_bootstrap_digest,
    }
    if version == 3:
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
        if limitations != "none":
            received = "an empty string" if not limitations else "a different string"
            raise ValueError(
                "successful completion requires limitations exactly 'none'; received " + received
            )
        if failed_gates:
            raise ValueError("successful completion contains failed gates")
    elif not limitations.strip() or limitations == "none" or not failed_gates:
        raise ValueError("failed completion requires limitations and a failed gate")
    domain_output = payload.get("domain_output")
    expected_domain = _domain_type(specification)
    if status_value == "success" and expected_domain:
        from .typed_data import validate_typed

        domain_output = validate_typed(domain_output, expected_domain, "/domain_output")
    elif domain_output is not None:
        raise ValueError("this completion must have null domain_output")
    return CapabilityCompletion(
        schema_version=version,
        capability=specification.capability,
        stage=specification.stage,
        occurrence=specification.occurrence,
        role=specification.role,
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
    version = _completion_version(specification)
    assessment = (
        "A valid gap assessment or review finding belongs in domain_output and does not by itself "
        "make the envelope fail. "
        if _domain_type(specification) is not None else ""
    )
    failed_domain_output = "Set domain_output to null for status=failed. " if version == 3 else ""
    return (
        _role_prompt(specification)
        + "\n\nCompletion contract:\n"
        + f"Return only Capability Completion Envelope {version} matching the supplied schema. "
        "The envelope status describes execution of the bounded role. "
        f"{assessment}"
        "Report every mandatory prerequisite or phase gate you relied on. "
        "Set status=success only when every reported gate passed and limitations is exactly 'none' "
        "(the lowercase string, never an empty string). "
        "Set status=failed if execution of the bounded role cannot complete, including failure of a "
        "mandatory execution gate, required tool or authority check; include a nonempty limitation "
        "other than 'none' and at least one failed gate. "
        f"{failed_domain_output}"
        "Never clear a real failure to obtain success. "
        f"Bind the envelope to launch_digest {specification.digest}."
    )


def _role_prompt(specification: LaunchSpecification) -> str:
    if _domain_type(specification) == "concorde-agent-loop-step":
        return (
            "Execute one fresh model-driven Agent decision. Use only the admitted context below.\n"
            f"{specification.runtime_input_json}\nAgent responsibility Spec:\n{specification.prompt}\n"
            "Return Completion Envelope 3 with concorde-agent-loop-step as domain_output. "
            "Set source=model-driven. Delegate only through that typed action, never native sub-agent tools. "
            "Only advertised child contracts are callable. Complete with the declared result schema, "
            "or return typed gap/decision details for spec_incomplete/waiting. "
            "No parent transcripts, project searches, ambient Skills or context expansion are admitted.\n"
        )
    if _domain_type(specification) == "concorde-review-stage-result":
        return (
            "Execute one independent Concorde review in a fresh session. You have no project write authority.\n"
            f"Capability: {specification.capability}\nStage: {specification.stage}\n"
            f"Host workspace grant:\n{specification.workspace_receipt_json}\n"
            f"Configuration snapshot:\n{specification.capability_configuration_json}\n"
            f"Complete admitted context and task:\n{specification.runtime_input_json}\n\n"
            f"Review instructions:\n{specification.prompt}\n\n"
            "Read the entire admitted Target Spec and Shared Specs, not just patches. Spec review must judge "
            "whether these documents alone support representative tasks; it cannot inspect implementation. "
            "Code review may read only granted target implementation files and compare their behavior with "
            "the supplied contracts. Do not load repository guidance, other Skills, ancestor/provider/child "
            "Specs, other worktrees, prior conversations, or remote sources. Do not run checks or modify "
            "Spec, source, tests, or control files. The host owns result persistence.\n"
            "Report concrete missing promises or behavior defects and affected tasks; avoid speculative "
            "completeness claims. Each finding identifies its target, local contract document, contract, "
            "location, problem, affected_task and blocking/advisory severity. The document field is the exact "
            "admitted Markdown path from document_order. A blocking Spec finding needs "
            "a gap whose blocked_step equals affected_task and needed_contract equals contract. Missing "
            "contracts encountered during code review also use gaps. No raw source snippets, patches or "
            "process logs may appear in answers or findings.\n"
            "Return Capability Completion Envelope 3 with typed concorde-review-stage-result in domain_output. "
            "For a valid bounded assessment, including findings, gaps or declared incomplete coverage, set "
            "the envelope status to success, limitations to exactly 'none', and every envelope gate to passed. "
            "The domain result status describes review coverage; findings are not process failures. A failed "
            "envelope instead requires a nonempty limitation and at least one failed gate. "
            "Bind context_id, input_digest and review_mode exactly to the supplied inputs. Use status=no_findings "
            "only after covering nonempty representative_tasks with no findings/gaps; findings means a "
            "completed review with concrete findings/gaps. If the review cannot complete, use incomplete and "
            "explain why; never treat failure or skipped coverage as no_findings. Neither successful status "
            "proves universal semantic completeness.\n"
            f"Invocation: {specification.invocation_id}\nLaunch digest: {specification.digest}\n"
        )
    if _domain_type(specification) == "concorde-topology-author-result":
        return (
            "Execute one Concorde topology Spec-author stage in a fresh target-local context.\n"
            f"Capability: {specification.capability}\nStage: {specification.stage}\n"
            f"Host workspace grant:\n{specification.workspace_receipt_json}\n"
            f"Configuration snapshot:\n{specification.capability_configuration_json}\n"
            f"Complete provisional target context:\n{specification.runtime_input_json}\n\n"
            "Use only the supplied target descriptor, matching kind definition, task, candidate document references, "
            "and current documents separated as Target Spec and Shared Specs. "
            "Return the complete content for every path in target.documents and no other path. Do not load another "
            "target, registry file, Module body outside this target, implementation code, prior conversation, or remote "
            "source. A shared document is collective truth: preserve its exact declared target set and return the same "
            "proposed bytes as every other referencing target author. Report missing target-local facts as structured gaps.\n"
            "Return Capability Completion Envelope 3 matching the supplied schema, with a typed "
            "concorde-topology-author-result in domain_output. Bind every identity exactly.\n"
            f"Invocation: {specification.invocation_id}\nLaunch digest: {specification.digest}\n"
        )
    if _domain_type(specification) == "concorde-main-stage-result":
        return (
            "Execute one Concorde Profile 10 main-coordinator stage in a fresh context.\n"
            f"Capability: {specification.capability}\nStage: {specification.stage}\n"
            f"Host discovery grant:\n{specification.workspace_receipt_json}\n"
            f"Configuration snapshot:\n{specification.capability_configuration_json}\n"
            f"Complete admitted discovery context and task:\n{specification.runtime_input_json}\n\n"
            "Use the complete Module documents in the supplied source pool; every architecture diagram is "
            "inline in them. Target Spec and Shared Specs references identify each Module's membership; read "
            "their full bodies. Never load implementation code, repository guidance, another Skill, a prior "
            "conversation, or a remote source. "
            "In route phase, request only Module IDs identified by an admitted Spec, or the explicit target "
            "hint, in expand_targets. For ask, answer directly from the admitted complete contexts with completed, "
            "or request more contexts; never return worker routes. Non-ask capabilities require one route and "
            "unchanged task intent. For design-topology, return topology_proposed with one complete candidate registry, "
            "target-local Spec tasks, migration constraints, and acceptance conditions after sufficient discovery; do "
            "not include document bodies or code facts. Do not perform routed mutations. "
            "Report missing required promises as structured Spec gaps owned by an "
            "admitted Module.\n"
            "Return Capability Completion Envelope 3 matching the supplied schema. Put a typed "
            "concorde-main-stage-result in domain_output with context_id, outcome, answer, expand_targets, routes, "
            "gaps, and nullable topology_design. Bind every launch, invocation, workspace, and context identity exactly.\n"
            f"Invocation: {specification.invocation_id}\nLaunch digest: {specification.digest}\n"
        )
    if _domain_type(specification) == "concorde-agent-stage-result":
        return (
            "Execute one Concorde Profile 10 agent stage in a fresh context.\n"
            f"Capability: {specification.capability}\nStage: {specification.stage}\n"
            f"Host workspace grant:\n{specification.workspace_receipt_json}\n"
            f"Configuration snapshot:\n{specification.capability_configuration_json}\n"
            f"Complete admitted context and task:\n{specification.runtime_input_json}\n\n"
            "Use only the supplied snapshot, whose document bodies are separated as Target Spec and Shared Specs, "
            "and enforced paths. Do not load repository guidance, "
            "other Skills, ancestor/provider Specs, prior conversations, or remote sources. "
            "Only the implementation stage may inspect or change the granted implementation files. Other stages "
            "see those file names as Spec facts and determine tasks solely from the complete Module Spec. "
            "When the current task requires a missing or ambiguous contract, report question, blocked_step "
            "and needed_contract as structured Spec gaps, and pause the judgments or steps that depend on it. "
            "Do not silently supply a contract by convention or infer it from code. Independent reasoning may "
            "continue in the answer; do not broaden retrieval or mark dependent tasks complete. "
            "Do not run framework resolvers or validation commands; the trusted host performs these.\n"
            "Return Capability Completion Envelope 3 matching the supplied schema, binding every identity "
            "and launch/context digest. Its status describes completion of this bounded role, including "
            "a valid gap assessment. Workflow progress is controlled by domain_output.data.outcome. "
            "Put the typed concorde-agent-stage-result in domain_output. Include context_id, outcome, "
            "answer, gaps, documents, plan, and tasks. Use empty arrays/strings for unused domain_output fields; "
            "this does not apply to the envelope limitations field. "
            "A spec_incomplete outcome requires concrete question/blocked_step/needed_contract gaps; "
            "other outcomes have no gaps. Only the specification stage may return Module document replacements; "
            "every other stage returns an empty documents array. "
            "Do not transmit raw code or implementation logs in a result for a later Spec-only stage.\n"
            f"Invocation: {specification.invocation_id}\nLaunch digest: {specification.digest}\n"
        )
    prior = "\n".join(
        f"{index + 1}. {result}" for index, result in enumerate(specification.prior_results)
    ) or "(none)"
    data_input = (
        "Capability configuration (project snapshot):\n"
        f"{specification.capability_configuration_json}\n\n"
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
        "Set protocol_change when the proposal changes normative Concorde Spec Protocol semantics. "
        "If the problem does not reproduce, choose dismiss and require a developer decision. "
        "Use plain paragraphs/lists inside section fields, without level-one or level-two headings. "
        "Do not write files: the parent validates and persists the typed result, preserving user comments and disposition.\n\n"
        if _domain_type(specification) is not None else ""
    )
    return (
        f"Capability: {specification.capability}\n"
        f"Stage: {specification.stage}\n"
        f"Role: {specification.role}\n"
        f"{data_input}"
        "Capability workspace receipt (trusted host result):\n"
        f"{specification.workspace_receipt_json}\n\n"
        f"Canonical capability prompt:\n{specification.prompt}\n\n"
        f"{investigation}"
        "Capability gate override:\n"
        "This capability-composed invocation has already satisfied the canonical Protocol 13 workspace "
        "gate through the trusted receipt above. Use only its bounded paths and do not rerun the "
        "workspace resolver or reopen broader project context. The complete canonical Skill body is "
        "supplied inline and its source file need not be readable. An attempt_state of 'absent' is a "
        "validated no-attempt state, not missing evidence; evaluate only attempt artifacts that the "
        "receipt reports as present.\n\n"
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
    ) -> tuple[str, LaunchSpecification, "agent_model.AgentBinding | None"]:
        config = specification.native_configuration
        if config.integration != specification.integration:
            raise CapabilityExecutionError("launch integration differs from native configuration")
        if config.policy_digest != specification.policy.digest:
            raise CapabilityExecutionError("native configuration policy digest is stale")
        if config.enforcement not in {"native", "outer"}:
            raise CapabilityExecutionError("launch has no verified enforcement boundary")
        if config.enforcement == "outer" and not config.outer_sandbox:
            raise CapabilityExecutionError("outer enforcement receipt has no provider identity")
        if not _exact_effective_boundary(specification):
            raise CapabilityExecutionError("native effective boundary differs from normalized policy")
        executable = config.argv[0] if config.argv else ""
        expected = "codex" if specification.integration == "codex" else "claude"
        if executable != expected:
            raise CapabilityExecutionError(
                f"native executable {executable!r} does not match {specification.integration}"
            )
        binding = None
        if specification.runtime_input_json is not None:
            binding = self._preflight_agent_binding(specification)
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
        except CapabilityExecutionError:
            raise
        except Exception as error:
            raise CapabilityExecutionError(f"runtime bootstrap preflight failed: {error}") from error
        if not _exact_effective_boundary(finalized):
            raise CapabilityExecutionError("final native effective boundary differs from normalized policy")
        finalized_executable = finalized.native_configuration.argv[0]
        try:
            version = self.version_probe(specification.integration, finalized_executable).strip()
        except Exception as error:  # pragma: no cover - exact probe backend is host-owned
            raise CapabilityExecutionError(f"client version preflight failed: {error}") from error
        if not version:
            raise CapabilityExecutionError("client version preflight returned no supported version")
        parsed = _version_tuple(version)
        if config.enforcement == "native" and parsed is not None:
            minimum = (0, 138, 0) if specification.integration == "codex" else (2, 1, 248)
            if parsed < minimum:
                raise CapabilityExecutionError(
                    f"client version preflight requires {expected}>={'.'.join(map(str, minimum))}"
                )
        return version, finalized, binding

    @staticmethod
    def _preflight_agent_binding(specification: LaunchSpecification) -> "agent_model.AgentBinding":
        """Reconstruct and verify the launch's declared Agent binding, failing closed on any
        mismatch between the launched prompt/policy/context/result and the admitted Agent (A1, A4)."""

        if not specification.agent_binding_json:
            raise CapabilityExecutionError("structured launch has no Agent binding")
        try:
            parsed = json.loads(specification.agent_binding_json)
            binding = agent_model.binding_from_json(specification.agent_binding_json)
        except Exception as error:
            raise CapabilityExecutionError(f"agent binding preflight failed: {error}") from error
        if not isinstance(parsed, dict) or agent_model.binding_digest(binding) != parsed.get("digest"):
            raise CapabilityExecutionError("agent binding digest does not match its own recorded fields")
        try:
            agent = agent_model.agent_definition(binding.agent)
        except Exception as error:
            raise CapabilityExecutionError(f"launch names an unknown Agent: {error}") from error
        if not (agent_model.external_agent_name(agent.name) == specification.role == specification.agent):
            raise CapabilityExecutionError("launch role/agent identity does not match the bound Agent")
        expected_instructions_digest = "sha256:" + hashlib.sha256(specification.prompt.encode("utf-8")).hexdigest()
        if binding.instructions_digest != expected_instructions_digest:
            raise CapabilityExecutionError("launch prompt does not match the bound Agent's rendered instructions")
        registered_harness = HARNESSES.get(binding.harness)
        if (binding.harness != agent.harness.name or registered_harness is None
                or registered_harness.digest != binding.harness_digest):
            raise CapabilityExecutionError("launch Harness identity does not match the bound Agent")
        result_type = _domain_type(specification)
        if result_type is None or result_type not in agent.constraints.results:
            raise CapabilityExecutionError("launch result type is not declared by the bound Agent")
        runtime_type = json.loads(specification.runtime_input_json).get("type_id")
        if runtime_type not in agent.constraints.contexts:
            raise CapabilityExecutionError("launch context type is not declared by the bound Agent")
        effects = agent.constraints.effects
        policy = specification.policy
        if effects.writes == () and policy.write_paths != ():
            raise CapabilityExecutionError("launch policy grants writes the bound Agent does not declare")
        if policy.network_enabled and not effects.network:
            raise CapabilityExecutionError("launch policy grants network access the bound Agent does not declare")
        if policy.credentials != "none" and effects.credentials != "declared":
            raise CapabilityExecutionError("launch policy grants credentials the bound Agent does not declare")
        return binding

    def __call__(self, specification: LaunchSpecification) -> CapabilityExecutionResult:
        source_environment = os.environ if self.environment is None else self.environment
        environment = {
            key: value
            for key, value in sorted(source_environment.items())
            if key in _SAFE_ENVIRONMENT and isinstance(value, str)
        }
        version, finalized, binding = self._preflight(specification, environment)
        config = finalized.native_configuration
        prompt = _prompt(finalized)
        argv = config.argv
        schema = _completion_schema(finalized)
        schema_json = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        bootstrap_digest = config.runtime_bootstrap_digest
        agent_binding_digest = binding.digest if binding is not None else ""
        timeout = binding.effective_loop.timeout_seconds if binding is not None else None

        def receipt(status: Literal["success", "failed"], limitations: str, *, exit_code: int) -> EnforcementReceipt:
            return EnforcementReceipt(
                requested_launch_digest=specification.digest,
                launch_digest=finalized.digest,
                policy_digest=finalized.policy.digest,
                config_digest=config.digest,
                integration=finalized.integration,
                client_version=version,
                enforcement=config.enforcement,
                exit_code=exit_code,
                status=status,
                runtime_bootstrap_digest=bootstrap_digest,
                completion_schema_version=_completion_version(finalized),
                completion_status=status,
                limitations=limitations,
                agent_binding_digest=agent_binding_digest,
            )
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
                    timeout=timeout,
                )
        except subprocess.TimeoutExpired as error:
            raise CapabilityExecutionError(
                f"{finalized.integration} process exceeded the Harness loop limit of {timeout}s",
                receipt("failed", f"execution limit exhausted: {timeout}s wall clock", exit_code=-1),
                outcome="limit_exhausted",
            ) from error
        except KeyboardInterrupt:
            # subprocess.run already terminated the child before propagating the interrupt.
            raise CapabilityExecutionError("agent process cancelled", None, outcome="cancelled")
        except Exception as error:
            raise CapabilityExecutionError(f"agent process launch failed: {error}") from error
        if not isinstance(completed, subprocess.CompletedProcess):
            raise CapabilityExecutionError("agent process runner returned an invalid result")
        if completed.returncode:
            limitations = (completed.stderr or completed.stdout or "process failed without diagnostics").strip()
            failed_receipt = receipt("failed", limitations, exit_code=completed.returncode)
            raise CapabilityExecutionError(
                f"{finalized.integration} process exited with exit {completed.returncode}: {limitations}",
                failed_receipt,
            )
        try:
            completion = _completion((completed.stdout or "").strip(), finalized)
        except ValueError as error:
            limitations = f"invalid capability completion: {error}"
            raise CapabilityExecutionError(
                limitations, receipt("failed", limitations, exit_code=completed.returncode),
                outcome="invalid_completion",
            ) from error
        if completion.status == "failed":
            raise CapabilityExecutionError(
                f"{finalized.capability} reported failed completion: {completion.limitations}",
                receipt("failed", completion.limitations, exit_code=completed.returncode),
                outcome="invalid_completion",
            )
        success_receipt = receipt("success", "none", exit_code=completed.returncode)
        return CapabilityExecutionResult(
            output=completion.output,
            receipt=success_receipt,
            completion=completion,
        )
