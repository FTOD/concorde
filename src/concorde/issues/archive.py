"""Explicit, lossless retirement of a legacy queue; never an Issue migration or disposition."""
from pathlib import Path

from ..spec.repository import SpecError
from ..spec.typed_data import checked_path
from .store import _lock


def archive_reflections(root: Path) -> dict:
    source_name, destination_name = ".concorde/reflections", ".concorde/archive/reflections"
    with _lock(root):
        source = checked_path(root, source_name)
        destination = checked_path(root, destination_name)
        if not source.exists():
            return {"status": "unchanged", "archive": destination_name if destination.exists() else None}
        if not source.is_dir() or any(path.is_symlink() for path in source.rglob("*")):
            raise SpecError("legacy archive source must be a real directory without symlinks", "unsafe_path")
        if destination.exists():
            raise SpecError("archive destination already exists; neither copy was changed", "invalid_input")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        return {"status": "archived", "archive": destination_name}
