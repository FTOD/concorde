"""How an admitted request ends: lost record writes, interrupts and execution failures."""

import unittest
from unittest.mock import patch

from concorde.harness import status_store
from concorde.harness.change_worktree import ensure_change, read_change
from concorde.harness.execution_error import OperationExecutionError
from concorde.harness.host import AdmissionServices, OperationHost
from concorde.operations.catalog import declarations
from concorde.operations.dispatch import dispatch, run_operation
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE
from tests.concorde.support.worktree_project import WorktreeProject


class FinalizationTests(WorktreeProject, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.state = ensure_change(self.change, task=self.task)

    def call(self, name, data, dispatcher=dispatch):
        services = AdmissionServices(catalog=declarations(), dispatcher=dispatcher)
        return run_operation(
            name,
            CONFIGURATION,
            typed(name + "-request", data),
            host_context=OperationHost(self.change, PACKAGE, services=services),
        )

    def run_record(self, result):
        from concorde.spec.typed_data import decode

        path = self.primary / ".concorde/runs" / result["invocation_id"] / "run.json"
        return decode(path.read_text())

    @verifies("scenario.admission.state-persistence-failed")
    def test_a_lost_run_record_write_is_reported_beside_the_output(self):
        original = status_store.record_run

        def failing_finish(host, **kwargs):
            if kwargs.get("result") is not None:
                raise OSError("disk full while finishing the run record")
            return original(host, **kwargs)

        with patch.object(status_store, "record_run", failing_finish):
            result = self.call(
                "concorde-configure",
                {"action": "propose", "configuration": CONFIGURATION},
            )
        # The provider's output is kept; the run record could not be finished.
        self.assertEqual("concorde-configure-response", result["output"]["type_id"])
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual(
            ["state_persistence_failed"], [e["code"] for e in result["errors"]]
        )
        self.assertIn("disk full", result["errors"][0]["message"])

    @verifies("scenario.admission.state-persistence-failed")
    def test_a_lost_change_status_write_is_reported_beside_the_output(self):
        with patch(
            "concorde.harness.admission.progress",
            side_effect=OSError("status directory is read-only"),
        ):
            result = self.call("concorde-validate", self.task)
        # Validation ended with a non-ready outcome whose status write failed.
        self.assertEqual("concorde-validate-response", result["output"]["type_id"])
        self.assertNotIn(
            result["output"]["data"]["outcome"], {"completed", "ready", "delivered"}
        )
        self.assertNotEqual("succeeded", result["status"], result)
        codes = [e["code"] for e in result["errors"]]
        self.assertIn("state_persistence_failed", codes, result)
        # The finished run record keeps the same envelope.
        self.assertEqual(result, self.run_record(result)["result"])

    def failing(self, error):
        calls = []

        def dispatcher(request):
            calls.append(request)
            (self.change / "edit.txt").write_text("work in progress\n")
            raise error

        return calls, dispatcher

    @verifies("scenario.admission.cancelled")
    def test_an_interrupted_request_ends_as_cancelled(self):
        _, request = self.configure_request()
        calls, dispatcher = self.failing(KeyboardInterrupt())
        result = self.call("concorde-configure", request, dispatcher)
        self.assertEqual(1, len(calls))
        self.assertEqual("failed", result["status"], result)
        self.assertEqual(["execution_cancelled"], [e["code"] for e in result["errors"]])
        self.assertIsNone(result["output"])
        self.assertEqual("cancelled", read_change(self.change, required=True)["status"])
        # The candidate and its edits are kept.
        self.assertEqual("work in progress\n", (self.change / "edit.txt").read_text())
        self.assertEqual(result, self.run_record(result)["result"])

    @verifies("scenario.admission.execution-failure")
    def test_an_execution_failure_is_not_a_business_outcome(self):
        _, request = self.configure_request()
        for outcome, code, lifecycle in (
            ("failed", "execution_failed", "failed"),
            ("limit_exhausted", "execution_limit", "limit_exhausted"),
        ):
            with self.subTest(outcome=outcome):
                _, dispatcher = self.failing(
                    OperationExecutionError("the Agent call stopped", outcome=outcome)
                )
                result = self.call("concorde-configure", request, dispatcher)
                self.assertEqual("failed", result["status"], result)
                self.assertEqual([code], [e["code"] for e in result["errors"]])
                self.assertIsNone(result["output"])
                self.assertEqual(
                    lifecycle, read_change(self.change, required=True)["status"]
                )
                self.assertEqual(result, self.run_record(result)["result"])


if __name__ == "__main__":
    unittest.main()
