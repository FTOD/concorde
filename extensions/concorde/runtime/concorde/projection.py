"""Reusable one-level projections from maintained Concorde sources."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from .model import SourceDocument


def markdown_section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def contract_records(package: Any, identifiers: list[str], role: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for identifier in identifiers:
        matches = package.by_id.get(identifier, ())
        source = matches[0] if len(matches) == 1 and matches[0].kind == "contract" else None
        metadata = source.metadata if source else {}
        counterparties = metadata.get("counterparties", [])
        records.append(
            {
                "id": identifier,
                "role": metadata.get("role", role),
                "flow": metadata.get("flow", "unknown"),
                "counterparties": counterparties if isinstance(counterparties, list) else [],
            }
        )
    return records


def module_projection(package: Any, module: SourceDocument, include_text: bool) -> dict[str, Any]:
    metadata = module.metadata
    contracts = metadata.get("contracts", {}) if isinstance(metadata.get("contracts"), dict) else {}
    result: dict[str, Any] = {
        "id": module.identifier,
        "contracts": {
            "provided": contract_records(package, list(contracts.get("provided", [])), "provided"),
            "required": contract_records(package, list(contracts.get("required", [])), "required"),
        },
        "organization": (
            {"parent": metadata.get("parent"), "children": list(metadata.get("children", []))}
            if include_text
            else {"parent": metadata.get("parent"), "position": "immediate-child"}
        ),
    }
    if include_text:
        module_dir = PurePosixPath(module.path).parent.as_posix()
        result["summary"] = module.path
        result["design_reference"] = f"{module_dir}/design.md"
        result["diagrams"] = sorted(package.module_diagrams(module))
        result["features"] = list(metadata.get("features", []))
        result["responsibility"] = markdown_section(module.body, "Responsibility")
        result["boundary"] = markdown_section(module.body, "Boundary")
    return result


def scenario_projections(view: dict[str, Any]) -> list[dict[str, Any]]:
    components = {
        item.get("id"): item.get("module_id")
        or (item.get("tag") if str(item.get("tag", "")).startswith(("module.", "feature.")) else None)
        or item.get("stable_id")
        or f"external.{item.get('id')}"
        for item in view.get("components", [])
        if isinstance(item, dict) and item.get("id")
    }
    connections = [item for item in view.get("connections", []) if isinstance(item, dict)]
    scenarios: list[dict[str, Any]] = []
    for scenario in view.get("meta", {}).get("views", []):
        if not isinstance(scenario, dict) or not scenario.get("id"):
            continue
        focus = [item for item in scenario.get("focus", []) if item in components]
        focus_set = set(focus)
        interactions = []
        for connection in connections:
            endpoints = {connection.get("from"), connection.get("to")}
            if focus_set and not endpoints.issubset(focus_set):
                continue
            interactions.append(
                {
                    "id": connection.get("id"),
                    "from": components.get(connection.get("from"), connection.get("from")),
                    "to": components.get(connection.get("to"), connection.get("to")),
                    "description": connection.get("label", ""),
                    "contract": contract_reference(connection),
                }
            )
        scenarios.append(
            {
                "id": scenario["id"],
                "participants": [components[item] for item in focus],
                "interactions": interactions,
            }
        )
    return sorted(scenarios, key=lambda item: item["id"])


def contract_reference(connection: dict[str, Any]) -> str | None:
    explicit = connection.get("contract")
    if isinstance(explicit, str):
        return explicit
    match = re.search(r"\b(contract\.[a-z0-9.-]+)\b", str(connection.get("label", "")))
    if match:
        return match.group(1)
    identifier = connection.get("id")
    if isinstance(identifier, str) and identifier.startswith("contract_"):
        return identifier.split("__", 1)[0].replace("_", ".")
    return None
