"""The plan workflow in a managed candidate: acceptance, rejection, staleness and failure."""

import unittest

from concorde.harness.change_worktree import git_value
from concorde.harness.revisions import target_revision
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import (
    NativeCandidate,
    failure_codes,
    stage_result_for,
    task_item,
)


class PlanWorkflowTests(NativeCandidate, unittest.TestCase):
    def start(self):
        """Prepare and launch the plan workflow, then run a sufficient assessment to ``advance``."""
        prepared = self.prepare("concorde-plan")
        self.assertEqual("prepared", prepared["state"], prepared)
        workflow = self.workflow(prepared)
        self.assertEqual({"state": "ready"}, workflow.host_step("bind"))
        workflow.child(
            "assessor", stage_result_for(workflow.slot_descriptor("assessor"))
        )
        advanced = workflow.host_step("advance")
        self.assertEqual("prepared", advanced["state"], advanced)
        return workflow

    def planner_result(self, workflow, plan):
        return stage_result_for(
            workflow.slot_descriptor("planner"), outcome="completed", plan=plan
        )

    def previous_work(self):
        """An accepted plan and task list the new workflow must not disturb."""
        self.own()
        self.accepted_plan("PREVIOUS ACCEPTED PLAN")
        self.accepted_tasks([task_item("previous-task")])
        return self.target()

    def plan_record(self):
        return (self.change / ".concorde/work/service.transfer/plan.md").read_text()

    @verifies("scenario.planning.plan-current")
    def test_an_accepted_plan_is_saved_bound_to_the_spec_revision_and_task(self):
        workflow = self.start()
        workflow.child("planner", self.planner_result(workflow, "Round to cents."))
        finished = workflow.host_step("finalize")
        self.assertEqual(
            {"state": "finished", "accepted": True, "outcome": "completed"}, finished
        )
        receipt = workflow.result()
        self.assertTrue(receipt["accepted"], receipt)
        output = receipt["output"]["data"]
        self.assertEqual("completed", output["outcome"])
        # The plan is saved in the candidate, bound to the current Spec revision and the task.
        self.assertEqual("Round to cents.", self.plan_record())
        record = self.target()
        run = self.invocation("concorde-plan")
        self.assertEqual(
            target_revision(run.repository, run.target), record["spec_digest"]
        )
        self.assertEqual(
            (self.task["task"], []), (record["task"], record["constraints"])
        )
        # The result references the saved plan.
        self.assertEqual(
            [".concorde/work/service.transfer/plan.md"],
            [item["path"] for item in output["artifacts"]],
        )
        # No task list, no code change and no readiness.
        self.assertEqual(([], "plan"), (record["tasks"], record["phase"]))
        self.assertEqual("", git_value(self.change, "status", "--porcelain", "app"))
        self.assertNotEqual("ready", self.change_state()["status"])

    @verifies("scenario.planning.plan-empty")
    def test_an_empty_plan_is_rejected_and_the_previous_work_stays(self):
        before = self.previous_work()
        workflow = self.start()
        slot = workflow.slot("planner")
        for empty in ("", "   \n"):
            with self.subTest(plan=empty):
                submitted = self.action(
                    slot,
                    "submit",
                    self.proposal(slot, self.planner_result(workflow, empty)),
                )
                self.assertEqual("rejected", submitted["state"], submitted)
                self.assertEqual(
                    ["invalid_completion"],
                    [e["code"] for e in submitted["result"]["errors"]],
                )
        # The rejected proposal cannot be finalized either.
        with self.assertRaises(SpecError):
            workflow.host_step("finalize")
        self.assertEqual(before, self.target())
        self.assertEqual("PREVIOUS ACCEPTED PLAN", self.plan_record())

    @verifies("scenario.planning.plan-stale")
    def test_changed_inputs_reject_the_returned_plan(self):
        before = self.previous_work()
        spec = self.change / "specs/transfer/module.md"
        registry = self.change / ".concorde/specs.json"
        for name, path in (("spec", spec), ("registry", registry)):
            with self.subTest(changed=name):
                workflow = self.start()
                workflow.child("planner", self.planner_result(workflow, "New plan"))
                original = path.read_bytes()
                if path == spec:
                    path.write_bytes(original + b"\nA later promise.\n")
                else:
                    path.write_bytes(original.replace(b'"modules"', b'"modules" '))
                with self.assertRaises(SpecError) as raised:
                    workflow.host_step("finalize")
                self.assertIn("stale_context", failure_codes(raised.exception))
                self.assertEqual(before, self.target())
                self.assertEqual("PREVIOUS ACCEPTED PLAN", self.plan_record())
                if path == spec:
                    # The kept plan is not current for the changed Spec.
                    self.refused(self.prepare("concorde-tasks"), "stale_context")
                    self.assertEqual(before, self.target())
                path.write_bytes(original)

    @verifies("scenario.planning.native-plan-failure")
    def test_a_failed_or_cancelled_workflow_blocks_progress_and_replaces_nothing(self):
        before = self.previous_work()
        for native_state, outcome in (
            ("failed", "execution_failed"),
            ("stopped", "execution_cancelled"),
        ):
            with self.subTest(native_state=native_state):
                workflow = self.start()
                workflow.stop_native(native_state)
                result = workflow.result()
                self.assertEqual(
                    (native_state, False, "failed"),
                    (result["native_state"], result["accepted"], result["state"]),
                )
                self.assertIsNotNone(result["failure"])
                state = self.change_state()
                self.assertEqual(
                    ("blocked", outcome), (state["status"], state["outcome"])
                )
                # The workflow stops at that step: no later Host step runs.
                with self.assertRaises(SpecError) as raised:
                    workflow.host_step("finalize")
                self.assertEqual("execution_cancelled", raised.exception.code)
                self.assertEqual(before["plan"], self.target()["plan"])
                self.assertEqual(before["tasks"], self.target()["tasks"])
                self.assertEqual("PREVIOUS ACCEPTED PLAN", self.plan_record())

    @verifies("scenario.planning.native-plan-failure")
    def test_a_failure_observed_after_the_inputs_changed_does_not_block_newer_work(
        self,
    ):
        self.previous_work()
        workflow = self.start()
        # Newer work changed the candidate's inputs before the old failure was observed.
        self.accepted_tasks([task_item("newer-task")])
        workflow.stop_native("failed")
        self.assertFalse(workflow.result()["accepted"])
        self.assertEqual("active", self.change_state()["status"])
        self.assertEqual(["newer-task"], [t["id"] for t in self.target()["tasks"]])


if __name__ == "__main__":
    unittest.main()
