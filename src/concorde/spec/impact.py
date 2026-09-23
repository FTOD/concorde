"""Change scope and promise-level review impact (Protocol ``boundaries.md``).

Both answers are derived from declarations alone, through the Protocol-named repository queries
(``selected_by``, ``referenced_by``, ``implemented_by``, ``shared_files``):

- ``change_scope`` is the set of Modules a change owned by one Module may span, because changing
  the owner can require them to change with it ("Atomic reconciliation"): what it contains or
  uses, the other participants of its contracts, the Modules whose declarations reference nodes
  it defines, and the Modules that bind its files.
- ``review_impact`` refines the ``selected-by`` impact of a Spec change to promise level: a Module
  is concerned when it selects a changed document without narrowing, or references a node whose
  definition changed. A Module whose only selection is a ``relies_on`` narrowing of unchanged
  nodes is not.
"""

from __future__ import annotations

from .typed_data import canonical


def owned_nodes(repository, module_id: str) -> tuple[str, ...]:
    """Identities of every node the Module defines, in identity order."""
    return tuple(
        sorted(node.id for node in repository.nodes.values() if node.owner == module_id)
    )


def binding_modules(repository, module_id: str) -> tuple[str, ...]:
    """The Module and every Module that binds a file in its ImplementationScope.

    Computed from entries alone (``shared_files``), so pending entries count as well.
    """
    return tuple(sorted({module_id, *repository.shared_files(module_id)}))


def change_scope(repository, module_id: str) -> tuple[str, ...]:
    """Every Module a change owned by ``module_id`` may edit, the owner included.

    The owner, the Modules it contains or uses, every Module whose Spec context selects one of the
    owner's documents (its consumers, its parent and Modules that include its documents), every
    Module that participates in a contract it defines or participates in (and the contract's
    owner), every Module whose declarations import, narrow, supersede, relate to, rely on or
    participate in a node it defines, and every Module that binds a file it binds. One level only:
    a Module in the scope does not bring its own scope.
    """
    declaration = repository.declarations[module_id]
    scope = {module_id}
    scope.update(item["target"] for item in declaration.contains)
    scope.update(item["target"] for item in declaration.uses)
    for path in declaration.owns:
        unit = repository.units.get(path)
        if unit is not None:
            scope.update(repository.selected_by(unit.document_id))
    nodes = owned_nodes(repository, module_id)
    contracts = {
        identity for identity in nodes if repository.nodes[identity].type == "contract"
    }
    contracts.update(item["contract"] for item in declaration.participates)
    for contract in contracts:
        node = repository.nodes.get(contract)
        if node is not None:
            scope.add(node.owner)
            scope.update(item["module"] for item in repository.referenced_by(contract))
    for identity in (module_id, *nodes):
        scope.update(item["module"] for item in repository.referenced_by(identity))
    scope.update(binding_modules(repository, module_id))
    return tuple(sorted(scope & set(repository.modules)))


def edited_modules(repository, paths) -> tuple[str, ...]:
    """Modules whose write sets hold a changed path: the owner of a changed Spec document member
    and every Module that binds a changed file. Paths in no write set concern no Module."""
    result: set[str] = set()
    for path in paths:
        reading = repository.source_documents.get(path)
        if reading is not None and reading in repository.units:
            result.add(repository.units[reading].owner)
        result.update(repository.implemented_by(path))
    return tuple(sorted(result & set(repository.modules)))


# --- promise-level impact ------------------------------------------------------------------


def _region(reading, line: int) -> str:
    """The text of the heading section that holds a line, heading included."""
    lines = reading.text.splitlines()
    heading = None
    for item in reading.headings:
        if item.line <= line:
            heading = item
        else:
            break
    if heading is None:
        return "\n".join(lines)
    end = next(
        (
            item.line
            for item in reading.headings
            if item.line > heading.line and item.level <= heading.level
        ),
        len(lines) + 1,
    )
    return "\n".join(lines[heading.line - 1 : end - 1])


def _record(unit, identity: str):
    return next(
        (
            record
            for record in unit.value.get("defines", [])
            if isinstance(record, dict) and record.get("id") == identity
        ),
        None,
    )


def node_definitions(repository, path: str) -> dict[str, str]:
    """The canonical definition text of every node a document defines.

    Requirements, scenarios and contracts are defined by their section; a contract also by its
    parsed fence. Concepts are defined by their metadata record, their Terminology row and the
    explanation their anchor introduces, realizations by their metadata record. The entry's
    ``module`` block defines the Module's own identity. Each value also names the document, so a
    node that moves to another document counts as changed.
    """
    unit = repository.unit(path)
    reading = repository.reading(path)
    result: dict[str, str] = {}
    for node in repository.nodes.values():
        if node.document != path:
            continue
        anchor = reading.anchors.get(node.id)
        parts: dict = {"document": path, "type": node.type, "title": node.title}
        if node.type in {"requirement", "scenario"}:
            parts["section"] = (
                _region(reading, node.line) if node.line else anchor and anchor.raw
            )
        elif node.type == "contract":
            contract = repository.contract_nodes.get(node.id, {})
            parts["contract"] = {
                key: value
                for key, value in contract.items()
                if key not in {"line", "source", "owner"}
            }
            parts["section"] = (
                anchor.raw if anchor else _region(reading, contract.get("line") or 1)
            )
        else:
            parts["record"] = _record(unit, node.id)
            if node.type == "concept":
                concept = repository.concept_nodes.get(node.id)
                parts["definition"] = concept.definition if concept else None
                parts["explanation"] = anchor.raw if anchor else None
        result[node.id] = canonical(parts)
    if unit.value.get("module") is not None:
        result[unit.owner] = canonical(
            {"document": path, "module": unit.value["module"]}
        )
    return result


def changed_documents(old, new, paths=None) -> tuple[str, ...]:
    """Reading paths of documents whose reading or metadata bytes differ between two revisions.

    A document present in only one revision is changed. ``paths`` limits the comparison.
    """
    candidates = set(old.units) | set(new.units)
    if paths is not None:
        candidates &= set(paths)
    changed = []
    for path in sorted(candidates):
        before, after = old.units.get(path), new.units.get(path)
        if (
            before is None
            or after is None
            or before.reading.content != after.reading.content
            or before.metadata.content != after.metadata.content
        ):
            changed.append(path)
    return tuple(changed)


def changed_nodes(old, new, paths) -> tuple[str, ...]:
    """Identities whose definition differs between two revisions of the given documents."""
    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for path in paths:
        if path in old.units:
            before.update(node_definitions(old, path))
        if path in new.units:
            after.update(node_definitions(new, path))
    return tuple(
        sorted(
            identity
            for identity in before.keys() | after.keys()
            if before.get(identity) != after.get(identity)
        )
    )


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


__all__ = [
    "binding_modules",
    "change_scope",
    "changed_documents",
    "changed_nodes",
    "edited_modules",
    "node_definitions",
    "owned_nodes",
    "review_impact",
    "unnarrowed_selectors",
]
