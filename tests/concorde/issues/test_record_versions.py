"""Historical Issue observations are readable evidence, not writable current records."""

import json
import tempfile
import unittest
from pathlib import Path

from concorde.issues.store import (
    dispose_issue,
    list_issues,
    read_issue,
    report_issue,
    resolve_report,
)
from concorde.spec.repository import SpecError, digest
from concorde.spec.typed_data import TypedDataError
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import report, source


class IssueRecordVersionTests(unittest.TestCase):
    @verifies("scenario.issues.historical-record")
    def test_history_retains_bytes_and_receipts_but_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = report_issue(root, report(), source())
            record, _ = read_issue(root, receipt["issue_id"])
            self.assertEqual(2, record["schema_version"])
            record["schema_version"] = 1
            observation = record["reports"][0]
            provenance = observation["source"]
            provenance["capability"] = provenance.pop("operation")
            observation["id"] = digest(
                {"report": observation["report"], "source": provenance}
            )
            receipt["report_id"] = observation["id"]
            path = root / receipt["path"]
            original = (
                f"# {record['id']}\n\n```json\n"
                + json.dumps(record, indent=2)
                + "\n```\n"
            )
            path.write_text(original)
            historical, revision = read_issue(root, record["id"])
            self.assertEqual(record, historical)
            self.assertEqual(observation, resolve_report(root, receipt))
            self.assertEqual(record["id"], list_issues(root)[0]["id"])
            with self.assertRaisesRegex(SpecError, "read-only") as refusal:
                dispose_issue(
                    root,
                    record["id"],
                    revision,
                    reason="resolved",
                    note="New evidence",
                    evidence=["check"],
                    actor="host",
                )
            self.assertEqual("unsupported_issue_version", refusal.exception.code)
            with self.assertRaisesRegex(SpecError, "read-only"):
                report_issue(
                    root,
                    report(issue_id=record["id"], expected_revision=revision),
                    source(),
                )
            self.assertEqual(original, path.read_text())
            observation["report"]["title"] = "Tampered"
            path.write_text(
                f"# {record['id']}\n\n```json\n" + json.dumps(record) + "\n```\n"
            )
            with self.assertRaisesRegex(SpecError, "digest differs"):
                read_issue(root, record["id"])

    @verifies("scenario.issues.historical-record")
    def test_old_provenance_is_not_an_alias_for_new_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            provenance = source()
            provenance["capability"] = provenance.pop("operation")
            with self.assertRaises(TypedDataError):
                report_issue(root, report(), provenance)
            self.assertEqual([], list_issues(root))
