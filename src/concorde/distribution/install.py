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
With ``develop`` it makes a develop install (see ``concorde.dogfooding.develop``): only from the
clean primary worktree of a Concorde repository, with Dogfooding's guidance added to the skill and
the ``CLAUDE.md`` block. It refuses a package whose build is stale and a project in which a
Concorde run is still running, fetches
and verifies ``d2`` before writing anything else, and never writes a Spec document, the registry or
the project configuration.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from ..dogfooding.develop import DevelopError, develop_source, guidance
from ..workflows.step import pid_alive
from .build import BuildError, verify_fresh
from .project_defaults import install_project_defaults, project_default_files
from .tools import TOOLS, ToolError, install_d2, install_pi_runtime

FRAMEWORK = ".concorde/framework"
# Concorde's own Python environment, a venv inside the framework copy: installed Concorde never
# runs on the project's interpreter or with its packages, and the project never sees Concorde's.
OWN_PYTHON = f"{FRAMEWORK}/python"
MINIMUM_PYTHON = (3, 11)
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
# Directories of ``scripts/`` that serve only the development of Concorde.
NOT_INSTALLED = ("e2e",)
# Written by `concorde update` and removed by the first validation that passes after it: the
# project is "Concorde unvalidated" until then. It is this checkout's state, never committed.
UPDATE_STATE = ".concorde/update.json"
IGNORED = (
    UPDATE_STATE,
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


def _source_commit(package: Path) -> str | None:
    """The commit ``package`` is checked out at, or ``None`` outside a Git checkout."""
    try:
        found = subprocess.run(
            ["git", "-C", str(package), "rev-parse", "--verify", "--quiet", "HEAD"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (found.stdout.strip() or None) if found.returncode == 0 else None


def active_runs(project: Path) -> list[str]:
    """Every Concorde run in ``project`` whose process still lives, described for a refusal:
    Operation runs from their progress files and pi task-session rounds from theirs."""
    found = []
    for path in sorted((project / ".concorde/runs").glob("*/status.json")):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            pid = int(state.get("host_pid") or 0)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if state.get("phase") != "finished" and pid_alive(pid):
            found.append(
                f"Operation run {state.get('run_id') or path.parent.name} "
                f"({state.get('operation')}, task {state.get('task')}, host process {pid}, "
                f"progress {path.relative_to(project).as_posix()})"
            )
    for path in sorted((project / ".concorde/tasks").glob("*.session/status.json")):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            pid = int(state.get("supervisor_pid") or 0)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if state.get("phase") == "running" and pid_alive(pid):
            found.append(
                f"round {state.get('round')} of the pi task session of task "
                f"{state.get('task')} (supervisor process {pid}, progress "
                f"{path.relative_to(project).as_posix()})"
            )
    return found


def _copy_runtime(package: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "node_modules", ".pytest_cache"
    )

    def runtime_ignore(directory, names):
        # End-to-end testing is how Concorde tests itself; it never reaches a user's project.
        skipped = set(ignore(directory, names))
        if Path(directory) == package / "scripts":
            skipped |= {name for name in names if name in NOT_INSTALLED}
        return skipped

    for name in RUNTIME:
        source = package / name
        if source.is_dir():
            shutil.copytree(
                source, target / name, ignore=runtime_ignore, symlinks=False
            )
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
    python: str | Path | None = None,
    develop: bool = False,
) -> dict:
    """Install ``package`` into ``project``; return the receipt.

    With ``d2`` false the docsite's diagram program is left to the developer. ``fetch`` replaces
    the download of the pinned ``d2`` archive, for tests and offline mirrors. With ``pi`` the pi
    runtime, extension and skill are installed too; ``run`` replaces the ``npm ci`` call.
    ``python`` is the interpreter Concorde's own environment is made from, the installer's own by
    default. ``develop`` makes a develop install.
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
    try:
        installed_from = develop_source(package) if develop else None
        if develop:
            section, paragraph = guidance(package)
            skill = skill.rstrip("\n") + "\n\n" + section
            block = block.rstrip("\n") + "\n\n" + paragraph
    except DevelopError as error:
        raise InstallError(error.code, str(error)) from error
    # Replacing the Framework copy under a running Operation or task session would change the
    # code it runs halfway through.
    running = active_runs(project)
    if running:
        raise InstallError(
            "concorde_busy",
            f"Concorde is still running in {project}: {'; '.join(running)}. Wait until "
            "these end, or stop them, before installing or updating Concorde",
        )
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
    own_python = _own_python(project, Path(python or sys.executable))
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
        # Nothing of the caller's Python setup reaches Concorde: an activated project venv, its
        # PYTHONPATH or the user's site-packages would otherwise decide what Concorde imports.
        f'python="$framework/{OWN_PYTHON[len(FRAMEWORK) + 1 :]}/bin/python"\n'
        'if [ ! -x "$python" ]; then\n'
        '  echo "concorde: its own Python environment $python is missing; install Concorde '
        'again" >&2\n'
        "  exit 1\n"
        "fi\n"
        "unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONSAFEPATH\n"
        'exec "$python" -E -s "$framework/scripts/concorde.py" "$@"\n'
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
        # The Concorde checkout installed from, which `concorde update` installs from again.
        "source": str(package),
        # A develop install runs a Concorde the developer also changes; see Dogfooding.
        "mode": "develop" if develop else "normal",
        # The commit installed, so that a report of a defect names the Concorde it was seen on.
        "source_commit": installed_from["commit"]
        if installed_from
        else _source_commit(package),
        "framework": FRAMEWORK,
        "command": COMMAND,
        "python": own_python,
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


def open_tasks(project: Path) -> list[dict]:
    """The tasks of ``project`` that have not ended, from their records."""
    found = []
    for path in sorted((project / ".concorde/tasks").glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            isinstance(record, dict)
            and isinstance(record.get("id"), str)
            and record.get("state") in ("open", "active", "delivered")
        ):
            found.append(
                {
                    "id": record["id"],
                    "branch": record.get("branch"),
                    "worktree": record.get("worktree"),
                }
            )
    return found


def update(
    project: str | Path,
    package: str | Path,
    *,
    python: str | Path | None = None,
    fetch: Callable[[str], bytes] | None = None,
    run: Callable | None = None,
) -> dict:
    """Update the Concorde installed in ``project`` from ``package``.

    It installs as the first install did (keeping d2, pi and develop mode when they were
    installed), binds the
    new Protocol copy in the configuration, and marks the project Concorde unvalidated until a
    validation passes; open tasks keep the old Protocol copy until the primary branch is merged
    into them, so they are listed.
    """
    from ..spec.initialize import installed_protocol_binding

    project = Path(project).resolve()
    try:
        previous = json.loads((project / RECEIPT).read_text())
    except (OSError, ValueError) as error:
        raise InstallError(
            "not_installed",
            f"{project} has no readable {RECEIPT} ({error}); install Concorde first",
        ) from error
    tools = previous.get("tools") or {}
    receipt = install(
        project,
        package,
        d2="d2" in tools,
        fetch=fetch,
        pi="pi-runtime" in tools,
        run=run,
        python=python or (previous.get("python") or {}).get("base"),
        develop=previous.get("mode") == "develop",
    )
    config_path = project / ".concorde/config.json"
    rebound = None
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        before = config.get("protocol")
        after = installed_protocol_binding(project)
        if before != after:
            config["protocol"] = after
            config_path.write_text(
                json.dumps(config, indent=2) + "\n", encoding="utf-8"
            )
            rebound = {"from": before, "to": after}
    state = {
        "state": "unvalidated",
        "from": previous.get("version"),
        "to": receipt["version"],
        "protocol": rebound,
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (project / UPDATE_STATE).write_text(json.dumps(state, indent=2) + "\n")
    tasks = open_tasks(project)
    return {
        "receipt": receipt,
        "update": state,
        "open_tasks": tasks,
        "next": [
            "commit the updated files",
            (
                "run `concorde validate` and repair what it reports; the first validation "
                "that passes marks the update validated"
            ),
        ]
        + (
            [
                (
                    "merge the primary branch into each open task, whose worktree still "
                    "carries the previous Protocol copy"
                )
            ]
            # Only a new Protocol copy makes an open task's own copy stale.
            if tasks and rebound
            else []
        ),
    }


def _own_python(project: Path, base: Path) -> dict:
    """Create Concorde's own environment from ``base``, replacing an earlier one."""
    probe = subprocess.run(
        [str(base), "-E", "-s", "-c", "import sys; print(*sys.version_info[:3])"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise InstallError(
            "python_unusable",
            f"{base} cannot run ({probe.stderr.strip() or f'exit {probe.returncode}'}); "
            "name another interpreter with --python",
        )
    version = tuple(int(part) for part in probe.stdout.split())
    if version[:2] < MINIMUM_PYTHON:
        raise InstallError(
            "python_too_old",
            f"{base} is Python {'.'.join(map(str, version))}, but Concorde needs "
            f"{'.'.join(map(str, MINIMUM_PYTHON))} or newer; name another interpreter with "
            "--python",
        )
    target = project / OWN_PYTHON
    shutil.rmtree(target, ignore_errors=True)
    made = subprocess.run(
        [str(base), "-E", "-s", "-m", "venv", "--without-pip", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if made.returncode != 0:
        raise InstallError(
            "python_env_failed",
            f"`{base} -m venv {target}` exited with {made.returncode}: "
            f"{made.stderr.strip()[-1000:]}",
        )
    return {
        "environment": OWN_PYTHON,
        "base": str(base),
        "version": ".".join(map(str, version)),
    }


def main(argv) -> int:
    import argparse

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
    parser.add_argument(
        "--python",
        help="the interpreter Concorde's own environment is made from (default: this one)",
    )
    parser.add_argument(
        "--develop",
        action="store_true",
        help="make a develop install from this Concorde repository's clean primary worktree",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="update an installed Concorde, as `concorde update` does",
    )
    arguments = parser.parse_args(argv)
    package = Path(__file__).resolve().parents[3]
    try:
        if arguments.update:
            receipt = update(arguments.project, package, python=arguments.python)
        else:
            receipt = install(
                arguments.project,
                package,
                d2=not arguments.without_d2,
                pi=arguments.pi,
                python=arguments.python,
                develop=arguments.develop,
            )
    except InstallError as error:
        sys.stdout.write(
            json.dumps({"error": error.code, "message": str(error)}) + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(receipt, indent=2) + "\n")
    return 0


__all__ = [
    "UPDATE_STATE",
    "InstallError",
    "active_runs",
    "install",
    "main",
    "open_tasks",
    "update",
]
