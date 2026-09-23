"""The native driver's Workflow services, driven through the Host-step entry points.

A probe workflow hook stands in for a provider: the Spec review capability's declaration names it
as its native entry, so admission, dispatch and the driver run unchanged. pi-subagents' launch
binding and ``status.json`` are written synthetically; no Pi process or model runs.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import native_driver
from concorde.harness.execution_error import failure
from concorde.harness.native_driver import (
    WorkflowPlan,
    command_text,
    workflow_result,
    workflow_step,
    workflow_stop,
)
from concorde.operations.catalog import CATALOG
from concorde.operations.dispatch import services
from concorde.spec.verification import verifies
from tests.concorde.harness.native_call_fixture import NativeCallFixture, codes
from tests.concorde.support.spec_project import PACKAGE

HOST = "pi/native-review-host.mjs"
SCRIPT = "tests/concorde/harness/fixtures/probe-workflow.mjs"


class ProbeWorkflow:
    """A workflow hook that issues one assessor slot and answers two Host steps."""

    def __init__(self):
        self.steps: list[str] = []
        self.failures: list[str] = []
        self.failure_receipt: dict | None = None

    def prepare(self, run, driver):
        call = driver.issue_slot(
            "assess",
            "context_assessor",
            {"target_id": run.target.id, "task": run.task["task"]},
            operation="concorde-context-solve",
        )
        return WorkflowPlan(
            script=SCRIPT,
            host=HOST,
            steps=("bind", "finish", "finalize"),
            expansion={"assess": call},
        )

    def step(self, run, driver, name):
        self.steps.append(name)
        if name == "bind":
            driver.check("assess")
            return {"state": "ready"}
        if name == "finalize":
            driver.coverage(["assess"])
            driver.admit("assess")
            driver.accept("assess")
            return {"state": "finished", "accepted": True}
        driver.receipt(
            {
                "state": "accepted",
                "accepted": True,
                "output": {"answer": "Workflow finished"},
            }
        )
        return {"state": "finished", "accepted": True}

    def on_failure(self, run, driver, native_state):
        self.failures.append(native_state)
        return self.failure_receipt


PROBE = ProbeWorkflow()


class WorkflowTests(NativeCallFixture, unittest.TestCase):
    operation = "concorde-spec-review"

    def setUp(self):
        super().setUp()
        PROBE.__init__()
        entry = patch.dict(
            CATALOG[self.operation].declaration,
            {"entry_point": "tests.concorde.harness.test_native_workflow:PROBE"},
        )
        entry.start()
        self.addCleanup(entry.stop)
        self.context = {"services": services(), "provenance": None}

    def prepare_workflow(self):
        prepared = self.prepare(native_node="/fixture/node")
        self.assertEqual("prepared", prepared["state"], prepared)
        return prepared

    def launch(self, prepared, state="running", **status):
        """Write the launch binding and pi-subagents' status as a launched Workflow has them."""
        directory = self.directory(prepared)
        native = Path(self.scratch.name) / "async" / prepared["ticket"]
        native.mkdir(parents=True, exist_ok=True)
        binding = directory / "workflow-binding.json"
        if not binding.exists():
            binding.write_text(json.dumps({"asyncDir": str(native), "runId": "wf-1"}))
        (native / "status.json").write_text(
            json.dumps(
                {
                    "runId": "wf-1",
                    "mode": "workflow",
                    "sessionId": "unit-session",
                    "state": state,
                    "steps": [],
                    "workflow": {"emits": []},
                    **status,
                }
            )
        )

    def step(self, prepared, name):
        return workflow_step(
            PACKAGE, name, prepared["descriptor"], prepared["digest"], self.context
        )

    def result(self, prepared):
        return workflow_result(
            PACKAGE, prepared["descriptor"], prepared["digest"], self.context
        )

    @verifies("scenario.execution.workflow-register")
    def test_preparation_returns_the_workflow_plan_and_issues_its_slots(self):
        prepared = self.prepare_workflow()
        self.assertIs(False, prepared["accepted"])
        self.assertNotIn("call", prepared)
        plan = prepared["workflow"]
        ticket = prepared["ticket"]
        self.assertEqual("concorde.spec-review." + ticket, plan["name"])
        self.assertEqual(
            (SCRIPT, HOST, ["bind", "finish", "finalize"], []),
            (plan["script"], plan["host"], plan["steps"], plan["helpers"]),
        )
        argv = {
            step: [
                "/fixture/node",
                str(PACKAGE / HOST),
                step,
                prepared["descriptor"],
                prepared["digest"],
            ]
            for step in ("bind", "finish", "finalize")
        }
        self.assertEqual(argv, plan["commands"])
        expansion = plan["expansion"]
        self.assertEqual(ticket, expansion["ticket"])
        self.assertEqual(
            {step: command_text(value) for step, value in argv.items()},
            expansion["commands"],
        )
        # The issued slot is prepared exactly as a single call, gated by its own stage step.
        slot = expansion["assess"]
        issued = json.loads(
            (self.directory(prepared) / "bindings/assess.json").read_text()
        )
        self.assertEqual(ticket + ":assess", issued["ticket"])
        self.assertEqual(slot, issued["call"])
        self.assertEqual("concorde-context-assessor", slot["agent"])
        self.assertTrue(
            slot["gate"]["command"].endswith(
                f"stage {issued['descriptor']} {issued['digest']}"
            )
        )
        self.assertTrue(
            expansion["slot_gate"].endswith(
                command_text(["slot-gate", prepared["descriptor"], prepared["digest"]])
            )
        )
        self.assertEqual(
            prepared["binding"],
            {
                "argv": native_driver.launcher_argv(PACKAGE),
                "root": str(self.root),
                "descriptor": prepared["descriptor"],
                "digest": prepared["digest"],
            },
        )
        # No Agent has run and nothing is accepted.
        slot_directory = self.directory(prepared) / "slots/assess"
        self.assertFalse((slot_directory / "proposal.json").exists())
        self.assertFalse((slot_directory / "terminal.json").exists())
        self.assertFalse((self.directory(prepared) / "workflow-result.json").exists())
        self.assertEqual([], PROBE.steps)

    @verifies("scenario.execution.workflow-running")
    def test_a_running_workflow_is_not_a_result(self):
        prepared = self.prepare_workflow()
        self.launch(prepared)
        self.assertEqual({"state": "ready"}, self.step(prepared, "bind"))
        value = self.result(prepared)
        self.assertEqual("running", value["state"])
        self.assertIs(False, value["accepted"])
        self.assertEqual("wf-1", value["run_id"])
        self.assertEqual("running", value["native_state"])
        self.assertIsNone(value["failure"])
        self.assertEqual([], PROBE.failures)

    @verifies("scenario.execution.workflow-accepted")
    def test_a_finished_workflow_reports_its_receipt(self):
        prepared = self.prepare_workflow()
        self.launch(prepared)
        self.assertTrue(self.step(prepared, "finish")["accepted"])
        self.launch(prepared, state="complete")
        value = self.result(prepared)
        self.assertEqual("accepted", value["state"])
        self.assertIs(True, value["accepted"])
        self.assertEqual({"answer": "Workflow finished"}, value["output"])
        self.assertEqual("complete", value["native_state"])
        self.assertIsNone(value["failure"])
        # A finished Workflow answers no further step.
        self.launch(prepared)
        refused = self.refused(prepared, "bind")
        self.assertEqual("invalid_completion", refused.code)

    def refused(self, prepared, name):
        with self.assertRaises(Exception) as caught:
            self.step(prepared, name)
        return caught.exception

    @verifies("scenario.execution.workflow-failed")
    def test_a_failed_workflow_records_its_failure_once(self):
        for receipt in (
            None,
            {"state": "failed", "accepted": False, "output": {"answer": "stopped"}},
        ):
            with self.subTest(receipt=receipt is not None):
                PROBE.__init__()
                PROBE.failure_receipt = receipt
                prepared = self.prepare_workflow()
                cause = failure(
                    "reviewer child assess failed", layer="workflow", attempt="assess"
                )
                self.launch(
                    prepared,
                    state="failed",
                    error="child assess exited 1",
                    workflow={
                        "emits": [
                            {
                                "kind": "concorde.failure",
                                "key": "assess",
                                "feedback": cause,
                            }
                        ]
                    },
                )
                first = self.result(prepared)
                second = self.result(prepared)
                self.assertEqual(["failed"], PROBE.failures)
                for value in (first, second):
                    self.assertEqual("failed", value["state"])
                    self.assertIs(False, value["accepted"])
                    self.assertEqual("failed", value["native_state"])
                    self.assertIn("child assess exited 1", value["native_error"])
                    causes = value["failure"]["causes"]
                    self.assertIn(cause, causes)
                    self.assertTrue(
                        any(
                            item.get("attempt") == prepared["ticket"] + ":assess"
                            for item in causes
                        ),
                        causes,
                    )
                recorded = self.directory(prepared) / "workflow-result.json"
                self.assertEqual(receipt is not None, recorded.exists())
                if receipt is not None:
                    self.assertEqual(receipt["output"], first["output"])

    @verifies("scenario.execution.workflow-stop")
    def test_stopping_ends_every_later_step(self):
        prepared = self.prepare_workflow()
        self.launch(prepared)
        self.assertEqual({"state": "ready"}, self.step(prepared, "bind"))
        stopped = workflow_stop(prepared["descriptor"], prepared["digest"])
        self.assertEqual({"state": "cancelled", "accepted": False}, stopped)
        for name in ("bind", "finish", "finalize"):
            self.assertEqual("execution_cancelled", self.refused(prepared, name).code)
        with self.assertRaises(Exception) as gate:
            native_driver.slot_gate(
                PACKAGE,
                prepared["descriptor"],
                prepared["digest"],
                "assess",
                self.context,
            )
        self.assertEqual("execution_cancelled", gate.exception.code)
        self.assertEqual(["bind"], PROBE.steps)

    @verifies("scenario.execution.workflow-stop")
    def test_a_receipt_written_before_the_stop_stays_accepted(self):
        prepared = self.prepare_workflow()
        self.launch(prepared)
        self.step(prepared, "finish")
        workflow_stop(prepared["descriptor"], prepared["digest"])
        self.launch(prepared, state="stopped")
        value = self.result(prepared)
        self.assertEqual("accepted", value["state"])
        self.assertIs(True, value["accepted"])
        self.assertEqual([], PROBE.failures)

    @verifies("scenario.execution.workflow-coverage-gap")
    def test_a_missing_or_failed_child_admits_no_slot(self):
        prepared = self.prepare_workflow()
        issued = json.loads(
            (self.directory(prepared) / "bindings/assess.json").read_text()
        )
        # The slot's child submitted its proposal; its native records are what is missing.
        slot = {
            "descriptor": issued["descriptor"],
            "digest": issued["digest"],
            "ticket": issued["ticket"],
        }
        submitted = self.command(slot, "submit", self.proposal(slot))
        self.assertEqual("proposed", submitted["state"], submitted)
        child = {
            "workflowKey": "assess",
            "runId": "child-1",
            "parentWorkflowRunId": "wf-1",
            "agent": "concorde-context-assessor",
            "status": "failed",
        }
        for name, steps in {
            "missing child": [],
            "failed child": [child],
            "duplicated child": [
                {**child, "status": "completed"},
                {**child, "status": "completed"},
            ],
        }.items():
            with self.subTest(case=name):
                self.launch(prepared, steps=steps)
                error = self.refused(prepared, "finalize")
                self.assertIn(
                    getattr(error, "code", None) or error.feedback["code"],
                    {"invalid_completion", "stale_evidence"},
                )
        slot_directory = Path(issued["descriptor"]).parent
        self.assertFalse((slot_directory / "terminal.json").exists())
        self.assertEqual([], self.archives())

    @verifies("scenario.execution.workflow-register")
    def test_a_capability_without_a_runtime_prepares_no_workflow(self):
        value = self.prepare(native_root="")
        self.assertEqual("rejected", value["state"])
        self.assertEqual({"missing_runtime"}, codes(value))
        self.assertEqual([], sorted(self.calls.iterdir()))


if __name__ == "__main__":
    unittest.main()
