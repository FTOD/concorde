"""Concorde's Agent inventory: one Python package per Pi worker.

Each ``agents/<name>/__init__.py`` declares ``AGENT``, the worker profile of one task contract
(``concorde.harness.agent_model.Agent``); its role Spec is ``agents/<name>/spec.md`` and its
lightweight children are pi-subagents Markdown definitions under ``agents/<name>/children/``.

A module named here with no matching ``agents/<name>/__init__.py`` package, or a package present
with no matching name here, is a validation error (``CONCORDE-AGENT-INVENTORY-001``).
"""

from __future__ import annotations

AGENTS = (
    "answerer",
    "router",
    "topology_designer",
    "spec_author",
    "topology_author",
    "spec_reviewer",
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "code_reviewer",
    "investigator",
)


def external_name(module_name: str) -> str:
    """Return the ``concorde-<hyphenated>`` identity an Agent module's name derives."""

    return "concorde-" + module_name.replace("_", "-")
