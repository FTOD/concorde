"""The error chain: how every Concorde actor reports an error it could not handle.

An error is one **link** written by the actor that reports it: which level and actor it is, a
stable code, a complete description of what went wrong, the evidence, what the actor tried, why
the actor could not handle the error itself (``unhandled``), the options and recommendation it
offers its parent, and the errors of its children that it received and could not handle
(``causes``). A parent that cannot handle an error never replaces it: it adds its own link with
the child's error among the causes, so the last receiver reads, level by level, why nobody below
could handle it. Several independent causes, such as every failing check, are siblings.

The schema is ``contract.concorde.error`` of the Framework's contracts.
"""

from __future__ import annotations

import re
import subprocess
import traceback
from pathlib import Path
from typing import Iterable

LEVELS = (
    "main-agent",
    "task-session",
    "workflow",
    "operation",
    "workers",
    "worker",
    "check",
    "component",
)

# Why an actor could not handle an error; the explanation names the specifics.
REASONS = {
    "permission": "the fix needs a read, write or tool the actor is not granted",
    "decision": "the fix needs a decision reserved to a higher level",
    "scope": "the fix lies outside the actor's task or bound Modules",
    "capability": "the actor has no means to repair this kind of error",
    "exhausted": "the actor used up its allowed rounds, turns, time or budget",
    "environment": "the environment failed and the actor cannot change it",
    "input": "the input the actor received is invalid and only its sender can correct it",
}

CODE = {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}
TEXT = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": TEXT}

EVIDENCE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "ref", "detail"],
    "properties": {
        "kind": TEXT,
        "ref": {"type": "string"},
        "detail": {"type": "string"},
    },
}

UNHANDLED_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reason", "explanation"],
    "properties": {
        "reason": {"enum": list(REASONS)},
        "explanation": TEXT,
    },
}

# The link schema; ``causes`` refers to ``#/$defs/error`` of the schema that embeds it.
LINK_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "level",
        "actor",
        "code",
        "detail",
        "evidence",
        "attempts",
        "unhandled",
        "options",
        "recommendation",
        "causes",
    ],
    "properties": {
        "level": {"enum": list(LEVELS)},
        "actor": TEXT,
        "code": CODE,
        "detail": TEXT,
        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "attempts": STRINGS,
        "unhandled": {"$ref": "#/$defs/unhandled"},
        "options": STRINGS,
        "recommendation": {"type": "string"},
        "causes": {"type": "array", "items": {"$ref": "#/$defs/error"}},
    },
}

# ``$defs`` an embedding schema merges into its own ``$defs``.
DEFS: dict = {
    "error": LINK_SCHEMA,
    "evidence": EVIDENCE_SCHEMA,
    "unhandled": UNHANDLED_SCHEMA,
}

# contract.concorde.error: one error with its causes, as a stand-alone schema.
ERROR_SCHEMA: dict = {"$ref": "#/$defs/error", "$defs": DEFS}

# What a worker reports about its own error: a link without level, actor or causes, which the
# host fills in from the run it launched.
WORKER_ERROR_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "code",
        "detail",
        "evidence",
        "attempts",
        "unhandled",
        "options",
        "recommendation",
    ],
    "properties": {
        "code": CODE,
        "detail": TEXT,
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "ref", "detail"],
                "properties": {
                    "kind": {"enum": ["file", "command", "output", "spec"]},
                    "ref": TEXT,
                    "detail": {"type": "string"},
                },
            },
        },
        "attempts": STRINGS,
        "unhandled": UNHANDLED_SCHEMA,
        "options": STRINGS,
        "recommendation": {"type": "string"},
    },
}


def evidence(kind: str, ref: str = "", detail: str = "") -> dict:
    return {"kind": kind, "ref": ref, "detail": detail}


def link(
    level: str,
    actor: str,
    code: str,
    detail: str,
    *,
    reason: str,
    explanation: str,
    evidence: Iterable[dict] = (),
    attempts: Iterable[str] = (),
    options: Iterable[str] = (),
    recommendation: str = "",
    causes: Iterable[dict | None] = (),
) -> dict:
    """One link of an error chain; ``None`` causes are dropped."""
    if level not in LEVELS:
        raise ValueError(f"unknown error level {level!r}")
    if reason not in REASONS:
        raise ValueError(f"unknown unhandled reason {reason!r}")
    return {
        "level": level,
        "actor": actor,
        "code": code,
        "detail": detail.strip() or code,
        "evidence": [dict(item) for item in evidence],
        "attempts": [item for item in attempts if item],
        "unhandled": {"reason": reason, "explanation": explanation.strip() or reason},
        "options": [item for item in options if item],
        "recommendation": recommendation,
        "causes": [item for item in causes if item is not None],
    }


def exception_detail(error: BaseException) -> str:
    """The type and message of an exception, with a failed command's exit status and output."""
    text = f"{type(error).__name__}: {error}"
    if isinstance(error, subprocess.CalledProcessError):
        output = error.stderr or error.output or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        if output.strip():
            text += f"; output: {output.strip()[-2000:]}"
    return text


def from_exception(
    actor: str,
    error: BaseException,
    *,
    code: str = "unexpected_error",
    reason: str = "capability",
    explanation: str = "",
    trace: Path | None = None,
) -> dict:
    """A component link for an exception; ``trace`` receives the full traceback."""
    found = []
    if trace is not None:
        trace.write_text(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
        )
        found.append(evidence("traceback", trace.as_posix(), "full traceback"))
    frames = traceback.extract_tb(error.__traceback__)
    if frames:
        last = frames[-1]
        found.append(
            evidence("raised-at", f"{last.filename}:{last.lineno}", last.name or "")
        )
    own = getattr(error, "code", None)
    if isinstance(own, str) and re.fullmatch(CODE["pattern"], own):
        code = own
    return link(
        "component",
        actor,
        code,
        exception_detail(error),
        reason=reason,
        explanation=explanation
        or "an unexpected exception ended the component; it has no recovery for it",
        evidence=found,
    )


def origins(error: dict) -> list[dict]:
    """The links without causes, where the chain started, in reading order."""
    if not error["causes"]:
        return [error]
    return [item for cause in error["causes"] for item in origins(cause)]


def codes(error: dict) -> list[str]:
    """Every code in the tree, outermost first."""
    return [error["code"]] + [code for item in error["causes"] for code in codes(item)]


def render(error: dict, depth: int = 0) -> str:
    """The chain as indented Markdown, outermost link first, for a human reader."""
    pad = "  " * depth
    detail = error["detail"].replace("\n", "\n" + pad + "  | ")
    lines = [
        f"{pad}- **{error['level']}** {error['actor']}: `{error['code']}`",
        f"{pad}  {detail}",
        f"{pad}  Not handled here ({error['unhandled']['reason']}): "
        f"{error['unhandled']['explanation']}",
    ]
    for item in error["attempts"]:
        lines.append(f"{pad}  Tried: {item}")
    for item in error["evidence"]:
        text = " ".join(part for part in (item["ref"], item["detail"]) if part)
        lines.append(f"{pad}  Evidence ({item['kind']}): {text}")
    if error["options"]:
        lines.append(f"{pad}  Options: " + "; ".join(error["options"]))
    if error["recommendation"]:
        lines.append(f"{pad}  Recommendation: {error['recommendation']}")
    for cause in error["causes"]:
        lines.append(f"{pad}  Caused by:")
        lines.append(render(cause, depth + 1))
    return "\n".join(lines)


__all__ = [
    "DEFS",
    "ERROR_SCHEMA",
    "LEVELS",
    "LINK_SCHEMA",
    "REASONS",
    "WORKER_ERROR_SCHEMA",
    "codes",
    "evidence",
    "exception_detail",
    "from_exception",
    "link",
    "origins",
    "render",
]
