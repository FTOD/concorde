"""The Operation host: ``concorde run`` with test providers standing in for real ones."""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.errors import ERROR_SCHEMA, LINK_SCHEMA, codes
from concorde.harness import models, pi_backend
from concorde.operations import catalog
from concorde.operations.host import RESULT_SCHEMA, UsageError
from concorde.operations.provider import Continue, Provider, evidence
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from tests.concorde.harness.workers.test_pi import FAKE as FAKE_PI
from tests.concorde.harness.workers.test_pi import fake_which
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


def reading_step(ctx):
    return ctx.run_worker(ctx.arguments.goal, task_type="understand", rounds=0)


def writing_step(ctx):
    return ctx.run_worker(ctx.arguments.goal, task_type="implement", rounds=0)


READER = Provider(
    "spec_review",
    "review-spec",
    False,
    (reading_step,),
    None,
    goal_arguments,
    task_scope="optional",
)
WRITER = Provider(
    "code_review",
    "review-code",
    False,
    (writing_step,),
    None,
    goal_arguments,
    task_scope="optional",
)


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
                "spec_review": f"{__name__}:READER",
                "code_review": f"{__name__}:WRITER",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def implement(self, steps, *extra, client="claude"):
        return self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(steps),
            *extra,
            client=client,
        )

    def worker_record(self, envelope) -> dict:
        [worker] = envelope["worker_runs"]
        return json.loads(
            (self.root / ".concorde/runs" / worker / "record.json").read_text()
        )

    def launched(self, envelope) -> list[str]:
        """The argument list the fake claude received in the first round."""
        work = Path(self.worker_record(envelope)["run_directory"]) / "work"
        return json.loads((work / "fake-round-1.json").read_text())["argv"]

    @verifies("scenario.operations.worker-model")
    def test_a_worker_runs_with_the_task_worktrees_model(self):
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "claude": {
                        "default": {"model": "sonnet", "reasoning": "medium"},
                        "operations": {"implement": {"model": "opus"}},
                    },
                }
            )
        )
        status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        argv = self.launched(envelope)
        self.assertEqual("opus", argv[argv.index("--model") + 1])
        self.assertEqual("medium", argv[argv.index("--effort") + 1])
        record = self.worker_record(envelope)
        self.assertEqual(
            ("claude", "opus", "medium"),
            (record["backend"], record["model"], record["reasoning"]),
        )
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("claude", shown["ref"])
        self.assertIn("model opus, reasoning medium", shown["detail"])
        (self.root / models.CONFIG).write_text(
            json.dumps({"schema_version": 2, "claude": {"default": {"model": "haiku"}}})
        )
        status, envelope = self.implement([{}])
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        argv = self.launched(envelope)
        self.assertEqual("opus", argv[argv.index("--model") + 1])

    def fake_pi(self) -> dict:
        """A fake ``pi``, sandbox-runtime and pi configuration, as the variables naming them."""
        base = self.project.base
        pi = base / "pi"
        pi.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE_PI}" "$@"\n')
        pi.chmod(0o755)
        runtime = base / "sandbox-runtime"
        (runtime / "dist").mkdir(parents=True)
        (runtime / "dist/index.js").write_text("export {};\n")
        agent = base / "pi-agent"
        agent.mkdir()
        (agent / "auth.json").write_text('{"local": {"key": "k"}}')
        (agent / "models.json").write_text('{"providers": {}}')
        which = patch.object(pi_backend, "which", side_effect=fake_which)
        which.start()
        self.addCleanup(which.stop)
        return {
            "CONCORDE_PI": str(pi),
            "CONCORDE_SANDBOX_RUNTIME": str(runtime),
            "PI_CODING_AGENT_DIR": str(agent),
        }

    @verifies("scenario.operations.worker-backend-configured")
    def test_a_claude_code_main_session_runs_a_pi_worker(self):
        environ = self.fake_pi()
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "backend": {"operations": {"implement": {"default": "pi"}}},
                    "pi": {"operations": {"implement": {"model": "local/fast"}}},
                }
            )
        )
        status, envelope = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            client="claude",
            environ=environ,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.worker_record(envelope)
        self.assertEqual(
            ("pi", "backend.operations.implement.default", "local/fast"),
            (record["backend"], record["backend_source"], record["model"]),
        )
        argv = self.launched(envelope)
        self.assertEqual("local/fast", argv[argv.index("--model") + 1])
        self.assertIn("--no-extensions", argv)
        [shown] = [
            item for item in envelope["host_evidence"] if item["kind"] == "worker-model"
        ]
        self.assertEqual("pi", shown["ref"])
        self.assertIn("backend.operations.implement.default", shown["detail"])
        status, envelope = self.project.run(
            "spec_review",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            client="claude",
            environ=environ,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        record = self.worker_record(envelope)
        self.assertEqual(
            ("claude", "CONCORDE_CLIENT=claude"),
            (record["backend"], record["backend_source"]),
        )

    @verifies("scenario.operations.no-task")
    def test_a_run_without_a_task_works_on_its_own_worktree(self):
        before = store.load_task(self.root, "t1")
        status, envelope = self.project.run(
            "spec_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["task"])
        self.assertEqual(["module.a"], envelope["modules"])
        record = self.worker_record(envelope)
        self.assertEqual(str(self.root), record["worktree"])
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertTrue(
            (
                self.root / ".concorde/runs" / envelope["run_id"] / "result.json"
            ).is_file()
        )
        validate(envelope, RESULT_SCHEMA)
        status, envelope = self.project.run(
            "spec_review", "--modules", "module.a", "--input", envelope["run_id"]
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        with self.assertRaises(UsageError):
            self.project.run("implement", "--goal", "x")

    @verifies("scenario.operations.no-task-primary-only")
    def test_a_run_without_a_task_is_refused_in_a_task_worktree(self):
        before = store.load_task(self.root, "t1")
        status, envelope = self.project.run(
            "spec_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
            cwd=self.worktree,
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        error = envelope["error"]
        self.assertEqual("task_worktree_without_task", error["code"])
        self.assertIn("the worktree of task t1", error["detail"])
        self.assertEqual("run it again with --task t1", error["recommendation"])
        self.assertTrue(
            (
                self.root / ".concorde/runs" / envelope["run_id"] / "result.json"
            ).is_file()
        )
        self.assertEqual(before, store.load_task(self.root, "t1"))
        validate(error, ERROR_SCHEMA)

    @verifies("scenario.operations.no-task-read-only")
    def test_a_run_without_a_task_launches_no_writing_worker(self):
        status, envelope = self.project.run(
            "code_review",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{}]),
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("project_scope_write", envelope["error"]["code"])
        self.assertIn("no task", envelope["error"]["actor"])
        status, task_run = self.implement([{}])
        self.assertEqual(0, status, task_run)
        status, envelope = self.project.run(
            "spec_review", "--modules", "module.a", "--input", task_run["run_id"]
        )
        self.assertEqual(
            (1, "input_not_admissible"), (status, envelope["host_evidence"][-1]["ref"])
        )

    @verifies("scenario.operations.worker-model-unavailable")
    def test_a_run_without_a_main_session_program_fails_before_launch(self):
        status, envelope = self.implement([{}], client=None)
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        error = envelope["error"]
        self.assertEqual("worker_model_unavailable", error["code"])
        [cause] = error["causes"]
        self.assertEqual(
            ("component", "client_unknown"), (cause["level"], cause["code"])
        )
        self.assertIn("CLAUDECODE", cause["detail"])
        validate(error, ERROR_SCHEMA)
        (self.worktree / models.CONFIG).write_text("{broken")
        status, envelope = self.implement([{}])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        [cause] = envelope["error"]["causes"]
        self.assertEqual("config_invalid", cause["code"])
        self.assertIn(str(self.worktree / models.CONFIG), cause["detail"])
        (self.worktree / models.CONFIG).write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "backend": {"operations": {"implement": {"default": "pi"}}},
                }
            )
        )
        status, envelope = self.project.run(
            "implement",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{}]),
            environ={"CONCORDE_PI": str(self.project.base / "nowhere")},
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("worker_model_unavailable", envelope["error"]["code"])
        [cause] = envelope["error"]["causes"]
        self.assertEqual("backend_missing", cause["code"])
        self.assertEqual("environment", cause["unhandled"]["reason"])
        self.assertIn("backend.operations.implement.default", cause["detail"])
        self.assertIn("CONCORDE_PI", cause["detail"])
        validate(envelope["error"], ERROR_SCHEMA)

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

    @verifies("scenario.operations.detached")
    def test_a_detached_run_is_announced_and_finishes_on_its_own(self):
        from concorde.operations.host import detach

        status, announced = detach(
            ["validate", "--task", "t1", "--detach"], cwd=self.root
        )
        self.assertEqual(0, status, announced)
        self.assertTrue(Path(announced["progress"]).is_file())
        result = Path(announced["result"])
        deadline = time.monotonic() + 120
        while not result.is_file() and time.monotonic() < deadline:
            time.sleep(0.1)
        envelope = json.loads(result.read_text())
        validate(envelope, RESULT_SCHEMA)
        self.assertEqual(announced["run_id"], envelope["run_id"])
        self.assertEqual("t1", envelope["task"])
        runs = {run["run_id"]: run for run in store.load_task(self.root, "t1")["runs"]}
        self.assertEqual(envelope["status"], runs[announced["run_id"]]["status"])
        # A task already running an Operation still gets its refusal as the result.
        store.begin_run(
            self.root, "t1", "r-other", "implement", ["module.a"], True, os.getpid()
        )
        status, announced = detach(["validate", "--task", "t1"], cwd=self.root)
        self.assertEqual(0, status, announced)
        result = Path(announced["result"])
        deadline = time.monotonic() + 120
        while not result.is_file() and time.monotonic() < deadline:
            time.sleep(0.1)
        refused = json.loads(result.read_text())
        self.assertEqual("failed", refused["status"])
        self.assertEqual("task_busy", refused["host_evidence"][0]["ref"])
        with self.assertRaises(UsageError):
            detach(["frobnicate", "--task", "t1", "--detach"], cwd=self.root)

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
