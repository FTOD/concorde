"""Review's promise-level impact: which Modules need a fresh Spec review after a change.

A Module is concerned when it selects a changed document without narrowing, or references a node
whose definition changed. A Module whose only selection is a ``relies_on`` narrowing of unchanged
nodes is not. Built on Spec tooling's changed-definition indexes; the policy itself is Review's.
"""

from __future__ import annotations

from ..spec.impact import changed_documents, changed_nodes


def unnarrowed_selectors(repository, path: str) -> tuple[str, ...]:
    """Modules that select a document whole: its owner, a ``contains`` or ``uses`` of its owner
    without ``relies_on``, an ``includes`` of its owner, or an ``includes`` of the document."""
    unit = repository.units.get(path)
    if unit is None:
        return ()
    owner, document = unit.owner, unit.document_id
    result = {owner}
    for module_id in repository.selected_by(document):
        declaration = repository.declarations[module_id]
        if any(
            item["target"] == owner and "relies_on" not in item
            for kind in ("contains", "uses")
            for item in declaration.relations(kind)
        ) or any(
            (item["kind"] == "module" and item["target"] == owner)
            or (item["kind"] == "document" and item["target"] == document)
            for item in declaration.includes
        ):
            result.add(module_id)
    return tuple(sorted(result))


def review_impact(old, new, paths) -> tuple[str, ...]:
    """Modules that need a fresh Spec review after the given documents changed.

    ``old`` is the baseline revision and ``new`` the candidate. A Module is concerned, in either
    revision, when it selects a changed document without narrowing or references a changed node
    (``referenced-by``: ``relies_on``, ``imports``, ``narrows``, ``supersedes``, ``relates``,
    ``participates``). Unchanged documents concern nobody.
    """
    documents = changed_documents(old, new, paths)
    concerned: set[str] = set()
    for repository in (old, new):
        for path in documents:
            concerned.update(unnarrowed_selectors(repository, path))
    for identity in changed_nodes(old, new, documents):
        for repository in (old, new):
            if identity in repository.nodes or identity in repository.modules:
                concerned.update(
                    item["module"] for item in repository.referenced_by(identity)
                )
    return tuple(sorted(concerned & set(new.modules)))
