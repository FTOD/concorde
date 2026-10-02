"""The installer: place Concorde into a project without touching its Specs.

It copies the package's runtime (``src``, ``scripts``, ``prompts``, ``protocol`` and the rendered
``generated`` outputs) to ``.concorde/framework/``, with the docsite template under
``.concorde/framework/docsite/`` selected by Views' template inventory rule, writes the
``.concorde/bin/concorde`` command, the Protocol copy under ``.concorde/protocol/``, the main-session guidance as the project skill
``.claude/skills/concorde/SKILL.md`` (the build's rendered skill) and a delimited block in
``CLAUDE.md``, the project MCP server's entry ``concorde`` in ``.mcp.json``, Concorde-owned
defaults when absent, the pinned ``d2`` program under ``.concorde/tools/``, ignore rules for local
state and task worktrees, and a receipt ``.concorde/install.json``. ``uv`` owns Concorde's Python:
it creates Concorde's own environment under ``.concorde/framework/python/`` on an interpreter that
satisfies the package's ``runtime.python`` requirement, a uv-managed CPython when the machine has
none, and installs the locked runtime dependencies of the package's ``uv.lock`` there, such as
LangGraph. The installer also places the locked pi runtime
under ``.concorde/tools/pi-runtime/``, which every pi worker runs in (workers run on pi unless the
worker configuration chooses Claude Code). The main agent and its task sessions are Claude Code
sessions, so every rendered workflow is installed for Claude Code under ``.claude/workflows/``
with the permission rules its step agents need in ``.claude/settings.json``.
With ``develop`` it makes a develop install through the check the package descriptor names under
``develop`` (Dogfooding's): only from the clean primary worktree of a Concorde repository, with
Dogfooding's guidance added to the skill and the ``CLAUDE.md`` block. It reaches the parts only
through their registrations: the files, defaults, ignore rules and install services each part
contributes, and the idle checks it asks before replacing anything. It refuses a package whose build is stale and a project in which a
Concorde run is still running, and checks that ``uv`` and, when the pi runtime is still to be
installed, ``npm`` are on ``PATH`` before it writes anything; it then fetches and verifies ``d2``
before writing anything else, so only the installation of the pi runtime, the creation of the
environment and the installation of its dependencies can fail after the first write. It never
writes a Spec document, the registry or the project configuration.
"""

from __future__ import annotations

import hashlib
import contextlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import formats, parts
from .build import BuildError, skill_path, verify_fresh
from .project_defaults import (
    PROTOCOL_MANIFEST_PATH,
    CopyError,
    binding,
    project_default_files,
    protocol_files,
)
from .tools import ToolError, install_d2, install_pi_runtime, plan_pi_runtime

FRAMEWORK = ".concorde/framework"
# Concorde's own Python environment, a venv inside the framework copy that uv creates: installed
# Concorde never runs on the project's interpreter or with its packages, and the project never
# sees Concorde's.
OWN_PYTHON = f"{FRAMEWORK}/python"
COMMAND = ".concorde/bin/concorde"
SKILL = ".claude/skills/concorde/SKILL.md"
CLAUDE_MD = "CLAUDE.md"
CLAUDE_WORKFLOWS = ".claude/workflows"
CLAUDE_SETTINGS = ".claude/settings.json"
# The project's Claude Code MCP configuration, where the project MCP server is registered.
MCP_CONFIG = ".mcp.json"
MCP_SERVER = "concorde"
# What every workflow's Claude Code step agents use: the project MCP server's step tool, which
# runs each step as the server's own process so that the run outlives the step agent's short call,
# and the report command.
STEP_RULES = (
    f"mcp__{MCP_SERVER}__workflow_step",
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


def ignored(registrations: dict) -> tuple[str, ...]:
    """The ignore rules the parts contribute, in the order of their registrations."""
    found: list[str] = []
    for registration in parts.ordered(registrations):
        for line in registration.data["install"]["gitignore"]:
            if line not in found:
                found.append(line)
    return tuple(found)


class InstallError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# Refusals only a different request, project or source checkout can correct; every other refusal
# comes from the environment the installer runs in.
INPUT_CODES = frozenset(
    {
        "invalid_project",
        "invalid_descriptor",
        "stale_build",
        "invalid_docsite_template",
        "settings_invalid",
        "mcp_config_invalid",
        "not_installed",
        "update_source_missing",
        "develop_source_not_repository",
        "develop_source_not_primary",
        "develop_source_detached",
        "develop_source_dirty",
    }
)


def refusal(
    code: str, message: str, actor: str = "Installer (install-concorde)"
) -> dict:
    """A refusal of the installer or of `concorde update` as its link of an error chain."""
    if code in INPUT_CODES:
        reason = "input"
        explanation = (
            "the installer cannot correct the project, the Concorde checkout or the arguments "
            "it was given; whoever asked must change them"
        )
    else:
        reason = "environment"
        explanation = (
            "the installer cannot change what it runs among: running Concorde processes, the "
            "network, npm or uv"
        )
    return formats.link(actor, code, message, reason=reason, explanation=explanation)


def _guidance(package: Path, name: str) -> str:
    """The rendered skill ``concorde``, with its front matter, or another main-session render."""
    path = package / (
        skill_path("concorde")
        if name == "skill"
        else f"generated/main-session/{name}.md"
    )
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


def active_work(project: Path, registrations: dict) -> list[str]:
    """Everything the installed parts' idle checks report still running in ``project``, such as
    the execution part's runs whose runners hold their run locks."""
    found = []
    for registration in parts.ordered(registrations):
        check = registration.data["idle_check"]
        if check is not None:
            found += list(registration.entry(check)(project))
    return found


def _prepared(package: Path, project: Path, registrations: dict) -> dict[str, bytes]:
    """What the parts' ``install.prepare`` services place, decided before the first write, by
    project-relative path; a service's refusal refuses the install."""
    files: dict[str, bytes] = {}
    for registration in parts.ordered(registrations):
        prepare = registration.data["install"]["prepare"]
        if prepare is None:
            continue
        answer = registration.entry(prepare)(package, project)
        if "refusal" in answer:
            raise InstallError(answer["refusal"]["code"], answer["refusal"]["message"])
        files.update(answer["files"])
    return files


def _develop(package: Path) -> dict:
    """The develop source check the package descriptor names, refused with its code."""
    import importlib

    descriptor = json.loads((package / "concorde.json").read_text(encoding="utf-8"))
    entry = (descriptor.get("develop") or {}).get("check")
    if not isinstance(entry, str) or ":" not in entry:
        raise InstallError(
            "invalid_descriptor",
            f"{package / 'concorde.json'} names no develop check under develop.check",
        )
    module, attribute = entry.split(":", 1)
    answer = getattr(importlib.import_module(module), attribute)(package)
    if "refusal" in answer:
        raise InstallError(answer["refusal"]["code"], answer["refusal"]["message"])
    return answer


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


# Marks the part of the CLAUDE.md block that imports the project's glossary. Claude Code loads
# an `@path` import at launch with no size limit, which a SessionStart hook's output has not.
GLOSSARY_MARK = "<!-- concorde:glossary -->"


def declared_glossary(project: Path) -> str | None:
    """The glossary path the project's registry declares, or None when there is none to read."""
    try:
        registry = json.loads((project / ".concorde/specs.json").read_text("utf-8"))
    except (OSError, UnicodeError, ValueError, AttributeError, TypeError):
        return None
    modules = registry.get("modules") if isinstance(registry, dict) else None
    for record in modules if isinstance(modules, list) else ():
        if isinstance(record, dict) and isinstance(record.get("glossary"), str):
            return record["glossary"]
    return None


def with_glossary(block: str, project: Path) -> str:
    """The CLAUDE.md block with the import of the project's glossary, when it declares one."""
    block = block.split(GLOSSARY_MARK, 1)[0].rstrip("\n")
    path = declared_glossary(project)
    if path is None:
        return block
    return (
        f"{block}\n\n{GLOSSARY_MARK}\n"
        "The project's terms, each defined once in its glossary, which you use exactly as "
        f'defined (the skill\'s "Project terms"): @{path}'
    )


def refresh_glossary(project: Path) -> bool:
    """Bring the glossary import of an installed CLAUDE.md block up to date; whether it changed."""
    path = project / CLAUDE_MD
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        return False
    block = text.split(START, 1)[1].split(END, 1)[0]
    updated = with_glossary(block, project)
    if updated.strip() == block.strip():
        return False
    _amend(project, CLAUDE_MD, updated)
    return True


def _amend(project: Path, name: str, block: str) -> None:
    """Write ``block`` between the markers of ``name``, replacing an earlier block in place."""
    path = project / name
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


def _read_mcp_config(project: Path) -> dict:
    """The project's ``.mcp.json``, refused before any write when not a JSON object whose
    ``mcpServers`` is an object."""
    path = project / MCP_CONFIG
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise InstallError(
            "mcp_config_invalid",
            f"{path} cannot be read as JSON: {error}; nothing was written",
        ) from error
    if not isinstance(value, dict) or not isinstance(value.get("mcpServers", {}), dict):
        raise InstallError(
            "mcp_config_invalid",
            f"{path} is not a JSON object with an optional mcpServers object; nothing was "
            "written",
        )
    return value


def _register_server(project: Path, config: dict) -> None:
    """Register the project MCP server as ``concorde`` in ``.mcp.json``, keeping every other
    server; Claude Code starts it from the directory the session starts in, the project root."""
    servers = config.setdefault("mcpServers", {})
    entry = {"command": COMMAND, "args": ["project-mcp"]}
    if servers.get(MCP_SERVER) == entry:
        return
    servers[MCP_SERVER] = entry
    (project / MCP_CONFIG).write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )


def _ignore(project: Path, lines: tuple[str, ...]) -> None:
    path = project / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in lines if line not in text.splitlines()]
    if missing:
        prefix = "" if not text or text.endswith("\n") else "\n"
        path.write_text(text + prefix + "\n".join(missing) + "\n", encoding="utf-8")


def install(
    project: str | Path,
    package: str | Path,
    *,
    d2: bool = True,
    fetch: Callable[[str], bytes] | None = None,
    pi_runtime: bool = True,
    run: Callable | None = None,
    develop: bool = False,
    dependencies: bool = True,
) -> dict:
    """Install ``package`` into ``project``; return the receipt.

    With ``d2`` false the docsite's diagram program is left to the developer. ``fetch`` replaces
    the download of the pinned ``d2`` archive, for tests and offline mirrors. With
    ``pi_runtime`` (the default) the pi runtime every pi worker runs in is installed; without it
    workers can run only on Claude Code. ``run`` replaces the ``npm ci`` call and the ``uv`` calls that
    install the Python dependencies, never the creation of the environment. ``develop`` makes a
    develop install. With ``dependencies`` false Concorde's Python dependencies are left out of
    its environment, and the Operations that need them refuse.
    """
    project, package = Path(project).resolve(), Path(package).resolve()
    if not project.is_dir():
        raise InstallError("invalid_project", f"{project} is not a directory")
    try:
        verify_fresh(package)
    except BuildError as error:
        raise InstallError("stale_build", str(error)) from error
    try:
        registrations = parts.package_parts(package)
    except parts.RegistrationError as error:
        raise InstallError("stale_build", str(error)) from error
    prepared = _prepared(package, project, registrations)
    try:
        protocol = protocol_files(package) if "spec" in registrations else {}
    except CopyError as error:
        raise InstallError("stale_build", str(error)) from error
    skill = _guidance(package, "skill")
    block = _guidance(package, "claude-md")
    installed_from = None
    if develop:
        checked = _develop(package)
        installed_from = checked["source"]
        skill = skill.rstrip("\n") + "\n\n" + checked["guidance"]["skill"]
        block = block.rstrip("\n") + "\n\n" + checked["guidance"]["claude_md"]
    # Replacing the Framework copy under a running Operation or execution command would change
    # the code it runs halfway through. This is checked once and holds no lock: a run started
    # after it is the developer's to avoid, as Distribution's Spec says.
    running = active_work(project, registrations)
    if running:
        raise InstallError(
            "concorde_busy",
            f"Concorde is still running in {project}: {'; '.join(running)}. Wait until "
            "these end, or stop them, before installing or updating Concorde, and start no "
            "concorde command in the project until the install or update ends",
        )
    descriptor = json.loads((package / "concorde.json").read_text())
    requirement = _python_requirement(descriptor, package)
    settings = _read_settings(project)
    mcp_config = _read_mcp_config(project)
    previous = {}
    if (project / RECEIPT).is_file():
        try:
            previous = json.loads((project / RECEIPT).read_text())
        except ValueError:
            previous = {}
    placed = _rendered_workflows(package)
    # Every cheap precondition is checked before the first write: only the npm and uv steps
    # below, which the installer cannot foresee, can still fail once something was written.
    uv = shutil.which("uv")
    if uv is None:
        raise InstallError(
            "uv_missing",
            "Concorde's own Python environment is created, and its Python dependencies are "
            "installed, with uv, which is not on PATH; install uv "
            "(https://docs.astral.sh/uv/getting-started/installation/) and install again; "
            "nothing was written",
        )
    try:
        runtime_plan = plan_pi_runtime(project, package) if pi_runtime else None
    except ToolError as error:
        raise InstallError(error.code, str(error)) from error
    tools = {}
    try:
        if d2:
            try:
                tools["d2"] = install_d2(
                    project, descriptor, **({"fetch": fetch} if fetch else {})
                )
            except ToolError as error:
                raise InstallError(error.code, str(error)) from error
        if pi_runtime:
            try:
                tools["pi-runtime"] = install_pi_runtime(
                    project, package, plan=runtime_plan, **({"run": run} if run else {})
                )
            except ToolError as error:
                raise InstallError(error.code, str(error)) from error
        return _place(
            project,
            package,
            descriptor=descriptor,
            registrations=registrations,
            prepared=prepared,
            protocol=protocol,
            skill=skill,
            block=block,
            installed_from=installed_from,
            develop=develop,
            requirement=requirement,
            settings=settings,
            mcp_config=mcp_config,
            previous=previous,
            placed=placed,
            uv=uv,
            tools=tools,
            pi_runtime=pi_runtime,
            dependencies=dependencies,
            run=run,
        )
    except OSError as error:
        raise _failed_write("installing Concorde into", project, error) from error


def _failed_write(action: str, project: Path, error: OSError) -> InstallError:
    """A file operation that failed after the first write, which nothing rolls back."""
    return InstallError(
        "install_failed",
        f"{action} {project} failed: {error}. Nothing is rolled back: what the steps before it "
        f"wrote stays in place, and {RECEIPT} names the previous install unless the failure came "
        "after it was replaced; remove the cause and run the same command again, which repeats "
        "every step",
    )


def _place(
    project: Path,
    package: Path,
    *,
    descriptor: dict,
    registrations: dict,
    prepared: dict[str, bytes],
    protocol: dict[str, bytes],
    skill: str,
    block: str,
    installed_from: dict | None,
    develop: bool,
    requirement: str,
    settings: dict,
    mcp_config: dict,
    previous: dict,
    placed: dict[str, Path],
    uv: str,
    tools: dict,
    pi_runtime: bool,
    dependencies: bool,
    run: Callable | None,
) -> dict:
    """Place Concorde's files once every refusal was decided; return the receipt."""
    defaults = project_default_files(registrations)
    written = list(protocol)
    for path, content in protocol.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_bytes(content)
    for path, content in defaults.items():
        if not (project / path).exists():
            (project / path).parent.mkdir(parents=True, exist_ok=True)
            (project / path).write_bytes(content)
    _copy_runtime(package, project / FRAMEWORK)
    # What the parts' install services prepared, such as the spec part's docsite template under
    # the Framework copy, from which `concorde docsite --propose` scaffolds a project's site.
    for path, content in prepared.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_bytes(content)
    own_python = _own_python(project, uv, requirement)
    installed = (
        _python_dependencies(project, package, uv, run or subprocess.run)
        if dependencies
        else None
    )
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
    (project / SKILL).write_text(skill, encoding="utf-8")
    _amend(project, CLAUDE_MD, with_glossary(block, project))
    for path, source in placed.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, project / path)
    owned_rules = _settings(
        project,
        settings,
        _permission_rules(placed),
        list(previous.get("permissions") or []),
    )
    _register_server(project, mcp_config)
    _ignore(project, ignored(registrations))
    amended = [".gitignore", CLAUDE_MD, MCP_CONFIG] + (
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
        # The locked Python dependencies placed in Concorde's own environment, or None when the
        # install left them out.
        "dependencies": installed,
        "tools": tools,
        # What the developer chose, which `concorde update` keeps: whether the pi worker runtime
        # was left out.
        "pi_runtime": pi_runtime,
        # Every file Concorde owns, whether this install wrote it or found it in place: a
        # default is written only when absent, yet stays Concorde's.
        "files": sorted(
            {
                *written,
                *defaults,
                COMMAND,
                SKILL,
                *placed,
            }
        ),
        # Files of the project that the installer only amends: a delimited block, ignore
        # lines, permission rules. They stay the project's own files.
        "amended": amended,
        "permissions": owned_rules,
    }
    # Replaced whole, so that a failure leaves either the previous receipt or this one.
    partial = project / (RECEIPT + ".partial")
    partial.write_text(json.dumps(receipt, indent=2) + "\n")
    os.replace(partial, project / RECEIPT)
    # An initialized project keeps every installed file bound, those this install added too.
    for registration in parts.ordered(registrations):
        bind = registration.data["install"]["bind"]
        failed = registration.entry(bind)(project) if bind is not None else None
        if failed is not None:
            # Everything else is installed, so the install still succeeds; the result keeps the
            # part's account (Spec core's error record), which names any file a failed restore
            # left with new content, and validation reports what is left unbound.
            return {**receipt, "binding_error": failed}
    return receipt


def open_tasks(project: Path, registrations: dict) -> list[dict]:
    """What the installed parts' after-update entries report, the coordination part's open
    tasks; none without such a part."""
    found: list[dict] = []
    for registration in parts.ordered(registrations):
        entry = registration.data["after_update"]
        if entry is not None:
            found += list(registration.entry(entry)(project))
    return found


def _update_mark(project: Path) -> dict | None:
    """The mark of an earlier update not validated since, or None when there is none to read."""
    try:
        mark = json.loads((project / UPDATE_STATE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return (
        mark if isinstance(mark, dict) and mark.get("state") == "unvalidated" else None
    )


def update(
    project: str | Path,
    package: str | Path,
    *,
    fetch: Callable[[str], bytes] | None = None,
    run: Callable | None = None,
) -> dict:
    """Update the Concorde installed in ``project`` from ``package``.

    It installs as the first install did (keeping d2 and develop mode when they were installed),
    always with the pi worker runtime
    unless the first install left it out and with Concorde's own environment created again by
    uv for the new package's Python requirement, binds the
    new Protocol copy in the configuration, and marks the project Concorde unvalidated until a
    validation passes; open tasks keep the old Protocol copy until the primary branch is merged
    into them, so they are listed.
    """
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
        pi_runtime=previous.get("pi_runtime", True),
        run=run,
        develop=previous.get("mode") == "develop",
        dependencies=previous.get("dependencies", {}) is not None,
    )
    config_path = project / ".concorde/config.json"
    rebound = None
    try:
        if config_path.is_file():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            before = config.get("protocol")
            after = binding((project / PROTOCOL_MANIFEST_PATH).read_bytes())
            if before != after:
                config["protocol"] = after
                config_path.write_text(
                    json.dumps(config, indent=2) + "\n", encoding="utf-8"
                )
                rebound = {"from": before, "to": after}
        # A project still unvalidated since an earlier update keeps that update's before-state:
        # what has not been validated reaches back to it.
        earlier = _update_mark(project)
        if earlier is not None:
            if earlier.get("protocol"):
                rebound = {
                    "from": earlier["protocol"].get("from"),
                    "to": rebound["to"] if rebound else earlier["protocol"].get("to"),
                }
        state = {
            "state": "unvalidated",
            "from": (earlier or {}).get("from", previous.get("version")),
            "to": receipt["version"],
            # The version seldom changes between commits of a Concorde repository; the commits do.
            "commits": {
                "from": ((earlier or {}).get("commits") or {}).get(
                    "from", previous.get("source_commit")
                ),
                "to": receipt["source_commit"],
            },
            "protocol": rebound,
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        # Replaced whole, so that a failure leaves the earlier mark, if any, as it was.
        partial = project / (UPDATE_STATE + ".partial")
        try:
            partial.write_text(json.dumps(state, indent=2) + "\n")
            os.replace(partial, project / UPDATE_STATE)
        except OSError:
            with contextlib.suppress(OSError):
                partial.unlink(missing_ok=True)
            raise
    except OSError as error:
        raise _failed_write("updating Concorde in", project, error) from error
    tasks = open_tasks(project, parts.package_parts(Path(package).resolve()))
    return {
        "receipt": receipt,
        "update": state,
        "open_tasks": tasks,
        "next": [
            "commit the updated files",
            (
                "run `concorde spec-validation` and repair what it reports; the first validation "
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


def _python_requirement(descriptor: dict, package: Path) -> str:
    """The Python version requirement of the package, ``runtime.python`` of ``concorde.json``."""
    requirement = (descriptor.get("runtime") or {}).get("python")
    if not isinstance(requirement, str) or not requirement.strip():
        raise InstallError(
            "invalid_descriptor",
            f"{package / 'concorde.json'} names no Python version requirement under "
            "runtime.python, which Concorde's own environment is created for",
        )
    return requirement.strip()


# Prints the version and the real path of the interpreter a venv was made on.
_PROBE = "import os, sys; print(*sys.version_info[:3]); print(os.path.realpath(sys.executable))"


def _own_python(project: Path, uv: str, requirement: str) -> dict:
    """Create Concorde's own environment with ``uv`` for ``requirement``, replacing an earlier one.

    uv chooses an interpreter that satisfies the requirement, a uv-managed one or one of the
    machine's, and downloads a managed CPython when none is installed; ``--no-project`` keeps the
    project's own Python requirement out of the choice. The environment has no pip of its own.
    """
    target = project / OWN_PYTHON
    shutil.rmtree(target, ignore_errors=True)
    command = [uv, "venv", "--no-project", "--python", requirement, str(target)]
    try:
        made = subprocess.run(
            command,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise InstallError(
            "python_env_failed",
            f"`{' '.join(command)}` failed while creating Concorde's own Python environment: "
            f"{error}",
        ) from error
    interpreter = target / "bin/python"
    probe = (
        subprocess.run(
            [str(interpreter), "-E", "-s", "-c", _PROBE],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if made.returncode == 0 and interpreter.exists()
        else None
    )
    if probe is None or probe.returncode != 0:
        output = ((made.stdout or "") + (made.stderr or ""))[-2000:]
        if probe is not None:
            output += f"; {interpreter} then failed: {probe.stderr.strip()[-1000:]}"
        raise InstallError(
            "python_env_failed",
            f"`{' '.join(command)}` exited with {made.returncode} and left no interpreter "
            f"satisfying Python {requirement} at {interpreter}; its output ends with: "
            f"{output.strip() or '(empty)'}",
        )
    version, base = probe.stdout.splitlines()[:2]
    return {
        "environment": OWN_PYTHON,
        "requirement": requirement,
        "base": base,
        "version": ".".join(version.split()),
    }


REQUIREMENTS = f"{FRAMEWORK}/requirements.txt"


def _python_dependencies(project: Path, package: Path, uv: str, run: Callable) -> dict:
    """Install the package's locked Python dependencies into Concorde's own environment.

    ``uv export`` writes the runtime part of the package's ``uv.lock`` (no development group, no
    project itself) with every hash, and ``uv pip install --require-hashes`` installs exactly those
    versions; the environment has no pip of its own. A check that the environment imports every
    top-level dependency closes the step.
    """
    requirements = project / REQUIREMENTS
    interpreter = project / OWN_PYTHON / "bin/python"
    steps = [
        [
            uv,
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--project",
            str(package),
            "--output-file",
            str(requirements),
        ],
        [
            uv,
            "pip",
            "install",
            "--python",
            str(interpreter),
            "--require-hashes",
            "--no-deps",
            "-r",
            str(requirements),
        ],
        [str(interpreter), "-E", "-s", "-c", "import langgraph.graph"],
    ]
    for command in steps:
        try:
            completed = run(
                command, cwd=project, capture_output=True, text=True, timeout=900
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise InstallError(
                "python_dependencies_failed", f"`{' '.join(command)}` failed: {error}"
            ) from error
        if completed.returncode != 0:
            output = ((completed.stdout or "") + (completed.stderr or ""))[-2000:]
            raise InstallError(
                "python_dependencies_failed",
                f"`{' '.join(command)}` exited with {completed.returncode} while installing "
                f"Concorde's Python dependencies into {interpreter.parent.parent}; its output "
                f"ends with: {output.strip() or '(empty)'}",
            )
    lines = requirements.read_text().splitlines() if requirements.is_file() else []
    return {
        "requirements": REQUIREMENTS,
        "lock_sha256": hashlib.sha256((package / "uv.lock").read_bytes()).hexdigest(),
        "packages": sum(
            1 for line in lines if "==" in line and not line.startswith("#")
        ),
    }


def main(argv) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="install-concorde",
        description="Install or update Concorde in a project. Start no concorde command, in any "
        "worktree of the project, until the install ends: it is refused only for runs already "
        "running when it checks, and a command started meanwhile may load partly replaced code.",
    )
    parser.add_argument("project")
    parser.add_argument(
        "--without-d2",
        action="store_true",
        help="do not download d2; the docsite then needs d2 on PATH or in CONCORDE_D2",
    )
    parser.add_argument(
        "--without-pi-runtime",
        action="store_true",
        help="do not install the pi runtime (with npm) that pi workers run in; workers must "
        "then all run on Claude Code",
    )
    parser.add_argument(
        "--without-dependencies",
        action="store_true",
        help="do not install Concorde's Python dependencies (with uv); the Operations that "
        "need them, such as spec_panel, then refuse",
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
            receipt = update(arguments.project, package)
        else:
            receipt = install(
                arguments.project,
                package,
                d2=not arguments.without_d2,
                pi_runtime=not arguments.without_pi_runtime,
                develop=arguments.develop,
                dependencies=not arguments.without_dependencies,
            )
    except InstallError as error:
        sys.stdout.write(
            json.dumps({"error": refusal(error.code, str(error))}, indent=2) + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(receipt, indent=2) + "\n")
    return 0


__all__ = [
    "UPDATE_STATE",
    "InstallError",
    "active_work",
    "ignored",
    "install",
    "main",
    "open_tasks",
    "refusal",
    "update",
]
