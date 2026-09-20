"""Prototype reader for native terminal evidence, not yet a production adapter.

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

from ..spec.repository import SpecError
from ..spec.typed_data import decode

MAX_NATIVE_RECORD_BYTES = 16 * 1024 * 1024


def _record(path: Path) -> dict:
    if not path.is_absolute() or any(
        parent.is_symlink() for parent in (path, *path.parents)
    ):
        raise SpecError("native evidence path is not canonical", "unsafe_path")
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
) -> tuple[dict, ...]:
    """Require exact complete coverage, with no workflow receipt publication cycle.

    ``status.json`` is the documented native async artifact. Integration requires
    proving publication of terminal child metadata and emitted references before
    this read, race-safe run binding, retention limits and version admission.
    Those production adapter checks are pending; synthetic fixtures only test
    this reader. Missing/stale artifacts fail closed, including write loss.
    The enclosing workflow may still be running at this explicit domain commit
    boundary; later cancellation does not undo an already durable domain commit.
    """
    status = _record(directory / "status.json")
    if (
        status.get("id", status.get("runId")) != run_id
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
    emits = status.get("workflow", {}).get("emits")
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
        acceptance = metadata.get("acceptance") or {}
        gates = acceptance.get("verifyRuns") or []
        if acceptance.get("status") != "verified" or len(gates) != 1:
            raise SpecError("native child gate did not verify", "invalid_completion")
        gate = gates[0]
        staged = gate.get("structuredOutput") or {}
        if (
            gate.get("command") != child.gate_command
            or gate.get("status") != "passed"
            or gate.get("exitCode") != 0
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
