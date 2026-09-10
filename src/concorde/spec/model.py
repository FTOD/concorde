"""Immutable result entities shared by Concorde Tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    source: str
    message: str
    remediation: str
    line: int | None = None
    column: int | None = None
    subject_id: str | None = None


@dataclass(frozen=True)
class ProposalFile:
    path: str
    content: str
    sha256: str


@dataclass(frozen=True)
class ToolResult:
    tool: str
    target: str
    status: str
    artifacts: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    result: Mapping[str, Any] = field(default_factory=dict)
