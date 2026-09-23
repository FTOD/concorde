"""The transfer change of the Framework acceptance tests, driven through every stage capability.

``DevelopProject`` is a ``unittest.TestCase`` mixin on ``WorktreeProject``: the primary branch's
configured check passes on a transfer that only debits, and the registered candidate is where the
user session asks for the rejection of invalid amounts that the transfer Module's Spec states.
The stage helpers call each capability through ``ScriptedSession`` with scripted Agent answers.
"""

from __future__ import annotations

import subprocess

from concorde.harness import change_worktree
from concorde.harness.change_worktree import git, git_value

from tests.concorde.support.worktree_project import WorktreeProject

from .develop_session import ScriptedSession, stage_result

DEBIT_ONLY = "def transfer(balance, amount):\n    return balance - amount\n"
DEBIT_CHECK = (
    "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path.cwd()))\n"
    "from app.transfer import transfer\nassert transfer(100, 20) == 80\n"
)
GUARDED = (
    "def transfer(balance, amount):\n"
    "    if amount <= 0 or amount > balance:\n"
    '        raise ValueError("invalid transfer")\n'
    "    return balance - amount\n"
)
GUARDED_CHECK = DEBIT_CHECK + (
    "for balance, amount in [(10, 20), (10, 0), (10, -1)]:\n"
    "    try:\n        transfer(balance, amount)\n    except ValueError:\n        pass\n"
    '    else:\n        raise AssertionError("invalid transfer accepted")\n'
)
PLAN = "Reject a non-positive or unaffordable amount before debiting; extend the transfer check."
TASKS = [
    {
        "id": "T1",
        "target_id": "service.transfer",
        "description": "Reject a non-positive or unaffordable amount with ValueError.",
        "acceptance": "The transfer check covers one debit and every rejected amount.",
        "complete": False,
    }
]


def assessment(child):
    return stage_result(
        child, "sufficient", "The transfer contract states every needed promise."
    )


def planning(child):
    return stage_result(child, "completed", "Planned the guarded transfer.", plan=PLAN)


def task_list(child):
    return stage_result(child, "completed", "Authored the transfer task.", tasks=TASKS)


def local_tasks(child) -> list[dict]:
    """The tasks the programmer was admitted to complete."""
    (task,) = [
        value
        for value in child.stage_inputs
        if value["type_id"] == "concorde-implementation-task"
    ]
    return task["data"]["tasks"]


def programmer(root, code=GUARDED, check=GUARDED_CHECK):
    """A programmer that writes ``code`` and ``check`` and reports every task complete."""

    def answer(child):
        (root / "app/transfer.py").write_text(code)
        (root / "checks/transfer_check.py").write_text(check)
        return stage_result(
            child,
            "completed",
            "Implemented the guarded transfer.",
            tasks=[{**task, "complete": True} for task in local_tasks(child)],
        )

    return answer


class DevelopProject(WorktreeProject):
    def setUp(self):
        super().setUp()
        (self.primary / "app/transfer.py").write_text(DEBIT_ONLY)
        (self.primary / "checks/transfer_check.py").write_text(DEBIT_CHECK)
        self.commit(self.primary, "Debit-only transfer")
        git(self.change, "merge", "-q", "--ff-only", "integration")
        # The user session registers its candidate for the agreed change.
        change_worktree.ensure_change(self.change, task=self.task)
        self.session = ScriptedSession(self, self.change)

    # -- observations --------------------------------------------------------------------

    def primary_state(self) -> dict:
        """The primary branch, its index and its files, as Git sees them."""
        return {
            "head": git_value(self.primary, "rev-parse", "integration"),
            "status": git_value(self.primary, "status", "--porcelain"),
            "transfer": (self.primary / "app/transfer.py").read_bytes(),
        }

    def delivered_branches(self) -> list[str]:
        return git_value(
            self.primary, "branch", "--list", "concorde/delivered/*"
        ).split()

    def spec_bytes(self, root) -> dict:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in sorted((root / "specs").rglob("*"))
            if path.is_file()
        }

    def run_check(self, root) -> int:
        return subprocess.run(
            ["python3", "checks/transfer_check.py"],
            cwd=root,
            capture_output=True,
            check=False,
        ).returncode

    # -- the stage capabilities ----------------------------------------------------------

    def context_solve(self, answer=assessment):
        return self.session.call("concorde-context-solve", self.task, answer)

    def plan(self, assessor=assessment, planner=planning):
        return self.session.workflow(
            "concorde-plan",
            self.task,
            lambda key: {"assessor": assessor, "planner": planner}[key],
        )

    def write_tasks(self, answer=task_list):
        return self.session.call("concorde-tasks", self.task, answer)

    def implement(self, answer=None):
        return self.session.call(
            "concorde-implement", self.task, answer or programmer(self.change)
        )

    def validate(self):
        return self.call_operation(self.change, "concorde-validate", self.task)

    def develop(self, answer=None):
        """Context solving, planning, task writing and implementation, each succeeding."""
        for name, step in (
            ("context-solve", self.context_solve),
            ("plan", self.plan),
            ("tasks", self.write_tasks),
            ("implement", lambda: self.implement(answer)),
        ):
            result = step()
            self.assertEqual("succeeded", result["status"], (name, result))
            self.assertEqual(
                "completed", result["output"]["data"]["outcome"], (name, result)
            )
