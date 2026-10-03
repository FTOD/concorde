"""The Operation catalog: the Operation definitions the installed parts register.

A part registers its definitions when its code loads, as the kernel's typed values and trace roots
are registered; Execution provides no definition of its own. ``Catalog`` is also the command
catalog's shape (``concorde.execution.commands.catalog``).
"""

from __future__ import annotations

import re

from ..context import Provider

MODULE_ID = re.compile(r"^module\.[a-z0-9][a-z0-9.-]*$")


class CatalogError(Exception):
    """A definition the catalog refuses to register: ``duplicate_definition`` when another part
    registered the name already, ``invalid_definition`` for anything that is no definition of
    the catalog's kind."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class Catalog:
    """The definitions of one kind (``operation`` or ``command``), one per name, each with its
    providing Module and the part that registered it."""

    def __init__(self, kind: str):
        self.kind = kind
        self.definitions: dict[str, Provider] = {}
        self.parts: dict[str, str] = {}

    def register(self, part: str, definition: Provider) -> None:
        """Register ``definition`` for ``part``; registering the same one again changes nothing,
        another under a registered name is refused naming both parts."""
        if not isinstance(definition, Provider) or definition.kind != self.kind:
            raise CatalogError(
                "invalid_definition",
                f"{part} registers {definition!r} as an {self.kind}, which it is not",
            )
        if not isinstance(definition.module, str) or not MODULE_ID.match(
            definition.module
        ):
            raise CatalogError(
                "invalid_definition",
                f"{part} registers the {self.kind} {definition.name} without the identity of "
                f"its providing Module (module {definition.module!r})",
            )
        if self.kind == "operation" and not definition.workers:
            raise CatalogError(
                "invalid_definition",
                f"{part} registers the operation {definition.name} without a worker id; an "
                "Operation launches at least one worker, and a job that launches none is an "
                "execution command",
            )
        name = definition.name
        existing = self.definitions.get(name)
        if existing is not None:
            if existing == definition and self.parts.get(name) == part:
                return
            raise CatalogError(
                "duplicate_definition",
                f"the {self.kind} {name} is registered by {self.parts.get(name, 'a part')} "
                f"and again by {part}; one name has one definition",
            )
        self.definitions[name] = definition
        self.parts[name] = part

    def get(self, name: str) -> Provider | None:
        return self.definitions.get(name)

    def part(self, name: str) -> str | None:
        """The part that registered ``name``."""
        return self.parts.get(name)

    def module(self, name: str) -> str | None:
        """The identity of the Module that provides ``name``."""
        definition = self.definitions.get(name)
        return definition.module if definition is not None else None

    def __contains__(self, name) -> bool:
        return name in self.definitions

    def __iter__(self):
        return iter(sorted(self.definitions))


OPERATIONS = Catalog("operation")


__all__ = ["OPERATIONS", "Catalog", "CatalogError"]
