"""Delivery refusals, retention, sessions and manual merges on real Git worktrees."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from concorde.delivery import deliver as delivery_service
from concorde.delivery.manual_merge import record_manual_merge
from concorde.delivery.records import manual_merge
from concorde.delivery.records import receipt as delivery_receipt
from concorde.harness.change_worktree import git, git_value, read_change
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.status_store import read_status
from concorde.review.review import require_reviews
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject


class DeliveryGateTests(WorktreeProject, unittest.TestCase):
    def deliver(self, root, change_id, **extra):
        return self.call_operation(
            root, "concorde-deliver", {"change_id": change_id, **extra}
        )

    def refused(self, result, code):
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(code, result["errors"][0]["code"], result)

    def branch(self, change_id):
        return "concorde/delivered/" + change_id

    def branch_exists(self, change_id):
        return (
            git(
                self.primary,
                "show-ref",
                "--verify",
                "--quiet",
                "refs/heads/" + self.branch(change_id),
                check=False,
            ).returncode
            == 0
        )

    def primary_state(self):
        return (
            git_value(self.primary, "rev-parse", "HEAD"),
            git_value(self.primary, "status", "--porcelain", "--untracked-files=all"),
            (self.primary / "shared.txt").read_bytes(),
        )

    def status(self, change_id):
        return read_status(self.primary, change_id)

    def assert_blocked_in_deliver(self):
        change = read_change(self.change, required=True)
        self.assertEqual(("blocked", "deliver"), (change["status"], change["phase"]))

    # --- delivering -------------------------------------------------------------------------

    @verifies("scenario.delivery.keep-worktree")
    def test_a_kept_worktree_is_marked_delivered_and_stays_through_retries(self):
        change_id = self.ready_delivery()
        result = self.deliver(self.change, change_id, keep_worktree=True)
        self.assertEqual("succeeded", result["status"], result)
        self.assertTrue(self.branch_exists(change_id))
        self.assertTrue(self.change.exists())
        self.assertEqual("delivered", read_change(self.change, required=True)["status"])
        state = self.status(change_id)
        self.assertEqual("retained", state["cleanup"]["status"])
        self.assertTrue(delivery_receipt(state)["retained_worktree"])
        # A retry that states nothing keeps the recorded choice.
        again = self.deliver(self.primary, change_id)
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        removed = self.deliver(self.primary, change_id, keep_worktree=False)
        self.assertEqual("succeeded", removed["status"], removed)
        self.assertFalse(self.change.exists())
        self.assertEqual("removed", self.status(change_id)["cleanup"]["status"])

    @verifies("scenario.delivery.not-ready")
    def test_a_change_that_is_not_ready_is_refused(self):
        from concorde.harness.change_worktree import ensure_change

        change_id = ensure_change(self.change, task=self.task)["change_id"]
        self.refused(self.deliver(self.change, change_id), "incomplete_change")
        self.assertFalse(self.branch_exists(change_id))

    @verifies("scenario.delivery.not-ready")
    def test_a_ready_change_whose_completion_check_fails_is_refused(self):
        change_id = self.ready_delivery()
        run = Invocation(
            "concorde-validate",
            CONFIGURATION,
            self.task,
            OperationHost(self.change, PACKAGE),
        )
        require_reviews(run, True)
        self.refused(self.deliver(self.change, change_id), "review_required")
        self.assertFalse(self.branch_exists(change_id))

    @verifies("scenario.delivery.stale-candidate")
    def test_a_candidate_edited_after_validation_is_refused(self):
        change_id = self.ready_delivery()
        path = self.change / "app/transfer.py"
        path.write_text(path.read_text() + "# edited after validation\n")
        edited = path.read_bytes()
        self.refused(self.deliver(self.change, change_id), "stale_evidence")
        self.assert_blocked_in_deliver()
        self.assertEqual(edited, path.read_bytes())
        self.assertFalse(self.branch_exists(change_id))

    @verifies("scenario.delivery.conflict")
    def test_a_candidate_conflicting_with_the_primary_head_is_refused(self):
        (self.change / "shared.txt").write_text("candidate\n")
        change_id = self.ready_delivery()
        (self.primary / "shared.txt").write_text("primary\n")
        self.commit(self.primary, "Conflicting primary change")
        before = self.primary_state()
        candidate = git_value(self.change, "status", "--porcelain")
        self.refused(self.deliver(self.change, change_id), "merge_conflict")
        self.assert_blocked_in_deliver()
        self.assertEqual(before, self.primary_state())
        self.assertEqual(candidate, git_value(self.change, "status", "--porcelain"))
        self.assertEqual("candidate\n", (self.change / "shared.txt").read_text())
        self.assertFalse(self.branch_exists(change_id))

    @verifies("scenario.delivery.failed-checks")
    def test_an_integration_failing_its_checks_is_not_published(self):
        change_id = self.ready_delivery()
        path = self.primary / "checks/transfer_check.py"
        path.write_text(path.read_text() + "\nassert transfer(100, 20) == 40\n")
        self.commit(self.primary, "Stricter acceptance on the primary branch")
        before = self.primary_state()
        self.refused(self.deliver(self.change, change_id), "failed_merge_checks")
        self.assert_blocked_in_deliver()
        self.assertFalse(self.branch_exists(change_id))
        self.assertEqual(before, self.primary_state())

    @verifies("scenario.delivery.cleanup-kept")
    def test_cleanup_keeps_a_candidate_edited_after_publication(self):
        change_id = self.ready_delivery()
        with patch.object(
            delivery_service, "_cleanup", side_effect=OSError("interrupted cleanup")
        ):
            self.assertEqual("failed", self.deliver(self.change, change_id)["status"])
        self.assertTrue(self.branch_exists(change_id))
        published = git_value(self.primary, "rev-parse", self.branch(change_id))
        edit = self.change / "shared.txt"
        edit.write_text("edited before cleanup\n")
        self.refused(self.deliver(self.primary, change_id), "stale_delivery")
        self.assertTrue(self.change.exists())
        self.assertEqual("edited before cleanup\n", edit.read_text())
        self.assertEqual(
            published, git_value(self.primary, "rev-parse", self.branch(change_id))
        )

    # --- who may deliver --------------------------------------------------------------------

    @verifies("scenario.delivery.session-rejected")
    def test_a_third_worktree_cannot_deliver(self):
        change_id = self.ready_delivery()
        third = self.directory / "third"
        git(self.primary, "worktree", "add", "-b", "third", str(third))
        self.refused(self.deliver(third, change_id), "delivery_session_required")
        redirected = OperationHost(self.primary, PACKAGE, session_root=third)
        result = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": change_id}, host=redirected
        )
        self.refused(result, "delivery_session_required")
        self.assertFalse(self.branch_exists(change_id))

    @verifies("scenario.delivery.nested-rejected")
    def test_a_nested_capability_request_cannot_deliver(self):
        change_id = self.ready_delivery()
        # A running capability's host; its own request is admitted one level deeper.
        running = replace(OperationHost(self.change, PACKAGE), depth=1)
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}, host=running
        )
        self.refused(result, "delivery_session_required")
        self.assertFalse(self.branch_exists(change_id))

    # --- primary merges ---------------------------------------------------------------------

    @verifies("scenario.delivery.merge-session-rejected")
    def test_a_primary_merge_from_the_kept_candidate_is_refused(self):
        change_id = self.ready_delivery()
        staged = self.deliver(self.change, change_id, keep_worktree=True)
        self.assertEqual("succeeded", staged["status"], staged)
        before = self.primary_state()
        self.refused(
            self.deliver(self.change, change_id, merge_primary=True),
            "primary_session_required",
        )
        self.assertEqual(before, self.primary_state())
        self.assertIsNone(delivery_receipt(self.status(change_id))["primary_merge"])

    @verifies("scenario.delivery.dirty-primary")
    def test_local_primary_edits_block_the_primary_merge(self):
        change_id = self.ready_delivery()
        staged = self.deliver(self.change, change_id)
        self.assertEqual("succeeded", staged["status"], staged)
        (self.primary / "shared.txt").write_text("local edit\n")
        (self.primary / "untracked.txt").write_text("untracked\n")
        before = self.primary_state()
        self.refused(
            self.deliver(self.primary, change_id, merge_primary=True), "dirty_primary"
        )
        self.assertEqual(before, self.primary_state())
        self.assertEqual("untracked\n", (self.primary / "untracked.txt").read_text())
        self.assertIsNone(delivery_receipt(self.status(change_id))["primary_merge"])


class ManualMergeTests(WorktreeProject, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.change_id = self.ready_delivery()
        # The developer commits the deliverable work, never the Host's worktree guidance.
        git(self.change, "add", "app/transfer.py")
        git(self.change, "commit", "-qm", "Candidate work")
        self.candidate_commit = git_value(self.change, "rev-parse", "HEAD")

    def merge(self):
        git(
            self.primary, "merge", "-q", "--no-ff", "-m", "Merge candidate", "candidate"
        )
        return git_value(self.primary, "rev-parse", "HEAD")

    def record(self, commit, cleanup="pending"):
        return record_manual_merge(
            self.primary, self.change_id, commit=commit, cleanup=cleanup
        )

    def refused(self, commit, code, cleanup="pending"):
        before = read_status(self.primary, self.change_id)
        with self.assertRaises(SpecError) as error:
            self.record(commit, cleanup)
        self.assertEqual(code, error.exception.code)
        self.assertEqual(before, read_status(self.primary, self.change_id))

    @verifies("scenario.delivery.manual-merge")
    def test_an_ordinary_git_merge_is_recorded_without_merging(self):
        merged = self.merge()
        state = self.record(merged)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        stored = read_status(self.primary, self.change_id)
        self.assertEqual(state, stored)
        self.assertEqual(
            {
                "commit": merged,
                "candidate_commit": self.candidate_commit,
                "method": "ordinary-git",
            },
            manual_merge(stored),
        )
        self.assertEqual(
            ("merged", "complete", "merged"),
            (stored["status"], stored["phase"], stored["outcome"]),
        )
        self.assertEqual("pending", stored["cleanup"]["status"])

    @verifies("scenario.delivery.manual-merge-not-integrated")
    def test_an_unintegrated_commit_is_not_recorded(self):
        before_merge = git_value(self.primary, "rev-parse", "HEAD")
        # The primary head does not contain the candidate commit.
        self.refused(before_merge, "stale_evidence")
        # The candidate commit itself is not in the primary branch's history.
        self.refused(self.candidate_commit, "stale_evidence")
        self.assertIsNone(manual_merge(read_status(self.primary, self.change_id)))

    @verifies("scenario.delivery.manual-merge-cleanup")
    def test_only_the_cleanup_outcome_of_a_recorded_merge_is_updated(self):
        merged = self.merge()
        recorded = manual_merge(self.record(merged))
        git(self.primary, "worktree", "remove", "--force", str(self.change))
        state = self.record(None, "removed")
        self.assertEqual(recorded, manual_merge(state))
        self.assertEqual("removed", state["cleanup"]["status"])
        self.assertEqual(("merged", "complete"), (state["status"], state["phase"]))

    @verifies("scenario.delivery.manual-merge-after-removal")
    def test_a_merge_cannot_be_recorded_after_unrecorded_cleanup(self):
        merged = self.merge()
        git(self.primary, "worktree", "remove", "--force", str(self.change))
        self.refused(merged, "stale_evidence")
        self.refused(merged, "stale_evidence", cleanup="removed")
        self.assertIsNone(manual_merge(read_status(self.primary, self.change_id)))


if __name__ == "__main__":
    unittest.main()
