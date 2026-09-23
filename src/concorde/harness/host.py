"""The trusted host of one capability request and what the launcher hands admission.

An ``OperationHost`` carries the project and package roots, the execution mode and the trusted
services one request shares with the capability requests nested in it. ``AdmissionServices`` is
what admission must not import itself: the capability declarations, the dispatcher that runs an
admitted request's declared entry point, and the local installation service. The launcher (or an
embedding program) supplies them; admission only calls them.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..spec.repository import SpecError


class InstallationService(Protocol):
    """The local installation service admission relies on (Distribution provides it)."""

    def verify(self, project_root: Path, package_root: Path) -> None:
        """Refuse a top-level run whose package is not this worktree's own installation."""

    def install(
        self, candidate: Path, package_root: Path, bootstrap: bool
    ) -> tuple[Path, Path]:
        """The candidate's own interpreter and launcher, installing only when ``bootstrap``."""


@dataclass(frozen=True)
class AdmissionServices:
    """The capability declarations, the dispatcher and the installation service of one launcher.

    ``catalog`` maps each capability name to its declaration as
    ``contract.admission.capability-declaration`` defines it. ``dispatcher`` receives one
    ``AdmittedRequest`` and returns the capability's response typed value. ``installation`` is
    None for an embedding program that installs nothing.
    """

    catalog: Mapping[str, Mapping[str, Any]]
    dispatcher: Callable[[AdmittedRequest], dict]
    installation: InstallationService | None = None


@dataclass(frozen=True)
class AdmittedRequest:
    """One capability request after admission: what the dispatcher and the entry point receive."""

    operation: str
    declaration: Mapping[str, Any]
    configuration: dict | None
    data: dict
    mutates: bool
    host: OperationHost


@dataclass(frozen=True)
class OperationHost:
    project_root: Path
    package_root: Path
    mode: str = "execute"
    services: AdmissionServices | None = None
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
    # The top-level request's identity, inherited by every nested request so one run keeps one
    # run directory under .concorde/runs/<root_invocation_id>/.
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
