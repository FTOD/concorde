"""Render root Concorde command sources into coding-agent command surfaces."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Mapping

from .frontmatter import FrontMatterError, parse_document


COMMAND_FILE = re.compile(r"^concorde(?:\.[a-z0-9-]+)+\.md$")
INTEGRATIONS = frozenset({"codex", "claude"})


class CommandAssetError(ValueError):
    """A canonical command cannot be projected safely."""


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


def render_command(path: Path, integration: str, framework_prefix: str = ".concorde/framework") -> str:
    if integration not in INTEGRATIONS:
        raise CommandAssetError(f"unsupported command integration: {integration}")
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
    heading = " ".join(part.capitalize() for part in skill_name(identifier).split("-"))
    source = f"commands/{path.name}"
    return _frontmatter(identifier, description.strip(), integration, source) + f"# {heading}\n\n" + body.lstrip()


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
