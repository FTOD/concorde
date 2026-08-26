#!/usr/bin/env python3
"""Verify Concorde release identity, catalogs, digests, and reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

_BUILDER_PATH = Path(__file__).with_name("build-components.py")
_BUILDER_SPEC = importlib.util.spec_from_file_location("concorde_release_builder", _BUILDER_PATH)
if _BUILDER_SPEC is None or _BUILDER_SPEC.loader is None:
    raise RuntimeError("cannot load release builder")
_BUILDER = importlib.util.module_from_spec(_BUILDER_SPEC)
_BUILDER_SPEC.loader.exec_module(_BUILDER)
VERSION = _BUILDER.VERSION
build_release = _BUILDER.build_release


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_release(dist: Path) -> dict[str, str]:
    dist = dist.resolve()
    expected = {
        "extensions.json": ("extensions", "concorde", f"concorde-{VERSION}.zip"),
        "presets.json": ("presets", "concorde-core", f"concorde-core-{VERSION}.zip"),
        "bundles.json": ("bundles", "concorde-bundle", f"concorde-bundle-{VERSION}.zip"),
    }
    verified: dict[str, str] = {}
    for catalog_name, (collection, identifier, archive_name) in expected.items():
        catalog = json.loads((dist / catalog_name).read_text(encoding="utf-8"))
        entry = catalog[collection][identifier]
        if entry["version"] != VERSION:
            raise ValueError(f"{catalog_name}: version does not match {VERSION}")
        digest = _sha256(dist / archive_name)
        if entry.get("sha256") != f"sha256:{digest}":
            raise ValueError(f"{catalog_name}: digest mismatch for {archive_name}")
        if not (entry["download_url"].startswith("https://") or entry["download_url"].startswith("http://127.0.0.1:")):
            raise ValueError(f"{catalog_name}: release URL must be HTTPS or acceptance localhost")
        with zipfile.ZipFile(dist / archive_name) as archive:
            if any(name.startswith("/") or ".." in Path(name).parts or "\\" in name for name in archive.namelist()):
                raise ValueError(f"{archive_name}: unsafe archive entry")
        verified[archive_name] = f"sha256:{digest}"
    with tempfile.TemporaryDirectory() as temporary:
        sample_catalog = json.loads((dist / "bundles.json").read_text(encoding="utf-8"))
        base_url = sample_catalog["catalog_url"].rsplit("/", 1)[0]
        build_release(Path(temporary), base_url)
        for archive_name in verified:
            if (dist / archive_name).read_bytes() != (Path(temporary) / archive_name).read_bytes():
                raise ValueError(f"{archive_name}: rebuild is not byte-equivalent")
    return verified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    arguments = parser.parse_args()
    print(json.dumps(verify_release(arguments.dist), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
