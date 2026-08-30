#!/usr/bin/env python3
"""Verify Concorde release identity, catalogs, digests, locations, and reproducibility."""

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
build_release = _BUILDER.build_release
read_release_identity = _BUILDER.read_release_identity
REPOSITORY = _BUILDER.REPOSITORY

CATALOGS = ("extensions.json", "presets.json", "bundles.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_acceptable_location(url: str) -> bool:
    return url.startswith("https://") or url.startswith("http://127.0.0.1:")


def verify_release(
    dist: Path,
    expect_version: str | None = None,
    expect_base_url: str | None = None,
) -> dict[str, str]:
    """Verify ``dist`` and return archive digests.

    ``expect_version`` must equal the single manifest version; ``expect_base_url`` pins every
    catalog and archive location to the published base. Without ``expect_base_url`` the
    acceptance localhost base remains acceptable.
    """
    dist = dist.resolve()
    identity = read_release_identity()
    version = identity.version
    if expect_version is not None and expect_version != version:
        raise ValueError(f"expected release version {expect_version} but the manifests declare {version}")
    expected = {
        "extensions.json": ("extensions", "concorde", f"concorde-extension-{version}.zip"),
        "presets.json": ("presets", "concorde", f"concorde-preset-{version}.zip"),
        "bundles.json": ("bundles", "concorde-bundle", f"concorde-bundle-{version}.zip"),
    }
    verified: dict[str, str] = {}
    for catalog_name, (collection, identifier, archive_name) in expected.items():
        catalog = json.loads((dist / catalog_name).read_text(encoding="utf-8"))
        entry = catalog[collection][identifier]
        if entry["version"] != version:
            raise ValueError(f"{catalog_name}: version {entry['version']} does not match {version}")
        digest = _sha256(dist / archive_name)
        if entry.get("sha256") != f"sha256:{digest}":
            raise ValueError(f"{catalog_name}: digest mismatch for {archive_name}")
        if entry.get("repository") != REPOSITORY:
            raise ValueError(f"{catalog_name}: repository {entry.get('repository')!r} is not {REPOSITORY}")
        if entry.get("requires", {}).get("speckit_version") != identity.speckit_range:
            raise ValueError(f"{catalog_name}: Spec Kit range does not match {identity.speckit_range}")
        if expect_base_url is not None:
            expected_download = f"{expect_base_url}/{archive_name}"
            expected_catalog = f"{expect_base_url}/{catalog_name}"
            if entry["download_url"] != expected_download:
                raise ValueError(f"{catalog_name}: download_url {entry['download_url']} is not {expected_download}")
            if catalog.get("catalog_url") != expected_catalog:
                raise ValueError(f"{catalog_name}: catalog_url {catalog.get('catalog_url')} is not {expected_catalog}")
        elif not (_is_acceptable_location(entry["download_url"]) and _is_acceptable_location(catalog.get("catalog_url", ""))):
            raise ValueError(f"{catalog_name}: release URLs must be HTTPS or acceptance localhost")
        with zipfile.ZipFile(dist / archive_name) as archive:
            if any(name.startswith("/") or ".." in Path(name).parts or "\\" in name for name in archive.namelist()):
                raise ValueError(f"{archive_name}: unsafe archive entry")
        verified[archive_name] = f"sha256:{digest}"
    with tempfile.TemporaryDirectory() as temporary:
        sample_catalog = json.loads((dist / "bundles.json").read_text(encoding="utf-8"))
        base_url = sample_catalog["catalog_url"].rsplit("/", 1)[0]
        build_release(Path(temporary), base_url)
        for name in list(verified) + list(CATALOGS):
            if (dist / name).read_bytes() != (Path(temporary) / name).read_bytes():
                raise ValueError(f"{name}: rebuild is not byte-equivalent")
    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--expect-version", default=None, help="Version the release must have (for example from the tag)")
    parser.add_argument("--expect-base-url", default=None, help="Published base URL every catalog and archive location must use")
    arguments = parser.parse_args()
    try:
        verified = verify_release(arguments.dist, arguments.expect_version, arguments.expect_base_url)
    except (ValueError, FileNotFoundError, KeyError) as error:
        print(f"error: {error}")
        return 1
    print(json.dumps(verified, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
