"""The issue store does not run agents, stop tasks, approve fixes or perform Git operations."""

from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from concorde.issues.store import (
    dispose_issue,
    list_issues,
    read_issue,
    report_issue,
    resolve_report,
)
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report, source


class IssueStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @verifies("scenario.issues.store-report")
    def test_report_is_readable_versioned_and_idempotent_without_a_change(self):
        original = report()
        receipt = report_issue(self.root, original, source())
        self.assertEqual(receipt, report_issue(self.root, original, source()))
        record, revision = read_issue(self.root, receipt["issue_id"])
        self.assertEqual("open", record["status"])
        self.assertEqual(
            [original], [observation["report"] for observation in record["reports"]]
        )
        self.assertEqual(original, resolve_report(self.root, receipt)["report"])
        self.assertEqual(revision, list_issues(self.root)[0]["revision"])
        self.assertEqual([], list_issues(self.root, target_id="module.foreign"))
        self.assertFalse((self.root / ".concorde/status").exists())
        self.assertIn(
            "Retry ownership is unspecified", (self.root / receipt["path"]).read_text()
        )

    @verifies("scenario.issues.store-report")
    def test_query_does_not_create_a_collection_and_invocations_do_not_semantically_deduplicate(
        self,
    ):
        self.assertEqual([], list_issues(self.root))
        self.assertEqual([], list(self.root.iterdir()))
        one = report_issue(self.root, report(), source())
        two = report_issue(self.root, report(), source(invocation_id="worker-2"))
        self.assertNotEqual(one["issue_id"], two["issue_id"])
        with self.assertRaisesRegex(SpecError, "different observation"):
            report_issue(self.root, report(title="Changed meaning"), source())
        self.assertEqual(2, len(list_issues(self.root)))

    @verifies("scenario.issues.store-report")
    def test_append_binds_current_bytes_preserves_observations_and_can_reclassify(self):
        first = report_issue(self.root, report(), source())
        _, revision = read_issue(self.root, first["issue_id"])
        update = report(
            issue_id=first["issue_id"],
            expected_revision=revision,
            report_key="found-promise",
            type="bug",
            subtype=None,
            description="Implementation loses a specified retry.",
        )
        second = report_issue(self.root, update, source(invocation_id="worker-2"))
        self.assertEqual(first["issue_id"], second["issue_id"])
        self.assertNotEqual(first["report_id"], second["report_id"])
        self.assertEqual(
            second, report_issue(self.root, update, source(invocation_id="worker-2"))
        )
        self.assertEqual("gap", resolve_report(self.root, first)["report"]["type"])
        self.assertEqual("bug", list_issues(self.root)[0]["type"])
        with self.assertRaisesRegex(SpecError, "changed before"):
            report_issue(
                self.root,
                {**update, "report_key": "another"},
                source(invocation_id="worker-3"),
            )

    @verifies("scenario.issues.store-concurrency")
    def test_parallel_reports_and_duplicate_retries_are_not_lost(self):
        def create(index):
            return report_issue(self.root, report(report_key=str(index)), source())

        with ThreadPoolExecutor(max_workers=8) as pool:
            receipts = list(pool.map(create, list(range(16)) * 3))
        self.assertEqual(16, len({item["issue_id"] for item in receipts}))
        self.assertEqual(16, len(list_issues(self.root)))
        self.assertTrue(
            all(
                len(read_issue(self.root, row["id"])[0]["reports"]) == 1
                for row in list_issues(self.root)
            )
        )

    @verifies("scenario.issues.store-disposition")
    def test_disposition_retains_record_and_requires_current_evidence(self):
        receipt = report_issue(self.root, report(), source())
        identifier = receipt["issue_id"]
        original, revision = read_issue(self.root, identifier)
        with self.assertRaises(TypedDataError):
            dispose_issue(
                self.root,
                identifier,
                revision,
                reason="resolved",
                note="Fixed",
                evidence=[],
                actor="host",
            )
        closed = dispose_issue(
            self.root,
            identifier,
            revision,
            reason="resolved",
            note="Verified in this branch",
            evidence=["verification: current check and independent review"],
            actor="solve",
        )
        record, current = read_issue(self.root, identifier)
        self.assertEqual(closed, current)
        self.assertEqual("closed", record["status"])
        self.assertEqual(original["reports"], record["reports"])
        self.assertEqual(receipt, report_issue(self.root, report(), source()))
        with self.assertRaisesRegex(SpecError, "changed before disposition"):
            dispose_issue(
                self.root,
                identifier,
                revision,
                reason="reopened",
                note="New evidence",
                evidence=["regression"],
                actor="solve",
            )
        dispose_issue(
            self.root,
            identifier,
            current,
            reason="reopened",
            note="New evidence",
            evidence=["regression"],
            actor="solve",
        )
        self.assertEqual("open", read_issue(self.root, identifier)[0]["status"])
        self.assertEqual(
            original["reports"], read_issue(self.root, identifier)[0]["reports"]
        )

    @verifies("scenario.issues.store-disposition")
    def test_duplicate_requires_another_existing_open_issue(self):
        first = report_issue(self.root, report(), source())
        second = report_issue(self.root, report(), source(invocation_id="worker-2"))
        identifier = second["issue_id"]
        _, revision = read_issue(self.root, identifier)
        with self.assertRaises(SpecError):
            dispose_issue(
                self.root,
                identifier,
                revision,
                reason="duplicate",
                note="Same issue",
                evidence=["comparison"],
                actor="solve",
                duplicate_of=identifier,
            )
        dispose_issue(
            self.root,
            identifier,
            revision,
            reason="duplicate",
            note="Same issue",
            evidence=["comparison"],
            actor="solve",
            duplicate_of=first["issue_id"],
        )
        self.assertEqual(
            first["issue_id"],
            read_issue(self.root, identifier)[0]["dispositions"][-1]["duplicate_of"],
        )

    @verifies("scenario.issues.store-disposition")
    def test_duplicate_target_revision_is_checked_inside_the_transaction(self):
        first = report_issue(self.root, report(), source())
        second = report_issue(self.root, report(), source(invocation_id="second"))
        _, first_revision = read_issue(self.root, first["issue_id"])
        _, second_revision = read_issue(self.root, second["issue_id"])
        report_issue(
            self.root,
            report(
                report_key="new-evidence",
                issue_id=first["issue_id"],
                expected_revision=first_revision,
            ),
            source(invocation_id="update"),
        )
        with self.assertRaisesRegex(SpecError, "duplicate target changed"):
            dispose_issue(
                self.root,
                second["issue_id"],
                second_revision,
                reason="duplicate",
                note="Earlier comparison",
                evidence=["comparison"],
                actor="solve",
                duplicate_of=first["issue_id"],
                duplicate_revision=first_revision,
            )
        self.assertEqual("open", read_issue(self.root, second["issue_id"])[0]["status"])

    @verifies("scenario.issues.store-boundary")
    def test_invalid_reports_and_symlinks_never_write_an_issue(self):
        for changes in (
            {"type": "bug"},
            {"subtype": None},
            {"type": "todo"},
            {"title": " "},
            {"unexpected": "field"},
            {"description": "x" * 65536},
            {"evidence": [{"path": "../outside", "description": "escape"}]},
            {"issue_id": "I-" + "a" * 32},
        ):
            with (
                self.subTest(changes=list(changes)),
                self.assertRaises((SpecError, TypedDataError)),
            ):
                report_issue(self.root, report(**changes), source())
        self.assertEqual([], list_issues(self.root))
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".concorde").mkdir(exist_ok=True)
        (self.root / ".concorde/issues").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(TypedDataError):
            report_issue(self.root, report(), source())
        self.assertEqual([], list(outside.iterdir()))

    @verifies("scenario.issues.store-boundary")
    def test_changed_record_and_failed_publish_are_not_accepted(self):
        receipt = report_issue(self.root, report(), source())
        path = self.root / receipt["path"]
        original = path.read_bytes()
        with (
            patch(
                "concorde.issues.store.apply_files", side_effect=OSError("disk full")
            ),
            self.assertRaisesRegex(OSError, "disk full"),
        ):
            report_issue(self.root, report(report_key="new"), source())
        self.assertEqual(1, len(list_issues(self.root)))
        path.write_text(
            path.read_text().replace("Retry ownership", "Changed ownership")
        )
        with self.assertRaisesRegex(SpecError, "digest differs"):
            read_issue(self.root, receipt["issue_id"])
        path.write_bytes(original)
        malformed = {**receipt, "path": ".concorde/issues/foreign.md"}
        with self.assertRaisesRegex(SpecError, "path differs"):
            resolve_report(self.root, malformed)

    @verifies("scenario.issues.store-concurrency")
    def test_git_style_branch_copies_have_independent_dispositions(self):
        import shutil

        receipt = report_issue(self.root, report(), source())
        with tempfile.TemporaryDirectory() as other:
            branch = Path(other)
            shutil.copytree(self.root / ".concorde/issues", branch / ".concorde/issues")
            _, revision = read_issue(branch, receipt["issue_id"])
            dispose_issue(
                branch,
                receipt["issue_id"],
                revision,
                reason="not-actionable",
                note="Contract permits the behavior",
                evidence=["contract"],
                actor="solve",
            )
            self.assertEqual(
                "closed", read_issue(branch, receipt["issue_id"])[0]["status"]
            )
            self.assertEqual(
                "open", read_issue(self.root, receipt["issue_id"])[0]["status"]
            )
