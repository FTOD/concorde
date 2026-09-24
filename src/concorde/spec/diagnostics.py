"""Canonical diagnostics and result serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from .errors import SpecError
from .model import Finding, ToolResult


STATUS_EXIT_CODES = {
    "success": 0,
    "proposal": 0,
    "unchanged": 0,
    "invalid": 1,
    "conflict": 2,
    "failed": 3,
}


def finding_key(finding: Finding) -> tuple[Any, ...]:
    return (
        finding.rule_id,
        finding.source,
        finding.line or 0,
        finding.column or 0,
        finding.message,
    )


def finding_dict(finding: Finding) -> dict[str, Any]:
    value = asdict(finding)
    return {key: item for key, item in value.items() if item is not None}


def envelope(
    tool: str,
    target: str,
    status: str,
    artifacts: Iterable[str],
    findings: Iterable[Finding],
    result: dict[str, Any],
    error: SpecError | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "tool": tool,
        "target": target,
        "status": status,
        "artifacts": sorted(set(artifacts)),
        "findings": [finding_dict(item) for item in sorted(findings, key=finding_key)],
        "result": result,
        "error": error.record() if error is not None else None,
    }


def tool_envelope(value: ToolResult) -> dict[str, Any]:
    return envelope(
        value.tool,
        value.target,
        value.status,
        value.artifacts,
        value.findings,
        dict(value.result),
        value.error,
    )


def canonical_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def exit_code(status: str) -> int:
    return STATUS_EXIT_CODES.get(status, 3)
