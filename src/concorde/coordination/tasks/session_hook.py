"""The task-session write hook: a Claude Code PreToolUse hook confining file edits to one task.

``concorde task session`` copies this file next to the session's settings with the task's paths
embedded in ``ALLOWED`` and registers it for the file-writing tools Edit, Write, MultiEdit and
NotebookEdit. It reads the hook input on standard input and prints nothing for a path inside the
task worktree or the task's decision log while the task's folder exists, so the permission mode
decides as usual; for any other path, a symbolic link judged by the file it points to, it prints a
``deny`` decision whose reason tells the session why.
Any failure denies.
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
    joined = os.path.join(data.get("cwd") or os.getcwd(), target)
    # Resolve the whole path, a final symbolic link included: Edit and Write write through a
    # link, so a link is judged by the file it points to. The operating system resolves each link
    # before the `..` that follows it, which then leaves the directory the link points to, while a
    # tool that collapses `..` first reaches another file: the path is allowed only when both
    # readings are.
    for resolved in (
        os.path.realpath(joined),
        os.path.realpath(os.path.normpath(joined)),
    ):
        reason = judge(resolved, target, allowed)
        if reason is not None:
            return reason
    return None


def judge(resolved: str, target: str, allowed: dict) -> str | None:
    """None to allow the file ``resolved``, ``target`` resolved, or the reason for a denial."""
    worktree = allowed["worktree"]
    if resolved == worktree or resolved.startswith(worktree + "/"):
        return None
    if resolved in allowed["files"]:
        if not os.path.isdir(os.path.dirname(resolved)):
            # The task was closed: its folder moved to the history, which nothing changes.
            return (
                f"{target} is the decision log of task {allowed['task']}, which is closed: its "
                "folder moved to the history, which is never changed"
            )
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
