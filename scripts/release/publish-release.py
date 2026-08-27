#!/usr/bin/env python3
"""Publish a verified Concorde release as immutable GitHub release assets.

Decision table (see the publish-release sub-feature data model):

    tag != manifest version        -> version-mismatch     (exit 1, nothing touched)
    verification fails             -> verification-failed  (exit 1, nothing touched)
    release absent                 -> create draft, upload 7 assets, publish (exit 0)
    leftover draft                 -> delete draft assets, upload, publish   (exit 0)
    published and identical        -> already-published    (exit 0, no-op)
    published and different        -> divergent            (exit 2, refused)

The publisher never passes ``--clobber``: a published asset is never replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Protocol


def _load_script(name: str, module_name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BUILDER = _load_script("build-components.py", "concorde_release_builder")
_VERIFIER = _load_script("verify-release.py", "concorde_release_verifier")

REPOSITORY = _BUILDER.REPOSITORY
REPOSITORY_SLUG = REPOSITORY.removeprefix("https://github.com/")
CATALOGS = ("extensions.json", "presets.json", "bundles.json")
POINTER = "release.json"
BUNDLE_ID = "concorde-bundle"
POINTER_SCHEMA_VERSION = "1.0"

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_DIVERGENT = 2

_CATALOG_ENTRIES = {
    "extensions.json": ("extensions", "concorde"),
    "presets.json": ("presets", "concorde-core"),
    "bundles.json": ("bundles", "concorde-bundle"),
}


class PublicationError(Exception):
    def __init__(self, outcome: str, message: str, exit_code: int = EXIT_REJECTED):
        super().__init__(message)
        self.outcome = outcome
        self.exit_code = exit_code


def archive_names(version: str) -> list[str]:
    return [f"concorde-core-{version}.zip", f"concorde-{version}.zip", f"concorde-bundle-{version}.zip"]


def asset_names(version: str) -> list[str]:
    return archive_names(version) + list(CATALOGS) + [POINTER]


def is_prerelease(version: str) -> bool:
    return "-" in version


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_release_pointer(
    dist: Path,
    version: str,
    tag: str,
    base_url: str,
    speckit_range: str,
    prerelease: bool = False,
) -> dict[str, Any]:
    """Write ``dist/release.json`` per ``contracts/release-publication.md`` and return it."""
    pointer: dict[str, Any] = {
        "schema_version": POINTER_SCHEMA_VERSION,
        "version": version,
        "tag": tag,
        "repository": REPOSITORY,
        "base_url": base_url,
        "speckit_version": speckit_range,
        "bundle_id": BUNDLE_ID,
        "catalogs": {
            "extensions": f"{base_url}/extensions.json",
            "presets": f"{base_url}/presets.json",
            "bundles": f"{base_url}/bundles.json",
        },
        "archives": {name: _sha256(dist / name) for name in archive_names(version)},
    }
    if prerelease:
        pointer["prerelease"] = True
    (dist / POINTER).write_text(json.dumps(pointer, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return pointer


def render_notes(version: str, speckit_range: str, base_url: str, archives: dict[str, str]) -> str:
    lines = [
        f"# Concorde {version}",
        "",
        "Pinned Spec Kit component set for this release:",
        "",
        "| Component | Kind | Version |",
        "|---|---|---|",
        f"| `concorde-bundle` | bundle | `concorde-bundle@{version}` |",
        f"| `concorde-core` | preset | `concorde-core@{version}` |",
        f"| `concorde` | extension | `concorde@{version}` |",
        "",
        f"Supported Spec Kit range: `{speckit_range}`",
        "",
        "## Archive digests",
        "",
        "| Archive | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(f"| `{name}` | `{digest}` |" for name, digest in sorted(archives.items()))
    lines.extend(
        [
            "",
            "## Install into a Spec Kit project",
            "",
            "```bash",
            f'specify extension catalog add "{base_url}/extensions.json" --name concorde --install-allowed',
            f'specify preset catalog add "{base_url}/presets.json" --name concorde --install-allowed',
            f'specify bundle catalog add "{base_url}/bundles.json" --id concorde',
            f"specify bundle install {BUNDLE_ID}",
            "```",
            "",
            f"Current-release pointer: `{REPOSITORY}/releases/latest/download/{POINTER}`",
            "",
            f"Quick start: {REPOSITORY}/blob/{'v' + version}/docs/quick-start.md",
            "",
        ]
    )
    return "\n".join(lines)


class ReleaseHost(Protocol):
    def view(self, tag: str) -> dict[str, Any] | None: ...
    def create_draft(self, tag: str, notes_file: Path, title: str, prerelease: bool) -> None: ...
    def upload(self, tag: str, path: Path) -> None: ...
    def delete_asset(self, tag: str, name: str) -> None: ...
    def publish(self, tag: str) -> None: ...
    def download(self, tag: str, name: str, directory: Path) -> None: ...


class GhClient:
    """Thin wrapper over the GitHub CLI; every method is one ``gh release`` call."""

    def __init__(self, executable: str = "gh", repository: str = REPOSITORY_SLUG):
        self.executable = executable
        self.repository = repository

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [self.executable, *args, "--repo", self.repository],
            text=True,
            capture_output=True,
        )
        if check and result.returncode:
            raise PublicationError(
                "host-error",
                f"{self.executable} {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}",
            )
        return result

    def view(self, tag: str) -> dict[str, Any] | None:
        result = self._run("release", "view", tag, "--json", "isDraft,isPrerelease,tagName,assets", check=False)
        if result.returncode:
            if "not found" in (result.stderr + result.stdout).lower():
                return None
            raise PublicationError("host-error", f"gh release view {tag} failed: {result.stderr.strip()}")
        return json.loads(result.stdout)

    def create_draft(self, tag: str, notes_file: Path, title: str, prerelease: bool) -> None:
        args = ["release", "create", tag, "--draft", "--verify-tag", "--title", title, "--notes-file", str(notes_file)]
        if prerelease:
            args.append("--prerelease")
        self._run(*args)

    def upload(self, tag: str, path: Path) -> None:
        self._run("release", "upload", tag, str(path))

    def delete_asset(self, tag: str, name: str) -> None:
        self._run("release", "delete-asset", tag, name, "--yes")

    def publish(self, tag: str) -> None:
        self._run("release", "edit", tag, "--draft=false")

    def download(self, tag: str, name: str, directory: Path) -> None:
        self._run("release", "download", tag, "--pattern", name, "--dir", str(directory))


def _plan_operations(tag: str, version: str, prerelease: bool) -> list[str]:
    create = f"gh release create {tag} --draft --verify-tag" + (" --prerelease" if prerelease else "")
    return [create, *[f"gh release upload {tag} {name}" for name in asset_names(version)], f"gh release edit {tag} --draft=false"]


def compare_with_published(dist: Path, version: str, tag: str, host: ReleaseHost) -> dict[str, Any]:
    """Compare the published catalogs and pointer with the local ``dist``; never mutates."""
    differences: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as temporary:
        downloaded = Path(temporary)
        for name in list(CATALOGS) + [POINTER]:
            try:
                host.download(tag, name, downloaded)
            except PublicationError as error:
                differences[name] = f"download failed: {error}"
                continue
            remote_path = downloaded / name
            if not remote_path.is_file():
                differences[name] = "missing from the published release"
                continue
            local = json.loads((dist / name).read_text(encoding="utf-8"))
            remote = json.loads(remote_path.read_text(encoding="utf-8"))
            if name == POINTER:
                fields = {"version": None, "base_url": None, "archives": None}
                changed = {field: {"published": remote.get(field), "local": local.get(field)} for field in fields if remote.get(field) != local.get(field)}
            else:
                collection, identifier = _CATALOG_ENTRIES[name]
                local_entry = local[collection][identifier]
                remote_entry = remote.get(collection, {}).get(identifier, {})
                changed = {}
                if remote.get("catalog_url") != local.get("catalog_url"):
                    changed["catalog_url"] = {"published": remote.get("catalog_url"), "local": local.get("catalog_url")}
                for field in ("version", "download_url", "sha256"):
                    if remote_entry.get(field) != local_entry.get(field):
                        changed[field] = {"published": remote_entry.get(field), "local": local_entry.get(field)}
            if changed:
                differences[name] = changed
    return {"identical": not differences, "differences": differences}


def publish(
    dist: Path,
    tag: str,
    host: ReleaseHost,
    *,
    dry_run: bool = False,
    compare_only: bool = False,
) -> tuple[dict[str, Any], int]:
    """Run the decision table and return the Publication Record with its exit code."""
    dist = dist.resolve()
    record: dict[str, Any] = {
        "outcome": None,
        "tag": tag,
        "version": None,
        "base_url": None,
        "plan": [],
        "compared": None,
        "residual_state": None,
        "message": None,
    }
    try:
        identity = _BUILDER.read_release_identity()
        version = identity.version
        record["version"] = version
        expected_tag = f"v{version}"
        if tag != expected_tag:
            raise PublicationError(
                "version-mismatch",
                f"tag {tag} does not match the manifest release version {version} (expected tag {expected_tag}); "
                f"bump {_BUILDER.BUNDLE_MANIFEST} and the component manifests together before tagging",
            )
        base_url = _BUILDER.default_base_url(version)
        record["base_url"] = base_url
        try:
            _VERIFIER.verify_release(dist, expect_version=version, expect_base_url=base_url)
        except (ValueError, FileNotFoundError, KeyError) as error:
            raise PublicationError("verification-failed", f"release verification failed: {error}") from error

        prerelease = is_prerelease(version)
        build_release_pointer(dist, version, tag, base_url, identity.speckit_range, prerelease)
        archives = {name: _sha256(dist / name) for name in archive_names(version)}
        notes = render_notes(version, identity.speckit_range, base_url, archives)
        record["plan"] = _plan_operations(tag, version, prerelease)
        record["notes"] = notes
        assets = [dist / name for name in asset_names(version)]
        missing = [path.name for path in assets if not path.is_file()]
        if missing:
            raise PublicationError("verification-failed", f"release assets missing from {dist}: {', '.join(missing)}")

        if dry_run:
            record["outcome"] = "dry-run"
            record["message"] = "plan printed; no release host operation was performed"
            return record, EXIT_OK

        existing = host.view(tag)
        if existing is not None and not existing.get("isDraft"):
            compared = compare_with_published(dist, version, tag, host)
            record["compared"] = compared
            if compared["identical"]:
                record["outcome"] = "already-published"
                record["message"] = f"{tag} is already published with identical catalogs and digests; nothing changed"
                return record, EXIT_OK
            raise PublicationError(
                "divergent",
                f"{tag} is already published with different content ({', '.join(sorted(compared['differences']))}); "
                "refusing to overwrite a published release — publish a new version instead",
                EXIT_DIVERGENT,
            )
        if compare_only:
            record["outcome"] = "draft" if existing is not None else "absent"
            record["message"] = f"{tag} is {record['outcome']}; compare-only performed no mutation"
            return record, EXIT_OK

        uploaded: list[str] = []
        try:
            if existing is None:
                with tempfile.TemporaryDirectory() as temporary:
                    notes_file = Path(temporary) / "notes.md"
                    notes_file.write_text(notes, encoding="utf-8")
                    host.create_draft(tag, notes_file, f"Concorde {version}", prerelease)
            else:
                for asset in existing.get("assets", []) or []:
                    host.delete_asset(tag, asset["name"])
            for path in assets:
                host.upload(tag, path)
                uploaded.append(path.name)
            host.publish(tag)
        except PublicationError as error:
            record["residual_state"] = {"draft": tag, "assets_uploaded": uploaded, "next_run": "repairs the draft and publishes"}
            raise PublicationError("publication-failed", str(error)) from error
        record["outcome"] = "published"
        record["message"] = f"{tag} published with {len(assets)} assets at {base_url}"
        return record, EXIT_OK
    except PublicationError as error:
        record["outcome"] = error.outcome
        record["message"] = str(error)
        return record, error.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag", required=True, help="Release tag, must equal v<manifest version>")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan; perform no release host operation")
    parser.add_argument("--compare-only", action="store_true", help="Compare with a published release; never mutate")
    parser.add_argument("--gh", default="gh", help="GitHub CLI executable")
    arguments = parser.parse_args(argv)
    record, code = publish(
        arguments.dist,
        arguments.tag,
        GhClient(arguments.gh),
        dry_run=arguments.dry_run,
        compare_only=arguments.compare_only,
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
