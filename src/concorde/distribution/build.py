"""The build: render the Protocol bundle and every prompt root into ``generated/``.

Prompts are authored under ``prompts/`` with ``@include`` directives and rendered to plain files
the runtime reads. The build records every source and output digest in
``generated/build-manifest.json`` so a stale render is detected instead of used.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_role_prompt,
)


class BuildError(ValueError):
    """The prompt source tree cannot be rendered deterministically, or is stale."""

    def __init__(self, message: str, code: str = "invalid_build"):
        super().__init__(message)
        self.code = code


PROTOCOL_KINDS = ("module",)
PROTOCOL_MANIFEST_PATH = "protocol/manifest.json"

# Prompt roots rendered one to one: ``prompts/<name>.md`` becomes ``generated/<name>.md``. Every
# file directly in ``prompts/workers/`` and ``prompts/main-session/`` is a root as well.
PROMPT_ROOTS: tuple[str, ...] = (
    "prompts/protocol/principles.md",
    *(f"prompts/protocol/kinds/{kind}.md" for kind in PROTOCOL_KINDS),
)
PROMPT_ROOT_DIRECTORIES: tuple[str, ...] = ("prompts/workers", "prompts/main-session")

# The build owns exactly these locations under `generated/`; `generated/` is a shared, ignored
# root, and check_build never judges locations it does not own.
GENERATED_OWNED_DIRS: tuple[str, ...] = (
    "generated/protocol",
    "generated/workers",
    "generated/main-session",
)


def prompt_roots(project_root: Path) -> tuple[str, ...]:
    """The fixed roots and every Markdown file directly in a root directory, sorted."""
    found = [
        path.relative_to(project_root).as_posix()
        for directory in PROMPT_ROOT_DIRECTORIES
        for path in sorted((project_root / directory).glob("*.md"))
        if path.is_file()
    ]
    return (*PROMPT_ROOTS, *found)


GENERATED_OWNED_FILES: tuple[str, ...] = ("generated/build-manifest.json",)

# Inputs whose change makes every render stale even though no prompt includes them.
EXTRA_SOURCES: tuple[str, ...] = ("concorde.json",)


@dataclass(frozen=True)
class BuildOutput:
    path: str
    content: bytes
    sources: tuple[str, ...]


@dataclass(frozen=True)
class BuildResult:
    outputs: tuple[BuildOutput, ...]
    manifest: bytes


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(project_root: Path, relative: str) -> str:
    return _sha256_bytes((project_root / relative).read_bytes())


def output_path(root: str) -> str:
    """The generated path of a prompt root."""
    return "generated/" + root.removeprefix("prompts/")


def render_prompt(project_root: Path, root: str) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, root)
    except PromptResolverError as error:
        raise BuildError(f"{root}: {error.rule_id}: {error}") from error
    return BuildOutput(
        path=output_path(root),
        content=resolved.body.encode("utf-8"),
        sources=resolved.sources,
    )


def _manifest(project_root: Path, outputs: tuple[BuildOutput, ...]) -> bytes:
    all_sources: set[str] = {
        relative for relative in EXTRA_SOURCES if (project_root / relative).is_file()
    }
    for output in outputs:
        all_sources.update(output.sources)
    sources = {
        relative: _sha256_file(project_root, relative)
        for relative in sorted(all_sources)
    }
    output_entries = {
        output.path: {
            "sha256": _sha256_bytes(output.content),
            "sources": sorted(output.sources),
        }
        for output in outputs
    }
    payload = {"schema_version": 1, "sources": sources, "outputs": output_entries}
    return (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")


def build(project_root: str | Path) -> BuildResult:
    """Render every prompt root; raise BuildError on any failure. Writes nothing."""
    root = Path(project_root)
    roots = prompt_roots(root)
    outputs = [render_prompt(root, item) for item in roots]
    unreachable = find_unreachable_prompts(root, list(roots))
    if unreachable:
        raise BuildError(
            f"unreachable prompt files (no root includes them): {list(unreachable)}"
        )
    ordered = tuple(sorted(outputs, key=lambda item: item.path))
    for output in ordered:
        assert output.path in GENERATED_OWNED_FILES or any(
            output.path.startswith(f"{owned}/") for owned in GENERATED_OWNED_DIRS
        ), f"build output {output.path!r} is outside the build-owned locations"
    return BuildResult(outputs=ordered, manifest=_manifest(root, ordered))


def _checked_output(root: Path, relative: str) -> Path:
    """Reject traversal, symlink ancestors and non-file destinations before mutation."""
    from ..spec.typed_data import checked_path

    try:
        path = checked_path(root, relative)
    except ValueError as error:
        raise BuildError(f"unsafe build output {relative}: {error}") from error
    for parent in path.parents:
        if parent == root:
            break
        if parent.exists() and not parent.is_dir():
            raise BuildError(f"build output ancestor is not a directory: {relative}")
    if path.exists() and not path.is_file():
        raise BuildError(f"build output is not a regular file: {relative}")
    return path


def _recorded_outputs(root: Path) -> dict:
    path = _checked_output(root, "generated/build-manifest.json")
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text())
        if value.get("schema_version") != 1 or not isinstance(
            value.get("outputs"), dict
        ):
            raise ValueError("unsupported build manifest")
        return value["outputs"]
    except (ValueError, AttributeError, OSError) as error:
        raise BuildError(f"invalid previous build manifest: {error}") from error


def _owned_generated_tree(root: Path) -> dict[str, bytes]:
    """Inspect only declared subtrees; reject links rather than following or hiding them."""
    contents = {}
    for directory in GENERATED_OWNED_DIRS:
        owned = root / directory
        _checked_output(root, directory + "/.preflight")
        if owned.exists() and not owned.is_dir():
            raise BuildError(f"build-owned path is not a directory: {directory}")
        for path in sorted(owned.rglob("*")) if owned.is_dir() else ():
            if path.is_symlink():
                raise BuildError(f"unsafe build output symlink: {path}")
            if path.is_file():
                contents[path.relative_to(root).as_posix()] = path.read_bytes()
            elif not path.is_dir():
                raise BuildError(f"unsafe build output: {path}")
    for relative in GENERATED_OWNED_FILES:
        path = _checked_output(root, relative)
        if path.exists():
            contents[relative] = path.read_bytes()
    return contents


def write_build(project_root: str | Path) -> BuildResult:
    """Write only into the named source root after whole-plan safety preflight.

    Installation uses the pure build renderer and its own receipt transaction. There is no
    alternate output root. An owned output the render no longer produces is removed only when
    its bytes match the previous manifest; unknown files, modified bytes and links block before
    any output changes.
    """
    root = Path(project_root)
    result = build(root)
    recorded = _recorded_outputs(root)
    expected = {output.path for output in result.outputs}
    current = _owned_generated_tree(root)
    stale = []
    for relative, content in current.items():
        if relative in expected or relative == "generated/build-manifest.json":
            continue
        if recorded.get(relative, {}).get("sha256") != _sha256_bytes(content):
            raise BuildError(
                f"unowned or modified output the build no longer produces: {relative}"
            )
        stale.append(_checked_output(root, relative))
    targets = [
        (output, _checked_output(root, output.path)) for output in result.outputs
    ]
    for path in stale:
        path.unlink()
        # Prune only this now-empty output ancestry, never unknown neighboring content.
        parent = path.parent
        while (
            parent != root
            and parent != root / "generated"
            and not any(parent.iterdir())
        ):
            parent.rmdir()
            parent = parent.parent
    for output, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output.content)
    manifest = root / "generated/build-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(result.manifest)
    return result


def check_build(project_root: str | Path) -> tuple[bool, tuple[str, ...]]:
    """Compare all owned output/catalog bytes with a pure render, without writing."""
    root = Path(project_root)
    result = build(root)
    fresh = {output.path: output.content for output in result.outputs}
    fresh["generated/build-manifest.json"] = result.manifest
    current = _owned_generated_tree(root)
    diffs = [
        relative
        for relative in set(fresh) | set(current)
        if fresh.get(relative) != current.get(relative)
    ]
    manifest_file = root / PROTOCOL_MANIFEST_PATH
    if manifest_file.is_file() and not manifest_file.is_symlink():
        try:
            assets = json.loads(manifest_file.read_text(encoding="utf-8"))["assets"]
            for item in assets:
                relative = item["path"]
                content = fresh.get(relative)
                if content is None or _sha256_bytes(content) != item.get("digest"):
                    diffs.append(f"{PROTOCOL_MANIFEST_PATH}:{relative}")
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            diffs.append(PROTOCOL_MANIFEST_PATH)
    return (not diffs, tuple(sorted(diffs)))


def recompute_protocol_manifest(project_root: str | Path) -> dict:
    """Recompute {path: sha256} for every tracked Protocol asset from the current build.

    Reads the already-rendered ``generated/protocol/...`` files on disk (call ``verify_fresh``
    first) and the tracked ``protocol/manifest.json``, returning an updated copy with fresh
    digests. Does not write anything.
    """

    root = Path(project_root)
    manifest_path = root / PROTOCOL_MANIFEST_PATH
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BuildError(f"no tracked Protocol manifest at {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildError(f"cannot read {manifest_path}: {error}") from error
    updated = copy.deepcopy(manifest)
    for item in updated.get("assets", []):
        path = root / item["path"]
        if path.is_symlink() or not path.is_file():
            raise BuildError(
                f"Protocol asset is missing from the current build: {item['path']}"
            )
        item["digest"] = _sha256_bytes(path.read_bytes())
    return updated


def verify_fresh(project_root: str | Path) -> None:
    """Fail closed with BuildError(code=stale_build) when sources drifted since the last build.

    This is a cheap freshness check: it reads ``generated/build-manifest.json`` and recomputes the
    sha256 of every recorded source. It never rebuilds or writes anything, and it never compares
    rendered output bytes (``check_build`` does that, more expensively, for CI).
    """

    root = Path(project_root)
    manifest_path = root / "generated/build-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BuildError(
            f"no build found at {root}; run the build before using this package",
            "stale_build",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildError(
            f"cannot read build manifest at {manifest_path}: {error}", "stale_build"
        ) from error
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise BuildError(
            f"build manifest has no recorded sources: {manifest_path}", "stale_build"
        )
    for relative, expected in sources.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise BuildError(
                f"build source is missing since the last build: {relative}",
                "stale_build",
            )
        if _sha256_file(root, relative) != expected:
            raise BuildError(
                f"build source changed since the last build: {relative}", "stale_build"
            )
