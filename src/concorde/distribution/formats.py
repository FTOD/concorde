"""The formats of other parts that Distribution writes or reads itself, without their code.

Distribution is installed with any part, the spec part alone included, and depends on none, so it
meets the few formats it shares with them on its own, as the spec part does: Tracing's error link
(``contract.tracing.error``), in whose shape the installer, ``concorde update``, the ``concorde``
command and the project MCP server refuse, and Spec core's shared command-line envelope, which the
distribution commands print and which Distribution amends for ``spec-validation`` and
``init --apply``.
"""

from __future__ import annotations

import json
import re
import traceback
from collections.abc import Iterable
from typing import Any

# contract.tracing.error: the reasons an actor gives for not handling an error.
REASONS = (
    "permission",
    "decision",
    "scope",
    "capability",
    "exhausted",
    "environment",
    "input",
)
CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def evidence(kind: str, ref: str = "", detail: str = "") -> dict:
    return {"kind": kind, "ref": ref, "detail": detail}


def link(
    actor: str,
    code: str,
    detail: str,
    *,
    reason: str,
    explanation: str,
    evidence: Iterable[dict] = (),
    options: Iterable[str] = (),
    recommendation: str = "",
    causes: Iterable[dict] = (),
) -> dict:
    """One ``component`` link of an error chain, in Tracing's error contract."""
    if reason not in REASONS:
        raise ValueError(f"unknown unhandled reason {reason!r}")
    return {
        "level": "component",
        "actor": actor,
        "code": code,
        "detail": detail.strip() or code,
        "evidence": [dict(item) for item in evidence],
        "attempts": [],
        "unhandled": {"reason": reason, "explanation": explanation.strip() or reason},
        "options": [item for item in options if item],
        "recommendation": recommendation,
        "causes": list(causes),
    }


def from_exception(actor: str, error: BaseException, *, explanation: str) -> dict:
    """The link of an unexpected exception, naming where it was raised."""
    frames = traceback.extract_tb(error.__traceback__)
    found = (
        [
            evidence(
                "raised-at",
                f"{frames[-1].filename}:{frames[-1].lineno}",
                frames[-1].name,
            )
        ]
        if frames
        else []
    )
    own = getattr(error, "code", None)
    code = (
        own if isinstance(own, str) and CODE_PATTERN.match(own) else "unexpected_error"
    )
    return link(
        actor,
        code,
        f"{type(error).__name__}: {error}",
        reason="capability",
        explanation=explanation,
        evidence=found,
    )


def render(error: dict, depth: int = 0) -> str:
    """An error chain as indented Markdown, outermost link first, for a human reader."""
    pad = "  " * depth
    unhandled = error.get("unhandled") or {}
    lines = [
        f"{pad}- **{error.get('level')}** {error.get('actor')}: `{error.get('code')}`",
        f"{pad}  {str(error.get('detail', '')).replace(chr(10), chr(10) + pad + '  | ')}",
        f"{pad}  Not handled here ({unhandled.get('reason')}): {unhandled.get('explanation')}",
    ]
    for item in error.get("evidence") or ():
        text = " ".join(part for part in (item.get("ref"), item.get("detail")) if part)
        lines.append(f"{pad}  Evidence ({item.get('kind')}): {text}")
    for item in error.get("options") or ():
        lines.append(f"{pad}  Option: {item}")
    if error.get("recommendation"):
        lines.append(f"{pad}  Recommended: {error['recommendation']}")
    for cause in error.get("causes") or ():
        lines.append(render(cause, depth + 1))
    return "\n".join(lines)


# Spec core's shared command-line envelope (schema version 4) and the exit status of each status.
ENVELOPE_VERSION = 4
STATUS_EXIT_CODES = {
    "success": 0,
    "proposal": 0,
    "unchanged": 0,
    "invalid": 1,
    "conflict": 2,
    "failed": 3,
}


def finding(
    rule_id: str, strictness: str, source: str, message: str, remediation: str
) -> dict:
    return {
        "rule_id": rule_id,
        "strictness": strictness,
        "source": source,
        "message": message,
        "remediation": remediation,
    }


def _finding_key(item: dict) -> tuple:
    return (
        item["rule_id"],
        item["source"],
        item.get("line") or 0,
        item.get("column") or 0,
        item["message"],
    )


def error_record(
    code: str,
    message: str,
    *,
    reason: str,
    remediation: str,
    path: str | None = None,
    field: str | None = None,
    causes: Iterable[dict] = (),
) -> dict:
    """An error record in the envelope's ``error`` shape (``contract.spec.error``): code,
    message, reason, location, remediation and causes."""
    return {
        "code": code,
        "message": message,
        "reason": reason,
        "location": {"path": path, "line": None, "field": field, "subject": None},
        "remediation": remediation,
        "causes": list(causes),
    }


def system_cause(error: BaseException, path: str) -> dict:
    """An operating system error as the ``system_error`` cause of an error record."""
    return error_record(
        "system_error",
        f"{type(error).__name__}: {error}",
        reason="the operating system refused the operation",
        remediation="repair what the message names",
        path=path,
    )


def envelope(
    tool: str,
    status: str,
    *,
    artifacts: Iterable[str] = (),
    findings: Iterable[dict] = (),
    result: dict | None = None,
    error: dict | None = None,
) -> dict:
    """Spec core's shared envelope of one command."""
    return {
        "schema_version": ENVELOPE_VERSION,
        "tool": tool,
        "target": ".",
        "status": status,
        "artifacts": sorted(set(artifacts)),
        "findings": sorted(findings, key=_finding_key),
        "result": dict(result or {}),
        "error": error,
    }


def with_findings(
    payload: dict, findings: Iterable[dict], status: str | None = None
) -> dict:
    """The envelope with more findings, kept in the envelope's order, and maybe another status."""
    return {
        **payload,
        "status": status or payload["status"],
        "findings": sorted([*payload.get("findings", []), *findings], key=_finding_key),
    }


def canonical_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def exit_code(status: str) -> int:
    return STATUS_EXIT_CODES.get(status, 3)


__all__ = [
    "REASONS",
    "canonical_json",
    "envelope",
    "error_record",
    "evidence",
    "exit_code",
    "finding",
    "from_exception",
    "link",
    "render",
    "system_cause",
    "with_findings",
]
