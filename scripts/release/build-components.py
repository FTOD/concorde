#!/usr/bin/env python3
"""Build deterministic Concorde component archives and matching catalogs.

The release version has exactly one authority: ``bundle.version`` in
``bundles/concorde-bundle/bundle.yml``. The bundle's pinned component versions and the
preset/extension manifests must agree with it, and every manifest must advertise the
maintained repository. A build stops with a named disagreement before writing anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path
from typing import Iterable, NamedTuple

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "https://github.com/FTOD/concorde"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
CATALOG_UPDATED_AT = "2026-08-20T00:00:00Z"

BUNDLE_MANIFEST = "bundles/concorde-bundle/bundle.yml"
PRESET_MANIFEST = "presets/concorde-core/preset.yml"
EXTENSION_MANIFEST = "extensions/concorde/extension.yml"


class ReleaseIdentityError(ValueError):
    """Raised when the maintained manifests disagree about version or repository."""


class ReleaseIdentity(NamedTuple):
    version: str
    speckit_range: str
    repository: str


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ReleaseIdentityError(f"{path}: manifest is not a mapping")
    return loaded


def _pinned(bundle: dict, collection: str, identifier: str) -> str | None:
    for entry in bundle.get("provides", {}).get(collection, []) or []:
        if entry.get("id") == identifier:
            return str(entry.get("version"))
    return None


def read_release_identity(root: Path = REPOSITORY_ROOT) -> ReleaseIdentity:
    """Read the single release version and check every manifest agrees with it."""
    bundle = _load_yaml(root / BUNDLE_MANIFEST)
    preset = _load_yaml(root / PRESET_MANIFEST)
    extension = _load_yaml(root / EXTENSION_MANIFEST)

    version = str(bundle["bundle"]["version"])
    observed_versions = {
        f"{BUNDLE_MANIFEST} provides.presets[concorde-core].version": _pinned(bundle, "presets", "concorde-core"),
        f"{BUNDLE_MANIFEST} provides.extensions[concorde].version": _pinned(bundle, "extensions", "concorde"),
        f"{PRESET_MANIFEST} preset.version": str(preset["preset"]["version"]),
        f"{EXTENSION_MANIFEST} extension.version": str(extension["extension"]["version"]),
    }
    disagreements = [f"{name} declares {value}" for name, value in observed_versions.items() if value != version]
    if disagreements:
        raise ReleaseIdentityError(
            f"release version disagreement: {BUNDLE_MANIFEST} bundle.version declares {version} but "
            + "; ".join(disagreements)
        )

    speckit_range = str(bundle["requires"]["speckit_version"])
    range_disagreements = [
        f"{name} declares {value}"
        for name, value in {
            f"{PRESET_MANIFEST} requires.speckit_version": str(preset["requires"]["speckit_version"]),
            f"{EXTENSION_MANIFEST} requires.speckit_version": str(extension["requires"]["speckit_version"]),
        }.items()
        if value != speckit_range
    ]
    if range_disagreements:
        raise ReleaseIdentityError(
            f"Spec Kit range disagreement: {BUNDLE_MANIFEST} declares {speckit_range} but "
            + "; ".join(range_disagreements)
        )

    repositories = {
        f"{PRESET_MANIFEST} preset.repository": preset["preset"].get("repository"),
        f"{EXTENSION_MANIFEST} extension.repository": extension["extension"].get("repository"),
    }
    wrong_repositories = [f"{name} declares {value}" for name, value in repositories.items() if value != REPOSITORY]
    if wrong_repositories:
        raise ReleaseIdentityError(
            f"repository disagreement: releases are published from {REPOSITORY} but " + "; ".join(wrong_repositories)
        )
    return ReleaseIdentity(version=version, speckit_range=speckit_range, repository=REPOSITORY)


def read_release_version(root: Path = REPOSITORY_ROOT) -> str:
    return read_release_identity(root).version


def default_base_url(version: str, repository: str = REPOSITORY) -> str:
    """Version-specific public location of the release assets."""
    return f"{repository}/releases/download/v{version}"


def _allowed_member(component: str, relative: Path) -> bool:
    path = relative.as_posix()
    if component == "concorde-core":
        return path in {"README.md", "preset.yml"} or (
            (path.startswith("commands/") or path.startswith("templates/")) and path.endswith(".md")
        )
    if component == "concorde":
        return (
            path in {"README.md", "extension.yml"}
            or (path.startswith("commands/") and path.endswith(".md"))
            or (path.startswith("scripts/bash/") and path.endswith(".sh"))
            or (path.startswith("scripts/powershell/") and path.endswith(".ps1"))
            or (path.startswith("scripts/python/") and path.endswith(".py"))
            or (path.startswith("runtime/concorde/") and path.endswith(".py"))
            or (path.startswith("schemas/") and path.endswith(".json"))
        )
    if component == "concorde-bundle":
        return path in {"README.md", "bundle.yml"}
    return False


def _source_files(directory: Path, component: str) -> Iterable[Path]:
    for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if not _allowed_member(component, relative):
            raise ValueError(f"{component}: source file is outside the release allowlist: {relative.as_posix()}")
        yield path


def deterministic_zip(
    source: Path,
    destination: Path,
    component: str,
    version: str | None = None,
    manifest_version: str | None = None,
) -> str:
    """Write a reproducible archive; returns its SHA-256 hex digest.

    ``version`` different from ``manifest_version`` rewrites the manifest version inside text
    members. That override exists only so acceptance fixtures can simulate a later release; a
    real release never passes it.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _source_files(source, component):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
            info.create_system = 3
            content = path.read_bytes()
            if version and manifest_version and version != manifest_version:
                try:
                    content = content.decode("utf-8").replace(manifest_version, version).encode("utf-8")
                except UnicodeDecodeError:
                    pass
            archive.writestr(info, content)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_release(output: Path, base_url: str | None = None, version: str | None = None) -> dict[str, str]:
    """Build the three archives and three catalogs into ``output``.

    ``base_url`` defaults to the version-specific public location. ``version`` overrides the
    manifest version only for acceptance fixtures that simulate a later release.
    """
    identity = read_release_identity()
    manifest_version = identity.version
    version = version or manifest_version
    base_url = base_url or default_base_url(version)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archives = {
        f"concorde-core-{version}.zip": ("concorde-core", REPOSITORY_ROOT / "presets/concorde-core"),
        f"concorde-{version}.zip": ("concorde", REPOSITORY_ROOT / "extensions/concorde"),
        f"concorde-bundle-{version}.zip": ("concorde-bundle", REPOSITORY_ROOT / "bundles/concorde-bundle"),
    }
    digests = {
        name: deterministic_zip(source, output / name, component, version, manifest_version)
        for name, (component, source) in archives.items()
    }
    common = {
        "author": "Concorde maintainers",
        "license": "MIT",
        "repository": identity.repository,
        "requires": {"speckit_version": identity.speckit_range},
        "verified": False,
    }
    _write_json(
        output / "extensions.json",
        {
            "schema_version": "1.0",
            "updated_at": CATALOG_UPDATED_AT,
            "catalog_url": f"{base_url}/extensions.json",
            "extensions": {
                "concorde": {
                    **common,
                    "id": "concorde",
                    "name": "Concorde Architecture Workflow",
                    "version": version,
                    "description": "Initialize, retrieve, validate, accept, and explain bounded hierarchical feature work",
                    "effect": "read-write",
                    "download_url": f"{base_url}/concorde-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-{version}.zip']}",
                    "provides": {"commands": 5, "scripts": 4},
                    "tags": ["architecture", "context", "validation"],
                }
            },
        },
    )
    _write_json(
        output / "presets.json",
        {
            "schema_version": "1.0",
            "updated_at": CATALOG_UPDATED_AT,
            "catalog_url": f"{base_url}/presets.json",
            "presets": {
                "concorde-core": {
                    **common,
                    "id": "concorde-core",
                    "name": "Concorde Core",
                    "version": version,
                    "description": "Architecture guidance plus authoritative nested-workspace routing for the Spec Kit lifecycle",
                    "download_url": f"{base_url}/concorde-core-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-core-{version}.zip']}",
                    "provides": {"templates": 6, "commands": 10},
                    "tags": ["architecture", "contracts", "spec-driven-development"],
                }
            },
        },
    )
    _write_json(
        output / "bundles.json",
        {
            "schema_version": "1.0",
            "updated_at": CATALOG_UPDATED_AT,
            "catalog_url": f"{base_url}/bundles.json",
            "bundles": {
                "concorde-bundle": {
                    **common,
                    "id": "concorde-bundle",
                    "name": "Concorde Bundle",
                    "version": version,
                    "role": "developer",
                    "description": "Pinned Concorde preset and extension installation recipe for Spec Kit",
                    "download_url": f"{base_url}/concorde-bundle-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-bundle-{version}.zip']}",
                    "provides": {"extensions": 1, "presets": 1, "steps": 0, "workflows": 0},
                    "tags": ["architecture", "context", "validation", "spec-driven-development"],
                }
            },
        },
    )
    return {name: f"sha256:{digest}" for name, digest in sorted(digests.items())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument(
        "--base-url",
        default=None,
        help="Catalog/archive location written into metadata (default: the version-specific release location)",
    )
    parser.add_argument("--publish-catalogs", action="store_true", help="Also copy the catalogs to catalogs/ (local convenience)")
    parser.add_argument("--print-version", action="store_true", help="Print the manifest release version and exit")
    arguments = parser.parse_args()
    try:
        if arguments.print_version:
            print(read_release_version())
            return 0
        digests = build_release(arguments.output, arguments.base_url)
    except ReleaseIdentityError as error:
        print(f"error: {error}")
        return 1
    if arguments.publish_catalogs:
        (REPOSITORY_ROOT / "catalogs").mkdir(exist_ok=True)
        for name in ("extensions.json", "presets.json", "bundles.json"):
            (REPOSITORY_ROOT / "catalogs" / name).write_bytes((arguments.output / name).read_bytes())
    print(json.dumps(digests, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
