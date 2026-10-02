"""The delivery commit: the one mark of a delivery, recognized by its subject alone.

A commit is a delivery commit of a workspace when it lies on the first-parent history of the
workspace's branch since its base commit and its subject is exactly ``concorde: deliver
<workspace>``; its body is the workspace's goal. It verifies only when it has exactly one parent, so
a merge commit carrying the subject is never taken for one. Who may make one, and what it checks
first, is the delivering command's rule, never the Kernel's
(``specs/concorde/kernel/contracts.md#delivery-commit``).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .refusal import KernelError

SUBJECT = "concorde: deliver {workspace}"


def subject(workspace: str) -> str:
    """The subject of a delivery commit of ``workspace``."""
    return SUBJECT.format(workspace=workspace)


def message(workspace: str, goal: str) -> str:
    """The whole message of a delivery commit of ``workspace`` with its goal."""
    return f"{subject(workspace)}\n\n{goal.strip()}\n"


def deliveries(worktree: Path, branch: str, base: str, workspace: str) -> list[dict]:
    """The delivery commits of ``workspace`` on the first-parent history of ``branch`` since
    ``base``, oldest first, each ``{"commit", "mismatches"}`` where ``mismatches`` says how it
    fails to verify and is empty when it does.

    ``git_failed`` when Git cannot list the history, naming the command and its output.
    """
    command = [
        "git",
        "log",
        "--first-parent",
        "--reverse",
        "--format=%H%x1f%P%x1f%s",
        f"{base}..{branch}",
    ]
    try:
        result = subprocess.run(
            command, cwd=worktree, capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise KernelError(
            "git_failed",
            f"`{' '.join(command)}` could not run in {worktree}: {error}",
            field=str(worktree),
            causes=[error],
        ) from error
    if result.returncode != 0:
        raise KernelError(
            "git_failed",
            f"`{' '.join(command)}` failed in {worktree} with exit status "
            f"{result.returncode}: {(result.stderr or result.stdout).strip() or 'no output'}",
            field=str(worktree),
        )
    wanted = subject(workspace)
    found = []
    for line in result.stdout.splitlines():
        commit, _, rest = line.partition("\x1f")
        parents, _, text = rest.partition("\x1f")
        if text.strip() != wanted:
            continue
        parents = parents.split()
        found.append(
            {
                "commit": commit.strip(),
                "mismatches": []
                if len(parents) == 1
                else [
                    f"it has {len(parents)} parent(s) ({', '.join(parents) or 'none'}) "
                    "instead of one"
                ],
            }
        )
    return found


__all__ = ["SUBJECT", "deliveries", "message", "subject"]
