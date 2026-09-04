"""One-module bounded architecture and feature context projection."""

from __future__ import annotations

from pathlib import Path

from .feature_workspace import WorkspaceError, reflections_open_count, resolve_phase_paths
from ..model import Finding, ToolResult
from ..projection import feature_summary, module_projection
from ..reflections.reflections import index_path, parse_auxiliary_reflections, reflection_document_paths, reflections_path
from .repository import ProjectRepository, RepositoryError
from .validation.entities import module_ancestry


def bounded_context(project_root: str | Path, requested_id: str) -> ToolResult:
    try:
        package = ProjectRepository(project_root).load()
    except RepositoryError as error:
        finding = Finding("CONCORDE-SOURCE-001", "error", ".concorde/config.json", str(error), "Correct the Profile 7 source hierarchy and project control state, then retry.")
        return ToolResult("context", requested_id, "invalid", findings=(finding,))
    matches = package.by_id.get(requested_id, ())
    if len(matches) != 1 or matches[0].kind not in {"module", "feature"}:
        finding = Finding("CONCORDE-CONTEXT-001", "error", ".concorde/config.json", f"Target '{requested_id}' does not resolve to exactly one module or feature.", "Pass one unique stable module or feature ID.")
        return ToolResult("context", requested_id, "invalid", tuple(source.path for source in package.sources), (finding,))
    target = matches[0]
    module_id = target.identifier if target.kind == "module" else str(target.metadata.get("module", ""))
    module_matches = package.by_id.get(module_id, ())
    if len(module_matches) != 1 or module_matches[0].kind != "module":
        finding = Finding("CONCORDE-CONTEXT-002", "error", target.path, f"Providing module '{module_id}' does not resolve exactly once.", "Correct feature ownership.", subject_id=target.identifier)
        return ToolResult("context", requested_id, "invalid", findings=(finding,))
    module = module_matches[0]
    child_sources = []
    for child_id in package.modules[module_id].modules:
        child = package.by_id.get(child_id, ())
        if len(child) != 1 or child[0].kind != "module":
            finding = Finding("CONCORDE-CONTEXT-003", "error", module.path, f"Child module '{child_id}' does not resolve exactly once.", "Correct the module inventory before requesting context.", subject_id=module_id)
            return ToolResult("context", requested_id, "invalid", findings=(finding,))
        child_sources.append(child[0])

    ancestry_ids = module_ancestry(package, module_id)
    ancestry = [
        module_projection(package, package.by_id[ancestor][0], False)
        for ancestor in ancestry_ids
        if len(package.by_id.get(ancestor, ())) == 1
    ]
    related = []
    if target.kind == "feature":
        for relation in package.features[target.identifier].relations:
            candidates = package.by_id.get(relation.target, ())
            if len(candidates) == 1 and candidates[0].kind == "feature":
                summary = feature_summary(package, candidates[0])
                summary["relation"] = relation.relation
                related.append(summary)
    else:
        for identifier in package.modules[module_id].features:
            candidates = package.by_id.get(identifier, ())
            if len(candidates) == 1 and candidates[0].kind == "feature":
                related.append(feature_summary(package, candidates[0]))

    context = {
        "requested_id": requested_id,
        "current_module": module_projection(package, module, True),
        "children": [module_projection(package, child, False) for child in child_sources],
        "module_ancestry": ancestry,
        "related_features": related,
        "externals": sorted(entity.identifier for entity in package.entities.values() if entity.owner == module_id and entity.entity_type == "external-system"),
        "deeper_references": sorted(child.identifier for child in child_sources),
        "feature_workspace": None,
        "architecture_readiness": None,
        "reflections": None,
    }
    artifacts = {module.path, *package.module_diagrams(module), *(child.path for child in child_sources)}
    artifacts.update(item["architecture"] for item in ancestry)
    reflection_paths = reflection_document_paths(package.auxiliary)
    if reflection_paths or index_path() in package.auxiliary:
        parsed = parse_auxiliary_reflections(package.auxiliary)
        context["reflections"] = {
            "path": reflections_path(),
            "open": {
                feature_id: parsed.open_count(feature_id)
                for feature_id in sorted(package.features)
                if parsed.open_count(feature_id)
            },
        }
        artifacts.update(reflection_paths)
        if index_path() in package.auxiliary:
            artifacts.add(index_path())
    if target.kind == "feature":
        from .readiness import architecture_readiness

        context["architecture_readiness"] = architecture_readiness(project_root, target.identifier)
        try:
            paths = resolve_phase_paths(project_root, target.path)
            attempt_artifacts = sorted(
                path
                for path in package.auxiliary
                if paths.attempt_dir is not None and path.startswith(paths.attempt_dir + "/")
            )
            durable_artifacts = [target.path, paths.module_architecture]
            durable_artifacts.extend(item["architecture"] for item in paths.module_ancestry)
            context["feature_workspace"] = {
                **paths.to_dict(),
                "durable_artifacts": sorted(set(durable_artifacts)),
                "attempt_artifacts": attempt_artifacts,
            }
            artifacts.update(durable_artifacts)
            artifacts.update(attempt_artifacts)
        except WorkspaceError:
            context["feature_workspace"] = None
    return ToolResult("context", requested_id, "success", tuple(sorted(artifacts)), result={"context": context})
