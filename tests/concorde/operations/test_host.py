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

from concorde.errors import ERROR_SCHEMA, LINK_SCHEMA, codes
from concorde.operations import catalog
from concorde.operations.host import RESULT_SCHEMA, UsageError
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
        self.assertIsNone(envelope["error"])
        self.assertEqual(envelope, self.saved(envelope))
        self.assertEqual("ok", self.run_status(envelope))

    @verifies("scenario.operations.progress-file")
    def test_the_progress_file_follows_the_run(self):
        status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        run = self.root / ".concorde/runs" / envelope["run_id"]
        progress = json.loads((run / "status.json").read_text())
        self.assertEqual(
            ("operation", "implement", "t1", "finished", "ok", envelope["summary"]),
            (
                progress["kind"],
                progress["operation"],
                progress["task"],
                progress["phase"],
                progress["status"],
                progress["summary"],
            ),
        )
        self.assertEqual(os.getpid(), progress["host_pid"])
        [worker] = envelope["worker_runs"]
        worker_progress = json.loads(
            (self.root / ".concorde/runs" / worker / "status.json").read_text()
        )
        self.assertEqual(progress["host_pid"], worker_progress["host_pid"])

    @verifies("scenario.operations.worker-blocked")
    def test_a_blocked_worker_escalates(self):
        status, envelope = self.implement(
            [
                {
                    "result": {
                        "status": "blocked",
                        "error": {
                            "code": "spec_gap",
                            "detail": "the Spec does not state the rounding rule",
                            "evidence": [],
                            "attempts": ["read specs/a/module.md"],
                            "unhandled": {
                                "reason": "decision",
                                "explanation": "the rounding rule is the Spec's to state",
                            },
                            "options": ["round per line", "round per order"],
                            "recommendation": "round per order",
                        },
                    }
                }
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual(["worker_blocked", "worker_blocked", "spec_gap"], codes(error))
        self.assertEqual(
            ["operation", "harness", "worker"],
            [
                error["level"],
                error["causes"][0]["level"],
                error["causes"][0]["causes"][0]["level"],
            ],
        )
        worker = error["causes"][0]["causes"][0]
        self.assertEqual("the Spec does not state the rounding rule", worker["detail"])
        self.assertEqual("round per order", worker["recommendation"])
        self.assertEqual("decision", worker["unhandled"]["reason"])
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertIn("round per line", error["options"])
        host_text = json.dumps(envelope["host_evidence"]) + envelope["summary"]
        self.assertNotIn("rounding rule", host_text)

    @verifies("scenario.operations.spec-error")
    def test_a_spec_tooling_error_keeps_its_reason_and_causes(self):
        from concorde.spec.errors import SpecError, system_cause

        refused = SpecError(
            "the implement grant would make src/shared.py writable, which module.b binds",
            "shared_file",
            "modules",
            causes=[system_cause(PermissionError(13, "denied", "src/shared.py"))],
        )
        with patch("concorde.spec.grants.grant", side_effect=refused):
            status, envelope = self.implement([{}])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual("grant_unavailable", error["code"])
        [spec] = error["causes"]
        self.assertEqual(("component", "shared_file"), (spec["level"], spec["code"]))
        self.assertIn("src/shared.py", spec["detail"])
        self.assertEqual(refused.reason, spec["unhandled"]["explanation"])
        self.assertEqual([refused.remediation], spec["options"])
        [system] = spec["causes"]
        self.assertEqual(
            ("system_error", "environment"),
            (system["code"], system["unhandled"]["reason"]),
        )
        self.assertIn("src/shared.py", system["detail"])

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
        error = envelope["error"]
        self.assertEqual(
            ["checks_failed", "checks_failed", "check_failed"], codes(error)
        )
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertEqual("exhausted", error["causes"][0]["unhandled"]["reason"])
        check = error["causes"][0]["causes"][0]
        self.assertEqual(("check", "check.a"), (check["level"], check["actor"]))
        self.assertIn("exit code 1", check["detail"])

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
        error = envelope["error"]
        self.assertEqual(["refused", "unknown_task"], codes(error))
        self.assertEqual("input", error["unhandled"]["reason"])
        self.assertIn("known tasks: t1", error["causes"][0]["detail"])
        store.begin_run(
            self.root, "t1", "r-other", "implement", ["module.a"], True, os.getpid()
        )
        before = store.load_task(self.root, "t1")
        status, envelope = self.project.run("validate", "--task", "t1")
        self.assertEqual("failed", envelope["status"])
        self.assertEqual("task_busy", envelope["host_evidence"][0]["ref"])
        self.assertEqual("decision", envelope["error"]["unhandled"]["reason"])
        self.assertIn("r-other", envelope["error"]["detail"])
        self.assertIsNone(envelope["output"])
        self.assertEqual(before["runs"], store.load_task(self.root, "t1")["runs"])

    @verifies("scenario.operations.bad-command")
    def test_a_malformed_command_line_writes_nothing(self):
        runs = self.root / ".concorde/runs"
        before = sorted(runs.iterdir()) if runs.exists() else []
        with self.assertRaisesRegex(UsageError, "unknown Operation 'frobnicate'"):
            self.project.run("frobnicate", "--task", "t1")
        with self.assertRaisesRegex(UsageError, "--task"):
            self.project.run("validate")
        after = sorted(runs.iterdir()) if runs.exists() else []
        self.assertEqual(before, after)

    @verifies("scenario.operations.host-error")
    def test_a_raising_step_is_a_failed_result(self):
        status, envelope = self.project.run("test", "--task", "t1")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [error] = [
            item for item in envelope["host_evidence"] if item["kind"] == "host-error"
        ]
        self.assertEqual("host step raising_step", error["ref"])
        self.assertIn("RuntimeError: boom", error["detail"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual(
            ("component", "RuntimeError: boom"), (cause["level"], cause["detail"])
        )
        trace = [item for item in cause["evidence"] if item["kind"] == "traceback"]
        self.assertTrue(Path(trace[0]["ref"]).is_file())
        self.assertIn("raising_step", Path(trace[0]["ref"]).read_text())
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
        self.assertIn("ended failed", refused["error"]["detail"])

    def test_the_result_schema_is_the_contract(self):
        text = (REPOSITORY_ROOT / "specs/concorde/operations/contracts.md").read_text()
        fence = text.split("```concorde-contract\n", 1)[1].split("```", 1)[0]
        self.assertEqual(json.loads(fence)["schema"], RESULT_SCHEMA)

    def test_the_error_link_is_the_framework_contract(self):
        text = (REPOSITORY_ROOT / "specs/concorde/contracts.md").read_text()
        fence = text.split("```concorde-contract\n", 1)[1].split("```", 1)[0]
        self.assertEqual(json.loads(fence)["schema"], ERROR_SCHEMA)
        self.assertEqual(RESULT_SCHEMA["$defs"]["error"], LINK_SCHEMA)


if __name__ == "__main__":
    unittest.main()
