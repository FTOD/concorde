"""The guidance composed of the parts: the project skill, the task-session prompt and the
``CLAUDE.md`` block.

Each part registers up to three rendered sections under ``guidance`` (``skill``, ``task_session``
and ``claude_md``). A composition is Coordination's section followed by every other part's section
of that kind, in the order of Distribution's parts table, each unchanged and separated by one blank
line; a part that is not in the set contributes nothing, and without Coordination there is no
task-session prompt. The skill carries the Agent Skills front
matter of the ``concorde`` skill. The build composes for every part of the package and the installer
for the parts it installs, both through ``compose``.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from .parts import GUIDANCE_FIELDS, Registration

# The order of Distribution's parts table, after Coordination, whose working method comes first; a
# part the table does not name follows by name.
ORDER = (
    "coordination",
    "spec",
    "kernel",
    "worker harness",
    "execution",
    "workflow",
    "issues",
    "method",
    "distribution",
)
SKILL = "concorde"
# Where the build places the task-session prompt it composes for every part, and the installer the
# one it composes for the installed parts, in its Framework copy: Coordination reads it there.
TASK_SESSION = "generated/guidance/task-session.md"
DESCRIPTIONS = {
    True: (
        "Work as Concorde's main agent in this project: split work into tasks, hand each "
        "to a task session and answer it, read results, keep decision logs and merge "
        "delivered work."
    ),
    False: (
        "Use the Concorde parts installed in this project: their commands, tools and the "
        "records they keep."
    ),
}


class GuidanceError(ValueError):
    """A registered section that cannot be read."""


def skill_header(name: str, description: str) -> str:
    """The Agent Skills front matter of a skill.

    The description is written as a JSON string, which YAML reads as a double-quoted scalar: its
    ": " would otherwise make the front matter invalid YAML, which skill readers refuse.
    """
    return f"---\nname: {name}\ndescription: {json.dumps(description)}\n---\n\n"


def _rank(registration: Registration) -> tuple[int, str]:
    part = registration.part
    return (ORDER.index(part) if part in ORDER else len(ORDER), part)


def sections(registrations: dict[str, Registration], kind: str) -> list[str]:
    """The rendered sections of ``kind`` the given parts register, in composition order."""
    if kind not in GUIDANCE_FIELDS:
        raise GuidanceError(f"no guidance section is of kind {kind!r}")
    found = []
    for registration in sorted(registrations.values(), key=_rank):
        guidance = registration.data["guidance"]
        if guidance is not None and guidance[kind] is not None:
            found.append(guidance[kind])
    return found


def compose(
    registrations: dict[str, Registration], kind: str, read: Callable[[str], str]
) -> str | None:
    """The guidance of ``kind`` composed of the given parts' sections, each read with ``read``
    from its build-relative path, or None when none of them contributes one. Task sessions are
    Coordination's, so without the coordination part there is no task-session prompt."""
    paths = sections(registrations, kind)
    if not paths or (kind == "task_session" and "coordination" not in registrations):
        return None
    body = "\n\n".join(read(path).strip("\n") for path in paths) + "\n"
    if kind == "skill":
        return skill_header(SKILL, DESCRIPTIONS["coordination" in registrations]) + body
    return body


__all__ = [
    "DESCRIPTIONS",
    "GuidanceError",
    "ORDER",
    "SKILL",
    "TASK_SESSION",
    "compose",
    "sections",
    "skill_header",
]
