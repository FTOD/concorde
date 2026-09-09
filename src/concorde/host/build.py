"""Deterministic rendering of prompt-sourced Agents and skills (proposal section 8).

The build renders the Agent and skill projections from ``agents/``/``prompts/``/``skills/``
sources into ``generated/`` and, for skills, directly into ``.claude/skills/<name>/SKILL.md`` and
``.agents/skills/<name>/SKILL.md``. After Stage B1 these rendered files are the only instruction
source the host and the agent runtimes consume: ``run_capability`` and ``load_agent`` verify
build freshness before using them and fail closed with ``BuildError(code="stale_build")`` when the
recorded sources have drifted. The build must be byte-identical across repeated runs and must not
perform any network or process I/O.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ..frontmatter import FrontMatterError, parse_document
from .effects import EffectDeclaration
from .typed_data import json_schema
from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_agent_spec,
    resolve_role_prompt,
    resolve_skill_source,
)
from .agent_model import agent_definition, load_agents, resolve_agent

if TYPE_CHECKING:
    from .agent_model import AgentBinding


@dataclass(frozen=True)
class SkillPrompt:
    """One Agent's rendered instructions and exact authority, resolved from the build.

    ``load_agent`` is the only place that constructs this. ``kind`` is always ``"skill"``: every
    Agent is a host-launched identity, never a paired capability (that kind no longer exists after
    the package cutover). ``binding`` carries the complete reproducible ``AgentBinding`` (A1, A4)
    when constructed by ``load_agent``; it is ``None`` for a plain ``SkillPrompt`` built elsewhere
    (for example a rendered Skill, which has no Agent binding).
    """

    name: str
    description: str
    source_path: str
    kind: Literal["skill"]
    body: str
    effects: EffectDeclaration | None = None
    binding: "AgentBinding | None" = None


class BuildError(ValueError):
    """The prompt/skill/role source tree cannot be rendered deterministically, or is stale."""

    def __init__(self, message: str, code: str = "invalid_build"):
        super().__init__(message)
        self.code = code


INTEGRATIONS = ("claude", "codex")
INTEGRATION_ROOTS = {"claude": ".claude/skills", "codex": ".agents/skills"}

AGENT_ROOTS: dict[str, str] = {
    agent.name.replace("_", "-"): agent.spec for agent in load_agents().values()
}
# Compatibility alias for one release: new code should read AGENT_ROOTS.
ROLE_ROOTS: dict[str, str] = AGENT_ROOTS

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

PROTOCOL_KINDS = ("module",)
PROTOCOL_MANIFEST_PATH = "protocol/manifest.json"

# The build owns exactly these locations under `generated/`; every recorded BuildOutput path
# lands inside one of them, and `generated/build-manifest.json` is written alongside them even
# though it is not itself a BuildOutput. `generated/` is a shared, ignored root -- another tool
# may write its own files there (for example diagram renders under `generated/architecture/`),
# and check_build must never judge locations it does not own.
GENERATED_OWNED_DIRS: tuple[str, ...] = ("generated/agents", "generated/protocol", "generated/docs")
GENERATED_OWNED_FILES: tuple[str, ...] = ("generated/build-manifest.json", "generated/langgraph.json")


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


def render_agent(project_root: Path, agent: str) -> BuildOutput:
    try:
        resolved = resolve_agent_spec(project_root, AGENT_ROOTS[agent])
    except PromptResolverError as error:
        raise BuildError(f"agent {agent}: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(path=f"generated/agents/{agent}.md", content=content, sources=resolved.sources)


# Compatibility alias for one release: new code should call render_agent.
render_role = render_agent


def _skill_frontmatter(name: str, description: str, integration: str, capability: str, entrypoint: str) -> str:
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
            f"  entrypoint: {json.dumps(entrypoint)}",
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
    entrypoint = f"{launcher} {name}"
    body = resolved.body.replace("{CAPABILITY}", f"python3 {launcher} {name}")
    unresolved = [token for token in ("{SCRIPT}", "{FRAMEWORK}", "{CAPABILITY}") if token in body]
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
    frontmatter = _skill_frontmatter(name, str(metadata["description"]), integration, str(metadata["capability"]), entrypoint)
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


def render_protocol_principles(project_root: Path) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, "prompts/protocol/principles.md")
    except PromptResolverError as error:
        raise BuildError(f"protocol principles: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(path="generated/protocol/principles.md", content=content, sources=resolved.sources)


def render_protocol_kind(project_root: Path, kind: str) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, f"prompts/protocol/kinds/{kind}.md")
    except PromptResolverError as error:
        raise BuildError(f"protocol kind {kind}: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(path=f"generated/protocol/kinds/{kind}.md", content=content, sources=resolved.sources)


def render_protocol_schemas(project_root: Path) -> BuildOutput:
    """Export the ``json_schema`` of every identity in ``contracts.exported_types()``.

    Replaces the former developer-run ``scripts/sync-protocol-assets.py``. This has no recorded
    ``sources``: the exported schemas are derived from Python contracts across ``capabilities/``
    and ``src/concorde/host/``, not from a fixed file set, so freshness here is verified by value
    (``package_validation._validate_contracts``), the same way it always was.
    """

    from .contracts import exported_types

    names = list(exported_types())
    payload = {name: json_schema(name) for name in names}
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(path="generated/protocol/schemas.json", content=content, sources=())


def render_docs_instructions(project_root: Path) -> BuildOutput:
    """Publish every Skill's rendered body and every Agent's rendered instructions (proposal §12).

    A read-only projection for the docsite's "Agent instructions" page: rendered bytes for human
    browsing, never a second authoring source or an agent-context channel. Each Agent entry's
    ``sources`` names the contributing prompt paths straight from its own build manifest entry, and
    ``spec``/``harness`` identify its authored Spec path and bound Harness name (A1, A2).
    """

    all_sources: set[str] = set()
    skills = []
    for name in SKILL_NAMES:
        metadata = _skill_metadata(project_root, name)
        rendered = render_skill(project_root, name, "claude")
        skills.append({
            "name": name,
            "description": str(metadata["description"]),
            "capability": str(metadata["capability"]),
            "body": rendered.content.decode("utf-8"),
        })
        all_sources.update(rendered.sources)
    agent_definitions = load_agents()
    agents = []
    for hyphenated in sorted(AGENT_ROOTS):
        rendered = render_agent(project_root, hyphenated)
        definition = agent_definitions[hyphenated.replace("-", "_")]
        agents.append({
            "name": f"concorde-{hyphenated}",
            "spec": definition.spec,
            "harness": definition.harness.name,
            "instructions": rendered.content.decode("utf-8"),
            "sources": sorted(rendered.sources),
        })
        all_sources.update(rendered.sources)
    payload = {"skills": skills, "agents": agents}
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(path="generated/docs/instructions.json", content=content, sources=tuple(sorted(all_sources)))


def render_docs_wire(project_root: Path) -> BuildOutput:
    """Publish the exported wire schemas for the docsite's "Wire contracts" page (proposal §12).

    Deliberately separate from ``generated/protocol/schemas.json`` (a Protocol-manifest-tracked
    runtime asset): this is a docsite-facing publication projection, not a distributed asset. No
    recorded ``sources``, matching ``render_protocol_schemas`` (derived from Python contracts, not
    a fixed file set); freshness is verified by value in ``package_validation``.
    """

    from .contracts import exported_types

    names = list(exported_types())
    payload = {name: json_schema(name) for name in names}
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(path="generated/docs/wire.json", content=content, sources=())


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
    """Render every Agent, skill and Studio-graph projection; raise BuildError on any failure."""

    root = Path(project_root)
    if integration == "all":
        integrations = INTEGRATIONS
    elif integration in INTEGRATIONS:
        integrations = (integration,)
    else:
        raise BuildError(f"unsupported integration: {integration}")

    outputs: list[BuildOutput] = []
    for agent in sorted(AGENT_ROOTS):
        outputs.append(render_agent(root, agent))
    for name in SKILL_NAMES:
        for one_integration in integrations:
            outputs.append(render_skill(root, name, one_integration, framework_prefix=framework_prefix))
    outputs.append(render_langgraph(root))
    outputs.append(render_protocol_principles(root))
    for kind in PROTOCOL_KINDS:
        outputs.append(render_protocol_kind(root, kind))
    outputs.append(render_protocol_schemas(root))
    outputs.append(render_docs_instructions(root))
    outputs.append(render_docs_wire(root))

    roots = (list(AGENT_ROOTS.values()) + list(SKILL_SOURCES.values()) + ["prompts/protocol/principles.md"]
             + [f"prompts/protocol/kinds/{kind}.md" for kind in PROTOCOL_KINDS])
    unreachable = find_unreachable_prompts(root, roots)
    if unreachable:
        raise BuildError(f"unreachable prompt files (no root includes them): {list(unreachable)}")

    ordered = tuple(sorted(outputs, key=lambda item: item.path))
    for output in ordered:
        if output.path.startswith("generated/"):
            assert output.path in GENERATED_OWNED_FILES or any(
                output.path.startswith(f"{owned_dir}/") for owned_dir in GENERATED_OWNED_DIRS
            ), (
                f"build output {output.path!r} is outside GENERATED_OWNED_DIRS/GENERATED_OWNED_FILES; "
                "update those declarations so check_build keeps judging every real output"
            )
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
    expected = {output.path for output in result.outputs}
    # A Protocol revision may retire a kind or role. Only these declared build-owned
    # subtrees are reconciled; diagrams and other tools' generated assets are preserved.
    for directory in GENERATED_OWNED_DIRS:
        owned = root / directory
        if owned.is_symlink():
            raise BuildError(f"build-owned output directory is a symlink: {directory}")
        if owned.is_dir():
            for path in owned.rglob("*"):
                if path.is_file() and not path.is_symlink() and path.relative_to(root).as_posix() not in expected:
                    path.unlink()
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


def _owned_generated_tree(root: Path) -> dict[str, bytes]:
    """Read every build-owned path under ``generated/`` at ``root``, keyed by path from ``root``."""
    contents: dict[str, bytes] = {}
    for owned_dir in GENERATED_OWNED_DIRS:
        for relative, data in _tree(root / owned_dir).items():
            contents[f"{owned_dir}/{relative}"] = data
    for owned_file in GENERATED_OWNED_FILES:
        path = root / owned_file
        if path.is_file() and not path.is_symlink():
            contents[owned_file] = path.read_bytes()
    return contents


def check_build(project_root: str | Path, integration: str = "all") -> tuple[bool, tuple[str, ...]]:
    """Render into a temporary directory and diff against every project_root output location.

    Returns (is_current, differences) where differences names every relative path (under the
    build-owned locations in ``generated/`` -- see ``GENERATED_OWNED_DIRS``/``GENERATED_OWNED_FILES``
    -- and, for our own seven skills, ``.claude/skills``/``.agents/skills``) that is missing,
    unexpected, or byte-different. Nothing under project_root is written or modified. A third
    party's own Skill directories (for example ``.claude/skills/archify``) are never inspected or
    reported, and neither is any other path under ``generated/`` that the build does not own (for
    example diagram renders under ``generated/architecture/``): ``generated/`` is a shared, ignored
    root and this check only judges what the build itself produces there.
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
        fresh_owned = _owned_generated_tree(temporary)
    current_owned = _owned_generated_tree(root)
    diffs = [
        relative
        for relative in set(fresh_owned) | set(current_owned)
        if fresh_owned.get(relative) != current_owned.get(relative)
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
    # A tracked Protocol manifest is optional here: some build roots (isolated build-lifecycle
    # fixtures, for example) hold only prompts/skills and never claim to distribute Protocol
    # assets at all. Its presence, once opted into, is still held to exact digest consistency.
    manifest_file = root / PROTOCOL_MANIFEST_PATH
    if manifest_file.is_file() and not manifest_file.is_symlink():
        try:
            tracked = json.loads(manifest_file.read_text(encoding="utf-8"))
            assets = tracked["assets"]
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
            diffs.append(PROTOCOL_MANIFEST_PATH)
        else:
            for item in assets:
                relative = item.get("path", "")
                content = fresh_owned.get(relative)
                if content is None or _sha256_bytes(content) != item.get("digest"):
                    diffs.append(f"{PROTOCOL_MANIFEST_PATH}:{relative}")
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
            raise BuildError(f"Protocol asset is missing from the current build: {item['path']}")
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


def load_agent(package_root: str | Path, name: str) -> SkillPrompt:
    """Load one Agent's rendered instructions and complete binding from the build.

    Verifies freshness first (via ``resolve_agent``). ``name`` accepts either the external
    ``concorde-<hyphenated>`` identity used throughout the host (for example
    ``concorde-spec-author``) or the bare hyphenated/underscored Agent name.
    """

    binding = resolve_agent(package_root, name)
    root = Path(package_root)
    try:
        body = (root / binding.instructions_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(f"cannot read rendered agent {binding.instructions_path}: {error}", "stale_build") from error
    hyphenated = binding.agent.replace("_", "-")
    return SkillPrompt(
        name=f"concorde-{hyphenated}",
        description=f"Concorde {hyphenated} agent.",
        source_path=binding.spec_path,
        kind="skill",
        body=body,
        effects=agent_definition(binding.agent).constraints.effects,
        binding=binding,
    )


# Compatibility alias for one release: new code should call load_agent.
load_role_prompt = load_agent
