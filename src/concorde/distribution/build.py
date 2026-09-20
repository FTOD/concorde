"""Deterministic worker instructions, Protocol assets and Pi Operation catalog.

Source builds write only private generated/session/pi integration output. Consumer
installation renders the same catalog with an explicit framework prefix; it owns deployment.
No standalone Skill publishing or client-selection interface remains.
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
import uuid
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import TYPE_CHECKING

from ..harness.effects import EffectDeclaration
from ..harness.worker_profile import (
    load_worker_profiles,
    resolve_worker,
    worker_profile,
)
from ..spec.contracts import PUBLIC_OPERATIONS
from ..spec.frontmatter import FrontMatterError, parse_document
from .prompt_resolver import (
    PromptResolverError,
    find_unreachable_prompts,
    resolve_model_instructions,
    resolve_operation_guidance,
    resolve_role_prompt,
)

if TYPE_CHECKING:
    from ..harness.worker_profile import WorkerBinding


@dataclass(frozen=True)
class ModelInstructions:
    """One admitted worker's instructions, effect ceiling and current build binding.

    This in-process record is not a public Operation catalog entry or a wire envelope.
    The host narrows its effects to the actual grant and reverifies its WorkerBinding.
    """

    name: str
    description: str
    source_path: str
    body: str
    effects: EffectDeclaration
    binding: WorkerBinding


class BuildError(ValueError):
    """The instruction/guidance source tree cannot be rendered deterministically, or is stale."""

    def __init__(self, message: str, code: str = "invalid_build"):
        super().__init__(message)
        self.code = code


# Private source entry and receipt-owned installed entry share the same catalog shape.
PI_SESSION_EXTENSION = "pi/extensions/concorde-session.ts"
PI_SESSION_SHIM = ".pi/extensions/concorde-session.ts"
PRIVATE_PI_SESSION_SHIM = "generated/session/pi/concorde-session.ts"
CONSUMER_RUNTIME_VENV = ".concorde/.venv"
# Explicit historical identities are retirement inventory, not supported clients/Skills.
LEGACY_OPERATION_NAMES = (
    *PUBLIC_OPERATIONS,
    "concorde-reflections-triage",
    "concorde-review",
    "concorde-main",
    "concorde-dev-loop",
    "concorde-specify-loop",
)
LEGACY_PROJECTION_ROOTS = (
    "generated/session/codex",
    "generated/session/claude",
    ".agents/skills",
    ".claude/skills",
)

MODEL_ROOTS: dict[str, str] = {
    agent.name.replace("_", "-"): agent.spec
    for agent in load_worker_profiles().values()
}
# The tier-one rules every worker follows, rendered before each worker's own role Spec.
WORKER_RULES = "prompts/workers/common.md"

OPERATION_GUIDANCE: dict[str, str] = {
    name: f"prompts/operation-guidance/{name}.md" for name in PUBLIC_OPERATIONS
}
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
    "generated/session",
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


def _guidance_metadata(project_root: Path, name: str) -> dict[str, object]:
    relative = OPERATION_GUIDANCE[name]
    path = project_root / relative
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise BuildError(
            f"cannot read operation guidance source {relative}: {error}"
        ) from error
    try:
        metadata, _ = parse_document(text, relative)
    except FrontMatterError as error:
        raise BuildError(
            f"invalid operation guidance source front matter in {relative}: {error}"
        ) from error
    required = {"name", "description", "operation"}
    if set(metadata) != required:
        raise BuildError(
            f"operation guidance source {relative} must declare exactly {sorted(required)}, found {sorted(metadata)}"
        )
    if metadata["name"] != name:
        raise BuildError(
            f"operation guidance source {relative} must declare name: {name}, found {metadata['name']!r}"
        )
    if (
        not isinstance(metadata["description"], str)
        or not metadata["description"].strip()
    ):
        raise BuildError(
            f"operation guidance source {relative} requires a non-empty description"
        )
    if not isinstance(metadata["operation"], str) or not metadata["operation"].strip():
        raise BuildError(
            f"operation guidance source {relative} requires a non-empty operation"
        )
    return metadata


def render_model_instructions(project_root: Path, agent: str) -> BuildOutput:
    """One worker's instructions: the common worker rules, then its own role Spec.

    Only authored terminal worker instructions are projected."""
    try:
        rules = resolve_role_prompt(project_root, WORKER_RULES)
        role = resolve_model_instructions(project_root, MODEL_ROOTS[agent])
    except PromptResolverError as error:
        raise BuildError(f"agent {agent}: {error.rule_id}: {error}") from error
    content = (rules.body.rstrip("\n") + "\n\n" + role.body).encode("utf-8")
    return BuildOutput(
        path=f"generated/agents/{agent}.md",
        content=content,
        sources=tuple(sorted({*rules.sources, *role.sources})),
    )


def _interpreters(prefix: str) -> list[str]:
    venv = CONSUMER_RUNTIME_VENV if prefix else ".venv"
    return [f"{venv}/bin/python", f"{venv}/Scripts/python.exe"]


def render_pi_session(project_root: Path, *, framework_prefix: str = "") -> BuildOutput:
    """Embed all public Operation guidance and versioned schemas in one Pi shim."""
    prefix = framework_prefix.strip("/")
    schemas, schema_sources, _ = _root_schemas(project_root)
    sources: set[str] = set(schema_sources)
    operations = []
    for name in PUBLIC_OPERATIONS:
        metadata = _guidance_metadata(project_root, name)
        try:
            resolved = resolve_operation_guidance(
                project_root, OPERATION_GUIDANCE[name]
            )
        except PromptResolverError as error:
            raise BuildError(f"operation {name}: {error.rule_id}: {error}") from error
        guidance = re.sub(r"\n{3,}", "\n\n", resolved.body).strip("\n") + "\n"
        unresolved = [
            token
            for token in ("{SCRIPT}", "{FRAMEWORK}", "{OPERATION}")
            if token in guidance
        ]
        if unresolved:
            raise BuildError(
                f"operation {name} guidance contains unresolved package tokens: {unresolved}"
            )
        request_type = f"{name}-request"
        if request_type not in schemas:
            raise BuildError(
                f"operation {name} has no exported request schema {request_type!r} in the named root's contracts"
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
        sources.add(OPERATION_GUIDANCE[name])
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
    shim_path = PI_SESSION_SHIM if prefix else PRIVATE_PI_SESSION_SHIM
    depth = shim_path.count("/")
    import_path = "../" * depth + extension
    content = (
        "// Rendered by `python3 scripts/concorde.py build` from operation guidance, prompts/ and the\n"
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
        "\tfileURLToPath(import.meta.url),\n"
        ");\n"
    ).encode("utf-8")
    return BuildOutput(path=shim_path, content=content, sources=tuple(sorted(sources)))


def render_langgraph(project_root: Path) -> BuildOutput:
    """Studio graph list derived from the public Operation inventory."""

    graphs = {
        name: f"./scripts/development/studio.py:{name.replace('-', '_')}"
        for name in PUBLIC_OPERATIONS
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
        sources=tuple(sorted(OPERATION_GUIDANCE.values())),
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
                # pi-lens-ignore: S102
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
    for directory in ("operations", "src/concorde"):
        all_sources.update(
            path.relative_to(project_root).as_posix()
            for path in (project_root / directory).rglob("*.py")
            if path.is_file()
        )
    # Pi implementation and dependency locks are transitive runtime provenance, not catalogs.
    all_sources.update(
        path.relative_to(project_root).as_posix()
        for path in (project_root / "pi").rglob("*")
        if not {"node_modules", "__pycache__"}.intersection(path.parts)
        and path.is_file()
    )
    for relative in (
        "concorde.json",
        "pi/package.json",
        "pi/package-lock.json",
        "pi/.npmrc",
        "scripts/requirements.lock",
        "scripts/concorde.py",
        "scripts/install-concorde.py",
        "scripts/run-operation.py",
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


def build(project_root: str | Path, *, framework_prefix: str = "") -> BuildResult:
    """Render every WorkerProfile, Pi catalog and Studio-graph projection; raise BuildError on any failure."""

    root = Path(project_root)

    outputs: list[BuildOutput] = []
    for agent in sorted(MODEL_ROOTS):
        outputs.append(render_model_instructions(root, agent))
    outputs.append(render_pi_session(root, framework_prefix=framework_prefix))
    outputs.append(render_langgraph(root))
    outputs.append(render_protocol_principles(root))
    for kind in PROTOCOL_KINDS:
        outputs.append(render_protocol_kind(root, kind))
    outputs.append(render_protocol_schemas(root))

    roots = (
        list(MODEL_ROOTS.values())
        + [WORKER_RULES]
        + list(OPERATION_GUIDANCE.values())
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


def _legacy_outputs(root: Path) -> dict[str, bytes]:
    """Inspect exact historical names only; neighboring external CLI content is not ours."""
    contents = {}
    for prefix in LEGACY_PROJECTION_ROOTS:
        for name in LEGACY_OPERATION_NAMES:
            relative = f"{prefix}/{name}/SKILL.md"
            path = _checked_output(root, relative)
            directory = path.parent
            if directory.exists():
                children = list(directory.iterdir())
                if any(child != path for child in children):
                    raise BuildError(
                        f"unexpected retired projection content: {directory}"
                    )
                if path.exists():
                    contents[relative] = path.read_bytes()
    path = _checked_output(root, PI_SESSION_SHIM)
    if path.exists():
        contents[PI_SESSION_SHIM] = path.read_bytes()
    return contents


def write_build(project_root: str | Path) -> BuildResult:
    """Write only into the named source root after whole-plan safety preflight.

    Installation uses the pure build renderer and its own receipt transaction. There is no
    alternate output root. Retired files require exact old manifest ownership; unknown files,
    extra retired contents, modified retired bytes and links block before any output changes.
    """
    root = Path(project_root)
    result = build(root)
    recorded = _recorded_outputs(root)
    expected = {output.path for output in result.outputs}
    current = _owned_generated_tree(root)
    current.update(_legacy_outputs(root))
    retired = []
    for relative, content in current.items():
        if relative in expected or relative == "generated/build-manifest.json":
            continue
        if recorded.get(relative, {}).get("sha256") != _sha256_bytes(content):
            raise BuildError(
                f"unowned or modified retired output; explicitly archive it: {relative}"
            )
        retired.append(_checked_output(root, relative))
    targets = [
        (output, _checked_output(root, output.path)) for output in result.outputs
    ]
    for path in retired:
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
    current.update(_legacy_outputs(root))
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
        body=body,
        effects=worker_profile(binding.agent).contract.effects,
        binding=binding,
    )
