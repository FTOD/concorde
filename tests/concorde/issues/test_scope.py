"""Explicit component authority stays separate while Issue blockers travel by reference."""

import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.native_planning import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import read_change
from concorde.implementation.implement import component_intent
from concorde.issues.store import resolve_report
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
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
        self.task = {"target_id": "scope.bank", "task": "Implement transfer"}
        self.model = ModelProcessDouble()

    def call(self, operation, task=None, callback=None):
        self.model.callback = callback
        host = OperationHost(
            self.root,
            PACKAGE,
            executor=self.model.executor,
            allow_primary_worktree=True,
        )
        return run_operation(
            operation,
            CONFIGURATION,
            typed(operation + "-request", task or self.task),
            host_context=host,
        )

    def parent_tasks(self):
        for operation in ("concorde-plan", "concorde-tasks"):
            result = self.call(operation)
            self.assertEqual("succeeded", result["status"], result)
        state = read_change(self.root, required=True)
        selected = state["targets"]["scope.bank"]["tasks"]
        return {
            "target_id": "service.transfer",
            "task": component_intent(selected),
            "change_id": state["change_id"],
        }

    @verifies("scenario.implementation.caller-components")
    def test_component_contexts_remain_separate(self):
        component = self.parent_tasks()
        result = self.call("concorde-implement")
        self.assertEqual("unsupported", result["output"]["data"]["outcome"], result)
        self.assertFalse(
            any(call["stage"] == "implementation" for call in self.model.calls)
        )
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            result = self.call(operation, component)
            self.assertEqual("succeeded", result["status"], result)
        owner_calls = [
            call
            for call in self.model.calls
            if call["snapshot"]["target_id"] == "scope.bank"
        ]
        self.assertTrue(owner_calls)
        self.assertFalse(any(call["stage"] == "implementation" for call in owner_calls))
        implementations = [
            call for call in self.model.calls if call["stage"] == "implementation"
        ]
        self.assertEqual(
            ["service.transfer"],
            [call["snapshot"]["target_id"] for call in implementations],
        )
        self.assertNotIn("app/ledger.py", implementations[0]["launch"].write_paths)
        self.assertEqual(
            "scope.bank", read_change(self.root, required=True)["target_id"]
        )

    @verifies("scenario.planning.tasks-foreign-target")
    def test_foreign_component_is_not_a_write_grant(self):
        self.assertEqual("succeeded", self.call("concorde-plan")["status"])

        def work(stage, snapshot, data, cwd):
            if stage == "tasks":
                data["tasks"][0]["target_id"] = "module.foreign"

        result = self.call("concorde-tasks", callback=work)
        self.assertEqual("blocked", result["status"], result)
        self.assertFalse(
            any(call["stage"] == "implementation" for call in self.model.calls)
        )

    @verifies("scenario.issues.blocker-history", "scenario.issues.reference")
    def test_component_blocker_preserves_the_reporting_owner(self):
        component = self.parent_tasks()

        def work(stage, snapshot, data, cwd):
            if stage == "context-solve":
                reporter = self.model.calls[-1]["report_issue"]
                receipt = reporter(
                    report(owner_target_id="service.transfer", evidence=[])
                )["receipt"]
                data.update(
                    outcome="spec_incomplete",
                    blockers=[{**receipt, "blocked_step": "Assess retries"}],
                )

        result = self.call("concorde-plan", component, work)
        self.assertEqual("blocked", result["status"], result)
        blocker = result["output"]["data"]["blockers"][0]
        receipt = {key: blocker[key] for key in ("issue_id", "report_id", "path")}
        observed = resolve_report(self.root, receipt)
        self.assertEqual("service.transfer", observed["source"]["target_id"])
        self.assertEqual("service.transfer", observed["report"]["owner_target_id"])
        self.assertEqual(
            "scope.bank", read_change(self.root, required=True)["target_id"]
        )
        self.assertFalse(
            any(call["stage"] == "implementation" for call in self.model.calls)
        )
