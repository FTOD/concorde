"""Reports made through a real native Agent call's ``report_issue`` service, without a model."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.native_driver import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.issues.store import (
    list_issues,
    read_issue,
    report_issue,
    resolve_report,
)
from concorde.operations.dispatch import services
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report, source
from tests.concorde.support.spec_project import PACKAGE, project


class WorkerReportTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        project(self.root)
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.root)
        runtime = patch(
            "concorde.harness.native_driver.admit_native_runtime",
            return_value=NativeRuntimeBinding(
                FORMAT, str(self.root), "sha256:" + "0" * 64
            ),
        )
        runtime.start()
        self.addCleanup(runtime.stop)
        self.services = services()
        self.prepared = execute(
            PACKAGE,
            "prepare",
            {
                "invocation": {
                    "type_id": "concorde-operation-invocation",
                    "schema_version": 3,
                    "operation_id": "concorde-context-solve",
                    "mode": "execute",
                    "configuration": None,
                    "input": typed(
                        "concorde-context-solve-request",
                        {"target_id": "service.transfer", "task": "Assess transfer"},
                    ),
                },
                "native_root": str(self.root),
                "session_id": "unit",
            },
            services=self.services,
        )
        self.assertEqual("prepared", self.prepared["state"], self.prepared)
        self.descriptor = json.loads(Path(self.prepared["descriptor"]).read_text())

    def command(self, action, payload):
        return execute(
            PACKAGE,
            action,
            payload,
            self.prepared["descriptor"],
            self.prepared["digest"],
            services=self.services,
        )

    def report(self, key):
        return report(
            report_key=key,
            type="bug",
            subtype=None,
            owner_target_id="service.transfer",
            evidence=[{"path": "specs/transfer/module.md", "description": "Contract"}],
        )

    def proposal(self, **changes):
        return {
            "invocation_id": self.prepared["ticket"],
            "result": typed(
                "concorde-agent-stage-result",
                {
                    "context_id": self.descriptor["snapshot"]["context_id"],
                    "outcome": "sufficient",
                    "answer": "Sufficient",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                    **changes,
                },
            ),
        }

    @verifies("scenario.issues.report-independent")
    def test_reports_are_acknowledged_and_the_call_still_completes_on_its_own(self):
        receipts = []
        for key in ("first", "second"):
            reply = self.command("report", self.report(key))
            receipts.append(reply["receipt"])
            # Acknowledged only after the record is on disk; the call stays open.
            self.assertEqual(
                reply["revision"],
                read_issue(self.root, reply["receipt"]["issue_id"])[1],
            )
            self.assertEqual("prepared", self.command("check", {})["state"])
        self.assertEqual(2, len(list_issues(self.root)))
        self.assertEqual("proposed", self.command("submit", self.proposal())["state"])
        staged = self.command("stage", {})
        self.assertEqual("staged", staged["state"], staged)
        proposal = json.loads(
            (Path(self.descriptor["directory"]) / "proposal.json").read_text()
        )
        self.assertEqual("sufficient", proposal["result"]["data"]["outcome"])
        # Reporting started no repair and changed no task state or other file.
        self.assertFalse((self.root / ".concorde/status").exists())
        for receipt in receipts:
            self.assertEqual(
                "open", read_issue(self.root, receipt["issue_id"])[0]["status"]
            )
            self.assertEqual(
                1, len(read_issue(self.root, receipt["issue_id"])[0]["reports"])
            )

    @verifies("scenario.issues.report-survives-failure")
    def test_a_report_survives_an_invalid_result_and_a_cancelled_call(self):
        reply = self.command("report", self.report("kept"))
        receipt = reply["receipt"]
        refused = self.command("submit", self.proposal(context_id="sha256:" + "f" * 64))
        self.assertEqual("rejected", refused["state"], refused)
        self.assertEqual("rejected", self.command("stage", {})["state"])
        self.command("invalidate", {"reason": "cancelled by the host"})
        observation = resolve_report(self.root, receipt)
        self.assertEqual("kept", observation["report"]["report_key"])
        self.assertEqual(
            [receipt["issue_id"]], [row["id"] for row in list_issues(self.root)]
        )

    def blocked(self, *receipts):
        return self.proposal(
            outcome="spec_incomplete",
            answer="Blocked by the reported problem",
            blockers=[{**receipt, "blocked_step": "Assess"} for receipt in receipts],
        )

    def refusal(self, proposal):
        refused = self.command("submit", proposal)
        self.assertEqual("rejected", refused["state"], refused)
        return refused["result"]["errors"][0]["code"]

    @verifies("scenario.issues.reference")
    def test_a_result_cannot_reference_a_report_it_neither_made_nor_received(self):
        own = self.command("report", self.report("own"))["receipt"]
        foreign = report_issue(
            self.root,
            self.report("foreign"),
            source(invocation_id="another-call", target_id="service.transfer"),
        )
        self.assertEqual("permission_denied", self.refusal(self.blocked(own, foreign)))
        # The reports already saved are kept.
        self.assertEqual("own", resolve_report(self.root, own)["report"]["report_key"])
        self.assertEqual(2, len(list_issues(self.root)))

    @verifies("scenario.issues.reference-repeated")
    def test_a_result_cannot_reference_one_report_twice(self):
        own = self.command("report", self.report("own"))["receipt"]
        self.assertEqual("invalid_completion", self.refusal(self.blocked(own, own)))
        self.assertEqual("own", resolve_report(self.root, own)["report"]["report_key"])

    def test_a_result_may_reference_its_own_report_once(self):
        own = self.command("report", self.report("own"))["receipt"]
        self.assertEqual("proposed", self.command("submit", self.blocked(own))["state"])


if __name__ == "__main__":
    unittest.main()
