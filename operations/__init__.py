"""Typed executable inventory. Directory/wire spellings `operations` are compatibility names.

Agents are native Pi roles, Workflows are authored pi-subagents compositions, Host tools are finite
deterministic services. LangGraph Operations are separately and explicitly selected StateGraph flows.
"""

from __future__ import annotations

# Compatibility adapter inventory, NOT a catalog of StateGraph Operations.
OPERATIONS = (
    "issues",
    "init",
    "configure",
    "validate",
    "deliver",
    "spec_review",
    "code_review",
    "context_solve",
    "plan",
    "tasks",
    "implement",
)


def external_name(module_name: str) -> str:
    return "concorde-" + module_name.replace("_", "-")


CAPABILITIES = OPERATIONS
WORKFLOWS = ("plan", "spec_review", "code_review", "issues")
HOST_TOOLS = ("init", "configure", "validate", "deliver")
