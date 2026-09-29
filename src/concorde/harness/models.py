"""The worker configuration ``.concorde/workers.json``: backends, models and limits of workers.

The file is tracked with the project, so a task starts from its base commit's configuration and
its own changes merge with it. The worktree's JSON is the source of truth, edited directly, and
the only source of a worker's model and level: nothing is read from the developer's own pi or
Claude Code settings. Every worker needs the file, its required ``enabled_models`` admits the
models any entry may name, each with an optional level of its own, and a worker whose entries
resolve no model is refused. Validation never discovers models or checks credentials. Explicit
backend entries reset inherited model/reasoning fields.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from ..spec.schema import ContractError, validate

CONFIG = ".concorde/workers.json"
# The untracked file that held worker models before; refused, never read.
RETIRED = ".concorde/worker-models.json"
SCHEMA_VERSION = 1
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
        # The models any entry may name, keyed by exact model id, each with its own level.
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


class ModelConfigError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def worker_ids() -> dict[str, tuple[str, ...]]:
    """Load the catalog lazily, avoiding provider import cycles at runtime."""
    from ..operations.catalog import CATALOG, provider

    return {
        name: provider(name).workers
        for name in CATALOG
        if provider(name).task_type is not None
    }


def validate_config(value: dict) -> None:
    """Check structure, catalog names, enabled models and backend reasoning vocabulary, never
    model availability."""
    if isinstance(value, dict) and "enabled_models" not in value:
        raise ModelConfigError(
            "config_invalid",
            "`enabled_models` is missing: it is required and lists every model a worker may "
            'run on, such as `"enabled_models": {"<provider>/<model>": {"reasoning": '
            '"medium"}}`; add every model the entries name',
        )
    try:
        validate(value, SCHEMA)
    except ContractError as error:
        raise ModelConfigError("config_invalid", str(error)) from error
    enabled = value["enabled_models"]
    if not enabled:
        raise ModelConfigError(
            "config_invalid",
            "`enabled_models` is empty: list every model a worker may run on",
        )
    for model, entry in enabled.items():
        if not model.strip() or model != model.strip() or not model.isprintable():
            raise ModelConfigError(
                "config_invalid",
                f"`enabled_models` names the model {json.dumps(model)}; a model id is "
                "non-empty printable text without surrounding spaces",
            )
        level = entry.get("reasoning")
        if level is not None and level not in LEVELS["pi"]:
            raise ModelConfigError(
                "config_invalid",
                f"enabled_models[{json.dumps(model)}].reasoning: {level!r} is not a level of "
                f"either backend; expected one of {', '.join(LEVELS['pi'])}",
            )
    ids = worker_ids()
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


def load(worktree: Path) -> dict:
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
            'such as {"schema_version": 1, "enabled_models": {"<provider>/<model>": {}}, '
            '"default": {"model": "<provider>/<model>"}}, and commit it; Concorde never '
            "takes a worker's model from the developer's own pi or Claude Code settings",
        ) from None
    except (OSError, ValueError) as error:
        raise ModelConfigError(
            "config_invalid", f"{path} cannot be read as JSON: {error}"
        ) from error
    if isinstance(value, dict) and value.get("schema_version") != SCHEMA_VERSION:
        raise ModelConfigError(
            "config_invalid",
            f"{path} has schema_version {value.get('schema_version')!r}; expected {SCHEMA_VERSION}",
        )
    try:
        validate_config(value)
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
    levels = _levels_of(config, operation, worker)
    chosen_at = next(
        (i for i, (entry, _) in enumerate(levels) if "backend" in entry), None
    )
    if chosen_at is None:
        backend, source = DEFAULT_BACKEND, "Concorde's default worker backend"
        eligible = levels
    else:
        backend, source = levels[chosen_at][0]["backend"], levels[chosen_at][1]
        eligible = levels[: chosen_at + 1]
    chosen = {"backend": backend, "backend_source": source}
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


def worker_choice(config: dict, operation: str, worker: str, environ=None) -> dict:
    validate_config(config)
    ids = worker_ids()
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
        levels = _levels_of(config, operation, worker)
        at = next(
            (
                i
                for i, (_, where) in enumerate(levels)
                if where == chosen["backend_source"]
            ),
            len(levels) - 1,
        )
        names = ", ".join(where for _, where in levels[: at + 1])
        raise ModelConfigError(
            "model_unresolved",
            f"the {worker} worker of {operation} runs on {backend} "
            f"({chosen['backend_source']}), but none of the entries its model may come from "
            f"({names}) of {CONFIG} sets `model`; set one of them to a model of "
            "`enabled_models`. Concorde never runs a worker on its program's own default model "
            "or on the developer's own.",
        )
    return chosen


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
}
