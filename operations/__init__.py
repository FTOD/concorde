"""Typed executable inventory. Directory/wire spellings `operations` are compatibility names.

Agents are native Pi roles, Workflows are authored pi-subagents compositions, Host tools are finite
deterministic services. LangGraph Operations are separately and explicitly selected StateGraph flows.
"""

from __future__ import annotations

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
    "spec_reviewer",
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "code_reviewer",
    "issue_solver",
)


def external_name(module_name: str) -> str:
    return "concorde-" + module_name.replace("_", "-")


AGENTS = (
    "spec_reviewer",
    "context_assessor",
    "planner",
    "task_author",
    "programmer",
    "code_reviewer",
    "issue_solver",
)
CAPABILITIES = tuple(name for name in OPERATIONS if name not in AGENTS)
WORKFLOWS = ("plan", "spec_review", "code_review", "issues")
HOST_TOOLS = ("init", "configure", "validate", "deliver")
STATE_OPERATIONS = ("terminal_agent_operation",)
