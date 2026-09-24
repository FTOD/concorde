"""The Task store and the ``concorde task`` commands on a real Git repository."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from concorde.errors import ERROR_SCHEMA, codes
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT


def git(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root

    def command(self, *argv, cwd=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=cwd or self.root)
        return status, json.loads(output.getvalue()) if output.getvalue() else None

    def record(self, task_id="t1"):
        return store.load_task(self.root, task_id)

    @verifies("scenario.tasks.open")
    def test_open_a_task(self):
        head = git(self.root, "rev-parse", "HEAD")
        status, value = self.command(
            "open",
            "severity",
            "--goal",
            "let reports carry a severity",
            "--modules",
            "module.a",
        )
        self.assertEqual(0, status, value)
        worktree = self.root.parent / f"{self.root.name}.tasks" / "severity"
        self.assertEqual(str(worktree), value["worktree"])
        self.assertEqual(("open", head), (value["state"], value["base_commit"]))
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/severity"))
        self.assertEqual("concorde/severity", git(worktree, "branch", "--show-current"))
        self.assertEqual(
            value, json.loads((self.root / ".concorde/tasks/severity.json").read_text())
        )
        self.assertEqual(
            "# Decision log: severity\n\nGoal: let reports carry a severity\n",
            (self.root / ".concorde/tasks/severity.decisions.md").read_text(),
        )

    @verifies("scenario.tasks.open-taken")
    def test_a_taken_identity_is_refused(self):
        self.project.open_task("t1")
        before = self.record()
        self.assertEqual(
            (1, "task_exists"),
            self.refusal("open", "t1", "--goal", "g", "--modules", "module.a"),
        )
        git(self.root, "branch", "concorde/t2")
        self.assertEqual(
            (1, "branch_exists"),
            self.refusal("open", "t2", "--goal", "g", "--modules", "module.a"),
        )
        taken = self.root.parent / "taken"
        taken.mkdir()
        self.assertEqual(
            (1, "path_exists"),
            self.refusal(
                "open",
                "t3",
                "--goal",
                "g",
                "--modules",
                "module.a",
                "--path",
                str(taken),
            ),
        )
        self.assertEqual(before, self.record())
        self.assertFalse((self.root / ".concorde/tasks/t3.json").exists())
        self.assertEqual("", git(self.root, "branch", "--list", "concorde/t3"))

    def refusal(self, *argv, cwd=None):
        status, value = self.command(*argv, cwd=cwd)
        validate(value["error"], ERROR_SCHEMA)
        self.assertEqual("component", value["error"]["level"])
        return status, value["error"]["code"]

    @verifies("scenario.tasks.escalate")
    def test_the_main_agent_adds_its_link_when_it_escalates(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        _, failed = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(
                [{"writes": {f"{worktree}/src/bmod/secret.py": "SECRET = 2\n"}}]
            ),
        )
        status, value = self.command(
            "escalate",
            "t1",
            "--run",
            failed["run_id"],
            "--code",
            "grant_decision",
            "--detail",
            "the change needs src/bmod/secret.py, which module.a does not bind",
            "--reason",
            "decision",
            "--explanation",
            "binding module.b changes what the task may touch; the developer decides",
            "--option",
            "bind module.b",
        )
        self.assertEqual(0, status, value)
        link = value["escalated"]
        validate(link, ERROR_SCHEMA)
        self.assertEqual(
            ("main-agent", "grant_decision"), (link["level"], link["code"])
        )
        self.assertEqual(
            ["grant_decision", "audit_violation", "audit_violation"], codes(link)[:3]
        )
        self.assertEqual(link, self.record()["escalations"][-1]["error"])
        text = (REPOSITORY_ROOT / "specs/concorde/tasks/contracts.md").read_text()
        contract = json.loads(
            text.split("```concorde-contract\n", 1)[1].split("```")[0]
        )
        validate(self.record(), contract["schema"])
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("Escalated to the developer", log)
        self.assertIn("Not handled here (decision)", log)
        self.assertIn("src/bmod/secret.py", value["rendered"])
        status, value = self.command(
            "escalate",
            "t1",
            "--code",
            "x",
            "--detail",
            "x",
            "--reason",
            "decision",
            "--explanation",
            "x",
        )
        self.assertEqual((1, "nothing_to_escalate"), (status, value["error"]["code"]))

    @verifies("scenario.tasks.open-unknown-module")
    def test_an_unknown_module_is_refused(self):
        self.assertEqual(
            (1, "unknown_module"),
            self.refusal("open", "t1", "--goal", "g", "--modules", "module.billing"),
        )
        self.assertEqual("", git(self.root, "branch", "--list", "concorde/t1"))
        self.assertFalse((self.root.parent / f"{self.root.name}.tasks/t1").exists())

    @verifies("scenario.tasks.not-primary")
    def test_linked_worktrees_cannot_open_or_close(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        before = self.record()
        self.assertEqual(
            (1, "not_primary"),
            self.refusal(
                "open", "t2", "--goal", "g", "--modules", "module.a", cwd=worktree
            ),
        )
        self.assertEqual(
            (1, "not_primary"), self.refusal("close", "t1", "--abandoned", cwd=worktree)
        )
        self.assertEqual(before, self.record())

    @verifies("scenario.tasks.list-show")
    def test_list_and_show(self):
        self.project.open_task("t1")
        self.project.open_task("t2")
        store.begin_run(
            self.root, "t2", "r-1", "understand", ["module.a"], False, os.getpid()
        )
        status, active = self.command("list", "--state", "active")
        self.assertEqual((0, ["t2"]), (status, [item["id"] for item in active]))
        _, everything = self.command("list")
        self.assertEqual(["t1", "t2"], [item["id"] for item in everything])
        _, shown = self.command("show", "t1")
        self.assertEqual("t1", shown["record"]["id"])
        self.assertEqual(
            str(self.root / ".concorde/tasks/t1.decisions.md"), shown["decision_log"]
        )
        self.assertEqual(2, cli.main(["frobnicate"], cwd=self.root))

    @verifies("scenario.tasks.first-run")
    def test_the_first_run_activates_a_task(self):
        self.project.open_task("t1")
        record = store.begin_run(
            self.root, "t1", "r-1", "implement", ["module.a"], True, os.getpid()
        )
        self.assertEqual("active", record["state"])
        self.assertEqual(
            ("r-1", "running", os.getpid()),
            (
                record["runs"][0]["run_id"],
                record["runs"][0]["status"],
                record["runs"][0]["host_pid"],
            ),
        )

    @verifies("scenario.tasks.run-adds-modules")
    def test_a_run_records_extra_modules(self):
        self.project.open_task("t1")
        record = store.begin_run(
            self.root,
            "t1",
            "r-1",
            "understand",
            ["module.a", "module.b"],
            False,
            os.getpid(),
        )
        self.assertEqual(["module.a", "module.b"], record["modules"])

    @verifies("scenario.tasks.busy")
    def test_a_second_concurrent_run_is_refused(self):
        self.project.open_task("t1")
        store.begin_run(
            self.root, "t1", "r-1", "implement", ["module.a"], True, os.getpid()
        )
        before = self.record()
        with self.assertRaises(store.TaskError) as raised:
            store.begin_run(
                self.root, "t1", "r-2", "test", ["module.a"], False, os.getpid()
            )
        self.assertEqual("task_busy", raised.exception.code)
        self.assertEqual(before, self.record())

    @verifies("scenario.tasks.interrupted")
    def test_a_dead_host_leaves_an_interrupted_run(self):
        self.project.open_task("t1")
        dead = subprocess.Popen(["true"])
        dead.wait()
        store.begin_run(
            self.root, "t1", "r-1", "implement", ["module.a"], True, dead.pid
        )
        record = store.begin_run(
            self.root, "t1", "r-2", "test", ["module.a"], False, os.getpid()
        )
        self.assertEqual(
            ["interrupted", "running"], [run["status"] for run in record["runs"]]
        )

    @verifies("scenario.tasks.concurrent-update")
    def test_a_concurrent_change_is_detected(self):
        self.project.open_task("t1")
        path = self.root / ".concorde/tasks/t1.json"
        real = store._locked
        calls = {"n": 0}

        @contextlib.contextmanager
        def meddling(primary):
            calls["n"] += 1
            value = json.loads(path.read_text())
            value["goal"] = f"changed by another process {calls['n']}"
            path.write_text(json.dumps(value))
            with real(primary):
                yield

        with patch.object(store, "_locked", meddling):
            with self.assertRaises(store.TaskError) as raised:
                store.begin_run(
                    self.root, "t1", "r-1", "test", ["module.a"], False, os.getpid()
                )
        self.assertEqual("record_conflict", raised.exception.code)
        self.assertEqual(3, calls["n"])
        self.assertEqual("changed by another process 3", self.record()["goal"])
        calls["n"] = 0
        once = {"done": False}

        @contextlib.contextmanager
        def once_meddling(primary):
            if not once["done"]:
                once["done"] = True
                value = json.loads(path.read_text())
                value["goal"] = "changed once"
                path.write_text(json.dumps(value))
            with real(primary):
                yield

        with patch.object(store, "_locked", once_meddling):
            record = store.begin_run(
                self.root, "t1", "r-1", "test", ["module.a"], False, os.getpid()
            )
        self.assertEqual("changed once", record["goal"])
        self.assertEqual("running", record["runs"][0]["status"])

    def deliver(self, task_id="t1"):
        worktree = self.project.worktree(task_id)
        (worktree / "src/a/calc.py").write_text("def add(a, b):\n    return a + b\n")
        head = commit(worktree, "deliver")
        store.begin_run(
            self.root, task_id, "r-d", "delivery", ["module.a"], False, os.getpid()
        )
        store.record_delivery(
            self.root, task_id, "r-d", head, ".concorde/evidence/t1/1.json", "r-v"
        )
        store.finish_run(self.root, task_id, "r-d", "ok")
        return head

    @verifies("scenario.tasks.delivered-reopened")
    def test_a_writing_run_reopens_a_delivered_task(self):
        self.project.open_task("t1")
        self.deliver()
        self.assertEqual("delivered", self.record()["state"])
        record = store.begin_run(
            self.root, "t1", "r-2", "test", ["module.a"], False, os.getpid()
        )
        self.assertEqual("delivered", record["state"])
        store.finish_run(self.root, "t1", "r-2", "ok")
        record = store.begin_run(
            self.root, "t1", "r-3", "implement", ["module.a"], True, os.getpid()
        )
        self.assertEqual("active", record["state"])

    @verifies("scenario.tasks.close-merged")
    def test_close_a_merged_task(self):
        self.project.open_task("t1")
        head = self.deliver()
        worktree = self.project.worktree("t1")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        status, value = self.command("close", "t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual("merged", value["state"])
        self.assertEqual(head, value["closed"]["primary_commit"])
        self.assertTrue(value["closed"]["worktree_removed"])
        self.assertFalse(worktree.exists())
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/t1"))
        self.assertTrue((self.root / ".concorde/tasks/t1.decisions.md").exists())

    @verifies("scenario.tasks.close-not-merged")
    def test_an_unmerged_task_cannot_close_as_merged(self):
        self.project.open_task("t1")
        self.assertEqual((1, "not_merged"), self.refusal("close", "t1", "--merged"))
        self.deliver()
        self.assertEqual((1, "not_merged"), self.refusal("close", "t1", "--merged"))
        worktree = self.project.worktree("t1")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        (worktree / "src/a/calc.py").write_text("moved = True\n")
        commit(worktree, "moved on")
        before = self.record()
        self.assertEqual((1, "not_merged"), self.refusal("close", "t1", "--merged"))
        self.assertEqual(before, self.record())
        self.assertTrue(worktree.exists())

    @verifies("scenario.tasks.abandon")
    def test_abandon_a_task(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("dirty = True\n")
        self.assertEqual(
            (1, "dirty_worktree"), self.refusal("close", "t1", "--abandoned")
        )
        self.assertTrue(worktree.exists())
        status, value = self.command("close", "t1", "--abandoned", "--force")
        self.assertEqual((0, "abandoned"), (status, value["state"]))
        self.assertFalse(worktree.exists())
        self.assertTrue(git(self.root, "branch", "--list", "concorde/t1"))

    @verifies("scenario.tasks.closed-inert")
    def test_a_closed_task_accepts_no_run(self):
        self.project.open_task("t1")
        self.command("close", "t1", "--abandoned", "--force")
        with self.assertRaises(store.TaskError) as raised:
            store.begin_run(
                self.root, "t1", "r-1", "test", ["module.a"], False, os.getpid()
            )
        self.assertEqual("task_closed", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
