"""Digest-bound architecture/interface readiness projection for one Profile 7 feature."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..diagnostics import finding_dict, finding_key
from .repository import ProjectRepository, RepositoryError
from .validation.entities import validate_entities, visible_entity_ids
from .validation.features import validate_features
from .validation.hierarchy import validate_hierarchy


def architecture_readiness(project_root: str | Path, feature_id: str) -> dict[str, Any]:
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        return {"feature_id": feature_id, "status": "incomplete", "source_digest": "sha256:" + "0" * 64, "findings": [{"rule_id": "CONCORDE-READY-001", "severity": "error", "source": ".concorde/config.json", "message": str(error), "remediation": "Correct the Profile 7 hierarchy and repeat readiness review."}]}
    matches = package.by_id.get(feature_id, ())
    if len(matches) != 1 or matches[0].kind != "feature":
        return {"feature_id": feature_id, "status": "incomplete", "source_digest": package.source_digest, "findings": [{"rule_id": "CONCORDE-READY-002", "severity": "error", "source": ".concorde/config.json", "message": f"Feature '{feature_id}' does not resolve exactly once.", "remediation": "Select one stable feature ID."}]}
    feature = package.features[feature_id]
    module = package.modules.get(feature.module)
    relevant_sources = {matches[0].path, module.path if module else ""}
    findings = [
        finding_dict(item)
        for item in sorted(
            [*validate_hierarchy(package), *validate_entities(package), *validate_features(package)],
            key=finding_key,
        )
        if item.source in relevant_sources or item.subject_id in {feature_id, feature.module}
    ]
    return {
        "feature_id": feature_id,
        "providing_module": feature.module,
        "module_architecture": module.path if module else None,
        "architecture_entities": sorted(visible_entity_ids(package, feature.module)) if module else [],
        "participating_entities": list(feature.architecture_zoom),
        "interfaces": {"provided": list(feature.provided_interfaces), "required": list(feature.required_interfaces)},
        "related_features": list(feature.related_features),
        "affected_diagrams": list(module.diagrams) if module else [],
        "source_digest": package.source_digest,
        "status": "incomplete" if findings else "ready",
        "findings": findings,
    }
