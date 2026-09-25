"""The installer: place Concorde into a project without touching its Specs.

It copies the package's runtime (``src``, ``scripts``, ``prompts``, ``protocol`` and the rendered
``generated`` outputs) to ``.concorde/framework/``, writes the ``.concorde/bin/concorde`` command,
the Protocol copy under ``.concorde/protocol/``, the main-session guidance as the project skill
``.claude/skills/concorde/SKILL.md`` and a delimited block in ``CLAUDE.md``, Concorde-owned
defaults when absent, the pinned ``d2`` program under ``.concorde/tools/``, ignore rules for local
state and task worktrees, and a receipt ``.concorde/install.json``. With ``pi`` it also places
the locked pi runtime under ``.concorde/tools/pi-runtime/``, Concorde's pi extension under
``.pi/extensions/concorde/`` and the guidance as the pi skill ``.pi/skills/concorde/SKILL.md``.
Every rendered workflow is installed for Claude Code under ``.claude/workflows/`` with the
permission rules its step agents need in ``.claude/settings.json``, and with ``pi`` under
``.concorde/workflows/pi/`` with the command-runner agents under ``.pi/agents/``.
It refuses a package whose build is stale, fetches
and verifies ``d2`` before writing anything else, and never writes a Spec document, the registry or
the project configuration.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

from .build import BuildError, verify_fresh
from .project_defaults import install_project_defaults, project_default_files
from .tools import TOOLS, ToolError, install_d2, install_pi_runtime

FRAMEWORK = ".concorde/framework"
COMMAND = ".concorde/bin/concorde"
SKILL = ".claude/skills/concorde/SKILL.md"
PI_SKILL = ".pi/skills/concorde/SKILL.md"
PI_EXTENSION = ".pi/extensions/concorde"
PI_EXTENSION_SOURCES = {
    "index.ts": "src/concorde/main_session/pi_extension.ts",
    "pi_runs.ts": "src/concorde/main_session/pi_runs.ts",
    "pi_models.ts": "src/concorde/main_session/pi_models.ts",
}
CLAUDE_MD = "CLAUDE.md"
CLAUDE_WORKFLOWS = ".claude/workflows"
CLAUDE_SETTINGS = ".claude/settings.json"
PI_WORKFLOWS = ".concorde/workflows/pi"
PI_AGENTS = ".pi/agents"
# The Bash commands every workflow's Claude Code step agents run.
STEP_RULES = (
    f"Bash({COMMAND} workflow step:*)",
    f"Bash({COMMAND} workflow report:*)",
)
RECEIPT = ".concorde/install.json"
START = "<!-- concorde:start -->"
END = "<!-- concorde:end -->"
RUNTIME = ("src", "scripts", "prompts", "protocol", "generated")
IGNORED = (
    ".concorde/runs/",
    ".concorde/tasks/",
    ".concorde/worker-models.json",
    ".concorde/framework/",
    f"{TOOLS}/",
    ".claude/worktrees/",
)
SKILL_DESCRIPTION = (
    "Work as Concorde's main agent in this project: split work into tasks, carry them out inside "
    "their worktrees or through task sessions, read results, keep decision logs and merge "
    "delivered work."
)
# The description is written as a JSON string, which YAML reads as a double-quoted scalar: its
# ": " would otherwise make the frontmatter invalid YAML, and pi drops a skill it cannot parse.
SKILL_HEADER = (
    f"---\nname: concorde\ndescription: {json.dumps(SKILL_DESCRIPTION)}\n---\n\n"
)


class InstallError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _guidance(package: Path, name: str) -> str:
    path = package / "generated/main-session" / f"{name}.md"
    if not path.is_file():
        raise InstallError("stale_build", f"{path} is missing; run the build")
    return path.read_text(encoding="utf-8")


def _copy_runtime(package: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "node_modules", ".pytest_cache"
    )
    for name in RUNTIME:
        source = package / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=ignore, symlinks=False)
    shutil.copy2(package / "concorde.json", target / "concorde.json")


def _claude_md(project: Path, block: str) -> None:
    path = project / CLAUDE_MD
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"{START}\n{block.strip()}\n{END}\n"
    if START in text and END in text:
        before, rest = text.split(START, 1)
        after = rest.split(END, 1)[1].lstrip("\n")
        text = before + section + after
    else:
        text = (text.rstrip("\n") + "\n\n" if text.strip() else "") + section
    path.write_text(text, encoding="utf-8")


def _rendered_workflows(package: Path) -> dict[str, Path]:
    """The build's workflow renders, by the path the installer places each at."""
    rendered = package / "generated/workflows"
    placed = {}
    for path in sorted((rendered / "claude").glob("*.js")):
        placed[f"{CLAUDE_WORKFLOWS}/{path.name}"] = path
    for path in sorted((rendered / "pi").glob("*.js")):
        placed[f"{PI_WORKFLOWS}/{path.name}"] = path
    for path in sorted((rendered / "pi/agents").glob("*.md")):
        placed[f"{PI_AGENTS}/{path.name}"] = path
    return placed


def _permission_rules(placed: dict[str, Path]) -> list[str]:
    names = [
        Path(path).stem for path in placed if path.startswith(f"{CLAUDE_WORKFLOWS}/")
    ]
    return [f"Workflow({name})" for name in names] + (list(STEP_RULES) if names else [])


def _read_settings(project: Path) -> dict:
    """The project's Claude Code settings, refused before any write when not a JSON object."""
    path = project / CLAUDE_SETTINGS
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InstallError(
            "settings_invalid",
            f"{path} cannot be read as JSON: {error}; nothing was written",
        ) from error
    permissions = value.get("permissions") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or not isinstance(permissions or {}, dict)
        or not isinstance((permissions or {}).get("allow", []), list)
    ):
        raise InstallError(
            "settings_invalid",
            f"{path} is not a JSON object with an optional permissions.allow list; nothing was "
            "written",
        )
    return value


def _settings(
    project: Path, settings: dict, rules: list[str], recorded: list[str]
) -> list[str]:
    """Add the missing rules, remove recorded ones no longer shipped; the rules Concorde owns."""
    permissions = settings.setdefault("permissions", {})
    before = list(permissions.get("allow", []))
    owned = [rule for rule in recorded if rule in rules]
    allow = [rule for rule in before if rule in rules or rule not in recorded]
    for rule in rules:
        if rule not in allow:
            allow.append(rule)
            owned.append(rule)
    if allow == before:
        return sorted(set(owned))
    permissions["allow"] = allow
    path = project / CLAUDE_SETTINGS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return sorted(set(owned))


def _ignore(project: Path) -> None:
    path = project / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in IGNORED if line not in text.splitlines()]
    if missing:
        prefix = "" if not text or text.endswith("\n") else "\n"
        path.write_text(text + prefix + "\n".join(missing) + "\n", encoding="utf-8")


def install(
    project: str | Path,
    package: str | Path,
    *,
    d2: bool = True,
    fetch: Callable[[str], bytes] | None = None,
    pi: bool = False,
    run: Callable | None = None,
) -> dict:
    """Install ``package`` into ``project``; return the receipt.

    With ``d2`` false the docsite's diagram program is left to the developer. ``fetch`` replaces
    the download of the pinned ``d2`` archive, for tests and offline mirrors. With ``pi`` the pi
    runtime, extension and skill are installed too; ``run`` replaces the ``npm ci`` call.
    """
    project, package = Path(project).resolve(), Path(package).resolve()
    if not project.is_dir():
        raise InstallError("invalid_project", f"{project} is not a directory")
    try:
        verify_fresh(package)
    except BuildError as error:
        raise InstallError("stale_build", str(error)) from error
    skill = _guidance(package, "skill")
    block = _guidance(package, "claude-md")
    descriptor = json.loads((package / "concorde.json").read_text())
    settings = _read_settings(project)
    previous = {}
    if (project / RECEIPT).is_file():
        try:
            previous = json.loads((project / RECEIPT).read_text())
        except ValueError:
            previous = {}
    placed = {
        path: source
        for path, source in _rendered_workflows(package).items()
        if pi or not path.startswith((PI_WORKFLOWS, PI_AGENTS))
    }
    tools = {}
    if d2:
        try:
            tools["d2"] = install_d2(
                project, descriptor, **({"fetch": fetch} if fetch else {})
            )
        except ToolError as error:
            raise InstallError(error.code, str(error)) from error
    if pi:
        try:
            tools["pi-runtime"] = install_pi_runtime(
                project, package, **({"run": run} if run else {})
            )
        except ToolError as error:
            raise InstallError(error.code, str(error)) from error
    written = install_project_defaults(project, package)
    _copy_runtime(package, project / FRAMEWORK)
    command = project / COMMAND
    command.parent.mkdir(parents=True, exist_ok=True)
    # A task worktree has no framework copy of its own (Git ignores it) unless the task
    # reinstalled Concorde there; it then runs the primary worktree's copy.
    command.write_text(
        "#!/usr/bin/env sh\n"
        'root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)\n'
        f'framework="$root/{FRAMEWORK}"\n'
        'if [ ! -d "$framework" ]; then\n'
        '  common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir) || exit 1\n'
        f'  framework="$(dirname -- "$common")/{FRAMEWORK}"\n'
        "fi\n"
        'exec python3 "$framework/scripts/concorde.py" "$@"\n'
    )
    command.chmod(0o755)
    (project / SKILL).parent.mkdir(parents=True, exist_ok=True)
    (project / SKILL).write_text(SKILL_HEADER + skill, encoding="utf-8")
    _claude_md(project, block)
    pi_files = []
    if pi:
        (project / PI_SKILL).parent.mkdir(parents=True, exist_ok=True)
        (project / PI_SKILL).write_text(SKILL_HEADER + skill, encoding="utf-8")
        extension = project / PI_EXTENSION
        extension.mkdir(parents=True, exist_ok=True)
        for name, source in PI_EXTENSION_SOURCES.items():
            shutil.copy2(package / source, extension / name)
        pi_files = [
            PI_SKILL,
            *(f"{PI_EXTENSION}/{name}" for name in PI_EXTENSION_SOURCES),
        ]
    for path, source in placed.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, project / path)
    owned_rules = _settings(
        project,
        settings,
        _permission_rules(placed),
        list(previous.get("permissions") or []),
    )
    _ignore(project)
    amended = [".gitignore", CLAUDE_MD] + (
        [CLAUDE_SETTINGS] if (project / CLAUDE_SETTINGS).exists() else []
    )
    receipt = {
        "version": descriptor["version"],
        "framework": FRAMEWORK,
        "command": COMMAND,
        "tools": tools,
        # Every file Concorde owns, whether this install wrote it or found it in place: a
        # default is written only when absent, yet stays Concorde's.
        "files": sorted(
            {
                *written,
                *project_default_files(package),
                COMMAND,
                SKILL,
                *pi_files,
                *placed,
            }
        ),
        # Files of the project that the installer only amends: a delimited block, ignore
        # lines, permission rules. They stay the project's own files.
        "amended": amended,
        "permissions": owned_rules,
    }
    (project / RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="install-concorde")
    parser.add_argument("project")
    parser.add_argument(
        "--without-d2",
        action="store_true",
        help="do not download d2; the docsite then needs d2 on PATH or in CONCORDE_D2",
    )
    parser.add_argument(
        "--pi",
        action="store_true",
        help="also install the pi runtime (with npm), Concorde's pi extension and the pi skill",
    )
    arguments = parser.parse_args(argv)
    package = Path(__file__).resolve().parents[3]
    try:
        receipt = install(
            arguments.project, package, d2=not arguments.without_d2, pi=arguments.pi
        )
    except InstallError as error:
        sys.stdout.write(
            json.dumps({"error": error.code, "message": str(error)}) + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(receipt, indent=2) + "\n")
    return 0


__all__ = ["InstallError", "install", "main"]
