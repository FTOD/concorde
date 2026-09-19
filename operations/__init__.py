"""The single inventory of executable LangGraph Operations.

Every entry declares PUBLIC, CONTEXT_SELECTION, DETERMINISTIC, USES, STATE and
run(state, runtime). PROFILE is optional model execution configuration, not a second identity.
An Operation may implement a deterministic node, a model node or a composed graph. All
composition names entries in this inventory; no separate AGENTS registry or call relation exists.
Public Skill/wire adapters are separate from the State interface and preserve existing envelopes.
"""

from __future__ import annotations

OPERATIONS = (
    "main",
    "dev_loop",
    "specify_loop",
    "issues",
    "init",
    "configure",
    "validate",
    "deliver",
    "specify",
    "spec_review",
    "code_review",
    "context_solve",
    "plan",
    "tasks",
    "implement",
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
    "issue_solver",
)


def external_name(module_name: str) -> str:
    return "concorde-" + module_name.replace("_", "-")
