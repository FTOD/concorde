"""The installer: place Concorde's parts into a project without touching its Specs.

It installs the parts it is asked for with every part they depend on and Distribution, every part
when it is asked for none, and records them in the receipt. It copies the installed parts' runtime
(``concorde.json``, each part's code directory and the files its registration ships) to
``.concorde/framework/``, so that no code of another part reaches the project, with the spec part's
docsite template under ``.concorde/framework/docsite/`` selected by Views' template inventory rule,
writes the ``.concorde/bin/concorde`` command, the spec part's Protocol copy under
``.concorde/protocol/``, the guidance
composed of the installed parts' rendered sections as the project skill
``.claude/skills/concorde/SKILL.md``, a delimited block in ``CLAUDE.md`` and the task-session
prompt of its Framework copy, the project MCP server's entry ``concorde`` in ``.mcp.json``, Concorde-owned
defaults when absent, the pinned ``d2`` program under ``.concorde/tools/``, ignore rules for local
state and task worktrees, and a receipt ``.concorde/install.json``. ``uv`` owns Concorde's Python:
it creates Concorde's own environment under ``.concorde/framework/python/`` on an interpreter that
satisfies the package's ``runtime.python`` requirement, a uv-managed CPython when the machine has
none, and, where an installed part needs one, installs the locked runtime dependencies of the
package's ``uv.lock`` there, such as Method's LangGraph. With the worker harness part the installer
also places the locked pi runtime under ``.concorde/tools/pi-runtime/``, which every pi worker runs
in (workers run on pi unless the worker configuration chooses Claude Code), and with the spec part
the pinned ``d2``. The main agent and its task sessions are Claude Code sessions, so every rendered
workflow of the installed parts is installed for Claude Code under ``.claude/workflows/`` with the
permission rules its step agents need in ``.claude/settings.json``.
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
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

from . import formats, guidance, parts
from .build import BuildError, verify_fresh
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
RECEIPT = ".concorde/install.json"
START = "<!-- concorde:start -->"
END = "<!-- concorde:end -->"
# Where each part's code lies in the package and in the Framework copy.
SOURCE = "src/concorde"
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
        "unknown_part",
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


def _guidance(package: Path, registrations: dict) -> dict[str, str | None]:
    """The guidance composed of the rendered sections of the parts ``registrations`` holds, by
    kind (``skill``, ``task_session``, ``claude_md``), None for a kind no part contributes."""

    def read(path: str) -> str:
        if not (package / path).is_file():
            raise InstallError(
                "stale_build", f"{package / path} is missing; run the build"
            )
        return (package / path).read_text(encoding="utf-8")

    return {
        kind: guidance.compose(registrations, kind, read)
        for kind in parts.GUIDANCE_FIELDS
    }


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


# The parts without which a develop install's guidance would name what is not there.
DEVELOP_GUIDANCE_NEEDS = frozenset({"coordination", "issues"})


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


def shipped(registrations: dict) -> list[str]:
    """The package-relative paths the Framework copy of the given parts holds: each part's code
    directory and the files and directories its registration lists under ``install.files``, a
    directory ending with ``/``; the package descriptor first."""
    found = ["concorde.json"]
    for registration in parts.ordered(registrations):
        for path in (
            f"{SOURCE}/{registration.directory}/",
            *registration.data["install"]["files"],
        ):
            if path not in found:
                found.append(path)
    return found


def _copy_runtime(package: Path, target: Path, registrations: dict) -> None:
    """Replace the Framework copy with the runtime of the given parts alone, so that the code of a
    part that is not installed is not in the project at all."""
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "node_modules", ".pytest_cache"
    )
    for path in shipped(registrations):
        source = package / path.rstrip("/")
        (target / path).parent.mkdir(parents=True, exist_ok=True)
        if path.endswith("/"):
            shutil.copytree(source, target / path, ignore=ignore, symlinks=False)
        else:
            shutil.copy2(source, target / path)


def _missing_shipped(package: Path, registrations: dict) -> list[str]:
    """The shipped paths the package lacks, which a stale or incomplete build leaves out."""
    return [
        path
        for path in shipped(registrations)
        if not (
            (package / path.rstrip("/")).is_dir()
            if path.endswith("/")
            else (package / path).is_file()
        )
    ]


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


def _rendered_workflows(package: Path, registrations: dict) -> dict[str, Path]:
    """The build's workflow renders of the given parts, by the path the installer places each
    at: none without the workflow part, and otherwise each render whose every source in a part's
    code directory, as the build manifest records them, lies in one of those parts, so that a
    workflow comes with the part whose procedure it is."""
    if "workflow" not in registrations:
        return {}
    try:
        outputs = json.loads(
            (package / "generated/build-manifest.json").read_text(encoding="utf-8")
        )["outputs"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise InstallError(
            "stale_build", f"{package / 'generated/build-manifest.json'}: {error}"
        ) from error
    directories = {registration.directory for registration in registrations.values()}
    placed = {}
    for path in sorted((package / "generated/workflows/claude").glob("*.js")):
        record = outputs.get(path.relative_to(package).as_posix())
        sources = record.get("sources") if isinstance(record, dict) else None
        if not isinstance(sources, list):
            raise InstallError(
                "stale_build",
                f"the build manifest records no sources for {path}; run the build",
            )
        owners = {
            source.split("/")[2]
            for source in sources
            if isinstance(source, str) and source.startswith(f"{SOURCE}/")
        }
        if owners <= directories:
            placed[f"{CLAUDE_WORKFLOWS}/{path.name}"] = path
    return placed


def _permission_rules(placed: dict[str, Path], registrations: dict) -> list[str]:
    """``Workflow(<name>)`` for each placed workflow, then the rules the installed parts
    contribute, such as the workflow part's rules for its step agents, when a workflow is
    placed."""
    names = [
        Path(path).stem for path in placed if path.startswith(f"{CLAUDE_WORKFLOWS}/")
    ]
    if not names:
        return []
    rules = [f"Workflow({name})" for name in names]
    for registration in parts.ordered(registrations):
        for rule in registration.data["install"]["permissions"]:
            if rule not in rules:
                rules.append(rule)
    return rules


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


def _previous_parts(previous: dict, everything: dict) -> set[str]:
    """The parts an earlier receipt names, every part of the package when it names none, and
    none without an earlier receipt."""
    if not previous:
        return set()
    named = previous.get("parts")
    return set(named) if isinstance(named, dict) else set(everything)


def needs(registrations: dict, field: str) -> set[str]:
    """What the given parts need, the union of one of their install fields, such as the programs
    or the Python dependencies."""
    return {
        item
        for registration in registrations.values()
        for item in registration.data["install"][field]
    }


def install(
    project: str | Path,
    package: str | Path,
    *,
    part_names: Iterable[str] | None = None,
    d2: bool = True,
    fetch: Callable[[str], bytes] | None = None,
    pi_runtime: bool = True,
    run: Callable | None = None,
    develop: bool = False,
    dependencies: bool = True,
) -> dict:
    """Install ``package`` into ``project``; return the receipt.

    ``part_names`` names the parts to install, which come with every part they depend on and
    Distribution; every part of the package when it is None. With ``d2`` false the docsite's
    diagram program is left to the developer. ``fetch`` replaces the download of the pinned ``d2``
    archive, for tests and offline mirrors. With ``pi_runtime`` (the default) the pi runtime every
    pi worker runs in is installed where the worker harness part is; without it workers can run
    only on Claude Code. ``run`` replaces the ``npm ci`` call and the ``uv`` calls that install
    the Python dependencies, never the creation of the environment. ``develop`` makes a develop
    install. With ``dependencies`` false Concorde's Python dependencies are left out of its
    environment, and the Operations that need them refuse; they are installed only where an
    installed part needs one.
    """
    project, package = Path(project).resolve(), Path(package).resolve()
    if not project.is_dir():
        raise InstallError("invalid_project", f"{project} is not a directory")
    try:
        verify_fresh(package)
    except BuildError as error:
        raise InstallError("stale_build", str(error)) from error
    try:
        everything = parts.package_parts(package)
        registrations = parts.closure(
            everything, everything if part_names is None else list(part_names)
        )
    except parts.RegistrationError as error:
        raise InstallError(
            "unknown_part" if error.code == "unknown_part" else "stale_build",
            str(error),
        ) from error
    missing = _missing_shipped(package, registrations)
    if missing:
        raise InstallError(
            "stale_build",
            f"{package} lacks {', '.join(missing)}, which the installed parts ship; run the "
            "build",
        )
    prepared = _prepared(package, project, registrations)
    try:
        protocol = protocol_files(package) if "spec" in registrations else {}
    except CopyError as error:
        raise InstallError("stale_build", str(error)) from error
    composed = _guidance(package, registrations)
    skill, block = composed["skill"] or "", composed["claude_md"] or ""
    installed_from = None
    if develop:
        checked = _develop(package)
        installed_from = checked["source"]
        # Dogfooding's guidance has the main agent report defects as Issues through its tasks,
        # so it is composed only where the coordination and issues parts are installed.
        if DEVELOP_GUIDANCE_NEEDS <= set(registrations):
            skill = skill.rstrip("\n") + "\n\n" + checked["guidance"]["skill"]
            block = block.rstrip("\n") + "\n\n" + checked["guidance"]["claude_md"]
    previous = {}
    if (project / RECEIPT).is_file():
        try:
            previous = json.loads((project / RECEIPT).read_text())
        except ValueError:
            previous = {}
    previous = previous if isinstance(previous, dict) else {}
    # Replacing the Framework copy under a running Operation or execution command would change
    # the code it runs halfway through. This is checked once and holds no lock: a run started
    # after it is the developer's to avoid, as Distribution's Spec says. The parts installed until
    # now are asked too, since their work may run under a copy this install replaces.
    asked = {
        name: everything[name]
        for name in _previous_parts(previous, everything) | set(registrations)
        if name in everything
    }
    running = active_work(project, asked)
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
    placed = _rendered_workflows(package, registrations)
    programs = needs(registrations, "programs")
    with_d2 = d2 and "d2" in programs
    with_pi_runtime = pi_runtime and "pi-runtime" in programs
    python_dependencies = sorted(needs(registrations, "python_dependencies"))
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
        runtime_plan = plan_pi_runtime(project, package) if with_pi_runtime else None
    except ToolError as error:
        raise InstallError(error.code, str(error)) from error
    tools = {}
    try:
        if with_d2:
            try:
                tools["d2"] = install_d2(
                    project, descriptor, **({"fetch": fetch} if fetch else {})
                )
            except ToolError as error:
                raise InstallError(error.code, str(error)) from error
        if with_pi_runtime:
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
            everything=everything,
            prepared=prepared,
            protocol=protocol,
            skill=skill,
            block=block,
            task_session=composed["task_session"],
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
            python_dependencies=python_dependencies if dependencies else [],
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
    everything: dict,
    prepared: dict[str, bytes],
    protocol: dict[str, bytes],
    skill: str,
    block: str,
    task_session: str | None,
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
    python_dependencies: list[str],
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
    _copy_runtime(package, project / FRAMEWORK, registrations)
    # The task-session prompt Coordination reads from its Framework copy, composed of the
    # installed parts' sections in place of the build's composition of every part.
    prompt = project / FRAMEWORK / guidance.TASK_SESSION
    if task_session is None:
        prompt.unlink(missing_ok=True)
    else:
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(task_session, encoding="utf-8")
    # What the parts' install services prepared, such as the spec part's docsite template under
    # the Framework copy, from which `concorde docsite --propose` scaffolds a project's site.
    for path, content in prepared.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_bytes(content)
    own_python = _own_python(project, uv, requirement)
    installed = (
        _python_dependencies(
            project, package, uv, run or subprocess.run, python_dependencies
        )
        if python_dependencies
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
    # The glossary import belongs to the spec part, which alone declares a glossary.
    _amend(
        project,
        CLAUDE_MD,
        with_glossary(block, project) if "spec" in registrations else block,
    )
    for path, source in placed.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, project / path)
    owned_rules = _settings(
        project,
        settings,
        _permission_rules(placed, registrations),
        list(previous.get("permissions") or []),
    )
    _register_server(project, mcp_config)
    _ignore(project, ignored(registrations))
    earlier = [
        path
        for path in previous.get("files") or []
        if isinstance(path, str)
        and not path.startswith("/")
        and ".." not in Path(path).parts
    ]
    # A Concorde-owned default holds the project's own data: once an install wrote or found it,
    # it stays Concorde's while it is in place, whether or not the parts now installed, or this
    # package, still declare it. An earlier receipt names its defaults; one written before it
    # did is read through the defaults this package declares.
    recorded = {path for path in previous.get("defaults") or [] if path in earlier} | {
        path for path in project_default_files(everything) if path in earlier
    }
    kept = set(defaults) | {path for path in recorded if (project / path).is_file()}
    owned = {*written, *kept, COMMAND, SKILL, *placed}
    # What an earlier install owned and this one no longer ships, such as the workflows of a part
    # it leaves out, goes; a default stays.
    for path in earlier:
        if path not in owned and path not in recorded:
            (project / path).unlink(missing_ok=True)
    amended = [".gitignore", CLAUDE_MD, MCP_CONFIG] + (
        [CLAUDE_SETTINGS] if (project / CLAUDE_SETTINGS).exists() else []
    )
    receipt = {
        "version": descriptor["version"],
        # The installed parts, each with the one version every part carries, which
        # `concorde update` installs again.
        "parts": {name: descriptor["version"] for name in sorted(registrations)},
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
        "files": sorted(owned),
        # Those of them that are Concorde-owned defaults, which no later install removes.
        "defaults": sorted(kept),
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


def _left_out(previous: dict, earlier: dict) -> dict[str, bool]:
    """What an earlier install left out by the developer's choice, which an update keeps: d2 or
    the Python dependencies only when a part it installed, one of ``earlier``, needed them and it
    placed none, the pi runtime when its receipt records that choice. A choice that changed
    nothing is not recorded, so the program or dependencies come with a part added later."""
    return {
        "d2": "d2" in needs(earlier, "programs")
        and "d2" not in (previous.get("tools") or {}),
        "dependencies": bool(needs(earlier, "python_dependencies"))
        and previous.get("dependencies", {}) is None,
        "pi_runtime": previous.get("pi_runtime", True) is False,
    }


def update(
    project: str | Path,
    package: str | Path,
    *,
    part_names: Iterable[str] = (),
    fetch: Callable[[str], bytes] | None = None,
    run: Callable | None = None,
) -> dict:
    """Update the Concorde installed in ``project`` from ``package``.

    It installs exactly the parts the receipt names (every part when it names none), with every
    part the new package makes one of them depend on and the parts ``part_names`` adds, as the
    first install did (keeping d2, the Python dependencies and the pi runtime left out when the
    first install left them out, and develop mode), with Concorde's own environment created again
    by uv for the new package's Python requirement. Where the spec part is installed it binds the
    new Protocol copy in the configuration and marks the project Concorde unvalidated until a
    validation passes; open tasks keep the old Protocol copy until the primary branch is merged
    into them, so they are listed.
    """
    project, package = Path(project).resolve(), Path(package).resolve()
    try:
        previous = json.loads((project / RECEIPT).read_text())
        if not isinstance(previous, dict):
            raise ValueError("the receipt is not a JSON object")
    except (OSError, ValueError) as error:
        raise InstallError(
            "not_installed",
            f"{project} has no readable {RECEIPT} ({error}); install Concorde first",
        ) from error
    try:
        everything = parts.package_parts(package)
    except parts.RegistrationError as error:
        raise InstallError("stale_build", str(error)) from error
    earlier = _previous_parts(previous, everything)
    named = sorted(earlier | set(part_names))
    left_out = _left_out(
        previous, {name: everything[name] for name in earlier if name in everything}
    )
    receipt = install(
        project,
        package,
        part_names=named,
        d2=not left_out["d2"],
        fetch=fetch,
        pi_runtime=not left_out["pi_runtime"],
        run=run,
        develop=previous.get("mode") == "develop",
        dependencies=not left_out["dependencies"],
    )
    installed = {name: everything[name] for name in receipt["parts"]}
    state = None
    rebound = None
    # The Protocol copy, its binding and the update mark that validation removes are the spec
    # part's: without it there is nothing to rebind and no validation to wait for.
    if "spec" in installed:
        state, rebound = _rebind_and_mark(project, previous, receipt)
    tasks = open_tasks(project, installed)
    return {
        "receipt": receipt,
        "update": state,
        "open_tasks": tasks,
        "next": ["commit the updated files"]
        + (
            [
                (
                    "run `concorde spec-validation` and repair what it reports; the first "
                    "validation that passes marks the update validated"
                )
            ]
            if state is not None
            else []
        )
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


def _rebind_and_mark(
    project: Path, previous: dict, receipt: dict
) -> tuple[dict, dict | None]:
    """Bind the new Protocol copy in the configuration and write the update mark; the mark and
    the rebinding it records."""
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
    return state, rebound


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


def _python_dependencies(
    project: Path, package: Path, uv: str, run: Callable, names: list[str]
) -> dict:
    """Install the package's locked Python dependencies into Concorde's own environment, for the
    installed parts that need the dependencies ``names``.

    ``uv export`` writes the runtime part of the package's ``uv.lock`` (no development group, no
    project itself) with every hash, and ``uv pip install --require-hashes`` installs exactly those
    versions; the environment has no pip of its own. A check that the environment imports every
    dependency the installed parts need closes the step.
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
        [
            str(interpreter),
            "-E",
            "-s",
            "-c",
            "; ".join(f"import {name.replace('-', '_')}" for name in names),
        ],
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


def split_parts(values: list[str] | None) -> list[str] | None:
    """The part names of every ``--parts`` value, each a comma-separated list; None for none."""
    if not values:
        return None
    return [
        name.strip() for value in values for name in value.split(",") if name.strip()
    ]


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
        "--parts",
        action="append",
        metavar="PART[,PART...]",
        help="install only these parts, by the names of Distribution's parts table (quote "
        "'worker harness'), with every part they depend on and Distribution; every part when "
        "left out. With --update, parts to add to those the receipt names",
    )
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
    named = split_parts(arguments.parts)
    try:
        if arguments.update:
            receipt = update(arguments.project, package, part_names=named or ())
        else:
            receipt = install(
                arguments.project,
                package,
                part_names=named,
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
    "shipped",
    "split_parts",
    "update",
]
