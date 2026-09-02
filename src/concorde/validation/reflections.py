"""Project control-state reflection log shape, vocabulary, and reference rules."""

from __future__ import annotations

from typing import Any

from ..model import Finding
from ..reflections import log_path, parse_reflection_log, strip_reference_suffix
from ..repository import RepositoryError, safe_relative_path

RULE_BY_PROBLEM = {"shape": "CONCORDE-REFLECT-001", "duplicate": "CONCORDE-REFLECT-002", "vocabulary": "CONCORDE-REFLECT-003"}


def _visible_scenario_ids(package: Any) -> set[str]:
    return {
        view.get("id")
        for architecture in package.views.values()
        for view in architecture.get("meta", {}).get("views", [])
        if isinstance(view, dict) and isinstance(view.get("id"), str)
    }


def _reference_resolves(value: str, package: Any, scenario_ids: set[str]) -> bool:
    reference = strip_reference_suffix(value)
    if not reference:
        return False
    if reference in package.by_id or reference in package.entities or reference in package.interactions or reference in package.interfaces or reference in scenario_ids:
        return True
    try:
        relative = safe_relative_path(reference)
    except RepositoryError:
        return False
    return (package.project_root / relative).exists()


def validate_reflections(package: Any) -> list[Finding]:
    path = log_path()
    body = package.auxiliary.get(path)
    if body is None:
        return []  # an absent log is not a breach
    parsed = parse_reflection_log(body)
    findings: list[Finding] = []
    for problem in parsed.problems:
        findings.append(Finding(RULE_BY_PROBLEM[problem.code], "error", path, problem.message, problem.remediation, line=problem.line, subject_id=problem.identifier))
    scenario_ids = _visible_scenario_ids(package)
    for entry in parsed.entries:
        feature = entry.feature.strip()
        matches = package.by_id.get(feature, ())
        if feature and not (len(matches) == 1 and matches[0].kind == "feature"):
            findings.append(Finding("CONCORDE-REFLECT-004", "error", path, f"Entry {entry.identifier} is attributed to '{feature}', which is not a known feature.", "Set Feature to the stable ID of the feature selected when the problem was recorded.", line=entry.line, subject_id=entry.identifier))
        concerns = entry.fields.get("Concerns", "").strip()
        if concerns and not _reference_resolves(concerns, package, scenario_ids):
            findings.append(Finding("CONCORDE-REFLECT-004", "error", path, f"Entry {entry.identifier} concerns '{concerns}', which is neither a known stable ID nor an existing project-relative path.", "Cite a module, feature, entity, interaction, interface, scenario, or existing project-relative path (an optional #fragment or :line suffix is ignored).", line=entry.line, subject_id=entry.identifier))
    return findings
