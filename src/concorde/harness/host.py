"""The trusted host of one operation invocation.

An ``OperationHost`` carries the project and package roots, the execution mode and the trusted
services one invocation shares with its nested invocations.
"""

from __future__ import annotations

import importlib
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..operations.catalog import load_operation_inventory
from ..spec.repository import SpecError


@dataclass(frozen=True)
class OperationHost:
    project_root: Path
    package_root: Path
    mode: str = "execute"
    # Finite native context preparation/acceptance only; never a suspended model callback.
    native_assessment: Any = None
    native_transport: bool = False
    allow_primary_worktree: bool = False
    outer_sandbox: str | None = None
    # A mutation admitted in the primary worktree runs in a host-created candidate worktree.
    # ``relay`` runs the same invocation there (``relay_operation``, the candidate's own launcher
    # in a subprocess, unless a trusted caller supplies another runner) and ``relay_target``
    # names that candidate once bind_workspace prepared it.
    relay: Any = None
    relay_target: dict | None = None
    configuration_snapshot: str = ""
    session_root: Path | None = None
    archive_root: Path | None = None
    session_provenance: dict | None = None
    coordinated: bool = False
    track_gaps: bool = False
    depth: int = 0
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # The top-level operation invocation's identity, inherited by every nested invocation so one
    # Graph run keeps one run directory under .concorde/runs/<root_invocation_id>/.
    root_invocation_id: str | None = None
    evidence: list[Any] = field(default_factory=list)
    lifecycle: dict = field(default_factory=dict)
    observer: Any = None

    def observe(self, event: str, **details) -> None:
        # Observability must never turn a completed mutation into a retryable failure.
        if self.observer is not None:
            with suppress(Exception):
                self.observer(event, **details)

    def __post_init__(self):
        if self.project_root.is_symlink() or self.package_root.is_symlink():
            raise SpecError("host roots cannot be symlinks", "workspace_mismatch")
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "package_root", self.package_root.resolve())
        object.__setattr__(
            self, "session_root", (self.session_root or self.project_root).resolve()
        )


def _operation_key(operation: str) -> str:
    return operation[len("concorde-") :].replace("-", "_")


def resolve_child_operation(parent_operation: str, child_operation: str):
    """Return the child operation module for one in-process nested dispatch, or refuse it.

    A parent may always invoke itself (recursive fan-out across component targets, as
    ``review_scope`` and ``implement_scope`` do, is not operation composition and needs no
    declared edge). Any other child must appear in the parent operation module's declared
    ``USES``, or this raises ``SpecError(..., "undeclared_operation")``. Pure name resolution
    with no side effect beyond importing the two modules; kept separate from ``invoke_operation``
    so the declared composition graph can be checked exhaustively without executing anything.
    """

    inventory = load_operation_inventory()
    from agents import DOMAIN_AGENTS

    def namespace(key):
        return "agents" if key in DOMAIN_AGENTS else inventory.__name__

    parent_key, child_key = (
        _operation_key(parent_operation),
        _operation_key(child_operation),
    )
    for key, external in ((parent_key, parent_operation), (child_key, child_operation)):
        if (
            key not in (*inventory.OPERATIONS, *DOMAIN_AGENTS)
            or inventory.external_name(key) != external
        ):
            raise SpecError(f"unknown operation: {external}", "unknown_operation")
    if parent_key != child_key:
        try:
            parent_module = importlib.import_module(
                f"{namespace(parent_key)}.{parent_key}"
            )
        except ImportError as error:
            raise SpecError(
                f"unknown parent operation: {parent_operation}", "unknown_operation"
            ) from error
        if child_key not in parent_module.USES:
            raise SpecError(
                f"{parent_operation} has no declared composition edge to {child_operation}",
                "undeclared_operation",
            )
    try:
        return importlib.import_module(f"{namespace(child_key)}.{child_key}")
    except ImportError as error:
        raise SpecError(
            f"unknown operation: {child_operation}", "unknown_operation"
        ) from error
