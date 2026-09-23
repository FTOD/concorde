"""Real Git regressions for delivering a ready candidate and merging it into the primary."""

import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from concorde.delivery import deliver as delivery_service
from concorde.delivery.records import receipt as delivery_receipt
from concorde.harness.change_worktree import git, git_value
from concorde.harness.host import OperationHost
from concorde.operations.dispatch import run_operation
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject


class DeliveryTests(WorktreeProject, unittest.TestCase):
    """Delivery transactions of a directly validated candidate."""

    @verifies("scenario.delivery.pending-confirmed")
    def test_created_pending_files_are_confirmed_and_the_rest_stay_pending(self):
        self.declare_pending_files()
        (self.change / "app/rounding.py").write_text(
            "def round_half_up(value):\n    return value\n"
        )
        # A pending entry whose file exists fails CHK.binds.pending-subset, so the host confirms
        # it in the candidate before validating; delivery then has nothing left to confirm.
        change_id = self.ready_delivery()
        realizations = [
            item
            for item in json.loads(
                (self.change / "specs/transfer/module.md.json").read_text()
            )["defines"]
            if item["type"] == "realization"
        ]
        self.assertEqual([], realizations[0]["pending"])
        self.assertEqual(["checks/rounding_check.py"], realizations[1]["pending"])
        result = self.call_operation(
            self.change,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": True},
        )
        self.assertEqual("succeeded", result["status"], result)
        answer = result["output"]["data"]["answer"]
        self.assertIn("checks/rounding_check.py", answer)
        receipt = delivery_receipt(
            json.loads(
                (self.primary / f".concorde/status/{change_id}.json").read_text()
            )
        )
        self.assertEqual([], receipt["confirmed_files"])
        self.assertEqual(["checks/rounding_check.py"], receipt["still_pending"])
        self.assertEqual(
            "success", validate_repository(self.change, package_root=PACKAGE).status
        )

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
    )
    def test_primary_merge_requires_separate_delivery_and_primary_session(self):
        change_id = self.ready_delivery()
        request = {"change_id": change_id, "merge_primary": True}
        result = self.call_operation(self.change, "concorde-deliver", request)
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        result = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("delivery_required", result["errors"][0]["code"], result)
        staged = self.call_operation(
            self.change,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": True},
        )
        self.assertEqual("succeeded", staged["status"], staged)
        result = self.call_operation(self.change, "concorde-deliver", request)
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        redirected = OperationHost(self.primary, PACKAGE, session_root=self.change)
        result = self.call_operation(
            self.primary, "concorde-deliver", request, host=redirected
        )
        self.assertEqual(
            "primary_session_required", result["errors"][0]["code"], result
        )
        merged = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", merged["status"], merged)
        head = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            delivery_service,
            "_verify_merged_tree",
            side_effect=AssertionError("duplicate merge checks"),
        ):
            again = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(head, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies("scenario.delivery.branch", "scenario.delivery.retry")
    def test_explicit_retention_survives_interrupted_initial_cleanup(self):
        change_id = self.ready_delivery()
        before = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            delivery_service, "_cleanup", side_effect=OSError("interrupted cleanup")
        ):
            result = self.call_operation(
                self.change,
                "concorde-deliver",
                {"change_id": change_id, "keep_worktree": True},
            )
        self.assertEqual("failed", result["status"], result)
        again = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        self.assertIn("retained", again["output"]["data"]["answer"])
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies("scenario.delivery.branch", "scenario.delivery.retry")
    def test_cleanup_retry_persists_a_changed_retention_choice_before_cleanup(self):
        change_id = self.ready_delivery()
        with patch.object(
            delivery_service, "_cleanup", side_effect=OSError("interrupted cleanup")
        ):
            result = self.call_operation(
                self.change, "concorde-deliver", {"change_id": change_id}
            )
            self.assertEqual("failed", result["status"], result)
            result = self.call_operation(
                self.primary,
                "concorde-deliver",
                {"change_id": change_id, "keep_worktree": True},
            )
        self.assertEqual("failed", result["status"], result)
        again = self.call_operation(
            self.primary, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", again["status"], again)
        self.assertTrue(self.change.exists())
        removed = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "keep_worktree": False},
        )
        self.assertEqual("succeeded", removed["status"], removed)
        self.assertFalse(self.change.exists())

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
    )
    def test_independent_deliveries_do_not_update_each_other_or_primary(self):
        before = git_value(self.primary, "rev-parse", "HEAD")
        first_id = self.ready_delivery()
        first = self.call_operation(
            self.change, "concorde-deliver", {"change_id": first_id}
        )
        self.assertEqual("succeeded", first["status"], first)
        first_branch = "concorde/delivered/" + first_id
        first_head = git_value(self.primary, "rev-parse", first_branch)
        self.change = self.directory / "second-change"
        git(self.primary, "worktree", "add", "-b", "second-candidate", str(self.change))
        second_id = self.ready_delivery()
        second = self.call_operation(
            self.change, "concorde-deliver", {"change_id": second_id}
        )
        self.assertEqual("succeeded", second["status"], second)
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(first_head, git_value(self.primary, "rev-parse", first_branch))
        self.assertTrue(
            git_value(self.primary, "rev-parse", "concorde/delivered/" + second_id)
        )
        start = threading.Barrier(2)
        checking = threading.Lock()
        verify = delivery_service._verify_merged_tree

        def checked(*args, **kwargs):
            self.assertTrue(
                checking.acquire(blocking=False), "overlapping primary merge checks"
            )
            try:
                return verify(*args, **kwargs)
            finally:
                checking.release()

        def promote(change_id):
            start.wait(timeout=10)
            return run_operation(
                "concorde-deliver",
                CONFIGURATION,
                typed(
                    "concorde-deliver-request",
                    {"change_id": change_id, "merge_primary": True},
                ),
                host_context=OperationHost(self.primary, PACKAGE),
            )

        with (
            patch.object(delivery_service, "_verify_merged_tree", side_effect=checked),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            results = list(pool.map(promote, (first_id, second_id)))
        for merged in results:
            self.assertEqual("succeeded", merged["status"], merged)
        for change_id in (first_id, second_id):
            branch = "concorde/delivered/" + change_id
            self.assertEqual(
                0,
                git(
                    self.primary,
                    "merge-base",
                    "--is-ancestor",
                    branch,
                    "HEAD",
                    check=False,
                ).returncode,
            )

    @verifies("scenario.delivery.branch")
    def test_primary_merge_checks_latest_integration_and_preserves_delivery_on_failure(
        self,
    ):
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        path = self.primary / "checks/transfer_check.py"
        path.write_text(path.read_text() + "\nassert transfer(100, 20) == 40\n")
        advanced = self.commit(self.primary, "Changed acceptance after delivery")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("failed_merge_checks", result["errors"][0]["code"], result)
        self.assertEqual(advanced, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertTrue(
            git_value(self.primary, "rev-parse", "concorde/delivered/" + change_id)
        )

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-conflict",
    )
    def test_final_merge_conflict_preserves_primary_and_delivered_branch(self):
        (self.change / "shared.txt").write_text("candidate\n")
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        (self.primary / "shared.txt").write_text("primary\n")
        before = self.commit(self.primary, "Conflicting change after delivery")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("merge_conflict", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))
        self.assertEqual(
            "candidate",
            git_value(
                self.primary, "show", "concorde/delivered/" + change_id + ":shared.txt"
            ),
        )
        self.assertEqual("", git_value(self.primary, "status", "--porcelain"))

    def test_delivery_does_not_overwrite_an_existing_branch(self):
        change_id = self.ready_delivery()
        branch = "concorde/delivered/" + change_id
        git(self.primary, "branch", branch)
        before = git_value(self.primary, "rev-parse", branch)
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", branch))
        self.assertTrue(self.change.exists())

    @verifies("scenario.delivery.preview")
    def test_primary_merge_preview_after_source_removal_is_read_only(self):
        change_id = self.ready_delivery()
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", result["status"], result)
        path = self.primary / result["output"]["data"]["artifacts"][0]["path"]
        receipt = path.read_bytes()
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
            mode="describe-policy",
        )
        self.assertEqual("described", result["status"], result)
        self.assertEqual(receipt, path.read_bytes())
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    def test_changed_delivery_ref_blocks_final_merge(self):
        change_id = self.ready_delivery()
        result = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", result["status"], result)
        branch = "concorde/delivered/" + change_id
        git(self.primary, "update-ref", "refs/heads/" + branch, "HEAD")
        before = git_value(self.primary, "rev-parse", "HEAD")
        result = self.call_operation(
            self.primary,
            "concorde-deliver",
            {"change_id": change_id, "merge_primary": True},
        )
        self.assertEqual("stale_delivery", result["errors"][0]["code"], result)
        self.assertEqual(before, git_value(self.primary, "rev-parse", "HEAD"))

    @verifies(
        "scenario.delivery.branch",
        "scenario.delivery.merge-primary",
        "scenario.delivery.merge-retry",
    )
    def test_primary_merge_recovers_receipt_after_update_without_merging_again(self):
        change_id = self.ready_delivery()
        staged = self.call_operation(
            self.change, "concorde-deliver", {"change_id": change_id}
        )
        self.assertEqual("succeeded", staged["status"], staged)
        write = delivery_service._write_json

        def interrupted(root, relative, receipt):
            if (receipt.get("primary_merge") or {}).get("status") == "merged":
                raise OSError("interrupted after primary ref update")
            return write(root, relative, receipt)

        request = {"change_id": change_id, "merge_primary": True}
        with patch.object(delivery_service, "_write_json", side_effect=interrupted):
            result = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("failed", result["status"], result)
        merged = git_value(self.primary, "rev-parse", "HEAD")
        with patch.object(
            delivery_service,
            "_verify_merged_tree",
            side_effect=AssertionError("duplicate checks"),
        ):
            again = self.call_operation(self.primary, "concorde-deliver", request)
        self.assertEqual("succeeded", again["status"], again)
        self.assertEqual(merged, git_value(self.primary, "rev-parse", "HEAD"))
        receipt = delivery_receipt(
            json.loads(
                (
                    self.primary / again["output"]["data"]["artifacts"][0]["path"]
                ).read_text()
            )
        )
        self.assertEqual("merged", receipt["primary_merge"]["status"])
        self.assertTrue(
            list((self.primary / ".concorde/runs").glob("*/delivery/staging"))
        )
        self.assertTrue(
            list((self.primary / ".concorde/runs").glob("*/delivery/primary"))
        )
        self.assertFalse((self.primary / ".concorde/deliveries").exists())

    @verifies("scenario.delivery.branch")
    def test_integration_is_verified_with_the_host_package_and_never_built(self):
        fixture_report = validate_repository(self.primary, package_root=PACKAGE)
        self.assertEqual(fixture_report.status, "success")
        # A self-hosted integration carries its own launcher; delivery never runs it.
        (self.primary / "scripts").mkdir(exist_ok=True)
        (self.primary / "scripts/concorde.py").write_text(
            "raise SystemExit('the integrated tree must not be executed')\n"
        )
        (self.primary / "concorde.json").write_text("{}")
        (self.primary / "app/transfer.py").write_text(
            "def transfer(balance, amount):\n"
            '    if amount <= 0 or amount > balance: raise ValueError("invalid transfer")\n'
            "    return balance - amount\n"
        )
        commit = self.commit(self.primary, "Self-hosted integration fixture")
        tree = git_value(self.primary, "rev-parse", "HEAD^{tree}")
        verified = []

        def inspect(root, **kwargs):
            self.assertNotEqual(root, self.primary)
            self.assertEqual(PACKAGE, kwargs["package_root"])
            self.assertEqual(git_value(root, "rev-parse", "HEAD^{tree}"), tree)
            self.assertFalse((root / "generated").exists())
            verified.append(root)
            return fixture_report

        with patch.object(delivery_service, "validate_repository", side_effect=inspect):
            checks = delivery_service._verify_merged_tree(
                OperationHost(self.primary, PACKAGE),
                commit,
                tree,
                "change.integration-build",
            )
        self.assertEqual(len(verified), 1)
        self.assertFalse(verified[0].exists())
        self.assertTrue(checks)
        self.assertTrue(all(check["status"] == "passed" for check in checks))
        self.assertFalse((self.primary / "generated").exists())


if __name__ == "__main__":
    unittest.main()
