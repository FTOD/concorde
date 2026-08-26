"""Digest-bound architecture readiness projection for one feature."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .diagnostics import finding_dict, finding_key
from .repository import ProjectRepository, RepositoryError
from .validation.scenarios import validate_scenarios
from .projection import contract_reference


def architecture_readiness(project_root: str | Path, feature_id: str) -> dict[str, Any]:
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        return {"feature_id": feature_id, "status": "incomplete", "source_digest": "sha256:" + "0" * 64, "findings": [{"rule_id": "CONCORDE-READY-001", "severity": "error", "source": ".concorde/config.json", "message": str(error), "remediation": "Correct the source hierarchy and repeat readiness review."}]}
    matches = package.by_id.get(feature_id, ())
    if len(matches) != 1 or matches[0].kind != "feature":
        return {"feature_id": feature_id, "status": "incomplete", "source_digest": package.source_digest, "findings": [{"rule_id": "CONCORDE-READY-002", "severity": "error", "source": ".concorde/config.json", "message": f"Feature '{feature_id}' does not resolve exactly once.", "remediation": "Select one stable feature ID."}]}
    feature = matches[0]
    module_id = feature.metadata.get("module")
    module_matches = package.by_id.get(module_id, ())
    module = module_matches[0] if len(module_matches) == 1 and module_matches[0].kind == "module" else None
    findings = [] if module else [{"rule_id": "CONCORDE-READY-003", "severity": "error", "source": feature.path, "message": "Providing module does not resolve.", "remediation": "Correct feature ownership before plan approval."}]
    scenario_findings = validate_scenarios(package)
    if module:
        scenario_findings = [item for item in scenario_findings if item.source in {module.path, feature.path}]
        findings.extend(finding_dict(item) for item in sorted(scenario_findings, key=finding_key))
    view_path = module.metadata.get("view") if module else None
    view = package.views.get(view_path, {}) if isinstance(view_path, str) else {}
    feature_scenarios = set(feature.metadata.get("scenarios", []))
    scenario_focus = {
        item.get("id"): list(item.get("focus", []))
        for item in view.get("meta", {}).get("views", [])
        if isinstance(item, dict) and item.get("id") in feature_scenarios
    }
    relevant_connections = [
        item for item in view.get("connections", [])
        if isinstance(item, dict) and any({item.get("from"), item.get("to")}.issubset(set(focus)) for focus in scenario_focus.values())
    ]
    return {
        "feature_id": feature.identifier,
        "workspace_kind": "subfeature" if feature.metadata.get("parent_feature") else "feature",
        "parent_feature": feature.metadata.get("parent_feature"),
        "subfeatures": list(feature.metadata.get("subfeatures", [])),
        "providing_module": module_id,
        "abstraction_level": module_id,
        "participating_children": sorted(module.metadata.get("children", [])) if module else [],
        "refinements": sorted(feature.metadata.get("refines", [])),
        "contract_crossings": [
            {"interaction": item.get("id"), "contract": contract_reference(item), "from": item.get("from"), "to": item.get("to")}
            for item in relevant_connections
        ],
        "dependency_direction": [{"from": item.get("from"), "to": item.get("to")} for item in relevant_connections],
        "affected_views": [view_path] if isinstance(view_path, str) else [],
        "expected_evidence": [
            {"kind": kind, "status": "unknown"}
            for kind in ("implementation", "test", "validation", "generated")
        ],
        "source_digest": package.source_digest,
        "status": "incomplete" if findings else "ready",
        "approval": None,
        "findings": findings,
    }
