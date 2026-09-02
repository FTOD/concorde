"""Load and project Concorde leaf Skills and paired Operations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, Mapping

from .frontmatter import FrontMatterError, parse_document


SKILL_NAME = re.compile(r"^concorde-[a-z0-9]+(?:-[a-z0-9]+)*$")
INTEGRATIONS = frozenset({"codex", "claude"})
CapabilityKind = Literal["skill", "operation"]


class SkillAssetError(ValueError):
    """A canonical Skill or Operation cannot be loaded or projected safely."""


@dataclass(frozen=True)
class SkillPrompt:
    """One complete canonical capability resolved for a package layout."""

    name: str
    description: str
    source_path: str
    kind: CapabilityKind
    body: str
    operation: str | None = None
    skills: tuple[str, ...] = ()


def capability_name(path: Path) -> str:
    """Return the stable capability name owned by a canonical directory."""

    if path.name != "SKILL.md" or not SKILL_NAME.fullmatch(path.parent.name):
        raise SkillAssetError(f"invalid Concorde capability path: {path}")
    return path.parent.name


def target_path(name: str, integration: str) -> str:
    if not isinstance(name, str) or not SKILL_NAME.fullmatch(name):
        raise SkillAssetError(f"invalid Concorde capability name: {name!r}")
    if integration == "codex":
        return f".agents/skills/{name}/SKILL.md"
    if integration == "claude":
        return f".claude/skills/{name}/SKILL.md"
    raise SkillAssetError(f"unsupported capability integration: {integration}")


def _safe_relative(value: str, label: str) -> str:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts or "\\" in value:
        raise SkillAssetError(f"{label} must be a safe package-relative path: {value!r}")
    return candidate.as_posix()


def _framework_path(prefix: str, relative: str) -> str:
    relative = _safe_relative(relative, "capability entry point")
    normalized_prefix = prefix.strip("/")
    return f"{normalized_prefix}/{relative}" if normalized_prefix else relative


def _read_manifest(root: Path) -> dict[str, object]:
    manifest_path = root / "concorde.json"
    if root.is_symlink() or not root.is_dir():
        raise SkillAssetError(f"Concorde package root is missing, unsafe, or a symlink: {root}")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise SkillAssetError(f"Concorde package manifest is missing or unsafe: {manifest_path}")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillAssetError(f"cannot read Concorde package manifest {manifest_path}: {error}") from error
    if not isinstance(value, dict):
        raise SkillAssetError(f"Concorde package manifest must be an object: {manifest_path}")
    return value


def _inventory(manifest: Mapping[str, object], field: CapabilityKind | Literal["operations"]) -> tuple[str, ...]:
    key = "skills" if field == "skill" else "operations"
    value = manifest.get(key)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and SKILL_NAME.fullmatch(item) for item in value
    ):
        raise SkillAssetError(f"Concorde package manifest has no valid {key} inventory")
    if len(value) != len(set(value)):
        raise SkillAssetError(f"Concorde package manifest {key} inventory contains duplicates")
    return tuple(value)


def _canonical_source(name: str, kind: CapabilityKind) -> str:
    root = "skills" if kind == "skill" else "operations"
    return f"{root}/{name}/SKILL.md"


def _validate_body(name: str, body: str) -> None:
    if not body.strip():
        raise SkillAssetError(f"capability {name} requires a complete prompt body")
    if not any(line.startswith("# ") for line in body.splitlines()):
        raise SkillAssetError(f"capability {name} requires a level-one heading")


def resolve_skill_prompt(
    path: Path,
    kind: CapabilityKind,
    framework_prefix: str = ".concorde/framework",
) -> SkillPrompt:
    """Resolve one canonical leaf or Operation without integration metadata."""

    if kind not in {"skill", "operation"}:
        raise SkillAssetError(f"unsupported capability kind: {kind!r}")
    name = capability_name(path)
    if path.is_symlink() or not path.is_file():
        raise SkillAssetError(f"canonical capability source must be one real file: {path}")
    try:
        metadata, body = parse_document(path.read_text(encoding="utf-8"), path.as_posix())
    except (OSError, UnicodeError, FrontMatterError) as error:
        raise SkillAssetError(f"cannot read canonical capability {path}: {error}") from error

    declared_name = metadata.get("name")
    description = metadata.get("description")
    if declared_name != name:
        raise SkillAssetError(
            f"capability {name} must declare its directory name, found {declared_name!r}"
        )
    if not isinstance(description, str) or not description.strip():
        raise SkillAssetError(f"capability {name} requires a description")
    _validate_body(name, body)

    operation: str | None = None
    composed: tuple[str, ...] = ()
    if kind == "skill":
        allowed = {"name", "description", "scripts"}
        scripts = metadata.get("scripts", {})
        if not isinstance(scripts, Mapping):
            raise SkillAssetError(f"capability {name} scripts must be a mapping")
        unknown_scripts = set(scripts) - {"py"}
        if unknown_scripts:
            raise SkillAssetError(
                f"capability {name} has unsupported scripts: {sorted(unknown_scripts)}"
            )
        script = scripts.get("py")
        if script is not None:
            if not isinstance(script, str) or not script.strip():
                raise SkillAssetError(f"capability {name} scripts.py must be a string")
            executable, separator, arguments = script.strip().partition(" ")
            invocation = "python3 " + _framework_path(framework_prefix, executable)
            if separator:
                invocation += " " + arguments
            body = body.replace("{SCRIPT}", invocation)
        elif "{SCRIPT}" in body:
            raise SkillAssetError(f"capability {name} uses {{SCRIPT}} without scripts.py")
        if "{OPERATION}" in body:
            raise SkillAssetError(f"leaf Skill {name} may not use {{OPERATION}}")
    else:
        allowed = {"name", "description", "operation", "skills"}
        operation_value = metadata.get("operation")
        if operation_value != "operation.py":
            raise SkillAssetError(f"Operation {name} must declare operation: operation.py")
        skills_value = metadata.get("skills")
        if not isinstance(skills_value, list) or len(skills_value) < 2 or not all(
            isinstance(item, str) and SKILL_NAME.fullmatch(item) for item in skills_value
        ):
            raise SkillAssetError(f"Operation {name} must declare at least two valid Skills")
        if len(skills_value) != len(set(skills_value)):
            raise SkillAssetError(f"Operation {name} declares duplicate Skills")
        composed = tuple(skills_value)
        operation = _framework_path(framework_prefix, f"operations/{name}/operation.py")
        body = body.replace("{OPERATION}", "python3 " + operation)
        if "{SCRIPT}" in body:
            raise SkillAssetError(f"Operation {name} may not use {{SCRIPT}}")

    unknown = set(metadata) - allowed
    if unknown:
        raise SkillAssetError(f"capability {name} has unsupported metadata: {sorted(unknown)}")
    framework = framework_prefix.strip("/") or "."
    body = body.replace("{FRAMEWORK}", framework)
    unresolved = [token for token in ("{SCRIPT}", "{FRAMEWORK}", "{OPERATION}") if token in body]
    if unresolved:
        raise SkillAssetError(f"capability {name} contains unresolved package tokens: {unresolved}")
    return SkillPrompt(
        name=name,
        description=description.strip(),
        source_path=_canonical_source(name, kind),
        kind=kind,
        body=body,
        operation=operation,
        skills=composed,
    )


def _exact_directory(root: Path, name: str, kind: CapabilityKind) -> Path:
    directory = root / ("skills" if kind == "skill" else "operations") / name
    if directory.is_symlink() or not directory.is_dir():
        raise SkillAssetError(f"canonical {kind} directory is missing or unsafe: {directory}")
    allowed = {"SKILL.md"} if kind == "skill" else {"SKILL.md", "operation.py"}
    observed: set[str] = set()
    for path in directory.iterdir():
        if path.name == "__pycache__":
            continue
        if path.is_symlink() or not path.is_file():
            raise SkillAssetError(f"canonical {kind} contains an unsafe entry: {path}")
        if path.suffix in {".pyc", ".pyo"}:
            continue
        observed.add(path.name)
    if observed != allowed:
        raise SkillAssetError(
            f"canonical {kind} {name} must contain exactly {sorted(allowed)}, found {sorted(observed)}"
        )
    return directory / "SKILL.md"


def load_skill_prompt(
    package_root: str | Path,
    name: str,
    framework_prefix: str = ".concorde/framework",
) -> SkillPrompt:
    """Load one manifested leaf Skill or paired Operation from a safe package root."""

    if not isinstance(name, str) or not SKILL_NAME.fullmatch(name):
        raise SkillAssetError(f"invalid Concorde capability name: {name!r}")
    root = Path(package_root)
    manifest = _read_manifest(root)
    skills = _inventory(manifest, "skill")
    operations = _inventory(manifest, "operations")
    overlap = set(skills) & set(operations)
    if overlap:
        raise SkillAssetError(f"capability names must be globally unique: {sorted(overlap)}")
    if name in skills:
        kind: CapabilityKind = "skill"
    elif name in operations:
        kind = "operation"
    else:
        raise SkillAssetError(f"capability {name} is not declared by {root / 'concorde.json'}")
    prompt = resolve_skill_prompt(_exact_directory(root, name, kind), kind, framework_prefix)
    unknown = set(prompt.skills) - set(skills)
    if unknown:
        raise SkillAssetError(f"Operation {name} composes unknown Skills: {sorted(unknown)}")
    return prompt


def _projection_frontmatter(prompt: SkillPrompt, integration: str) -> str:
    values = [
        "---",
        f"name: {prompt.name}",
        f"description: {json.dumps(prompt.description)}",
    ]
    if integration == "claude":
        values.append('argument-hint: "Optional capability guidance"')
    values.extend(
        [
            'compatibility: "Requires a Concorde project"',
            "metadata:",
            '  author: "concorde"',
            f"  source: {json.dumps(prompt.source_path)}",
            f"  kind: {json.dumps(prompt.kind)}",
        ]
    )
    if prompt.operation is not None:
        values.append(f"  entrypoint: {json.dumps(prompt.operation)}")
    if integration == "claude":
        values.extend(["user-invocable: true", "disable-model-invocation: false"])
    values.extend(["---", ""])
    return "\n".join(values)


def render_skill(
    path: Path,
    integration: str,
    framework_prefix: str = ".concorde/framework",
    *,
    kind: CapabilityKind = "skill",
) -> str:
    """Render one canonical capability for a coding-agent integration."""

    if integration not in INTEGRATIONS:
        raise SkillAssetError(f"unsupported capability integration: {integration}")
    prompt = resolve_skill_prompt(path, kind, framework_prefix)
    return _projection_frontmatter(prompt, integration) + prompt.body.lstrip()


def render_capabilities(
    package_root: str | Path,
    integration: str,
    framework_prefix: str = ".concorde/framework",
) -> dict[str, str]:
    """Render the complete manifested Skill and Operation inventory."""

    if integration not in INTEGRATIONS:
        raise SkillAssetError(f"unsupported capability integration: {integration}")
    root = Path(package_root)
    manifest = _read_manifest(root)
    skills = _inventory(manifest, "skill")
    operations = _inventory(manifest, "operations")
    overlap = set(skills) & set(operations)
    if overlap:
        raise SkillAssetError(f"capability names must be globally unique: {sorted(overlap)}")

    for directory_name, declared in (("skills", skills), ("operations", operations)):
        capability_root = root / directory_name
        if capability_root.is_symlink() or not capability_root.is_dir():
            raise SkillAssetError(f"canonical capability directory is missing: {capability_root}")
        observed = sorted(
            path.name
            for path in capability_root.iterdir()
            if path.name != "__pycache__" and path.is_dir() and not path.is_symlink()
        )
        if observed != sorted(declared):
            raise SkillAssetError(
                f"Concorde manifest {directory_name} inventory differs from root {directory_name}/"
            )

    rendered: dict[str, str] = {}
    for name in (*skills, *operations):
        prompt = load_skill_prompt(root, name, framework_prefix)
        path = _exact_directory(root, name, prompt.kind)
        target = target_path(name, integration)
        if target in rendered:
            raise SkillAssetError(f"capability projection collision: {target}")
        rendered[target] = _projection_frontmatter(prompt, integration) + prompt.body.lstrip()
    return dict(sorted(rendered.items()))
