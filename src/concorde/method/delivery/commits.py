"""The delivery commit: its message, its output, and reading the earlier delivery commits back
from Git.

A delivery commit is recognised by its subject, ``concorde: deliver <workspace>``, alone; it is
the only record of a delivery.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

COMMIT = {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"}
TEXT = {"type": "string", "minLength": 1}

OUTPUT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["commit", "branch", "sequence", "recovered"],
    "properties": {
        "commit": COMMIT,
        "branch": TEXT,
        "sequence": {"type": "integer", "minimum": 1},
        "recovered": {"type": "boolean"},
    },
}

SUBJECT = "concorde: deliver {workspace}"


def commit_message(workspace: dict) -> str:
    return (
        f"{SUBJECT.format(workspace=workspace['workspace'])}\n\n"
        f"{workspace['goal'].strip()}\n"
    )


def delivery_commits(
    worktree: Path, base: str | None, head: str, workspace: str | None
) -> list[dict]:
    """The delivery commits of ``workspace`` between ``base`` and ``head`` on the first-parent
    history, oldest first, each as ``{"commit": ...}``.

    A delivery commit is one whose subject is exactly ``concorde: deliver <workspace>``.
    """
    if not workspace:
        return []
    span = f"{base}..{head}" if base else head
    result = subprocess.run(
        ["git", "log", "--first-parent", "--reverse", "--format=%H%x1f%s", span],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    )
    subject = SUBJECT.format(workspace=workspace)
    found = []
    for line in result.stdout.splitlines():
        commit, _, text = line.partition("\x1f")
        if text.strip() == subject:
            found.append({"commit": commit.strip()})
    return found


def delivery_mismatches(worktree: Path, delivery: dict) -> list[str]:
    """How the delivery commit ``delivery`` (as ``delivery_commits`` reads it) fails to be one
    Delivery could have created; empty when it verifies, which it does when it has exactly one
    parent."""
    listed = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", delivery["commit"]],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    parents = listed[1:]
    if len(parents) == 1:
        return []
    return [
        f"it has {len(parents)} parent(s) ({', '.join(parents) or 'none'}) instead of one"
    ]


__all__ = [
    "OUTPUT_SCHEMA",
    "SUBJECT",
    "commit_message",
    "delivery_commits",
    "delivery_mismatches",
]
