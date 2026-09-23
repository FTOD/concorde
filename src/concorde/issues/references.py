"""Issue observations are the sole problem content; stages carry only scoped judgments."""

from __future__ import annotations

from .store import resolve_report
from .shapes import RECEIPT
from ..spec.typed_data import check_schema, typed
from ..spec.repository import SpecError


def receipt(reference: dict) -> dict:
    value = {key: reference[key] for key in RECEIPT["properties"]}
    check_schema(value, RECEIPT)
    return value


def review_blockers(issues: list[dict]) -> list[dict]:
    return [
        {**receipt(item), "blocked_step": item["affected_task"]}
        for item in issues
        if item["severity"] == "blocking"
    ]


def observation_context(root, references: list[dict]) -> dict:
    """Admit contract-level report text, never whole history, code bodies or tool logs."""
    unique = {item["report_id"]: receipt(item) for item in references}
    observations = []
    for ref in unique.values():
        report = resolve_report(root, ref)["report"]
        observations.append(
            {
                "receipt": ref,
                **{key: report[key] for key in ("description", "impact", "basis")},
            }
        )
    return typed("concorde-issue-context", {"observations": observations})


def validate_references(root, references: list[dict], *, admitted: list[dict]) -> None:
    allowed = {tuple(ref[key] for key in RECEIPT["properties"]) for ref in admitted}
    seen = set()
    for reference in references:
        ref = receipt(reference)
        key = tuple(ref[name] for name in RECEIPT["properties"])
        if key not in allowed:
            raise SpecError(
                "Issue reference was neither reported nor admitted for this worker",
                "permission_denied",
            )
        if key in seen:
            raise SpecError(
                "Issue observation is repeated in the result", "invalid_completion"
            )
        seen.add(key)
        resolve_report(root, ref)


def requires_contract_repair(root, references: list[dict]) -> bool:
    for reference in references:
        report = resolve_report(root, receipt(reference))["report"]
        if report["type"] == "gap" and report["subtype"] in {
            "missing-contract",
            "spec-conflict",
        }:
            return True
    return False
