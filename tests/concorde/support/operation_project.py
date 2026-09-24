"""A committed fixture project with an open task, for tests that run Operations end to end.

The project has Module A (``src/a/``, pending ``src/new.py``, a configured check that passes while
``src/a/flag`` is absent or says ``ok``) and Module B (``src/bmod/``). ``open_task`` creates a task
through the Task store; ``run`` runs ``concorde run`` in-process with the fake ``claude`` of the
worker tests, whose plan is taken from ``FAKE-PLAN: <json>`` in the brief.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

from concorde.operations.host import execute
from concorde.tasks import store
from tests.concorde.harness.workers.test_workers import WorkerProject


def worker_error(
    detail: str,
    *,
    code: str = "spec_gap",
    reason: str = "decision",
    attempts=(),
    options=(),
    recommendation: str = "",
) -> dict:
    """The ``error`` of a fake worker result."""
    return {
        "code": code,
        "detail": detail,
        "evidence": [],
        "attempts": list(attempts),
        "unhandled": {"reason": reason, "explanation": f"{reason}: {detail}"},
        "options": list(options),
        "recommendation": recommendation,
    }


def link_at(error: dict, level: str) -> dict | None:
    """The first link of ``level`` in the error tree, depth first."""
    if error["level"] == level:
        return error
    for cause in error["causes"]:
        found = link_at(cause, level)
        if found is not None:
            return found
    return None


def commit(root: Path, message: str = "change") -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class OperationProject(WorkerProject):
    """``WorkerProject`` plus task and Operation helpers; ``home`` isolates deny rules."""

    def __init__(self, test, **options):
        super().__init__(test, **options)
        self.test = test

    def open_task(
        self, task_id: str = "t1", modules=("module.a",), goal="Fix A."
    ) -> dict:
        return store.open_task(self.root, task_id, goal, list(modules))

    def worktree(self, task_id: str = "t1") -> Path:
        return Path(store.load_task(self.root, task_id)["worktree"])

    def run(
        self, *argv: str, cwd: Path | None = None, client: str | None = "claude"
    ) -> tuple[int, dict | None]:
        """Run ``concorde run <argv>`` with the fake claude and this project's home, as if
        started from a main session of ``client``, or from no main session when it is None."""
        values = {"CONCORDE_CLAUDE": str(self.fake)}
        if client:
            values["CONCORDE_CLIENT"] = client
        with (
            patch.dict(os.environ, values),
            patch("pathlib.Path.home", return_value=self.home),
        ):
            if not client:
                for name in (
                    "CONCORDE_CLIENT",
                    "CLAUDECODE",
                    "PI_SESSION_ID",
                    "PI_CODING_AGENT",
                ):
                    os.environ.pop(name, None)
            return execute(list(argv), cwd=cwd or self.root)

    @staticmethod
    def plan(steps) -> str:
        """A goal text carrying the fake worker's plan."""
        return "Do the task.\nFAKE-PLAN: " + json.dumps(steps)


__all__ = ["OperationProject", "commit", "link_at", "worker_error"]
