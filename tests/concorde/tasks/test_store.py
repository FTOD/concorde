"""The Task store and the ``concorde task`` commands on a real Git repository."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde import errors
from concorde.errors import ERROR_SCHEMA, codes
from concorde.execution import binding
from concorde.execution.runs import workspace_lock
from concorde.harness import configure, models
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver, write_run

TASK_CONTRACTS = "specs/concorde/coordination/tasks/contracts.md"


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

    def state(self, task_id="t1"):
        return store.show_task(self.root, task_id)["record"]["state"]

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
        self.assertEqual(
            str(self.root / ".concorde/tasks/severity.decisions.md"),
            value["decision_log"],
        )
        value = value["record"]
        worktree = self.root / ".claude/worktrees/severity"
        self.assertEqual(str(worktree), value["worktree"])
        self.assertEqual(("open", head), (value["state"], value["base_commit"]))
        self.assertEqual([], value["sessions"])
        self.assertNotIn(".claude", git(self.root, "status", "--porcelain"))
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/severity"))
        self.assertEqual("concorde/severity", git(worktree, "branch", "--show-current"))
        self.assertEqual(
            value, json.loads((self.root / ".concorde/tasks/severity.json").read_text())
        )
        self.assertEqual(
            "# Decision log: severity\n\nGoal: let reports carry a severity\n",
            (self.root / ".concorde/tasks/severity.decisions.md").read_text(),
        )
        self.assertNotIn("runs", value)
        self.assertNotIn("deliveries", value)
        self.assertNotIn("workflow", value)

    @verifies("scenario.tasks.open")
    def test_open_binds_the_worktree_as_the_tasks_workspace(self):
        head = git(self.root, "rev-parse", "HEAD")
        record = self.project.open_task("t1", modules=("module.a", "module.b"))
        worktree = self.project.worktree("t1")
        self.assertEqual(
            {
                "schema_version": 1,
                "workspace": "t1",
                "root": str(worktree),
                "branch": "concorde/t1",
                "base_commit": head,
                "goal": "Fix A.",
                "modules": ["module.a", "module.b"],
                "records": str(self.root / ".concorde"),
            },
            binding.load(worktree),
        )
        self.assertEqual(record["worktree"], str(worktree))
        # The binding is the worktree's own state, never a change on the task branch.
        self.assertEqual("", git(worktree, "status", "--porcelain"))
        self.assertIsNone(binding.load(self.root))
        self.assertEqual("open", self.state())

    @verifies("scenario.tasks.open-inherits-worker-models")
    def test_a_new_task_keeps_its_own_worker_models(self):
        primary_config = self.root / models.CONFIG
        primary_config.write_text(
            json.dumps({"schema_version": 3, "default": {"model": "anthropic/a"}})
        )
        worktree = Path(self.project.open_task("t1")["worktree"])
        task_config = worktree / models.CONFIG
        inherited = task_config.read_text()
        self.assertEqual(primary_config.read_text(), inherited)
        self.assertEqual("", git(worktree, "status", "--porcelain"))
        primary_config.write_text(
            json.dumps({"schema_version": 3, "default": {"model": "anthropic/b"}})
        )
        self.assertEqual(inherited, task_config.read_text())
        # AI edits the task's source file directly; validation is read-only and offline.
        task_config.write_text(
            json.dumps({"schema_version": 3, "default": {"model": "anthropic/c"}})
        )
        edited = task_config.read_bytes()
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            status = configure.main(["--check", "--json"], cwd=worktree)
        self.assertEqual(edited, task_config.read_bytes())
        value = json.loads(output.getvalue())
        self.assertEqual((0, "ok"), (status, value["status"]), value)
        self.assertEqual(str(task_config), value["output"]["config"])
        self.assertEqual(
            "anthropic/c", json.loads(task_config.read_text())["default"]["model"]
        )
        self.assertEqual(
            "anthropic/b",
            json.loads(primary_config.read_text())["default"]["model"],
        )
        primary_config.unlink()
        second = Path(self.project.open_task("t2")["worktree"])
        self.assertFalse((second / models.CONFIG).exists())

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

    @verifies("scenario.tasks.open-not-ignored")
    def test_a_worktree_the_primary_would_track_is_refused(self):
        (self.root / ".gitignore").write_text(".concorde/runs/\n")
        status, value = self.command(
            "open", "t1", "--goal", "g", "--modules", "module.a"
        )
        self.assertEqual(1, status)
        self.assertEqual("worktree_not_ignored", value["error"]["code"])
        self.assertIn(".claude/worktrees/t1/", value["error"]["detail"])
        self.assertIn("add .claude/worktrees/ to .gitignore", value["error"]["options"])
        self.assertFalse((self.root / ".concorde/tasks/t1.json").exists())
        self.assertFalse((self.root / ".claude/worktrees/t1").exists())
        self.assertEqual("", git(self.root, "branch", "--list", "concorde/t1"))

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
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("Escalated to the developer", log)
        self.assertIn("Not handled here (decision)", log)
        self.assertIn("src/bmod/secret.py", value["rendered"])
        self.assertEqual(len(self.record()["escalations"]), value["number"])
        self.assert_contract(self.record())

    @verifies("scenario.tasks.escalate-decision")
    def test_a_decision_without_an_error_is_escalated_as_a_link_alone(self):
        self.project.open_task("t1")
        status, value = self.command(
            "escalate",
            "t1",
            "--by",
            "task-session",
            "--code",
            "workflow_decision",
            "--detail",
            "the no-ask survey split module.a in two without the developer",
            "--reason",
            "decision",
            "--explanation",
            "the split changes what module.a promises; the developer decides",
            "--option",
            "keep the split",
            "--recommendation",
            "keep the split",
        )
        self.assertEqual(0, status, value)
        link = value["escalated"]
        validate(link, ERROR_SCHEMA)
        self.assertEqual(
            ("task-session", "workflow_decision", []),
            (link["level"], link["code"], link["causes"]),
        )
        self.assertEqual(
            [{"at": self.record()["escalations"][0]["at"], "error": link}],
            self.record()["escalations"],
        )
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("workflow_decision", log)
        self.assertIn("the no-ask survey split module.a", log)
        self.assert_contract(self.record())

    @verifies("scenario.tasks.escalate")
    def test_only_a_run_of_the_tasks_workspace_is_escalated(self):
        self.project.open_task("t1")
        for run_id, workspace in (
            ("r-20260927T000000-understand-00000001", "t2"),
            ("r-20260927T000000-understand-00000002", None),
        ):
            write_run(self.root, run_id, workspace, status="failed")
            status, value = self.command(
                "escalate",
                "t1",
                "--run",
                run_id,
                "--code",
                "x",
                "--detail",
                "x",
                "--reason",
                "decision",
                "--explanation",
                "x",
            )
            self.assertEqual((1, "unknown_run"), (status, value["error"]["code"]))
            self.assertIn(
                f"a run of {workspace or 'no workspace'}", value["error"]["detail"]
            )
        self.assertEqual([], self.record()["escalations"])

    @verifies("scenario.tasks.session-escalates")
    def test_a_task_session_escalates_to_the_main_agent(self):
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
            "--by",
            "task-session",
            "--run",
            failed["run_id"],
            "--code",
            "outside_task",
            "--detail",
            "the goal needs src/bmod/secret.py, which the task's Modules do not bind",
            "--reason",
            "scope",
            "--explanation",
            "binding module.b goes beyond the task; the main agent decides",
            cwd=worktree,
        )
        self.assertEqual(0, status, value)
        session_link = value["escalated"]
        validate(session_link, ERROR_SCHEMA)
        self.assertEqual(
            ("task-session", "task session (task t1)"),
            (session_link["level"], session_link["actor"]),
        )
        self.assertEqual(failed["error"], session_link["causes"][0])
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("Escalated to the main agent", log)
        status, value = self.command(
            "escalate",
            "t1",
            "--escalation",
            "1",
            "--code",
            "scope_decision",
            "--detail",
            "binding module.b widens what the task may change",
            "--reason",
            "decision",
            "--explanation",
            "changing a task's Modules is the developer's call here",
        )
        self.assertEqual(0, status, value)
        self.assertEqual("main-agent", value["escalated"]["level"])
        self.assertEqual([session_link], value["escalated"]["causes"])
        self.assertIn("Escalated to the developer", self.project_log())
        status, value = self.command(
            "escalate",
            "t1",
            "--escalation",
            "9",
            "--code",
            "x",
            "--detail",
            "x",
            "--reason",
            "decision",
            "--explanation",
            "x",
        )
        self.assertEqual((1, "unknown_escalation"), (status, value["error"]["code"]))

    def project_log(self):
        return (self.root / ".concorde/tasks/t1.decisions.md").read_text()

    @verifies("scenario.tasks.open-unknown-module")
    def test_an_unknown_module_is_refused(self):
        self.assertEqual(
            (1, "unknown_module"),
            self.refusal("open", "t1", "--goal", "g", "--modules", "module.billing"),
        )
        self.assertEqual("", git(self.root, "branch", "--list", "concorde/t1"))
        self.assertFalse((self.root / ".claude/worktrees/t1").exists())

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
            (1, "not_primary"),
            self.refusal("close", "t1", "--completed", "--note", "x", cwd=worktree),
        )
        self.assertEqual((1, "not_primary"), self.refusal("merge", "t1", cwd=worktree))
        self.assertEqual(
            (1, "not_primary"),
            self.refusal("session", "t1", "--main", "m", "--dry-run", cwd=worktree),
        )
        self.assertEqual(before, self.record())

    @verifies("scenario.tasks.list-show")
    def test_list_and_show(self):
        self.project.open_task("t1")
        self.project.open_task("t2")
        status, value = self.project.run("task-validation", "--task", "t2")
        self.assertEqual("t2", value["workspace"], value)
        status, active = self.command("list", "--state", "active")
        self.assertEqual((0, ["t2"]), (status, [item["id"] for item in active]))
        _, everything = self.command("list")
        self.assertEqual(["t1", "t2"], [item["id"] for item in everything])
        self.assertEqual(["open", "active"], [item["state"] for item in everything])
        # The stored state stays open: active is derived from the run store.
        self.assertEqual("open", self.record("t2")["state"])
        _, shown = self.command("show", "t1")
        self.assertEqual("t1", shown["record"]["id"])
        self.assertEqual(
            ([], [], None), (shown["runs"], shown["deliveries"], shown["busy"])
        )
        self.assertEqual(
            str(self.root / ".concorde/tasks/t1.decisions.md"), shown["decision_log"]
        )
        _, shown = self.command("show", "t2")
        self.assertEqual(
            [(value["run_id"], "command", "task-validation", value["status"])],
            [
                (run["run_id"], run["kind"], run["name"], run["status"])
                for run in shown["runs"]
            ],
        )
        self.assertEqual(2, cli.main(["frobnicate"], cwd=self.root))

    @verifies("scenario.tasks.first-run")
    def test_the_first_run_activates_a_task(self):
        self.project.open_task("t1")
        self.assertEqual("open", self.state())
        # A run of another workspace or an unbound run leaves the task open.
        write_run(self.root, "r-20260927T000000-understand-00000001", "t2")
        write_run(self.root, "r-20260927T000000-understand-00000002", None)
        self.assertEqual("open", self.state())
        write_run(
            self.root,
            "r-20260927T000001-implement-00000003",
            "t1",
            name="implement",
            status=None,
            host_pid=os.getpid(),
        )
        shown = store.show_task(self.root, "t1")
        self.assertEqual("active", shown["record"]["state"])
        self.assertEqual(
            [("r-20260927T000001-implement-00000003", "running")],
            [(run["run_id"], run["status"]) for run in shown["runs"]],
        )
        self.assertEqual("open", self.record()["state"])

    @verifies("scenario.tasks.first-run")
    def test_a_commit_or_a_change_activates_a_task(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("changed = True\n")
        self.assertEqual("active", self.state())
        commit(worktree, "a verified step")
        self.assertEqual("active", self.state())

    @verifies("scenario.tasks.modules-fixed")
    def test_a_run_records_extra_modules(self):
        # A run may work on more Modules than the task names; the run store keeps them with the
        # run, and the task record, which nothing below the task level writes, keeps its own.
        self.project.open_task("t1")
        _, value = self.project.run(
            "task-validation", "--task", "t1", "--modules", "module.a,module.b"
        )
        self.assertEqual(["module.a", "module.b"], value["modules"], value)
        shown = store.show_task(self.root, "t1")
        self.assertEqual(["module.a", "module.b"], shown["runs"][0]["modules"])
        self.assertEqual(["module.a"], shown["record"]["modules"])

    @verifies("scenario.tasks.busy")
    def test_a_second_concurrent_run_is_refused(self):
        self.project.open_task("t1")
        records = self.root / ".concorde"
        with workspace_lock(records, "t1", "implement run r-held"):
            self.assertIn(
                "implement run r-held", store.show_task(self.root, "t1")["busy"]
            )
            status, value = self.project.run("task-validation", "--task", "t1")
        self.assertEqual(
            (1, "failed", "refused"),
            (status, value["status"], value["error"]["code"]),
        )
        self.assertEqual(["refused", "workspace_busy"], codes(value["error"]))
        self.assertIn("implement run r-held", value["error"]["detail"])
        self.assertEqual("decision", value["error"]["unhandled"]["reason"])
        self.assertIsNone(store.show_task(self.root, "t1")["busy"])
        status, value = self.project.run("task-validation", "--task", "t1")
        self.assertNotEqual("refused", (value["error"] or {}).get("code"), value)

    @verifies("scenario.tasks.interrupted")
    def test_a_dead_host_leaves_an_interrupted_run(self):
        self.project.open_task("t1")
        dead = subprocess.Popen(["true"])
        dead.wait()
        write_run(
            self.root,
            "r-20260927T000000-implement-00000001",
            "t1",
            name="implement",
            status=None,
            host_pid=dead.pid,
        )
        shown = store.show_task(self.root, "t1")
        self.assertEqual(["lost"], [run["status"] for run in shown["runs"]])
        self.assertIsNone(shown["busy"])
        self.assertEqual("active", shown["record"]["state"])

    @verifies("scenario.tasks.concurrent-update")
    def test_a_concurrent_change_is_detected(self):
        self.project.open_task("t1")
        path = self.root / ".concorde/tasks/t1.json"
        real = store._locked
        calls = {"n": 0}

        def escalated(record):
            record["escalations"].append({"at": store.now(), "error": {}})
            return record

        @contextlib.contextmanager
        def meddling(primary):
            calls["n"] += 1
            value = json.loads(path.read_text())
            value["goal"] = f"changed by another process {calls['n']}"
            path.write_text(json.dumps(value))
            with real(primary):
                yield

        with (
            patch.object(store, "_locked", meddling),
            self.assertRaises(store.TaskError) as raised,
        ):
            store.update(self.root, "t1", escalated)
        self.assertEqual("record_conflict", raised.exception.code)
        self.assertEqual(3, calls["n"])
        self.assertEqual("changed by another process 3", self.record()["goal"])
        self.assertEqual([], self.record()["escalations"])
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
            record = store.update(self.root, "t1", escalated)
        self.assertEqual("changed once", record["goal"])
        self.assertEqual(1, len(record["escalations"]))

    def deliver(self, task_id="t1"):
        return deliver(self.project.worktree(task_id))

    @verifies("scenario.tasks.delivered-reopened")
    def test_a_writing_run_reopens_a_delivered_task(self):
        self.project.open_task("t1")
        head = self.deliver()
        shown = store.show_task(self.root, "t1")
        self.assertEqual("delivered", shown["record"]["state"])
        self.assertEqual([head], [item["commit"] for item in shown["deliveries"]])
        self.assertEqual(
            ".concorde/evidence/t1/1.json", shown["deliveries"][0]["bundle"]
        )
        self.assertEqual([], shown["deliveries"][0]["mismatches"])
        # A run that changes nothing leaves the task delivered.
        write_run(self.root, "r-20260927T000000-test-00000001", "t1", name="test")
        self.assertEqual("delivered", self.state())
        # A change after the delivery commit makes it active again, committed or not.
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("changed = True\n")
        self.assertEqual("active", self.state())
        commit(worktree, "after the delivery")
        self.assertEqual("active", self.state())
        second = self.deliver()
        self.assertEqual("delivered", self.state())
        self.assertEqual(
            [".concorde/evidence/t1/1.json", ".concorde/evidence/t1/2.json"],
            [item["bundle"] for item in store.show_task(self.root, "t1")["deliveries"]],
        )
        self.assertEqual(second, git(self.root, "rev-parse", "concorde/t1"))

    @verifies("scenario.tasks.sandbox-masks")
    def test_a_path_a_sandbox_masks_is_no_change(self):
        bwrap = shutil.which("bwrap")
        sandbox = [bwrap, "--dev-bind", "/", "/"] if bwrap else []
        if not bwrap or subprocess.run([*sandbox, "true"], check=False).returncode != 0:
            self.skipTest("bubblewrap cannot create a sandbox here")
        self.project.open_task("t1")
        self.deliver()
        worktree = self.project.worktree("t1")
        concorde = [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py")]

        # Every call masks the same paths: bwrap leaves each mount point behind as an empty
        # file, which a call that did not mask it would see as a real new file.
        binds = [
            item
            for path in (".bashrc", ".mcp.json")
            for item in ("--bind", "/dev/null", str(worktree / path))
        ]

        def shown() -> dict:
            done = subprocess.run(
                [*sandbox, *binds, *concorde, "task", "show", "t1"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)
            return json.loads(done.stdout)

        # Git lists the masked paths as untracked, but they are no content of the task.
        self.assertEqual("delivered", shown()["record"]["state"])
        # A real new file beside the masked paths still makes the task active.
        (worktree / "notes.txt").write_text("a real change\n")
        self.assertEqual("active", shown()["record"]["state"])

    @verifies("scenario.tasks.delivery-unverified")
    def test_a_delivery_commit_that_does_not_verify_is_not_delivered(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        # Only the subject and trailers of a delivery commit, and no bundle.
        head = deliver(worktree, bundle_run=None)
        shown = store.show_task(self.root, "t1")
        self.assertEqual("active", shown["record"]["state"])
        self.assertEqual([head], [item["commit"] for item in shown["deliveries"]])
        (mismatch,) = shown["deliveries"][0]["mismatches"]
        self.assertIn(".concorde/evidence/t1/1.json", mismatch)
        self.assertIn("not in the commit", mismatch)
        self.assertEqual(
            ["active"], [item["state"] for item in store.list_tasks(self.root)]
        )
        git(self.root, "merge", "--ff-only", "concorde/t1")
        before = self.record()
        status, value = self.command("close", "t1", "--merged")
        self.assertEqual(1, status, value)
        error = value["error"]
        self.assertEqual(
            ("delivery_unverified", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn(head, error["detail"])
        self.assertIn(mismatch, error["detail"])
        self.assertEqual(before, self.record())
        self.assertTrue(worktree.exists())
        # A bundle whose readiness run is not the trailer's does not verify either.
        second = deliver(worktree, text="second = True\n", bundle_run="r-other")
        shown = store.show_task(self.root, "t1")
        self.assertEqual("active", shown["record"]["state"])
        self.assertEqual(second, shown["deliveries"][1]["commit"])
        (mismatch,) = shown["deliveries"][1]["mismatches"]
        self.assertIn("readiness run r-other", mismatch)
        # The next delivery that verifies delivers the task.
        deliver(worktree, text="third = True\n")
        shown = store.show_task(self.root, "t1")
        self.assertEqual("delivered", shown["record"]["state"])
        self.assertEqual([], shown["deliveries"][2]["mismatches"])

    @verifies("scenario.tasks.close-merged")
    def test_close_a_merged_task(self):
        self.project.open_task("t1")
        head = self.deliver()
        worktree = self.project.worktree("t1")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        status, value = self.command("close", "t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "merged"), (value["state"], value["closed"]["outcome"])
        )
        self.assertEqual(head, value["closed"]["primary_commit"])
        self.assertTrue(value["closed"]["worktree_removed"])
        self.assertFalse(worktree.exists())
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/t1"))
        self.assertTrue((self.root / ".concorde/tasks/t1.decisions.md").exists())

    @verifies("scenario.tasks.close-submodules")
    def test_close_removes_a_worktree_with_checked_out_submodules(self):
        library = self.root.parent / "library"
        library.mkdir()
        git(library, "init", "-q")
        (library / "README.md").write_text("library\n")
        git(library, "add", "-A")
        git(
            library, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lib"
        )
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        git(
            worktree,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(library),
            "vendor/lib",
        )
        head = self.deliver()
        self.assertTrue((worktree / "vendor/lib/README.md").is_file())
        (worktree / "vendor/lib/README.md").write_text("changed inside the submodule\n")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        self.assertEqual((1, "dirty_worktree"), self.refusal("close", "t1", "--merged"))
        self.assertTrue(worktree.exists())
        git(worktree / "vendor/lib", "checkout", "--", "README.md")
        status, value = self.command("close", "t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(head, value["closed"]["primary_commit"])
        self.assertTrue(value["closed"]["worktree_removed"])
        self.assertFalse(worktree.exists())

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

    @verifies("scenario.tasks.close-completed")
    def test_close_a_task_that_reached_its_goal_without_merging(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        self.assertEqual(
            (1, "invalid_input"), self.refusal("close", "t1", "--completed")
        )
        (worktree / "src/a/calc.py").write_text("dirty = True\n")
        self.assertEqual(
            (1, "dirty_worktree"),
            self.refusal("close", "t1", "--completed", "--note", "tried it"),
        )
        self.assertTrue(worktree.exists())
        status, value = self.command(
            "close", "t1", "--completed", "--note", "the probe answered", "--force"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "completed", "the probe answered", []),
            (
                value["state"],
                value["closed"]["outcome"],
                value["closed"]["note"],
                value["closed"]["errors"],
            ),
        )
        self.assertFalse(worktree.exists())
        self.assertTrue(git(self.root, "branch", "--list", "concorde/t1"))
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("## Closed: completed", log)
        self.assertIn("the probe answered", log)
        self.assert_contract(self.record())

    def assert_contract(self, record):
        text = (REPOSITORY_ROOT / TASK_CONTRACTS).read_text()
        contract = json.loads(
            text.split("```concorde-contract\n", 1)[1].split("```")[0]
        )
        validate(record, contract["schema"])

    @verifies("scenario.tasks.close-failed")
    def test_a_failed_task_keeps_its_reason_and_error_chains(self):
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
        reason = ["--reason", "the change needs module.b, which is out of scope"]
        self.assertEqual(
            (1, "invalid_input"), self.refusal("close", "t1", "--failed", *reason)
        )
        self.assertEqual(
            (1, "invalid_input"),
            self.refusal(
                "close", "t1", "--failed", *reason, "--no-error", "--run", "r-x"
            ),
        )
        self.assertEqual(
            (1, "invalid_input"),
            self.refusal("close", "t1", "--failed", "--run", failed["run_id"]),
        )
        status, value = self.command(
            "close", "t1", "--failed", *reason, "--run", failed["run_id"], "--force"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("failed", "failed", reason[1]),
            (value["state"], value["closed"]["outcome"], value["closed"]["note"]),
        )
        self.assertEqual([failed["error"]], value["closed"]["errors"])
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("## Closed: failed", log)
        self.assertIn(failed["error"]["code"], log)
        self.project.open_task("t2")
        status, value = self.command(
            "close",
            "t2",
            "--failed",
            "--reason",
            "the direction was wrong",
            "--no-error",
        )
        self.assertEqual(0, status, value)
        self.assertEqual([], value["closed"]["errors"])
        self.assert_contract(self.record())

    @verifies("scenario.tasks.closed-inert")
    def test_a_closed_task_accepts_no_run(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        self.command("close", "t1", "--completed", "--note", "done")
        # Closing removes the worktree and with it the workspace binding, so no run of the
        # task's workspace can start; a run recorded anyway leaves the task closed.
        self.assertFalse(binding.path_of(worktree).exists())
        write_run(self.root, "r-20260927T000000-test-00000001", "t1", name="test")
        self.assertEqual("closed", self.state())
        _, closed = self.command("list", "--state", "closed")
        self.assertEqual(["t1"], [item["id"] for item in closed])
        with self.assertRaises(store.TaskError) as raised:
            store.record_session(self.root, "t1", {"program": "claude"})
        self.assertEqual("task_closed", raised.exception.code)

    @verifies("scenario.tasks.round-closed")
    def test_no_round_begins_in_a_task_closed_meanwhile(self):
        self.project.open_task("t1")
        store.record_session(
            self.root, "t1", {"program": "pi", "id": "s1", "rounds": []}
        )
        running = {"round": 1, "status": "running", "supervisor_pid": 1}
        store.begin_round(self.root, "t1", "s1", dict(running))
        # A round running when the task closes still records its outcome.
        self.command("close", "t1", "--completed", "--note", "done")
        record = store.finish_round(self.root, "t1", "s1", 1, {"status": "stopped"})
        self.assertEqual("stopped", record["sessions"][0]["rounds"][0]["status"])
        with self.assertRaises(store.TaskError) as raised:
            store.begin_round(self.root, "t1", "s1", dict(running, round=2))
        self.assertEqual("task_closed", raised.exception.code)
        # A close stored between the round's first check and its write refuses it on retry.
        self.project.open_task("t2")
        store.record_session(
            self.root, "t2", {"program": "pi", "id": "s1", "rounds": []}
        )
        path = self.root / ".concorde/tasks/t2.json"
        real_locked, real_session = store._locked, store._pi_session
        checked = {"n": 0}

        @contextlib.contextmanager
        def closing(primary):
            value = json.loads(path.read_text())
            if value["state"] == "open":
                value["state"] = "closed"
                path.write_text(json.dumps(value))
            with real_locked(primary):
                yield

        def counted(record, session_id):
            checked["n"] += 1
            return real_session(record, session_id)

        with (
            patch.object(store, "_locked", closing),
            patch.object(store, "_pi_session", counted),
            self.assertRaises(store.TaskError) as raised,
        ):
            store.begin_round(self.root, "t2", "s1", dict(running))
        self.assertEqual("task_closed", raised.exception.code)
        self.assertEqual(1, checked["n"])
        self.assertEqual([], self.record("t2")["sessions"][0]["rounds"])

    def read_only_log(self, task_id="t1"):
        log = self.root / f".concorde/tasks/{task_id}.decisions.md"
        log.chmod(0o444)
        self.addCleanup(log.chmod, 0o644)
        return log

    @verifies("scenario.tasks.close-rerun")
    def test_running_a_close_again_finishes_it(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        real_git = store._git

        def refusing_removal(root, *arguments, check=True):
            if arguments[:2] == ("worktree", "remove"):
                return subprocess.CompletedProcess(arguments, 128, "", "fatal: locked")
            return real_git(root, *arguments, check=check)

        with patch.object(store, "_git", refusing_removal):
            status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual((1, "worktree_failed"), (status, value["error"]["code"]))
        self.assertIn("record of task t1 is unchanged", value["error"]["detail"])
        self.assertIn("finishes the close", value["error"]["detail"])
        self.assertTrue(worktree.exists())
        real = store.update

        def conflicting(primary, task_id, change):
            raise store.TaskError(
                "record_conflict", f"task {task_id} changed concurrently"
            )

        with patch.object(store, "update", conflicting):
            status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(1, status, value)
        error = value["error"]
        self.assertEqual("record_conflict", error["code"])
        self.assertIn(f"already removed the worktree {worktree}", error["detail"])
        self.assertIn("stays open", error["detail"])
        self.assertIn(
            "`concorde task close t1 --completed` with the same", error["detail"]
        )
        self.assertFalse(worktree.exists())
        self.assertEqual("open", self.record()["state"])
        self.assertIs(real, store.update)
        status, value = self.command("close", "t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", False), (value["state"], value["closed"]["worktree_removed"])
        )
        self.assertIn("## Closed: completed", self.log())
        # The record is written but the decision log refuses the closing.
        self.project.open_task("t2")
        log = self.read_only_log("t2")
        status, value = self.command(
            "close", "t2", "--failed", "--reason", "no", "--no-error"
        )
        self.assertEqual(1, status, value)
        validate(value["error"], ERROR_SCHEMA)
        self.assertEqual(
            ("decision_log_failed", "environment"),
            (value["error"]["code"], value["error"]["unhandled"]["reason"]),
        )
        self.assertIn("is failed in its record", value["error"]["detail"])
        self.assertIn("`concorde task close t2 --failed`", value["error"]["detail"])
        stored = self.record("t2")
        self.assertEqual("failed", stored["state"])
        self.assertEqual(
            (1, "invalid_transition"),
            self.refusal("close", "t2", "--completed", "--note", "other"),
        )
        log.chmod(0o644)
        status, value = self.command(
            "close", "t2", "--failed", "--reason", "no", "--no-error"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(stored, self.record("t2"))
        heading = f"## Closed: failed, {stored['closed']['at']}"
        self.assertEqual(1, self.log("t2").splitlines().count(heading))
        self.assertIn("\nno\n", self.log("t2"))
        self.assertEqual(
            (1, "invalid_transition"),
            self.refusal("close", "t2", "--failed", "--reason", "no", "--no-error"),
        )
        self.assert_contract(self.record("t2"))

    def log(self, task_id="t1"):
        return (self.root / f".concorde/tasks/{task_id}.decisions.md").read_text()

    @verifies("scenario.tasks.escalate-log-failed")
    def test_an_escalation_the_log_refused_is_recorded_once(self):
        self.project.open_task("t1")
        cause = self.root.parent / "cause.json"
        cause.write_text(
            json.dumps(
                errors.link(
                    "operation",
                    "implement",
                    "check_failed",
                    "the tests of module.a failed",
                    reason="decision",
                    explanation="the fix is outside the goal",
                )
            )
        )
        self.read_only_log()
        before = self.log()
        status, value = self.command(
            "escalate",
            "t1",
            "--error-file",
            str(cause),
            "--code",
            "scope_decision",
            "--detail",
            "the fix needs module.b",
            "--reason",
            "decision",
            "--explanation",
            "binding module.b is the developer's decision",
        )
        self.assertEqual(1, status, value)
        validate(value["error"], ERROR_SCHEMA)
        detail = value["error"]["detail"]
        self.assertEqual("decision_log_failed", value["error"]["code"])
        self.assertIn("as escalation 1", detail)
        self.assertIn("would record it twice", detail)
        self.assertIn("the tests of module.a failed", detail)
        self.assertEqual(1, len(self.record()["escalations"]))
        self.assertEqual(before, self.log())
        self.assert_contract(self.record())


if __name__ == "__main__":
    unittest.main()
