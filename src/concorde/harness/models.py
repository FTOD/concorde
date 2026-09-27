"""Worker configuration, shared by runtime, read-only commands and the draft editor.

The worktree's JSON is the source of truth. Validation never discovers models or checks
credentials. Explicit backend entries reset inherited model/reasoning fields.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from ..spec.schema import ContractError, validate

CONFIG = ".concorde/worker-models.json"
SCHEMA_VERSION = 3
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
        return {"schema_version": SCHEMA_VERSION}
    except (OSError, ValueError) as error:
        raise ModelConfigError(
            "config_invalid", f"{path} cannot be read as JSON: {error}"
        ) from error
    if isinstance(value, dict) and value.get("schema_version") != SCHEMA_VERSION:
        raise ModelConfigError(
            "config_invalid",
            f"{path} has schema_version {value.get('schema_version')!r}; expected {SCHEMA_VERSION}, keyed by worker id",
        )
    try:
        validate_config(value)
    except ModelConfigError as error:
        raise ModelConfigError(error.code, f"{path}: {error}") from error
    return value


def save(worktree: Path, value: dict) -> Path:
    validate_config(value)
    path = config_path(worktree)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".worker-models.")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, path)
    except OSError as error:
        raise ModelConfigError("config_write_failed", f"{path}: {error}") from error
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return path


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
            "A worker never falls back; install its program or edit its backend in "
            ".concorde/worker-models.json (or use concorde configure-workers).",
        )
    return chosen


def inherit(primary: Path, worktree: Path) -> str | None:
    source = config_path(primary)
    if not source.is_file():
        return None
    target = config_path(worktree)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target.as_posix()


def _entry(config: dict, operation: str | None, worker: str | None, create: bool):
    if operation is None:
        return config.setdefault("default", {}) if create else config.get("default")
    operations = (
        config.setdefault("operations", {}) if create else config.get("operations", {})
    )
    entry = (
        operations.setdefault(operation, {})
        if create
        else operations.get(operation, {})
    )
    if worker is None:
        return entry.setdefault("default", {}) if create else entry.get("default")
    workers = entry.setdefault("workers", {}) if create else entry.get("workers", {})
    return workers.setdefault(worker, {}) if create else workers.get(worker)


def set_choice(config, operation, worker, backend, model, reasoning) -> dict:
    entry = _entry(config, operation, worker, create=True)
    assert entry is not None
    for field, value in (
        ("backend", backend),
        ("model", model),
        ("reasoning", reasoning),
    ):
        if value is not None:
            entry[field] = value
    return config


def unset_choice(config: dict, operation: str | None, worker: str | None) -> bool:
    if operation is None:
        return config.pop("default", None) is not None
    operations = config.get("operations", {})
    entry = operations.get(operation, {})
    if worker is None:
        removed = entry.pop("default", None)
    else:
        workers = entry.get("workers", {})
        removed = workers.pop(worker, None)
        if "workers" in entry and not workers:
            entry.pop("workers")
    if operation in operations and not entry:
        operations.pop(operation)
    if "operations" in config and not operations:
        config.pop("operations")
    return removed is not None


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
        ["install the backend or edit .concorde/worker-models.json"],
    ),
    "discovery_failed": (
        "environment",
        "the program could not list candidates",
        ["configure a custom model directly or repair discovery"],
    ),
    "config_invalid": (
        "input",
        "invalid configuration is never ignored",
        [
            "edit .concorde/worker-models.json and run concorde configure-workers --check"
        ],
    ),
    "config_write_failed": (
        "environment",
        "the configuration could not be saved",
        ["check the file and directory permissions"],
    ),
}
