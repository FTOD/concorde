#!/usr/bin/env python3
"""Build one deterministic standalone Concorde release archive and pointer."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path
from typing import Iterable, NamedTuple


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "https://github.com/FTOD/concorde"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ARCHITECTURE_PROFILE = 7
WORKSPACE_PROTOCOL = 13


class ReleaseIdentityError(ValueError):
    """The native package manifest is not a releasable identity."""


class ReleaseIdentity(NamedTuple):
    version: str
    repository: str


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseIdentityError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ReleaseIdentityError(f"{path}: expected a JSON object")
    return value


def read_release_identity(root: Path = REPOSITORY_ROOT) -> ReleaseIdentity:
    manifest = _read_json(root / "concorde.json")
    if manifest.get("schema_version") != 2 or manifest.get("name") != "concorde":
        raise ReleaseIdentityError("concorde.json must declare schema_version 2 and name 'concorde'")
    version = manifest.get("version")
    if not isinstance(version, str) or not version or version.startswith("v"):
        raise ReleaseIdentityError("concorde.json version must be an unprefixed release version")
    if manifest.get("repository") != REPOSITORY:
        raise ReleaseIdentityError(
            f"concorde.json repository {manifest.get('repository')!r} does not match {REPOSITORY}"
        )
    if manifest.get("architecture_profile") != ARCHITECTURE_PROFILE:
        raise ReleaseIdentityError(f"concorde.json must declare Architecture Profile {ARCHITECTURE_PROFILE}")
    if manifest.get("workspace_protocol") != WORKSPACE_PROTOCOL:
        raise ReleaseIdentityError(f"concorde.json must declare Workspace Protocol {WORKSPACE_PROTOCOL}")
    return ReleaseIdentity(version, REPOSITORY)


def read_release_version(root: Path = REPOSITORY_ROOT) -> str:
    return read_release_identity(root).version


def default_base_url(version: str, repository: str = REPOSITORY) -> str:
    return f"{repository}/releases/download/v{version}"


def archive_name(version: str) -> str:
    return f"concorde-{version}.zip"


def _included(relative: str) -> bool:
    if relative in {"LICENSE", "README.md", "concorde.json", "scripts/install-concorde.py"}:
        return True
    if relative.startswith(
        ("agent-assets/", "operations/", "skills/", "src/concorde/", "templates/")
    ):
        return Path(relative).suffix in {".json", ".md", ".py", ".tmpl"}
    if relative.startswith("scripts/"):
        return Path(relative).name in {
            "concorde.py",
            "concorde.ps1",
            "concorde.sh",
            "reflections_queue.py",
            "render-capability-surfaces.py",
            "workspace.py",
        }
    return False


def package_files(root: Path = REPOSITORY_ROOT) -> Iterable[Path]:
    candidates = [root / "LICENSE", root / "README.md", root / "concorde.json", root / "scripts/install-concorde.py"]
    for directory in (
        "agent-assets",
        "operations",
        "skills",
        "src/concorde",
        "templates",
        "scripts",
    ):
        candidates.extend(sorted((root / directory).rglob("*")))
    seen: set[str] = set()
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
        if path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in seen or "__pycache__" in Path(relative).parts or path.suffix in {".pyc", ".pyo"}:
            continue
        seen.add(relative)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"release input must be one regular file: {relative}")
        if not _included(relative):
            continue
        yield path


def deterministic_archive(root: Path, destination: Path, version: str) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in package_files(root):
            relative = f"concorde/{path.relative_to(root).as_posix()}"
            info = zipfile.ZipInfo(relative, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = path.parent.name == "scripts" and path.suffix in {".py", ".sh"}
            info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
            info.create_system = 3
            content = path.read_bytes()
            if path.name == "concorde.json":
                manifest = json.loads(content)
                if manifest.get("version") != version:
                    manifest["version"] = version
                    content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
            archive.writestr(info, content)
    return "sha256:" + hashlib.sha256(destination.read_bytes()).hexdigest()


def build_release(
    output: Path,
    base_url: str | None = None,
    version: str | None = None,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, str]:
    identity = read_release_identity(root)
    release_version = version or identity.version
    base_url = (base_url or default_base_url(release_version)).rstrip("/")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = archive_name(release_version)
    digest = deterministic_archive(root, output / name, release_version)
    pointer = {
        "schema_version": 1,
        "name": "concorde",
        "version": release_version,
        "tag": f"v{release_version}",
        "repository": identity.repository,
        "architecture_profile": ARCHITECTURE_PROFILE,
        "workspace_protocol": WORKSPACE_PROTOCOL,
        "archive": {
            "name": name,
            "url": f"{base_url}/{name}",
            "sha256": digest,
        },
        "installer": f"{identity.repository}/blob/v{release_version}/scripts/install-concorde.py",
    }
    (output / "release.json").write_text(
        json.dumps(pointer, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return {name: digest, "release.json": "sha256:" + hashlib.sha256((output / "release.json").read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--base-url")
    parser.add_argument("--print-version", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.print_version:
            print(read_release_version())
            return 0
        print(json.dumps(build_release(arguments.output, arguments.base_url), indent=2, sort_keys=True))
        return 0
    except (ReleaseIdentityError, ValueError, OSError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
