"""Report authority stays separate from file writes, stage outcomes and final completion."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.worker_executor import CapabilityExecutionError
from concorde.issues.reporting import IssueReporter
from concorde.issues.store import list_issues, read_issue
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError, typed
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import report, source
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, ModelProcessDouble, project


class ReportingBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.reporter = IssueReporter(self.root, source(), frozenset({"module.service", "module.provider"}),
                                     frozenset({"specs/service/module.md"}))

    @verifies("scenario.issues.report-authority")
    def test_unknown_owner_is_honest_but_foreign_owners_paths_and_forged_provenance_are_refused(self):
        self.reporter(report(owner_target_id=None))
        self.reporter(report(report_key="provider", owner_target_id="module.provider"))
        for changes in ({"owner_target_id": "module.foreign"}, {"source": source()},
                        {"evidence": [{"path": "secret.py", "description": "Not admitted"}]}):
            with self.subTest(changes=changes), self.assertRaises((SpecError, TypedDataError)):
                self.reporter(report(report_key="invalid", **changes))
        self.assertEqual(2, len(self.reporter.receipts))
        self.assertEqual(2, len(list_issues(self.root)))
        self.assertFalse((self.root / ".concorde/worktree.json").exists())

    @verifies("scenario.issues.report-authority")
    def test_reporter_cannot_append_to_an_issue_it_was_not_granted(self):
        first = self.reporter(report())["receipt"]
        _, revision = read_issue(self.root, first["issue_id"])
        another = IssueReporter(self.root, source(invocation_id="other"), self.reporter.admitted_owners,
                                self.reporter.evidence_paths)
        with self.assertRaisesRegex(SpecError, "not admitted"):
            another(report(issue_id=first["issue_id"], expected_revision=revision))
        admitted = IssueReporter(self.root, source(invocation_id="other"), self.reporter.admitted_owners,
            self.reporter.evidence_paths, selected_issues=frozenset({first["issue_id"]}))
        reply = admitted(report(issue_id=first["issue_id"], expected_revision=revision))
        self.assertEqual(first["issue_id"], reply["receipt"]["issue_id"])
        self.assertEqual(read_issue(self.root, first["issue_id"])[1], reply["revision"])


class ReportingIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def call(self, behavior, *, capability="concorde-plan", mode="execute"):
        def callback(stage, snapshot, data, cwd):
            if stage == "plan" or capability == "concorde-main":
                reporter = double.calls[-1]["report_issue"]
                self.assertIsNotNone(reporter)
                self.assertIn("report_issue", double.calls[-1]["launch"].tools)
                self.assertEqual((), double.calls[-1]["launch"].write_paths)
                behavior(reporter, data)
        double = ModelProcessDouble(callback)
        host = CapabilityHost(self.root, PACKAGE, mode=mode, executor=double.executor,
                              allow_primary_worktree=True, routed_target="service.transfer")
        request = {"target_id": "service.transfer", "task": "Plan transfer"}
        return run_capability(capability, CONFIGURATION, typed(capability + "-request", request), host_context=host)

    @staticmethod
    def observed(reporter, key):
        return reporter(report(report_key=key, owner_target_id=None, evidence=[]))

    @verifies("scenario.issues.report-independent")
    def test_multiple_issues_do_not_stop_or_fail_a_completed_stage(self):
        def work(reporter, data):
            self.observed(reporter, "one")
            self.observed(reporter, "two")
        result = self.call(work)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(2, len(list_issues(self.root)))
        self.assertTrue(all(item["type"] == "gap" for item in list_issues(self.root)))

    @verifies("scenario.issues.report-independent")
    def test_queries_can_report_without_acquiring_project_write_authority(self):
        result = self.call(lambda reporter, data: self.observed(reporter, "query"), capability="concorde-main")
        self.assertEqual("succeeded", result["status"], result)
        self.assertGreaterEqual(len(list_issues(self.root)), 1)
        self.assertFalse((self.root / ".concorde/worktree.json").exists())

    @verifies("scenario.issues.report-survives-failure")
    def test_failed_or_invalid_worker_completion_cannot_erase_accepted_reports(self):
        for failure in ("invalid", "cancelled", "limit_exhausted"):
            with self.subTest(failure=failure):
                before = len(list_issues(self.root))
                def work(reporter, data):
                    self.observed(reporter, failure)
                    if failure == "invalid":
                        data.pop("answer")
                    else:
                        raise CapabilityExecutionError("Interrupted after reporting",
                                                       outcome="cancelled" if failure == "cancelled" else "limit_exhausted")
                result = self.call(work)
                self.assertNotEqual("succeeded", result["status"], result)
                self.assertEqual(before + 1, len(list_issues(self.root)))

    @verifies("scenario.issues.store-boundary")
    def test_repository_validation_binds_issue_bytes_and_rejects_corruption(self):
        from concorde.spec.validation import validate_repository
        before = validate_repository(self.root)
        result = self.call(lambda reporter, data: self.observed(reporter, "validation"))
        self.assertEqual("succeeded", result["status"], result)
        after = validate_repository(self.root)
        self.assertEqual("success", after.status)
        self.assertNotEqual(before.result["source_digest"], after.result["source_digest"])
        path = next((self.root / ".concorde/issues").glob("I-*.md"))
        path.write_text(path.read_text().replace("Retry ownership", "Corrupted ownership"))
        invalid = validate_repository(self.root)
        self.assertEqual("invalid", invalid.status)
        self.assertIn("CONCORDE-ISSUE-001", [item.rule_id for item in invalid.findings])

    @verifies("scenario.issues.report-authority")
    def test_preview_never_launches_a_reporter_or_creates_an_issue(self):
        result = self.call(lambda *_: self.fail("preview launched a worker"), mode="describe-policy")
        self.assertEqual("described", result["status"], result)
        self.assertEqual([], list_issues(self.root))
        self.assertFalse((self.root / ".concorde/issues").exists())
