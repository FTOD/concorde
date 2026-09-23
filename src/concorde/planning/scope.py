"""Planning's change scope: which Modules a change owned by one Module may edit.

Built on Spec tooling's impact indexes; the policy itself is Planning's.
"""

from __future__ import annotations

from ..spec.impact import binding_modules


def owned_nodes(repository, module_id: str) -> tuple[str, ...]:
    """Identities of every node the Module defines, in identity order."""
    return tuple(
        sorted(node.id for node in repository.nodes.values() if node.owner == module_id)
    )


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
