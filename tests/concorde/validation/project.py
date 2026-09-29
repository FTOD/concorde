"""A task fixture whose committed Specs validate without errors, for task-validation and delivery
tests.

It extends ``OperationProject``: ``checks/`` and ``.gitignore`` are bound to Module A so that the
base commit has no unbound file, the repository has an author identity for delivery commits, and
``shared=True`` adds ``src/shared.py`` bound by A and B with a configured check of B.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from concorde.tasks import store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.spec_project import (
    read_checks,
    set_realization,
    write_checks,
)


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class ValidationProject(OperationProject):
    def __init__(self, test, *, shared: bool = False):
        super().__init__(test)
        root = self.root
        set_realization(
            root, "realization.a.code", entries=["src/a/", "checks/", ".gitignore"]
        )
        if shared:
            (root / "src/shared.py").write_text("SHARED = 1\n")
            (root / "checks/b_check.py").write_text("raise SystemExit(0)\n")
            set_realization(
                root,
                "realization.a.code",
                entries=["src/a/", "checks/", ".gitignore", "src/shared.py"],
            )
            set_realization(
                root, "realization.b.code", entries=["src/bmod/", "src/shared.py"]
            )
            write_checks(
                root,
                [
                    *read_checks(root),
                    {
                        "id": "check.b",
                        "module": "module.b",
                        "argv": ["{python}", "checks/b_check.py"],
                        "timeout_seconds": 30,
                        "inputs": ["checks/b_check.py"],
                    },
                ],
            )
        git(root, "config", "user.name", "Delivery Test")
        git(root, "config", "user.email", "delivery@test")
        self.base_commit = commit(root, "bind the fixture")

    def task(self, task_id: str = "t1", modules=("module.a",)) -> Path:
        """Open a task and return its worktree."""
        self.open_task(task_id, modules)
        return self.worktree(task_id)

    def record(self, task_id: str = "t1") -> dict:
        return store.load_task(self.root, task_id)

    def state(self, task_id: str = "t1") -> str:
        """The task's derived state."""
        return store.show_task(self.root, task_id)["record"]["state"]

    def deliveries(self, task_id: str = "t1") -> list[dict]:
        """The delivery commits of the task's workspace on its branch, read from Git."""
        return store.deliveries(self.root, self.record(task_id))

    def validate(self, task_id: str = "t1", *extra: str):
        """``concorde task-validation`` in the task's worktree."""
        return self.run("task-validation", "--task", task_id, *extra)

    def deliver(self, task_id: str = "t1", *extra: str):
        """``concorde delivery`` in the task's worktree."""
        return self.run("delivery", "--task", task_id, *extra)


def evidence_of(envelope: dict, kind: str) -> list[dict]:
    return [item for item in envelope["host_evidence"] if item["kind"] == kind]


def run_folder(envelope: dict) -> Path:
    """The run's trace node folder, which the first host evidence of every run names."""
    first = envelope["host_evidence"][0]
    assert (first["kind"], first["ref"]) == ("trace", envelope["run_id"]), first
    return Path(first["detail"])


def workspace_run(root: Path, envelope: dict, task_id: str = "t1") -> Path:
    """The run's node folder in the workspace folder of task ``task_id`` of primary ``root``,
    checked against the folder the run reports."""
    folder = root / ".concorde/tasks" / task_id / "workspace/runs" / envelope["run_id"]
    assert run_folder(envelope) == folder, (run_folder(envelope), folder)
    return folder


def status_lines(worktree: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


__all__ = [
    "ValidationProject",
    "evidence_of",
    "git",
    "run_folder",
    "status_lines",
    "workspace_run",
]
