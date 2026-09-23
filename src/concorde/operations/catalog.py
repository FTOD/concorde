"""The Operation catalog: the declared capabilities, their tables and their typed values.

The catalog loads the declarations the repository-root ``operations`` package lists, together with
the Domain Agent modules the dispatch still reaches by their wire names, and derives the tables
admission and dispatch read. ``register_types`` is the one explicit registration entry of every
process that checks typed values: it loads each owner's record module, which registers the owner's
types with Spec tooling, and registers every declaration's request and response.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from ..spec.typed_data import register


def load_operation_inventory():
    """Import the repository-root ``operations`` package normally.

    ``tests/concorde`` holds one flat package per Module and none of them is named
    ``operations``, so test collection never registers an unrelated package under that name.
    """

    package_root = Path(__file__).resolve().parents[3]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    import operations

    return operations


# Each bound operation stage runs the one worker whose contract names that phase.
MODEL_STAGES = {
    "concorde-plan": ("plan", "concorde-planner"),
    "concorde-tasks": ("tasks", "concorde-task-author"),
    "concorde-implement": ("implementation", "concorde-programmer"),
    "concorde-context-solve": ("context-solve", "concorde-context-assessor"),
    "concorde-issues": ("issue-solve", "concorde-issue-solver"),
}
# The two public review operations fix the review kind; callers cannot select it in task data.
REVIEW_OPERATIONS = {
    "concorde-spec-review": "spec",
    "concorde-code-review": "code",
}
REVIEW_STAGES = {
    "spec": ("spec-review", "concorde-spec-reviewer"),
    "code": ("code-review", "concorde-code-reviewer"),
}


def operation_modules() -> dict:
    """Every declaration by its wire name: the capabilities and the Domain Agent modules."""
    inventory = load_operation_inventory()
    import agents

    assert not set(inventory.OPERATIONS).intersection(agents.DOMAIN_AGENTS), (
        "capability and Agent identities must be disjoint"
    )
    return {
        **{
            inventory.external_name(name): importlib.import_module(
                f"{inventory.__name__}.{name}"
            )
            for name in inventory.OPERATIONS
        },
        **{
            agents.external_name(name): importlib.import_module(f"agents.{name}")
            for name in agents.DOMAIN_AGENTS
        },
    }


_MODULES = operation_modules()
OPERATION_NAMES = tuple(sorted(_MODULES))
PUBLIC_OPERATIONS = tuple(name for name in OPERATION_NAMES if _MODULES[name].PUBLIC)
INTERNAL_OPERATIONS = tuple(
    name for name in OPERATION_NAMES if not _MODULES[name].PUBLIC
)
DETERMINISTIC_OPERATIONS = frozenset(
    name for name in OPERATION_NAMES if _MODULES[name].DETERMINISTIC
)
COMPOSITE_OPERATIONS = tuple(name for name in OPERATION_NAMES if _MODULES[name].USES)
MODEL_OPERATIONS = tuple(
    name for name in OPERATION_NAMES if _MODULES[name].PROFILE is not None
)
# Every capability with a request/response pair: name -> (request type, response type).
OPERATION_CONTRACTS = {
    name: (f"{name}-request", f"{name}-response")
    for name in OPERATION_NAMES
    if hasattr(_MODULES[name], "REQUEST")
}


def dependencies(operation: str) -> tuple[str, ...]:
    module = _MODULES[operation]
    return tuple("concorde-" + name.replace("_", "-") for name in module.USES)


# The owners' record modules; loading one registers that owner's typed values.
RECORD_MODULES = (
    "..spec.initialize",
    "..harness.configuration",
    "..harness.context",
    "..harness.native_result",
    "..issues.shapes",
    "..planning.records",
    "..review.records",
)


def register_types() -> tuple[str, ...]:
    """Register every owner's typed values and every declaration's request and response.

    Idempotent; returns the registered request and response type identities in catalog order.
    """
    for name in RECORD_MODULES:
        importlib.import_module(name, __package__)
    registered = []
    for name, (request, response) in OPERATION_CONTRACTS.items():
        module = _MODULES[name]
        register(request, module.REQUEST_VERSION, module.REQUEST)
        register(response, module.RESPONSE_VERSION, module.RESPONSE)
        registered.extend((request, response))
    return tuple(registered)
