"""One-level bounded architecture context projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import Finding, OperationResult, SourceDocument
from .projection import module_projection, scenario_projections
from .repository import ProjectRepository, RepositoryError
from .feature_workspace import WorkspaceError, _summary, resolve_phase_paths


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
    scenarios = scenario_projections(view)
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
        "current_module": module_projection(package, module, True),
        "children": [module_projection(package, child, False) for child in children],
        "externals": externals,
        "scenarios": scenarios,
        "refinement_links": sorted(links, key=lambda item: (item["from"], item["to"])),
        "subfeatures": [],
        "parent_feature": None,
        "siblings": [],
        "deeper_references": sorted(child.identifier for child in children),
        "architecture_readiness": None,
        "feature_workspace": None,
        "feature_diagrams": [],
        "contracts": [],
        "evidence": [],
    }
    if target.kind == "feature":
        from .readiness import architecture_readiness

        parent_id = target.metadata.get("parent_feature")
        if isinstance(parent_id, str) and parent_id:
            parent_matches = package.by_id.get(parent_id, ())
            if len(parent_matches) == 1 and parent_matches[0].kind == "feature":
                parent = parent_matches[0]
                context["parent_feature"] = _summary(parent)
                siblings = []
                for child_id in parent.metadata.get("subfeatures", []):
                    if child_id == target.identifier:
                        continue
                    child_matches = package.by_id.get(child_id, ())
                    if len(child_matches) == 1 and child_matches[0].kind == "feature":
                        siblings.append(_summary(child_matches[0]))
                context["siblings"] = siblings
                artifacts.add(parent.path)
                parent_design = f"{Path(parent.path).parent.as_posix()}/design.md"
                if (package.project_root / parent_design).is_file():
                    artifacts.add(parent_design)
        else:
            children = []
            for child_id in target.metadata.get("subfeatures", []):
                child_matches = package.by_id.get(child_id, ())
                if len(child_matches) == 1 and child_matches[0].kind == "feature":
                    children.append(_summary(child_matches[0]))
            context["subfeatures"] = children

        context["architecture_readiness"] = architecture_readiness(project_root, target.identifier)
        feature_root = Path(target.path).parent.as_posix()
        try:
            workspace_paths = resolve_phase_paths(project_root, feature_root)
            implementation_artifacts = sorted(
                path for path in package.auxiliary if path.startswith(workspace_paths.implementation_dir + "/")
            )
            durable_artifacts = [target.path, workspace_paths.feature_design]
            diagram_projections = []
            for declaration in target.metadata.get("diagrams", []):
                if not isinstance(declaration, dict):
                    continue
                source = declaration.get("source")
                if not isinstance(source, str) or source not in package.diagrams:
                    continue
                diagram = package.diagrams[source]
                diagram_projections.append({
                    "source": source,
                    "role": declaration.get("role"),
                    "kind": declaration.get("kind"),
                    "scenarios": declaration.get("scenarios", []),
                    "output": declaration.get("output"),
                    "title": diagram.get("meta", {}).get("title"),
                })
                durable_artifacts.append(source)
            root_path = package.project_root / feature_root
            for directory in ("contracts", "checklists"):
                candidate = root_path / directory
                if candidate.is_dir():
                    durable_artifacts.extend(
                        path.relative_to(package.project_root).as_posix()
                        for path in sorted(candidate.rglob("*"))
                        if path.is_file() and not path.is_symlink()
                    )
            context["feature_workspace"] = {
                **workspace_paths.to_dict(),
                "durable_artifacts": sorted(durable_artifacts),
                "implementation_artifacts": implementation_artifacts,
            }
            context["feature_diagrams"] = sorted(diagram_projections, key=lambda item: item["source"])
            artifacts.update(durable_artifacts)
            artifacts.update(implementation_artifacts)
        except WorkspaceError:
            context["feature_workspace"] = None
        contract_ids = set()
        for metadata in (target.metadata, module.metadata):
            sets = metadata.get("contracts", {}) if isinstance(metadata.get("contracts"), dict) else {}
            contract_ids.update(sets.get("provided", []))
            contract_ids.update(sets.get("required", []))
        contract_sources = []
        for identifier in sorted(contract_ids):
            matches = package.by_id.get(identifier, ())
            if len(matches) == 1 and matches[0].kind == "contract":
                source = matches[0]
                contract_sources.append({"id": identifier, "path": source.path, "body": source.body, "metadata": dict(source.metadata)})
                artifacts.add(source.path)
        context["contracts"] = contract_sources
        evidence = target.metadata.get("evidence", [])
        context["evidence"] = evidence if isinstance(evidence, list) else []
    return OperationResult("context", requested_id, "success", tuple(sorted(artifacts)), result={"context": context})
