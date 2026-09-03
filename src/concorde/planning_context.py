"""Trusted least-privilege context resolution for the planning Operation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping

from .feature_workspace import (
    WorkspaceError,
    checked_project_path,
    locator_project_path,
    resolve_selected_workspace,
    workspace_role_paths,
)
from .model import ArchitecturePackage
from .repository import ProjectRepository, RepositoryError


class PlanningContextError(ValueError):
    """A planning context cannot be resolved without widening a module boundary."""


@dataclass(frozen=True)
class RequiredFeatureSpec:
    feature_id: str
    feature_path: str
    interface_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkspacePermissionContext:
    project_root: str
    feature_id: str
    feature_path: str
    module_architecture: str
    ancestry_paths: tuple[str, ...]
    required_feature_specs: tuple[RequiredFeatureSpec, ...]
    owned_implementation_paths: tuple[str, ...]
    task_authorized_paths: tuple[str, ...]
    attempt_paths: tuple[str, ...]
    reflection_path: str
    constitution_path: str | None
    role_paths: Mapping[str, tuple[str, ...]]
    denied_paths: tuple[str, ...]
    source_digest: str


def _under(path: str, parent: str) -> bool:
    candidate = PurePosixPath(path)
    root = PurePosixPath(parent)
    return candidate == root or root in candidate.parents


def _module_locator_paths(
    project: Path,
    package: ArchitecturePackage,
    module_id: str,
) -> tuple[str, ...]:
    module = package.modules[module_id]
    paths: list[str] = []
    for entity_id in module.entities:
        entity = package.entities.get(entity_id)
        if entity is None:
            raise PlanningContextError(
                f"providing module entity {entity_id!r} does not resolve exactly once"
            )
        try:
            path = locator_project_path(project, entity.locator)
        except WorkspaceError as error:
            raise PlanningContextError(str(error)) from error
        if path is not None and path not in paths:
            paths.append(path)
    return tuple(sorted(paths))


def _required_specs(
    package: ArchitecturePackage,
    feature_id: str,
) -> tuple[RequiredFeatureSpec, ...]:
    feature = package.features[feature_id]
    grouped: dict[str, list[str]] = {}
    paths: dict[str, str] = {}
    for interface_id in feature.required_interfaces:
        external_declarations = tuple(
            item
            for item in package.required_interface_declarations
            if item.owner == feature_id
            and item.identifier == interface_id
            and item.provider
            and item.provider.startswith("external:")
        )
        declarations = tuple(
            item
            for item in package.interfaces_by_id.get(interface_id, ())
            if item.role == "provided"
        )
        if not declarations and len(external_declarations) == 1:
            continue
        if len(declarations) != 1:
            raise PlanningContextError(
                f"required interface {interface_id!r} has {len(declarations)} provider owners"
            )
        provider = declarations[0]
        if provider.owner == feature_id:
            continue
        sources = package.by_id.get(provider.owner, ())
        if len(sources) != 1 or sources[0].kind != "feature":
            raise PlanningContextError(
                f"required interface owner {provider.owner!r} does not resolve to one feature"
            )
        grouped.setdefault(provider.owner, []).append(interface_id)
        paths[provider.owner] = sources[0].path
    return tuple(
        RequiredFeatureSpec(owner, paths[owner], tuple(interface_ids))
        for owner, interface_ids in grouped.items()
    )


def _descendant_modules(package: ArchitecturePackage, root: str) -> tuple[str, ...]:
    result: list[str] = []
    pending = [root]
    while pending:
        parent = pending.pop(0)
        children = sorted(
            module.identifier
            for module in package.modules.values()
            if module.parent == parent
        )
        result.extend(children)
        pending.extend(children)
    return tuple(result)


def _provider_private_paths(
    project: Path,
    package: ArchitecturePackage,
    specs: tuple[RequiredFeatureSpec, ...],
) -> tuple[str, ...]:
    included = {item.feature_path for item in specs}
    modules: set[str] = set()
    for item in specs:
        modules.add(package.features[item.feature_id].module)
    modules.update(
        descendant
        for module in tuple(modules)
        for descendant in _descendant_modules(package, module)
    )
    denied: list[str] = []
    for module_id in sorted(modules):
        architecture = checked_project_path(project, package.modules[module_id].path)
        if architecture not in denied:
            denied.append(architecture)
        for path in _module_locator_paths(project, package, module_id):
            if path not in included and path not in denied:
                denied.append(path)
        for feature in sorted(package.features.values(), key=lambda item: item.path):
            if feature.module == module_id and feature.path not in included:
                path = checked_project_path(project, feature.path)
                if path not in denied:
                    denied.append(path)
    return tuple(denied)


def _other_attempts(project: Path, selected: str | None) -> tuple[str, ...]:
    attempts = project / ".concorde/attempts"
    if not attempts.exists():
        return ()
    if attempts.is_symlink() or not attempts.is_dir():
        raise PlanningContextError(".concorde/attempts must be one real directory")
    result: list[str] = []
    for path in sorted(attempts.iterdir()):
        relative = path.relative_to(project).as_posix()
        if relative == selected:
            continue
        try:
            result.append(checked_project_path(project, relative))
        except WorkspaceError as error:
            raise PlanningContextError(str(error)) from error
    return tuple(result)


def _source_digest(
    project: Path,
    roles: Mapping[str, tuple[str, ...]],
    required: tuple[RequiredFeatureSpec, ...],
    denied: tuple[str, ...],
) -> str:
    files: dict[str, str] = {}
    for relative in sorted({path for values in roles.values() for path in values}):
        path = project / relative
        if path.is_file():
            files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_symlink():
                    raise PlanningContextError(
                        f"planning context directory contains a symlink: {relative}"
                    )
                if child.is_file():
                    child_relative = child.relative_to(project).as_posix()
                    files[child_relative] = hashlib.sha256(child.read_bytes()).hexdigest()
        else:
            files[relative] = "authorized-creation"
    payload = {
        "roles": {name: list(values) for name, values in sorted(roles.items())},
        "required": [
            {
                "feature_id": item.feature_id,
                "feature_path": item.feature_path,
                "interface_ids": list(item.interface_ids),
            }
            for item in required
        ],
        "denied": list(denied),
        "files": files,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def resolve_planning_context(
    project_root: str | Path,
    feature_path: str | None = None,
) -> WorkspacePermissionContext:
    """Resolve the selected feature's owned context and published dependency feature bodies."""

    project_input = Path(project_root)
    if project_input.is_symlink():
        raise PlanningContextError(f"project root may not be a symlink: {project_input}")
    project = project_input.resolve()
    try:
        workspace = resolve_selected_workspace(project, feature_path)
        package = ProjectRepository(project).load()
    except (WorkspaceError, RepositoryError) as error:
        raise PlanningContextError(str(error)) from error
    if workspace.feature_id is None or workspace.feature_id not in package.features:
        raise PlanningContextError("planning requires one existing stable selected feature")
    required = _required_specs(package, workspace.feature_id)
    owned = _module_locator_paths(project, package, workspace.providing_module or "")
    roles = workspace_role_paths(project, workspace)
    required_paths = tuple(item.feature_path for item in required)
    provider_private = _provider_private_paths(project, package, required)

    task_owned: list[str] = []
    for path in roles["task-authorized"]:
        if any(_under(path, private) or _under(private, path) for private in provider_private):
            raise PlanningContextError(
                f"task-authorized path is outside providing module: {path}"
            )
        if any(_under(path, locator) or _under(locator, path) for locator in owned):
            task_owned.append(path)

    roles["required-feature-specs"] = required_paths
    roles["owned-implementation"] = owned
    roles["task-authorized"] = tuple(sorted(dict.fromkeys(task_owned)))
    denied = tuple(
        sorted(
            dict.fromkeys(
                (*provider_private, *_other_attempts(project, workspace.attempt_dir))
            )
        )
    )
    readable = {path for values in roles.values() for path in values}
    overlap = readable & set(denied)
    if overlap:
        raise PlanningContextError(
            f"planning path appears in both allow and deny sets: {sorted(overlap)}"
        )
    frozen_roles = MappingProxyType(
        {name: tuple(values) for name, values in sorted(roles.items())}
    )
    constitution = roles["constitution"][0] if roles["constitution"] else None
    reflection = roles["reflections"][0]
    attempt_paths = tuple(
        dict.fromkeys((*roles["attempt"], *roles["checklists"]))
    )
    return WorkspacePermissionContext(
        project_root=project.as_posix(),
        feature_id=workspace.feature_id,
        feature_path=workspace.feature_path,
        module_architecture=workspace.module_architecture,
        ancestry_paths=roles["module-ancestry"],
        required_feature_specs=required,
        owned_implementation_paths=owned,
        task_authorized_paths=roles["task-authorized"],
        attempt_paths=attempt_paths,
        reflection_path=reflection,
        constitution_path=constitution,
        role_paths=frozen_roles,
        denied_paths=denied,
        source_digest=_source_digest(project, frozen_roles, required, denied),
    )
