"""Acceptance: a ready candidate is delivered on its own branch and merged on authorization."""

import subprocess
import unittest

from concorde.harness.change_worktree import git_value, read_change
from concorde.spec.verification import verifies

from .develop_flow import GUARDED, DevelopProject


class DeliverChangeAcceptance(DevelopProject, unittest.TestCase):
    """The user session delivers the developed transfer change and then merges it."""

    def is_ancestor(self, older: str, newer: str) -> bool:
        return (
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", older, newer],
                cwd=self.primary,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )

    def ready_change(self) -> str:
        self.develop()
        result = self.validate()
        self.assertEqual("ready", result["output"]["data"]["outcome"], result)
        return read_change(self.change, required=True)["change_id"]

    @verifies("scenario.concorde.deliver-stage", "scenario.concorde.deliver-merge")
    def test_a_ready_change_is_delivered_and_then_merged_with_authorization(self):
        change_id = self.ready_change()
        # The primary branch moved on while the change was developed.
        (self.primary / "shared.txt").write_text("updated on the primary branch\n")
        self.commit(self.primary, "Unrelated primary work")
        primary = self.primary_state()

        delivered = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", delivered["status"], delivered)
        branch = "concorde/delivered/" + change_id
        self.assertEqual([branch], self.delivered_branches())
        # The published tree combines the candidate with the current primary branch.
        self.assertTrue(self.is_ancestor(primary["head"], branch))
        self.assertEqual(
            GUARDED.rstrip("\n"),
            git_value(self.primary, "show", branch + ":app/transfer.py"),
        )
        self.assertEqual(
            "updated on the primary branch",
            git_value(self.primary, "show", branch + ":shared.txt"),
        )
        self.assertFalse(self.change.exists())
        self.assertNotIn(str(self.change), git_value(self.primary, "worktree", "list"))
        self.assertEqual(primary, self.primary_state())

        # The developer authorizes the merge; the primary session requests it.
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))
        merged = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("succeeded", merged["status"], merged)
        head = git_value(self.primary, "rev-parse", "integration")
        self.assertTrue(self.is_ancestor(primary["head"], head))
        self.assertTrue(self.is_ancestor(branch, head))
        self.assertEqual(GUARDED, (self.primary / "app/transfer.py").read_text())
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))

    @verifies("scenario.concorde.validate-stale")
    def test_a_changed_file_invalidates_readiness_before_delivery(self):
        change_id = self.ready_delivery()
        before = git_value(self.primary, "rev-parse", "integration")
        (self.change / "app/transfer.py").write_text(
            GUARDED + "# Edited after validation.\n"
        )
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertNotEqual("succeeded", result["status"], result)
        (error,) = result["errors"]
        self.assertEqual("stale_evidence", error["code"], result)
        self.assertEqual([], self.delivered_branches())
        self.assertEqual(before, git_value(self.primary, "rev-parse", "integration"))
        self.assertTrue(self.change.exists())


if __name__ == "__main__":
    unittest.main()
