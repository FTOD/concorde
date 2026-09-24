"""Worker model configuration: which model and reasoning level workers of each task type use.

The configuration is the file ``.concorde/worker-models.json`` of one worktree. Git ignores it: it
names models of this machine's Claude Code or pi installation, and it belongs to the worktree, not
to the branch. ``concorde task open`` copies the primary worktree's file into a new task worktree,
so a task starts with the configuration of its creation and keeps its own copy; later changes in
the primary worktree never reach an existing task, and a task's copy changes only when a command
names it. For each backend it holds a default and optional overrides per task type; an override
replaces only the fields it sets.

The backend is not configured: workers run on the agent program of the main session that started
the run (``client``), Claude Code or pi. Mixing a main session of one with workers of the other is
future work.

``concorde workers models|show|set|unset`` prints one JSON value; refusals print
``{"error": <error link>}`` and exit 1, a malformed command line exits 2.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import errors
from ..spec.schema import ContractError, validate
from .settings import TOOL_SETS

CONFIG = ".concorde/worker-models.json"
SCHEMA_VERSION = 1
CLIENTS = ("claude", "pi")
TASK_TYPES = tuple(TOOL_SETS)
# The command-line flag each backend takes the reasoning level with.
REASONING_FLAG = {"claude": "--effort", "pi": "--thinking"}
# The levels each program documents today, used when its --help cannot be read.
LEVELS = {
    "claude": ("low", "medium", "high", "xhigh", "max"),
    "pi": ("off", "minimal", "low", "medium", "high", "xhigh", "max"),
}
# Claude Code resolves these aliases for the account it is signed in to; it cannot list models.
CLAUDE_ALIASES = (
    (
        "fable",
        "the Fable model of the account's provider, for the hardest and longest work",
    ),
    ("opus", "the latest Opus model of the account's provider, for complex reasoning"),
    ("sonnet", "the latest Sonnet model of the account's provider, for daily coding"),
    ("haiku", "the fast Haiku model, for simple tasks"),
    ("opus[1m]", "Opus with a one million token context window"),
)
CLAUDE_PINNED = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
)
TIMEOUT = 60.0

TEXT = {"type": "string", "minLength": 1}
SELECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"model": TEXT, "reasoning": TEXT},
    "anyOf": [{"required": ["model"]}, {"required": ["reasoning"]}],
}
BACKEND_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "default": SELECTION_SCHEMA,
        "task_types": {
            "type": "object",
            "additionalProperties": False,
            "properties": {name: SELECTION_SCHEMA for name in TASK_TYPES},
        },
    },
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        **{name: BACKEND_SCHEMA for name in CLIENTS},
    },
}


class ModelConfigError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# Client detection ---------------------------------------------------------------------------


def detect_client(environ=None) -> tuple[str, str]:
    """The main session's agent program and the variable that told it.

    ``CONCORDE_CLIENT`` wins; Concorde's pi extension sets it to ``pi`` in the pi session. Then
    ``CLAUDECODE=1``, which Claude Code sets for its commands, and pi's own session variables.
    """
    environ = os.environ if environ is None else environ
    named = environ.get("CONCORDE_CLIENT", "").strip()
    if named:
        if named not in CLIENTS:
            raise ModelConfigError(
                "invalid_client",
                f"CONCORDE_CLIENT is {named!r}; Concorde knows the clients "
                f"{', '.join(CLIENTS)}",
            )
        return named, f"CONCORDE_CLIENT={named}"
    if environ.get("CLAUDECODE") == "1":
        return "claude", "CLAUDECODE=1"
    for name in ("PI_SESSION_ID", "PI_CODING_AGENT"):
        if environ.get(name):
            return "pi", f"{name} is set"
    raise ModelConfigError(
        "client_unknown",
        "the command was not started from a Claude Code or pi main session: CONCORDE_CLIENT is "
        "unset, CLAUDECODE is not 1 and neither PI_SESSION_ID nor PI_CODING_AGENT is set. Workers "
        "run on the main session's own agent program, so it must be known",
    )


# The configuration file ----------------------------------------------------------------------


def config_path(worktree: Path) -> Path:
    return Path(worktree) / CONFIG


def load(worktree: Path) -> dict:
    """The worktree's configuration; an absent file is an empty configuration."""
    path = config_path(worktree)
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ModelConfigError(
            "config_invalid", f"{path} cannot be read as JSON: {error}"
        ) from error
    try:
        validate(value, SCHEMA)
    except ContractError as error:
        raise ModelConfigError(
            "config_invalid",
            f"{path} does not match the worker model configuration: {error}",
        ) from error
    return value


def save(worktree: Path, value: dict) -> Path:
    validate(value, SCHEMA)
    path = config_path(worktree)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".worker-models.")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)
    return path


def selection(config: dict, backend: str, task_type: str) -> dict:
    """The model and reasoning level for one task type, and where each came from."""
    section = config.get(backend) or {}
    default = section.get("default") or {}
    override = (section.get("task_types") or {}).get(task_type) or {}
    chosen = {}
    for field in ("model", "reasoning"):
        if field in override:
            chosen[field] = override[field]
            chosen[f"{field}_source"] = f"{backend}.task_types.{task_type}"
        elif field in default:
            chosen[field] = default[field]
            chosen[f"{field}_source"] = f"{backend}.default"
        else:
            chosen[field] = None
            chosen[f"{field}_source"] = "the backend's own default"
    return chosen


def inherit(primary: Path, worktree: Path) -> str | None:
    """Copy the primary worktree's configuration into a new task worktree, if it has one."""
    source = config_path(primary)
    if not source.is_file():
        return None
    target = config_path(worktree)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target.as_posix()


# Discovering the candidates -------------------------------------------------------------------


def _program(backend: str, environ) -> str | None:
    named = environ.get("CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI")
    name = named or backend
    if os.path.isabs(name):
        return name if os.access(name, os.X_OK) else None
    return shutil.which(name, path=environ.get("PATH"))


def _run(argv: list[str], environ) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env=dict(environ),
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ModelConfigError(
            "discovery_failed",
            f"{' '.join(argv)} did not finish within {TIMEOUT:.0f}s",
        ) from error
    except OSError as error:
        raise ModelConfigError(
            "discovery_failed", f"{' '.join(argv)} could not start: {error}"
        ) from error


def _levels(backend: str, program: str, environ) -> list[str]:
    """The reasoning levels the program's --help lists, or the documented ones."""
    help_text = _run([program, "--help"], environ).stdout
    flag = re.escape(REASONING_FLAG[backend])
    found = re.search(
        flag + r"\s+<level>\s+.*?(?:\(|:\s*)([a-z]+(?:,\s*[a-z]+)+)",
        help_text,
        re.DOTALL,
    )
    if not found:
        return list(LEVELS[backend])
    return [item.strip() for item in found.group(1).split(",")]


def _version(program: str, environ) -> str:
    done = _run([program, "--version"], environ)
    lines = (done.stdout or done.stderr).strip().splitlines()
    return lines[-1].strip() if lines else ""


def _claude_settings(environ) -> tuple[Path, dict]:
    base = environ.get("CLAUDE_CONFIG_DIR")
    path = (
        Path(base) if base else Path(environ.get("HOME") or Path.home()) / ".claude"
    ) / ("settings.json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return path, {}
    return path, value if isinstance(value, dict) else {}


def _claude_models(levels: list[str], environ) -> tuple[list[dict], str]:
    path, settings = _claude_settings(environ)
    allowed = settings.get("availableModels")
    allowed = (
        [item for item in allowed if isinstance(item, str)]
        if isinstance(allowed, list)
        else None
    )
    models: list[dict] = []

    def add(model_id: str, source: str, note: str = "") -> None:
        if model_id and all(item["id"] != model_id for item in models):
            models.append(
                {
                    "id": model_id,
                    "source": source,
                    "reasoning": True,
                    "levels": list(levels),
                    "note": note,
                }
            )

    for alias, note in CLAUDE_ALIASES:
        if allowed is None or alias in allowed:
            add(alias, "Claude Code alias", note)
    for item in allowed or []:
        add(item, f"availableModels of {path}")
    if isinstance(settings.get("model"), str):
        add(
            settings["model"], f"model of {path}", "the main session's configured model"
        )
    for name in CLAUDE_PINNED:
        if environ.get(name):
            add(
                environ[name],
                f"environment variable {name}",
                "workers do not receive this variable, so the full name is passed",
            )
    note = (
        "Claude Code has no command that lists the models of the signed-in account, so this list "
        "holds its aliases and the models named in your settings and environment. A full model "
        "name such as claude-opus-5-5 also works; configure it with --allow-unlisted."
    )
    if allowed is not None:
        note += f" Only the aliases in availableModels of {path} are listed."
    return models, note


PI_ROW = re.compile(
    r"^(?P<provider>\S+)\s+(?P<model>\S+)\s+(?P<context>\S+)\s+(?P<max_out>\S+)\s+"
    r"(?P<thinking>yes|no)\s+(?P<images>yes|no)\s*$"
)


def _pi_models(program: str, levels: list[str], environ) -> tuple[list[dict], str]:
    quiet = dict(environ)
    quiet.update({"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"})
    argv = [program, "--no-extensions", "--list-models"]
    done = _run(argv, quiet)
    if done.returncode != 0:
        raise ModelConfigError(
            "discovery_failed",
            f"{' '.join(argv)} exited {done.returncode}: "
            + ((done.stderr or done.stdout).strip()[-2000:] or "(no output)"),
        )
    models = []
    for line in done.stdout.splitlines():
        row = PI_ROW.match(line.strip())
        if not row or row["provider"] == "provider":
            continue
        reasoning = row["thinking"] == "yes"
        models.append(
            {
                "id": f"{row['provider']}/{row['model']}",
                "source": "pi --list-models",
                "reasoning": reasoning,
                "levels": list(levels) if reasoning else ["off"],
                "context": row["context"],
                "max_output": row["max_out"],
                "images": row["images"] == "yes",
                "note": "",
            }
        )
    agent = environ.get("PI_CODING_AGENT_DIR") or "~/.pi/agent"
    note = (
        "pi lists the models it has credentials for in "
        f"{agent}; workers get a copy of its auth.json and models.json."
    )
    if not models:
        note += (
            " It listed none: sign in with pi's /login or add a provider in models.json, then "
            f"list again. Its output was: {done.stdout.strip()[-500:] or '(empty)'}"
        )
    return models, note


def candidates(backend: str, environ=None) -> dict:
    """The models and reasoning levels the installed agent program offers workers."""
    environ = os.environ if environ is None else environ
    program = _program(backend, environ)
    if not program:
        variable = "CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI"
        raise ModelConfigError(
            "backend_missing",
            f"the {backend} command is not installed: it is not on PATH and {variable} does not "
            "name an executable",
        )
    levels = _levels(backend, program, environ)
    if backend == "claude":
        models, note = _claude_models(levels, environ)
    else:
        models, note = _pi_models(program, levels, environ)
    return {
        "backend": backend,
        "program": program,
        "version": _version(program, environ),
        "complete": backend == "pi",
        "reasoning_flag": REASONING_FLAG[backend],
        "reasoning_levels": levels,
        "models": models,
        "note": note,
    }


# The command ------------------------------------------------------------------------------------

HANDLING = {
    "client_unknown": (
        "input",
        "Workers runs on the main session's agent program and cannot guess which one it is",
    ),
    "invalid_client": ("input", "only claude and pi are clients Concorde supports"),
    "backend_missing": (
        "environment",
        "Workers does not install agent programs; the machine must provide the command",
    ),
    "discovery_failed": (
        "environment",
        (
            "the agent program did not answer the listing, and Workers has no other source of "
            "its models"
        ),
    ),
    "config_invalid": (
        "input",
        (
            "Workers does not repair a configuration file it cannot read; the file must be "
            "fixed or removed"
        ),
    ),
    "unknown_task": (
        "input",
        "the command names a task the primary worktree does not know",
    ),
    "not_a_worktree": (
        "input",
        "a worker model configuration belongs to a worktree, and the command ran outside one",
    ),
    "missing_worktree": (
        "environment",
        "the task's worktree is gone from disk, and recreating it is not Workers' decision",
    ),
}
OPTIONS = {
    "client_unknown": [
        "run the command from the Claude Code or pi main session",
        "set CONCORDE_CLIENT to claude or pi",
    ],
    "backend_missing": [
        "install the agent program, or set CONCORDE_CLAUDE or CONCORDE_PI"
    ],
    "config_invalid": [
        "fix the file by hand, or delete it and configure again with concorde workers set"
    ],
    "unknown_model": [
        "choose a model from concorde workers models",
        "pass --allow-unlisted for a model the listing cannot show",
    ],
    "unknown_level": ["choose a level listed for the model by concorde workers models"],
    "unknown_task": ["run concorde task list to see the tasks"],
}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ModelConfigError("invalid_command", f"{self.prog}: {message}")


def parser() -> argparse.ArgumentParser:
    root = _Parser(prog="concorde workers")
    commands = root.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("models", "show", "set", "unset"):
        command = commands.add_parser(name)
        command.add_argument("--backend", choices=CLIENTS)
        command.add_argument("--task")
        if name in ("set", "unset"):
            command.add_argument("--task-type", choices=TASK_TYPES)
        if name == "set":
            command.add_argument("--model")
            command.add_argument("--reasoning")
            command.add_argument("--allow-unlisted", action="store_true")
    return root


def refusal(command: str, error: ModelConfigError) -> dict:
    reason, explanation = HANDLING.get(
        error.code,
        ("input", "the request names a model, level or option Workers does not admit"),
    )
    return errors.link(
        "component",
        f"Workers (concorde workers {command})",
        error.code,
        str(error),
        reason=reason,
        explanation=explanation,
        options=OPTIONS.get(error.code, []),
    )


def _target(here: Path, task: str | None) -> tuple[Path, str]:
    """The worktree the command reads or changes: the named task's, or the current one."""
    from ..tasks import store

    try:
        if task:
            record = store.load_task(store.primary_of(here), task)
            worktree = Path(record["worktree"])
            if not worktree.is_dir():
                raise ModelConfigError(
                    "missing_worktree",
                    f"the worktree {worktree} of task {task} does not exist",
                )
            return worktree, f"task {task}"
    except store.TaskError as error:
        raise ModelConfigError(error.code, str(error)) from error
    found = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=here,
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0:
        raise ModelConfigError(
            "not_a_worktree",
            f"{here} is not inside a Git worktree, so it has no worker model configuration: "
            + (found.stderr.strip() or f"git exited {found.returncode}"),
        )
    return Path(found.stdout.strip()), "this worktree"


def _backend(arguments, environ) -> tuple[str, str]:
    if arguments.backend:
        return arguments.backend, "--backend"
    return detect_client(environ)


def _effective(config: dict, backend: str) -> dict:
    return {name: selection(config, backend, name) for name in TASK_TYPES}


def _check_choice(found: dict, config: dict, arguments, backend: str) -> None:
    ids = [item["id"] for item in found["models"]]
    if arguments.model and arguments.model not in ids and not arguments.allow_unlisted:
        raise ModelConfigError(
            "unknown_model",
            f"{arguments.model!r} is not a {backend} model this machine lists "
            f"({', '.join(ids) or 'none'})",
        )
    if not arguments.reasoning:
        return
    model = arguments.model
    if not model:
        current = selection(config, backend, arguments.task_type or "")
        model = current["model"]
    listed = next((item for item in found["models"] if item["id"] == model), None)
    levels = listed["levels"] if listed else found["reasoning_levels"]
    if arguments.reasoning not in levels:
        raise ModelConfigError(
            "unknown_level",
            f"{arguments.reasoning!r} is not a reasoning level of "
            f"{model or f'the {backend} default model'} (levels: {', '.join(levels)})",
        )


def _set(config: dict, arguments, backend: str, environ) -> dict:
    if not arguments.model and not arguments.reasoning:
        raise ModelConfigError(
            "invalid_command", "concorde workers set needs --model, --reasoning or both"
        )
    _check_choice(candidates(backend, environ), config, arguments, backend)
    section = config.setdefault(backend, {})
    if arguments.task_type:
        entry = section.setdefault("task_types", {}).setdefault(arguments.task_type, {})
    else:
        entry = section.setdefault("default", {})
    if arguments.model:
        entry["model"] = arguments.model
    if arguments.reasoning:
        entry["reasoning"] = arguments.reasoning
    return config


def _unset(config: dict, arguments, backend: str) -> tuple[dict, bool]:
    section = config.get(backend) or {}
    if arguments.task_type:
        removed = (section.get("task_types") or {}).pop(arguments.task_type, None)
        if section.get("task_types") == {}:
            section.pop("task_types")
    else:
        removed = section.pop("default", None)
    if backend in config and not config[backend]:
        config.pop(backend)
    return config, removed is not None


def run(argv, cwd: Path | None = None, environ=None) -> dict:
    environ = os.environ if environ is None else environ
    arguments = parser().parse_args(list(argv))
    here = Path(cwd or Path.cwd())
    worktree, scope = _target(here, arguments.task)
    backend, told = _backend(arguments, environ)
    config = load(worktree)
    value: dict = {
        "backend": backend,
        "backend_from": told,
        "worktree": worktree.as_posix(),
        "scope": scope,
        "config": config_path(worktree).as_posix(),
    }
    if arguments.command == "models":
        value.update(candidates(backend, environ))
    elif arguments.command == "set":
        config = _set(config, arguments, backend, environ)
        save(worktree, config)
    elif arguments.command == "unset":
        config, removed = _unset(config, arguments, backend)
        save(worktree, config)
        value["removed"] = removed
    value["configured"] = config.get(backend) or {}
    value["effective"] = _effective(config, backend)
    return value


def main(argv, cwd: Path | None = None, environ=None) -> int:
    words = list(argv)
    command = words[0] if words else "?"
    try:
        value = run(words, cwd, environ)
    except ModelConfigError as error:
        sys.stdout.write(
            json.dumps({"error": refusal(command, error)}, indent=2) + "\n"
        )
        return 2 if error.code == "invalid_command" else 1
    except SystemExit as exit_:
        return 0 if exit_.code in (0, None) else 2
    except Exception as error:  # noqa: BLE001 -- every failure leaves a detailed error
        link = errors.from_exception(
            f"Workers (concorde workers {command})",
            error,
            explanation="Workers has no recovery for an unexpected error; nothing after it ran",
        )
        sys.stdout.write(json.dumps({"error": link}, indent=2) + "\n")
        return 1
    sys.stdout.write(json.dumps(value, indent=2) + "\n")
    return 0


__all__ = [
    "CLIENTS",
    "CONFIG",
    "ModelConfigError",
    "candidates",
    "detect_client",
    "inherit",
    "load",
    "main",
    "save",
    "selection",
]
