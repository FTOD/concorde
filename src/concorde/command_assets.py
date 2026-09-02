"""Render root Concorde command sources into coding-agent command surfaces."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

from .frontmatter import FrontMatterError, parse_document


COMMAND_FILE = re.compile(r"^concorde(?:\.[a-z0-9-]+)+\.md$")
INTEGRATIONS = frozenset({"codex", "claude"})


class CommandAssetError(ValueError):
    """A canonical command cannot be projected safely."""


@dataclass(frozen=True)
class CommandPrompt:
    """One complete canonical command resolved for a source or installed package layout."""

    command_id: str
    description: str
    source_path: str
    body: str


def command_id(path: Path) -> str:
    if not COMMAND_FILE.fullmatch(path.name):
        raise CommandAssetError(f"invalid Concorde command filename: {path.name}")
    return path.stem


def skill_name(identifier: str) -> str:
    return identifier.replace(".", "-")


def target_path(identifier: str, integration: str) -> str:
    name = skill_name(identifier)
    if integration == "codex":
        return f".agents/skills/{name}/SKILL.md"
    if integration == "claude":
        return f".claude/skills/{name}/SKILL.md"
    raise CommandAssetError(f"unsupported command integration: {integration}")


def _framework_path(prefix: str, relative: str) -> str:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
        raise CommandAssetError(f"command script must be a safe package-relative path: {relative}")
    normalized_prefix = prefix.strip("/")
    return f"{normalized_prefix}/{candidate.as_posix()}" if normalized_prefix else candidate.as_posix()


def _frontmatter(identifier: str, description: str, integration: str, source: str) -> str:
    name = skill_name(identifier)
    values = [
        "---",
        f"name: {name}",
        f"description: {json.dumps(description)}",
    ]
    if integration == "claude":
        values.append('argument-hint: "Optional command guidance"')
    values.extend(
        [
            'compatibility: "Requires a Concorde project"',
            "metadata:",
            '  author: "concorde"',
            f"  source: {json.dumps(source)}",
        ]
    )
    if integration == "claude":
        values.extend(["user-invocable: true", "disable-model-invocation: false"])
    values.extend(["---", ""])
    return "\n".join(values)


def resolve_command_prompt(
    path: Path,
    framework_prefix: str = ".concorde/framework",
) -> CommandPrompt:
    """Resolve one canonical command without integration-specific skill metadata."""

    identifier = command_id(path)
    try:
        metadata, body = parse_document(path.read_text(encoding="utf-8"), path.as_posix())
    except (OSError, UnicodeError, FrontMatterError) as error:
        raise CommandAssetError(f"cannot read canonical command {path}: {error}") from error
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        raise CommandAssetError(f"command {identifier} requires a description")
    allowed = {"description", "scripts"}
    unknown = set(metadata) - allowed
    if unknown:
        raise CommandAssetError(f"command {identifier} has unsupported metadata: {sorted(unknown)}")
    scripts = metadata.get("scripts", {})
    if not isinstance(scripts, Mapping):
        raise CommandAssetError(f"command {identifier} scripts must be a mapping")
    script = scripts.get("py")
    if script is not None:
        if not isinstance(script, str) or not script.strip():
            raise CommandAssetError(f"command {identifier} scripts.py must be a string")
        executable, separator, arguments = script.strip().partition(" ")
        invocation = "python3 " + _framework_path(framework_prefix, executable)
        if separator:
            invocation += " " + arguments
        body = body.replace("{SCRIPT}", invocation)
    elif "{SCRIPT}" in body:
        raise CommandAssetError(f"command {identifier} uses {{SCRIPT}} without scripts.py")
    framework = framework_prefix.strip("/") or "."
    body = body.replace("{FRAMEWORK}", framework)
    if "{SCRIPT}" in body or "{FRAMEWORK}" in body:
        raise CommandAssetError(f"command {identifier} contains an unresolved package token")
    return CommandPrompt(
        command_id=identifier,
        description=description.strip(),
        source_path=f"commands/{path.name}",
        body=body,
    )


def load_command_prompt(
    package_root: str | Path,
    command_identifier: str,
    framework_prefix: str = ".concorde/framework",
) -> CommandPrompt:
    """Load one manifested command prompt from a safe Concorde package root."""

    if not isinstance(command_identifier, str) or not COMMAND_FILE.fullmatch(
        f"{command_identifier}.md"
    ):
        raise CommandAssetError(f"invalid Concorde command identity: {command_identifier!r}")
    root = Path(package_root)
    if root.is_symlink() or not root.is_dir():
        raise CommandAssetError(f"Concorde package root is missing, unsafe, or a symlink: {root}")
    manifest_path = root / "concorde.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise CommandAssetError(f"Concorde package manifest is missing or unsafe: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CommandAssetError(f"cannot read Concorde package manifest {manifest_path}: {error}") from error
    commands = manifest.get("commands") if isinstance(manifest, dict) else None
    if not isinstance(commands, list) or not all(isinstance(item, str) for item in commands):
        raise CommandAssetError(f"Concorde package manifest has no valid command inventory: {manifest_path}")
    if command_identifier not in commands:
        raise CommandAssetError(
            f"command {command_identifier} is not declared by {manifest_path.as_posix()}"
        )
    command_root = root / "commands"
    path = command_root / f"{command_identifier}.md"
    if command_root.is_symlink() or path.is_symlink():
        raise CommandAssetError(f"canonical command source may not be a symlink: {path}")
    if not command_root.is_dir() or not path.is_file():
        raise CommandAssetError(f"canonical command source is missing: {path}")
    return resolve_command_prompt(path, framework_prefix)


def render_command(path: Path, integration: str, framework_prefix: str = ".concorde/framework") -> str:
    if integration not in INTEGRATIONS:
        raise CommandAssetError(f"unsupported command integration: {integration}")
    prompt = resolve_command_prompt(path, framework_prefix)
    identifier = prompt.command_id
    heading = " ".join(part.capitalize() for part in skill_name(identifier).split("-"))
    return (
        _frontmatter(identifier, prompt.description, integration, prompt.source_path)
        + f"# {heading}\n\n"
        + prompt.body.lstrip()
    )


def render_commands(
    package_root: Path,
    integration: str,
    framework_prefix: str = ".concorde/framework",
) -> dict[str, str]:
    command_root = package_root / "commands"
    if command_root.is_symlink() or not command_root.is_dir():
        raise CommandAssetError(f"canonical command directory is missing: {command_root}")
    paths = sorted(command_root.glob("*.md"))
    if not paths or any(path.is_symlink() or not path.is_file() for path in paths):
        raise CommandAssetError("canonical commands must be regular Markdown files")
    rendered: dict[str, str] = {}
    identifiers: set[str] = set()
    for path in paths:
        identifier = command_id(path)
        if identifier in identifiers:
            raise CommandAssetError(f"duplicate command identity: {identifier}")
        identifiers.add(identifier)
        rendered[target_path(identifier, integration)] = render_command(
            path, integration, framework_prefix
        )
    return dict(sorted(rendered.items()))
