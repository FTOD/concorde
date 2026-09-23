"""The stored operation configuration: its typed value, admission and loading."""

from __future__ import annotations

from pathlib import Path

from ..harness.model_selection import validate_worker_selections
from ..spec.typed_data import (
    STRING,
    TypedDataError,
    checked_path,
    decode,
    obj,
    register,
    validate_typed,
)

CONFIG_PATH = ".concorde/config.json"
CONFIG_TYPE = "concorde-operation-configuration"

# The Pi model selection of a worker: a provider/id model, a thinking level and a timeout. An absent
# value keeps Pi's default model and thinking level and the worker profile's timeout.
_SELECTION = {
    "model": STRING,
    "thinking": {"enum": ["off", "minimal", "low", "medium", "high", "xhigh", "max"]},
    "timeout_seconds": {"type": "integer"},
}
OPERATION_CONFIGURATION = obj(
    {
        **_SELECTION,
        # Overrides keyed by a worker or by one of its children (worker/child); the most specific
        # wins.
        "workers": {
            "type": "object",
            "properties": {},
            "additionalProperties": obj(_SELECTION, tuple(_SELECTION)),
        },
    },
    (*_SELECTION.keys(), "workers"),
)

register(CONFIG_TYPE, 2, OPERATION_CONFIGURATION)


def admit_configuration(value, field: str = "/configuration") -> dict:
    """The typed shape plus a Pi model selection every worker and child can run with."""
    configuration = validate_typed(value, CONFIG_TYPE, field)
    validate_worker_selections(configuration, field)
    return configuration


def load_configuration(project_root: str | Path) -> dict:
    project = Path(project_root)
    if project.is_symlink():
        raise TypedDataError(
            "configuration_mismatch",
            "/configuration",
            "project root may not be a symlink",
        )
    try:
        document = decode(
            checked_path(project, CONFIG_PATH).read_text(encoding="utf-8")
        )
        value = (
            document.get("operation_configuration")
            if isinstance(document, dict)
            else None
        )
        if value is None:
            raise TypedDataError(
                "configuration_mismatch",
                "/configuration",
                "project operation settings are missing; apply an explicit configure proposal",
            )
        return admit_configuration(value)
    except OSError as error:
        raise TypedDataError(
            "configuration_mismatch",
            "/configuration",
            f"cannot load project configuration: {error}",
        ) from error
