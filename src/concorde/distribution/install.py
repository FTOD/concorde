"""The installer: place Concorde into a project without touching its Specs.

It copies the package's runtime (``src``, ``scripts``, ``prompts``, ``protocol`` and the rendered
``generated`` outputs) to ``.concorde/framework/``, writes the ``.concorde/bin/concorde`` command,
the Protocol copy under ``.concorde/protocol/``, the main-session guidance as the project skill
``.claude/skills/concorde/SKILL.md`` and a delimited block in ``CLAUDE.md``, Concorde-owned
defaults when absent, ignore rules for local state, and a receipt ``.concorde/install.json``. It
refuses a package whose build is stale and never writes a Spec document, the registry or the
project configuration.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .build import BuildError, verify_fresh
from .project_defaults import install_project_defaults

FRAMEWORK = ".concorde/framework"
COMMAND = ".concorde/bin/concorde"
SKILL = ".claude/skills/concorde/SKILL.md"
CLAUDE_MD = "CLAUDE.md"
RECEIPT = ".concorde/install.json"
START = "<!-- concorde:start -->"
END = "<!-- concorde:end -->"
RUNTIME = ("src", "scripts", "prompts", "protocol", "generated")
IGNORED = (".concorde/runs/", ".concorde/tasks/", ".concorde/framework/")
SKILL_HEADER = (
    "---\n"
    "name: concorde\n"
    "description: Work as Concorde's main agent in this project: split work into tasks, run "
    "Concorde Operations in task worktrees, read their results, keep decision logs and merge "
    "delivered work.\n"
    "---\n\n"
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


def _ignore(project: Path) -> None:
    path = project / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in IGNORED if line not in text.splitlines()]
    if missing:
        prefix = "" if not text or text.endswith("\n") else "\n"
        path.write_text(text + prefix + "\n".join(missing) + "\n", encoding="utf-8")


def install(project: str | Path, package: str | Path) -> dict:
    """Install ``package`` into ``project``; return the receipt."""
    project, package = Path(project).resolve(), Path(package).resolve()
    if not project.is_dir():
        raise InstallError("invalid_project", f"{project} is not a directory")
    try:
        verify_fresh(package)
    except BuildError as error:
        raise InstallError("stale_build", str(error)) from error
    skill = _guidance(package, "skill")
    block = _guidance(package, "claude-md")
    written = install_project_defaults(project, package)
    _copy_runtime(package, project / FRAMEWORK)
    command = project / COMMAND
    command.parent.mkdir(parents=True, exist_ok=True)
    command.write_text(
        "#!/usr/bin/env sh\n"
        'root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)\n'
        f'exec python3 "$root/{FRAMEWORK}/scripts/concorde.py" "$@"\n'
    )
    command.chmod(0o755)
    (project / SKILL).parent.mkdir(parents=True, exist_ok=True)
    (project / SKILL).write_text(SKILL_HEADER + skill, encoding="utf-8")
    _claude_md(project, block)
    _ignore(project)
    version = json.loads((package / "concorde.json").read_text())["version"]
    receipt = {
        "version": version,
        "framework": FRAMEWORK,
        "command": COMMAND,
        "files": sorted({*written, COMMAND, SKILL, CLAUDE_MD, ".gitignore"}),
    }
    (project / RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="install-concorde")
    parser.add_argument("project")
    arguments = parser.parse_args(argv)
    package = Path(__file__).resolve().parents[3]
    try:
        receipt = install(arguments.project, package)
    except InstallError as error:
        sys.stdout.write(
            json.dumps({"error": error.code, "message": str(error)}) + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(receipt, indent=2) + "\n")
    return 0


__all__ = ["InstallError", "install", "main"]
