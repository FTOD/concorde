"""Protocol-derived change indexes (Protocol ``boundaries.md`` and ``context.md``).

Computed from declarations alone, through the Protocol-named repository queries
(``selected_by``, ``referenced_by``, ``implemented_by``, ``shared_files``): the binding Modules of
a Module and the documents and node definitions that differ between two revisions. Which Modules
a change may edit, which need a fresh review and which a candidate edited are policies of
Planning, Review and Validation built on these indexes.
"""

from __future__ import annotations

from .typed_data import canonical


def binding_modules(repository, module_id: str) -> tuple[str, ...]:
    """The Module and every Module that binds a file in its ImplementationScope.

    Computed from entries alone (``shared_files``), so pending entries count as well.
    """
    return tuple(sorted({module_id, *repository.shared_files(module_id)}))


# --- changed definitions ------------------------------------------------------------------


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


__all__ = [
    "binding_modules",
    "changed_documents",
    "changed_nodes",
    "node_definitions",
]
