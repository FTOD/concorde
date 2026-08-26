"""Safe nested feature-workspace resolution and Spec Kit selection state."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .model import Finding, OperationResult, SourceDocument
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
    feature_design: str
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
    }


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
        "feature_design": f"{parent_root}/design.md",
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
    design = root / "design.md"
    if not root.is_dir() or not spec.is_file() or spec.is_symlink():
        raise WorkspaceError(f"selected feature root has no canonical spec.md: {relative}")
    if not design.is_file() or design.is_symlink():
        raise WorkspaceError(f"selected feature root has no canonical design.md: {relative}")
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
    return WorkspacePaths(
        workspace_kind=workspace_kind,
        feature_id=feature.identifier,
        providing_module=str(feature.metadata.get("module")) if feature.metadata.get("module") else None,
        parent_context=parent_context,
        siblings=siblings,
        feature_directory=relative,
        feature_spec=f"{relative}/spec.md",
        feature_design=f"{relative}/design.md",
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
            "feature_design": f"{parent_root}/design.md",
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
    return WorkspacePaths(
        workspace_kind=workspace_kind,
        feature_id=feature_id,
        providing_module=providing_module,
        parent_context=parent_context,
        siblings=siblings,
        feature_directory=relative,
        feature_spec=f"{relative}/spec.md",
        feature_design=f"{relative}/design.md",
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


def _workspace_finding(rule: str, source: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source, message, remediation)


def _nearest_common_parent(modules: dict[str, SourceDocument], participants: tuple[str, ...]) -> str | None:
    trails: list[list[str]] = []
    for participant in participants:
        trail: list[str] = []
        current = participant
        seen: set[str] = set()
        while current and current not in seen and current in modules:
            seen.add(current)
            trail.append(current)
            parent = modules[current].metadata.get("parent")
            current = parent if isinstance(parent, str) else ""
        if not trail:
            return None
        trails.append(trail)
    common = set(trails[0]).intersection(*(set(trail) for trail in trails[1:]))
    return next((identifier for identifier in trails[0] if identifier in common), None)


def propose_feature(
    project_root: str | Path,
    module_id: str | None,
    feature_id: str,
    short_name: str,
    number: str | None = None,
    participant_modules: tuple[str, ...] = (),
    parent_feature: str | None = None,
) -> OperationResult:
    project = Path(project_root).resolve()
    try:
        package = ProjectRepository(project).load()
    except RepositoryError as error:
        return OperationResult(
            "feature.create",
            parent_feature or module_id or ".",
            "invalid",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-001", ".concorde/config.json", str(error), "Correct the source hierarchy before placing a feature."),),
        )
    modules = {item.identifier: item for item in package.documents("module")}
    features = {item.identifier: item for item in package.documents("feature")}
    if bool(module_id) == bool(parent_feature):
        return OperationResult(
            "feature.create",
            parent_feature or module_id or ".",
            "invalid",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-012", ".concorde/config.json", "Feature creation requires exactly one placement mode: --module-id or --parent-feature.", "Choose module placement for a top-level feature or parent placement for an immediate sub-feature."),),
        )
    parent: SourceDocument | None = None
    workspace_kind = "feature"
    if parent_feature:
        parent = features.get(parent_feature)
        if parent is None:
            return OperationResult(
                "feature.create",
                parent_feature,
                "invalid",
                findings=(_workspace_finding("CONCORDE-WORKSPACE-013", ".concorde/config.json", f"Parent feature '{parent_feature}' does not resolve exactly once.", "Choose one canonical top-level feature from bounded context."),),
            )
        if parent.metadata.get("parent_feature"):
            return OperationResult(
                "feature.create",
                parent_feature,
                "invalid",
                findings=(_workspace_finding("CONCORDE-WORKSPACE-014", parent.path, "A sub-feature cannot parent another sub-feature.", "Keep feature containment to one immediate level."),),
            )
        workspace_kind = "subfeature"
        module_id = str(parent.metadata.get("module"))
        if participant_modules:
            return OperationResult(
                "feature.create",
                parent_feature,
                "invalid",
                findings=(_workspace_finding("CONCORDE-WORKSPACE-015", parent.path, "Sub-feature placement inherits its parent module and cannot choose participant modules.", "Review cross-module behavior at the parent feature level."),),
            )
    module = modules.get(module_id or "")
    if module is None:
        return OperationResult(
            "feature.create",
            module_id,
            "invalid",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-002", ".concorde/config.json", f"Providing module '{module_id}' does not resolve exactly once.", "Choose one module ID from bounded context."),),
        )
    if feature_id in package.by_id:
        return OperationResult(
            "feature.create",
            module_id,
            "conflict",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-003", module.path, f"Feature ID '{feature_id}' already exists.", "Choose a new stable feature ID or select the existing feature."),),
        )
    if not re.fullmatch(r"feature\.[a-z0-9-]+(?:\.[a-z0-9-]+)+", feature_id) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", short_name):
        return OperationResult(
            "feature.create",
            module_id,
            "invalid",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-004", module.path, "Feature ID or short name is not a safe stable identifier.", "Use a lowercase dotted feature ID and lowercase hyphenated short name."),),
        )
    if participant_modules and workspace_kind == "feature":
        nearest = _nearest_common_parent(modules, participant_modules)
        if nearest is None or nearest != module_id:
            return OperationResult(
                "feature.create",
                module_id,
                "invalid",
                findings=(_workspace_finding("CONCORDE-WORKSPACE-005", module.path, f"Providing module is not the nearest common parent; expected '{nearest}'.", "Place cross-module behavior on the nearest common parent shown by bounded context."),),
            )
    module_dir = Path(module.path).parent.as_posix()
    placement_dir = (
        project / Path(parent.path).parent / "subfeatures"
        if parent is not None
        else project / module_dir / "features"
    )
    if number is None:
        existing = [int(match.group(1)) for path in placement_dir.glob("[0-9]*-*") if (match := re.match(r"^(\d+)-", path.name))]
        number = f"{max(existing, default=0) + 1:03d}"
    if not re.fullmatch(r"\d{3,}", number):
        return OperationResult(
            "feature.create",
            module_id,
            "invalid",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-006", module.path, "Feature number is invalid.", "Use a zero-padded numeric feature number such as 002."),),
        )
    relative = (
        f"{Path(parent.path).parent.as_posix()}/subfeatures/{number}-{short_name}"
        if parent is not None
        else f"{module_dir}/features/{number}-{short_name}"
    )
    parent_context = None
    siblings: tuple[dict[str, str], ...] = ()
    if parent is not None:
        parent_root = Path(parent.path).parent.as_posix()
        parent_context = {
            "feature_id": parent.identifier,
            "feature_directory": parent_root,
            "feature_spec": parent.path,
            "feature_design": f"{parent_root}/design.md",
        }
        registered = parent.metadata.get("subfeatures", [])
        if isinstance(registered, list):
            siblings = tuple(
                _summary(matches[0])
                for child_id in registered
                if len(matches := package.by_id.get(child_id, ())) == 1 and matches[0].kind == "feature"
            )
    paths = _planned_paths(
        relative,
        workspace_kind=workspace_kind,
        feature_id=feature_id,
        providing_module=module_id,
        parent_context=parent_context,
        siblings=siblings,
    )
    if (project / relative).exists():
        return OperationResult(
            "feature.create",
            module_id,
            "conflict",
            findings=(_workspace_finding("CONCORDE-WORKSPACE-007", relative, "Proposed feature path already exists.", "Select the existing feature or choose another number/short name."),),
            result={"workspace": paths.protocol_paths(), "changes": [], "source_digest": package.source_digest},
        )
    registration = (
        {"path": parent.path, "action": "update", "meaning": f"Register {feature_id} with parent feature {parent.identifier}."}
        if parent is not None
        else {"path": module.path, "action": "update", "meaning": f"Register {feature_id} with {module_id}."}
    )
    changes = [
        registration,
        {"path": paths.feature_spec, "action": "create", "meaning": "Create the canonical specification through the normal specify phase."},
        {"path": paths.feature_design, "action": "create", "meaning": "Create the durable feature design with no hardened realization yet."},
    ]
    return OperationResult(
        "feature.create",
        module_id,
        "proposal",
        tuple(item["path"] for item in changes),
        result={
            "workspace": paths.protocol_paths(),
            "changes": changes,
            "source_digest": package.source_digest,
            "feature_id": feature_id,
            "providing_module": module_id,
            "parent_feature": parent.identifier if parent is not None else None,
            "workspace_kind": workspace_kind,
        },
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


def select_feature(project_root: str | Path, target: str, resume: bool = False) -> OperationResult:
    project = Path(project_root).resolve()
    try:
        package = ProjectRepository(project).load()
    except RepositoryError as error:
        return OperationResult("feature.select", target, "invalid", findings=(_workspace_finding("CONCORDE-WORKSPACE-001", ".concorde/config.json", str(error), "Correct the hierarchy before selecting a feature."),))
    feature = _resolve_feature(package, target)
    if feature is None:
        return OperationResult("feature.select", target, "invalid", findings=(_workspace_finding("CONCORDE-WORKSPACE-008", ".specify/feature.json", f"Feature target '{target}' does not resolve exactly once.", "Pass a stable feature ID or canonical project-relative feature root."),))
    root = Path(feature.path).parent.as_posix()
    canonical = feature.metadata.get("canonical_spec")
    module_id = feature.metadata.get("module")
    module = package.by_id.get(module_id, ())
    parent_id = feature.metadata.get("parent_feature")
    registration_valid = False
    if len(module) == 1:
        if isinstance(parent_id, str) and parent_id:
            parent_matches = package.by_id.get(parent_id, ())
            registration_valid = (
                len(parent_matches) == 1
                and parent_matches[0].kind == "feature"
                and feature.identifier in parent_matches[0].metadata.get("subfeatures", [])
                and feature.identifier not in module[0].metadata.get("features", [])
                and feature.metadata.get("module") == parent_matches[0].metadata.get("module")
            )
        else:
            registration_valid = feature.identifier in module[0].metadata.get("features", [])
    if canonical != feature.path or not registration_valid:
        return OperationResult("feature.select", target, "invalid", findings=(_workspace_finding("CONCORDE-WORKSPACE-009", feature.path, "Feature canonical path or module/parent registration is inconsistent.", "Align canonical_spec, containing lifecycle root, providing module, and parent registration."),))
    try:
        paths = resolve_phase_paths(project, root)
    except WorkspaceError as error:
        return OperationResult("feature.select", target, "invalid", findings=(_workspace_finding("CONCORDE-WORKSPACE-010", feature.path, str(error), "Restore a safe canonical feature root."),))
    if paths.implementation_state == "active" and any((project / paths.implementation_dir).iterdir()) and not resume:
        return OperationResult(
            "feature.select",
            target,
            "conflict",
            (feature.path,),
            (_workspace_finding("CONCORDE-WORKSPACE-011", paths.implementation_dir, "A non-empty implementation attempt requires explicit resume.", "Review the attempt and repeat selection with --resume, or archive it by project policy."),),
            {"workspace": paths.protocol_paths(), "changes": [], "source_digest": package.source_digest},
        )
    status = persist_selection(project, root)
    changes = [] if status == "unchanged" else [{"path": ".specify/feature.json", "action": "select", "meaning": f"Select {feature.identifier}."}]
    return OperationResult(
        "feature.select",
        target,
        status,
        (".specify/feature.json", feature.path),
        result={"workspace": paths.protocol_paths(), "changes": changes, "source_digest": package.source_digest},
    )
