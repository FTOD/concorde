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
from concorde.harness import models
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from concorde.tracing import layout, locks
from concorde.tracing import node as trace
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver, write_run

TASK_CONTRACTS = "specs/concorde/coordination/tasks/contracts.md"


# A fake runner of a run of a task's workspace: it holds the workspace lock and the run lock, as
# a live runner does, and on SIGTERM writes its own result before it releases them.
RUNNER = """
import json, signal, sys, time
from pathlib import Path
from concorde.tracing import layout, locks
concorde, task, run_id, folder = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
stopped = []
signal.signal(signal.SIGTERM, lambda *_: stopped.append(True))
with locks.hold(layout.lock_file(concorde, "workspace", task), f"implement run {run_id}"):
    with locks.hold(layout.lock_file(concorde, "run", run_id), "runner", remove=True):
        print("ready", flush=True)
        while not stopped:
            time.sleep(0.02)
        progress = json.loads((folder / "status.json").read_text())
        result = {
            key: progress[key] for key in ("kind", "name", "workspace", "modules", "run_id")
        }
        result.update(
            status="failed",
            summary="stopped by SIGTERM",
            output=None,
            worker=None,
            worker_runs=[],
            host_evidence=[],
            error=None,
            started_at=progress["started_at"],
            finished_at=progress["started_at"],
        )
        (folder / "result.json").write_text(json.dumps(result))
"""


def snapshot(folder: Path) -> dict:
    """Every file below ``folder`` with its bytes."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


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

    def close(self, *argv, cwd=None):
        """``task close`` with ``argv``; an accepted close's record, which warns of nothing."""
        status, value = self.command("close", *argv, cwd=cwd)
        if status == 0:
            self.assertEqual([], value["warnings"])
            value = value["record"]
        return status, value

    def record(self, task_id="t1"):
        """The stored record of the task, current or in the history."""
        return store.load_any(self.root, task_id)[0]

    def state(self, task_id="t1"):
        return store.show_task(self.root, task_id)["record"]["state"]

    def folder(self, task_id="t1"):
        return self.root / ".concorde/tasks" / task_id

    def history(self, key="t1"):
        return self.root / ".concorde/history" / key

    def escalations(self, task_id="t1"):
        return store.show_task(self.root, task_id)["escalations"]

    def node(self, task_id="t1"):
        """The task's own trace node, current or in the history."""
        return trace.read(store.load_any(self.root, task_id)[1])

    def lock(self, kind, name=None):
        return layout.lock_file(self.root / ".concorde", kind, name)

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
        folder = self.folder("severity")
        self.assertEqual(str(folder / "decisions.md"), value["decision_log"])
        value = value["record"]
        worktree = self.root / ".claude/worktrees/severity"
        self.assertEqual(str(worktree), value["worktree"])
        self.assertEqual(
            (5, "open", head, None, [], []),
            (
                value["schema_version"],
                value["state"],
                value["base_commit"],
                value["main"],
                value["mains"],
                value["reports"],
            ),
        )
        self.assertNotIn(".claude", git(self.root, "status", "--porcelain"))
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/severity"))
        self.assertEqual("concorde/severity", git(worktree, "branch", "--show-current"))
        # One folder holds the record, the trace node, the decision log and the workspace folder.
        self.assertEqual(value, json.loads((folder / "task.json").read_text()))
        self.assertEqual(
            "# Decision log: severity\n\nGoal: let reports carry a severity\n",
            (folder / "decisions.md").read_text(),
        )
        self.assertTrue((folder / "workspace").is_dir())
        # The record keeps no history: runs, deliveries, sessions and escalations are elsewhere.
        for field in ("runs", "deliveries", "workflow", "sessions", "escalations"):
            self.assertNotIn(field, value)
        self.assert_contract(value)
        node = trace.read(folder)
        self.assertEqual(
            ("severity", "task", "running", None),
            (node["id"], node["kind"], node["status"], node["ended_at"]),
        )
        self.assertEqual(
            {
                "goal": "let reports carry a severity",
                "worktree": str(worktree),
                "transitions": [{"state": "open", "at": value["created_at"]}],
                "escalations": [],
                "closing": None,
            },
            node["content"]["data"],
        )
        self.assertEqual(
            ("severity", ["module.a"], "concorde/severity", head),
            tuple(
                node["metadata"][key]
                for key in ("task", "modules", "branch", "base_commit")
            ),
        )
        # The task's lock lies under .concorde/locks/, apart from the folder it protects.
        self.assertTrue(self.lock("task", "severity").is_file())
        self.assertFalse(any(folder.glob("*.lock")))

    @verifies("scenario.tasks.open")
    def test_open_binds_the_worktree_as_the_tasks_workspace(self):
        head = git(self.root, "rev-parse", "HEAD")
        record = self.project.open_task("t1", modules=("module.a", "module.b"))
        worktree = self.project.worktree("t1")
        self.assertEqual(
            {
                "schema_version": 2,
                "workspace": "t1",
                "root": str(worktree),
                "branch": "concorde/t1",
                "base_commit": head,
                "goal": "Fix A.",
                "modules": ["module.a", "module.b"],
                "traces": os.path.realpath(self.folder() / "workspace"),
                "concorde": os.path.realpath(self.root / ".concorde"),
            },
            binding.load(worktree),
        )
        self.assertEqual(record["worktree"], str(worktree))
        # The binding is the worktree's own state, never a change on the task branch.
        self.assertEqual("", git(worktree, "status", "--porcelain"))
        self.assertIsNone(binding.load(self.root))
        self.assertEqual("open", self.state())

    @verifies("scenario.tasks.open-carries-worker-configuration")
    def test_a_new_task_carries_the_worker_configuration_of_its_base_commit(self):
        def commit_models(root: Path, model: str) -> None:
            (root / models.CONFIG).write_text(
                json.dumps({"schema_version": 1, "default": {"model": model}})
            )
            git(root, "add", models.CONFIG)
            git(
                root,
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-qm",
                model,
            )

        commit_models(self.root, "anthropic/a")
        worktree = Path(self.project.open_task("t1")["worktree"])
        task_config = worktree / models.CONFIG
        self.assertEqual(
            "anthropic/a", json.loads(task_config.read_text())["default"]["model"]
        )
        self.assertEqual("", git(worktree, "status", "--porcelain"))
        # A models-only change committed on the primary branch reaches only later tasks.
        commit_models(self.root, "anthropic/b")
        self.assertEqual("", git(self.root, "status", "--porcelain", models.CONFIG))
        self.assertEqual(
            "anthropic/a", json.loads(task_config.read_text())["default"]["model"]
        )
        # The task changes its own models as any tracked file of its branch.
        commit_models(worktree, "anthropic/c")
        self.assertEqual(
            "anthropic/b",
            json.loads((self.root / models.CONFIG).read_text())["default"]["model"],
        )
        second = Path(self.project.open_task("t2")["worktree"])
        self.assertEqual(
            "anthropic/b",
            json.loads((second / models.CONFIG).read_text())["default"]["model"],
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
        self.assertFalse(self.folder("t3").exists())
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
        self.assertFalse(self.folder().exists())
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
        (escalation,) = self.escalations()
        self.assertEqual(
            (1, "main-agent", link),
            (escalation["number"], escalation["by"], escalation["error"]),
        )
        self.assertEqual(1, value["number"])
        # The chain is in the task's trace node, not in its record.
        self.assertEqual([escalation], self.node()["content"]["data"]["escalations"])
        self.assertNotIn("escalations", self.record())
        log = self.log()
        self.assertIn("Escalated to the developer", log)
        self.assertIn("Not handled here (decision)", log)
        self.assertEqual(str(self.folder() / "decisions.md"), value["decision_log"])
        self.assertIn("src/bmod/secret.py", value["rendered"])
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
        escalations = self.escalations()
        self.assertEqual(
            [
                {
                    "number": 1,
                    "at": escalations[0]["at"],
                    "by": "task-session",
                    "error": link,
                }
            ],
            escalations,
        )
        log = self.log()
        self.assertIn("workflow_decision", log)
        self.assertIn("the no-ask survey split module.a", log)
        self.assert_contract(self.record())

    @verifies("scenario.tasks.escalate-refused")
    def test_only_a_run_of_the_tasks_workspace_is_escalated(self):
        self.project.open_task("t1")
        log = self.log()
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
        run_id = "r-20260927T000000-understand-00000003"
        write_run(self.root, run_id, "t1", status="ok")
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
        self.assertEqual((1, "nothing_to_escalate"), (status, value["error"]["code"]))
        self.assertIn(f"{run_id} ended ok without an error", value["error"]["detail"])
        self.assertEqual([], self.escalations())
        self.assertEqual(log, self.log())

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
        self.assertIn("Escalated to the main agent", self.log())
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
        self.assertIn("Escalated to the developer", self.log())
        self.assertEqual(
            [("task-session", 1), ("main-agent", 2)],
            [(item["by"], item["number"]) for item in self.escalations()],
        )
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

    def started(self, task_id="t1", main="concorde-7d", session_id="s1"):
        """Record a task session of ``task_id`` started for ``main``."""
        session = {**self.session(task_id, session_id), "main": main}
        store.record_session(self.root, task_id, {**session, "started_at": store.now()})

    @verifies("scenario.tasks.report")
    def test_a_report_is_recorded_before_the_message(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        self.started()
        self.assertEqual("concorde-7d", self.record()["main"])
        status, value = self.command(
            "escalate",
            "t1",
            "--by",
            "task-session",
            "--code",
            "need_choice",
            "--detail",
            "which retry limit",
            "--reason",
            "decision",
            "--explanation",
            "the limit is a promise",
            cwd=worktree,
        )
        self.assertEqual(0, status, value)
        status, value = self.command(
            "report",
            "t1",
            "--text",
            "Escalation 1 needs your answer.",
            "--escalation",
            "1",
            cwd=worktree,
        )
        self.assertEqual(0, status, value)
        self.assertEqual("concorde-7d", value["main"])
        report = value["report"]
        self.assertEqual(
            (1, "concorde-7d", "Escalation 1 needs your answer.", [1], None),
            (
                report["number"],
                report["main"],
                report["text"],
                report["escalations"],
                report["answer"],
            ),
        )
        self.assertEqual(
            [report], store.show_task(self.root, "t1")["record"]["reports"]
        )
        self.assertEqual([report], self.record()["reports"])
        self.assert_contract(self.record())
        self.assertIn(
            f"## Report 1 to the main agent (concorde-7d), {report['at']}", self.log()
        )
        self.assertIn("Escalation 1 needs your answer.", self.log())
        before = snapshot(self.folder())
        self.assertEqual(
            (1, "unknown_escalation"),
            self.refusal("report", "t1", "--text", "x", "--escalation", "4"),
        )
        self.assertEqual(before, snapshot(self.folder()))
        # The session is no real Claude Code session, so the close warns of its transcript.
        self.assertEqual(
            0, self.command("close", "t1", "--completed", "--note", "done")[0]
        )
        self.assertEqual(
            (1, "task_closed"), self.refusal("report", "t1", "--text", "late")
        )

    @verifies("scenario.tasks.rebind")
    def test_the_main_agent_rebinds_its_tasks(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        self.started()
        status, value = self.command("rebind", "t1", "--main", "concorde-8e")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("concorde-8e", "concorde-7d"), (value["record"]["main"], value["former"])
        )
        self.assert_contract(self.record())
        self.assertEqual(
            ["concorde-7d", "concorde-8e"],
            [item["main"] for item in value["record"]["mains"]],
        )
        _, former = self.command("list", "--main", "concorde-7d")
        _, current = self.command("list", "--main", "concorde-8e")
        self.assertEqual(([], ["t1"]), (former, [item["id"] for item in current]))
        # The session of the task was started for the former name; its node keeps it.
        self.assertEqual(
            ["concorde-7d"],
            [item["main"] for item in store.show_task(self.root, "t1")["sessions"]],
        )
        _, value = self.command("report", "t1", "--text", "done", cwd=worktree)
        self.assertEqual("concorde-8e", value["main"])
        # Naming the same session again changes nothing in the trace.
        _, value = self.command("rebind", "t1", "--main", "concorde-8e")
        self.assertEqual(2, len(value["record"]["mains"]))
        self.assertEqual(
            (1, "not_primary"),
            self.refusal("rebind", "t1", "--main", "x", cwd=worktree),
        )
        self.assertEqual(
            0, self.command("close", "t1", "--completed", "--note", "done")[0]
        )
        self.assertEqual(
            (1, "task_closed"), self.refusal("rebind", "t1", "--main", "concorde-9f")
        )

    @verifies("scenario.tasks.answer")
    def test_an_answer_marks_reports_answered(self):
        self.project.open_task("t1")
        self.started()
        store.report(self.root, "t1", "first", [])
        store.report(self.root, "t1", "second", [])
        status, value = self.command(
            "answer", "t1", "--report", "1", "--report", "2", "--text", "Go on."
        )
        self.assertEqual(0, status, value)
        self.assertEqual([1, 2], [item["number"] for item in value["answered"]])
        reports = self.record()["reports"]
        self.assertEqual(
            [("Go on.", "main-agent")] * 2,
            [(item["answer"]["text"], item["answer"]["by"]) for item in reports],
        )
        self.assert_contract(self.record())
        self.assertIn("## Answer to report(s) 1, 2 of the task session", self.log())
        before = snapshot(self.folder())
        self.assertEqual(
            (1, "already_answered"),
            self.refusal("answer", "t1", "--report", "1", "--text", "Again."),
        )
        self.assertEqual(
            (1, "unknown_report"),
            self.refusal("answer", "t1", "--report", "3", "--text", "Again."),
        )
        self.assertEqual(before, snapshot(self.folder()))
        self.assertEqual(
            (1, "not_primary"),
            self.refusal(
                "answer",
                "t1",
                "--report",
                "1",
                "--text",
                "x",
                cwd=self.project.worktree("t1"),
            ),
        )

    @verifies("scenario.tasks.close-settles-reports")
    def test_closing_a_task_answers_its_unanswered_reports(self):
        self.project.open_task("t1")
        self.started()
        for text in ("first", "second", "third"):
            store.report(self.root, "t1", text, [])
        store.answer(self.root, "t1", [1], "Go on.")
        status, closed = self.command(
            "close", "t1", "--completed", "--note", "the probe answered"
        )
        self.assertEqual(0, status, closed)
        reports = self.record()["reports"]
        at = closed["record"]["closed"]["at"]
        settling = (
            "The task ended before the main agent answered: `concorde task close "
            "--completed` closed it as completed: the probe answered. Nobody answers a "
            "report after that."
        )
        self.assertEqual("main-agent", reports[0]["answer"]["by"])
        self.assertEqual(
            [{"at": at, "text": settling, "by": "close"}] * 2,
            [item["answer"] for item in reports[1:]],
        )
        self.assert_contract(self.record())
        self.assertTrue(
            self.log().endswith(
                f"## Closed: completed, {at}\n\nthe probe answered\n\n"
                f"The close answered report(s) 2, 3 of the task session, unanswered until "
                f"then: {settling}\n"
            ),
            self.log(),
        )
        # The committed copy is the log as the task ended.
        self.assertEqual(
            self.log(), (self.root / ".concorde/decisions/t1.md").read_text()
        )
        self.assertEqual(
            (1, "task_closed"),
            self.refusal("answer", "t1", "--report", "2", "--text", "late"),
        )
        # A failed close answers them likewise, with its reason.
        self.project.open_task("t2")
        self.started("t2", session_id="s2")
        store.report(self.root, "t2", "stuck", [])
        status, _ = self.command(
            "close", "t2", "--failed", "--reason", "wrong direction", "--no-error"
        )
        self.assertEqual(0, status)
        answer = self.record("t2")["reports"][0]["answer"]
        self.assertEqual("close", answer["by"])
        self.assertIn(
            "`concorde task close --failed` closed it as failed: wrong direction",
            answer["text"],
        )
        self.assertIn(
            "The close answered report(s) 1 of the task session", self.log("t2")
        )

    @verifies("scenario.tasks.list-not-ended")
    def test_the_tasks_not_ended_that_name_a_session_are_listed(self):
        for task_id, main in (("t1", "concorde-7d"), ("t2", "concorde-7d")):
            self.project.open_task(task_id)
            self.started(task_id, main=main, session_id=f"s-{task_id}")
        self.project.open_task("t3")
        self.started("t3", main="concorde-8e", session_id="s-t3")
        self.assertEqual(
            0, self.command("close", "t1", "--completed", "--note", "done")[0]
        )
        _, both = self.command("list", "--main", "concorde-7d")
        self.assertEqual(["t1", "t2"], [item["id"] for item in both])
        status, listed = self.command(
            "list", "--main", "concorde-7d", "--state", "open,active,delivered,merging"
        )
        self.assertEqual(0, status, listed)
        self.assertEqual(["t2"], [item["id"] for item in listed])
        _, ended = self.command("list", "--state", "closed,failed")
        self.assertEqual(["t1"], [item["id"] for item in ended])
        self.assertEqual(
            (1, "invalid_input"), self.refusal("list", "--state", "open,finished")
        )

    @verifies("scenario.tasks.report-merge-incomplete")
    def test_reports_and_rebinds_go_on_while_a_merge_is_unfinished(self):
        self.project.open_task("t1")
        self.project.open_task("t2")
        self.started("t2", session_id="s2")
        head = git(self.root, "rev-parse", "HEAD")
        store.begin_merge(
            self.root,
            "t1",
            {
                "before": head,
                "checked": head,
                "branch": "main",
                "after": None,
                "history": "t1",
                "checks": [["true"]],
                "since": store.now(),
                "pid": 999999,
            },
        )
        worktree = self.project.worktree("t2")
        status, refused = self.command(
            "escalate",
            "t2",
            "--by",
            "task-session",
            "--code",
            "x",
            "--detail",
            "x",
            "--reason",
            "decision",
            "--explanation",
            "x",
            cwd=worktree,
        )
        self.assertEqual((1, "merge_incomplete"), (status, refused["error"]["code"]))
        status, value = self.command(
            "report", "t2", "--text", json.dumps(refused), cwd=worktree
        )
        self.assertEqual((0, 1), (status, value["report"]["number"]))
        status, value = self.command("rebind", "t1", "--main", "concorde-8e")
        self.assertEqual((0, "concorde-8e"), (status, value["record"]["main"]))
        self.assertEqual("merging", self.record("t1")["state"])

    @verifies("scenario.tasks.old-record")
    def test_a_task_opened_before_the_main_was_recorded_keeps_working(self):
        self.project.open_task("t1")
        self.started()
        folder = self.folder()
        # Write the record back as it was before the main was recorded.
        record = json.loads((folder / "task.json").read_text())
        del record["main"], record["mains"], record["reports"], record["resolves"]
        record["schema_version"] = 2
        (folder / "task.json").write_text(json.dumps(record, indent=2) + "\n")
        node = trace.read(folder)
        shown = store.show_task(self.root, "t1")["record"]
        self.assertEqual("concorde-7d", shown["main"])
        self.assertEqual(["concorde-7d"], [item["main"] for item in shown["mains"]])
        self.assertEqual([], shown["reports"])
        _, listed = self.command("list", "--main", "concorde-7d")
        self.assertEqual(["t1"], [item["id"] for item in listed])
        store.report(self.root, "t1", "still reachable", [])
        store.rebind(self.root, "t1", "concorde-8e")
        stored = json.loads((folder / "task.json").read_text())
        self.assertEqual(
            (5, "concorde-8e", ["concorde-7d", "concorde-8e"], 1),
            (
                stored["schema_version"],
                stored["main"],
                [item["main"] for item in stored["mains"]],
                len(stored["reports"]),
            ),
        )
        self.assert_contract(stored)
        # The trace node keeps the shape an earlier Concorde writes.
        self.assertEqual(node["content"], trace.read(folder)["content"])
        # A record of version 3 holds answers only the main agent gave.
        store.answer(self.root, "t1", [1], "Go on.")
        stored = json.loads((folder / "task.json").read_text())
        del stored["reports"][0]["answer"]["by"]
        stored["schema_version"] = 3
        (folder / "task.json").write_text(json.dumps(stored, indent=2) + "\n")
        answer = store.show_task(self.root, "t1")["record"]["reports"][0]["answer"]
        self.assertEqual(("Go on.", "main-agent"), (answer["text"], answer["by"]))
        self.assertEqual(5, self.record()["schema_version"])

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
        self.assertEqual(
            (1, "not_primary"),
            self.refusal("rebind", "t1", "--main", "m", cwd=worktree),
        )
        self.assertEqual(
            (1, "not_primary"),
            self.refusal("answer", "t1", "--report", "1", "--text", "x", cwd=worktree),
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
            (str(self.folder() / "decisions.md"), str(self.folder()), [], []),
            (
                shown["decision_log"],
                shown["folder"],
                shown["sessions"],
                shown["escalations"],
            ),
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

    @verifies("scenario.main-session.claude-sees-by-query")
    def test_show_gives_another_session_the_state_of_runs_and_sessions(self):
        # A main session that owns neither the run nor the task session, such as one nothing is
        # pushed into, sees both by asking once.
        self.project.open_task("t1")
        run = write_run(self.root, "r-20260927T000001-implement-00000003", "t1")
        store.record_session(
            self.root,
            "t1",
            {
                "id": "task-t1-s",
                "reported_id": "task-t1-s",
                "name": "task-t1",
                "main": "0199a3",
                "model": None,
                "started_at": store.now(),
            },
        )
        _, shown = self.command("show", "t1")
        self.assertEqual(
            [(run.parent.name, "ok")],
            [(item["run_id"], item["status"]) for item in shown["runs"]],
        )
        # The main session a task session reports to is the `main` of its trace node.
        self.assertEqual(
            [("task-t1-s", "task-t1", "0199a3")],
            [(item["id"], item["name"], item["main"]) for item in shown["sessions"]],
        )

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
        )
        # Its runner holds the run lock, as a live runner does.
        self.enterContext(
            locks.hold(
                self.lock("run", "r-20260927T000001-implement-00000003"), "test runner"
            )
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
        with workspace_lock(
            store.workspace_store(self.root, "t1"), "t1", "implement run r-held"
        ):
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

    @verifies("scenario.tasks.interrupted", "scenario.execution.run-lock")
    def test_a_dead_host_leaves_an_interrupted_run(self):
        self.project.open_task("t1")
        # The runner ran in a sandbox's PID namespace, where it was process 2; on the host that
        # number names a live, unrelated process, which must not make the run look alive.
        write_run(
            self.root,
            "r-20260927T000000-implement-00000001",
            "t1",
            name="implement",
            status=None,
            host_pid=1,
        )
        shown = store.show_task(self.root, "t1")
        self.assertEqual(["lost"], [run["status"] for run in shown["runs"]])
        self.assertIsNone(shown["busy"])
        self.assertEqual("active", shown["record"]["state"])

    @verifies("scenario.tasks.concurrent-update")
    def test_a_concurrent_change_is_detected(self):
        self.project.open_task("t1")
        path = self.folder() / "task.json"
        calls = {"n": 0}

        def meddled(record):
            # Another process that does not take the task's lock changes the record between
            # Tasks' read and its write.
            calls["n"] += 1
            value = json.loads(path.read_text())
            value["goal"] = f"changed by another process {calls['n']}"
            path.write_text(json.dumps(value))
            record["modules"] = [*record["modules"], "module.b"]
            return record

        with self.assertRaises(store.TaskError) as raised:
            store.update(self.root, "t1", meddled)
        self.assertEqual("record_conflict", raised.exception.code)
        self.assertEqual(3, calls["n"])
        self.assertEqual("changed by another process 3", self.record()["goal"])
        self.assertEqual(["module.a"], self.record()["modules"])

        def meddled_once(record):
            calls["n"] += 1
            if calls["n"] == 1:
                value = json.loads(path.read_text())
                value["goal"] = "changed once"
                path.write_text(json.dumps(value))
            record["modules"] = [*record["modules"], "module.b"]
            return record

        calls["n"] = 0
        record = store.update(self.root, "t1", meddled_once)
        # The update was applied again to what the other process wrote.
        self.assertEqual(2, calls["n"])
        self.assertEqual(
            ("changed once", ["module.a", "module.b"]),
            (record["goal"], record["modules"]),
        )
        self.assertEqual(record, self.record())

    def deliver(self, task_id="t1"):
        return deliver(self.project.worktree(task_id))

    @verifies("scenario.tasks.delivered-reopened")
    def test_a_writing_run_reopens_a_delivered_task(self):
        self.project.open_task("t1")
        head = self.deliver()
        shown = store.show_task(self.root, "t1")
        self.assertEqual("delivered", shown["record"]["state"])
        self.assertEqual([{"commit": head, "mismatches": []}], shown["deliveries"])
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
            [head, second],
            [item["commit"] for item in store.show_task(self.root, "t1")["deliveries"]],
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
        # The subject of a delivery commit on a commit with two parents.
        head = deliver(worktree, verifies=False)
        shown = store.show_task(self.root, "t1")
        self.assertEqual("active", shown["record"]["state"])
        self.assertEqual([head], [item["commit"] for item in shown["deliveries"]])
        (mismatch,) = shown["deliveries"][0]["mismatches"]
        self.assertIn("it has 2 parent(s)", mismatch)
        self.assertEqual(
            ["active"], [item["state"] for item in store.list_tasks(self.root)]
        )
        git(self.root, "merge", "--ff-only", "concorde/t1")
        before = self.record()
        status, value = self.close("t1", "--merged")
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
        # The next delivery that verifies delivers the task.
        deliver(worktree, text="second = True\n")
        shown = store.show_task(self.root, "t1")
        self.assertEqual("delivered", shown["record"]["state"])
        self.assertEqual([], shown["deliveries"][1]["mismatches"])

    @verifies("scenario.tasks.close-merged")
    def test_close_a_merged_task(self):
        self.project.open_task("t1")
        head = self.deliver()
        worktree = self.project.worktree("t1")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        status, value = self.close("t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "merged"), (value["state"], value["closed"]["outcome"])
        )
        self.assertEqual(head, value["closed"]["primary_commit"])
        self.assertTrue(value["closed"]["worktree_removed"])
        self.assertEqual("t1", value["closed"]["history"])
        self.assertFalse(worktree.exists())
        self.assertEqual(head, git(self.root, "rev-parse", "concorde/t1"))
        # The whole folder moved to the history, and the task's locks are gone.
        self.assertFalse(self.folder().exists())
        history = self.history()
        self.assertEqual(value, json.loads((history / "task.json").read_text()))
        self.assertIn("## Closed: merged", (history / "decisions.md").read_text())
        # A merge made by hand has no merge commit to carry the log, so the close commits it
        # alone, with its closing, on top of the merged head.
        self.assertEqual(
            [head], git(self.root, "rev-list", "--parents", "-n1", "HEAD").split()[1:]
        )
        self.assert_log_committed("t1", history)
        self.assertTrue((history / "workspace").is_dir())
        self.assertFalse((history / "runtime").exists())
        node = trace.read(history)
        self.assertEqual(
            ("ok", "merged", value["closed"]["at"]),
            (node["status"], node["outcome"], node["ended_at"]),
        )
        self.assertEqual(
            ["open", "closed"],
            [item["state"] for item in node["content"]["data"]["transitions"]],
        )
        self.assertEqual("merged", node["content"]["data"]["closing"]["outcome"])
        for kind in ("task", "workspace", "workflow"):
            self.assertFalse(self.lock(kind, "t1").exists(), kind)
        self.assert_contract(self.record())
        # The history still answers list and show.
        _, shown = self.command("show", "t1")
        self.assertEqual(
            ("closed", str(history), str(history / "decisions.md"), None),
            (
                shown["record"]["state"],
                shown["folder"],
                shown["decision_log"],
                shown["busy"],
            ),
        )
        _, listed = self.command("list")
        self.assertEqual(
            [("t1", "closed")], [(item["id"], item["state"]) for item in listed]
        )

    @verifies(
        "scenario.tasks.close-submodules", "scenario.tasks.close-submodules-dirty"
    )
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
        modules = Path(
            git(
                worktree, "rev-parse", "--path-format=absolute", "--git-path", "modules"
            )
        )
        self.assertTrue((modules / "vendor/lib").is_dir())
        (worktree / "vendor/lib/README.md").write_text("changed inside the submodule\n")
        git(self.root, "merge", "--ff-only", "concorde/t1")
        before = self.record()
        self.assertEqual((1, "dirty_worktree"), self.refusal("close", "t1", "--merged"))
        # A configuration that tells Git to ignore the submodule hides nothing from the close.
        git(self.root, "config", "submodule.vendor/lib.ignore", "all")
        self.assertEqual((1, "dirty_worktree"), self.refusal("close", "t1", "--merged"))
        self.assertTrue(worktree.exists())
        self.assertEqual(before, self.record())
        git(worktree / "vendor/lib", "checkout", "--", "README.md")
        shared = self.root / ".git/config"
        config = shared.read_text()
        self.assertIn('[submodule "vendor/lib"]', config)
        status, value = self.close("t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(head, value["closed"]["primary_commit"])
        self.assertTrue(value["closed"]["worktree_removed"])
        self.assertFalse(worktree.exists())
        self.assertFalse(modules.exists())
        # The submodule stays registered for every other worktree.
        self.assertEqual(config, shared.read_text())

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

    @verifies("scenario.tasks.close-completed-no-note")
    def test_closing_as_completed_needs_a_note(self):
        self.project.open_task("t1")
        before = self.record()
        self.assertEqual(
            (1, "invalid_input"), self.refusal("close", "t1", "--completed")
        )
        self.assertTrue(self.project.worktree("t1").exists())
        self.assertEqual(before, self.record())

    @verifies("scenario.tasks.close-completed-dirty")
    def test_closing_as_completed_keeps_uncommitted_changes_without_force(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("dirty = True\n")
        before = self.record()
        self.assertEqual(
            (1, "dirty_worktree"),
            self.refusal("close", "t1", "--completed", "--note", "tried it"),
        )
        self.assertEqual("dirty = True\n", (worktree / "src/a/calc.py").read_text())
        self.assertEqual(before, self.record())

    def assert_log_committed(self, key, history, task_id="t1"):
        """The primary branch's head commits the history's decision log alone as ``key``."""
        path = f".concorde/decisions/{key}.md"
        self.assertEqual(
            [path], git(self.root, "show", "--name-only", "--format=", "HEAD").split()
        )
        self.assertEqual(
            (history / "decisions.md").read_text().strip(),
            git(self.root, "show", f"HEAD:{path}"),
        )
        message = git(self.root, "log", "-1", "--format=%B")
        self.assertTrue(
            message.startswith(f"concorde: keep the decision log of {task_id}\n"),
            message,
        )
        self.assertTrue(message.endswith(f"Concorde-Task: {task_id}"), message)

    @verifies("scenario.tasks.close-commits-log")
    def test_a_close_commits_the_decision_log_alone(self):
        self.project.open_task("t1")
        before = git(self.root, "rev-parse", "HEAD")
        # The primary worktree's own changes, staged and not, are no part of the commit.
        (self.root / "src/a/calc.py").write_text("staged = True\n")
        git(self.root, "add", "src/a/calc.py")
        (self.root / "src/bmod/secret.py").write_text("unstaged = True\n")
        changes = git(self.root, "status", "--porcelain", "--untracked-files=no")
        # On a detached HEAD there is no branch to commit on: the close stops before moving.
        git(self.root, "checkout", "-q", "--detach")
        arguments = ("t1", "--failed", "--reason", "the probe failed", "--no-error")
        status, value = self.close(*arguments)
        self.assertEqual(1, status, value)
        self.assertEqual("decision_log_uncommitted", value["error"]["code"])
        self.assertIn("detached HEAD", value["error"]["detail"])
        self.assertEqual(before, git(self.root, "rev-parse", "HEAD"))
        self.assertTrue(self.folder().exists())
        self.assertFalse((self.root / ".concorde/decisions").exists())
        self.assertEqual("failed", self.record()["state"])
        git(self.root, "checkout", "-q", "-")
        status, value = self.close(*arguments)
        self.assertEqual(0, status, value)
        self.assertEqual(
            [before], git(self.root, "rev-list", "--parents", "-n1", "HEAD").split()[1:]
        )
        self.assert_log_committed("t1", self.history())
        self.assertIn("the probe failed", (self.history() / "decisions.md").read_text())
        self.assertEqual(
            changes, git(self.root, "status", "--porcelain", "--untracked-files=no")
        )
        self.assertFalse(self.folder().exists())

    @verifies("scenario.tasks.close-completed")
    def test_close_a_task_that_reached_its_goal_without_merging(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("dirty = True\n")
        status, value = self.close(
            "t1", "--completed", "--note", "the probe answered", "--force"
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
        self.assertFalse(self.folder().exists())
        log = (self.history() / "decisions.md").read_text()
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
        status, value = self.close(
            "t1", "--failed", *reason, "--run", failed["run_id"], "--force"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("failed", "failed", reason[1]),
            (value["state"], value["closed"]["outcome"], value["closed"]["note"]),
        )
        self.assertEqual([failed["error"]], value["closed"]["errors"])
        log = (self.history() / "decisions.md").read_text()
        self.assertIn("## Closed: failed", log)
        self.assertIn(failed["error"]["code"], log)
        self.assert_contract(self.record())
        # The trace node ends failed with the first error chain that caused the failure.
        node = self.node()
        self.assertEqual(
            ("failed", "failed", failed["error"]),
            (node["status"], node["outcome"], node["error"]),
        )
        # The run that failed moved to the history with the task.
        self.assertTrue(
            (
                self.history() / "workspace/runs" / failed["run_id"] / "result.json"
            ).is_file()
        )

    @verifies("scenario.tasks.close-failed-no-error")
    def test_a_task_that_failed_for_no_error_closes_without_errors(self):
        self.project.open_task("t1")
        status, value = self.close(
            "t1",
            "--failed",
            "--reason",
            "the direction was wrong",
            "--no-error",
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("failed", "the direction was wrong", []),
            (value["state"], value["closed"]["note"], value["closed"]["errors"]),
        )
        self.assert_contract(self.record())
        node = self.node()
        self.assertEqual(
            ("failed", "failed", None), (node["status"], node["outcome"], node["error"])
        )

    @verifies("scenario.tasks.close-failed-invalid")
    def test_a_failed_close_needs_a_reason_and_one_error_choice(self):
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
        run_id = failed["run_id"]
        before = self.record()
        reason = ["--reason", "the change needs module.b, which is out of scope"]
        for argv in (
            reason,
            (*reason, "--no-error", "--run", run_id),
            ("--run", run_id),
        ):
            self.assertEqual(
                (1, "invalid_input"), self.refusal("close", "t1", "--failed", *argv)
            )
        self.assertTrue(self.project.worktree("t1").exists())
        self.assertEqual(before, self.record())

    @verifies("scenario.tasks.closed-inert")
    def test_a_closed_task_accepts_no_run(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        self.close("t1", "--completed", "--note", "done")
        # Closing removes the worktree and with it the workspace binding, so no run of the
        # task's workspace can start; a run recorded anyway leaves the task closed.
        self.assertFalse(binding.path_of(worktree).exists())
        write_run(
            self.root,
            "r-20260927T000000-test-00000001",
            "t1",
            name="test",
            traces=self.history() / "workspace",
        )
        self.assertEqual("closed", self.state())
        _, closed = self.command("list", "--state", "closed")
        self.assertEqual(["t1"], [item["id"] for item in closed])
        with self.assertRaises(store.TaskError) as raised:
            store.record_session(self.root, "t1", self.session("t1"))
        self.assertEqual("task_closed", raised.exception.code)
        # Refusing it made no lock of the closed task again.
        self.assertFalse(self.lock("task", "t1").exists())

    @staticmethod
    def session(task_id, session_id="s1"):
        return {
            "id": session_id,
            "reported_id": session_id,
            "name": f"task-{task_id}",
            "main": "main",
            "model": None,
        }

    def child(self, code, *argv):
        """A child process running ``code`` with Concorde importable, once it said it is
        ready."""
        process = subprocess.Popen(
            [sys.executable, "-c", code, *argv],
            stdout=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT / "src")},
        )
        self.addCleanup(process.wait, 30)
        self.addCleanup(process.stdout.close)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.assertEqual("ready\n", process.stdout.readline())
        return process

    @verifies("scenario.tasks.close-stops-runs")
    def test_a_failed_close_stops_what_still_runs_before_the_folder_moves(self):
        self.project.open_task("t1")
        run_id = "r-20260927T000000-implement-00000001"
        folder = write_run(
            self.root, run_id, "t1", name="implement", status=None
        ).parent
        runner = self.child(
            RUNNER, str(self.root / ".concorde"), "t1", run_id, str(folder)
        )
        shown = store.show_task(self.root, "t1")
        self.assertEqual(["running"], [run["status"] for run in shown["runs"]])
        self.assertIn(run_id, shown["busy"])
        status, value = self.close(
            "t1",
            "--failed",
            "--reason",
            "the direction was wrong",
            "--no-error",
        )
        self.assertEqual(0, status, value)
        # It was stopped with SIGTERM and ended on its own.
        self.assertEqual(0, runner.wait(30))
        self.assertEqual(
            ("failed", "failed"), (value["state"], value["closed"]["outcome"])
        )
        # Only then did the folder move: the run's own result is in the history, and nothing was written into the task's former folder afterwards.
        self.assertFalse(self.folder().exists())
        result = json.loads(
            (self.history() / "workspace/runs" / run_id / "result.json").read_text()
        )
        self.assertEqual(
            ("failed", "stopped by SIGTERM"), (result["status"], result["summary"])
        )
        shown = store.show_task(self.root, "t1")
        self.assertEqual(str(self.history()), shown["folder"])
        self.assertEqual(
            [(run_id, "failed")],
            [(run["run_id"], run["status"]) for run in shown["runs"]],
        )
        for kind in ("task", "workspace", "workflow", "run"):
            name = run_id if kind == "run" else "t1"
            self.assertFalse(self.lock(kind, name).exists(), kind)

    @verifies("scenario.tasks.closed-run-refused")
    def test_a_run_in_the_worktree_of_a_closed_task_is_refused(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        bound = binding.path_of(worktree).read_text()
        status, value = self.close("t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        # The worktree is put back by hand, with its binding.
        git(self.root, "worktree", "add", str(worktree), "concorde/t1")
        binding.path_of(worktree).parent.mkdir(parents=True, exist_ok=True)
        binding.path_of(worktree).write_text(bound)
        before = snapshot(self.history())
        status, value = self.project.run("task-validation", cwd=worktree)
        self.assertEqual(1, status, value)
        self.assertIn("binding_invalid", codes(value["error"]), value["error"])
        self.assertIn(str(self.folder() / "workspace"), json.dumps(value["error"]))
        self.assertEqual(before, snapshot(self.history()))
        self.assertFalse(self.folder().exists())

    @verifies("scenario.tasks.history-key")
    def test_a_reused_name_gets_its_own_history_folder(self):
        self.project.open_task("retry")
        status, value = self.close("retry", "--completed", "--note", "first")
        self.assertEqual((0, "retry"), (status, value["closed"]["history"]), value)
        git(self.root, "branch", "-D", "concorde/retry")
        first = snapshot(self.history("retry"))
        self.project.open_task("retry")
        status, value = self.close("retry", "--completed", "--note", "second")
        self.assertEqual((0, "retry.2"), (status, value["closed"]["history"]), value)
        self.assertEqual(
            "second",
            json.loads((self.history("retry.2") / "task.json").read_text())["closed"][
                "note"
            ],
        )
        self.assertEqual(first, snapshot(self.history("retry")))
        self.assertFalse(self.folder("retry").exists())
        # The name shows the latest; each history key shows its own.
        _, shown = self.command("show", "retry")
        self.assertEqual(str(self.history("retry.2")), shown["folder"])
        _, shown = self.command("show", "retry.2")
        self.assertEqual("second", shown["record"]["closed"]["note"])
        _, listed = self.command("list")
        self.assertEqual(
            ["first", "second"], [item["closed"]["note"] for item in listed]
        )
        # Each key's decision log is committed; once retention removed the history folders,
        # the committed logs alone keep their keys taken.
        for key in ("retry", "retry.2"):
            self.assertTrue((self.root / f".concorde/decisions/{key}.md").is_file())
            shutil.rmtree(self.history(key))
        git(self.root, "branch", "-D", "concorde/retry")
        self.project.open_task("retry")
        status, value = self.close("retry", "--completed", "--note", "third")
        self.assertEqual((0, "retry.3"), (status, value["closed"]["history"]), value)
        self.assert_log_committed("retry.3", self.history("retry.3"), "retry")

    def read_only_log(self, task_id="t1"):
        log = self.folder(task_id) / "decisions.md"
        log.chmod(0o444)
        self.addCleanup(lambda: log.exists() and log.chmod(0o644))
        return log

    @verifies("scenario.tasks.close-rerun", "scenario.tasks.close-other-outcome")
    def test_running_a_close_again_finishes_it(self):
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        real_git = store._git

        def refusing_removal(root, *arguments, check=True):
            if arguments[:2] == ("worktree", "remove"):
                return subprocess.CompletedProcess(arguments, 128, "", "fatal: locked")
            return real_git(root, *arguments, check=check)

        with patch.object(store, "_git", refusing_removal):
            status, value = self.close("t1", "--completed", "--note", "done")
        self.assertEqual((1, "worktree_failed"), (status, value["error"]["code"]))
        self.assertIn("record of task t1 is unchanged", value["error"]["detail"])
        self.assertIn("finishes the close", value["error"]["detail"])
        self.assertTrue(worktree.exists())
        real = store.update

        def conflicting(primary, task_id, change, *, locked=False):
            raise store.TaskError(
                "record_conflict", f"task {task_id} changed concurrently"
            )

        with patch.object(store, "update", conflicting):
            status, value = self.close("t1", "--completed", "--note", "done")
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
        self.assertTrue(self.folder().is_dir())
        self.assertIs(real, store.update)
        status, value = self.close("t1", "--completed", "--note", "done")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", False), (value["state"], value["closed"]["worktree_removed"])
        )
        self.assertIn("## Closed: completed", self.log())
        self.assertFalse(self.folder().exists())
        self.assertTrue((self.history() / "task.json").is_file())
        # The record is written but the decision log refuses the closing.
        self.project.open_task("t2")
        log = self.read_only_log("t2")
        status, value = self.close("t2", "--failed", "--reason", "no", "--no-error")
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
        # The folder moves only once the closing is in the decision log.
        self.assertTrue(self.folder("t2").is_dir())
        self.assertEqual(
            (1, "invalid_transition"),
            self.refusal("close", "t2", "--completed", "--note", "other"),
        )
        log.chmod(0o644)
        status, value = self.close("t2", "--failed", "--reason", "no", "--no-error")
        self.assertEqual(0, status, value)
        self.assertEqual(stored, self.record("t2"))
        self.assertFalse(self.folder("t2").exists())
        self.assertTrue((self.history("t2") / "task.json").is_file())
        heading = f"## Closed: failed, {stored['closed']['at']}"
        self.assertEqual(1, self.log("t2").splitlines().count(heading))
        self.assertIn("\nno\n", self.log("t2"))
        closing = self.log("t2")
        for argv in (
            ("--failed", "--reason", "no", "--no-error"),
            ("--completed", "--note", "other"),
        ):
            self.assertEqual(
                (1, "invalid_transition"), self.refusal("close", "t2", *argv)
            )
        self.assertEqual((stored, closing), (self.record("t2"), self.log("t2")))
        self.assert_contract(self.record("t2"))

    def log(self, task_id="t1"):
        """The task's decision log, in its folder or, once closed, in the history."""
        return store.decision_log_path(self.root, task_id).read_text()

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
        self.assertEqual(1, len(self.escalations()))
        self.assertEqual(before, self.log())
        self.assert_contract(self.record())


if __name__ == "__main__":
    unittest.main()
