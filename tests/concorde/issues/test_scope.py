"""Component authority remains separate while Issue blockers travel by reference."""

import tempfile
import unittest
from pathlib import Path

from concorde.development.operation_service import OperationHost, run_operation
from concorde.issues.store import resolve_report
from concorde.spec.typed_data import typed
from tests.concorde.issues.test_store import report
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    ModelProcessDouble,
    project,
)


class ComponentIssueTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def call(self, callback=None):
        self.model = ModelProcessDouble(callback)
        host = OperationHost(
            self.root,
            PACKAGE,
            executor=self.model.executor,
            allow_primary_worktree=True,
        )
        return run_operation(
            "concorde-dev-loop",
            CONFIGURATION,
            typed(
                "concorde-dev-loop-request",
                {"target_id": "scope.bank", "task": "Implement transfer"},
            ),
            host_context=host,
        )

    def test_component_contexts_remain_separate(self):
        result = self.call()
        self.assertEqual("succeeded", result["status"], result)
        owner_calls = [
            call
            for call in self.model.calls
            if call["stage"] != "route"
            and call["snapshot"]["target_id"] == "scope.bank"
        ]
        self.assertTrue(owner_calls)
        self.assertFalse(any(call["stage"] == "implementation" for call in owner_calls))
        self.assertTrue(
            any(
                call["stage"] == "implementation"
                and call["snapshot"]["target_id"] == "service.transfer"
                for call in self.model.calls
            )
        )

    def test_foreign_component_is_not_a_write_grant(self):
        def work(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "scope.bank":
                data["tasks"][0]["target_id"] = "module.foreign"

        result = self.call(work)
        self.assertNotEqual("succeeded", result["status"])
        self.assertFalse(
            any(call["stage"] == "implementation" for call in self.model.calls)
        )

    def test_component_blocker_preserves_the_reporting_owner(self):
        def work(stage, snapshot, data, cwd):
            if stage == "specify" and snapshot["target_id"] == "service.transfer":
                reporter = self.model.calls[-1]["report_issue"]
                receipt = reporter(
                    report(owner_target_id="service.transfer", evidence=[])
                )["receipt"]
                data.update(
                    outcome="spec_incomplete",
                    blockers=[{**receipt, "blocked_step": "Specify retries"}],
                )

        result = self.call(work)
        self.assertEqual("blocked", result["status"], result)
        blocker = result["output"]["data"]["blockers"][0]
        receipt = {key: blocker[key] for key in ("issue_id", "report_id", "path")}
        self.assertEqual(
            "service.transfer",
            resolve_report(self.root, receipt)["source"]["target_id"],
        )
        self.assertFalse(
            any(call["stage"] == "implementation" for call in self.model.calls)
        )
