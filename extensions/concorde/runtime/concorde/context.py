"""One-level bounded architecture context projection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .model import Finding, OperationResult, SourceDocument
from .repository import ProjectRepository, RepositoryError


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _contract_records(package: Any, identifiers: list[str], role: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for identifier in identifiers:
        matches = package.by_id.get(identifier, ())
        metadata = matches[0].metadata if len(matches) == 1 and matches[0].kind == "contract" else {}
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


def _module_projection(package: Any, module: SourceDocument, include_text: bool) -> dict[str, Any]:
    metadata = module.metadata
    contracts = metadata.get("contracts", {}) if isinstance(metadata.get("contracts"), dict) else {}
    result: dict[str, Any] = {
        "id": module.identifier,
        "contracts": {
            "provided": _contract_records(package, list(contracts.get("provided", [])), "provided"),
            "required": _contract_records(package, list(contracts.get("required", [])), "required"),
        },
        "organization": (
            {"parent": metadata.get("parent"), "children": list(metadata.get("children", []))}
            if include_text
            else {"parent": metadata.get("parent"), "position": "immediate-child"}
        ),
    }
    if include_text:
        result["features"] = list(metadata.get("features", []))
        result["responsibility"] = _section(module.body, "Responsibility")
        result["boundary"] = _section(module.body, "Boundary")
    return result


def bounded_context(project_root: str | Path, requested_id: str) -> OperationResult:
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        finding = Finding("CONCORDE-SOURCE-001", "error", ".concorde/config.json", str(error), "Correct the source profile or malformed maintained source and retry.")
        return OperationResult("context", requested_id, "invalid", findings=(finding,))
    matches = package.by_id.get(requested_id, ())
    if len(matches) != 1 or matches[0].kind not in {"module", "feature"}:
        finding = Finding("CONCORDE-CONTEXT-001", "error", ".concorde/config.json", f"Target '{requested_id}' does not resolve to exactly one module or feature.", "Pass one unique stable module or feature ID from the configured hierarchy.")
        return OperationResult("context", requested_id, "invalid", tuple(source.path for source in package.sources), (finding,))
    target = matches[0]
    module_id = target.identifier if target.kind == "module" else target.metadata.get("module")
    module_matches = package.by_id.get(module_id, ())
    if len(module_matches) != 1 or module_matches[0].kind != "module":
        finding = Finding("CONCORDE-CONTEXT-002", "error", target.path, f"Providing module '{module_id}' does not resolve exactly once.", "Correct the feature's providing module reference.", subject_id=target.identifier)
        return OperationResult("context", requested_id, "invalid", findings=(finding,))
    module = module_matches[0]
    children: list[SourceDocument] = []
    for child_id in module.metadata.get("children", []):
        child_matches = package.by_id.get(child_id, ())
        if len(child_matches) != 1 or child_matches[0].kind != "module":
            finding = Finding("CONCORDE-CONTEXT-003", "error", module.path, f"Child module '{child_id}' does not resolve exactly once.", "Correct the child reference before requesting bounded context.", subject_id=module.identifier)
            return OperationResult("context", requested_id, "invalid", findings=(finding,))
        children.append(child_matches[0])
    view_path = module.metadata.get("view")
    view = package.views.get(view_path, {}) if isinstance(view_path, str) else {}
    externals = sorted(
        {
            component.get("stable_id", f"external.{component.get('id')}")
            for component in view.get("components", [])
            if component.get("type") == "external" and component.get("id")
        }
    )
    scenarios = sorted(
        item.get("id") for item in view.get("meta", {}).get("views", []) if isinstance(item, dict) and item.get("id")
    )
    current_features = set(module.metadata.get("features", []))
    child_ids = {child.identifier for child in children}
    links: list[dict[str, str]] = []
    for feature in package.documents("feature"):
        for refined in feature.metadata.get("refines", []):
            if (feature.metadata.get("module") in child_ids and refined in current_features) or feature.identifier in current_features:
                links.append({"from": feature.identifier, "to": refined})
    artifacts = {module.path}
    if isinstance(view_path, str):
        artifacts.add(view_path)
    artifacts.update(child.path for child in children)
    context = {
        "requested_id": requested_id,
        "current_module": _module_projection(package, module, True),
        "children": [_module_projection(package, child, False) for child in children],
        "externals": externals,
        "scenarios": scenarios,
        "refinement_links": sorted(links, key=lambda item: (item["from"], item["to"])),
        "deeper_references": sorted(child.identifier for child in children),
    }
    return OperationResult("context", requested_id, "success", tuple(sorted(artifacts)), result={"context": context})
