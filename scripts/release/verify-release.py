#!/usr/bin/env python3
"""Verify a standalone Concorde release for identity, safety, installation, and reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


BUILDER_PATH = Path(__file__).with_name("build-release.py")
BUILDER_SPEC = importlib.util.spec_from_file_location("concorde_release_builder", BUILDER_PATH)
if BUILDER_SPEC is None or BUILDER_SPEC.loader is None:
    raise RuntimeError("cannot load release builder")
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
sys.modules[BUILDER_SPEC.name] = BUILDER
BUILDER_SPEC.loader.exec_module(BUILDER)

ARCHITECTURE_PROFILE = BUILDER.ARCHITECTURE_PROFILE
WORKSPACE_PROTOCOL = BUILDER.WORKSPACE_PROTOCOL
REPOSITORY = BUILDER.REPOSITORY
EXPECTED_SKILLS = BUILDER.EXPECTED_SKILLS
EXPECTED_OPERATIONS = BUILDER.EXPECTED_OPERATIONS
archive_name = BUILDER.archive_name
build_release = BUILDER.build_release
read_release_identity = BUILDER.read_release_identity


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_member(name: str) -> bool:
    candidate = PurePosixPath(name)
    return (
        bool(name)
        and not candidate.is_absolute()
        and ".." not in candidate.parts
        and "\\" not in name
        and candidate.parts[0] == "concorde"
    )


def verify_release(
    dist: Path,
    expect_version: str | None = None,
    expect_base_url: str | None = None,
) -> dict[str, str]:
    dist = dist.resolve()
    identity = read_release_identity()
    version = identity.version
    if expect_version is not None and expect_version != version:
        raise ValueError(f"expected release version {expect_version} but concorde.json declares {version}")
    pointer = json.loads((dist / "release.json").read_text(encoding="utf-8"))
    if not isinstance(pointer, dict) or pointer.get("schema_version") != 1:
        raise ValueError("release.json must use schema_version 1")
    expected_name = archive_name(version)
    expected_url = f"{expect_base_url.rstrip('/')}/{expected_name}" if expect_base_url else pointer.get("archive", {}).get("url")
    expected = {
        "name": "concorde",
        "version": version,
        "tag": f"v{version}",
        "repository": REPOSITORY,
        "architecture_profile": ARCHITECTURE_PROFILE,
        "workspace_protocol": WORKSPACE_PROTOCOL,
    }
    for field, value in expected.items():
        if pointer.get(field) != value:
            raise ValueError(f"release.json {field} {pointer.get(field)!r} does not match {value!r}")
    archive = pointer.get("archive")
    if not isinstance(archive, dict) or archive.get("name") != expected_name:
        raise ValueError(f"release.json must name {expected_name}")
    if archive.get("url") != expected_url:
        raise ValueError(f"release.json archive URL {archive.get('url')!r} does not match {expected_url!r}")
    archive_path = dist / expected_name
    digest = _digest(archive_path)
    if archive.get("sha256") != digest:
        raise ValueError(f"release.json digest does not match {expected_name}")
    with zipfile.ZipFile(archive_path) as package:
        names = package.namelist()
        if len(names) != len(set(names)) or any(not _safe_member(name) for name in names):
            raise ValueError(f"{expected_name} contains duplicate or unsafe members")
        required = {
            "concorde/concorde.json",
            "concorde/LICENSE",
            "concorde/scripts/install-concorde.py",
            "concorde/scripts/concorde.py",
            "concorde/src/concorde/cli.py",
            "concorde/templates/feature-template.md",
            "concorde/skills/concorde-specify/SKILL.md",
            "concorde/operations/concorde-standard-dev-loop/SKILL.md",
            "concorde/operations/concorde-standard-dev-loop/operation.py",
            "concorde/operations/concorde-reflections-triage/SKILL.md",
            "concorde/operations/concorde-reflections-triage/operation.py",
            "concorde/operations/concorde-plan/SKILL.md",
            "concorde/operations/concorde-plan/operation.py",
            "concorde/skills/concorde-plan-context/SKILL.md",
            "concorde/skills/concorde-plan-author/SKILL.md",
        }
        missing = required - set(names)
        if missing:
            raise ValueError(f"{expected_name} is missing package members: {sorted(missing)}")
        if any(
            "/.specify/" in f"/{name}"
            or name.startswith("concorde/presets/")
            or name.startswith("concorde/extensions/")
            or name.startswith("concorde/bundles/")
            or name.startswith("concorde/commands/")
            or name.startswith("concorde/examples/")
            for name in names
        ):
            raise ValueError(f"{expected_name} contains removed host-package layout")
        manifest = json.loads(package.read("concorde/concorde.json"))
        if manifest.get("version") != version:
            raise ValueError(f"{expected_name} package manifest version does not match {version}")
        if tuple(manifest.get("skills", ())) != EXPECTED_SKILLS:
            raise ValueError(f"{expected_name} must contain the exact 17-leaf inventory")
        if tuple(manifest.get("operations", ())) != EXPECTED_OPERATIONS:
            raise ValueError(f"{expected_name} must contain the exact three-Operation inventory")
        skill_names = sorted(
            PurePosixPath(name).parts[2]
            for name in names
            if name.startswith("concorde/skills/") and name.endswith("/SKILL.md")
        )
        operation_members = {
            operation: {
                PurePosixPath(name).name
                for name in names
                if name.startswith(f"concorde/operations/{operation}/")
            }
            for operation in manifest.get("operations", [])
        }
        if skill_names != sorted(manifest.get("skills", [])):
            raise ValueError(f"{expected_name} Skill inventory differs from concorde.json")
        if any(members != {"SKILL.md", "operation.py"} for members in operation_members.values()):
            raise ValueError(f"{expected_name} must retain every exact Operation pair")
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        extracted = temporary_root / "extracted"
        target = temporary_root / "target"
        with zipfile.ZipFile(archive_path) as package:
            package.extractall(extracted)
        installer = extracted / "concorde/scripts/install-concorde.py"
        result = subprocess.run(
            [
                sys.executable,
                str(installer),
                "--target",
                str(target),
                "--checkout",
                str(extracted / "concorde"),
                "--integration",
                "codex",
                "--apply",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise ValueError(f"release installation failed: {result.stderr or result.stdout}")
        installation = json.loads(result.stdout)
        if installation.get("status") != "installed" or not (target / ".concorde/install.json").is_file():
            raise ValueError("release installation did not produce a native owned installation")
        rebuilt = temporary_root / "rebuilt"
        base_url = str(archive.get("url")).rsplit("/", 1)[0]
        build_release(rebuilt, base_url)
        for name in (expected_name, "release.json"):
            if (dist / name).read_bytes() != (rebuilt / name).read_bytes():
                raise ValueError(f"{name}: rebuild is not byte-equivalent")
    return {expected_name: digest, "release.json": _digest(dist / "release.json")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--expect-version")
    parser.add_argument("--expect-base-url")
    arguments = parser.parse_args()
    try:
        verified = verify_release(arguments.dist, arguments.expect_version, arguments.expect_base_url)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"error: {error}")
        return 1
    print(json.dumps(verified, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
