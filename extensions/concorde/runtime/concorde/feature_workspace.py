"""Safe nested feature-workspace resolution over the standard Spec Kit selection."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .model import SourceDocument
from .repository import (
    ProjectRepository,
    RepositoryError,
    classify_feature_root,
    safe_relative_path,
)


class WorkspaceError(ValueError):
    """A selected feature root is unsafe, stale, or structurally invalid."""


@dataclass(frozen=True)
class WorkspacePaths:
    workspace_kind: str
    feature_id: str | None
    providing_module: str | None
    parent_context: dict[str, str] | None
    siblings: tuple[dict[str, str], ...]
    feature_directory: str
    feature_spec: str
    feature_implementation: str
    module_summary: str
    module_design: str
    contracts_dir: str
    checklists_dir: str
    diagrams_dir: str
    implementation_dir: str
    implementation_state: str
    plan: str
    research: str
    data_model: str
    quickstart: str
    tasks: str
    validation: str

    def protocol_paths(self) -> dict[str, Any]:
        """Return the complete protocol-defined workspace path/state record."""
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ROOT_PHASES = frozenset({"specify", "clarify", "checklist", "contracts"})
IMPLEMENTATION_PHASES = frozenset(
    {"plan", "tasks", "implement", "analyze", "converge", "taskstoissues", "validation"}
)


def _implementation_state(root: Path) -> str:
    implementation = root / "implementation"
    if not implementation.exists():
        return "absent"
    if not implementation.is_dir() or implementation.is_symlink():
        raise WorkspaceError("implementation must be a real directory below the feature root")
    return "active" if any(implementation.iterdir()) else "active"


def _heading_value(body: str, heading: str) -> str:
    lines = body.splitlines()
    marker = f"## {heading}"
    try:
        start = lines.index(marker) + 1
    except ValueError:
        return ""
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            values.append(line.strip())
    return " ".join(values).strip()


def _title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return re.sub(r"^Feature Specification:\s*", "", line[2:].strip())
    return fallback


def _summary(feature: SourceDocument) -> dict[str, str]:
    return {
        "feature_id": feature.identifier,
        "title": _title(feature.body, feature.identifier),
        "outcome": _heading_value(feature.body, "Outcome") or _title(feature.body, feature.identifier),
        "evidence_status": str(feature.metadata.get("evidence_status", "unknown")),
        "feature_directory": Path(feature.path).parent.as_posix(),
        "implementation": f"{Path(feature.path).parent.as_posix()}/implementation.md",
    }


def _module_directory(relative: str, workspace_kind: str) -> str:
    """Return the directory of the module at which a canonical feature root is specified."""
    path = PurePosixPath(relative)
    depth = 1 if workspace_kind == "feature" else 3
    return path.parents[depth].as_posix()


def _module_paths(package: Any, module_id: Any, fallback_directory: str) -> tuple[str, str]:
    """Return the providing module's summary and design-reference paths."""
    directory = fallback_directory
    if isinstance(module_id, str) and module_id:
        matches = package.by_id.get(module_id, ())
        if len(matches) != 1 or matches[0].kind != "module":
            raise WorkspaceError(f"providing module '{module_id}' does not resolve exactly once")
        directory = Path(matches[0].path).parent.as_posix()
    return f"{directory}/module.md", f"{directory}/design.md"


def _workspace_relationships(package: Any, feature: SourceDocument) -> tuple[str, dict[str, str] | None, tuple[dict[str, str], ...]]:
    parent_id = feature.metadata.get("parent_feature")
    if not isinstance(parent_id, str) or not parent_id:
        return "feature", None, ()
    if feature.metadata.get("subfeatures"):
        raise WorkspaceError("a sub-feature cannot register another sub-feature")
    matches = package.by_id.get(parent_id, ())
    if len(matches) != 1 or matches[0].kind != "feature":
        raise WorkspaceError(f"parent feature '{parent_id}' does not resolve exactly once")
    parent = matches[0]
    parent_root = Path(parent.path).parent.as_posix()
    children = parent.metadata.get("subfeatures", [])
    if not isinstance(children, list) or feature.identifier not in children:
        raise WorkspaceError("sub-feature is not registered by its parent")
    if feature.metadata.get("module") != parent.metadata.get("module"):
        raise WorkspaceError("sub-feature providing module does not match its parent")
    expected_parent = Path(feature.path).parent.parent.parent.as_posix()
    if parent_root != expected_parent:
        raise WorkspaceError("sub-feature canonical path does not match its parent root")
    parent_context = {
        "feature_id": parent.identifier,
        "feature_directory": parent_root,
        "feature_spec": parent.path,
        "feature_implementation": f"{parent_root}/implementation.md",
    }
    siblings: list[dict[str, str]] = []
    for child_id in children:
        if child_id == feature.identifier:
            continue
        child_matches = package.by_id.get(child_id, ())
        if len(child_matches) == 1 and child_matches[0].kind == "feature":
            siblings.append(_summary(child_matches[0]))
    return "subfeature", parent_context, tuple(siblings)


def resolve_phase_paths(project_root: str | Path, feature_directory: str) -> WorkspacePaths:
    project = Path(project_root).resolve()
    try:
        relative = safe_relative_path(feature_directory.rstrip("/"))
        repository = ProjectRepository(project)
        package = repository.load()
        root = repository.resolve(relative)
        classified_kind, _ = classify_feature_root(relative, package.specification_root)
    except RepositoryError as error:
        raise WorkspaceError(str(error)) from error
    if root.is_symlink():
        raise WorkspaceError("feature root may not be a symlink")
    spec = root / "spec.md"
    realization = root / "implementation.md"
    legacy = root / "design.md"
    if not root.is_dir() or not spec.is_file() or spec.is_symlink():
        raise WorkspaceError(f"selected feature root has no canonical spec.md: {relative}")
    if legacy.exists() and realization.exists():
        raise WorkspaceError(
            f"selected feature root holds both design.md and implementation.md; remove the legacy design.md after merging it into implementation.md: {relative}"
        )
    if legacy.exists():
        raise WorkspaceError(
            f"selected feature root uses the legacy accepted-realization name design.md; rename it to implementation.md: {relative}"
        )
    if not realization.is_file() or realization.is_symlink():
        raise WorkspaceError(f"selected feature root has no canonical implementation.md: {relative}")
    feature = next(
        (item for item in package.documents("feature") if Path(item.path).parent.as_posix() == relative),
        None,
    )
    if feature is None:
        raise WorkspaceError(f"selected root is not a discovered canonical feature: {relative}")
    workspace_kind, parent_context, siblings = _workspace_relationships(package, feature)
    if workspace_kind != classified_kind:
        raise WorkspaceError("feature containment metadata does not match its canonical path")
    implementation = f"{relative}/implementation"
    module_summary, module_design = _module_paths(
        package, feature.metadata.get("module"), _module_directory(relative, workspace_kind)
    )
    return WorkspacePaths(
        workspace_kind=workspace_kind,
        feature_id=feature.identifier,
        providing_module=str(feature.metadata.get("module")) if feature.metadata.get("module") else None,
        parent_context=parent_context,
        siblings=siblings,
        feature_directory=relative,
        feature_spec=f"{relative}/spec.md",
        feature_implementation=f"{relative}/implementation.md",
        module_summary=module_summary,
        module_design=module_design,
        contracts_dir=f"{relative}/contracts",
        checklists_dir=f"{implementation}/checklists",
        diagrams_dir=f"{relative}/diagrams",
        implementation_dir=implementation,
        implementation_state=_implementation_state(root),
        plan=f"{implementation}/plan.md",
        research=f"{implementation}/research.md",
        data_model=f"{implementation}/data-model.md",
        quickstart=f"{implementation}/quickstart.md",
        tasks=f"{implementation}/tasks.md",
        validation=f"{implementation}/validation.md",
    )


def resolve_planned_phase_paths(project_root: str | Path, feature_directory: str) -> WorkspacePaths:
    """Resolve a safe not-yet-specified feature root for the specify phase only."""
    project = Path(project_root).resolve()
    try:
        relative = safe_relative_path(feature_directory.rstrip("/"))
        repository = ProjectRepository(project)
        config = repository.load_config()
        root = repository.resolve(relative)
        workspace_kind, parent_root = classify_feature_root(relative, config["specification_root"])
    except RepositoryError as error:
        raise WorkspaceError(str(error)) from error
    specification_root = config["specification_root"].rstrip("/")
    if relative == specification_root or not relative.startswith(specification_root + "/"):
        raise WorkspaceError("planned feature root must remain below the configured specification root")
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise WorkspaceError("planned feature root must be an absent path or a real directory")
    parent_context = None
    providing_module = None
    siblings: tuple[dict[str, str], ...] = ()
    if workspace_kind == "subfeature" and parent_root:
        package = repository.load()
        parent = next(
            (item for item in package.documents("feature") if Path(item.path).parent.as_posix() == parent_root),
            None,
        )
        if parent is None or parent.metadata.get("parent_feature"):
            raise WorkspaceError("planned sub-feature parent must be one canonical top-level feature")
        providing_module = str(parent.metadata.get("module"))
        parent_context = {
            "feature_id": parent.identifier,
            "feature_directory": parent_root,
            "feature_spec": parent.path,
            "feature_implementation": f"{parent_root}/implementation.md",
        }
        children = parent.metadata.get("subfeatures", [])
        if isinstance(children, list):
            siblings = tuple(
                _summary(matches[0])
                for child_id in children
                if len(matches := package.by_id.get(child_id, ())) == 1 and matches[0].kind == "feature"
            )
    return _planned_paths(
        relative,
        workspace_kind=workspace_kind,
        providing_module=providing_module,
        parent_context=parent_context,
        siblings=siblings,
    )


def _selection_path(project_root: Path) -> Path:
    return project_root / ".specify" / "feature.json"


def _read_persisted_selection(project_root: Path) -> str:
    path = _selection_path(project_root)
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkspaceError(f"cannot read .specify/feature.json: {error}") from error
    if not isinstance(value, dict) or not isinstance(value.get("feature_directory"), str):
        raise WorkspaceError(".specify/feature.json must contain feature_directory")
    return value["feature_directory"]


def resolve_selected_workspace(
    project_root: str | Path,
    explicit_feature_directory: str | None = None,
    allow_missing_spec: bool = False,
) -> WorkspacePaths:
    project = Path(project_root).resolve()
    selected = explicit_feature_directory or os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if not selected:
        selected = _read_persisted_selection(project)
    try:
        return resolve_phase_paths(project, selected)
    except WorkspaceError:
        if not allow_missing_spec:
            raise
        return resolve_planned_phase_paths(project, selected)


def persist_selection(project_root: str | Path, feature_directory: str) -> str:
    project = Path(project_root).resolve()
    paths = resolve_phase_paths(project, feature_directory)
    target = _selection_path(project)
    encoded = json.dumps({"feature_directory": paths.feature_directory}, sort_keys=True, separators=(",", ":")) + "\n"
    if target.is_file() and target.read_text(encoding="utf-8") == encoded:
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(".feature.json.concorde-stage")
    try:
        temporary.write_text(encoded, encoding="utf-8", newline="\n")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return "selected"


def phase_target(paths: WorkspacePaths, phase: str) -> str:
    if phase in ROOT_PHASES:
        return paths.feature_directory
    if phase in IMPLEMENTATION_PHASES:
        return paths.implementation_dir
    raise WorkspaceError(f"unsupported Spec Kit phase: {phase}")


def _planned_paths(
    relative: str,
    *,
    workspace_kind: str = "feature",
    feature_id: str | None = None,
    providing_module: str | None = None,
    parent_context: dict[str, str] | None = None,
    siblings: tuple[dict[str, str], ...] = (),
) -> WorkspacePaths:
    implementation = f"{relative}/implementation"
    module_directory = _module_directory(relative, workspace_kind)
    return WorkspacePaths(
        workspace_kind=workspace_kind,
        feature_id=feature_id,
        providing_module=providing_module,
        parent_context=parent_context,
        siblings=siblings,
        feature_directory=relative,
        feature_spec=f"{relative}/spec.md",
        feature_implementation=f"{relative}/implementation.md",
        module_summary=f"{module_directory}/module.md",
        module_design=f"{module_directory}/design.md",
        contracts_dir=f"{relative}/contracts",
        checklists_dir=f"{implementation}/checklists",
        diagrams_dir=f"{relative}/diagrams",
        implementation_dir=implementation,
        implementation_state="absent",
        plan=f"{implementation}/plan.md",
        research=f"{implementation}/research.md",
        data_model=f"{implementation}/data-model.md",
        quickstart=f"{implementation}/quickstart.md",
        tasks=f"{implementation}/tasks.md",
        validation=f"{implementation}/validation.md",
    )


def _resolve_feature(package: Any, target: str) -> SourceDocument | None:
    matches = package.by_id.get(target, ())
    if len(matches) == 1 and matches[0].kind == "feature":
        return matches[0]
    try:
        relative = safe_relative_path(target.rstrip("/"))
    except RepositoryError:
        return None
    return next(
        (
            item
            for item in package.documents("feature")
            if Path(item.path).parent.as_posix() == relative
        ),
        None,
    )
