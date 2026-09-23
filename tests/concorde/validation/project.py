"""A task fixture whose committed Specs validate without errors, for validate and delivery tests.

It extends ``OperationProject``: ``checks/`` and ``.gitignore`` are bound to Module A so that the
base commit has no unbound file, the repository has an author identity for delivery commits, and
``shared=True`` adds ``src/shared.py`` bound by A and B with a configured check of B.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from concorde.tasks import store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.spec_project import set_realization


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
            config = json.loads((root / ".concorde/config.json").read_text())
            config["checks"].append(
                {
                    "id": "check.b",
                    "module": "module.b",
                    "argv": ["{python}", "checks/b_check.py"],
                    "timeout_seconds": 30,
                    "inputs": ["checks/b_check.py"],
                }
            )
            (root / ".concorde/config.json").write_text(
                json.dumps(config, indent=2) + "\n"
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

    def validate(self, task_id: str = "t1", *extra: str):
        return self.run("validate", "--task", task_id, *extra)

    def deliver(self, task_id: str = "t1"):
        return self.run("delivery", "--task", task_id)


def evidence_of(envelope: dict, kind: str) -> list[dict]:
    return [item for item in envelope["host_evidence"] if item["kind"] == kind]


def status_lines(worktree: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


__all__ = ["ValidationProject", "evidence_of", "git", "status_lines"]
