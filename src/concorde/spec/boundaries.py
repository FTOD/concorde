"""Boundary sets and impact indexes of Spec Protocol 11 (``protocol/boundaries.md``).

Every set is computed from declarations alone: two tools reading the same checkout compute the
same sets. The three read sets are ``SpecContext``, ``ExternalContext`` and
``ImplementationContext``; the two write sets are ``SpecScope`` and ``ImplementationScope``. The
impact indexes answer the reverse question, whom a write concerns, and never widen a set.
"""

from __future__ import annotations

from dataclasses import dataclass

from .content_model import metadata_path
from .repository_base import bound_by, entry_base, expand_entry, is_directory_entry


@dataclass(frozen=True)
class ExternalEntry:
    """One ``includes`` of kind ``external``: the entry, its readable files and one tree digest."""

    path: str
    directory: bool
    files: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class BoundarySets:
    """The five boundary sets of one Module."""

    module: str
    spec_context: tuple[str, ...]
    external_context: tuple[ExternalEntry, ...]
    implementation_context: tuple[str, ...]
    spec_scope: tuple[str, ...]
    implementation_scope: tuple[str, ...]

    def writable(self, path: str) -> bool:
        """Whether a path lies in one of the two write sets."""
        return path in self.spec_scope or any(
            bound_by(entry, path) for entry in self.implementation_scope
        )


def spec_context(repository, module_id: str) -> tuple[str, ...]:
    """SpecContext(M): both members of every document M owns or selects, sorted."""
    return repository.spec_files(module_id)


def external_context(repository, module_id: str) -> tuple[ExternalEntry, ...]:
    """ExternalContext(M): only M's own external inclusions; a selected Module brings none."""
    target = repository.select(module_id)
    return tuple(
        ExternalEntry(
            entry,
            is_directory_entry(entry),
            repository.external_reference_files(entry),
            repository.external_reference_digest(entry),
        )
        for entry in repository.external_references(target)
    )


def implementation_context(repository, module_id: str) -> tuple[str, ...]:
    """ImplementationContext(M): names of existing bound files and of pending exact entries."""
    target = repository.select(module_id)
    names = set(repository.implementation_files(target))
    for realization in repository.realizations(target):
        names.update(
            entry for entry in realization.pending if not is_directory_entry(entry)
        )
    return tuple(sorted(names))


def spec_scope(repository, module_id: str) -> tuple[str, ...]:
    """SpecScope(M): both members of every document M owns, including the entry."""
    target = repository.select(module_id)
    return tuple(
        sorted(
            member
            for path in target.documents
            for member in (path, metadata_path(path))
        )
    )


def implementation_scope(repository, module_id: str) -> tuple[str, ...]:
    """ImplementationScope(M): M's realization entries, pending entries included.

    A directory entry covers every present and future file below it under the exclusion rule;
    use ``BoundarySets.writable`` or ``bound_by`` to test one path.
    """
    return tuple(repository.select(module_id).files)


def boundary_sets(repository, module_id: str) -> BoundarySets:
    return BoundarySets(
        module_id,
        spec_context(repository, module_id),
        external_context(repository, module_id),
        implementation_context(repository, module_id),
        spec_scope(repository, module_id),
        implementation_scope(repository, module_id),
    )


def selected_by(repository, document_id: str) -> tuple[str, ...]:
    """Modules whose SpecContext contains a document; they are concerned when it changes."""
    return repository.context_users(document_id)


def referenced_by(repository, identity: str) -> tuple[dict, ...]:
    """Declarations that depend on a concept, requirement, scenario or contract.

    Inverts ``relies_on``, ``imports``, ``narrows``, ``supersedes``, ``relates`` and
    ``participates``. Each record names the relation, the declaring Module and the declaring
    document.
    """
    result = []
    for module in repository.modules.values():
        for kind in ("contains", "uses"):
            for item in module.relations(kind):
                if identity in item.get("relies_on", ()):
                    result.append(
                        {
                            "relation": "relies_on",
                            "module": module.id,
                            "document": module.entry,
                        }
                    )
        for item in module.participates:
            if item["contract"] == identity:
                result.append(
                    {
                        "relation": "participates",
                        "module": module.id,
                        "document": module.entry,
                    }
                )
    for item in repository.imports:
        if item["concept"] == identity:
            result.append(
                {
                    "relation": "imports",
                    "module": item["owner"],
                    "document": item["document"],
                }
            )
    for relation in repository.metadata_relations:
        if (
            relation["type"] in {"narrows", "supersedes", "relates"}
            and relation.get("target") == identity
        ):
            result.append(
                {
                    "relation": relation["type"],
                    "module": relation["owner"],
                    "document": relation["document"],
                }
            )
    return tuple(
        sorted(
            {tuple(sorted(item.items())): item for item in result}.values(),
            key=lambda item: (item["module"], item["relation"], item["document"]),
        )
    )


def implemented_by(repository, path: str) -> tuple[str, ...]:
    """Modules whose realizations bind a path; a change to it concerns all of them."""
    return tuple(
        target.id
        for target in repository.targets.values()
        if any(bound_by(entry, path) or entry == path for entry in target.files)
    )


def covered_by(repository, scenario_id: str) -> tuple:
    """The verification declarations, read from bound tests, that name a scenario."""
    scenario = repository.scenario_nodes.get(scenario_id)
    if scenario is None:
        from .repository_base import SpecError

        raise SpecError(
            f"unknown scenario: {scenario_id}", "invalid_target", scenario_id
        )
    return repository.scenario_verifications(repository.targets[scenario.owner])[
        scenario_id
    ]


def impact(repository, *, documents=(), nodes=(), paths=()) -> tuple[str, ...]:
    """Every Module a write concerns: readers of written documents, dependants of written nodes
    and contracts, and binders of written files."""
    concerned: set[str] = set()
    for document_id in documents:
        concerned.update(selected_by(repository, document_id))
    for identity in nodes:
        concerned.update(item["module"] for item in referenced_by(repository, identity))
    for path in paths:
        concerned.update(implemented_by(repository, path))
    return tuple(sorted(concerned))


def entry_root(entry: str) -> str:
    return entry_base(entry)


__all__ = [
    "BoundarySets",
    "ExternalEntry",
    "boundary_sets",
    "covered_by",
    "expand_entry",
    "external_context",
    "impact",
    "implementation_context",
    "implementation_scope",
    "implemented_by",
    "referenced_by",
    "selected_by",
    "spec_context",
    "spec_scope",
]
