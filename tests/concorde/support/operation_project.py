"""A committed fixture project with an open task, for tests that run Operations end to end.

The project has Module A (``src/a/``, pending ``src/new.py``, a configured check that passes while
``src/a/flag`` is absent or says ``ok``) and Module B (``src/bmod/``). ``open_task`` creates a task
through the Task store; ``run`` runs an Operation or execution command in-process, in the worktree
of the task a ``--task`` names, with the fake ``claude`` of the worker tests, whose plan is taken
from ``FAKE-PLAN: <json>`` in the brief.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

from concorde.tasks import store
from tests.concorde.support import runs
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


# Every worker on Claude Code, on a model the fake ``claude`` accepts like any other.
CLAUDE_WORKERS = {
    "schema_version": 1,
    "enabled_models": {"sonnet": {}},
    "default": {"backend": "claude", "model": "sonnet"},
}


def claude_workers(root: Path) -> Path:
    """Choose Claude Code for every worker of ``root``, whose workers would otherwise run on pi, so
    that the fake ``claude`` answers them. The worker configuration is tracked, so when ``root``
    already has a commit the choice is committed, for the tasks opened from it to carry."""
    path = root / ".concorde/workers.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(CLAUDE_WORKERS) + "\n")
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if head.returncode == 0:
        subprocess.run(["git", "add", ".concorde/workers.json"], cwd=root, check=True)
        subprocess.run(
            [
                *("git", "-c", "user.name=t", "-c", "user.email=t@t"),
                *("commit", "-qm", "run the workers on Claude Code"),
            ],
            cwd=root,
            check=True,
            capture_output=True,
        )
    return path


class OperationProject(WorkerProject):
    """``WorkerProject`` plus task and Operation helpers; ``home`` isolates deny rules. Its
    workers run on the fake ``claude``: the project's worker configuration chooses Claude
    Code for every worker."""

    def __init__(self, test, **options):
        super().__init__(test, **options)
        self.test = test
        claude_workers(self.root)

    def open_task(
        self, task_id: str = "t1", modules=("module.a",), goal="Fix A."
    ) -> dict:
        return store.open_task(self.root, task_id, goal, list(modules))

    def worktree(self, task_id: str = "t1") -> Path:
        return Path(store.load_task(self.root, task_id)["worktree"])

    def run(
        self,
        *argv: str,
        cwd: Path | None = None,
        environ: dict | None = None,
    ) -> tuple[int, dict | None]:
        """Run ``<name> [--task <task>] [arguments]`` with the fake claude and this project's
        home, in the task's worktree; ``environ`` adds or replaces variables."""
        values = {"CONCORDE_CLAUDE": str(self.fake), **(environ or {})}
        with (
            patch.dict(os.environ, values),
            patch("pathlib.Path.home", return_value=self.home),
        ):
            return runs.run(argv, self.root, cwd)

    @staticmethod
    def plan(steps) -> str:
        """A goal text carrying the fake worker's plan."""
        return "Do the task.\nFAKE-PLAN: " + json.dumps(steps)


__all__ = [
    "OperationProject",
    "claude_workers",
    "commit",
    "link_at",
    "worker_error",
]
