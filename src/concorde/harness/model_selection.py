"""Resolve defaults and per-terminal-worker model, thinking and timeout overrides."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..spec.typed_data import TypedDataError

THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")


@dataclass(frozen=True)
class WorkerSelection:
    model: str | None = None
    thinking: str | None = None
    timeout_seconds: int | None = None

    def wire(self) -> dict:
        return asdict(self)


def _narrow(selection: WorkerSelection, entry: dict) -> WorkerSelection:
    return WorkerSelection(
        entry.get("model", selection.model),
        entry.get("thinking", selection.thinking),
        entry.get("timeout_seconds", selection.timeout_seconds),
    )


def worker_selection(configuration: dict, agent: str) -> WorkerSelection:
    """Resolve one worker's selection; ``agent`` may be bare, hyphenated or external."""
    from .worker_profile import worker_key

    data = configuration["data"]
    selection = WorkerSelection(
        data.get("model"), data.get("thinking"), data.get("timeout_seconds")
    )
    workers = data.get("workers", {})
    name = worker_key(agent)
    if name in workers:
        selection = _narrow(selection, workers[name])
    return selection


def _pointer(field: str, key: str) -> str:
    return f"{field}/data/workers/" + key.replace("~", "~0").replace("/", "~1")


def validate_worker_selections(
    configuration: dict, field: str = "/configuration"
) -> None:
    """Reject keys naming no worker, bad timeouts and non-Pi model names."""
    from .worker_profile import load_worker_profiles

    agents = load_worker_profiles()
    data = configuration["data"]
    workers = data.get("workers", {})
    for key, entry in workers.items():
        if key not in agents:
            raise TypedDataError(
                "invalid_field",
                _pointer(field, key),
                "names no terminal worker; worker-child overrides are retired",
            )
    for location, entry in (
        (f"{field}/data", data),
        *((_pointer(field, key), entry) for key, entry in workers.items()),
    ):
        if "timeout_seconds" in entry and entry["timeout_seconds"] <= 0:
            raise TypedDataError(
                "invalid_field",
                f"{location}/timeout_seconds",
                "a timeout must be positive",
            )
        if "model" in entry and "/" not in entry["model"].strip("/"):
            raise TypedDataError(
                "invalid_field",
                f"{location}/model",
                "a model is Pi's provider/id, such as openai-codex/gpt-6-astra",
            )
