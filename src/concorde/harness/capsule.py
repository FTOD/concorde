"""Capsule assembly: the delivered copies of one Agent call's context.

The capsule is the ``context/`` directory an Agent call starts in. It holds byte-identical copies of
exactly the files the snapshot delivers to the bound Agent and the snapshot itself as
``context.json``. Assembly returns the digest of every file it wrote; verification recomputes them
before acceptance and compares every context document with its current source bytes.
"""

from __future__ import annotations

from pathlib import Path

from ..spec.boundaries import scope_roots
from ..spec.repository import (
    REFERENCE_SKIPPED_SUFFIXES,
    SpecError,
    SpecRepository,
    digest,
    expand_entry,
    read_file,
)
from ..spec.typed_data import canonical, checked_path, typed
from .context import ContextSnapshot, context_documents, writes_implementation


def _effects(value: dict) -> dict:
    return value["agent_binding"]["effects"]


def delivered_documents(repository: SpecRepository, value: dict) -> list[str]:
    """The project-relative paths of every Protocol and Spec context file the capsule holds."""
    return list(context_documents(repository, value))


def context_index(
    repository: SpecRepository, snapshot: ContextSnapshot, review: dict | None = None
) -> str:
    """The text of ``context.json`` for a snapshot, with its review input when there is one."""
    value = snapshot.value
    if review is not None:
        return (
            canonical(
                {
                    "snapshot": typed("concorde-context-snapshot", value),
                    "review": typed("concorde-review-input", review),
                }
            )
            + "\n"
        )
    if writes_implementation(value):
        target = repository.module(value["target_id"], value["focus_id"])
        return (
            canonical(
                {
                    **value,
                    "native_workspace": str(repository.root),
                    "intended_write_paths": [
                        str(repository.root / path)
                        for path in scope_roots(repository.implementation_scope(target))
                    ],
                    "file_scope_enforcement": "prompt-level",
                    "network_and_credentials": "model policy, not OS confinement",
                }
            )
            + "\n"
        )
    return snapshot.serialized + "\n"


def _write(directory: Path, relative: str, raw: bytes) -> None:
    copy = checked_path(directory, relative)
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_bytes(raw)


def assemble_capsule(
    repository: SpecRepository,
    snapshot: ContextSnapshot,
    directory: Path,
    review: dict | None = None,
) -> dict[str, str]:
    """Write the capsule into ``directory`` and return the digest of every file it wrote."""
    value = snapshot.value
    effects = _effects(value)
    files: dict[str, bytes] = dict(context_documents(repository, value))
    if "references" in effects["reads"]:
        for record in value["external_references"]:
            for path in expand_entry(
                repository.root,
                record["path"],
                skipped_suffixes=REFERENCE_SKIPPED_SUFFIXES,
            ):
                files[path] = read_file(repository.root, path)
    if "implementation" in effects["reads"] and not writes_implementation(value):
        for item in value["implementation_artifacts"]:
            raw = read_file(repository.root, item["path"])
            if digest(raw) != item["digest"]:
                raise SpecError(
                    f"implementation file changed: {item['path']}", "stale_context"
                )
            files[item["path"]] = raw
    files["context.json"] = context_index(repository, snapshot, review).encode()
    directory.mkdir(parents=True, exist_ok=True)
    for relative, raw in files.items():
        _write(directory, relative, raw)
    return {relative: digest(raw) for relative, raw in sorted(files.items())}


def verify_capsule(
    repository: SpecRepository,
    snapshot: ContextSnapshot,
    directory: Path,
    digests: dict[str, str],
) -> None:
    """Refuse with ``stale_context`` when a capsule file or a context source changed."""
    for relative, expected in digests.items():
        if digest(read_file(directory, relative)) != expected:
            raise SpecError("delivered capsule file changed", "stale_context")
    for relative, raw in context_documents(repository, snapshot.value).items():
        if read_file(directory, relative) != raw:
            raise SpecError("delivered context document changed", "stale_context")
