"""What installing Concorde places in a project besides the Framework tree: the Protocol copy and
the defaults the installed parts contribute.

The Protocol copy is Distribution's own: the rendered Spec Protocol bundle under
``.concorde/protocol/``, built from the tracked manifest ``protocol/manifest.json``, whose shape
Spec core defines and which Distribution reads itself, and the rendered assets it lists, placed only
where the spec part is installed. The defaults are the Concorde-owned files each installed part's
registration names under ``install.defaults``, written only where absent. Initialization creates
none of them, because it produces only what the user's project generates through Concorde.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from . import parts

PROTOCOL_DIR = ".concorde/protocol"
PROTOCOL_MANIFEST_PATH = PROTOCOL_DIR + "/manifest.json"
RENDERED_PROTOCOL_PREFIX = "generated/protocol/"

__all__ = [
    "PROTOCOL_DIR",
    "PROTOCOL_MANIFEST_PATH",
    "CopyError",
    "binding",
    "install_project_defaults",
    "project_default_files",
    "protocol_asset_path",
    "protocol_files",
    "write_protocol_copy",
]


class CopyError(ValueError):
    """The Protocol copy cannot be built: a stale build or an asset that changed since its
    manifest was written."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def binding(manifest: bytes) -> dict:
    """The Protocol binding of a manifest's bytes, as the project configuration holds it."""
    return {
        "version": json.loads(manifest.decode("utf-8"))["version"],
        "digest": digest(manifest),
    }


def protocol_asset_path(asset_path: str) -> str:
    """Where a rendered Protocol asset lives in a project: ``generated/protocol/<name>`` is
    installed as ``.concorde/protocol/<name>``."""
    if not asset_path.startswith(RENDERED_PROTOCOL_PREFIX):
        raise CopyError(
            f"the Protocol manifest lists {asset_path}, which is not under "
            f"{RENDERED_PROTOCOL_PREFIX}",
            "invalid_manifest",
        )
    return PROTOCOL_DIR + "/" + asset_path.removeprefix(RENDERED_PROTOCOL_PREFIX)


def _read(package: Path, relative: str) -> bytes:
    path = package / relative
    if any(part in ("", ".", "..") for part in PurePosixPath(relative).parts) or (
        path.is_symlink() or not path.is_file()
    ):
        raise CopyError(
            f"{relative} is missing or unsafe in {package}", "invalid_manifest"
        )
    return path.read_bytes()


def protocol_files(package: Path) -> dict[str, bytes]:
    """The Protocol bundle a project carries under ``.concorde/protocol/``.

    It is the package manifest verbatim, whose digest is the configuration binding, and every
    rendered asset the manifest lists. Agents are granted the Protocol as these project files.
    """
    from .build import BuildError, verify_fresh

    try:
        verify_fresh(package)
    except BuildError as error:
        raise CopyError(str(error), error.code) from error
    raw = _read(package, "protocol/manifest.json")
    files = {PROTOCOL_MANIFEST_PATH: raw}
    try:
        assets = json.loads(raw.decode("utf-8"))["assets"]
    except (UnicodeError, ValueError, KeyError, TypeError) as error:
        raise CopyError(
            f"protocol/manifest.json cannot be read: {error}", "invalid_manifest"
        )
    for item in assets:
        content = _read(package, item["path"])
        if digest(content) != item["digest"]:
            raise CopyError(
                f"Protocol asset has changed: {item['path']}", "protocol_mismatch"
            )
        files[protocol_asset_path(item["path"])] = content
    return files


def _write(root: Path, relative: str, content: bytes) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def write_protocol_copy(root: Path, package: Path) -> list[str]:
    """Write the Protocol copy the way the installer does (source checkout tooling and fixtures);
    nothing is written when the copy cannot be built."""
    files = protocol_files(Path(package))
    for path, content in files.items():
        _write(Path(root), path, content)
    return list(files)


def project_default_files(registrations) -> dict[str, bytes]:
    """The Concorde-owned defaults the given parts contribute; the installer seeds them only when
    absent."""
    found = {}
    for registration in registrations.values():
        for path, text in registration.data["install"]["defaults"].items():
            found[path] = text.encode("utf-8")
    return found


def install_project_defaults(root: Path, package: Path) -> list[str]:
    """Place what the installer places before a project is initialized: the Protocol copy, always,
    and the installed parts' defaults when absent. For fixtures and tooling, not a receipt-owned
    install."""
    written = write_protocol_copy(root, package)
    for path, content in project_default_files(parts.installed(Path(package))).items():
        if (Path(root) / path).exists():
            continue
        _write(Path(root), path, content)
        written.append(path)
    return written
