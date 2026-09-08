"""Render known handoff facts without reading another worktree or granting authority.

The ambient conversation completes/localizes this draft under Protocol P10. This is
presentation inside existing error messages, never a new worker input contract.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

UNKNOWN = "Unknown to the runtime; the originating conversation must supply known details."


def handoff_prompt(
    path: str | Path, *, branch: str | None = None, change_id: str | None = None,
    task: str | None = None, constraints: list[str] | None = None,
    completed: str | None = None, remaining: str | None = None,
    checks: str | None = None, artifacts: list[dict] | None = None,
    next_steps: str | None = None, completion: str | None = None,
) -> str:
    # Absolute paths are supplied by the host; do not resolve/stat/read the destination.
    if not Path(path).is_absolute():
        raise ValueError("handoff initial directory must be absolute")
    facts = {
        "Initial working directory": str(path), "Branch": branch or UNKNOWN,
        "Change ID": change_id or UNKNOWN, "Original task and accepted scope": task or UNKNOWN,
        "User constraints and authorizations": constraints if constraints is not None else UNKNOWN,
        "Completed / changes already applied": completed or UNKNOWN,
        "Remaining work": remaining or UNKNOWN, "Checks passed / failed / not run": checks or UNKNOWN,
        "Patch / handoff artifacts (absolute paths, applied state, temporary storage)":
            artifacts if artifacts is not None else UNKNOWN,
    }
    text = ("Start an independent agent session with the stated initial working directory, fresh "
            "context and that worktree's own Skills. Do not inherit the old conversation or Skill bodies.\n"
            "First read this worktree's AGENTS.md and CLAUDE.md where present, and follow its "
            "Protocol entry. Perform the policy's affinity verification using this new runtime's "
            "advertised Skill path where required; do not reuse the old session's Skill body or path.\n"
            + json.dumps(facts, ensure_ascii=False, indent=2) + "\n"
            + "Next concrete steps: " + (next_steps or UNKNOWN) + "\n"
            + "Completion criteria: " + (completion or UNKNOWN) + "\n"
            + "This handoff grants no additional reads, writes, merge, or delivery authority. "
            "Review any saved patch before applying it; do not reapply changes already present.\n")
    fence = "`" * max(3, 1 + max((len(m.group()) for m in re.finditer(r"`+", text)), default=0))
    return ("The outer agent must start the new session automatically under P10. Only if automatic "
            "startup is unavailable or cannot establish the required isolation, ask the user to "
            "open a new agent manually with the complete prompt. This draft does not launch a session.\n"
            "Protocol P10 handoff draft: the originating conversation must complete known details "
            "and render the final copyable prompt in the user's language.\n\n"
            + fence + "text\n" + text + fence)
