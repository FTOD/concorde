"""Explicit full worktree installations, never cross-worktree execution fallbacks.

The caller owns its target and excludes other writers/launches for the transaction.
This service has no authority to create worktrees, accept Protocol or persist lifecycle truth.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from . import installation as installer
from . import managed_runtime


@dataclass(frozen=True)
class PackageSource:
    root: Path
    version: str
    digest: str
    build_digest: str

    @property
    def identity(self) -> dict[str, str]:
        return {
            "version": self.version,
            "digest": self.digest,
            "build_digest": self.build_digest,
        }


@dataclass(frozen=True)
class LocalInstallation:
    target: Path
    framework: Path
    pi_entry: Path
    python: Path
    launcher: Path
    receipt: Path
    package: PackageSource
    provider_root: str
    receipt_digest: str
    runtime_digest: str
    protocol_matches_package: bool
    status: str = "verified"


def _canonical(path: Path) -> Path:
    path = path.absolute()
    if path != path.resolve():
        raise installer.InstallError(
            f"installation path must be canonical without symlinks: {path}"
        )
    return path


def admit_package(root: Path) -> PackageSource:
    """Admit the explicitly invoking package, binding its exact deployment, not just version."""
    root = _canonical(root)
    package = installer.load_package(root)
    identity = installer.package_identity(package)
    return PackageSource(root, **identity)


@contextmanager
def installation_lock(target: Path) -> Iterator[None]:
    """Serialize supported installer writers; lock inode is stable and never unlinked.

    POSIX flock releases on process death. Unsupported locking fails before deployment.
    The lock is installation metadata only, not a candidate-local lifecycle record.
    """
    try:
        import fcntl
    except ImportError as error:
        raise installer.InstallError(
            "local installation requires POSIX file locking"
        ) from error
    path = installer._check_parent(target, ".concorde/install.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise installer.InstallError("installation lock must be one regular file")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise installer.InstallError(
                "another installer owns this target; retry after it finishes"
            ) from error
        yield
    finally:
        os.close(fd)


def verify_installation(
    target: Path, *, expected: PackageSource | None = None
) -> LocalInstallation:
    """Read-only local integrity/health observation; no install, marker refresh or fallback.

    Protocol compatibility is reported separately: this is not Operation admission.
    The caller must keep the worktree quiescent through its later launch.
    """
    target = _canonical(target)
    receipt_path = installer._check_parent(target, installer.RECEIPT_PATH)
    before = installer._file_digest(receipt_path)
    if before is None:
        raise installer.InstallError(
            "local install receipt is missing; explicitly bootstrap this worktree"
        )
    framework = target / installer.FRAMEWORK_ROOT
    source = admit_package(framework)
    if expected is not None and source.identity != expected.identity:
        raise installer.InstallError(
            "local package differs from admitted invoking package; explicitly update it"
        )
    package = installer.Package(
        framework, installer._read_json(framework / "concorde.json", "package")
    )
    receipt = installer._verify_owned(target, package)
    # Check preserved bundles for completeness too; never fill them with another version.
    if receipt.get("preserve_project"):
        installer._preserve_project(target, {}, receipt)
    spec = managed_runtime.load_runtime_spec(framework, package.manifest)
    try:
        runtime = managed_runtime.verify_runtime(target, framework, spec, receipt)
    except managed_runtime.ManagedRuntimeError as error:
        raise installer.InstallError(str(error)) from error
    if installer._file_digest(receipt_path) != before:
        raise installer.InstallError("installation receipt changed during verification")
    installer._verify_owned(target, package)
    protocol = target / installer.PROTOCOL_ROOT / "manifest.json"
    return LocalInstallation(
        target=target,
        framework=framework,
        pi_entry=target / ".pi/extensions/concorde-session.ts",
        python=managed_runtime.runtime_python(target / spec.venv),
        launcher=framework / spec.launcher,
        receipt=receipt_path,
        package=source,
        provider_root=receipt.get("provider_root", ""),
        receipt_digest=before,
        runtime_digest=runtime["runtime_sha256"],
        protocol_matches_package=installer._file_digest(protocol)
        == installer._file_digest(framework / "protocol/manifest.json"),
    )


def ensure_installation(
    target: Path,
    source: PackageSource,
    *,
    bootstrap: bool = False,
    preserve_project: bool = True,
) -> LocalInstallation:
    """Verify/reuse local assets; only an explicit host bootstrap may apply a current plan.

    ``source`` must be issued from the exact invoking package. It is rechecked, never
    rediscovered by package name or primary-worktree location. This is not a worker API.
    """
    target = _canonical(target)
    current = admit_package(source.root)
    if current != source:
        raise installer.InstallError(
            "admitted package changed; re-admit before installing"
        )
    if (target / "concorde.json").exists() and (target / "src/concorde").exists():
        raise installer.InstallError(
            "cannot install into an active Concorde source checkout"
        )
    try:
        return verify_installation(target, expected=source)
    except (installer.InstallError, OSError, ValueError):
        if not bootstrap:
            raise
    installer._check_target(target)
    with installation_lock(target):
        # Recheck provider after obtaining ownership; a saved identity is not perpetual authority.
        if admit_package(source.root) != source:
            raise installer.InstallError(
                "admitted package changed while waiting to install"
            )
        package = installer.load_package(source.root)
        actions, desired, _ = installer.installation_plan(
            target, package, preserve_project=preserve_project
        )
        installer.apply_plan(
            target, package, actions, desired, preserve_project=preserve_project
        )
        return verify_installation(target, expected=source)
