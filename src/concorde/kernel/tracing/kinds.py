"""Node kinds: the kinds of trace node the parts produce, with their content types and metadata.

The part a producer belongs to registers each of its kinds here as plain data when its code loads,
as it registers its trace roots and typed value types: in Concorde, Coordination its task, session,
merge and delivery kinds, Execution its run and check kinds, Workflows its workflow and step kinds
and the worker harness its worker-run and worker-round kinds. Tracing checks every node it writes
against the registration of its kind, and so names no part's kinds itself
(``specs/concorde/kernel/tracing/contracts.md#node-kinds``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class KindError(Exception):
    """A node kind registered again with another definition, or a definition that is not one."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NodeKind:
    """One registered node kind.

    ``kind`` is its name, ``content_type`` the type identity of its nodes' content and
    ``metadata`` the metadata dimensions its nodes may list.
    """

    kind: str
    content_type: str
    metadata: tuple[str, ...]


_KINDS: dict[str, NodeKind] = {}
_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def register(*kinds: NodeKind) -> None:
    """Register each of ``kinds``; registering an equal kind again changes nothing, another
    definition under a registered name is refused with ``duplicate_kind``."""
    from .node import METADATA

    for item in kinds:
        if (
            not isinstance(item, NodeKind)
            or not isinstance(item.kind, str)
            or not _NAME.match(item.kind)
            or not isinstance(item.content_type, str)
            or not item.content_type
            or not isinstance(item.metadata, tuple)
            or any(name not in METADATA for name in item.metadata)
        ):
            raise KindError("invalid_kind", f"{item!r} is no node kind definition")
        existing = _KINDS.get(item.kind)
        if existing is not None and existing != item:
            raise KindError(
                "duplicate_kind",
                f"the node kind {item.kind} is registered already as {existing!r}",
            )
        _KINDS[item.kind] = item


def lookup(kind: str) -> NodeKind | None:
    """The registration of ``kind``, or None when no installed part registered it."""
    return _KINDS.get(kind)


def registered() -> tuple[NodeKind, ...]:
    """Every registered kind, in the order registered."""
    return tuple(_KINDS.values())


__all__ = ["KindError", "NodeKind", "lookup", "register", "registered"]
