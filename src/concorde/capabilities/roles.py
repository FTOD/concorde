"""Frozen role identities and their exact effect declarations (proposal section 5).

A ``Role`` names one launchable agent identity: a repository-relative root prompt under
``prompts/`` plus its exact ``EffectDeclaration``. Roles are Python data, not Markdown front
matter: the policy compiler consumes ``Role.effects`` directly, and nothing about authority is
parsed from a Skill body at run time. A role's rendered instructions live at
``generated/roles/<hyphenated-name>.md``; ``build.load_role_prompt`` is the only host-facing way
to obtain a role's instructions and effects together, and it verifies build freshness first.
"""

from __future__ import annotations

from dataclasses import dataclass

from .effects import EffectDeclaration


@dataclass(frozen=True)
class Role:
    """One launchable agent identity: its root prompt and exact authority."""

    name: str
    prompt: str
    effects: EffectDeclaration


COORDINATOR = Role(
    name="coordinator",
    prompt="prompts/workflow-host/coordinator.md",
    effects=EffectDeclaration(("discovery-context",), (), False, "none"),
)
READER = Role(
    name="reader",
    prompt="prompts/spec-context/reader.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
SPEC_AUTHOR = Role(
    name="spec_author",
    prompt="prompts/spec-context/spec-author.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
CONTEXT_ASSESSOR = Role(
    name="context_assessor",
    prompt="prompts/spec-context/context-assessor.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
PLANNER = Role(
    name="planner",
    prompt="prompts/workflow-host/planner.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
TASK_AUTHOR = Role(
    name="task_author",
    prompt="prompts/workflow-host/task-author.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
IMPLEMENTATION_WORKER = Role(
    name="implementation_worker",
    prompt="prompts/workflow-host/implementation-worker.md",
    effects=EffectDeclaration(("spec-context", "implementation"), ("implementation",), False, "none"),
)
SPEC_REVIEWER = Role(
    name="spec_reviewer",
    prompt="prompts/workflow-host/spec-reviewer.md",
    effects=EffectDeclaration(("spec-context",), (), False, "none"),
)
CODE_REVIEWER = Role(
    name="code_reviewer",
    prompt="prompts/workflow-host/code-reviewer.md",
    effects=EffectDeclaration(("spec-context", "implementation"), (), False, "none"),
)

ROLES: dict[str, Role] = {
    role.name: role
    for role in (
        COORDINATOR,
        READER,
        SPEC_AUTHOR,
        CONTEXT_ASSESSOR,
        PLANNER,
        TASK_AUTHOR,
        IMPLEMENTATION_WORKER,
        SPEC_REVIEWER,
        CODE_REVIEWER,
    )
}
ROLE_NAMES: tuple[str, ...] = tuple(ROLES)


def external_role_name(role_name: str) -> str:
    """Return the ``concorde-<hyphenated>`` external identity for one role."""

    return "concorde-" + ROLES[role_name].name.replace("_", "-")


def role_key(name: str) -> str:
    """Normalize an external (``concorde-spec-author``) or bare (``spec-author``) role name."""

    key = name[len("concorde-"):] if name.startswith("concorde-") else name
    return key.replace("-", "_")
