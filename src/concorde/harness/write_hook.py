"""The write hook: a Claude Code PreToolUse hook that allows Edit and Write only on ``rw`` paths.

The host copies this file into a run's ``control/`` directory with the grant's lists embedded in
``GRANT`` and registers it for Edit and Write. It reads the hook input on standard input and
prints nothing for an allowed path, so the permission mode decides as usual; for any other path it
prints a ``deny`` decision whose reason tells the worker why. Any failure denies.
"""

import json
import os
import sys

GRANT: dict = {}


def decide(data: dict, grant: dict) -> str | None:
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
    worktree = grant["worktree"]
    if resolved != worktree and not resolved.startswith(worktree + "/"):
        return f"{target} is outside the task worktree"
    relative = resolved[len(worktree) + 1 :]

    def listed(level: str) -> bool:
        return any(
            relative == path or (path.endswith("/") and relative.startswith(path))
            for path in grant[level]
        )

    if listed("rw"):
        return None
    if listed("ro"):
        return f"{relative} is read-only for this task"
    if listed("names"):
        return f"only the name of {relative} is visible to this task"
    return (
        f"{relative} is undeclared; it must first be declared as a pending file of a Module "
        "through a specify task"
    )


def main() -> int:
    try:
        reason = decide(json.load(sys.stdin), GRANT)
    except Exception as error:  # noqa: BLE001 -- any failure denies
        reason = f"the hook could not decide: {error}"
    if reason is not None:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "Concorde grant: " + reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
