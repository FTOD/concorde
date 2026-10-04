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
    # Resolve every symbolic link, the final one included, even when its target does not exist
    # yet: a write is judged by the file it would change, never by a link's own name.
    resolved = os.path.realpath(absolute)
    worktree = grant["worktree"]
    if resolved != worktree and not resolved.startswith(worktree + "/"):
        if os.path.islink(absolute):
            return (
                f"{target} is a symbolic link to {resolved}, outside the task worktree"
            )
        return f"{target} is outside the task worktree"
    relative = resolved[len(worktree) + 1 :]
    # The worktree's own .git and every submodule's, at any depth.
    if ".git" in relative.split("/"):
        return "Git metadata is not available to workers"

    # The most specific entry decides: an exact entry, else the longest directory entry above.
    levels = ("rw", "ro", "names")
    level = next((name for name in levels if relative in grant[name]), None)
    if level is None:
        covering = [
            (len(path), name)
            for name in levels
            for path in grant[name]
            if path.endswith("/") and relative.startswith(path)
        ]
        level = max(covering)[1] if covering else None
    if level == "rw":
        return None
    # A denial through a final link names the file judged and the link it was reached by.
    named = (
        f"{relative} (the target of the symbolic link {target})"
        if os.path.islink(absolute)
        else relative
    )
    if level == "ro":
        return f"{named} is read-only for this task"
    if level == "names":
        return f"only the name of {named} is visible to this task"
    return (
        f"{named} is not in this task's grant; a new file outside the bound directories is "
        "created and bound to a Module by the task level before a worker fills it, and a "
        "file another Module binds needs that Module bound to the task"
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
