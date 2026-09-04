"""Shared docsite package template inventory rule.

Owns the single definition of which bytes under ``docsite/`` travel as the packaged adapter
template — used identically by the installer and the scaffold Tool (``docsite_scaffold``) so a
project always receives exactly the same adapter Concorde runs for its own site.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Iterator, Mapping


TEMPLATE_ROOT = "docsite"
EXCLUDED_DIRECTORIES = ("node_modules", "build", ".generated", ".docusaurus", "coverage", "tests/repository")
EXCLUDED_FILES = ("site.json",)
ALLOWED_SUFFIXES = (".css", ".json", ".md", ".svg", ".ts", ".tsx", ".yml")
SCAFFOLD_ONLY_DIRECTORIES = ("scaffold",)
WORKFLOW_TEMPLATE = "scaffold/deploy-docsite.yml"

_SINGLE_EXCLUDED_NAMES = frozenset(name for name in EXCLUDED_DIRECTORIES if "/" not in name)
_COMPOUND_EXCLUDED_PREFIXES = tuple(tuple(name.split("/")) for name in EXCLUDED_DIRECTORIES if "/" in name)


class DocsiteTemplateError(ValueError):
    """The package docsite template root is missing, unsafe, or disagrees with the manifest."""


def _directory_excluded(parts: tuple[str, ...]) -> bool:
    if any(part in _SINGLE_EXCLUDED_NAMES for part in parts):
        return True
    return any(parts[: len(prefix)] == prefix for prefix in _COMPOUND_EXCLUDED_PREFIXES)


def _walk(directory: Path, parts: tuple[str, ...]) -> Iterator[tuple[tuple[str, ...], Path]]:
    for entry in sorted(directory.iterdir(), key=lambda item: item.name):
        entry_parts = parts + (entry.name,)
        if _directory_excluded(entry_parts):
            # Disposable directories are never inventoried, even when a project links them elsewhere.
            continue
        if entry.is_dir() and not entry.is_symlink():
            yield from _walk(entry, entry_parts)
            continue
        if entry.is_symlink():
            relative = "/".join((TEMPLATE_ROOT, *entry_parts))
            raise DocsiteTemplateError(f"docsite template may not contain a symlink: {relative}")
        if entry.is_file():
            yield entry_parts, entry


def verify_package_root(package_root: Path) -> None:
    """Confirm ``package_root`` declares and safely ships the ``docsite/`` template root."""
    manifest_path = Path(package_root) / "concorde.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise DocsiteTemplateError(f"cannot read package manifest {manifest_path}: file is missing or unsafe")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DocsiteTemplateError(f"cannot read package manifest {manifest_path}: {error}") from error
    if not isinstance(manifest, dict) or TEMPLATE_ROOT not in manifest.get("package_roots", []):
        raise DocsiteTemplateError(f"{manifest_path}: package_roots must include '{TEMPLATE_ROOT}'")
    root = Path(package_root) / TEMPLATE_ROOT
    if root.is_symlink() or not root.is_dir():
        raise DocsiteTemplateError(f"docsite template root is missing or unsafe: {root}")


def template_files(package_root: Path) -> dict[str, bytes]:
    """Sorted package-relative POSIX path -> bytes for every packaged docsite template file."""
    root = Path(package_root) / TEMPLATE_ROOT
    if root.is_symlink() or not root.is_dir():
        raise DocsiteTemplateError(f"docsite template root is missing or unsafe: {root}")
    files: dict[str, bytes] = {}
    for parts, path in _walk(root, ()):
        if len(parts) == 1 and parts[0] in EXCLUDED_FILES:
            continue
        if path.suffix not in ALLOWED_SUFFIXES:
            continue
        package_relative = "/".join((TEMPLATE_ROOT, *parts))
        files[package_relative] = path.read_bytes()
    return dict(sorted(files.items()))


def adapter_files(package_root: Path) -> dict[str, bytes]:
    """``template_files`` minus the scaffold-only entries a scaffold copies into a target project."""
    files = template_files(package_root)
    prefixes = tuple(f"{TEMPLATE_ROOT}/{name}/" for name in SCAFFOLD_ONLY_DIRECTORIES)
    return {path: content for path, content in files.items() if not path.startswith(prefixes)}


def workflow_template(package_root: Path) -> bytes:
    """Bytes of the packaged GitHub Pages deployment workflow template."""
    path = Path(package_root) / TEMPLATE_ROOT / WORKFLOW_TEMPLATE
    if path.is_symlink() or not path.is_file():
        raise DocsiteTemplateError(f"docsite workflow template is missing or unsafe: {path}")
    return path.read_bytes()


def template_digest(files: Mapping[str, bytes]) -> str:
    """Deterministic ``sha256:`` digest over a sorted ``path -> sha256(content)`` manifest."""
    lines = (f"{path}\t{hashlib.sha256(content).hexdigest()}" for path, content in sorted(files.items()))
    text = "\n".join(lines) + "\n"
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
