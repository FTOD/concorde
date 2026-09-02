"""Canonical diagnostics and result serialization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .model import Finding, OperationResult


STATUS_EXIT_CODES = {
    "success": 0,
    "proposal": 0,
    "eligible": 0,
    "selected": 0,
    "delivered": 0,
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
    operation: str,
    target: str,
    status: str,
    artifacts: Iterable[str],
    findings: Iterable[Finding],
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation": operation,
        "target": target,
        "status": status,
        "artifacts": sorted(set(artifacts)),
        "findings": [finding_dict(item) for item in sorted(findings, key=finding_key)],
        "result": result,
    }


def operation_envelope(value: OperationResult) -> dict[str, Any]:
    if value.operation == "deliver":
        return {
            "schema_version": 12,
            "operation": value.operation,
            "target": value.target,
            "status": value.status,
            "workspace": value.result.get("workspace"),
            "changes": value.result.get("changes", []),
            "artifacts": sorted(set(value.artifacts)),
            "findings": [finding_dict(item) for item in sorted(value.findings, key=finding_key)],
            "source_digest": value.result.get("source_digest", "sha256:" + "0" * 64),
            **{
                key: value.result[key]
                for key in (
                    "proposal_path",
                    "proposal_version",
                    "task_summary",
                    "checklist_summary",
                    "evidence_summary",
                    "removed_artifacts",
                    "retained_artifacts",
                    "retained_digests",
                    "reflection_summary",
                )
                if key in value.result
            },
        }
    return envelope(
        value.operation,
        value.target,
        value.status,
        value.artifacts,
        value.findings,
        dict(value.result),
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def exit_code(status: str) -> int:
    return STATUS_EXIT_CODES.get(status, 3)


def digest_sources(root: Path, paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(set(paths)):
        data = (root / relative).read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data.replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"
