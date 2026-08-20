"""Safe deterministic discovery for a Concorde specification hierarchy."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from .diagnostics import digest_sources
from .frontmatter import FrontMatterError, parse_document
from .model import ArchitecturePackage, SourceDocument


class RepositoryError(ValueError):
    pass


def safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RepositoryError("path must be a non-empty project-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RepositoryError(f"unsafe project-relative path: {value}")
    if len(path.parts[0]) >= 2 and path.parts[0][1] == ":":
        raise RepositoryError(f"absolute drive path is not permitted: {value}")
    return path.as_posix()


class ProjectRepository:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()

    def resolve(self, relative: str) -> Path:
        safe = safe_relative_path(relative)
        candidate = (self.project_root / safe).resolve(strict=False)
        try:
            candidate.relative_to(self.project_root)
        except ValueError as error:
            raise RepositoryError(f"path escapes project root: {relative}") from error
        return candidate

    def load_config(self) -> dict[str, Any]:
        path = self.resolve(".concorde/config.json")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RepositoryError(f"cannot read .concorde/config.json: {error}") from error
        if value.get("profile_version") != 1:
            raise RepositoryError("unsupported Concorde source profile; expected profile_version 1")
        specification_root = value.get("specification_root")
        if not specification_root and value.get("architecture_root"):
            specification_root = value["architecture_root"]
        value["specification_root"] = safe_relative_path(specification_root)
        if not isinstance(value.get("root_module_id"), str) or not value["root_module_id"]:
            raise RepositoryError("root_module_id is required")
        return value

    def _markdown_paths(self, specification_root: str) -> list[Path]:
        root = self.resolve(specification_root)
        if not root.is_dir():
            raise RepositoryError(f"specification root does not exist: {specification_root}")
        candidates = set(root.rglob("module.md"))
        candidates.update(root.glob("**/contracts/**/contract.md"))
        candidates.update(root.glob("**/features/*/spec.md"))
        return sorted(candidates, key=lambda item: item.relative_to(self.project_root).as_posix())

    def load(self) -> ArchitecturePackage:
        config = self.load_config()
        specification_root = config["specification_root"]
        sources: list[SourceDocument] = []
        view_paths: set[str] = set()
        for path in self._markdown_paths(specification_root):
            relative = path.relative_to(self.project_root).as_posix()
            try:
                metadata, body = parse_document(path.read_text(encoding="utf-8"), relative)
            except (OSError, UnicodeError, FrontMatterError) as error:
                raise RepositoryError(str(error)) from error
            kind = metadata.get("kind")
            identifier = metadata.get("id")
            if kind not in {"module", "feature", "contract", "scenario"}:
                raise RepositoryError(f"{relative}: unsupported or missing kind")
            if not isinstance(identifier, str) or not identifier:
                raise RepositoryError(f"{relative}: missing stable id")
            sources.append(SourceDocument(relative, kind, identifier, metadata, body))
            for key in ("view", "architecture_view"):
                value = metadata.get(key)
                if isinstance(value, str) and value:
                    view_paths.add(safe_relative_path(value))
        views: dict[str, Any] = {}
        for relative in sorted(view_paths):
            path = self.resolve(relative)
            try:
                views[relative] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RepositoryError(f"{relative}: invalid architecture JSON: {error}") from error
        by_id: dict[str, list[SourceDocument]] = defaultdict(list)
        for source in sources:
            by_id[source.identifier].append(source)
        artifacts = [source.path for source in sources] + list(views)
        return ArchitecturePackage(
            project_root=self.project_root,
            specification_root=specification_root,
            root_module_id=config["root_module_id"],
            profile_version=config["profile_version"],
            sources=tuple(sources),
            views=views,
            by_id={key: tuple(value) for key, value in sorted(by_id.items())},
            source_digest=digest_sources(self.project_root, artifacts),
        )

    def stage_and_promote(self, files: dict[str, str]) -> list[str]:
        """Write a complete set atomically enough for project-local source initialization."""
        resolved = {safe_relative_path(path): self.resolve(path) for path in files}
        conflicts = [path for path, target in resolved.items() if target.exists()]
        if conflicts:
            raise RepositoryError("target files already exist: " + ", ".join(sorted(conflicts)))
        staged: list[tuple[Path, Path]] = []
        promoted: list[Path] = []
        try:
            for relative, target in sorted(resolved.items()):
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(f".{target.name}.concorde-stage")
                temporary.write_text(files[relative], encoding="utf-8", newline="\n")
                staged.append((temporary, target))
            for temporary, target in staged:
                temporary.replace(target)
                promoted.append(target)
        except OSError:
            for temporary, _ in staged:
                temporary.unlink(missing_ok=True)
            for target in reversed(promoted):
                target.unlink(missing_ok=True)
            raise
        return sorted(resolved)
