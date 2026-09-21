"""Version-bound reader for native terminal evidence; provider wiring is separate.

The owning Pi extension binds ``directory`` and ``run_id`` from the actual subagent
Tool result. Task text, an emitted ``ok`` boolean, and a typed gate's success are
not accepted substitutes. The authored workflow emits only native metadata pointers;
this reader correlates them with independently published terminal status and gates.
This is cooperative runtime provenance, not protection against arbitrary same-user
filesystem tampering by an unsandboxed process.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..spec.repository import SpecError, digest
from ..spec.typed_data import decode
from .native_runtime import FORMAT, NativeRuntimeBinding
from .native_result import staging_control

MAX_NATIVE_RECORD_BYTES = 16 * 1024 * 1024


def _record(path: Path) -> dict:
    if not path.is_absolute() or any(
        parent.is_symlink() for parent in (path, *path.parents)
    ):
        raise SpecError("native evidence path is not canonical", "unsafe_path")
    if not path.is_file():
        raise SpecError(
            "native evidence is not an available regular file", "stale_evidence"
        )
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_NATIVE_RECORD_BYTES + 1)
        if len(raw) > MAX_NATIVE_RECORD_BYTES:
            raise ValueError("native evidence exceeds its read bound")
        value = decode(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("native evidence is not an object")
        return value
    except (OSError, ValueError) as error:
        raise SpecError(
            "native evidence is missing or invalid", "stale_evidence"
        ) from error


@dataclass(frozen=True)
class NativeChildEvidence:
    key: str
    agent: str
    invocation_id: str
    proposal_digest: str
    gate_command: str


def verify_native_children(
    directory: Path,
    *,
    run_id: str,
    session_id: str,
    ticket: str,
    children: tuple[NativeChildEvidence, ...],
    runtime: NativeRuntimeBinding,
) -> tuple[dict, ...]:
    """Require exact complete coverage, with no workflow receipt publication cycle.

    ``status.json`` is the documented native async artifact. Dependency probes
    exercise actual publication with only model execution replaced. Callers must
    still bind the actual launch response, preserve retained evidence and admit
    the producer before using this reader. Missing/stale artifacts fail closed,
    including native best-effort publication loss.
    The enclosing workflow may still be running at this explicit domain commit
    boundary; later cancellation does not undo an already durable domain commit.
    """
    if (
        not isinstance(runtime, NativeRuntimeBinding)
        or runtime.format != FORMAT
        or runtime.artifact_version is not None
    ):
        raise SpecError("unsupported native artifact producer", "unsupported_version")
    status = _record(directory / "status.json")
    if any(key in status for key in ("schema_version", "lifecycleArtifactVersion")):
        raise SpecError(
            "expected explicitly admitted versionless workflow status",
            "unsupported_version",
        )
    if (
        status.get("mode") != "workflow"
        or status.get("runId") != run_id
        or status.get("sessionId") != session_id
        or status.get("state") not in {"running", "complete"}
        or status.get("stopped")
        or status.get("timedOut")
        or status.get("error")
        or status.get("terminalOutcome")
    ):
        raise SpecError(
            "native workflow is foreign or not successful", "incompatible_handoff"
        )
    steps = status.get("steps")
    workflow = status.get("workflow")
    emits = workflow.get("emits") if isinstance(workflow, dict) else None
    if not isinstance(steps, list) or not isinstance(emits, list):
        raise SpecError("native child coverage is unavailable", "stale_evidence")
    expected = {child.key: child for child in children}
    if not expected or len(expected) != len(children):
        raise SpecError(
            "native child coverage must be nonempty and unique", "invalid_completion"
        )
    indexed = {}
    for step in steps:
        if not isinstance(step, dict) or "workflowKey" not in step:
            continue
        key = step["workflowKey"]
        if not isinstance(key, str):
            raise SpecError("malformed native child key", "invalid_completion")
        if key in indexed:
            raise SpecError("duplicate native child evidence", "invalid_completion")
        indexed[key] = step
    pointers = {}
    for emission in emits:
        if (
            not isinstance(emission, dict)
            or emission.get("kind") != "concorde.child-terminal"
        ):
            continue
        if not isinstance(emission.get("key"), str):
            raise SpecError("malformed native emission key", "invalid_completion")
        if emission.get("ticket") != ticket or emission.get("key") in pointers:
            raise SpecError(
                "foreign or duplicate native emission", "incompatible_handoff"
            )
        pointers[emission.get("key")] = emission
    if set(indexed) != set(expected) or set(pointers) != set(expected):
        raise SpecError(
            "native review or workflow coverage is incomplete", "invalid_completion"
        )
    records = []
    for key, child in expected.items():
        step, pointer = indexed[key], pointers[key]
        if (
            step.get("parentWorkflowRunId") != run_id
            or step.get("agent") != child.agent
            or step.get("status") != "completed"
            or not step.get("runId")
            or step.get("runId") != pointer.get("runId")
            or step.get("error")
            or step.get("stopped")
            or step.get("timedOut")
            or pointer.get("invocation_id") != child.invocation_id
            or pointer.get("proposal_digest") != child.proposal_digest
            or not isinstance(pointer.get("metadata"), str)
        ):
            raise SpecError(
                "native child is foreign or incomplete", "invalid_completion"
            )
        metadata = _record(Path(pointer["metadata"]))
        if any(
            key in metadata for key in ("schema_version", "lifecycleArtifactVersion")
        ):
            raise SpecError(
                "expected explicitly admitted versionless child metadata",
                "unsupported_version",
            )
        if (
            metadata.get("runId") != step["runId"]
            or metadata.get("agent") != child.agent
            or type(metadata.get("exitCode")) is not int
            or metadata["exitCode"] != 0
            or metadata.get("error")
            or metadata.get("transcriptError")
        ):
            raise SpecError(
                "native child execution did not succeed", "execution_failed"
            )
        acceptance = metadata.get("acceptance")
        if not isinstance(acceptance, dict):
            raise SpecError("native acceptance is unavailable", "invalid_completion")
        gates = acceptance.get("verifyRuns")
        if (
            acceptance.get("status") != "verified"
            or not isinstance(gates, list)
            or len(gates) != 1
            or not isinstance(gates[0], dict)
        ):
            raise SpecError("native child gate did not verify", "invalid_completion")
        gate = gates[0]
        # Native structuredOutput belongs to the model. Only the separately
        # generated plain gate's stdout carries Host staging control.
        staged = staging_control(
            gate.get("stdout"),
            ticket=ticket,
            invocation_id=child.invocation_id,
            proposal_digest=child.proposal_digest,
        )
        if (
            "structuredOutput" in gate
            or gate.get("command") != child.gate_command
            or gate.get("status") != "passed"
            or type(gate.get("exitCode")) is not int
            or gate["exitCode"] != 0
            or staged.get("invocation_id") != child.invocation_id
            or staged.get("proposal_digest") != child.proposal_digest
            or staged.get("state") != "staged"
            or staged.get("accepted") is not False
        ):
            raise SpecError(
                "native gate is not bound to the proposal", "incompatible_handoff"
            )
        records.append(metadata)
    return tuple(records)


def verify_native_single(
    correlation, *, agent, session_id, ticket, proposal_digest, gate_command, runtime
):
    """Foreground native tool_result plus independently read native metadata.

    The loaded Pi extension supplies correlation from its exact tool_call/result
    pair, not from model args. Foreground artifacts omit parent session ownership;
    that ownership comes from the live Pi event context, never a invented field.
    No workflow status, history projection or returned proposal proves completion.
    """
    if not isinstance(runtime, NativeRuntimeBinding) or runtime.format != FORMAT:
        raise SpecError("unsupported native producer", "unsupported_version")
    details = correlation.get("details", {})
    rows = details.get("results")
    if (
        correlation.get("isError")
        or correlation.get("session_id") != session_id
        or not correlation.get("tool_call_id")
        or details.get("mode") != "single"
        or not details.get("runId")
        or not isinstance(rows, list)
        or len(rows) != 1
    ):
        raise SpecError(
            "native single result is foreign or incomplete", "execution_failed"
        )
    row = rows[0]
    if (
        not isinstance(row, dict)
        or row.get("agent") != agent
        or type(row.get("exitCode")) is not int
        or row["exitCode"] != 0
        or any(
            row.get(key)
            for key in (
                "error",
                "detached",
                "interrupted",
                "stopped",
                "terminalOutcome",
                "timedOut",
                "metadataSaveError",
                "outputSaveError",
                "transcriptError",
            )
        )
    ):
        raise SpecError("native assessment did not complete", "execution_failed")
    launch = correlation.get("launch_contract_digest")
    if not launch or row.get("launchContractDigest") != launch:
        raise SpecError(
            "native preflight differs from execution", "incompatible_handoff"
        )
    native_proposal = _record(Path(row.get("structuredOutputPath", "")))
    if (
        digest(native_proposal) != proposal_digest
        or native_proposal.get("invocation_id") != ticket
    ):
        raise SpecError(
            "native structured proposal differs from captured proposal",
            "incompatible_handoff",
        )
    metadata = _record(Path(row.get("artifactPaths", {}).get("metadataPath", "")))
    if any(key in metadata for key in ("schema_version", "lifecycleArtifactVersion")):
        raise SpecError("expected versionless native metadata", "unsupported_version")
    if (
        metadata.get("runId") != details["runId"]
        or metadata.get("agent") != agent
        or metadata.get("launchContractDigest") != launch
        or type(metadata.get("exitCode")) is not int
        or metadata["exitCode"] != 0
        or metadata.get("error")
        or metadata.get("transcriptError")
        or metadata.get("processSignal")
    ):
        raise SpecError("native terminal metadata disagrees", "execution_failed")
    acceptance = metadata.get("acceptance", {})
    gates = acceptance.get("verifyRuns")
    if (
        acceptance.get("status") != "verified"
        or not isinstance(gates, list)
        or len(gates) != 1
        or not isinstance(gates[0], dict)
    ):
        raise SpecError("native staging gate is missing", "invalid_completion")
    gate = gates[0]
    if (
        gate.get("command") != gate_command
        or gate.get("status") != "passed"
        or type(gate.get("exitCode")) is not int
        or gate["exitCode"] != 0
        or "structuredOutput" in gate
    ):
        raise SpecError("native gate is foreign or failed", "invalid_completion")
    staging_control(
        gate.get("stdout"),
        ticket=ticket,
        invocation_id=ticket,
        proposal_digest=proposal_digest,
    )
    return metadata
