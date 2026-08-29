"""Current-level scenario and governing-contract validation."""

from __future__ import annotations

from typing import Any

from ..model import Finding, SourceDocument
from ..projection import contract_reference


def validate_scenarios(package: Any) -> list[Finding]:
    findings: list[Finding] = []
    modules = {item.identifier: item for item in package.documents("module")}
    for module in modules.values():
        diagrams = package.module_diagrams(module)
        if not diagrams:
            continue
        visible_scenarios: dict[str, set[str]] = {}
        for view_path, view in diagrams.items():
            for item in view.get("meta", {}).get("views", []):
                if isinstance(item, dict) and item.get("id"):
                    visible_scenarios.setdefault(item["id"], set(item.get("focus", [])))
            if view.get("diagram_type") != "architecture":
                continue
            components = {item.get("id"): item for item in view.get("components", []) if isinstance(item, dict) and item.get("id")}
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
                            f"Boundary connection '{connection.get('id')}' in '{view_path}' has no resolvable governing contract.",
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
                            f"Scenario '{scenario_id}' is not defined in any diagram of the providing module.",
                            "Add the representative scenario to one of the module's diagrams under architecture/diagrams/ or mark it prose-only with rationale.",
                            subject_id=feature.identifier,
                        )
                    )
    return findings
