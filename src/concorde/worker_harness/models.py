"""The worker configuration ``.concorde/workers.json``: backends, models and limits of workers,
and the model map that resolves its project model names on this machine.

The file is tracked with the project, so a task starts from its base commit's configuration and
its own changes merge with it. The worktree's JSON is the source of truth, edited directly, and
the only source of a worker's model and level: nothing is read from the developer's own pi or
Claude Code settings. Every worker needs the file, its required ``enabled_models`` admits the
project model names any entry may name, each with an optional level of its own, and a worker whose
entries resolve no model is refused. Every field is inherited alike, the most specific entry that
sets it winning. Validation never discovers models or checks credentials.

A project model name, such as ``gpt-6-astra``, depends on no installation. The model map, a JSON
file of the user outside every repository, gives its local model id for each program; a worker
whose model has no id for its backend there is refused, and the name is never used as the id.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..kernel.refusal import KernelError
from ..kernel.schema import validate

CONFIG = ".concorde/workers.json"
# The untracked file that held worker models before; refused, never read.
RETIRED = ".concorde/worker-models.json"
SCHEMA_VERSION = 2
# The model map: the file the environment variable names, else this path below the user's XDG
# configuration directory.
MODEL_MAP_VARIABLE = "CONCORDE_MODEL_MAP"
MODEL_MAP = "concorde/models.json"
MODEL_MAP_VERSION = 1
# The limits of every worker launch when the configuration names none.
LIMITS = {
    "timeout_seconds": 1800,
    "max_turns": 200,
    "max_budget_usd": None,
    "rounds": 3,
}
# The paths Bash may read besides the grant when the configuration names none.
DEFAULT_RUNTIME = (".venv", "node_modules")
DEFAULT_BACKEND = "pi"
CLIENTS = ("claude", "pi")
LEVELS = {
    "claude": ("low", "medium", "high", "xhigh", "max"),
    "pi": ("off", "minimal", "low", "medium", "high", "xhigh", "max"),
}
TEXT = {
    "type": "string",
    "minLength": 1,
    "pattern": r"^[^\s\x00-\x1f\x7f](?:[^\x00-\x1f\x7f]*[^\s\x00-\x1f\x7f])?\Z",
}
# A project model name names a model independently of any installation, so it holds none of the
# `provider/` prefixes or other syntax of one program's local ids.
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
NAME_RULE = (
    "a project model name is letters, digits, `.`, `_` and `-`, starting with a letter or "
    "digit, such as `gpt-6-astra` or `claude-opus-5-5`; it names the model independently of "
    "any installation, and the model map gives each program's own id for it, such as "
    "`local-openai/gpt-6-astra`"
)
ENTRY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "backend": {"enum": list(CLIENTS)},
        "model": TEXT,
        "reasoning": TEXT,
    },
    "anyOf": [{"required": [field]} for field in ("backend", "model", "reasoning")],
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "enabled_models"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        # The models any entry may name, keyed by project model name, each with its own level.
        "enabled_models": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"reasoning": TEXT},
            },
        },
        "default": ENTRY_SCHEMA,
        "operations": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "default": ENTRY_SCHEMA,
                    "workers": {"type": "object", "additionalProperties": ENTRY_SCHEMA},
                },
            },
        },
        "limits": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "timeout_seconds": {"type": "number", "minimum": 1},
                "max_turns": {"type": "integer", "minimum": 1},
                "max_budget_usd": {"type": "number", "minimum": 0.01},
                "rounds": {"type": "integer", "minimum": 0},
            },
        },
        "runtime": {"type": "array", "items": TEXT, "uniqueItems": True},
    },
}
MODEL_MAP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "models"],
    "properties": {
        "schema_version": {"const": MODEL_MAP_VERSION},
        # Each project model name's local model id, per program.
        "models": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {backend: TEXT for backend in CLIENTS},
            },
        },
    },
}


class ModelConfigError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# The Operations a caller may launch workers for, each with the ids of its workers, the first its
# default: the names the configuration's entries may use. In Concorde they are the Operations the
# installed parts register; to the worker harness they are labels.
Declared = Mapping[str, Sequence[str]]


def validate_config(value: dict, declared: Declared) -> None:
    """Check structure, the Operation and worker names against those ``declared``, enabled models
    and backend reasoning vocabulary, never model availability."""
    if isinstance(value, dict) and "enabled_models" not in value:
        raise ModelConfigError(
            "config_invalid",
            "`enabled_models` is missing: it is required and lists every model a worker may "
            'run on by its project model name, such as `"enabled_models": {"gpt-6-astra": '
            '{"reasoning": "medium"}}`; add every model the entries name',
        )
    try:
        validate(value, SCHEMA)
    except KernelError as error:
        raise ModelConfigError(
            "config_invalid", f"{error.field or '/'}: {error}"
        ) from error
    enabled = value["enabled_models"]
    if not enabled:
        raise ModelConfigError(
            "config_invalid",
            "`enabled_models` is empty: list every model a worker may run on",
        )
    for model, entry in enabled.items():
        if not NAME.fullmatch(model):
            raise ModelConfigError(
                "config_invalid",
                f"`enabled_models` names the model {json.dumps(model)}; {NAME_RULE}",
            )
        level = entry.get("reasoning")
        if level is not None and level not in LEVELS["pi"]:
            raise ModelConfigError(
                "config_invalid",
                f"enabled_models[{json.dumps(model)}].reasoning: {level!r} is not a level of "
                f"either backend; expected one of {', '.join(LEVELS['pi'])}",
            )
    ids = declared
    scopes: list[tuple[str | None, str | None]] = [(None, None)]
    for operation, entry in value.get("operations", {}).items():
        if operation not in ids:
            raise ModelConfigError(
                "config_invalid",
                f"unknown Operation {operation!r}; expected {', '.join(ids)}",
            )
        scopes.append((operation, None))
        for worker in entry.get("workers", {}):
            if worker not in ids[operation]:
                raise ModelConfigError(
                    "config_invalid",
                    f"unknown worker {worker!r} of {operation}; expected {', '.join(ids[operation])}",
                )
            scopes.append((operation, worker))
    for entry, where in _entries(value):
        model = entry.get("model")
        if model is not None and model not in enabled:
            raise ModelConfigError(
                "model_not_enabled",
                f"{where}.model: {model!r} is not in `enabled_models` "
                f"({', '.join(sorted(enabled))}); add it to `enabled_models` or choose one of "
                "those",
            )
    for operation, worker in scopes:
        selected = choice(value, operation, worker)
        level = selected["reasoning"]
        if level is not None and level not in LEVELS[selected["backend"]]:
            raise ModelConfigError(
                "config_invalid",
                f"{selected['reasoning_source']}.reasoning: {level!r} is not a {selected['backend']} level; expected {', '.join(LEVELS[selected['backend']])}",
            )


def _entries(config: dict):
    """Every entry of the file with the path that names it."""
    if "default" in config:
        yield config["default"], "default"
    for operation, scope in config.get("operations", {}).items():
        if "default" in scope:
            yield scope["default"], f"operations.{operation}.default"
        for worker, entry in scope.get("workers", {}).items():
            yield entry, f"operations.{operation}.workers.{worker}"


def config_path(worktree: Path) -> Path:
    return Path(worktree) / CONFIG


def limits(config: dict) -> dict:
    """The limits of every worker launch: the configuration's, else ``LIMITS``."""
    return LIMITS | config.get("limits", {})


def runtime(config: dict) -> tuple[str, ...]:
    """The paths Bash may read besides the grant: the configuration's, else the default."""
    return tuple(config.get("runtime", DEFAULT_RUNTIME))


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def load(worktree: Path, declared: Declared) -> dict:
    """The worktree's worker configuration, validated against the Operations and worker ids its
    caller ``declared``."""
    path = config_path(worktree)
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except FileNotFoundError:
        if (Path(worktree) / RETIRED).exists():
            raise ModelConfigError(
                "config_invalid",
                f"{Path(worktree) / RETIRED} is no longer read: worker models are configured "
                f"in the tracked {CONFIG}, which this worktree does not have; move its "
                f"default and operations into {CONFIG} with schema_version {SCHEMA_VERSION}, "
                f"commit it and delete {RETIRED}",
            ) from None
        raise ModelConfigError(
            "config_missing",
            f"{path} does not exist, and every worker needs it: write it with schema_version "
            f"{SCHEMA_VERSION}, the `enabled_models` workers may run on and a `default` model, "
            f'such as {{"schema_version": {SCHEMA_VERSION}, "enabled_models": '
            '{"gpt-6-astra": {}}, "default": {"model": "gpt-6-astra"}}, and commit it; '
            "Concorde never takes a worker's model from the developer's own pi or Claude Code "
            "settings",
        ) from None
    except (OSError, ValueError) as error:
        raise ModelConfigError(
            "config_invalid", f"{path} cannot be read as JSON: {error}"
        ) from error
    if isinstance(value, dict) and value.get("schema_version") == 1:
        raise ModelConfigError(
            "config_invalid",
            f"{path} has schema_version 1; expected {SCHEMA_VERSION}, which names every model by "
            "a project model name instead of one program's local model id: replace each id in "
            "`enabled_models` and in every entry's `model`, such as `local-openai/gpt-6-astra`, "
            "by a project model name such as `gpt-6-astra`, set schema_version "
            f"{SCHEMA_VERSION}, commit the file, and map each name to its local id in the model "
            f"map ({MODEL_MAP_VARIABLE}, else $XDG_CONFIG_HOME/{MODEL_MAP}, by default "
            f"~/.config/{MODEL_MAP})",
        )
    if isinstance(value, dict) and value.get("schema_version") != SCHEMA_VERSION:
        raise ModelConfigError(
            "config_invalid",
            f"{path} has schema_version {value.get('schema_version')!r}; expected {SCHEMA_VERSION}",
        )
    try:
        validate_config(value, declared)
    except ModelConfigError as error:
        raise ModelConfigError(error.code, f"{path}: {error}") from error
    return value


def _levels_of(
    config: dict, operation: str | None, worker: str | None
) -> list[tuple[dict, str]]:
    levels = []
    if operation is not None:
        entry = config.get("operations", {}).get(operation, {})
        if worker is not None:
            levels.append(
                (
                    entry.get("workers", {}).get(worker, {}),
                    f"operations.{operation}.workers.{worker}",
                )
            )
        levels.append((entry.get("default", {}), f"operations.{operation}.default"))
    levels.append((config.get("default", {}), "default"))
    return levels


def choice(
    config: dict, operation: str | None = None, worker: str | None = None
) -> dict:
    """The backend, model and level of one worker: for each field the most specific entry that
    sets it, the level of the entry that chose the model or a more specific one before the
    model's own."""
    eligible = _levels_of(config, operation, worker)
    backend_at = next(
        (i for i, (entry, _) in enumerate(eligible) if "backend" in entry), None
    )
    chosen = (
        {
            "backend": DEFAULT_BACKEND,
            "backend_source": "Concorde's default worker backend",
        }
        if backend_at is None
        else {
            "backend": eligible[backend_at][0]["backend"],
            "backend_source": eligible[backend_at][1],
        }
    )
    model_at = next(
        (i for i, (entry, _) in enumerate(eligible) if "model" in entry), None
    )
    chosen["model"], chosen["model_source"] = (
        (eligible[model_at][0]["model"], eligible[model_at][1])
        if model_at is not None
        else (None, "no entry")
    )
    level_at = next(
        (i for i, (entry, _) in enumerate(eligible) if "reasoning" in entry), None
    )
    own = config.get("enabled_models", {}).get(chosen["model"], {})
    if level_at is not None and (model_at is None or level_at <= model_at):
        # A level set with the model, or more specifically, is meant for it.
        found = (eligible[level_at][0]["reasoning"], eligible[level_at][1])
    elif "reasoning" in own:
        found = (
            own["reasoning"],
            f"enabled_models[{json.dumps(chosen['model'])}]",
        )
    elif level_at is not None:
        found = (eligible[level_at][0]["reasoning"], eligible[level_at][1])
    else:
        found = (None, "the backend's own default")
    chosen["reasoning"], chosen["reasoning_source"] = found
    return chosen


def _program(backend: str, environ) -> str | None:
    name = (
        environ.get("CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI")
        or backend
    )
    if os.path.isabs(name):
        try:
            return name if os.path.isfile(name) and os.access(name, os.X_OK) else None
        except OSError:
            return None
    return shutil.which(name, path=environ.get("PATH"))


def worker_choice(
    config: dict, declared: Declared, operation: str, worker: str, environ=None
) -> dict:
    """The backend, project model name, level, local model id and model map of the worker
    ``worker`` of ``operation``, one of those ``declared``."""
    validate_config(config, declared)
    ids = declared
    if operation not in ids or worker not in ids[operation]:
        raise ModelConfigError("config_invalid", f"unknown worker {operation}/{worker}")
    environ = os.environ if environ is None else environ
    chosen = choice(config, operation, worker)
    backend = chosen["backend"]
    if _program(backend, environ) is None:
        variable = "CONCORDE_CLAUDE" if backend == "claude" else "CONCORDE_PI"
        raise ModelConfigError(
            "backend_missing",
            f"the {worker} worker of {operation} runs on {backend} ({chosen['backend_source']}), "
            f"but the {backend} command is not installed: PATH and {variable} name no executable. "
            f"A worker never falls back; install its program or edit its backend in {CONFIG}.",
        )
    if chosen["model"] is None:
        names = ", ".join(where for _, where in _levels_of(config, operation, worker))
        raise ModelConfigError(
            "model_unresolved",
            f"the {worker} worker of {operation} runs on {backend} "
            f"({chosen['backend_source']}), but none of the entries its model may come from "
            f"({names}) of {CONFIG} sets `model`; set one of them to a model of "
            "`enabled_models`. Concorde never runs a worker on its program's own default model "
            "or on the developer's own.",
        )
    path, mapped = load_model_map(environ)
    return chosen | {
        "local_model": _local_model(
            chosen, f"the {worker} worker of {operation}", path, mapped
        ),
        "model_map": path.as_posix(),
    }


def model_map_path(environ=None) -> Path:
    """The model map: the file ``CONCORDE_MODEL_MAP`` names, else ``concorde/models.json`` of the
    user's XDG configuration directory, ``~/.config`` unless ``XDG_CONFIG_HOME`` is absolute."""
    environ = os.environ if environ is None else environ
    named = environ.get(MODEL_MAP_VARIABLE)
    if named:
        return Path(named)
    base = environ.get("XDG_CONFIG_HOME") or ""
    if not os.path.isabs(base):
        home = environ.get("HOME") or str(Path.home())
        base = os.path.join(home, ".config")
    return Path(base) / MODEL_MAP


def load_model_map(environ=None) -> tuple[Path, dict]:
    """The model map's path and its ``models``, each project model name's id per program."""
    path = model_map_path(environ)
    example = (
        f'{{"schema_version": {MODEL_MAP_VERSION}, "models": {{"gpt-6-astra": '
        '{"pi": "local-openai/gpt-6-astra"}, "claude-opus-5-5": {"pi": '
        '"anthropic/claude-opus-5-5", "claude": "claude-opus-5-5"}}}'
    )
    if not path.is_absolute():
        raise ModelConfigError(
            "model_map_invalid",
            f"{MODEL_MAP_VARIABLE} names {str(path)!r}, which is not an absolute path; name the "
            "model map by its absolute path, or unset the variable to use "
            f"$XDG_CONFIG_HOME/{MODEL_MAP}",
        )
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except FileNotFoundError:
        raise ModelConfigError(
            "model_map_missing",
            f"the model map {path} does not exist, and every worker needs it to find its "
            "model's local id: write it with every project model name the worker "
            f"configuration names and each program's own id for it, such as {example}. It "
            "belongs to this machine and is never committed; `python3 "
            "scripts/available_models.py --backend pi|claude` lists the local ids",
        ) from None
    except (OSError, ValueError) as error:
        raise ModelConfigError(
            "model_map_invalid", f"the model map {path} cannot be read as JSON: {error}"
        ) from error
    try:
        validate(value, MODEL_MAP_SCHEMA)
    except KernelError as error:
        raise ModelConfigError(
            "model_map_invalid",
            f"the model map {path}: {error.field or '/'}: {error}; it holds schema_version {MODEL_MAP_VERSION} and "
            "`models`, each project model name's id for `pi`, `claude` or both, such as "
            f"{example}",
        ) from error
    for name, ids in value["models"].items():
        if not NAME.fullmatch(name):
            raise ModelConfigError(
                "model_map_invalid",
                f"the model map {path} names the model {json.dumps(name)}; {NAME_RULE}",
            )
        if not ids:
            raise ModelConfigError(
                "model_map_invalid",
                f"the model map {path} gives `models.{name}` no id; give its id for `pi`, "
                "`claude` or both",
            )
    return path, value["models"]


def _local_model(chosen: dict, who: str, path: Path, mapped: dict) -> str:
    """The local id the model map gives the chosen model on the chosen backend."""
    name, backend = chosen["model"], chosen["backend"]
    local = mapped.get(name, {}).get(backend)
    if local is None:
        others = mapped.get(name, {})
        known = (
            f"; it maps the model only for {', '.join(sorted(others))}"
            if others
            else "; it does not name the model at all"
        )
        raise ModelConfigError(
            "model_unmapped",
            f"{who} runs on {backend} ({chosen['backend_source']}) with the project model "
            f"{name!r} ({chosen['model_source']}), but the model map {path} gives no {backend} "
            f'id for it{known}. Add it as `"{backend}": "<{backend}\'s id of the model>"` '
            f"under `models.{name}`; `python3 scripts/available_models.py --backend {backend}` "
            "lists the ids. Concorde never uses a project model name as a local id.",
        )
    return local


def check_mapped(
    config: dict, declared: Declared, environ=None, operation: str | None = None
) -> None:
    """Refuse with one error every model a worker of ``operation`` would take that the model map
    does not give an id for its backend, as that Operation's run asks before its first worker
    launches; without ``operation``, the workers of every Operation, such as before a test
    project's workers first run. A worker without a model is left to its own resolution."""
    validate_config(config, declared)
    ids = declared
    if operation is not None and operation not in ids:
        raise ModelConfigError(
            "config_invalid", f"{operation} is no Operation that launches workers"
        )
    path, mapped = load_model_map(environ)
    missing: dict[tuple[str, str], list[str]] = {}
    for name, workers in ids.items():
        if operation is not None and name != operation:
            continue
        for worker in workers:
            chosen = choice(config, name, worker)
            if chosen["model"] is not None and chosen["backend"] not in mapped.get(
                chosen["model"], {}
            ):
                missing.setdefault((chosen["model"], chosen["backend"]), []).append(
                    f"{name}/{worker}"
                )
    if missing:
        entries = "; ".join(
            f"`models.{name}.{backend}` (for {', '.join(workers)})"
            for (name, backend), workers in sorted(missing.items())
        )
        raise ModelConfigError(
            "model_unmapped",
            f"the model map {path} gives no local id for {entries}; add each, since Concorde "
            "never uses a project model name as a local id",
        )


HANDLING = {
    "backend_missing": (
        "environment",
        "the machine must provide the program",
        [f"install the backend or edit {CONFIG}"],
    ),
    "discovery_failed": (
        "environment",
        "the program could not list candidates",
        ["configure a custom model directly or repair discovery"],
    ),
    "config_invalid": (
        "input",
        "invalid configuration is never ignored",
        [f"correct {CONFIG} as the error says"],
    ),
    "config_missing": (
        "input",
        "a worker runs only on what the project's worker configuration chooses",
        [f"write {CONFIG} with `enabled_models` and a `default` model and commit it"],
    ),
    "model_unresolved": (
        "input",
        "a worker never runs on a model its configuration does not name",
        [f"set `model` in the worker's entry or a default of {CONFIG}"],
    ),
    "model_not_enabled": (
        "input",
        "every model a worker may run on must be enabled in the worker configuration",
        [f"add the model to `enabled_models` of {CONFIG} or choose an enabled one"],
    ),
    "model_map_missing": (
        "environment",
        "a project model name reaches a program only through this machine's model map",
        ["write the model map with each project model name's local id per program"],
    ),
    "model_map_invalid": (
        "environment",
        "an unreadable model map is never ignored",
        ["correct the model map as the error says"],
    ),
    "model_unmapped": (
        "environment",
        "a worker never runs on a project model name its backend has no local id for",
        ["add the model's id for the worker's backend to the model map"],
    ),
}
