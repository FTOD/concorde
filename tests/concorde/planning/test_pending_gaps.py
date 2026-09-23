"""Pending gaps recorded by an accepted assessment stop later steps until the Spec is repaired."""

import unittest

from concorde.issues.store import read_issue
from concorde.planning.gaps import open_gaps
from concorde.planning.records import gap_history
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate, task_item


class PendingGapTests(NativeCandidate, unittest.TestCase):
    def assess(self, **fields):
        """Accept one native context assessment for the owner's task."""
        prepared = self.prepare("concorde-context-solve")
        self.assertEqual("prepared", prepared["state"], prepared)
        if fields.get("outcome") == "spec_incomplete":
            issue = self.report(prepared)
            fields["blockers"] = [{**issue, "blocked_step": "Plan the transfer"}]
        value = self.complete(prepared, self.stage_result(prepared, **fields))
        self.assertTrue(value["accepted"], value)
        return value["result"]["output"]["data"]

    def assert_blocked(self, operation, blockers):
        value = self.prepare(operation)
        self.assertEqual(("not-run", False), (value["state"], value["accepted"]), value)
        self.assertNotIn("descriptor", value)
        output = value["result"]["output"]["data"]
        self.assertEqual(
            ("spec_incomplete", blockers), (output["outcome"], output["blockers"])
        )

    @verifies("scenario.planning.pending-gap-blocks")
    def test_a_pending_gap_stops_plan_tasks_and_implementation(self):
        self.own()
        blockers = self.assess(outcome="spec_incomplete")["blockers"]
        [gap] = open_gaps(self.change_state())
        self.assertEqual(
            ("context-solve", "service.transfer"), (gap["phase"], gap["target_id"])
        )
        # The gap is checked before the plan: an unplanned Module reports the blocker.
        self.assert_blocked("concorde-tasks", blockers)
        for _ in range(2):
            self.assert_blocked("concorde-plan", blockers)
        self.accepted_plan()
        self.accepted_tasks([task_item("transfer-rounding")])
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            with self.subTest(operation=operation):
                self.assert_blocked(operation, blockers)
        # Repeating the requests did not clear the gap.
        self.assertEqual([gap["id"]], [g["id"] for g in open_gaps(self.change_state())])

    @verifies("scenario.planning.pending-gap-cleared")
    def test_a_repaired_spec_and_a_sufficient_assessment_clear_the_gap(self):
        self.own()
        blockers = self.assess(outcome="spec_incomplete")["blockers"]
        # Without a Spec change a sufficient assessment leaves the gap bound to its revision.
        self.assertEqual("completed", self.assess()["outcome"])
        self.assertEqual(1, len(open_gaps(self.change_state())))
        spec = self.change / "specs/transfer/module.md"
        spec.write_bytes(spec.read_bytes() + b"\nTransfers round half to even.\n")
        self.assertEqual("completed", self.assess()["outcome"])
        self.assertEqual([], open_gaps(self.change_state()))
        [gap] = gap_history(self.change_state())
        self.assertEqual("resolved", gap["status"])
        # Later steps may start.
        self.assertEqual("prepared", self.prepare("concorde-plan")["state"])
        # The Issue the gap cited stays open.
        record, _ = read_issue(self.change, blockers[0]["issue_id"])
        self.assertEqual("open", record["status"])


if __name__ == "__main__":
    unittest.main()
