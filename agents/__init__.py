"""The Agents inventory: the seven Agents and their definitions.

Each package ``agents/<name>/`` exports exactly ``DEFINITION``, written in the record format Task
context's Agent binding reads, and keeps the Agent's own instructions ``spec.md``.
"""

import importlib

AGENTS = (
    "spec_reviewer",
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "code_reviewer",
    "issue_solver",
)


def _key(name: str) -> str:
    return name.removeprefix("concorde-").replace("-", "_")


def definition(name: str):
    """The checked ``DEFINITION`` of one Agent; a bare, hyphenated or prefixed name."""
    from concorde.harness.worker_profile import validate_definition

    key = _key(name)
    if key not in AGENTS:
        raise KeyError(f"unknown Agent: {name!r}")
    value = importlib.import_module(f"{__name__}.{key}").DEFINITION
    if getattr(value, "name", None) != key:
        raise ValueError(f"agents.{key} does not define DEFINITION with name={key!r}")
    validate_definition(value)
    return value


def external_name(name: str) -> str:
    """``concorde-`` plus the hyphenated name: the Agent definition file a call launches."""
    return "concorde-" + _key(name).replace("_", "-")
