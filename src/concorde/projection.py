"""Reusable bounded projections from Profile 7 architecture and feature sources."""

from __future__ import annotations

import re
from typing import Any

from .model import SourceDocument


def markdown_section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def module_projection(package: Any, module: SourceDocument, include_text: bool) -> dict[str, Any]:
    normalized = package.modules[module.identifier]
    result: dict[str, Any] = {
        "id": module.identifier,
        "architecture": module.path,
        "organization": (
            {"parent": normalized.parent, "modules": list(normalized.modules)}
            if include_text
            else {"parent": normalized.parent, "position": "immediate-child"}
        ),
        "responsibility": normalized.responsibility,
        "boundary": normalized.boundary,
    }
    if include_text:
        result.update(
            {
                "features": list(normalized.features),
                "diagrams": list(normalized.diagrams),
                "entities": [
                    {
                        "id": entity.identifier,
                        "type": entity.entity_type,
                        "definition": entity.definition,
                        "locator": entity.locator,
                        "roles": list(entity.roles),
                    }
                    for entity in package.entities.values()
                    if entity.owner == module.identifier
                ],
                "relationships": [
                    {
                        "source": relationship.source_entity,
                        "predicate": relationship.predicate,
                        "target": relationship.target_entity,
                        "description": relationship.description,
                        "interface": relationship.interface,
                    }
                    for relationship in normalized.relationships
                ],
                "interactions": [
                    {
                        "id": interaction.identifier,
                        "trigger": interaction.trigger,
                        "steps": list(interaction.steps),
                        "result": interaction.result,
                        "interfaces": list(interaction.interfaces),
                    }
                    for identifier in normalized.interactions
                    if (interaction := package.interactions.get(identifier)) is not None
                ],
            }
        )
    return result


def feature_summary(package: Any, feature: SourceDocument) -> dict[str, Any]:
    normalized = package.features[feature.identifier]
    title = next((line[2:].strip() for line in feature.body.splitlines() if line.startswith("# ")), feature.identifier)
    return {
        "feature_id": feature.identifier,
        "title": re.sub(r"^Feature Design:\s*", "", title),
        "module": normalized.module,
        "feature_path": feature.path,
        "outcome": " ".join(normalized.outcome.split()),
        "evidence_status": normalized.evidence_status,
    }


def scenario_projections(view: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep diagram-view summaries as generated navigation, never architecture authority."""
    result: list[dict[str, Any]] = []
    for item in view.get("meta", {}).get("views", []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result.append({"id": item["id"], "participants": list(item.get("focus", [])), "interactions": []})
    return sorted(result, key=lambda item: item["id"])


def contract_reference(connection: dict[str, Any]) -> str | None:
    """Compatibility helper: diagram links may preserve a contract.* interface identity."""
    explicit = connection.get("interface", connection.get("contract"))
    if isinstance(explicit, str):
        return explicit
    match = re.search(r"\b((?:contract|interface)\.[a-z0-9.-]+)\b", str(connection.get("label", "")))
    return match.group(1) if match else None
