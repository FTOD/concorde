"""Workflows: keyed steps, the workflow result, and the rendered scripts under stand-in clients."""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from concorde import errors
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from concorde.workflows import catalog
from concorde.workflows import step as steps
from concorde.workflows.report import RESULT_SCHEMA, report
from concorde.workflows.step import (
    REQUEST_SCHEMA,
    STEP_SCHEMA,
    run_step,
    step_key,
)
from tests.concorde.support.brownfield_project import BrownfieldProject
from tests.concorde.support.paths import REPOSITORY_ROOT

HARNESS = Path(__file__).with_name("run_script.mjs")
DEAD_PID = 2**22 + 12345


def contract(path: str, identity: str) -> dict:
    text = (REPOSITORY_ROOT / path).read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        body = json.loads(fence)
        if body["id"] == identity:
            return body["schema"]
    raise AssertionError(f"{identity} not in {path}")


def operation_link(
    operation: str, run_id: str, code: str, reason: str = "decision"
) -> dict:
    return errors.link(
        "operation",
        f"Operation {operation} {run_id} (task adopt)",
        code,
        f"{operation} stopped with {code}",
        reason=reason,
        explanation="a test stand-in",
    )


class Runs:
    """Saved Operation results written by hand, standing in for finished or dying hosts."""

    def __init__(self, primary: Path):
        self.primary = primary

    def make(
        self,
        operation: str,
        status: str | None = "ok",
        output: dict | None = None,
        error: dict | None = None,
        modules=("module.shop",),
        pid: int = DEAD_PID,
    ) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        run_id = f"r-{stamp}-{operation}-{secrets.token_hex(4)}"
        directory = self.primary / ".concorde/runs" / run_id
        directory.mkdir(parents=True)
        (directory / "status.json").write_text(json.dumps({"host_pid": pid}))
        if status is not None:
            if status != "ok" and error is None:
                error = operation_link(operation, run_id, f"{operation}_{status}")
            (directory / "result.json").write_text(
                json.dumps(
                    {
                        "operation": operation,
                        "task": "adopt",
                        "modules": list(modules),
                        "run_id": run_id,
                        "status": status,
                        "summary": f"{operation} ended {status}.",
                        "output": output,
                        "worker": None,
                        "worker_runs": [],
                        "host_evidence": [],
                        "error": error,
                        "started_at": "2026-09-25T10:00:00Z",
                        "finished_at": "2026-09-25T10:01:00Z",
                    }
                )
            )
        return run_id


SURVEY_OUTPUT = {
    "module": "module.shop",
    "summary": "two parts",
    "children": [
        {
            "id": "module.checkout",
            "title": "Checkout",
            "purpose": "p",
            "entries": ["src/checkout/"],
            "uses": [{"target": "module.inventory", "reason": "r"}],
        },
        {
            "id": "module.inventory",
            "title": "Inventory",
            "purpose": "p",
            "entries": ["src/inventory/"],
            "uses": [],
        },
    ],
    "remaining_entries": ["README.md"],
    "checks": [
        {
            "id": "check.checkout.tests",
            "module": "module.checkout",
            "argv": ["pytest"],
            "timeout_seconds": 60,
            "inputs": ["tests"],
            "reason": "found pytest",
        }
    ],
    "decisions": [
        {
            "id": "d.db-helper",
            "module": "module.shop",
            "question": "own Module?",
            "options": ["yes", "no"],
            "chosen": "no",
            "reason": "small",
            "decided_by": "worker",
        }
    ],
    "open_questions": [],
}
QUESTION = {
    "id": "q.retry",
    "module": "module.checkout",
    "subject": "retries",
    "observed": "declines retried",
    "evidence": ["src/checkout/payment.py"],
    "why_uncertain": "no reason given",
    "options": ["keep", "drop"],
    "recommendation": "ask",
}


def describe_output(module: str, questions=()) -> dict:
    return {
        "modules": [module],
        "summary": "s",
        "changed_documents": [],
        "created_documents": [],
        "removed_stubs": [],
        "promises": [],
        "decisions": [],
        "open_questions": list(questions),
        "deviations": [],
        "validation": {"new_errors": [], "preexisting_errors": 0},
    }


class StepTests(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)
        self.project.open_task()
        self.primary = self.project.root
        self.runs = Runs(self.primary)
        self.started: list[list[str]] = []

    def request(
        self, key="survey", argv=("survey", "--modules", "module.shop"), **changes
    ):
        value = {
            "task": "adopt",
            "workflow": "brownfield",
            "mode": "no-ask",
            "key": key,
            "argv": list(argv),
            "answers": None,
            "retry": False,
            "restart": None,
        }
        value.update(changes)
        return value

    def starter(self, status="ok", output=None, pid=DEAD_PID):
        def start(workflow, record, argv):
            self.started.append(list(argv))
            return {"run_id": self.runs.make(argv[0], status, output, pid=pid)}

        return patch.object(steps, "start_run", side_effect=start)

    def test_the_schemas_are_the_contracts(self):
        path = "specs/concorde/workflows/contracts.md"
        for identity, schema in (
            ("contract.workflows.step", STEP_SCHEMA),
            ("contract.workflows.step-request", REQUEST_SCHEMA),
            ("contract.workflows.result", RESULT_SCHEMA),
        ):
            with self.subTest(identity=identity):
                self.assertEqual(contract(path, identity), schema)

    @verifies("scenario.workflows.step-starts")
    def test_a_step_starts_and_records_a_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            status, outcome = run_step(self.primary, self.request())
        self.assertEqual(0, status)
        self.assertEqual(
            [["survey", "--task", "adopt", "--modules", "module.shop"]], self.started
        )
        self.assertEqual(
            ("finished", "ok", 1),
            (outcome["state"], outcome["status"], outcome["decision_points"]),
        )
        workflow = store.load_task(self.primary, "adopt")["workflow"]
        self.assertEqual("brownfield", workflow["name"])
        self.assertEqual(["survey"], [s["key"] for s in workflow["steps"]])
        self.assertEqual(outcome["run_id"], workflow["steps"][0]["run_id"])
        validate(outcome, STEP_SCHEMA)

    @verifies("scenario.workflows.step-starts")
    def test_a_real_step_runs_detached_with_the_worktrees_concorde(self):
        _status, outcome = run_step(
            self.primary, self.request("validate", ("validate",)), wait=120
        )
        self.assertIn(outcome["state"], ("finished",), outcome)
        self.assertEqual("validate", outcome["operation"])
        self.assertIsNotNone(outcome["status"])
        runs = {run["run_id"] for run in store.load_task(self.primary, "adopt")["runs"]}
        self.assertIn(outcome["run_id"], runs)

    @verifies("scenario.workflows.step-waits")
    def test_a_long_run_is_awaited_by_repeated_calls(self):
        with self.starter(status=None, pid=os.getpid()):
            before = time.monotonic()
            status, outcome = run_step(self.primary, self.request(), wait=0.3)
            self.assertLess(time.monotonic() - before, 5)
            self.assertEqual((3, "running"), (status, outcome["state"]))
            status, again = run_step(self.primary, self.request(), wait=0.1)
        self.assertEqual(1, len(self.started))
        self.assertEqual(outcome["run_id"], again["run_id"])

    @verifies("scenario.workflows.step-cached")
    def test_a_finished_step_returns_at_once_and_retry_restarts_a_failed_one(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.primary, self.request())
            run_step(self.primary, self.request())
        self.assertEqual(1, len(self.started))
        with self.starter(status="failed"):
            run_step(self.primary, self.request("validate", ("validate",)))
            _, failed = run_step(self.primary, self.request("validate", ("validate",)))
        self.assertEqual("failed", failed["status"])
        self.assertEqual(2, len(self.started))
        with self.starter(status="ok"):
            _status, retried = run_step(
                self.primary, self.request("validate", ("validate",), retry=True)
            )
        self.assertEqual(3, len(self.started))
        self.assertNotEqual(failed["run_id"], retried["run_id"])

    @verifies("scenario.workflows.restarted")
    def test_a_restart_generation_reruns_an_ok_step_once(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.primary, self.request())
        with self.starter(output={"created": []}):
            _, first = run_step(self.primary, self.request("scaffold", ("scaffold",)))
            run_step(self.primary, self.request("validate", ("validate",)))
            _, again = run_step(
                self.primary, self.request("scaffold", ("scaffold",), restart="2")
            )
        self.assertEqual("scaffold#2", again["key"])
        self.assertNotEqual(first["run_id"], again["run_id"])
        record = store.load_task(self.primary, "adopt")
        self.assertEqual(
            ["survey", "scaffold#2"], [s["key"] for s in store.current_steps(record)]
        )
        started = len(self.started)
        with self.starter(output={"created": []}):
            _, same = run_step(
                self.primary, self.request("scaffold", ("scaffold",), restart="2")
            )
        self.assertEqual(
            (again["run_id"], started), (same["run_id"], len(self.started))
        )

    @verifies("scenario.workflows.step-refused")
    def test_a_step_that_does_not_belong_is_rejected(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.primary, self.request())
            for request, code in (
                (self.request(workflow="other"), "workflow_conflict"),
                (self.request(argv=("validate",)), "step_conflict"),
            ):
                with self.subTest(code=code):
                    status, value = run_step(self.primary, request)
                    self.assertEqual((1, "refused"), (status, value["state"]))
                    self.assertIsNone(value["run_id"])
                    link = value["error"]
                    self.assertEqual(
                        ("workflow", "step_rejected"), (link["level"], link["code"])
                    )
                    self.assertEqual(code, link["causes"][0]["code"])
        self.assertEqual(1, len(self.started))
        self.assertEqual(
            1, len(store.load_task(self.primary, "adopt")["workflow"]["steps"])
        )

    @verifies("scenario.workflows.refused-step")
    def test_a_step_whose_run_cannot_start_is_recorded_without_a_run(self):
        status, outcome = run_step(
            self.primary, self.request("validate", ("validate", "--bogus"))
        )
        self.assertEqual((1, "refused"), (status, outcome["state"]))
        self.assertIsNone(outcome["run_id"])
        self.assertEqual("step_refused", outcome["error"]["code"])
        self.assertIn("--bogus", json.dumps(outcome["error"]))
        [recorded] = store.load_task(self.primary, "adopt")["workflow"]["steps"]
        self.assertIsNone(recorded["run_id"])
        self.assertEqual("step_refused", recorded["error"]["code"])
        result = report(self.primary, "adopt")
        self.assertEqual("failed", result["status"])
        self.assertEqual("step_refused", result["problems"][0]["error"]["code"])

    @verifies("scenario.workflows.lost")
    def test_a_step_whose_host_died_is_lost(self):
        with self.starter(status=None, pid=DEAD_PID):
            status, outcome = run_step(
                self.primary, self.request("describe:module.shop", ("code_to_spec",))
            )
        self.assertEqual((1, "lost"), (status, outcome["state"]))
        self.assertEqual("step_lost", outcome["error"]["code"])
        result = report(self.primary, "adopt", ["describe:module.shop"])
        self.assertEqual("failed", result["status"])
        self.assertEqual("lost", result["problems"][0]["status"])
        # A key reported lost that has a finished run keeps that run's outcome.
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.primary, self.request())
        result = report(self.primary, "adopt", ["survey"])
        self.assertEqual(
            "ok", {s["key"]: s["status"] for s in result["steps"]}["survey"]
        )

    @verifies("scenario.workflows.superseded")
    def test_a_retried_step_supersedes_later_steps(self):
        with self.starter(output=SURVEY_OUTPUT):
            run_step(self.primary, self.request())
        with self.starter(status="failed"):
            run_step(
                self.primary,
                self.request("describe:module.checkout", ("code_to_spec",)),
            )
        with self.starter(status="ok", output={"ready": True}):
            run_step(self.primary, self.request("validate", ("validate",)))
            run_step(self.primary, self.request("delivery", ("delivery",)))
        with self.starter(status="ok", output=describe_output("module.checkout")):
            run_step(
                self.primary,
                self.request("describe:module.checkout", ("code_to_spec",), retry=True),
            )
        record = store.load_task(self.primary, "adopt")
        current = [s["key"] for s in store.current_steps(record)]
        self.assertEqual(["survey", "describe:module.checkout"], current)
        before = len(self.started)
        with self.starter(status="ok", output={"ready": True}):
            run_step(self.primary, self.request("validate", ("validate",)))
        self.assertEqual(before + 1, len(self.started))
        result = report(self.primary, "adopt")
        self.assertEqual(
            ["describe:module.checkout", "validate", "delivery"],
            [s["key"] for s in result["superseded"]],
        )

    @verifies("scenario.workflows.interactive-resume")
    def test_answers_make_a_new_step_that_admits_the_asking_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            _, first = run_step(self.primary, self.request(mode="interactive"))
        answers = [{"id": "d.db-helper", "question": "own Module?", "answer": "yes"}]
        followed = json.loads(json.dumps(SURVEY_OUTPUT))
        followed["decisions"][0].update(chosen="yes", decided_by="developer")
        with self.starter(output=followed):
            _, second = run_step(
                self.primary, self.request(mode="interactive", answers=answers)
            )
        self.assertEqual(step_key("survey", answers), second["key"])
        argv = self.started[-1]
        self.assertEqual(first["run_id"], argv[argv.index("--input") + 1])
        answers_file = Path(argv[argv.index("--answers") + 1])
        self.assertEqual({"answers": answers}, json.loads(answers_file.read_text()))
        self.assertEqual(0, second["decision_points"])
        # The same answers find the same step again.
        with self.starter(output=followed):
            _, again = run_step(
                self.primary, self.request(mode="interactive", answers=answers)
            )
        self.assertEqual(second["run_id"], again["run_id"])

    @verifies("scenario.workflows.step-waits")
    def test_a_step_waits_while_another_run_of_the_task_runs(self):
        store.begin_run(
            self.primary,
            "adopt",
            "r-other",
            "implement",
            ["module.shop"],
            True,
            os.getpid(),
        )
        with self.starter(output=SURVEY_OUTPUT):
            status, value = run_step(self.primary, self.request(), wait=0.3)
            self.assertEqual(
                (3, "running", None), (status, value["state"], value["run_id"])
            )
            self.assertEqual([], self.started)
            store.finish_run(self.primary, "adopt", "r-other", "ok")
            status, value = run_step(self.primary, self.request())
        self.assertEqual((0, "finished"), (status, value["state"]))
        self.assertEqual(1, len(self.started))

    def test_answered_points_are_no_longer_decision_points(self):
        answers = [{"id": "q.retry", "question": "retries", "answer": "keep"}]
        with self.starter(output=describe_output("module.checkout", [QUESTION])):
            _, value = run_step(
                self.primary,
                self.request(
                    "describe:module.checkout",
                    ("code_to_spec",),
                    mode="interactive",
                    answers=answers,
                ),
            )
        self.assertEqual(0, value["decision_points"])
        self.assertEqual([], report(self.primary, "adopt")["pending"])

    @verifies("scenario.workflows.interactive-resume")
    def test_a_retried_answered_step_still_admits_the_asking_run(self):
        with self.starter(output=SURVEY_OUTPUT):
            _, first = run_step(self.primary, self.request(mode="interactive"))
        answers = [{"id": "d.db-helper", "question": "own Module?", "answer": "yes"}]
        with self.starter(status="failed"):
            run_step(self.primary, self.request(mode="interactive", answers=answers))
        with self.starter(output=SURVEY_OUTPUT):
            run_step(
                self.primary,
                self.request(mode="interactive", answers=answers, retry=True),
            )
        argv = self.started[-1]
        self.assertEqual(first["run_id"], argv[argv.index("--input") + 1])

    @verifies("scenario.workflows.lost")
    def test_a_lost_step_carries_its_host_output(self):
        with self.starter(status=None, pid=DEAD_PID):
            _, value = run_step(
                self.primary, self.request("validate", ("validate",)), wait=0
            )
        (self.primary / ".concorde/runs" / value["run_id"] / "host.out").write_text(
            "Traceback: KeyError: 'modules'\n"
        )
        _, value = run_step(self.primary, self.request("validate", ("validate",)))
        self.assertEqual("lost", value["state"])
        self.assertIn("KeyError", json.dumps(value["error"]["evidence"]))
        self.assertEqual("host_ended", value["error"]["causes"][0]["code"])
        self.assertIn(
            "KeyError",
            report(self.primary, "adopt")["problems"][0]["error"]["causes"][0][
                "detail"
            ],
        )

    def test_a_started_run_that_cannot_be_recorded_is_named(self):
        with (
            self.starter(output=SURVEY_OUTPUT),
            patch.object(
                store,
                "record_workflow_step",
                side_effect=store.TaskError("record_conflict", "busy"),
            ),
        ):
            status, value = run_step(self.primary, self.request())
        self.assertEqual((1, "refused"), (status, value["state"]))
        self.assertEqual("step_unrecorded", value["error"]["code"])
        self.assertIsNotNone(value["run_id"])
        self.assertIn(value["run_id"], value["error"]["detail"])
        self.assertEqual("record_conflict", value["error"]["causes"][0]["code"])


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)
        self.project.open_task()
        self.primary = self.project.root
        self.runs = Runs(self.primary)

    def record(
        self, key, operation, status="ok", output=None, mode="no-ask", error=None
    ):
        run_id = self.runs.make(operation, status, output, error=error)
        store.record_workflow_step(
            self.primary, "adopt", "brownfield", key, operation, run_id, mode, None
        )
        return run_id

    def complete(self, describe_status="ok"):
        self.record("survey", "survey", output=SURVEY_OUTPUT)
        self.record("scaffold", "scaffold", output={"created": []})
        self.record(
            "describe:module.inventory",
            "code_to_spec",
            describe_status,
            describe_output("module.inventory") if describe_status == "ok" else None,
        )
        self.record(
            "describe:module.checkout",
            "code_to_spec",
            output=describe_output("module.checkout", [QUESTION]),
        )
        self.record(
            "spec_review",
            "spec_review",
            output={
                "verdict": "changes_required",
                "modules": [{"module": "module.checkout", "findings": [1, 2]}],
            },
        )
        self.record("validate", "validate", output={"ready": True})
        self.record("delivery", "delivery", output={})

    @verifies("scenario.workflows.no-ask-complete")
    @verifies("scenario.workflows.reviews-reported")
    @verifies("scenario.workflows.report-ignores-relay")
    def test_a_no_ask_run_reports_everything(self):
        self.complete(describe_status="blocked")
        result = report(self.primary, "adopt")
        validate(result, RESULT_SCHEMA)
        self.assertEqual("ok", result["status"])
        self.assertIsNone(result["error"])
        self.assertEqual(["d.db-helper"], [d["id"] for d in result["decisions"]])
        self.assertEqual("small", result["decisions"][0]["reason"])
        self.assertEqual(
            [QUESTION["observed"]], [q["observed"] for q in result["open_questions"]]
        )
        self.assertEqual("changes_required", result["reviews"][0]["verdict"])
        self.assertEqual(
            ["check.checkout.tests"], [c["id"] for c in result["proposed_checks"]]
        )
        [problem] = result["problems"]
        self.assertEqual(
            ("describe:module.inventory", "blocked"),
            (problem["step"], problem["status"]),
        )
        self.assertEqual("code_to_spec_blocked", problem["error"]["code"])
        log = store.decision_log_path(self.primary, "adopt").read_text()
        self.assertIn("Workflow brownfield report: ok", log)
        self.assertIn("q.retry", log)
        self.assertIn("check.checkout.tests", log)
        saved = json.loads(
            (self.primary / ".concorde/tasks/adopt.workflow.json").read_text()
        )
        self.assertEqual(result["summary"], saved["summary"])
        self.assertEqual(
            "ok",
            store.load_task(self.primary, "adopt")["workflow"]["reports"][-1]["status"],
        )

    @verifies("scenario.workflows.interactive-pause")
    def test_an_interactive_run_ends_at_survey_decisions(self):
        self.record("survey", "survey", output=SURVEY_OUTPUT, mode="interactive")
        result = report(self.primary, "adopt")
        self.assertEqual("awaiting_decision", result["status"])
        self.assertEqual(["d.db-helper"], [p["id"] for p in result["pending"]])
        self.assertEqual(["yes", "no"], result["pending"][0]["options"])
        self.assertEqual(
            ("workflow", "awaiting_decision", "decision"),
            (
                result["error"]["level"],
                result["error"]["code"],
                result["error"]["unhandled"]["reason"],
            ),
        )

    @verifies("scenario.workflows.failed-chain")
    def test_a_stopping_step_keeps_its_chain_under_the_workflow_link(self):
        self.record("survey", "survey", output=SURVEY_OUTPUT)
        cause = operation_link("scaffold", "r-x", "stale_proposal")
        cause["causes"] = [
            errors.link(
                "component",
                "Spec core",
                "missing",
                "gone",
                reason="input",
                explanation="x",
            )
        ]
        self.record("scaffold", "scaffold", "blocked", error=cause)
        result = report(self.primary, "adopt")
        self.assertEqual("blocked", result["status"])
        error = result["error"]
        self.assertEqual(("workflow", "step_blocked"), (error["level"], error["code"]))
        self.assertEqual([cause], error["causes"])

    def test_a_report_during_a_running_step(self):
        run_id = self.runs.make("survey", None, pid=os.getpid())
        store.record_workflow_step(
            self.primary,
            "adopt",
            "brownfield",
            "survey",
            "survey",
            run_id,
            "no-ask",
            None,
        )
        result = report(self.primary, "adopt")
        self.assertEqual("running", result["status"])
        self.assertEqual("step_running", result["error"]["code"])


class ScriptTests(unittest.TestCase):
    """The rendered scripts, run under stand-ins for Claude Code's and pi's workflow runtimes."""

    def setUp(self):
        self.directory = Path(self.id().replace(".", "_"))

    def run_script(self, client, args, outcomes, report_status="ok"):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "script.js"
            script.write_text(catalog.render("brownfield", client))
            completed = subprocess.run(
                ["node", str(HARNESS)],
                input=json.dumps(
                    {
                        "script": str(script),
                        "client": client,
                        "args": args,
                        "outcomes": outcomes,
                        "report": {"status": report_status, "summary": "s"},
                    }
                ),
                capture_output=True,
                text=True,
                check=True,
            )
        return json.loads(completed.stdout)

    def outcome(self, key, operation, status="ok", points=0, created=(), ready=None):
        return {
            "workflow": "brownfield",
            "task": "adopt",
            "key": key,
            "operation": operation,
            "run_id": "r-20260925T100000-x-00000000",
            "state": "finished",
            "status": status,
            "summary": "s",
            "result_path": "p",
            "decision_points": points,
            "created_modules": list(created),
            "ready": ready,
            "error": None,
        }

    def full(self, points=0, describe_status="ok"):
        created = [
            {"id": "module.checkout", "uses": ["module.inventory"]},
            {"id": "module.inventory", "uses": []},
        ]
        return {
            "survey": self.outcome("survey", "survey", points=points),
            "scaffold": self.outcome("scaffold", "scaffold", created=created),
            "describe:module.inventory": self.outcome(
                "describe:module.inventory", "code_to_spec", describe_status
            ),
            "describe:module.checkout": self.outcome(
                "describe:module.checkout", "code_to_spec"
            ),
            "describe:module.shop": self.outcome(
                "describe:module.shop", "code_to_spec"
            ),
            "spec_review": self.outcome("spec_review", "spec_review"),
            "validate": self.outcome("validate", "validate", ready=True),
            "delivery": self.outcome("delivery", "delivery"),
        }

    ARGS: ClassVar[dict] = {"task": "adopt", "module": "module.shop", "mode": "no-ask"}

    @verifies("scenario.workflows.no-ask-complete")
    def test_both_clients_run_the_whole_procedure_providers_first(self):
        for client in ("claude", "pi"):
            with self.subTest(client=client):
                run = self.run_script(
                    client, self.ARGS, self.full(points=2, describe_status="blocked")
                )
                self.assertIsNone(run["error"])
                self.assertEqual(
                    [
                        "survey",
                        "scaffold",
                        "describe:module.inventory",
                        "describe:module.checkout",
                        "describe:module.shop",
                        "spec_review",
                        "validate",
                        "delivery",
                        "report",
                    ],
                    [call["key"] for call in run["calls"]],
                )
                review = next(c for c in run["calls"] if c["key"] == "spec_review")
                self.assertEqual(
                    [
                        "spec_review",
                        "--modules",
                        "module.inventory,module.checkout,module.shop",
                    ],
                    review["request"]["argv"],
                )
                self.assertEqual("ok", run["result"]["reported"]["status"])
        claude = self.run_script("claude", self.ARGS, self.full())
        self.assertEqual("concorde-brownfield", claude["meta"]["name"])
        self.assertEqual("haiku", claude["calls"][0]["options"]["model"])
        pi = self.run_script("pi", self.ARGS, self.full())
        self.assertEqual(
            {"concorde-step", "concorde-report"}, {c["agent"] for c in pi["calls"]}
        )

    @verifies("scenario.workflows.interactive-pause")
    def test_an_interactive_run_stops_after_the_survey(self):
        run = self.run_script(
            "claude", {**self.ARGS, "mode": "interactive"}, self.full(points=1)
        )
        self.assertEqual(["survey", "report"], [c["key"] for c in run["calls"]])

    @verifies("scenario.workflows.interactive-resume")
    def test_answers_and_retries_reach_their_steps(self):
        answers = {"survey": [{"id": "d.db-helper", "question": "q", "answer": "yes"}]}
        run = self.run_script(
            "pi",
            {
                **self.ARGS,
                "mode": "interactive",
                "answers": answers,
                "retry": ["validate"],
            },
            self.full(),
        )
        requests = {
            c["key"]: c["request"] for c in run["calls"] if c["key"] != "report"
        }
        self.assertEqual(answers["survey"], requests["survey"]["answers"])
        self.assertIsNone(requests["scaffold"]["answers"])
        self.assertTrue(requests["validate"]["retry"])
        self.assertFalse(requests["survey"]["retry"])

    def test_restart_labels_reach_their_steps(self):
        run = self.run_script(
            "claude", {**self.ARGS, "restart": {"scaffold": "2"}}, self.full()
        )
        requests = {
            c["key"]: c["request"] for c in run["calls"] if c["key"] != "report"
        }
        self.assertEqual("2", requests["scaffold"]["restart"])
        self.assertIsNone(requests["survey"]["restart"])

    def test_interactive_stops_at_a_failed_description_and_no_ask_goes_on(self):
        outcomes = self.full(describe_status="failed")
        interactive = self.run_script(
            "claude", {**self.ARGS, "mode": "interactive"}, outcomes
        )
        self.assertEqual("report", interactive["calls"][-1]["key"])
        self.assertEqual("describe:module.inventory", interactive["calls"][-2]["key"])
        no_ask = self.run_script("claude", self.ARGS, outcomes)
        self.assertIn("delivery", [c["key"] for c in no_ask["calls"]])

    @verifies("scenario.workflows.lost")
    def test_a_step_agent_that_returned_nothing_is_reported_lost(self):
        outcomes = self.full()
        outcomes["scaffold"] = None
        for client in ("claude", "pi"):
            with self.subTest(client=client):
                run = self.run_script(client, self.ARGS, outcomes)
                self.assertEqual(
                    ["survey", "scaffold", "report"], [c["key"] for c in run["calls"]]
                )
                self.assertEqual("scaffold", run["calls"][-1]["lost"])

    def test_a_rejected_step_travels_with_the_report(self):
        outcomes = self.full()
        rejected = self.outcome("scaffold", "scaffold")
        rejected.update(
            state="refused",
            status=None,
            run_id=None,
            error={"code": "step_rejected", "level": "workflow"},
        )
        outcomes["scaffold"] = rejected
        for client in ("claude", "pi"):
            with self.subTest(client=client):
                run = self.run_script(client, self.ARGS, outcomes)
                self.assertEqual(
                    ["survey", "scaffold", "report"], [c["key"] for c in run["calls"]]
                )
                self.assertEqual("scaffold", run["calls"][-1]["lost"])
                self.assertEqual(
                    "step_rejected", run["result"]["rejected"]["error"]["code"]
                )

    def test_a_step_still_running_ends_a_no_ask_run(self):
        outcomes = self.full()
        outcomes["describe:module.inventory"]["state"] = "running"
        run = self.run_script("claude", self.ARGS, outcomes)
        self.assertEqual("report", run["calls"][-1]["key"])
        self.assertEqual("describe:module.inventory", run["calls"][-2]["key"])

    def test_an_unready_validation_ends_the_run_before_delivery(self):
        outcomes = self.full()
        outcomes["validate"] = self.outcome(
            "validate", "validate", "blocked", ready=False
        )
        run = self.run_script("claude", self.ARGS, outcomes)
        self.assertNotIn("delivery", [c["key"] for c in run["calls"]])


if __name__ == "__main__":
    unittest.main()
