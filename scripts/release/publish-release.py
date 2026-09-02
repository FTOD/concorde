#!/usr/bin/env python3
"""Publish a verified standalone Concorde release as immutable GitHub assets."""

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
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_script("build-release.py", "concorde_release_builder")
VERIFIER = _load_script("verify-release.py", "concorde_release_verifier")

REPOSITORY = BUILDER.REPOSITORY
REPOSITORY_SLUG = REPOSITORY.removeprefix("https://github.com/")
EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_DIVERGENT = 2


class PublicationError(Exception):
    def __init__(self, outcome: str, message: str, exit_code: int = EXIT_REJECTED):
        super().__init__(message)
        self.outcome = outcome
        self.exit_code = exit_code


def archive_names(version: str) -> list[str]:
    return [BUILDER.archive_name(version)]


def asset_names(version: str) -> list[str]:
    return [BUILDER.archive_name(version), "release.json"]


def is_prerelease(version: str) -> bool:
    return "-" in version


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def render_notes(version: str, base_url: str, assets: dict[str, str]) -> str:
    name = BUILDER.archive_name(version)
    lines = [
        f"# Concorde {version}",
        "",
        "Standalone Concorde package:",
        "",
        f"- Architecture Profile: `{BUILDER.ARCHITECTURE_PROFILE}`",
        f"- Workspace Protocol: `{BUILDER.WORKSPACE_PROTOCOL}`",
        f"- Archive: `{name}`",
        "",
        "## SHA-256",
        "",
        *[f"- `{asset}`: `{digest}`" for asset, digest in sorted(assets.items())],
        "",
        "## Install",
        "",
        "```bash",
        f'curl -fLO "{base_url}/{name}"',
        f'unzip "{name}"',
        "python3 concorde/scripts/install-concorde.py --checkout concorde --target . --integration codex --apply",
        "```",
        "",
        "The package contains 17 canonical leaf Skills (15 public, 2 internal) and three paired LangGraph Operations; supported agents receive exactly 18 public `concorde-*` projections.",
        "",
    ]
    return "\n".join(lines)


class ReleaseHost(Protocol):
    def view(self, tag: str) -> dict[str, Any] | None: ...
    def create_draft(self, tag: str, notes_file: Path, title: str, prerelease: bool) -> None: ...
    def upload(self, tag: str, path: Path) -> None: ...
    def delete_asset(self, tag: str, name: str) -> None: ...
    def publish(self, tag: str) -> None: ...
    def download(self, tag: str, name: str, directory: Path) -> None: ...


class GhClient:
    def __init__(self, executable: str = "gh", repository: str = REPOSITORY_SLUG):
        self.executable = executable
        self.repository = repository

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [self.executable, *args, "--repo", self.repository], text=True, capture_output=True
        )
        if check and result.returncode:
            raise PublicationError(
                "host-error",
                f"{self.executable} {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}",
            )
        return result

    def view(self, tag: str) -> dict[str, Any] | None:
        result = self._run(
            "release", "view", tag, "--json", "isDraft,isPrerelease,tagName,assets", check=False
        )
        if result.returncode:
            if "not found" in (result.stderr + result.stdout).lower():
                return None
            raise PublicationError("host-error", f"gh release view {tag} failed: {result.stderr.strip()}")
        return json.loads(result.stdout)

    def create_draft(self, tag: str, notes_file: Path, title: str, prerelease: bool) -> None:
        args = [
            "release", "create", tag, "--draft", "--verify-tag", "--title", title,
            "--notes-file", str(notes_file),
        ]
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
    differences: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as temporary:
        downloaded = Path(temporary)
        for name in asset_names(version):
            try:
                host.download(tag, name, downloaded)
            except PublicationError as error:
                differences[name] = f"download failed: {error}"
                continue
            remote = downloaded / name
            if not remote.is_file():
                differences[name] = "missing from published release"
            elif remote.read_bytes() != (dist / name).read_bytes():
                differences[name] = {"published": _sha256(remote), "local": _sha256(dist / name)}
    return {"identical": not differences, "differences": differences}


def publish(
    dist: Path,
    tag: str,
    host: ReleaseHost,
    *,
    dry_run: bool = False,
    compare_only: bool = False,
) -> tuple[dict[str, Any], int]:
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
        identity = BUILDER.read_release_identity()
        version = identity.version
        record["version"] = version
        expected_tag = f"v{version}"
        if tag != expected_tag:
            raise PublicationError(
                "version-mismatch",
                f"tag {tag} does not match concorde.json version {version} (expected {expected_tag})",
            )
        base_url = BUILDER.default_base_url(version)
        record["base_url"] = base_url
        try:
            VERIFIER.verify_release(dist, expect_version=version, expect_base_url=base_url)
        except (ValueError, OSError, KeyError) as error:
            raise PublicationError("verification-failed", f"release verification failed: {error}") from error
        prerelease = is_prerelease(version)
        assets = [dist / name for name in asset_names(version)]
        missing = [path.name for path in assets if not path.is_file()]
        if missing:
            raise PublicationError("verification-failed", f"release assets missing: {', '.join(missing)}")
        digests = {path.name: _sha256(path) for path in assets}
        notes = render_notes(version, base_url, digests)
        record["plan"] = _plan_operations(tag, version, prerelease)
        record["notes"] = notes
        if dry_run:
            record["outcome"] = "dry-run"
            record["message"] = "plan printed; no release-host action was performed"
            return record, EXIT_OK
        existing = host.view(tag)
        if existing is not None and not existing.get("isDraft"):
            compared = compare_with_published(dist, version, tag, host)
            record["compared"] = compared
            if compared["identical"]:
                record["outcome"] = "already-published"
                record["message"] = f"{tag} already contains identical standalone assets"
                return record, EXIT_OK
            raise PublicationError(
                "divergent",
                f"{tag} contains different immutable assets; publish a new version",
                EXIT_DIVERGENT,
            )
        if compare_only:
            record["outcome"] = "draft" if existing is not None else "absent"
            record["message"] = "compare-only performed no mutation"
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
            record["residual_state"] = {"draft": tag, "assets_uploaded": uploaded, "next_run": "repairs the draft"}
            raise PublicationError("publication-failed", str(error)) from error
        record["outcome"] = "published"
        record["message"] = f"{tag} published with {len(assets)} standalone assets"
        return record, EXIT_OK
    except PublicationError as error:
        record["outcome"] = error.outcome
        record["message"] = str(error)
        return record, error.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--compare-only", action="store_true")
    parser.add_argument("--gh", default="gh")
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
    raise SystemExit(main())
