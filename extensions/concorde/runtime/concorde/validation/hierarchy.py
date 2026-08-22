"""Module prose and explicit one-level view identity rules."""

from __future__ import annotations

from typing import Any

from ..model import Finding, SourceDocument
from ..projection import markdown_section


def _finding(rule: str, source: SourceDocument, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source.path, message, remediation, subject_id=source.identifier)


def validate_hierarchy(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    for module in package.documents("module"):
        for heading in ("Responsibility", "Boundary"):
            if not markdown_section(module.body, heading):
                findings.append(
                    _finding(
                        "CONCORDE-MODULE-001",
                        module,
                        f"Module {heading.lower()} is missing or empty.",
                        f"Add a non-empty ## {heading} section defining this module boundary.",
                    )
                )
        children = set(module.metadata.get("children", []))
        view_path = module.metadata.get("view")
        view = package.views.get(view_path) if isinstance(view_path, str) else None
        if not children or not isinstance(view, dict):
            continue
        declared = {
            item.get("module_id") or (item.get("tag") if str(item.get("tag", "")).startswith("module.") else None)
            for item in view.get("components", [])
            if isinstance(item, dict) and (item.get("module_id") or str(item.get("tag", "")).startswith("module."))
        }
        missing = children - declared
        if missing:
            findings.append(
                _finding(
                    "CONCORDE-VIEW-005",
                    module,
                    "Immediate child components lack explicit module_id values: " + ", ".join(sorted(missing)) + ".",
                    "Set module_id on every immediate-child component; do not rely on label inference.",
                )
            )
    return findings
