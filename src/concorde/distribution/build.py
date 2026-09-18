"""Deterministic rendering of model Operation instructions and public client projections.

The build renders the WorkerProfile and client projections from ``operations/``/``prompts/``/``skills/``
sources into ``generated/`` and, for the developer's clients, directly into the project: Skills at
``.claude/skills/<name>/SKILL.md`` and ``.agents/skills/<name>/SKILL.md`` for Claude Code and Codex,
and the Pi session extension shim at ``.pi/extensions/concorde-session.ts``, which binds the tracked
extension to this project and carries the same public Operations as one typed tool. After Stage B1
these rendered files are the only instruction source the host and the agent runtimes consume:
``run_operation`` and ``load_model_instructions`` verify build freshness before using them and fail
closed with ``BuildError(code="stale_build")`` when the recorded sources have drifted. The build
must be byte-identical across repeated runs and must not perform any network or process I/O.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ..harness.effects import EffectDeclaration
from ..harness.worker_profile import (
    load_worker_profiles,
    resolve_worker,
    worker_profile,
)
from ..spec.contracts import SKILL_NAMES
from ..spec.frontmatter import FrontMatterError, parse_document
from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_model_instructions,
    resolve_role_prompt,
    resolve_skill_source,
)

if TYPE_CHECKING:
    from ..harness.worker_profile import WorkerBinding


@dataclass(frozen=True)
class SkillPrompt:
    """One WorkerProfile's rendered instructions and exact authority, resolved from the build.

    ``kind=skill`` is retained record compatibility, not an executable kind. Model projections
    carry a complete WorkerBinding; plain external Skill instructions have no worker binding.
    """

    name: str
    description: str
    source_path: str
    kind: Literal["skill"]
    body: str
    effects: EffectDeclaration | None = None
    binding: "WorkerBinding | None" = None


@dataclass(frozen=True)
class ModelInstructions(SkillPrompt):
    """An admitted worker projection always has explicit effects and a complete WorkerProfile binding."""

    effects: EffectDeclaration = field()
    binding: "WorkerBinding" = field()


class BuildError(ValueError):
    """The prompt/skill/role source tree cannot be rendered deterministically, or is stale."""

    def __init__(self, message: str, code: str = "invalid_build"):
        super().__init__(message)
        self.code = code


# Claude Code and Codex read Skills; Pi reads the session extension shim instead of Skills.
SKILL_INTEGRATIONS = ("claude", "codex")
INTEGRATIONS = (*SKILL_INTEGRATIONS, "pi")
INTEGRATION_ROOTS = {
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "pi": ".pi/extensions",
}
# The tracked Pi session extension and the shim that binds it to one project. The shim carries
# the catalog of public Operations; the extension is framework code the shim imports.
PI_SESSION_EXTENSION = "pi/extensions/concorde-session.ts"
PI_SESSION_SHIM = f"{INTEGRATION_ROOTS['pi']}/concorde-session.ts"
# Skill includes that describe another client's invocation mechanics (the stdin envelope the
# Skills send through the launcher); the Pi tool builds that envelope itself, so its guidance
# leaves them out.
PI_OMITTED_INCLUDES = frozenset(
    {
        "prompts/workflow-host/stdin-invocation-open.md",
        "prompts/workflow-host/stdin-invocation-config-input.md",
    }
)
# An installed consumer runs the launcher with its managed runtime (manifest ``runtime.venv``,
# verified by ``managed_runtime``); the source checkout uses its own development environment.
CONSUMER_RUNTIME_VENV = ".concorde/.venv"
# Keep explicit ownership after a Skill leaves SKILL_NAMES, even if a newer manifest
# has already forgotten it. A name prefix alone never authorizes deletion.
RETIRED_SKILL_NAMES = ("concorde-reflections-triage",)

MODEL_ROOTS: dict[str, str] = {
    agent.name.replace("_", "-"): agent.spec
    for agent in load_worker_profiles().values()
}
# The tier-one rules every worker follows, rendered before each worker's own role Spec.
WORKER_RULES = "prompts/workers/common.md"

SKILL_SOURCES: dict[str, str] = {
    name: f"skills/{name}/SKILL.md" for name in SKILL_NAMES
}

SCHEMA_INTRO = "This complete schema is the invocation's input field. It does not grant project reads.\n"

PROTOCOL_KINDS = ("module",)
PROTOCOL_MANIFEST_PATH = "protocol/manifest.json"

# The build owns exactly these locations under `generated/`; every recorded BuildOutput path
# lands inside one of them, and `generated/build-manifest.json` is written alongside them even
# though it is not itself a BuildOutput. `generated/` is a shared, ignored root -- another tool
# may write its own files there (for example diagram renders under `generated/architecture/`),
# and check_build must never judge locations it does not own.
GENERATED_OWNED_DIRS: tuple[str, ...] = (
    "generated/agents",
    "generated/protocol",
    "generated/docs",
)
GENERATED_OWNED_FILES: tuple[str, ...] = (
    "generated/build-manifest.json",
    "generated/langgraph.json",
)


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
        raise BuildError(
            f"invalid skill source front matter in {relative}: {error}"
        ) from error
    required = {"name", "description", "operation"}
    if set(metadata) != required:
        raise BuildError(
            f"skill source {relative} must declare exactly {sorted(required)}, found {sorted(metadata)}"
        )
    if metadata["name"] != name:
        raise BuildError(
            f"skill source {relative} must declare name: {name}, found {metadata['name']!r}"
        )
    if (
        not isinstance(metadata["description"], str)
        or not metadata["description"].strip()
    ):
        raise BuildError(f"skill source {relative} requires a non-empty description")
    if not isinstance(metadata["operation"], str) or not metadata["operation"].strip():
        raise BuildError(f"skill source {relative} requires a non-empty operation")
    return metadata


def render_model_instructions(project_root: Path, agent: str) -> BuildOutput:
    """One worker's instructions: the common worker rules, then its own role Spec.

    Its child definitions are sources too, so a changed child makes the build stale."""
    try:
        rules = resolve_role_prompt(project_root, WORKER_RULES)
        role = resolve_model_instructions(project_root, MODEL_ROOTS[agent])
    except PromptResolverError as error:
        raise BuildError(f"agent {agent}: {error.rule_id}: {error}") from error
    children = tuple(child.definition for child in worker_profile(agent).children)
    content = (rules.body.rstrip("\n") + "\n\n" + role.body).encode("utf-8")
    return BuildOutput(
        path=f"generated/agents/{agent}.md",
        content=content,
        sources=tuple(sorted({*rules.sources, *role.sources, *children})),
    )


def _skill_frontmatter(
    name: str,
    description: str,
    integration: str,
    operation: str,
    entrypoint: str,
    *,
    model_invocable: bool,
) -> str:
    values = ["---", f"name: {name}", f"description: {json.dumps(description)}"]
    if integration == "claude":
        values.append('argument-hint: "Optional operation guidance"')
    values.extend(
        [
            'compatibility: "Requires a Concorde project"',
            "metadata:",
            '  author: "concorde"',
            f"  source: {json.dumps(SKILL_SOURCES[name])}",
            '  kind: "skill"',
            f"  operation: {json.dumps(operation)}",
            f"  entrypoint: {json.dumps(entrypoint)}",
        ]
    )
    if integration == "claude":
        # `disable-model-invocation: true` hides the Skill from the model entirely; only the user's
        # own `/name` invocation reaches it. `false` lets Claude Code select it by description.
        values.extend(
            [
                "user-invocable: true",
                f"disable-model-invocation: {'false' if model_invocable else 'true'}",
            ]
        )
    values.extend(["---", ""])
    return "\n".join(values)


def render_skill(
    project_root: Path, name: str, integration: str, *, framework_prefix: str = ""
) -> BuildOutput:
    """Render one public Skill for one integration.

    Without a ``framework_prefix`` the Skill is projected into the Concorde source checkout
    itself, whose launcher is the checkout's own ``scripts/run-operation.py``. Developing that
    checkout is direct maintenance by default and a Concorde graph runs there only on the
    developer's explicit request, so the Claude projection is rendered user-invocable only:
    hidden from the model, reachable through the developer's own ``/name`` invocation. With a
    framework prefix the Skill is the installed consumer projection and stays model-invocable.
    """
    if integration not in INTEGRATIONS:
        raise BuildError(f"unsupported integration: {integration}")
    metadata = _skill_metadata(project_root, name)
    try:
        resolved = resolve_skill_source(project_root, SKILL_SOURCES[name])
    except PromptResolverError as error:
        raise BuildError(f"skill {name}: {error.rule_id}: {error}") from error
    prefix = framework_prefix.strip("/")
    launcher = (
        f"{prefix}/scripts/run-operation.py" if prefix else "scripts/run-operation.py"
    )
    entrypoint = f"{launcher} {name}"
    body = resolved.body.replace("{OPERATION}", f"python3 {launcher} {name}")
    unresolved = [
        token for token in ("{SCRIPT}", "{FRAMEWORK}", "{OPERATION}") if token in body
    ]
    if unresolved:
        raise BuildError(
            f"skill {name} contains unresolved package tokens: {unresolved}"
        )
    schemas, schema_sources, _ = _root_schemas(project_root)
    request_type = f"{name}-request"
    if request_type not in schemas:
        raise BuildError(
            f"skill {name} has no exported request schema {request_type!r} in the named root's contracts"
        )
    body = (
        body.rstrip("\n")
        + "\n\n## Input TypedValue schema\n\n"
        + SCHEMA_INTRO
        + "\n```json\n"
        + json.dumps(schemas[f"{name}-request"], indent=2)
        + "\n```\n"
    )
    frontmatter = _skill_frontmatter(
        name,
        str(metadata["description"]),
        integration,
        str(metadata["operation"]),
        entrypoint,
        model_invocable=bool(prefix),
    )
    content = (frontmatter + body.lstrip()).encode("utf-8")
    target = f"{INTEGRATION_ROOTS[integration]}/{name}/SKILL.md"
    return BuildOutput(
        path=target,
        content=content,
        sources=tuple(
            sorted(set((*resolved.sources, SKILL_SOURCES[name], *schema_sources)))
        ),
    )


def _interpreters(prefix: str) -> list[str]:
    venv = CONSUMER_RUNTIME_VENV if prefix else ".venv"
    return [f"{venv}/bin/python", f"{venv}/Scripts/python.exe"]


def render_pi_session(project_root: Path, *, framework_prefix: str = "") -> BuildOutput:
    """Render the Pi session extension shim: the public Operations as one typed tool.

    Pi loads project-local extensions from ``.pi/extensions/``; the shim rendered there imports
    the tracked extension (``PI_SESSION_EXTENSION``, below the framework prefix in an installed
    project) and binds it to this project with the catalog: every public Operation's description,
    its Skill guidance without the stdin envelope mechanics, and its request schema. The tool wraps
    the request in the invocation envelope and runs the same launcher the Skills name. Without a
    framework prefix the shim marks the source checkout, where an Operation runs only on the
    developer's explicit request, as the Claude Skill projection does.
    """
    prefix = framework_prefix.strip("/")
    schemas, schema_sources, _ = _root_schemas(project_root)
    sources: set[str] = set(schema_sources)
    operations = []
    for name in SKILL_NAMES:
        metadata = _skill_metadata(project_root, name)
        try:
            resolved = resolve_skill_source(
                project_root, SKILL_SOURCES[name], omit=PI_OMITTED_INCLUDES
            )
        except PromptResolverError as error:
            raise BuildError(f"skill {name}: {error.rule_id}: {error}") from error
        guidance = re.sub(r"\n{3,}", "\n\n", resolved.body).strip("\n") + "\n"
        unresolved = [
            token
            for token in ("{SCRIPT}", "{FRAMEWORK}", "{OPERATION}")
            if token in guidance
        ]
        if unresolved:
            raise BuildError(
                f"skill {name} guidance contains unresolved package tokens: {unresolved}"
            )
        request_type = f"{name}-request"
        if request_type not in schemas:
            raise BuildError(
                f"skill {name} has no exported request schema {request_type!r} in the named root's contracts"
            )
        schema = schemas[request_type]
        try:
            version = schema["properties"]["schema_version"]["const"]
        except (KeyError, TypeError) as error:
            raise BuildError(
                f"request schema {request_type} declares no constant schema_version"
            ) from error
        operations.append(
            {
                "name": name,
                "description": str(metadata["description"]),
                "guidance": guidance,
                "request_version": version,
                "request_schema": schema,
            }
        )
        sources.update(resolved.sources)
        sources.add(SKILL_SOURCES[name])
    catalog = {
        "schema_version": 1,
        "launcher": f"{prefix}/scripts/run-operation.py"
        if prefix
        else "scripts/run-operation.py",
        "interpreters": _interpreters(prefix),
        "explicit_request_only": not prefix,
        "operations": operations,
    }
    extension = f"{prefix}/{PI_SESSION_EXTENSION}" if prefix else PI_SESSION_EXTENSION
    depth = PI_SESSION_SHIM.count("/")
    import_path = "../" * depth + extension
    content = (
        "// Rendered by `python3 scripts/concorde.py build` from skills/, prompts/ and the\n"
        "// operation contracts; do not edit. The Concorde session extension itself lives at\n"
        f"// {extension}; this shim binds it to this project.\n"
        'import { fileURLToPath } from "node:url";\n'
        f'import {{ concordeSession }} from "{import_path}";\n'
        f'import type {{ SessionCatalog }} from "{import_path}";\n\n'
        "const CATALOG: SessionCatalog = "
        + json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False)
        + ";\n\n"
        "export default concordeSession(\n"
        f'\tfileURLToPath(new URL("{"../" * depth}", import.meta.url)),\n'
        "\tCATALOG,\n"
        ");\n"
    ).encode("utf-8")
    return BuildOutput(
        path=PI_SESSION_SHIM, content=content, sources=tuple(sorted(sources))
    )


def render_langgraph(project_root: Path) -> BuildOutput:
    """Studio graph list derived from ``skills/`` (proposal section 8, item 6)."""

    graphs = {
        name: f"./scripts/development/studio.py:{name.replace('-', '_')}"
        for name in SKILL_NAMES
    }
    payload = {
        "$schema": "https://langgra.ph/schema.json",
        "dependencies": ["."],
        "graphs": graphs,
        "env": {"LANGSMITH_TRACING": "false"},
    }
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(
        path="generated/langgraph.json",
        content=content,
        sources=tuple(sorted(SKILL_SOURCES.values())),
    )


def render_protocol_principles(project_root: Path) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(project_root, "prompts/protocol/principles.md")
    except PromptResolverError as error:
        raise BuildError(f"protocol principles: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(
        path="generated/protocol/principles.md",
        content=content,
        sources=resolved.sources,
    )


def render_protocol_kind(project_root: Path, kind: str) -> BuildOutput:
    try:
        resolved = resolve_role_prompt(
            project_root, f"prompts/protocol/kinds/{kind}.md"
        )
    except PromptResolverError as error:
        raise BuildError(f"protocol kind {kind}: {error.rule_id}: {error}") from error
    content = resolved.body.encode("utf-8")
    return BuildOutput(
        path=f"generated/protocol/kinds/{kind}.md",
        content=content,
        sources=resolved.sources,
    )


def _root_schemas(project_root: Path) -> tuple[dict, tuple[str, ...], tuple[str, ...]]:
    """Evaluate schema sources in a private namespace, without stale module/pyc caches.

    Returns the rendered schemas, the root-local source files they depend on, and the root's
    exported identity sequence exactly as declared, so callers can judge uniqueness before the
    schema dictionary collapses any duplicate.
    """
    source_root = project_root / "src/concorde"
    if not (source_root / "spec").is_dir():
        # A root without any schema source tree, such as a prompt-only fixture, renders the
        # running package's schemas and binds no root-local schema source.
        from ..spec.contracts import exported_types
        from ..spec.typed_data import json_schema

        identities = tuple(exported_types())
        return {name: json_schema(name) for name in identities}, (), identities
    for required in ("contracts.py", "typed_data.py"):
        if not (source_root / "spec" / required).is_file():
            # A populated schema tree missing its entry modules is a broken root, never a
            # reason to fall back to another package's schemas.
            raise BuildError(
                f"incomplete schema source tree: src/concorde/spec/{required} is missing"
            )
    namespace = "_concorde_build_" + uuid.uuid4().hex
    sources: set[str] = set()

    class Sources(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, fullname, path=None, target=None):
            if fullname != namespace and not fullname.startswith(namespace + "."):
                return None
            parts = fullname.split(".")[1:]
            location = source_root.joinpath(*parts)
            if location.is_dir():
                return importlib.util.spec_from_loader(fullname, self, is_package=True)
            if location.with_suffix(".py").is_file():
                return importlib.util.spec_from_loader(fullname, self)
            return None

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            location = source_root.joinpath(*module.__name__.split(".")[1:])
            if location.is_dir():
                module.__path__ = [str(location)]
                # Namespace containers avoid unrelated package initialization.
                return
            location = location.with_suffix(".py")
            relative = location.relative_to(project_root).as_posix()
            from ..spec.typed_data import checked_path

            location = checked_path(project_root, relative)
            sources.add(relative)
            module.__file__ = str(location)
            try:
                # Use the normal Python source-loader contract, but bypass timestamp-based bytecode
                # caches: build identity covers these exact trusted package source bytes.
                loader = SourceFileLoader(module.__name__, str(location))
                code = loader.source_to_code(location.read_bytes(), str(location))
                exec(code, module.__dict__)
            except BuildError:
                raise
            except Exception as error:
                raise BuildError(
                    f"cannot evaluate schema source {relative}: {error}"
                ) from error

    finder = Sources()
    sys.meta_path.insert(0, finder)
    try:
        try:
            contracts = importlib.import_module(namespace + ".spec.contracts")
            provider = importlib.import_module(namespace + ".spec.typed_data")
            identities = tuple(contracts.exported_types())
            payload = {name: provider.json_schema(name) for name in identities}
        except BuildError:
            raise
        except Exception as error:
            # Every failure of the root's own schema sources stays inside the declared
            # BuildError boundary instead of escaping as an undeclared exception.
            raise BuildError(
                f"cannot evaluate schema sources under {source_root}: {error}"
            ) from error
        return payload, tuple(sorted(sources)), identities
    finally:
        sys.meta_path.remove(finder)
        for name in tuple(sys.modules):
            if name == namespace or name.startswith(namespace + "."):
                del sys.modules[name]


def render_protocol_schemas(project_root: Path) -> BuildOutput:
    """Export schemas from the named root and bind every loaded source to the output."""
    payload, sources, _ = _root_schemas(project_root)
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return BuildOutput(
        path="generated/protocol/schemas.json", content=content, sources=sources
    )


def _manifest(project_root: Path, outputs: tuple[BuildOutput, ...]) -> bytes:
    all_sources: set[str] = set()
    for output in outputs:
        all_sources.update(output.sources)
    # WorkerProfile declarations and operation wire metadata are authored build inputs too.
    for directory in ("operations",):
        all_sources.update(
            path.relative_to(project_root).as_posix()
            for path in (project_root / directory).rglob("*.py")
            if path.is_file()
        )
    for relative in (
        "src/concorde/spec/contracts.py",
        "src/concorde/spec/contract_shapes.py",
        "src/concorde/spec/wire_shapes.py",
        "src/concorde/harness/worker_profile.py",
        "src/concorde/harness/operation_state.py",
        "src/concorde/harness/operation_node.py",
        # The shim binds the tracked session extension; its behavior is part of the projection.
        PI_SESSION_EXTENSION,
    ):
        if (project_root / relative).is_file():
            all_sources.add(relative)
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


def build(
    project_root: str | Path, integration: str = "all", *, framework_prefix: str = ""
) -> BuildResult:
    """Render every WorkerProfile, skill and Studio-graph projection; raise BuildError on any failure."""

    root = Path(project_root)
    integrations = _selected_integrations(integration)

    outputs: list[BuildOutput] = []
    for agent in sorted(MODEL_ROOTS):
        outputs.append(render_model_instructions(root, agent))
    for one_integration in integrations:
        if one_integration == "pi":
            outputs.append(render_pi_session(root, framework_prefix=framework_prefix))
            continue
        for name in SKILL_NAMES:
            outputs.append(
                render_skill(
                    root, name, one_integration, framework_prefix=framework_prefix
                )
            )
    outputs.append(render_langgraph(root))
    outputs.append(render_protocol_principles(root))
    for kind in PROTOCOL_KINDS:
        outputs.append(render_protocol_kind(root, kind))
    outputs.append(render_protocol_schemas(root))

    roots = (
        list(MODEL_ROOTS.values())
        + [WORKER_RULES]
        + list(SKILL_SOURCES.values())
        + ["prompts/protocol/principles.md"]
        + [f"prompts/protocol/kinds/{kind}.md" for kind in PROTOCOL_KINDS]
    )
    unreachable = find_unreachable_prompts(root, roots)
    if unreachable:
        raise BuildError(
            f"unreachable prompt files (no root includes them): {list(unreachable)}"
        )

    ordered = tuple(sorted(outputs, key=lambda item: item.path))
    for output in ordered:
        if output.path.startswith("generated/"):
            assert output.path in GENERATED_OWNED_FILES or any(
                output.path.startswith(f"{owned_dir}/")
                for owned_dir in GENERATED_OWNED_DIRS
            ), (
                f"build output {output.path!r} is outside GENERATED_OWNED_DIRS/GENERATED_OWNED_FILES; "
                "update those declarations so check_build keeps judging every real output"
            )
    manifest = _manifest(root, ordered)
    return BuildResult(outputs=ordered, manifest=manifest)


def _selected_integrations(integration: str) -> tuple[str, ...]:
    if integration == "all":
        return INTEGRATIONS
    if integration in INTEGRATIONS:
        return (integration,)
    raise BuildError(f"unsupported integration: {integration}")


def _retired_skill_directories(root: Path, integration: str) -> tuple[Path, ...]:
    """Locate explicitly retired projections without following integration-root symlinks."""
    directories: list[Path] = []
    for selected in _selected_integrations(integration):
        if selected not in SKILL_INTEGRATIONS:
            continue
        prefix = Path(INTEGRATION_ROOTS[selected])
        for relative in (prefix.parent, prefix):
            if (root / relative).is_symlink():
                raise BuildError(f"skill output directory is a symlink: {relative}")
        for name in RETIRED_SKILL_NAMES:
            directory = root / prefix / name
            if directory.exists() or directory.is_symlink():
                directories.append(directory)
    return tuple(directories)


def _retired_skill_cleanup(root: Path, integration: str) -> tuple[Path, ...]:
    """Preflight every retirement before writes; preserve unexpected files and links."""
    directories = _retired_skill_directories(root, integration)
    for directory in directories:
        if directory.is_symlink() or not directory.is_dir():
            raise BuildError(f"unsafe retired skill directory: {directory}")
        for path in directory.iterdir():
            if path.name != "SKILL.md" or path.is_symlink() or not path.is_file():
                raise BuildError(f"unexpected retired skill content: {path}")
    return directories


def write_build(
    project_root: str | Path,
    integration: str = "all",
    *,
    framework_prefix: str = "",
    integration_root: str | Path | None = None,
) -> BuildResult:
    """Render and write outputs.

    Outputs under ``generated/`` are always written below ``project_root`` (the location that
    owns the recorded build manifest). Rendered client projections (``.claude/skills/*``,
    ``.agents/skills/*`` and the ``.pi/extensions`` shim) are written below ``integration_root``
    when given, so an installer can render a consumer's framework sources while placing the
    consumer-facing projections at the consumer's own project root.
    """

    root = Path(project_root)
    destination = Path(integration_root) if integration_root is not None else root
    projected = tuple(f"{prefix}/" for prefix in INTEGRATION_ROOTS.values())
    result = build(root, integration, framework_prefix=framework_prefix)
    retired = _retired_skill_cleanup(destination, integration)
    expected = {output.path for output in result.outputs}
    # A Protocol revision may retire a kind or role. Only these declared build-owned
    # subtrees are reconciled; diagrams and other tools' generated assets are preserved.
    for directory in GENERATED_OWNED_DIRS:
        owned = root / directory
        if owned.is_symlink():
            raise BuildError(f"build-owned output directory is a symlink: {directory}")
        if owned.is_dir():
            for path in owned.rglob("*"):
                if (
                    path.is_file()
                    and not path.is_symlink()
                    and path.relative_to(root).as_posix() not in expected
                ):
                    path.unlink()
    for directory in retired:
        (directory / "SKILL.md").unlink(missing_ok=True)
        directory.rmdir()
    for output in result.outputs:
        base = destination if output.path.startswith(projected) else root
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


def check_build(
    project_root: str | Path, integration: str = "all"
) -> tuple[bool, tuple[str, ...]]:
    """Render into a temporary directory and diff against every project_root output location.

    Returns (is_current, differences) where differences names every relative path (under the
    build-owned locations in ``generated/`` -- see ``GENERATED_OWNED_DIRS``/``GENERATED_OWNED_FILES``
    -- for our current or explicitly retired skills, ``.claude/skills``/``.agents/skills``, and the
    Pi session shim) that is missing, unexpected, or byte-different. Nothing under project_root is
    written or modified. A third party's own Skill directories (for example
    ``.claude/skills/<vendor-skill>``) and the developer's own Pi extensions beside the shim are
    never inspected or reported, and neither is any other path under ``generated/`` that the build
    does not own (for example diagram renders under ``generated/architecture/``): ``generated/`` is
    a shared, ignored root and this check only judges what the build itself produces there.
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
    diffs.extend(
        directory.relative_to(root).as_posix()
        for directory in _retired_skill_directories(root, integration)
    )
    selected = _selected_integrations(integration)
    for selected_integration in selected:
        prefix = INTEGRATION_ROOTS[selected_integration]
        if selected_integration == "pi":
            fresh = next(
                (output.content for output in result.outputs if output.path == PI_SESSION_SHIM),
                None,
            )
            shim = root / PI_SESSION_SHIM
            current = (
                shim.read_bytes() if shim.is_file() and not shim.is_symlink() else None
            )
            if fresh != current:
                diffs.append(PI_SESSION_SHIM)
            continue
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


def load_model_instructions(package_root: str | Path, name: str) -> ModelInstructions:
    """Load one worker's rendered instructions and complete binding from the build.

    Verifies freshness first (via ``resolve_worker``). ``name`` accepts either the external
    ``concorde-<hyphenated>`` identity used throughout the host (for example
    ``concorde-code-reviewer``) or the bare hyphenated/underscored WorkerProfile name.
    """

    binding = resolve_worker(package_root, name)
    root = Path(package_root)
    try:
        body = (root / binding.instructions_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(
            f"cannot read rendered agent {binding.instructions_path}: {error}",
            "stale_build",
        ) from error
    hyphenated = binding.agent.replace("_", "-")
    return ModelInstructions(
        name=f"concorde-{hyphenated}",
        description=f"Concorde {hyphenated} agent.",
        source_path=binding.spec_path,
        kind="skill",
        body=body,
        effects=worker_profile(binding.agent).contract.effects,
        binding=binding,
    )
