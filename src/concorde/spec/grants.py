"""Task-type grants of Spec Protocol 14 (``protocol/boundaries.md``, task types).

Code-phase task types read the whole project's implementation (``ProjectImplementation``): a
worker runs the code it changes together with the code it uses, and a package is only importable
whole. Only the bound Modules' own scopes are ever writable.

A grant lists the paths a task of one task type, bound to one or more Modules, may know by name
(``names``), read (``ro``) or change (``rw``); every other path is denied and omitted. It is
computed from one worktree's declarations alone and carries the context identity of the bound
Modules, so a harness can freeze it when a worker starts and tell later whether anything inside it
changed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .model import ToolResult
from .repository_base import SpecError, digest, installed_files, is_directory_entry

TASK_TYPES = (
    "understand",
    "specify",
    "implement",
    "test",
    "review-spec",
    "review-code",
    "code-to-spec",
)

# The Protocol's task-type table (protocol/model.yaml ``task_types``) in grant levels: ``read``
# is written ``ro`` and ``write`` ``rw``; ``None`` means the set contributes nothing.
LEVELS: dict[str, dict[str, str | None]] = {
    "understand": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": None,
        "SpecScope": None,
        "ExternalContext": "ro",
        "ProjectImplementation": None,
    },
    "specify": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": None,
        "SpecScope": "rw",
        "ExternalContext": "ro",
        "ProjectImplementation": None,
    },
    "implement": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": "rw",
        "SpecScope": None,
        "ExternalContext": "ro",
        "ProjectImplementation": "ro",
    },
    "test": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": "ro",
        "SpecScope": None,
        "ExternalContext": "ro",
        "ProjectImplementation": "ro",
    },
    "review-spec": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": None,
        "SpecScope": None,
        "ExternalContext": "ro",
        "ProjectImplementation": None,
    },
    "review-code": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": "ro",
        "SpecScope": None,
        "ExternalContext": "ro",
        "ProjectImplementation": "ro",
    },
    "code-to-spec": {
        "SpecContext": "ro",
        "ImplementationContext": "names",
        "ImplementationScope": "ro",
        "SpecScope": "rw",
        "ExternalContext": "ro",
        "ProjectImplementation": "ro",
    },
}
RANK = {"names": 1, "ro": 2, "rw": 3}


@dataclass(frozen=True)
class Grant:
    """One computed grant; ``value`` is its record."""

    value: dict

    @property
    def entries(self) -> tuple[dict, ...]:
        return tuple(self.value["entries"])

    def level(self, path: str) -> str | None:
        """The level of one concrete path: its own entry or the directory entry covering it."""
        best = None
        for entry in self.value["entries"]:
            listed = entry["path"]
            if listed == path or (
                is_directory_entry(listed) and path.startswith(listed)
            ):
                if best is None or RANK[entry["level"]] > RANK[best]:
                    best = entry["level"]
        return best


def _modules(repository, modules: Sequence[str]) -> list[str]:
    if (
        isinstance(modules, str)
        or not modules
        or any(not isinstance(item, str) for item in modules)
        or len(set(modules)) != len(modules)
    ):
        raise SpecError(
            f"a grant needs a nonempty list of distinct Module identities, not {modules!r}",
            "invalid_input",
            "modules",
        )
    unknown = sorted(item for item in modules if item not in repository.modules)
    if unknown:
        raise SpecError(
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not registered in "
            f"{repository.root}; registered: {', '.join(sorted(repository.modules))}",
            "unknown_module",
            "modules",
            path=repository.registry_path,
        )
    return sorted(modules)


def context_identity(repository, modules: Sequence[str]) -> str:
    """Digest of the bound Modules' selected sources and external material (see contracts)."""
    items = []
    for module in _modules(repository, modules):
        items.append(
            {
                "module": module,
                "sources": repository.spec_context(module).value["sources"],
                "external": sorted(
                    (
                        {"path": entry.path, "digest": entry.digest}
                        for entry in repository.external_context(module)
                    ),
                    key=lambda item: item["path"],
                ),
            }
        )
    return digest({"modules": items})


def _paths_of(repository, module: str) -> dict[str, tuple[str, ...]]:
    """Each boundary set of one Module as the grant paths it contributes."""
    sets = repository.boundary_sets(module)
    return {
        "SpecContext": sets.spec_context,
        "ImplementationContext": sets.implementation_context,
        "ImplementationScope": sets.implementation_scope,
        "SpecScope": sets.spec_scope,
        "ExternalContext": tuple(entry.path for entry in sets.external_context),
        "ProjectImplementation": sets.project_implementation,
    }


def grant(repository, modules: Sequence[str], task_type: str) -> Grant:
    """The grant of ``task_type`` for ``modules``, computed from ``repository`` alone."""
    if task_type not in LEVELS:
        raise SpecError(
            f"unknown task type: {task_type!r}; expected one of {', '.join(TASK_TYPES)}",
            "invalid_task_type",
            "task_type",
        )
    bound = _modules(repository, modules)
    levels: dict[str, str] = {}
    for module in bound:
        for name, paths in _paths_of(repository, module).items():
            level = LEVELS[task_type][name]
            if level is None:
                continue
            for path in paths:
                if path not in levels or RANK[level] > RANK[levels[path]]:
                    levels[path] = level
    if LEVELS[task_type]["ImplementationScope"] == "rw":
        shared = []
        for module in bound:
            for other, files in sorted(repository.shared_files(module).items()):
                if other not in bound:
                    shared.extend(f"{path} (also bound by {other})" for path in files)
        if shared:
            raise SpecError(
                f"the {task_type} grant for {', '.join(bound)} would make files writable "
                "that Modules outside the grant also bind: "
                + "; ".join(sorted(set(shared))),
                "shared_file",
                "modules",
            )
    # An installed file is the installer's: bound only by its exact path (CHK.binds.installed),
    # it is at most readable, whatever the Module binding it is granted.
    installed = installed_files(repository.root)
    for path, level in list(levels.items()):
        if level == "rw" and path in installed:
            levels[path] = "ro"
    directories = [
        (path, level) for path, level in levels.items() if is_directory_entry(path)
    ]
    entries = [
        {"path": path, "level": level}
        for path, level in sorted(levels.items())
        if not any(
            other != path and path.startswith(other) and RANK[cover] >= RANK[level]
            for other, cover in directories
        )
    ]
    return Grant(
        {
            "task_type": task_type,
            "modules": bound,
            "context_identity": context_identity(repository, bound),
            "entries": entries,
        }
    )


def grant_command(root, modules: str, task_type: str) -> ToolResult:
    """``concorde grant``: load the worktree at ``root`` and print its grant."""
    from .repository import SpecRepository

    try:
        repository = SpecRepository(root)
        value = grant(
            repository,
            [item.strip() for item in modules.split(",") if item.strip()],
            task_type,
        ).value
    except SpecError as error:
        return ToolResult("grant", ".", "invalid", error=error)
    return ToolResult("grant", ".", "success", result=value)


__all__ = [
    "Grant",
    "LEVELS",
    "TASK_TYPES",
    "context_identity",
    "grant",
    "grant_command",
]
