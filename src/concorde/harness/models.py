"""Worker model configuration: which backend, model and reasoning level each worker uses.

The configuration is the file ``.concorde/worker-models.json`` of one worktree. Git ignores it: it
names models of this machine's Claude Code or pi installation, and it belongs to the worktree, not
to the branch. ``concorde task open`` copies the primary worktree's file into a new task worktree,
so a task starts with the configuration of its creation and keeps its own copy; later changes in
the primary worktree never reach an existing task, and a task's copy changes only when a request
names it.

The file is keyed by **worker id**, the stable name an Operation gives each worker it launches,
such as ``spec_panel``'s ``reviewer1`` or ``chair``: a global ``default``, and per Operation a
``default`` and one entry per worker id. Each entry may set a ``backend`` (``pi`` or ``claude``), a
``model`` and a ``reasoning`` level. For each field the worker's entry wins, then the Operation's
default, then the global default; a worker whose entries choose no backend runs on pi. An entry
that chooses a backend starts that program afresh: the model and level come only from that entry or
a more specific one, since a model named for one program means nothing to the other. A chosen
program must be installed, and a worker never falls back to the other one.

This module knows no Operation or worker names; the ``concorde configure-workers`` command checks them
against the catalog and changes the file through ``set_choice`` and ``unset_choice``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..spec.schema import ContractError, validate

CONFIG = ".concorde/worker-models.json"
SCHEMA_VERSION = 3
# The program a worker runs on when its configuration chooses none.
DEFAULT_BACKEND = "pi"
CLIENTS = ("claude", "pi")
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
PROGRAM = {"enum": list(CLIENTS)}
# One entry: the default, an Operation's default or one worker's.
ENTRY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"backend": PROGRAM, "model": TEXT, "reasoning": TEXT},
    "anyOf": [
        {"required": ["backend"]},
        {"required": ["model"]},
        {"required": ["reasoning"]},
    ],
}
OPERATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "default": ENTRY_SCHEMA,
        "workers": {"type": "object", "additionalProperties": ENTRY_SCHEMA},
    },
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "default": ENTRY_SCHEMA,
        "operations": {"type": "object", "additionalProperties": OPERATION_SCHEMA},
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
        "unset, CLAUDECODE is not 1 and neither PI_SESSION_ID nor PI_CODING_AGENT is set",
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
    if isinstance(value, dict) and value.get("schema_version") != SCHEMA_VERSION:
        raise ModelConfigError(
            "config_invalid",
            f"{path} has schema_version {value.get('schema_version')!r}, but the worker model "
            f"configuration is version {SCHEMA_VERSION}, keyed by worker id; earlier versions, "
            "keyed by backend and worker role, are not read. Delete the file and configure the "
            "workers again with concorde configure-workers",
        )
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


def _levels_of(
    config: dict, operation: str | None, worker: str | None
) -> list[tuple[dict, str]]:
    """The entries that decide for one worker, an Operation's default or the default, most
    specific first, each with its place in the file."""
    levels = []
    if operation is not None:
        entry = (config.get("operations") or {}).get(operation) or {}
        if worker is not None:
            levels.append(
                (
                    (entry.get("workers") or {}).get(worker) or {},
                    f"operations.{operation}.workers.{worker}",
                )
            )
        levels.append((entry.get("default") or {}, f"operations.{operation}.default"))
    levels.append((config.get("default") or {}, "default"))
    return levels


def choice(
    config: dict, operation: str | None = None, worker: str | None = None
) -> dict:
    """The backend, model and reasoning level of the worker ``worker`` of ``operation`` (or of an
    Operation's default, or of the default), each with the entry it came from.

    The most specific entry that sets a field wins. The backend is pi when no entry chooses one;
    the model and level come only from the entry that chose the backend or a more specific one.
    """
    levels = _levels_of(config, operation, worker)
    chosen_at = next(
        (index for index, (entry, _) in enumerate(levels) if "backend" in entry), None
    )
    if chosen_at is None:
        backend, source = DEFAULT_BACKEND, "Concorde's default worker backend"
        eligible = levels
    else:
        backend, source = levels[chosen_at][0]["backend"], levels[chosen_at][1]
        eligible = levels[: chosen_at + 1]
    chosen = {"backend": backend, "backend_source": source}
    for field in ("model", "reasoning"):
        found = next(
            ((entry[field], where) for entry, where in eligible if field in entry), None
        )
        chosen[field], chosen[f"{field}_source"] = found or (
            None,
            "the backend's own default",
        )
    return chosen


def worker_choice(config: dict, operation: str, worker: str, environ=None) -> dict:
    """The choice of one worker, refused when its program is not installed."""
    environ = os.environ if environ is None else environ
    chosen = choice(config, operation, worker)
    backend = chosen["backend"]
    if _program(backend, environ) is None:
        variable = "CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI"
        other = "claude" if backend == "pi" else "pi"
        raise ModelConfigError(
            "backend_missing",
            f"the {worker} worker of {operation} runs on {backend} ({chosen['backend_source']}), "
            f"but the {backend} command is not installed: it is not on PATH and {variable} does "
            "not name an executable. A worker runs only on the program its configuration chooses "
            f"and never falls back to the other one; install {backend}, or choose {other} for it "
            f"with concorde configure-workers --operation {operation} --worker {worker} --backend {other}",
        )
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


# Changing the configuration -------------------------------------------------------------------

# Why a caller cannot handle each error of this module itself, and what it can offer instead.
HANDLING = {
    "client_unknown": (
        "input",
        "the main session's agent program must be known where the command depends on it, and "
        "nothing names which one it is",
        [
            "run the command from the Claude Code or pi main session",
            "set CONCORDE_CLIENT to claude or pi",
        ],
    ),
    "invalid_client": (
        "input",
        "only claude and pi are clients Concorde supports",
        ["set CONCORDE_CLIENT to claude or pi"],
    ),
    "backend_missing": (
        "environment",
        "agent programs are not installed by Concorde; the machine must provide the command",
        [
            "install the agent program, or set CONCORDE_CLAUDE or CONCORDE_PI",
            "choose the other program for the worker with concorde configure-workers --backend",
        ],
    ),
    "discovery_failed": (
        "environment",
        "the agent program did not answer the listing, and there is no other source of its models",
        ["run the listed command by hand to see why it fails"],
    ),
    "config_invalid": (
        "input",
        "a configuration file that cannot be read is never repaired or ignored",
        [
            "fix the file by hand, or delete it and configure again with concorde configure-workers"
        ],
    ),
    "unknown_model": (
        "input",
        "only a model the installed program lists is admitted without --allow-unlisted",
        [
            "choose a model from the candidates concorde configure-workers lists",
            "pass --allow-unlisted for a model the listing cannot show",
        ],
    ),
    "unknown_level": (
        "input",
        "only a reasoning level the model offers is admitted",
        ["choose a level listed for the model"],
    ),
}


def check_choice(
    found: dict,
    backend: str,
    model: str | None,
    reasoning: str | None,
    allow_unlisted: bool,
    effective_model: str | None,
) -> None:
    """Refuse a model the listing ``found`` of ``backend`` does not show, or a level that the model
    the entry will run with, ``effective_model``, does not offer."""
    ids = [item["id"] for item in found["models"]]
    if model and model not in ids and not allow_unlisted:
        raise ModelConfigError(
            "unknown_model",
            f"{model!r} is not a {backend} model this machine lists ({', '.join(ids) or 'none'})",
        )
    if not reasoning:
        return
    listed = next(
        (item for item in found["models"] if item["id"] == effective_model), None
    )
    levels = listed["levels"] if listed else found["reasoning_levels"]
    if reasoning not in levels:
        raise ModelConfigError(
            "unknown_level",
            f"{reasoning!r} is not a reasoning level of "
            f"{effective_model or f'the {backend} default model'} (levels: {', '.join(levels)})",
        )


def _entry(config: dict, operation: str | None, worker: str | None, create: bool):
    """The entry of the default, an Operation's default or one worker, created when asked."""
    if operation is None:
        return config.setdefault("default", {}) if create else config.get("default")
    operations = (
        config.setdefault("operations", {})
        if create
        else config.get("operations") or {}
    )
    entry = (
        operations.setdefault(operation, {})
        if create
        else operations.get(operation) or {}
    )
    if worker is None:
        return entry.setdefault("default", {}) if create else entry.get("default")
    workers = entry.setdefault("workers", {}) if create else entry.get("workers") or {}
    return workers.setdefault(worker, {}) if create else workers.get(worker)


def set_choice(
    config: dict,
    operation: str | None,
    worker: str | None,
    backend: str | None,
    model: str | None,
    reasoning: str | None,
) -> dict:
    """Set the fields given on the default, an Operation's default or one worker's entry."""
    entry = _entry(config, operation, worker, create=True)
    for field, value in (
        ("backend", backend),
        ("model", model),
        ("reasoning", reasoning),
    ):
        if value:
            entry[field] = value
    return config


def unset_choice(config: dict, operation: str | None, worker: str | None) -> bool:
    """Remove the default, an Operation's default or one worker's entry, and every section the
    removal leaves empty; whether the entry existed."""
    if operation is None:
        return config.pop("default", None) is not None
    operations = config.get("operations") or {}
    entry = operations.get(operation) or {}
    if worker is None:
        removed = entry.pop("default", None)
    else:
        workers = entry.get("workers") or {}
        removed = workers.pop(worker, None)
        if "workers" in entry and not workers:
            entry.pop("workers")
    if operation in operations and not entry:
        operations.pop(operation)
    if "operations" in config and not operations:
        config.pop("operations")
    return removed is not None


__all__ = [
    "CLIENTS",
    "CONFIG",
    "DEFAULT_BACKEND",
    "HANDLING",
    "ModelConfigError",
    "candidates",
    "check_choice",
    "choice",
    "config_path",
    "detect_client",
    "inherit",
    "load",
    "save",
    "set_choice",
    "unset_choice",
    "worker_choice",
]
