"""Safe direct-feature workspace resolution for Workspace Protocol 13."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from ..model import SourceDocument
from ..projection import feature_summary
from ..reflections.reflections import parse_auxiliary_reflections, reflections_path
from .repository import (
    FEATURE_ID,
    ProjectRepository,
    RepositoryError,
    attempt_directory_for_feature_id,
    classify_feature_path,
    safe_relative_path,
)
from .validation.entities import module_ancestry


class WorkspaceError(ValueError):
    """A selected feature path is unsafe, stale, or structurally invalid."""


@dataclass(frozen=True)
class WorkspacePaths:
    feature_id: str | None
    providing_module: str | None
    feature_path: str
    module_architecture: str
    module_ancestry: tuple[dict[str, Any], ...]
    related_features: tuple[dict[str, Any], ...]
    executable_context: Mapping[str, tuple[str, ...]]
    checklists_dir: str | None
    attempt_dir: str | None
    attempt_state: str
    plan: str | None
    research: str | None
    data_model: str | None
    quickstart: str | None
    tasks: str | None
    validation: str | None
    reflections: str = ""
    reflections_open: int = 0

    def protocol_paths(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ROOT_PHASES = frozenset({"specify", "clarify", "checklist", "fast-loop"})
ATTEMPT_PHASES = frozenset({"plan", "tasks", "implement", "analyze", "converge", "taskstoissues", "validation"})
_TASK = re.compile(r"^\s*-\s+\[([ xX])\]\s+T\d{3,}\b")
_CHECK = re.compile(r"^\s*-\s+\[([ xX])\]")
_TASK_PATH = re.compile(r"`([^`]+)`")
_TASK_PATH_PREFIXES = (
    ".agents/",
    ".claude/",
    ".codex/",
    ".concorde/",
    "agent-assets/",
    "docsite/",
    "generated/",
    "operations/",
    "scripts/",
    "skills/",
    "specs/",
    "src/",
    "templates/",
    "tests/",
)
_TASK_ROOT_FILES = frozenset(
    {"README.md", "concorde.json", "pyproject.toml", "package.json", "uv.lock"}
)


def _attempt_state(attempt: Path) -> str:
    if not attempt.exists():
        return "absent"
    if not attempt.is_dir() or attempt.is_symlink():
        raise WorkspaceError("attempt must be one real project-control directory")
    tasks = attempt / "tasks.md"
    if not tasks.is_file() or tasks.is_symlink():
        return "active"
    matches = [_TASK.match(line) for line in tasks.read_text(encoding="utf-8").splitlines()]
    task_states = [match.group(1).lower() for match in matches if match]
    if not task_states or any(state != "x" for state in task_states):
        return "active"
    checklists = attempt / "checklists"
    if checklists.exists():
        if not checklists.is_dir() or checklists.is_symlink():
            raise WorkspaceError("attempt/checklists must be a real directory")
        for checklist in sorted(checklists.glob("*.md")):
            if checklist.is_symlink():
                raise WorkspaceError("attempt checklist files may not be symlinks")
            states = [
                match.group(1).lower()
                for line in checklist.read_text(encoding="utf-8").splitlines()
                if (match := _CHECK.match(line))
            ]
            if any(state != "x" for state in states):
                return "active"
    validation = attempt / "validation.md"
    if (
        not validation.is_file()
        or validation.is_symlink()
        or not re.search(
            r"\*\*Outcome\*\*:\s*passed\b",
            validation.read_text(encoding="utf-8"),
            re.IGNORECASE,
        )
    ):
        return "active"
    return "complete"


def reflections_open_count(package: Any, feature_id: str) -> int:
    return parse_auxiliary_reflections(package.auxiliary).open_count(feature_id)


def _summary(package: Any, feature: SourceDocument) -> dict[str, Any]:
    return {
        **feature_summary(package, feature),
        "reflections_open": reflections_open_count(package, feature.identifier),
    }


def _module_ancestry_summary(package: Any, identifier: str) -> dict[str, Any]:
    module = package.modules[identifier]
    return {
        "module_id": identifier,
        "architecture": module.path,
        "responsibility": " ".join(module.responsibility.split()),
        "boundary": " ".join(module.boundary.split()),
    }


def _related_summaries(package: Any, feature: SourceDocument) -> tuple[dict[str, Any], ...]:
    result = []
    for identifier in package.features[feature.identifier].related_features:
        matches = package.by_id.get(identifier, ())
        if len(matches) != 1 or matches[0].kind != "feature":
            raise WorkspaceError(f"related feature '{identifier}' does not resolve exactly once")
        result.append(_summary(package, matches[0]))
    return tuple(result)


def _executable_context(project: Path) -> dict[str, tuple[str, ...]]:
    source_candidates = ("src", "app", "lib", "packages", "extensions", "scripts")
    test_candidates = ("tests", "test", "spec", "docsite/tests")
    sources = tuple(
        name
        for name in source_candidates
        if (project / name).is_dir() and not (project / name).is_symlink()
    )
    tests = tuple(
        name
        for name in test_candidates
        if (project / name).is_dir() and not (project / name).is_symlink()
    )
    return {"source_roots": sources, "test_roots": tests}


def _attempt_paths(feature_id: str | None) -> dict[str, str | None]:
    if feature_id is None:
        return {
            "attempt": None,
            "checklists": None,
            "plan": None,
            "research": None,
            "data_model": None,
            "quickstart": None,
            "tasks": None,
            "validation": None,
        }
    attempt = attempt_directory_for_feature_id(feature_id)
    return {
        "attempt": attempt,
        "checklists": f"{attempt}/checklists",
        "plan": f"{attempt}/plan.md",
        "research": f"{attempt}/research.md",
        "data_model": f"{attempt}/data-model.md",
        "quickstart": f"{attempt}/quickstart.md",
        "tasks": f"{attempt}/tasks.md",
        "validation": f"{attempt}/validation.md",
    }


def _paths_for(package: Any, project: Path, feature: SourceDocument) -> WorkspacePaths:
    if not FEATURE_ID.fullmatch(feature.identifier):
        raise WorkspaceError(
            f"feature identity '{feature.identifier}' is not safe for project-control attempt storage"
        )
    module_id = feature.metadata.get("module")
    if not isinstance(module_id, str) or module_id not in package.modules:
        raise WorkspaceError(f"providing module '{module_id}' does not resolve exactly once")
    _, physical_module = classify_feature_path(feature.path, package.specification_root)
    expected_module = PurePosixPath(package.modules[module_id].path).parent.as_posix()
    if physical_module != expected_module:
        raise WorkspaceError("feature physical placement does not match its providing module")
    temporal = _attempt_paths(feature.identifier)
    ancestry = tuple(
        _module_ancestry_summary(package, identifier)
        for identifier in module_ancestry(package, module_id)
    )
    return WorkspacePaths(
        feature_id=feature.identifier,
        providing_module=module_id,
        feature_path=feature.path,
        module_architecture=package.modules[module_id].path,
        module_ancestry=ancestry,
        related_features=_related_summaries(package, feature),
        executable_context=_executable_context(project),
        checklists_dir=temporal["checklists"],
        attempt_dir=temporal["attempt"],
        attempt_state=_attempt_state(project / temporal["attempt"]),  # type: ignore[arg-type]
        plan=temporal["plan"],
        research=temporal["research"],
        data_model=temporal["data_model"],
        quickstart=temporal["quickstart"],
        tasks=temporal["tasks"],
        validation=temporal["validation"],
        reflections=reflections_path(),
        reflections_open=reflections_open_count(package, feature.identifier),
    )


def _resolve_feature(package: Any, target: str) -> SourceDocument | None:
    matches = package.by_id.get(target, ())
    if len(matches) == 1 and matches[0].kind == "feature":
        return matches[0]
    if target.endswith("/"):
        return None
    try:
        relative = safe_relative_path(target)
    except RepositoryError:
        return None
    return next((item for item in package.documents("feature") if item.path == relative), None)


def resolve_phase_paths(project_root: str | Path, feature_path: str) -> WorkspacePaths:
    project = Path(project_root).resolve()
    try:
        repository = ProjectRepository(project)
        package = repository.load()
        feature = _resolve_feature(package, feature_path)
        if feature is None:
            raise WorkspaceError(f"feature target '{feature_path}' does not resolve exactly once")
        classify_feature_path(feature.path, package.specification_root)
        resolved = repository.resolve(feature.path)
    except RepositoryError as error:
        raise WorkspaceError(str(error)) from error
    if resolved.is_symlink() or not resolved.is_file():
        raise WorkspaceError("selected feature path must be one real canonical Markdown file")
    return _paths_for(package, project, feature)


def _planned_paths(
    package: Any,
    project: Path,
    relative: str,
    module_directory: str,
    planned_feature_id: str | None,
) -> WorkspacePaths:
    module_source = next(
        (
            source
            for source in package.documents("module")
            if PurePosixPath(source.path).parent.as_posix() == module_directory
        ),
        None,
    )
    if module_source is None:
        raise WorkspaceError("planned feature provider is not a discovered module")
    temporal = _attempt_paths(planned_feature_id)
    ancestry = tuple(
        _module_ancestry_summary(package, identifier)
        for identifier in module_ancestry(package, module_source.identifier)
    )
    return WorkspacePaths(
        feature_id=planned_feature_id,
        providing_module=module_source.identifier,
        feature_path=relative,
        module_architecture=module_source.path,
        module_ancestry=ancestry,
        related_features=(),
        executable_context=_executable_context(project),
        checklists_dir=temporal["checklists"],
        attempt_dir=temporal["attempt"],
        attempt_state="absent" if planned_feature_id is not None else "unresolved",
        plan=temporal["plan"],
        research=temporal["research"],
        data_model=temporal["data_model"],
        quickstart=temporal["quickstart"],
        tasks=temporal["tasks"],
        validation=temporal["validation"],
        reflections=reflections_path(),
        reflections_open=0,
    )


def resolve_planned_phase_paths(
    project_root: str | Path,
    feature_path: str,
    planned_feature_id: str | None = None,
) -> WorkspacePaths:
    project = Path(project_root).resolve()
    try:
        if feature_path.endswith("/"):
            raise RepositoryError("planned feature must be a direct .md path")
        relative = safe_relative_path(feature_path)
        repository = ProjectRepository(project)
        package = repository.load()
        _, module_directory = classify_feature_path(relative, package.specification_root)
        candidate = repository.resolve(relative)
        if planned_feature_id is not None:
            if not FEATURE_ID.fullmatch(planned_feature_id):
                raise RepositoryError(
                    "planned feature ID must be one lowercase qualified feature.* stable ID"
                )
            if package.by_id.get(planned_feature_id):
                raise RepositoryError(
                    f"planned feature ID '{planned_feature_id}' already exists"
                )
            attempt = repository.resolve(attempt_directory_for_feature_id(planned_feature_id))
        else:
            attempt = None
    except RepositoryError as error:
        raise WorkspaceError(str(error)) from error
    if candidate.exists() or candidate.is_symlink():
        raise WorkspaceError("planned feature path must be absent")
    if attempt is not None and (attempt.exists() or attempt.is_symlink()):
        raise WorkspaceError("planned feature cannot adopt an existing or orphan attempt")
    return _planned_paths(package, project, relative, module_directory, planned_feature_id)


def _selection_path(project_root: Path) -> Path:
    return project_root / ".concorde" / "feature.json"


def _read_persisted_selection(project_root: Path) -> str:
    path = _selection_path(project_root)
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkspaceError(f"cannot read .concorde/feature.json: {error}") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"feature_path"}
        or not isinstance(value.get("feature_path"), str)
    ):
        raise WorkspaceError(".concorde/feature.json must contain only feature_path")
    return value["feature_path"]


def resolve_selected_workspace(
    project_root: str | Path,
    explicit_feature_path: str | None = None,
    allow_missing_feature: bool = False,
    planned_feature_id: str | None = None,
) -> WorkspacePaths:
    project = Path(project_root).resolve()
    selected = (
        explicit_feature_path
        or os.environ.get("CONCORDE_FEATURE_PATH")
        or _read_persisted_selection(project)
    )
    try:
        paths = resolve_phase_paths(project, selected)
        if planned_feature_id is not None and paths.feature_id != planned_feature_id:
            raise WorkspaceError(
                f"explicit feature ID '{planned_feature_id}' does not match selected feature '{paths.feature_id}'"
            )
        return paths
    except WorkspaceError:
        if not allow_missing_feature:
            raise
        return resolve_planned_phase_paths(project, selected, planned_feature_id)


def persist_selection(
    project_root: str | Path,
    feature_path: str,
    allow_missing_feature: bool = False,
    planned_feature_id: str | None = None,
) -> str:
    project = Path(project_root).resolve()
    try:
        paths = resolve_phase_paths(project, feature_path)
        if planned_feature_id is not None and paths.feature_id != planned_feature_id:
            raise WorkspaceError(
                f"explicit feature ID '{planned_feature_id}' does not match selected feature '{paths.feature_id}'"
            )
    except WorkspaceError:
        if not allow_missing_feature:
            raise
        paths = resolve_planned_phase_paths(project, feature_path, planned_feature_id)
    target = _selection_path(project)
    encoded = json.dumps(
        {"feature_path": paths.feature_path}, sort_keys=True, separators=(",", ":")
    ) + "\n"
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
        return paths.feature_path
    if phase in ATTEMPT_PHASES:
        if paths.attempt_dir is None:
            raise WorkspaceError(
                "attempt phases require a resolved stable feature ID; rerun specify after choosing the feature ID"
            )
        return paths.attempt_dir
    raise WorkspaceError(f"unsupported Concorde phase: {phase}")


def checked_project_path(
    project_root: str | Path,
    relative: str,
    *,
    allow_missing: bool = False,
) -> str:
    """Validate one concrete project-relative path without following a symlink boundary."""

    project_input = Path(project_root)
    if project_input.is_symlink():
        raise WorkspaceError(f"project root may not be a symlink: {project_input}")
    project = project_input.resolve()
    try:
        normalized = safe_relative_path(relative.rstrip("/"))
    except RepositoryError as error:
        raise WorkspaceError(str(error)) from error
    candidate = project / normalized
    current = candidate
    while current != project:
        if current.is_symlink():
            raise WorkspaceError(f"project path may not contain a symlink: {normalized}")
        current = current.parent
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(project)
    except ValueError as error:
        raise WorkspaceError(f"project path escapes root: {normalized}") from error
    if candidate.exists():
        if not (candidate.is_file() or candidate.is_dir()):
            raise WorkspaceError(f"project path is not a regular file or directory: {normalized}")
    elif not allow_missing:
        raise WorkspaceError(f"project path does not exist: {normalized}")
    else:
        ancestor = candidate.parent
        while ancestor != project and not ancestor.exists():
            if ancestor.is_symlink():
                raise WorkspaceError(f"project path may not contain a symlink: {normalized}")
            ancestor = ancestor.parent
        if ancestor.is_symlink() or not ancestor.is_dir():
            raise WorkspaceError(f"creation parent is missing or unsafe: {normalized}")
    return normalized


def locator_project_path(
    project_root: str | Path,
    locator: str,
    *,
    allow_missing: bool = False,
) -> str | None:
    """Resolve one filesystem locator, ignoring explicitly external/conceptual identities."""

    if not isinstance(locator, str) or not locator.strip():
        raise WorkspaceError("architecture locator must be a non-empty string")
    value = locator.strip()
    if value.startswith(("external:", "concept:", "http://", "https://")):
        return None
    relative = value.split("#", 1)[0]
    return checked_project_path(project_root, relative, allow_missing=allow_missing)


def task_declared_paths(
    project_root: str | Path,
    tasks_path: str | None,
) -> tuple[str, ...]:
    """Return exact path-shaped Markdown tokens declared by the selected task list."""

    if tasks_path is None:
        return ()
    project = Path(project_root).resolve()
    normalized_tasks = checked_project_path(project, tasks_path, allow_missing=True)
    path = project / normalized_tasks
    if not path.exists():
        return ()
    if not path.is_file() or path.is_symlink():
        raise WorkspaceError(f"task source is missing or unsafe: {normalized_tasks}")
    result: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if _TASK.match(line) is None:
            continue
        for raw in _TASK_PATH.findall(line):
            token = raw.strip()
            if token.endswith("/"):
                token = token.rstrip("/")
            if not (token in _TASK_ROOT_FILES or token.startswith(_TASK_PATH_PREFIXES)):
                continue
            resolved = checked_project_path(project, token, allow_missing=True)
            if resolved not in result:
                result.append(resolved)
    return tuple(result)


def workspace_role_paths(
    project_root: str | Path,
    paths: WorkspacePaths,
) -> dict[str, tuple[str, ...]]:
    """Resolve Protocol 13 durable/control/task roles to concrete safe project paths."""

    project = Path(project_root).resolve()

    def existing(relative: str | None, *, creation: bool = False) -> tuple[str, ...]:
        if relative is None:
            return ()
        return (checked_project_path(project, relative, allow_missing=creation),)

    ancestry = tuple(
        checked_project_path(project, item["architecture"])
        for item in paths.module_ancestry
        if isinstance(item.get("architecture"), str)
    )
    tasks = task_declared_paths(project, paths.tasks)
    constitution = existing(".concorde/constitution.md") if (project / ".concorde/constitution.md").is_file() else ()
    framework = existing(".concorde/framework") if (project / ".concorde/framework").is_dir() else ()
    templates = existing("templates") if (project / "templates").is_dir() else ()
    generated = existing("generated") if (project / "generated").is_dir() else ()
    reflections_root = project / ".concorde/reflections"
    return {
        "selected-feature": existing(paths.feature_path),
        "module-architecture": existing(paths.module_architecture),
        "module-ancestry": ancestry,
        "related-summaries": (),
        "required-feature-specs": (),
        "owned-implementation": (),
        "task-authorized": tasks,
        "attempt": existing(paths.attempt_dir, creation=True),
        "checklists": existing(paths.checklists_dir, creation=True),
        "constitution": constitution,
        "reflections": existing(paths.reflections, creation=True),
        "framework": framework,
        "templates": templates,
        "reflection-queue": existing(paths.reflections, creation=True),
        "reflection-plans": existing(".concorde/reflections/plans", creation=True)
        if reflections_root.is_dir()
        else (),
        "reflection-worktrees": existing(".concorde/reflections/worktrees", creation=True)
        if reflections_root.is_dir()
        else (),
        "generated-projections": generated,
    }
