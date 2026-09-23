"""Validation of candidates: change identity, pending files, direct readiness and check gates."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import change_worktree
from concorde.harness.change_worktree import ensure_change, git_value, read_change
from concorde.harness.host import OperationHost
from concorde.operations.dispatch import run_operation
from concorde.planning.records import targets
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from concorde.validation.records import direct_evidence
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE, project
from tests.concorde.support.worktree_project import WorktreeProject


class CandidateValidationTests(WorktreeProject, unittest.TestCase):
    """Validation of a registered candidate in real Git worktrees."""

    @verifies("scenario.validation.without-change")
    def test_validation_from_the_primary_needs_an_existing_change(self):
        worktrees = git_value(self.primary, "worktree", "list", "--porcelain")
        for request in (self.task, {**self.task, "change_id": "change.unknown"}):
            for mode in ("execute", "describe-policy"):
                with self.subTest(request=request, mode=mode):
                    result = self.call_operation(
                        self.primary,
                        "concorde-validate",
                        request,
                        host=OperationHost(
                            self.primary,
                            PACKAGE,
                            mode=mode,
                            relay=self.relay_in_process(),
                        ),
                    )
                    self.assertEqual("blocked", result["status"], result)
                    self.assertEqual(
                        "missing_change", result["errors"][0]["code"], result
                    )
                    self.assertEqual([], self.relayed)
        self.assertFalse((self.primary / ".concorde/status").exists())
        self.assertEqual(
            worktrees, git_value(self.primary, "worktree", "list", "--porcelain")
        )
        # A linked worktree without a registered change is refused the same way.
        result = self.call_operation(self.change, "concorde-validate", self.task)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("missing_change", result["errors"][0]["code"], result)
        self.assertFalse((self.primary / ".concorde/status").exists())

    @verifies("scenario.validation.pending-confirmed")
    def test_created_pending_files_are_confirmed_before_the_specs_are_validated(self):
        self.declare_pending_files()
        (self.change / "app/rounding.py").write_text(
            "def round_half_up(value):\n    return value\n"
        )
        # A pending entry whose file exists fails CHK.binds.pending-subset, so the host confirms
        # it in the candidate before validating.
        self.ready_delivery()
        realizations = [
            item
            for item in json.loads(
                (self.change / "specs/transfer/module.md.json").read_text()
            )["defines"]
            if item["type"] == "realization"
        ]
        self.assertEqual([], realizations[0]["pending"])
        self.assertEqual(["checks/rounding_check.py"], realizations[1]["pending"])
        self.assertEqual(
            "success", validate_repository(self.change, package_root=PACKAGE).status
        )

    def test_a_declared_file_that_was_never_created_or_marked_is_invalid(self):
        self.declare_pending_files()
        path = self.change / "specs/transfer/module.md.json"
        metadata = json.loads(path.read_text())
        next(item for item in metadata["defines"] if item["type"] == "realization").pop(
            "pending"
        )
        path.write_text(json.dumps(metadata, indent=2) + "\n")
        report = validate_repository(self.change, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        self.assertIn(
            "CHK.binds.exists", {finding.rule_id for finding in report.findings}
        )

    @verifies("scenario.validation.ready-direct")
    def test_directly_authored_candidate_becomes_ready_without_a_plan(self):
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


class ValidationCheckTests(unittest.TestCase):
    """Configured checks of the fixture project as `concorde-validate` runs them."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        project(self.root)
        self.config = json.loads((self.root / ".concorde/config.json").read_text())

    def save_config(self):
        (self.root / ".concorde/config.json").write_text(json.dumps(self.config))

    def configure(self, code, timeout=10):
        check = self.config["checks"][0]
        check.update(argv=["{python}", "-c", code], timeout_seconds=timeout)
        self.save_config()
        repo = SpecRepository(self.root, PACKAGE)
        return repo, repo.module("service.transfer"), check["id"]

    @verifies("scenario.validation.check-input-unsafe")
    def test_public_validation_reports_preflight_owner_without_executing_checks(self):
        self.config["checks"][0]["inputs"] = ["removed-lock.json"]
        _, target, check_id = self.configure("print('must not run')")
        # Validation needs an existing change; this embedding host registers it in place.
        ensure_change(self.root, allow_primary=True)
        with patch("concorde.harness.checks.execute_check") as execute:
            result = run_operation(
                "concorde-validate",
                CONFIGURATION,
                typed(
                    "concorde-validate-request",
                    {"target_id": target.id, "task": "Check candidate"},
                ),
                host_context=OperationHost(
                    self.root, PACKAGE, allow_primary_worktree=True
                ),
            )
        execute.assert_not_called()
        self.assertNotEqual("succeeded", result["status"], result)
        for value in (check_id, target.id, "removed-lock.json", "missing_source"):
            self.assertIn(value, json.dumps(result))

    @verifies("scenario.validation.failed-check")
    def test_real_project_write_fails_validation_and_never_records_ready(self):
        self.configure("open('unlisted-new.txt','w').write('unsafe')")
        ensure_change(self.root, allow_primary=True)
        result = run_operation(
            "concorde-validate",
            CONFIGURATION,
            typed(
                "concorde-validate-request",
                {"target_id": "service.transfer", "task": "Check candidate"},
            ),
            host_context=OperationHost(self.root, PACKAGE, allow_primary_worktree=True),
        )
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertFalse((self.root / "unlisted-new.txt").exists())
        self.assertIn("failed", json.dumps(result))
        change = read_change(self.root)
        if change is not None:
            self.assertNotEqual("ready", change["status"])


if __name__ == "__main__":
    unittest.main()
