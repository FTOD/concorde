"""Current-level scenario and governing-contract validation."""

from __future__ import annotations

from typing import Any

from ..model import Finding, SourceDocument
from ..projection import contract_reference


def validate_scenarios(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    modules = {item.identifier: item for item in package.documents("module")}
    for module in modules.values():
        view_path = module.metadata.get("view")
        view = package.views.get(view_path) if isinstance(view_path, str) else None
        if not isinstance(view, dict):
            continue
        components = {item.get("id"): item for item in view.get("components", []) if isinstance(item, dict) and item.get("id")}
        visible_scenarios = {
            item.get("id"): set(item.get("focus", []))
            for item in view.get("meta", {}).get("views", [])
            if isinstance(item, dict) and item.get("id")
        }
        for connection in view.get("connections", []):
            if not isinstance(connection, dict):
                continue
            source_id, target_id = connection.get("from"), connection.get("to")
            if source_id not in components or target_id not in components:
                continue
            contract = contract_reference(connection)
            if not isinstance(contract, str) or contract not in package.by_id:
                findings.append(
                    Finding(
                        "CONCORDE-SCENARIO-003",
                        "error",
                        module.path,
                        f"Boundary connection '{connection.get('id')}' has no resolvable governing contract.",
                        "Name one declared contract on every current-level boundary connection.",
                        subject_id=module.identifier,
                    )
                )
        for feature_id in module.metadata.get("features", []):
            matches = package.by_id.get(feature_id, ())
            if len(matches) != 1 or matches[0].kind != "feature":
                continue
            feature: SourceDocument = matches[0]
            for scenario_id in feature.metadata.get("scenarios", []):
                if scenario_id not in visible_scenarios:
                    findings.append(
                        Finding(
                            "CONCORDE-SCENARIO-004",
                            "error",
                            feature.path,
                            f"Scenario '{scenario_id}' is not defined in the providing module's current-level view.",
                            "Add the representative scenario to the current-level view or mark it prose-only with rationale.",
                            subject_id=feature.identifier,
                        )
                    )
    return findings
