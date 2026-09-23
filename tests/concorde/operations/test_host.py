"""The Operation host: ``concorde run`` with test providers standing in for real ones."""

from __future__ import annotations

import json
import os
import signal
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.operations import catalog
from concorde.operations.host import RESULT_SCHEMA
from concorde.operations.provider import Continue, Provider, evidence
from concorde.spec.verification import verifies
from concorde.tasks import store
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT


def worker_step(ctx):
    return ctx.run_worker(
        ctx.arguments.goal,
        task_type="implement",
        checks=True,
        rounds=ctx.arguments.rounds,
    )


def goal_arguments(parser):
    parser.add_argument("--goal", default="Do it.")
    parser.add_argument("--rounds", type=int, default=1)


def deterministic_step(ctx):
    return Continue(
        output={"ready": True}, evidence=[evidence("readiness", "", "ready")]
    )


def raising_step(ctx):
    raise RuntimeError("boom")


def admitted_step(ctx):
    return Continue(output={"inputs": sorted(ctx.inputs)})


WORKER = Provider("implement", "implement", True, (worker_step,), None, goal_arguments)
DETERMINISTIC = Provider("validate", None, False, (deterministic_step,))
RAISING = Provider("test", None, False, (raising_step,))
ADMITTED = Provider("understand", None, False, (admitted_step,))


class HostTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.project.open_task("t1")
        self.worktree = self.project.worktree("t1")
        patcher = patch.dict(
            catalog.CATALOG,
            {
                "implement": f"{__name__}:WORKER",
                "validate": f"{__name__}:DETERMINISTIC",
                "test": f"{__name__}:RAISING",
                "understand": f"{__name__}:ADMITTED",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def implement(self, steps, *extra):
        return self.project.run(
            "implement", "--task", "t1", "--goal", OperationProject.plan(steps), *extra
        )

    def saved(self, envelope):
        return json.loads(
            (
                self.root / ".concorde/runs" / envelope["run_id"] / "result.json"
            ).read_text()
        )

    def run_status(self, envelope):
        record = store.load_task(self.root, "t1")
        return {run["run_id"]: run["status"] for run in record["runs"]}.get(
            envelope["run_id"]
        )

    @verifies("scenario.operations.worker-ok")
    def test_a_worker_backed_run_succeeds(self):
        status, envelope = self.implement(
            [
                {
                    "writes": {
                        f"{self.worktree}/src/a/calc.py": "def add(a, b):\n    return a + b\n"
                    }
                }
            ]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        kinds = {item["kind"] for item in envelope["host_evidence"]}
        self.assertTrue(
            {"grant", "context-identity", "audit", "check", "rounds"} <= kinds
        )
        self.assertEqual("done", envelope["worker"]["summary"])
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertIsNone(envelope["escalation"])
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual("ok", self.run_status(envelope))

    @verifies("scenario.operations.worker-blocked")
    def test_a_blocked_worker_escalates(self):
        status, envelope = self.implement(
            [
                {
                    "result": {
                        "status": "blocked",
                        "problem": "the Spec does not state the rounding rule",
                        "options": ["round per line", "round per order"],
                        "recommendation": "round per order",
                        "blocking": True,
                    }
                }
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        escalation = envelope["escalation"]
        self.assertEqual("worker", escalation["source"])
        self.assertEqual(
            "the Spec does not state the rounding rule", escalation["problem"]
        )
        self.assertEqual("round per order", escalation["recommendation"])
        host_text = json.dumps(envelope["host_evidence"]) + envelope["summary"]
        self.assertNotIn("rounding rule", host_text)

    @verifies("scenario.operations.checks-exhausted")
    def test_checks_still_failing_after_the_last_round(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/a/flag": "broken"}}], "--rounds", "1"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("ok", envelope["worker"]["status"])
        checks = [item for item in envelope["host_evidence"] if item["kind"] == "check"]
        self.assertTrue(
            checks
            and "exit 1" in checks[-1]["detail"]
            and "log" in checks[-1]["detail"]
        )
        self.assertIn("2 round(s)", json.dumps(envelope["host_evidence"]))
        self.assertEqual("host", envelope["escalation"]["source"])

    @verifies("scenario.operations.audit-violation")
    def test_a_write_outside_the_grant_fails_the_run(self):
        status, envelope = self.implement(
            [{"writes": {f"{self.worktree}/src/bmod/secret.py": "SECRET = 2\n"}}]
        )
        self.assertEqual("failed", envelope["status"])
        audits = [item for item in envelope["host_evidence"] if item["kind"] == "audit"]
        self.assertIn("src/bmod/secret.py", audits[0]["detail"])
        self.assertFalse(
            any(item["kind"] == "check" for item in envelope["host_evidence"])
        )

    @verifies("scenario.operations.deterministic")
    def test_a_deterministic_operation_launches_no_worker(self):
        status, envelope = self.project.run("validate", "--task", "t1")
        self.assertEqual((0, "ok"), (status, envelope["status"]))
        self.assertIsNone(envelope["worker"])
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual({"ready": True}, envelope["output"])

    @verifies("scenario.operations.refused-task")
    def test_a_task_that_cannot_accept_a_run_is_refused(self):
        status, envelope = self.project.run("validate", "--task", "missing")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual("unknown_task", envelope["host_evidence"][0]["ref"])
        self.assertEqual("host", envelope["escalation"]["source"])
        store.begin_run(
            self.root, "t1", "r-other", "implement", ["module.a"], True, os.getpid()
        )
        before = store.load_task(self.root, "t1")
        status, envelope = self.project.run("validate", "--task", "t1")
        self.assertEqual("failed", envelope["status"])
        self.assertEqual("task_busy", envelope["host_evidence"][0]["ref"])
        self.assertIsNone(envelope["output"])
        self.assertEqual(before["runs"], store.load_task(self.root, "t1")["runs"])

    @verifies("scenario.operations.bad-command")
    def test_a_malformed_command_line_writes_nothing(self):
        runs = self.root / ".concorde/runs"
        before = sorted(runs.iterdir()) if runs.exists() else []
        self.assertEqual((2, None), self.project.run("frobnicate", "--task", "t1"))
        self.assertEqual((2, None), self.project.run("validate"))
        after = sorted(runs.iterdir()) if runs.exists() else []
        self.assertEqual(before, after)

    @verifies("scenario.operations.host-error")
    def test_a_raising_step_is_a_failed_result(self):
        status, envelope = self.project.run("test", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [error] = [
            item for item in envelope["host_evidence"] if item["kind"] == "host-error"
        ]
        self.assertEqual("raising_step", error["ref"])
        self.assertIn("traceback", error["detail"])
        self.assertTrue(
            (
                self.root / ".concorde/runs" / envelope["run_id"] / "traceback.txt"
            ).exists()
        )
        self.assertEqual("failed", self.run_status(envelope))

    @verifies("scenario.operations.cancelled")
    def test_a_cancelled_run_ends_its_worker(self):
        pid_file = self.project.base / "child.pid"

        def cancel():
            deadline = time.monotonic() + 20
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            time.sleep(0.2)
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=cancel, daemon=True).start()
        status, envelope = self.implement([{"spawn": str(pid_file), "sleep": 60}])
        self.assertEqual("failed", envelope["status"])
        self.assertIn("cancelled", {item["kind"] for item in envelope["host_evidence"]})
        self.assertEqual(envelope, self.saved(envelope))
        child = int(pid_file.read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and Path(f"/proc/{child}").exists():
            state = Path(f"/proc/{child}/stat")
            if state.exists() and state.read_text().split()[2] == "Z":
                break
            time.sleep(0.05)
        state = Path(f"/proc/{child}/stat")
        self.assertTrue(not state.exists() or state.read_text().split()[2] == "Z")

    @verifies("scenario.operations.inputs")
    def test_earlier_results_are_admitted_as_task_material(self):
        _, first = self.project.run("validate", "--task", "t1")
        status, envelope = self.project.run(
            "understand", "--task", "t1", "--input", first["run_id"]
        )
        self.assertEqual((0, [first["run_id"]]), (status, envelope["output"]["inputs"]))
        _, failed = self.project.run("test", "--task", "t1")
        _, refused = self.project.run(
            "understand", "--task", "t1", "--input", failed["run_id"]
        )
        self.assertEqual("failed", refused["status"])
        self.assertEqual("input_not_admissible", refused["host_evidence"][0]["ref"])

    def test_the_result_schema_is_the_contract(self):
        text = (REPOSITORY_ROOT / "specs/concorde/operations/contracts.md").read_text()
        fence = text.split("```concorde-contract\n", 1)[1].split("```", 1)[0]
        self.assertEqual(json.loads(fence)["schema"], RESULT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
