#!/usr/bin/env python3
"""Build deterministic Concorde component archives and matching catalogs."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path
from typing import Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VERSION = "0.1.0"
SPECKIT_RANGE = ">=0.16.4,<0.16.5"
DEFAULT_BASE_URL = "https://github.com/concorde-workflow/concorde/releases/download/v0.1.0"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _source_files(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        yield path


def deterministic_zip(source: Path, destination: Path, version: str = VERSION) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _source_files(source):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
            info.create_system = 3
            content = path.read_bytes()
            if version != VERSION:
                try:
                    content = content.decode("utf-8").replace(VERSION, version).encode("utf-8")
                except UnicodeDecodeError:
                    pass
            archive.writestr(info, content)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_release(output: Path, base_url: str = DEFAULT_BASE_URL, version: str = VERSION) -> dict[str, str]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archives = {
        f"concorde-core-{version}.zip": REPOSITORY_ROOT / "presets/concorde-core",
        f"concorde-{version}.zip": REPOSITORY_ROOT / "extensions/concorde",
        f"concorde-starter-{version}.zip": REPOSITORY_ROOT / "bundles/concorde-starter",
    }
    digests = {name: deterministic_zip(source, output / name, version) for name, source in archives.items()}
    common = {
        "author": "Concorde maintainers",
        "license": "MIT",
        "repository": "https://github.com/concorde-workflow/concorde",
        "requires": {"speckit_version": SPECKIT_RANGE},
        "verified": False,
    }
    _write_json(
        output / "extensions.json",
        {
            "schema_version": "1.0",
            "updated_at": "2026-08-20T00:00:00Z",
            "catalog_url": f"{base_url}/extensions.json",
            "extensions": {
                "concorde": {
                    **common,
                    "id": "concorde",
                    "name": "Concorde Architecture Workflow",
                    "version": version,
                    "description": "Initialize, retrieve, and validate bounded hierarchical architecture sources",
                    "effect": "read-write",
                    "download_url": f"{base_url}/concorde-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-{version}.zip']}",
                    "provides": {"commands": 3, "scripts": 3},
                    "tags": ["architecture", "context", "validation"],
                }
            },
        },
    )
    _write_json(
        output / "presets.json",
        {
            "schema_version": "1.0",
            "updated_at": "2026-08-20T00:00:00Z",
            "catalog_url": f"{base_url}/presets.json",
            "presets": {
                "concorde-core": {
                    **common,
                    "id": "concorde-core",
                    "name": "Concorde Core",
                    "version": version,
                    "description": "Append-only architecture guidance for the Spec Kit feature lifecycle",
                    "download_url": f"{base_url}/concorde-core-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-core-{version}.zip']}",
                    "provides": {"templates": 3, "commands": 0},
                    "tags": ["architecture", "contracts", "spec-driven-development"],
                }
            },
        },
    )
    _write_json(
        output / "bundles.json",
        {
            "schema_version": "1.0",
            "updated_at": "2026-08-20T00:00:00Z",
            "catalog_url": f"{base_url}/bundles.json",
            "bundles": {
                "concorde-starter": {
                    **common,
                    "id": "concorde-starter",
                    "name": "Concorde Starter",
                    "version": version,
                    "role": "developer",
                    "description": "Architecture-aware Spec Kit starter workflow",
                    "download_url": f"{base_url}/concorde-starter-{version}.zip",
                    "sha256": f"sha256:{digests[f'concorde-starter-{version}.zip']}",
                    "provides": {"extensions": 1, "presets": 1, "steps": 0, "workflows": 0},
                    "tags": ["architecture", "context", "validation", "spec-driven-development"],
                }
            },
        },
    )
    return {name: f"sha256:{digest}" for name, digest in sorted(digests.items())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--version", default=VERSION)
    parser.add_argument("--publish-catalogs", action="store_true")
    arguments = parser.parse_args()
    digests = build_release(arguments.output, arguments.base_url, arguments.version)
    if arguments.publish_catalogs:
        for name in ("extensions.json", "presets.json", "bundles.json"):
            (REPOSITORY_ROOT / "catalogs").mkdir(exist_ok=True)
            (REPOSITORY_ROOT / "catalogs" / name).write_bytes((arguments.output / name).read_bytes())
    print(json.dumps(digests, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
