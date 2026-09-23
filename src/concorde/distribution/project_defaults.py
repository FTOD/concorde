"""What installing Concorde places in a project besides the Framework tree.

Everything here exists only because Concorde is installed: the Protocol copy the configuration
binds and agents are granted, and the Concorde-owned defaults a project starts from. The installer
deploys them; initialization creates none of them, because initialization produces only what the
user's project generates through Concorde (its configuration, registry and Module stub).
"""

from __future__ import annotations

from pathlib import Path

from ..spec.repository import (
    PROTOCOL_DIR,
    PROTOCOL_MANIFEST_PATH,
    SpecError,
    digest,
    protocol_asset_path,
    read_file,
)
from ..spec.typed_data import checked_path, decode

__all__ = [
    "ISSUES_IGNORE_PATH",
    "PROTOCOL_DIR",
    "PROTOCOL_MANIFEST_PATH",
    "install_project_defaults",
    "project_default_files",
    "protocol_asset_path",
    "protocol_files",
    "write_protocol_copy",
]

ISSUES_IGNORE_PATH = ".concorde/issues/.gitignore"


def protocol_files(package: Path) -> dict[str, bytes]:
    """The Protocol bundle a project carries under ``.concorde/protocol/``.

    It is the package manifest verbatim, whose digest is the configuration binding, and every
    rendered asset the manifest lists. Agents are granted the Protocol as these project files.
    """
    from .build import BuildError, verify_fresh

    try:
        verify_fresh(package)
    except BuildError as error:
        raise SpecError(str(error), error.code) from error
    raw = read_file(package, "protocol/manifest.json")
    files = {PROTOCOL_MANIFEST_PATH: raw}
    for item in decode(raw.decode())["assets"]:
        content = read_file(package, item["path"])
        if digest(content) != item["digest"]:
            raise SpecError(
                f"Protocol asset has changed: {item['path']}", "protocol_mismatch"
            )
        files[protocol_asset_path(item["path"])] = content
    return files


def project_default_files(package: Path) -> dict[str, bytes]:
    """Concorde-owned defaults a project starts from; the installer seeds them only when absent."""
    return {
        ISSUES_IGNORE_PATH: b"# Issue records are versioned project data. Host locks live under ../runs/.\n",
    }


def write_protocol_copy(root: Path, package: Path) -> list[str]:
    """Write the Protocol copy the way the installer does (source checkout tooling and fixtures)."""
    written = []
    for path, content in protocol_files(package).items():
        target = checked_path(root, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        written.append(path)
    return written


def install_project_defaults(root: Path, package: Path) -> list[str]:
    """Place what the installer places before a project is initialized: the Protocol copy, always,
    and the Concorde-owned defaults when absent. For fixtures and tooling, not a receipt-owned install."""
    written = write_protocol_copy(root, package)
    for path, content in project_default_files(package).items():
        target = checked_path(root, path)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        written.append(path)
    return written
