"""The issue store does not run agents, stop tasks, approve fixes or perform Git operations."""

from __future__ import annotations

import errno
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from concorde.issues.store import (
    IssueError,
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


@contextmanager
def refused_record_writes():
    """The operating system refuses to replace any Issue record, even for root."""
    replace = os.replace

    def refusing(source_path, target, *args, **kwargs):
        if "/.concorde/issues/" in str(target):
            raise OSError(errno.EROFS, "Read-only file system", str(target))
        return replace(source_path, target, *args, **kwargs)

    with patch("concorde.spec.changes.os.replace", side_effect=refusing):
        yield


@contextmanager
def racing_writer():
    """Another program changes the record after the store read it and before it publishes;
    yields the list of bytes that program left."""
    from concorde.issues import store

    publish = store.apply_files
    left = []

    def racing(root, changes, allowed, **kwargs):
        target = Path(root) / changes[0]["path"]
        target.write_bytes(target.read_bytes() + b"\n")
        left.append(target.read_bytes())
        return publish(root, changes, allowed, **kwargs)

    with patch("concorde.issues.store.apply_files", side_effect=racing):
        yield left


class IssueStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def issue_files(self):
        directory = self.root / ".concorde/issues"
        if not directory.is_dir():
            return {}
        return {path.name: path.read_bytes() for path in directory.iterdir()}

    def close(self, identifier, revision, **changes):
        arguments = {
            "reason": "resolved",
            "note": "Verified in this branch",
            "evidence": ["verification: current check and independent review"],
            "actor": "solve",
            **changes,
        }
        return dispose_issue(self.root, identifier, revision, **arguments)

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

    @verifies("scenario.issues.store-empty")
    def test_listing_without_issues_creates_nothing(self):
        self.assertEqual([], list_issues(self.root))
        self.assertEqual([], list(self.root.iterdir()))

    @verifies("scenario.issues.store-key-conflict")
    def test_a_reused_key_with_other_content_is_refused(self):
        one = report_issue(self.root, report(), source())
        two = report_issue(self.root, report(), source(invocation_id="worker-2"))
        self.assertNotEqual(one["issue_id"], two["issue_id"])
        before = self.issue_files()
        with self.assertRaisesRegex(IssueError, "different observation") as raised:
            report_issue(self.root, report(title="Changed meaning"), source())
        self.assertEqual("issue_key_conflict", raised.exception.code)
        self.assertEqual(before, self.issue_files())
        self.assertEqual(report(), resolve_report(self.root, one)["report"])

    @verifies("scenario.issues.store-append")
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
        self.assertEqual(report(), resolve_report(self.root, first)["report"])
        self.assertEqual(2, len(read_issue(self.root, first["issue_id"])[0]["reports"]))
        self.assertEqual("bug", list_issues(self.root)[0]["type"])

    @verifies("scenario.issues.store-append-stale")
    def test_an_append_at_an_old_revision_is_refused(self):
        first = report_issue(self.root, report(), source())
        identifier = first["issue_id"]
        _, old = read_issue(self.root, identifier)
        later = report(report_key="later", issue_id=identifier, expected_revision=old)
        report_issue(self.root, later, source(invocation_id="worker-2"))
        _, current = read_issue(self.root, identifier)
        before = self.issue_files()
        with self.assertRaisesRegex(IssueError, "changed before") as raised:
            report_issue(
                self.root,
                {**later, "report_key": "another"},
                source(invocation_id="worker-3"),
            )
        self.assertEqual("stale_issue", raised.exception.code)
        for fragment in (identifier, old, current):
            self.assertIn(fragment, str(raised.exception))
        self.assertEqual(before, self.issue_files())

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
    def test_a_closing_disposition_keeps_every_report(self):
        receipt = report_issue(self.root, report(), source())
        identifier = receipt["issue_id"]
        original, revision = read_issue(self.root, identifier)
        closed = self.close(identifier, revision)
        record, current = read_issue(self.root, identifier)
        self.assertEqual(closed, current)
        self.assertEqual("closed", record["status"])
        self.assertEqual(
            ("resolved", "solve"),
            (record["dispositions"][0]["reason"], record["dispositions"][0]["actor"]),
        )
        self.assertEqual(original["reports"], record["reports"])
        self.assertEqual(receipt, report_issue(self.root, report(), source()))

    @verifies("scenario.issues.store-disposition-duplicate")
    def test_a_duplicate_names_another_open_issue(self):
        first = report_issue(self.root, report(), source())
        second = report_issue(self.root, report(), source(invocation_id="worker-2"))
        identifier = second["issue_id"]
        _, revision = read_issue(self.root, identifier)
        self.close(
            identifier, revision, reason="duplicate", duplicate_of=first["issue_id"]
        )
        record, _ = read_issue(self.root, identifier)
        self.assertEqual("closed", record["status"])
        self.assertEqual(first["issue_id"], record["dispositions"][-1]["duplicate_of"])
        self.assertEqual("open", read_issue(self.root, first["issue_id"])[0]["status"])

    @verifies("scenario.issues.store-reopen")
    def test_reopening_at_the_current_revision_opens_the_issue(self):
        identifier = report_issue(self.root, report(), source())["issue_id"]
        original, revision = read_issue(self.root, identifier)
        closed = self.close(identifier, revision)
        dispose_issue(
            self.root,
            identifier,
            closed,
            reason="reopened",
            note="New evidence",
            evidence=["regression"],
            actor="solve",
        )
        record, _ = read_issue(self.root, identifier)
        self.assertEqual("open", record["status"])
        self.assertEqual(original["reports"], record["reports"])

    @verifies("scenario.issues.store-disposition-stale")
    def test_a_disposition_at_an_old_revision_is_refused(self):
        identifier = report_issue(self.root, report(), source())["issue_id"]
        _, old = read_issue(self.root, identifier)
        current = self.close(identifier, old)
        before = self.issue_files()
        with self.assertRaisesRegex(IssueError, "changed before disposition") as raised:
            dispose_issue(
                self.root,
                identifier,
                old,
                reason="reopened",
                note="New evidence",
                evidence=["regression"],
                actor="solve",
            )
        self.assertEqual("stale_issue", raised.exception.code)
        for fragment in (identifier, old, current):
            self.assertIn(fragment, str(raised.exception))
        self.assertEqual(before, self.issue_files())

    @verifies("scenario.issues.store-duplicate-stale")
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
        _, first_current = read_issue(self.root, first["issue_id"])
        before = self.issue_files()
        with self.assertRaisesRegex(SpecError, "duplicate target changed") as raised:
            self.close(
                second["issue_id"],
                second_revision,
                reason="duplicate",
                duplicate_of=first["issue_id"],
                duplicate_revision=first_revision,
            )
        self.assertEqual("stale_issue", raised.exception.code)
        for fragment in (first["issue_id"], first_revision, first_current):
            self.assertIn(fragment, str(raised.exception))
        self.assertEqual("open", read_issue(self.root, second["issue_id"])[0]["status"])
        self.assertEqual(before, self.issue_files())

    @verifies("scenario.issues.store-disposition-invalid")
    def test_a_disposition_without_evidence_is_refused(self):
        identifier = report_issue(self.root, report(), source())["issue_id"]
        _, revision = read_issue(self.root, identifier)
        before = self.issue_files()
        with self.assertRaises(TypedDataError) as raised:
            self.close(identifier, revision, evidence=[])
        self.assertEqual("invalid_field", raised.exception.code)
        self.assertEqual("/dispositions/0/evidence", raised.exception.field)
        self.assertEqual(before, self.issue_files())

    @verifies("scenario.issues.store-self-duplicate")
    def test_an_issue_cannot_be_its_own_duplicate(self):
        identifier = report_issue(self.root, report(), source())["issue_id"]
        _, revision = read_issue(self.root, identifier)
        before = self.issue_files()
        with self.assertRaisesRegex(IssueError, "duplicate of itself") as raised:
            self.close(
                identifier, revision, reason="duplicate", duplicate_of=identifier
            )
        self.assertEqual("invalid_issue", raised.exception.code)
        self.assertIn(identifier, str(raised.exception))
        self.assertEqual(before, self.issue_files())

    @verifies("scenario.issues.store-boundary")
    def test_a_report_that_breaks_the_report_schema_is_refused(self):
        for changes, field in (
            ({"type": "todo"}, "/type"),
            ({"title": " "}, "/title"),
            ({"unexpected": "field"}, "/unexpected"),
        ):
            with (
                self.subTest(field=field),
                self.assertRaises(TypedDataError) as raised,
            ):
                report_issue(self.root, report(**changes), source())
            self.assertEqual(
                ("invalid_field", field),
                (raised.exception.code, raised.exception.field),
            )
        self.assertEqual({}, self.issue_files())

    @verifies("scenario.issues.store-report-inconsistent")
    def test_a_report_that_breaks_an_issue_rule_is_refused(self):
        for changes, rule in (
            ({"type": "bug"}, "subtype"),
            ({"subtype": None}, "subtype"),
            ({"issue_id": "I-" + "a" * 32}, "expected_revision"),
            ({"description": "x" * 65536}, "64 KiB"),
        ):
            with (
                self.subTest(changes=list(changes)),
                self.assertRaisesRegex(IssueError, rule) as raised,
            ):
                report_issue(self.root, report(**changes), source())
            self.assertEqual("invalid_issue", raised.exception.code)
        self.assertEqual({}, self.issue_files())

    @verifies("scenario.issues.store-unsafe-evidence-path")
    def test_an_evidence_path_outside_the_project_is_refused(self):
        for path in ("../outside", "/etc/passwd", "specs/./module.md", "a\\b"):
            with (
                self.subTest(path=path),
                self.assertRaises(TypedDataError) as raised,
            ):
                report_issue(
                    self.root,
                    report(evidence=[{"path": path, "description": "escape"}]),
                    source(),
                )
            self.assertEqual(
                ("invalid_field", "/evidence/0/path"),
                (raised.exception.code, raised.exception.field),
            )
        self.assertEqual({}, self.issue_files())

    @verifies("scenario.issues.store-symlinked-directory")
    def test_a_symlinked_issue_directory_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".concorde").mkdir()
        (self.root / ".concorde/issues").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(TypedDataError, "symlink") as raised:
            report_issue(self.root, report(), source())
        self.assertEqual("invalid_field", raised.exception.code)
        self.assertEqual([], list(outside.iterdir()))

    @verifies("scenario.issues.store-corrupted-record")
    def test_a_record_whose_report_no_longer_matches_its_digest_is_refused(self):
        receipt = report_issue(self.root, report(), source())
        path = self.root / receipt["path"]
        path.write_text(
            path.read_text().replace("Retry ownership", "Changed ownership")
        )
        corrupted = path.read_bytes()
        with self.assertRaisesRegex(IssueError, "digest differs") as raised:
            read_issue(self.root, receipt["issue_id"])
        self.assertEqual("invalid_issue", raised.exception.code)
        self.assertIn(receipt["issue_id"], str(raised.exception))
        self.assertEqual(corrupted, path.read_bytes())

    @verifies("scenario.issues.store-failed-publication")
    def test_a_refused_record_write_returns_no_receipt(self):
        receipt = report_issue(self.root, report(), source())
        before = self.issue_files()
        with refused_record_writes(), self.assertRaises(SpecError) as raised:
            report_issue(self.root, report(report_key="new"), source())
        self.assertEqual("system_error", raised.exception.code)
        self.assertEqual(before, self.issue_files())
        self.assertEqual(report(), resolve_report(self.root, receipt)["report"])

    @verifies("scenario.issues.store-failed-publication")
    def test_a_read_only_issue_directory_returns_no_receipt(self):
        if os.geteuid() == 0:
            self.skipTest("root writes into a read-only directory")
        receipt = report_issue(self.root, report(), source())
        before = self.issue_files()
        directory = self.root / ".concorde/issues"
        directory.chmod(0o555)
        self.addCleanup(directory.chmod, 0o755)
        with self.assertRaises(SpecError) as raised:
            report_issue(self.root, report(report_key="new"), source())
        self.assertEqual("system_error", raised.exception.code)
        directory.chmod(0o755)
        self.assertEqual(before, self.issue_files())
        self.assertEqual(report(), resolve_report(self.root, receipt)["report"])

    @verifies("scenario.issues.store-publication-stale")
    def test_a_record_changed_during_publication_is_refused_as_stale(self):
        receipt = report_issue(self.root, report(), source())
        identifier = receipt["issue_id"]
        path = self.root / receipt["path"]
        original = path.read_bytes()
        for action in ("append", "dispose"):
            path.write_bytes(original)
            _, revision = read_issue(self.root, identifier)
            with (
                self.subTest(action=action),
                racing_writer() as left,
                self.assertRaisesRegex(IssueError, "changed while") as raised,
            ):
                if action == "append":
                    report_issue(
                        self.root,
                        report(
                            report_key="later",
                            issue_id=identifier,
                            expected_revision=revision,
                        ),
                        source(invocation_id="worker-2"),
                    )
                else:
                    self.close(identifier, revision)
            self.assertEqual("stale_issue", raised.exception.code)
            self.assertIn(identifier, str(raised.exception))
            self.assertEqual(left[-1], path.read_bytes())

    def test_a_receipt_whose_path_is_not_its_issues_is_refused(self):
        receipt = report_issue(self.root, report(), source())
        malformed = {**receipt, "path": ".concorde/issues/foreign.md"}
        with self.assertRaisesRegex(IssueError, "path differs"):
            resolve_report(self.root, malformed)

    @verifies("scenario.issues.store-status-mismatch")
    def test_status_without_a_supporting_disposition_is_refused_without_repair(self):
        receipt = report_issue(self.root, report(), source())
        path = self.root / receipt["path"]
        record = path.read_text()
        self.assertIn('"status": "open"', record)
        malformed = record.replace('"status": "open"', '"status": "closed"', 1)
        path.write_text(malformed)
        with self.assertRaisesRegex(
            SpecError, "status differs from its disposition"
        ) as raised:
            read_issue(self.root, receipt["issue_id"])
        self.assertEqual("invalid_issue", raised.exception.code)
        self.assertEqual(malformed, path.read_text())

    @verifies("scenario.issues.branch-local")
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
