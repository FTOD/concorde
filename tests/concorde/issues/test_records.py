"""Issue records through the store and the reporting service, on temporary directories."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.harness.change_worktree import ensure_change, read_change
from concorde.issues.reporting import IssueReporter
from concorde.issues.store import (
    dispose_issue,
    issue_path,
    list_issues,
    read_issue,
    report_issue,
    restore_issue,
)
from concorde.planning.gaps import open_gaps, record_task_gaps
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report, source
from tests.concorde.support.spec_project import project


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class IssueRecordTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def opened(self):
        receipt = report_issue(self.root, report(), source())
        record, revision = read_issue(self.root, receipt["issue_id"])
        return receipt, record, revision

    def bytes_of(self, receipt) -> bytes:
        return (self.root / receipt["path"]).read_bytes()

    def dispose(self, identifier, revision, **changes):
        return dispose_issue(
            self.root,
            identifier,
            revision,
            **{
                "reason": "resolved",
                "note": "Verified",
                "evidence": ["verification"],
                "actor": "solve",
                **changes,
            },
        )

    @verifies("scenario.issues.report-provenance")
    def test_the_service_saves_the_caller_provenance_and_answers_receipt_and_revision(
        self,
    ):
        provenance = source(invocation_id="call-7", agent="planner", phase="plan")
        service = IssueReporter(
            self.root,
            provenance,
            frozenset({"module.service"}),
            frozenset({"specs/service/module.md"}),
        )
        reply = service(report())
        record, revision = read_issue(self.root, reply["receipt"]["issue_id"])
        self.assertEqual(provenance, record["reports"][0]["source"])
        self.assertEqual(revision, reply["revision"])
        self.assertEqual(
            {"issue_id", "report_id", "path"}, set(reply["receipt"]), reply
        )
        self.assertEqual(issue_path(record["id"]), reply["receipt"]["path"])
        self.assertEqual(record["reports"][0]["id"], reply["receipt"]["report_id"])

    @verifies("scenario.issues.store-append")
    def test_a_later_observation_is_appended_and_the_first_stays_unchanged(self):
        receipt, record, revision = self.opened()
        first = record["reports"][0]
        later = report(
            report_key="later",
            issue_id=receipt["issue_id"],
            expected_revision=revision,
            type="limitation",
            subtype=None,
            description="The retry limit is also undocumented.",
        )
        appended = report_issue(self.root, later, source(invocation_id="worker-2"))
        self.assertEqual(receipt["issue_id"], appended["issue_id"])
        record, _ = read_issue(self.root, receipt["issue_id"])
        self.assertEqual(2, len(record["reports"]))
        self.assertEqual(first, record["reports"][0])
        self.assertEqual("limitation", record["reports"][1]["report"]["type"])

    @verifies("scenario.issues.store-key-conflict")
    def test_a_reused_key_with_other_content_is_refused(self):
        receipt, _, _ = self.opened()
        before = self.bytes_of(receipt)
        with self.assertRaises(SpecError) as refused:
            report_issue(self.root, report(title="Another meaning"), source())
        self.assertEqual("issue_key_conflict", refused.exception.code)
        self.assertEqual(before, self.bytes_of(receipt))

    @verifies("scenario.issues.store-empty")
    def test_listing_without_issues_creates_nothing(self):
        self.assertEqual([], list_issues(self.root))
        self.assertEqual([], list_issues(self.root, status="open"))
        self.assertFalse((self.root / ".concorde").exists())

    @verifies("scenario.issues.store-disposition-stale")
    def test_a_disposition_over_a_changed_record_is_refused(self):
        receipt, _, revision = self.opened()
        report_issue(
            self.root,
            report(
                report_key="later",
                issue_id=receipt["issue_id"],
                expected_revision=revision,
            ),
            source(invocation_id="worker-2"),
        )
        changed = self.bytes_of(receipt)
        with self.assertRaises(SpecError) as refused:
            self.dispose(receipt["issue_id"], revision)
        self.assertEqual("stale_issue", refused.exception.code)
        self.assertEqual(changed, self.bytes_of(receipt))

    @verifies("scenario.issues.store-disposition-invalid")
    def test_invalid_dispositions_are_refused_without_writing(self):
        receipt, _, revision = self.opened()
        other = report_issue(self.root, report(), source(invocation_id="other"))
        _, other_revision = read_issue(self.root, other["issue_id"])
        self.dispose(other["issue_id"], other_revision, reason="not-actionable")
        identifier = receipt["issue_id"]
        before = self.bytes_of(receipt)
        for changes in (
            {"evidence": []},
            {"reason": "duplicate", "duplicate_of": identifier},
            {"reason": "duplicate", "duplicate_of": other["issue_id"]},
            {"reason": "duplicate", "duplicate_of": None},
            {"reason": "reopened"},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaises((SpecError, TypedDataError)),
            ):
                self.dispose(identifier, revision, **changes)
            self.assertEqual(before, self.bytes_of(receipt))
        closed = self.dispose(identifier, revision)
        closed_bytes = self.bytes_of(receipt)
        with self.assertRaises(SpecError):
            self.dispose(identifier, closed, reason="not-actionable")
        self.assertEqual(closed_bytes, self.bytes_of(receipt))

    @verifies("scenario.issues.store-restore")
    def test_restoring_the_open_bytes_is_exact_and_idempotent(self):
        receipt, _, revision = self.opened()
        original = self.bytes_of(receipt)
        closed = self.dispose(receipt["issue_id"], revision)
        restore_issue(self.root, receipt["issue_id"], original, closed)
        self.assertEqual(original, self.bytes_of(receipt))
        self.assertEqual(revision, read_issue(self.root, receipt["issue_id"])[1])
        restore_issue(self.root, receipt["issue_id"], original, closed)
        self.assertEqual(original, self.bytes_of(receipt))

    @verifies("scenario.issues.store-restore-stale")
    def test_restoring_over_other_bytes_is_refused(self):
        receipt, _, revision = self.opened()
        original = self.bytes_of(receipt)
        closed = self.dispose(receipt["issue_id"], revision)
        reopened = self.dispose(
            receipt["issue_id"], closed, reason="reopened", evidence=["regression"]
        )
        self.dispose(receipt["issue_id"], reopened, reason="not-actionable")
        current = self.bytes_of(receipt)
        with self.assertRaises(SpecError) as refused:
            restore_issue(self.root, receipt["issue_id"], original, closed)
        self.assertEqual("stale_issue", refused.exception.code)
        self.assertEqual(current, self.bytes_of(receipt))

    @verifies("scenario.issues.unknown-owner-listed")
    def test_an_issue_of_an_unregistered_owner_is_listed_and_read(self):
        project(self.root)
        receipt = report_issue(
            self.root,
            report(owner_target_id="module.removed"),
            source(target_id="module.removed"),
        )
        record, revision = read_issue(self.root, receipt["issue_id"])
        self.assertEqual(
            "module.removed", record["reports"][0]["report"]["owner_target_id"]
        )
        rows = list_issues(self.root)
        self.assertEqual([receipt["issue_id"]], [row["id"] for row in rows])
        self.assertEqual("module.removed", rows[0]["owner_target_id"])
        self.assertEqual(revision, rows[0]["revision"])
        self.assertEqual(rows, list_issues(self.root, target_id="module.removed"))


class BlockerIndependenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    @verifies("scenario.issues.blocker-independent")
    def test_closing_an_issue_changes_only_its_record_and_keeps_the_blocker(self):
        receipt = report_issue(
            self.root,
            report(owner_target_id="service.transfer", evidence=[]),
            source(target_id="service.transfer"),
        )
        ensure_change(self.root, allow_primary=True)
        record_task_gaps(
            self.root,
            "service.transfer",
            "Implement transfer",
            "plan",
            [{**receipt, "blocked_step": "Implement transfer"}],
            "context",
            scope_id="module:service.transfer",
        )
        change = read_change(self.root, required=True)
        self.assertEqual(1, len(open_gaps(change)))
        files = {
            path: path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and ".concorde/runs" not in str(path)
        }
        _, revision = read_issue(self.root, receipt["issue_id"])
        dispose_issue(
            self.root,
            receipt["issue_id"],
            revision,
            reason="resolved",
            note="Fixed",
            evidence=["verification"],
            actor="solve",
        )
        changed = {
            path
            for path, content in files.items()
            if not path.exists() or path.read_bytes() != content
        }
        self.assertEqual({self.root / receipt["path"]}, changed)
        self.assertEqual(change, read_change(self.root, required=True))
        self.assertEqual(open_gaps(change), open_gaps(read_change(self.root)))


class BranchLocalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.primary = Path(temporary.name) / "primary"
        self.primary.mkdir()
        git(self.primary, "init", "-q", "-b", "main")
        git(self.primary, "config", "user.email", "fixture@example.invalid")
        git(self.primary, "config", "user.name", "Fixture")
        (self.primary / ".gitignore").write_text(".concorde/runs/\n")
        self.receipt = report_issue(self.primary, report(), source())
        git(self.primary, "add", "-A")
        git(self.primary, "commit", "-qm", "Issue")
        self.candidate = Path(temporary.name) / "candidate"
        git(
            self.primary,
            "worktree",
            "add",
            "-q",
            "-b",
            "candidate",
            str(self.candidate),
        )

    @verifies("scenario.issues.branch-local")
    def test_closing_in_a_candidate_leaves_the_primary_copy_open_until_merge(self):
        identifier = self.receipt["issue_id"]
        _, revision = read_issue(self.candidate, identifier)
        dispose_issue(
            self.candidate,
            identifier,
            revision,
            reason="not-actionable",
            note="The contract permits it",
            evidence=["contract"],
            actor="solve",
        )
        self.assertEqual("closed", read_issue(self.candidate, identifier)[0]["status"])
        self.assertEqual("open", read_issue(self.primary, identifier)[0]["status"])
        # The store lock lives in the primary worktree's run records, not the candidate's.
        self.assertTrue((self.primary / ".concorde/runs/issues.lock").exists())
        self.assertFalse((self.candidate / ".concorde/runs").exists())
        git(self.candidate, "commit", "-qam", "Close the Issue")
        self.assertEqual("open", read_issue(self.primary, identifier)[0]["status"])
        git(self.primary, "merge", "-q", "--ff-only", "candidate")
        self.assertEqual("closed", read_issue(self.primary, identifier)[0]["status"])


if __name__ == "__main__":
    unittest.main()
