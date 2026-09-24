"""The task-session write hook: a Claude Code PreToolUse hook confining file edits to one task.

``concorde task session`` copies this file next to the session's settings with the task's paths
embedded in ``ALLOWED`` and registers it for Edit and Write. It reads the hook input on standard
input and prints nothing for a path inside the task worktree or the task's decision log, so the
permission mode decides as usual; for any other path it prints a ``deny`` decision whose reason
tells the session why. Any failure denies.
"""

import json
import os
import sys

ALLOWED: dict = {}


def decide(data: dict, allowed: dict) -> str | None:
    """None to allow, or the reason for a denial."""
    tool_input = data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(target, str) or not target:
        return "the hook could not decide: the tool call names no file"
    base = data.get("cwd") or os.getcwd()
    absolute = os.path.normpath(os.path.join(base, target))
    # Resolve every directory, but not a final symbolic link: a link is judged by its own name.
    parent = os.path.realpath(os.path.dirname(absolute))
    resolved = os.path.join(parent, os.path.basename(absolute))
    worktree = allowed["worktree"]
    if resolved == worktree or resolved.startswith(worktree + "/"):
        return None
    if resolved in allowed["files"]:
        return None
    return (
        f"{target} is outside the worktree of task {allowed['task']} ({worktree}); a task "
        "session changes only its own worktree and decision log, and asks the main agent for "
        "anything else"
    )


def main() -> int:
    try:
        reason = decide(json.load(sys.stdin), ALLOWED)
    except Exception as error:  # noqa: BLE001 -- any failure denies
        reason = f"the hook could not decide: {error}"
    if reason is not None:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "Concorde task session: " + reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
