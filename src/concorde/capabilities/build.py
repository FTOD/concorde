"""Deterministic rendering of prompt-sourced roles and skills (proposal section 8).

The build renders the role and skill projections from ``prompts/``/``skills/`` sources into
``generated/`` and, for skills, directly into ``.claude/skills/<name>/SKILL.md`` and
``.agents/skills/<name>/SKILL.md``. After Stage B1 these rendered files are the only instruction
source the host and the agent runtimes consume: ``run_operation`` and ``load_role_prompt`` verify
build freshness before using them and fail closed with ``BuildError(code="stale_build")`` when the
recorded sources have drifted. The build must be byte-identical across repeated runs and must not
perform any network or process I/O.
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
from .roles import ROLES, role_key
from .skill_assets import SkillPrompt


class BuildError(ValueError):
    """The prompt/skill/role source tree cannot be rendered deterministically, or is stale."""

    def __init__(self, message: str, code: str = "invalid_build"):
        super().__init__(message)
        self.code = code


INTEGRATIONS = ("claude", "codex")
INTEGRATION_ROOTS = {"claude": ".claude/skills", "codex": ".agents/skills"}

ROLE_ROOTS: dict[str, str] = {
    role.name.replace("_", "-"): role.prompt for role in ROLES.values()
}

SKILL_NAMES: tuple[str, ...] = (
    "concorde-main",
    "concorde-dev-loop",
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
    if not isinstance(metadata["capability"], str) or not metadata["capability"].strip():
        raise BuildError(f"skill source {relative} requires a non-empty capability")
    return metadata


def render_role(project_root: Path, role: str) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, ROLE_ROOTS[role])
    except PromptResolverError as error:
        raise BuildError(f"role {role}: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(path=f"generated/roles/{role}.md", content=content, sources=resolved.sources)


def _skill_frontmatter(name: str, description: str, integration: str, capability: str) -> str:
    values = ["---", f"name: {name}", f"description: {json.dumps(description)}"]
    if integration == "claude":
        values.append('argument-hint: "Optional capability guidance"')
    values.extend(
        [
            'compatibility: "Requires a Concorde project"',
            "metadata:",
            '  author: "concorde"',
            f"  source: {json.dumps(SKILL_SOURCES[name])}",
            '  kind: "skill"',
            f"  capability: {json.dumps(capability)}",
        ]
    )
    if integration == "claude":
        values.extend(["user-invocable: true", "disable-model-invocation: false"])
    values.extend(["---", ""])
    return "\n".join(values)


def render_skill(project_root: Path, name: str, integration: str, *, framework_prefix: str = "") -> BuildOutput:
    if integration not in INTEGRATIONS:
        raise BuildError(f"unsupported integration: {integration}")
    metadata = _skill_metadata(project_root, name)
    try:
        resolved = resolve_skill_source(project_root, SKILL_SOURCES[name])
    except PromptResolverError as error:
        raise BuildError(f"skill {name}: {error.rule_id}: {error}") from error
    prefix = framework_prefix.strip("/")
    launcher = f"{prefix}/scripts/run-capability.py" if prefix else "scripts/run-capability.py"
    body = resolved.body.replace("{OPERATION}", f"python3 {launcher} {name}")
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
    frontmatter = _skill_frontmatter(name, str(metadata["description"]), integration, str(metadata["capability"]))
    content = (frontmatter + body.lstrip()).encode("utf-8")
    target = f"{INTEGRATION_ROOTS[integration]}/{name}/SKILL.md"
    return BuildOutput(path=target, content=content, sources=(*resolved.sources, SKILL_SOURCES[name]))


def render_langgraph(project_root: Path) -> BuildOutput:
    """Studio graph list derived from ``skills/`` (proposal section 8, item 6)."""

    graphs = {name: f"./scripts/development/studio.py:{name.replace('-', '_')}" for name in SKILL_NAMES}
    payload = {
        "$schema": "https://langgra.ph/schema.json",
        "dependencies": ["."],
        "graphs": graphs,
        "env": {"LANGSMITH_TRACING": "false"},
    }
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(path="generated/langgraph.json", content=content, sources=tuple(sorted(SKILL_SOURCES.values())))


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


def build(project_root: str | Path, integration: str = "all", *, framework_prefix: str = "") -> BuildResult:
    """Render every role, skill and Studio-graph projection; raise BuildError on any failure."""

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
            outputs.append(render_skill(root, name, one_integration, framework_prefix=framework_prefix))
    outputs.append(render_langgraph(root))

    roots = list(ROLE_ROOTS.values()) + list(SKILL_SOURCES.values())
    unreachable = find_unreachable_prompts(root, roots)
    if unreachable:
        raise BuildError(f"unreachable prompt files (no root includes them): {list(unreachable)}")

    ordered = tuple(sorted(outputs, key=lambda item: item.path))
    manifest = _manifest(root, ordered)
    return BuildResult(outputs=ordered, manifest=manifest)


def write_build(
    project_root: str | Path,
    integration: str = "all",
    *,
    framework_prefix: str = "",
    integration_root: str | Path | None = None,
) -> BuildResult:
    """Render and write outputs.

    Outputs under ``generated/`` are always written below ``project_root`` (the location that
    owns the recorded build manifest). Rendered skill wrappers (``.claude/skills/*``,
    ``.agents/skills/*``) are written below ``integration_root`` when given, so an installer can
    render a consumer's framework sources while placing the consumer-facing Skill wrappers at the
    consumer's own project root.
    """

    root = Path(project_root)
    destination = Path(integration_root) if integration_root is not None else root
    result = build(root, integration, framework_prefix=framework_prefix)
    for output in result.outputs:
        base = destination if output.path.startswith((".claude/skills/", ".agents/skills/")) else root
        target = base / output.path
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
    """Render into a temporary directory and diff against every project_root output location.

    Returns (is_current, differences) where differences names every relative path (under
    ``generated/`` and, for our own seven skills, ``.claude/skills``/``.agents/skills``) that is
    missing, unexpected, or byte-different. Nothing under project_root is written or modified. A
    third party's own Skill directories (for example ``.claude/skills/archify``) are never
    inspected or reported.
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
        fresh_generated = _tree(temporary / "generated")
    current_generated = _tree(root / "generated")
    diffs = [
        f"generated/{relative}"
        for relative in set(fresh_generated) | set(current_generated)
        if fresh_generated.get(relative) != current_generated.get(relative)
    ]
    for prefix in INTEGRATION_ROOTS.values():
        for name in SKILL_NAMES:
            fresh_key = f"{prefix}/{name}"
            fresh_contents = {}
            for output in result.outputs:
                if output.path.startswith(f"{fresh_key}/"):
                    fresh_contents[output.path[len(fresh_key) + 1 :]] = output.content
            current_contents = _tree(root / prefix / name)
            for relative in set(fresh_contents) | set(current_contents):
                if fresh_contents.get(relative) != current_contents.get(relative):
                    diffs.append(f"{fresh_key}/{relative}")
    return (not diffs, tuple(sorted(diffs)))


def verify_fresh(project_root: str | Path) -> None:
    """Fail closed with BuildError(code=stale_build) when sources drifted since the last build.

    This is a cheap freshness check: it reads ``generated/build-manifest.json`` and recomputes the
    sha256 of every recorded source. It never rebuilds or writes anything, and it never compares
    rendered output bytes (``check_build`` does that, more expensively, for CI).
    """

    root = Path(project_root)
    manifest_path = root / "generated/build-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BuildError(f"no build found at {root}; run the build before using this package", "stale_build")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildError(f"cannot read build manifest at {manifest_path}: {error}", "stale_build") from error
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise BuildError(f"build manifest has no recorded sources: {manifest_path}", "stale_build")
    for relative, expected in sources.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise BuildError(f"build source is missing since the last build: {relative}", "stale_build")
        if _sha256_file(root, relative) != expected:
            raise BuildError(f"build source changed since the last build: {relative}", "stale_build")


def load_role_prompt(package_root: str | Path, role_name: str) -> SkillPrompt:
    """Load one role's rendered instructions from the build; verifies freshness first.

    ``role_name`` accepts either the external ``concorde-<hyphenated>`` identity used throughout
    the host (for example ``concorde-spec-author``) or the bare hyphenated/underscored role key.
    """

    verify_fresh(package_root)
    key = role_key(role_name)
    role = ROLES.get(key)
    if role is None:
        raise BuildError(f"unknown role: {role_name!r}", "unknown_role")
    root = Path(package_root)
    hyphenated = role.name.replace("_", "-")
    path = root / "generated/roles" / f"{hyphenated}.md"
    if path.is_symlink() or not path.is_file():
        raise BuildError(f"no build found at {root}; run the build before using this package", "stale_build")
    try:
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(f"cannot read rendered role {path}: {error}", "stale_build") from error
    return SkillPrompt(
        name=f"concorde-{hyphenated}",
        description=f"Concorde {hyphenated} role.",
        source_path=role.prompt,
        kind="skill",
        body=body,
        exposure="internal",
        effects=role.effects,
    )
