"""The coordination part's report after an update, which its part registration names: the tasks
that have not ended, which an update result lists so that the primary branch is merged into each
when the Protocol copy changed."""

from __future__ import annotations

import json
from pathlib import Path

from .store import TASKS


def open_tasks(project) -> list[dict]:
    """The tasks of ``project`` that have not ended, from their records, in their folders' order:
    each with its identity, branch and worktree, None where the record lacks one."""
    found = []
    for path in sorted((Path(project) / ".concorde" / TASKS).glob("*/task.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            isinstance(record, dict)
            and isinstance(record.get("id"), str)
            and record.get("state") not in ("closed", "failed")
        ):
            found.append(
                {
                    "id": record["id"],
                    "branch": record.get("branch"),
                    "worktree": record.get("worktree"),
                }
            )
    return found


__all__ = ["open_tasks"]
