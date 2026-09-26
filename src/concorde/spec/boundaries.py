"""Boundary-set records of Spec Protocol 13 (``protocol/boundaries.md``).

The repository computes every set from declarations alone (``SpecRepository.boundary_sets``,
``spec_context``, ``implementation_context``, ``external_context``, ``spec_scope`` and
``implementation_scope``) and the impact indexes that answer the reverse question, whom a write
concerns (``selected_by``, ``referenced_by``, ``implemented_by``, ``shared_files`` and
``impact``). This module holds the immutable records those queries return and the path helper
that turns a set of entries into permission roots.
"""

from __future__ import annotations

from dataclasses import dataclass

from .repository_base import bound_by, entry_base


@dataclass(frozen=True)
class ExternalEntry:
    """One ``includes`` of kind ``external``: the entry, its readable files and one tree digest.

    ``exists`` is false when the pinned material is not checked out; it then has no files.
    """

    path: str
    directory: bool
    files: tuple[str, ...]
    digest: str
    exists: bool = True

    def record(self) -> dict:
        """The snapshot form: entry, kind and tree digest, never the bytes."""
        return {"path": self.path, "directory": self.directory, "digest": self.digest}


@dataclass(frozen=True)
class BoundarySets:
    """The boundary sets of one Module."""

    module: str
    spec_context: tuple[str, ...]
    external_context: tuple[ExternalEntry, ...]
    implementation_context: tuple[str, ...]
    spec_scope: tuple[str, ...]
    implementation_scope: tuple[str, ...]
    # The whole project's implementation, the same for every Module: every realization entry and
    # every piece of external material, so that a code task can read and run the code it uses.
    project_implementation: tuple[str, ...] = ()

    def writable(self, path: str) -> bool:
        """Whether a path lies in one of the two write sets."""
        return path in self.spec_scope or any(
            bound_by(entry, path) for entry in self.implementation_scope
        )


def scope_roots(entries) -> tuple[str, ...]:
    """Permission roots of path entries: each entry without its trailing slash, in order."""
    return tuple(dict.fromkeys(entry_base(entry) for entry in entries))


__all__ = ["BoundarySets", "ExternalEntry", "scope_roots"]
