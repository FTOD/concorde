"""Deterministic rendering of prompt-sourced roles and skills (proposal section 8, Stage A).

Stage A renders the role and skill projections from ``prompts/``/``skills/`` sources into
``generated/``. Nothing yet consumes these outputs: the tracked ``.claude/skills/concorde-*``,
``.agents/skills/concorde-*`` and canonical ``operations/``/``roles/`` sources are unaffected. The
build must be byte-identical across repeated runs and must not perform any network or process I/O.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..frontmatter import FrontMatterError, parse_document
from .operation_data import json_schema
from .prompt_resolver import PromptResolverError, find_unreachable_prompts, resolve_role_prompt, resolve_skill_source
from .protocol_contracts import dependencies
from .skill_assets import SkillPrompt, _projection_frontmatter


class BuildError(ValueError):
    """The prompt/skill/role source tree cannot be rendered deterministically."""


INTEGRATIONS = ("claude", "codex")

ROLE_ROOTS: dict[str, str] = {
    "coordinator": "prompts/workflow-host/coordinator.md",
    "reader": "prompts/spec-context/reader.md",
    "spec-author": "prompts/spec-context/spec-author.md",
    "context-assessor": "prompts/spec-context/context-assessor.md",
    "planner": "prompts/workflow-host/planner.md",
    "task-author": "prompts/workflow-host/task-author.md",
    "implementation-worker": "prompts/workflow-host/implementation-worker.md",
    "spec-reviewer": "prompts/workflow-host/spec-reviewer.md",
    "code-reviewer": "prompts/workflow-host/code-reviewer.md",
}

SKILL_NAMES: tuple[str, ...] = (
    "concorde-main",
    "concorde-standard-dev-loop",
    "concorde-fast-loop",
    "concorde-reflections-triage",
    "concorde-init",
    "concorde-configure",
    "concorde-validate",
    "concorde-deliver",
)

SKILL_SOURCES: dict[str, str] = {name: f"skills/{name}/SKILL.md" for name in SKILL_NAMES}

SCHEMA_INTRO = "This complete schema is the invocation's input field. It does not grant project reads.\n"


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


def _skill_metadata(project_root: Path, name: str) -> dict[str, object]:
    relative = SKILL_SOURCES[name]
    path = project_root / relative
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(f"cannot read skill source {relative}: {error}") from error
    try:
        metadata, _ = parse_document(text, relative)
    except FrontMatterError as error:
        raise BuildError(f"invalid skill source front matter in {relative}: {error}") from error
    required = {"name", "description", "capability"}
    if set(metadata) != required:
        raise BuildError(f"skill source {relative} must declare exactly {sorted(required)}, found {sorted(metadata)}")
    if metadata["name"] != name:
        raise BuildError(f"skill source {relative} must declare name: {name}, found {metadata['name']!r}")
    if not isinstance(metadata["description"], str) or not metadata["description"].strip():
        raise BuildError(f"skill source {relative} requires a non-empty description")
    return metadata


def render_role(project_root: Path, role: str) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, ROLE_ROOTS[role])
    except PromptResolverError as error:
        raise BuildError(f"role {role}: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(path=f"generated/roles/{role}.md", content=content, sources=resolved.sources)


def render_skill(project_root: Path, name: str, integration: str) -> BuildOutput:
    if integration not in INTEGRATIONS:
        raise BuildError(f"unsupported integration: {integration}")
    metadata = _skill_metadata(project_root, name)
    try:
        resolved = resolve_skill_source(project_root, SKILL_SOURCES[name])
    except PromptResolverError as error:
        raise BuildError(f"skill {name}: {error.rule_id}: {error}") from error
    launcher = "scripts/run-operation.py"
    operation = f"operations/{name}/operation.py"
    body = resolved.body.replace("{OPERATION}", f"python3 {launcher} {operation}")
    unresolved = [token for token in ("{SCRIPT}", "{FRAMEWORK}", "{OPERATION}") if token in body]
    if unresolved:
        raise BuildError(f"skill {name} contains unresolved package tokens: {unresolved}")
    body = (
        body.rstrip("\n")
        + "\n\n## Input TypedValue schema\n\n"
        + SCHEMA_INTRO
        + "\n```json\n"
        + json.dumps(json_schema(f"{name}-request"), indent=2)
        + "\n```\n"
    )
    prompt = SkillPrompt(
        name=name,
        description=str(metadata["description"]),
        source_path=SKILL_SOURCES[name],
        kind="operation",
        body=body,
        exposure="public",
        operation=operation,
        capabilities=dependencies(name),
    )
    rendered = _projection_frontmatter(prompt, integration) + prompt.body.lstrip()
    content = rendered.encode("utf-8")
    target = f"generated/skills/{integration}/{name}/SKILL.md"
    return BuildOutput(path=target, content=content, sources=(*resolved.sources, SKILL_SOURCES[name]))


def _manifest(project_root: Path, outputs: tuple[BuildOutput, ...]) -> bytes:
    all_sources: set[str] = set()
    for output in outputs:
        all_sources.update(output.sources)
    sources = {relative: _sha256_file(project_root, relative) for relative in sorted(all_sources)}
    output_entries = {
        output.path: {"sha256": _sha256_bytes(output.content), "sources": sorted(output.sources)}
        for output in outputs
    }
    payload = {"schema_version": 1, "sources": sources, "outputs": output_entries}
    return (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")


def build(project_root: str | Path, integration: str = "all") -> BuildResult:
    """Render every role and skill projection; raise BuildError on any resolution failure."""

    root = Path(project_root)
    if integration == "all":
        integrations = INTEGRATIONS
    elif integration in INTEGRATIONS:
        integrations = (integration,)
    else:
        raise BuildError(f"unsupported integration: {integration}")

    outputs: list[BuildOutput] = []
    for role in sorted(ROLE_ROOTS):
        outputs.append(render_role(root, role))
    for name in SKILL_NAMES:
        for one_integration in integrations:
            outputs.append(render_skill(root, name, one_integration))

    roots = list(ROLE_ROOTS.values()) + list(SKILL_SOURCES.values())
    unreachable = find_unreachable_prompts(root, roots)
    if unreachable:
        raise BuildError(f"unreachable prompt files (no root includes them): {list(unreachable)}")

    ordered = tuple(sorted(outputs, key=lambda item: item.path))
    manifest = _manifest(root, ordered)
    return BuildResult(outputs=ordered, manifest=manifest)


def write_build(project_root: str | Path, integration: str = "all") -> BuildResult:
    """Render and write outputs under project_root/generated/."""

    root = Path(project_root)
    result = build(root, integration)
    for output in result.outputs:
        target = root / output.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output.content)
    manifest_path = root / "generated/build-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(result.manifest)
    return result


def _tree(directory: Path) -> dict[str, bytes]:
    if not directory.is_dir():
        return {}
    contents: dict[str, bytes] = {}
    for path in directory.rglob("*"):
        if path.is_file() and not path.is_symlink():
            contents[path.relative_to(directory).as_posix()] = path.read_bytes()
    return contents


def check_build(project_root: str | Path, integration: str = "all") -> tuple[bool, tuple[str, ...]]:
    """Render into a temporary directory and diff against project_root/generated/.

    Returns (is_current, differences) where differences names every relative path (under
    generated/) that is missing, unexpected, or byte-different, including the manifest itself.
    Nothing under project_root is written or modified.
    """

    root = Path(project_root)
    result = build(root, integration)
    with tempfile.TemporaryDirectory(prefix="concorde-build-check-") as raw_temporary:
        temporary = Path(raw_temporary)
        for output in result.outputs:
            target = temporary / output.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(output.content)
        manifest_path = temporary / "generated/build-manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(result.manifest)
        fresh = _tree(temporary / "generated")
    current = _tree(root / "generated")
    diffs = tuple(sorted(relative for relative in set(fresh) | set(current) if fresh.get(relative) != current.get(relative)))
    return (not diffs, diffs)
