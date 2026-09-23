"""Causal execution feedback. Diagnostic data is not acceptance or retry authority.

Only selected error fields cross this boundary, never exception __dict__, environment,
request bodies or transcripts. Messages are sanitized, not silently shortened.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from copy import deepcopy
from typing import Literal

from ..spec.repository import SpecError


def safe_text(value) -> str:
    text = re.sub(
        r"\n\nReceived arguments:[\s\S]*$",
        "\n[Argument values omitted from causal diagnostics]",
        str(value),
    )
    text = re.sub(
        r"\n\nOutput:\n[\s\S]*?(?=\n\nOutput artifact:|$)",
        "\n[Model output omitted from causal diagnostics]",
        text,
    )
    text = re.sub(r"(?i)(bearer\s+)[^\s\"',;]+", r"\1[REDACTED]", text)
    return re.sub(
        r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|authorization)\s*[\"']?\s*[:=]\s*[\"']?)[^\s\"',;}]+",
        r"\1[REDACTED]",
        text,
    )


def failure(
    message,
    *,
    code="execution_failed",
    layer="host",
    category="unknown",
    attempt=None,
    causes=(),
    references=(),
    diagnostics=None,
):
    return {
        "schema_version": 1,
        "code": code,
        "message": safe_text(message),
        "layer": layer,
        "category": category,
        "attempt": attempt,
        "causes": list(causes),
        "diagnostics": {
            "complete": all(
                cause.get("diagnostics", {}).get("complete", False) for cause in causes
            ),
            "redacted": True,
            "text": safe_text(diagnostics) if diagnostics is not None else None,
            "references": list(references),
        },
    }


def exception_feedback(error, *, layer="host", attempt=None, _seen=None):
    seen = set() if _seen is None else _seen
    if id(error) in seen:
        return failure("Cyclic exception cause; further cause unavailable", layer=layer)
    seen.add(id(error))
    if isinstance(getattr(error, "feedback", None), dict):
        return deepcopy(error.feedback)
    cause = error.__cause__ or (
        error.__context__ if not error.__suppress_context__ else None
    )
    code = (
        getattr(error, "code", None)
        or getattr(error, "errno", None)
        or type(error).__name__
    )
    category = {
        "cancelled": "cancelled",
        "limit_exhausted": "timeout",
        "invalid_completion": "invalid-completion",
    }.get(getattr(error, "outcome", None), "unknown")
    if isinstance(error, (asyncio.CancelledError, KeyboardInterrupt)):
        category = "cancelled"
    elif isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
        category = "timeout"
    elif type(error).__name__ in {"TypedDataError", "ContractError"}:
        category = "schema-rejection"
    elif isinstance(error, SpecError):
        category = "host-refusal"
    return failure(
        str(error),
        code=code,
        layer=layer,
        category=category,
        attempt=attempt,
        causes=[exception_feedback(cause, layer=layer, attempt=attempt, _seen=seen)]
        if cause
        else (),
    )


def error_entry(error, *, code=None, layer="host", attempt=None):
    return {
        "code": code or getattr(error, "code", None) or "execution_failed",
        "field": getattr(error, "field", ""),
        "message": safe_text(error),
        "feedback": exception_feedback(error, layer=layer, attempt=attempt),
    }


class OperationExecutionError(RuntimeError):
    """An Agent call was refused, failed, was cancelled, ran out of time or returned an invalid
    result. ``outcome`` classifies why; ``code`` preserves a contract rejection class. The host maps
    these to distinct result error codes, and none retries automatically."""

    def __init__(
        self,
        message: str,
        outcome: Literal[
            "failed", "cancelled", "limit_exhausted", "invalid_completion"
        ] = "failed",
        code: str | None = None,
    ):
        super().__init__(message)
        self.outcome = outcome
        self.code = code


class ExecutionFailure(SpecError):
    def __init__(self, feedback):
        super().__init__(feedback["message"], feedback["code"])
        self.feedback = feedback


def native_feedback(value, *, layer="native", attempt=None, references=()):
    """Select native error facts; absent submission evidence is not zero attempts."""
    value = value if isinstance(value, dict) else {}
    category = (
        "timeout"
        if value.get("timedOut")
        else "cancelled"
        if value.get("stopped")
        or value.get("interrupted")
        or value.get("state") == "stopped"
        else "native-exit"
        if value.get("exitCode") not in (None, 0)
        else "observation"
        if any(
            value.get(k)
            for k in ("metadataSaveError", "outputSaveError", "transcriptError")
        )
        else "unknown"
    )
    causes = []
    for key in ("error", "metadataSaveError", "outputSaveError", "transcriptError"):
        if value.get(key):
            causes.append(
                failure(
                    value[key],
                    code=key,
                    layer=layer,
                    category="observation" if key != "error" else category,
                    attempt=attempt,
                )
            )
    for row in value.get("results", []) + value.get("steps", []):
        if isinstance(row, dict) and (
            row.get("error")
            or row.get("status") in {"failed", "stopped"}
            or row.get("exitCode") not in (None, 0)
        ):
            causes.append(
                native_feedback(
                    row, layer=layer, attempt=row.get("runId") or row.get("workflowKey")
                )
            )
    facts = {
        key: value[key]
        for key in (
            "exitCode",
            "processSignal",
            "timedOut",
            "stopped",
            "interrupted",
            "detached",
            "terminalOutcome",
            "state",
            "status",
        )
        if key in value
    }
    from ..spec.typed_data import canonical

    result = failure(
        "Native execution did not complete successfully",
        layer=layer,
        category=category,
        attempt=attempt or value.get("runId"),
        causes=causes,
        references=references,
        diagnostics=canonical(facts),
    )
    result["diagnostics"]["complete"] = False
    return result


def workflow_feedback(base, status, binding):
    """Collect owned error records even when failed children emitted no success receipt."""
    from pathlib import Path

    from .native_evidence import _record

    directory = Path(base["directory"])
    feedback = native_feedback(
        status,
        layer="native-workflow",
        attempt=binding["runId"],
        references=[str(Path(binding["asyncDir"]) / "status.json")],
    )
    if (
        status.get("state") == "complete"
        and not (directory / "workflow-result.json").exists()
    ):
        feedback["causes"].append(
            failure(
                "Native workflow completed without a Host acceptance receipt",
                layer="workflow-host",
                category="observation",
                attempt=binding["runId"],
            )
        )
    for emission in status.get("workflow", {}).get("emits", []):
        if (
            isinstance(emission, dict)
            and emission.get("kind") == "concorde.failure"
            and isinstance(emission.get("feedback"), dict)
        ):
            feedback["causes"].append(emission["feedback"])
    files = list(directory.glob("host-failure-*.json"))
    slots = []
    try:
        for file in sorted((directory / "bindings").glob("*.json")):
            slots.append(_record(Path(_record(file)["descriptor"])))
        files.extend(
            Path(slot["directory"]) / "failure.json"
            for slot in slots
            if (Path(slot["directory"]) / "failure.json").exists()
        )
        for slot in slots:
            files.extend(Path(slot["directory"]).glob("submission-error-*.json"))
        for slot in slots:
            if (
                slot.get("agent")
                and slot.get("snapshot")
                and not (Path(slot["directory"]) / "proposal.json").exists()
                and not (Path(slot["directory"]) / "failure.json").exists()
                and not list(Path(slot["directory"]).glob("submission-error-*.json"))
            ):
                feedback["causes"].append(
                    failure(
                        "Issued slot has no captured proposal; submission attempts unknown",
                        layer="native-slot",
                        category="no-submission",
                        attempt=slot.get("ticket"),
                    )
                )
        for file in sorted(set(files)):
            feedback["causes"].append(_record(file))
            feedback["diagnostics"]["references"].append(str(file))
    except (ValueError, OSError) as error:
        feedback["diagnostics"]["complete"] = False
        feedback["causes"].append(
            exception_feedback(error, layer="failure-observation")
        )
    return feedback


def response_failure(message, response, *, layer, attempt=None):
    """A refused finite service already has causes; do not flatten it to parent prose."""
    envelope = response.get("result", response)
    causes = [
        row.get("feedback")
        or failure(
            row.get("message", "Unknown Host refusal"),
            code=row.get("code", "execution_failed"),
            layer="host",
            category="host-refusal",
            attempt=envelope.get("invocation_id"),
        )
        for row in envelope.get("errors", [])
    ]
    if response.get("failure"):
        causes.append(response["failure"])
    return ExecutionFailure(
        failure(
            message,
            code="invalid_completion",
            layer=layer,
            category="host-refusal",
            attempt=attempt,
            causes=causes,
        )
    )
