"""The worker configuration ``.concorde/workers.json``: backends, models and limits of workers.

The file is tracked with the project, so a task starts from its base commit's configuration and
its own changes merge with it. The worktree's JSON is the source of truth, edited directly.
Validation never discovers models or checks credentials. Explicit backend entries reset
inherited model/reasoning fields.
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
    "required": ["schema_version"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
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


def detect_client(environ=None) -> tuple[str, str]:
    """The main session's program; unrelated to the default worker backend."""
    environ = os.environ if environ is None else environ
    named = environ.get("CONCORDE_CLIENT", "").strip()
    if named:
        if named not in CLIENTS:
            raise ModelConfigError(
                "invalid_client", f"CONCORDE_CLIENT is {named!r}; expected claude or pi"
            )
        return named, f"CONCORDE_CLIENT={named}"
    if environ.get("CLAUDECODE") == "1":
        return "claude", "CLAUDECODE=1"
    for name in ("PI_SESSION_ID", "PI_CODING_AGENT"):
        if environ.get(name):
            return "pi", f"{name} is set"
    raise ModelConfigError(
        "client_unknown",
        "CONCORDE_CLIENT is unset, CLAUDECODE is not 1 and neither PI_SESSION_ID nor PI_CODING_AGENT is set",
    )


def worker_ids() -> dict[str, tuple[str, ...]]:
    """Load the catalog lazily, avoiding provider import cycles at runtime."""
    from ..operations.catalog import CATALOG, provider

    return {
        name: provider(name).workers
        for name in CATALOG
        if provider(name).task_type is not None
    }


def validate_config(value: dict) -> None:
    """Check structure, catalog names and backend reasoning vocabulary, never model availability."""
    try:
        validate(value, SCHEMA)
    except ContractError as error:
        raise ModelConfigError("config_invalid", str(error)) from error
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
    for operation, worker in scopes:
        selected = choice(value, operation, worker)
        level = selected["reasoning"]
        if level is not None and level not in LEVELS[selected["backend"]]:
            raise ModelConfigError(
                "config_invalid",
                f"{selected['reasoning_source']}.reasoning: {level!r} is not a {selected['backend']} level; expected {', '.join(LEVELS[selected['backend']])}",
            )


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
        return {"schema_version": SCHEMA_VERSION}
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
    for field in ("model", "reasoning"):
        found = next(
            ((entry[field], where) for entry, where in eligible if field in entry), None
        )
        chosen[field], chosen[f"{field}_source"] = found or (
            None,
            "the backend's own default",
        )
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
    return chosen


HANDLING = {
    "client_unknown": (
        "input",
        "the main session's program is unknown",
        ["set CONCORDE_CLIENT to claude or pi"],
    ),
    "invalid_client": (
        "input",
        "only claude and pi are supported",
        ["set CONCORDE_CLIENT to claude or pi"],
    ),
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
}
