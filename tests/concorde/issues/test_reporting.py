"""Report authority stays separate from file writes, stage outcomes and final completion."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from concorde.issues.reporting import IssueReporter
from concorde.issues.store import list_issues, read_issue
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report, source


class ReportingBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.reporter = IssueReporter(
            self.root,
            source(),
            frozenset({"module.service", "module.provider"}),
            frozenset({"specs/service/module.md"}),
        )

    @verifies(
        "scenario.issues.report-unknown-owner", "scenario.issues.report-authority"
    )
    def test_unknown_owner_is_honest_but_foreign_owners_paths_and_forged_provenance_are_refused(
        self,
    ):
        self.reporter(report(owner_target_id=None))
        self.reporter(report(report_key="provider", owner_target_id="module.provider"))
        for changes in (
            {"owner_target_id": "module.foreign"},
            {"source": source()},
            {"evidence": [{"path": "secret.py", "description": "Not admitted"}]},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaises((SpecError, TypedDataError)),
            ):
                self.reporter(report(report_key="invalid", **changes))
        self.assertEqual(2, len(self.reporter.receipts))
        self.assertEqual(2, len(list_issues(self.root)))
        self.assertFalse((self.root / ".concorde/status").exists())

    @verifies("scenario.issues.report-authority", "scenario.issues.report-append")
    def test_reporter_cannot_append_to_an_issue_it_was_not_granted(self):
        first = self.reporter(report())["receipt"]
        _, revision = read_issue(self.root, first["issue_id"])
        another = IssueReporter(
            self.root,
            source(invocation_id="other"),
            self.reporter.admitted_owners,
            self.reporter.evidence_paths,
        )
        with self.assertRaisesRegex(SpecError, "not admitted"):
            another(report(issue_id=first["issue_id"], expected_revision=revision))
        admitted = IssueReporter(
            self.root,
            source(invocation_id="other"),
            self.reporter.admitted_owners,
            self.reporter.evidence_paths,
            selected_issues=frozenset({first["issue_id"]}),
        )
        reply = admitted(report(issue_id=first["issue_id"], expected_revision=revision))
        self.assertEqual(first["issue_id"], reply["receipt"]["issue_id"])
        self.assertEqual(read_issue(self.root, first["issue_id"])[1], reply["revision"])
