"""Acceptance: a directly edited candidate is validated with recorded evidence and delivered."""

import unittest

from concorde.harness import change_worktree
from concorde.harness.change_worktree import git_value, read_change
from concorde.planning.records import targets
from concorde.spec.verification import verifies
from concorde.validation.records import direct_evidence
from tests.concorde.support.worktree_project import WorktreeProject


class ValidateAndDeliverAcceptance(WorktreeProject, unittest.TestCase):
    """The user session validates a candidate and delivers its change."""

    @verifies("scenario.concorde.validate-record")
    def test_directly_authored_candidate_can_be_validated_and_delivered_without_a_plan(
        self,
    ):
        path = self.change / "app/transfer.py"
        path.write_text(
            'def transfer(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError("invalid transfer")\n    return balance - amount\n'
        )
        spec = self.change / "specs/transfer/module.md"
        spec.write_text(spec.read_text() + "\nClarified directly in the candidate.\n")
        change_worktree.ensure_change(self.change, task=self.task)
        result = self.call_operation(self.change, "concorde-validate", self.task)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        state = read_change(self.change, required=True)
        self.assertEqual({}, targets(state))
        self.assertTrue(direct_evidence(state)["checks"])
        result = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": state["change_id"]}
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertIn(
            "Clarified directly",
            git_value(
                self.primary,
                "show",
                "concorde/delivered/"
                + state["change_id"]
                + ":specs/transfer/module.md",
            ),
        )
        self.assertFalse(self.change.exists())


if __name__ == "__main__":
    unittest.main()
