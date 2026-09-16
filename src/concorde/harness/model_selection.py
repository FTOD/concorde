"""Per-worker Pi model selection: the model, thinking level and timeout of every worker and child.

The project capability configuration names a default Pi ``model`` (``provider/id``), ``thinking``
level and ``timeout_seconds`` and, under ``workers``, overrides keyed either by a worker
(``programmer``) or by one of its children (``programmer/scout``). A worker resolves the default,
then its own entry; a child resolves its worker's selection, then its own entry, each value
independently, so the most specific entry wins. A child's timeout is its worker's, so a child entry
names no timeout. An absent model or thinking level keeps Pi's own default, and an absent timeout
keeps the worker profile's.
"""
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
    return WorkerSelection(entry.get("model", selection.model), entry.get("thinking", selection.thinking),
                           entry.get("timeout_seconds", selection.timeout_seconds))


def worker_selection(configuration: dict, agent: str, child: str | None = None) -> WorkerSelection:
    """Resolve one worker's or one child's selection; ``agent`` may be bare, hyphenated or external."""
    from .worker_profile import worker_key

    data = configuration["data"]
    selection = WorkerSelection(data.get("model"), data.get("thinking"), data.get("timeout_seconds"))
    workers = data.get("workers", {})
    name = worker_key(agent)
    for key in (name, f"{name}/{child}" if child is not None else None):
        if key in workers:
            selection = _narrow(selection, workers[key])
    return selection


def _pointer(field: str, key: str) -> str:
    return f"{field}/data/workers/" + key.replace("~", "~0").replace("/", "~1")


def validate_worker_selections(configuration: dict, field: str = "/configuration") -> None:
    """Reject keys naming no worker or child, child timeouts, bad timeouts and non-Pi model names."""
    from .worker_profile import load_worker_profiles

    agents = load_worker_profiles()
    children = {f"{name}/{child.name}" for name, agent in agents.items() for child in agent.children}
    data = configuration["data"]
    workers = data.get("workers", {})
    for key, entry in workers.items():
        if key not in agents and key not in children:
            raise TypedDataError("invalid_field", _pointer(field, key),
                                 "names no worker or worker child; use a worker such as programmer or a "
                                 "child such as programmer/scout")
        if key in children and "timeout_seconds" in entry:
            raise TypedDataError("invalid_field", _pointer(field, key), "a child runs within its worker's timeout")
    for location, entry in ((f"{field}/data", data), *((_pointer(field, key), entry) for key, entry in workers.items())):
        if "timeout_seconds" in entry and entry["timeout_seconds"] <= 0:
            raise TypedDataError("invalid_field", f"{location}/timeout_seconds", "a timeout must be positive")
        if "model" in entry and "/" not in entry["model"].strip("/"):
            raise TypedDataError("invalid_field", f"{location}/model", "a model is Pi's provider/id, such as openai-codex/gpt-6-astra")
