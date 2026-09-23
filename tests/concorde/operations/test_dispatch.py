"""Dispatch refuses unresolved targets and native capabilities without their Pi preparation."""

import tempfile
import unittest
from pathlib import Path

from concorde.operations.dispatch import run_operation
from concorde.harness.change_worktree import git, git_value, read_change
from concorde.harness.host import OperationHost as RealHost
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE, project

TARGET = {"target_id": "service.transfer", "task": "Implement the transfer contract"}


class DispatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        self.primary = directory / "primary"
        self.primary.mkdir()
        project(self.primary)
        git(self.primary, "init", "-q", "-b", "integration")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        git(self.primary, "add", "-A")
        git(self.primary, "commit", "-qm", "Fixture")
        self.change = directory / "change"
        git(self.primary, "worktree", "add", "-q", "-b", "candidate", str(self.change))

    def call(self, root, name, data, host):
        return run_operation(
            name, CONFIGURATION, typed(name + "-request", data), host_context=host
        )

    @verifies("scenario.operations.native-without-pi")
    def test_native_capability_without_its_pi_preparation_is_refused(self):
        for name in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            with self.subTest(operation=name):
                host = RealHost(self.change, PACKAGE)
                missing = self.call(
                    self.change, name, {**TARGET, "target_id": "module.unknown"}, host
                )
                # Admission and the target check run first, as for any request.
                self.assertEqual("unknown_target", missing["errors"][0]["code"])
                result = self.call(
                    self.change, name, TARGET, RealHost(self.change, PACKAGE)
                )
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("native_required", result["errors"][0]["code"])
                self.assertIsNone(result["output"])
        # Only the candidate's session guidance was bound; no plan, task or code was accepted.
        self.assertEqual(
            "M AGENTS.md", git_value(self.change, "status", "--porcelain").strip()
        )
        state = read_change(self.change, required=True)
        self.assertEqual(("created", {}), (state["phase"], state["sections"]))


if __name__ == "__main__":
    unittest.main()
