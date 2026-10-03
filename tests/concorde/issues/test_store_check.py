"""The configured Issue store check, run as its configured command on a fixture project."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.issues.store import dispose_issue, read_issue, report_issue
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import git_project, report, source
from tests.concorde.support.spec_project import PACKAGE, project


class StoreCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = git_project(Path(os.path.realpath(temporary.name)))
        project(self.root)
        self.check = next(
            item
            for item in json.loads(
                (PACKAGE / ".concorde/checks/module.issues.json").read_text()
            )["checks"]
            if item["id"] == "check.issues.store"
        )

    def run_check(self):
        """Run the configured argv of ``check.issues.store`` in the project directory."""
        argv = [
            sys.executable if part == "{python}" else part
            for part in self.check["argv"]
        ]
        argv[1] = str(PACKAGE / argv[1])
        result = subprocess.run(
            argv,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def orphan(self, **changes):
        return report_issue(
            self.root,
            report(owner_target_id=None, evidence=[], **changes),
            source(target_id="module.removed"),
        )

    @verifies("scenario.issues.store-check-pass")
    def test_valid_records_and_an_absent_directory_pass(self):
        self.assertEqual((0, {"errors": [], "notes": []}), self.run_check())
        report_issue(
            self.root,
            report(owner_target_id=None, evidence=[]),
            source(target_id="service.transfer"),
        )
        self.assertEqual((0, {"errors": [], "notes": []}), self.run_check())

    @verifies("scenario.issues.store-check-invalid")
    def test_a_malformed_or_misnamed_record_fails_and_is_named(self):
        receipt = report_issue(
            self.root,
            report(owner_target_id="service.transfer", evidence=[]),
            source(target_id="service.transfer"),
        )
        path = self.root / receipt["path"]
        path.write_text(path.read_text().replace("Retry ownership", "Edited"))
        stray = self.root / ".concorde/issues/notes.md"
        stray.write_text("# notes\n")
        misnamed = self.root / ".concorde/issues" / ("I-" + "0" * 32 + ".md")
        misnamed.write_text(
            (self.root / receipt["path"]).read_text().replace(receipt["issue_id"], "x")
        )
        status, value = self.run_check()
        self.assertNotEqual(0, status)
        text = "\n".join(value["errors"])
        for name in (receipt["path"], ".concorde/issues/notes.md", misnamed.name):
            self.assertIn(name, text)
        self.assertEqual(3, len(value["errors"]), value)

    @verifies("scenario.issues.store-check-invalid")
    def test_a_symbolically_linked_record_is_named(self):
        receipt = report_issue(
            self.root,
            report(owner_target_id="service.transfer", evidence=[]),
            source(target_id="service.transfer"),
        )
        target = self.root / "elsewhere.md"
        target.write_text((self.root / receipt["path"]).read_text())
        linked = self.root / ".concorde/issues" / ("I-" + "1" * 32 + ".md")
        linked.symlink_to(target)
        status, value = self.run_check()
        self.assertEqual(1, status)
        self.assertEqual(1, len(value["errors"]), value)
        self.assertIn(linked.name, value["errors"][0])

    @verifies("scenario.issues.store-check-unknown-owner")
    def test_an_open_issue_of_an_unregistered_owner_fails(self):
        receipt = self.orphan()
        status, value = self.run_check()
        self.assertEqual(1, status)
        self.assertEqual(
            [f"{receipt['issue_id']} names unknown owner module.removed"],
            value["errors"],
        )

    @verifies("scenario.issues.store-check-closed-unknown-owner")
    def test_a_closed_issue_of_an_unregistered_owner_is_noted_but_passes(self):
        receipt = self.orphan()
        _, revision = read_issue(self.root, receipt["issue_id"])
        dispose_issue(
            self.root,
            receipt["issue_id"],
            revision,
            reason="not-actionable",
            note="Module removed",
            evidence=["registry"],
            actor="developer",
        )
        status, value = self.run_check()
        self.assertEqual(0, status)
        self.assertEqual([], value["errors"])
        self.assertEqual(
            [f"{receipt['issue_id']} names unknown owner module.removed"],
            value["notes"],
        )

    @verifies("scenario.issues.store-check-misplaced")
    def test_a_misplaced_record_and_an_issue_recorded_twice_fail(self):
        issues = self.root / ".concorde/issues"

        def recorded(key, status):
            receipt = report_issue(
                self.root,
                report(report_key=key, owner_target_id="service.transfer", evidence=[]),
                source(target_id="service.transfer"),
            )
            if status == "closed":
                _, revision = read_issue(self.root, receipt["issue_id"])
                dispose_issue(
                    self.root,
                    receipt["issue_id"],
                    revision,
                    reason="resolved",
                    note="Fixed",
                    evidence=["commit abc123"],
                    actor="main-agent",
                )
            return receipt["issue_id"]

        legacy, reopened = recorded("legacy", "closed"), recorded("reopened", "open")
        twice = recorded("twice", "closed")
        # A closed record where an earlier Concorde kept it, an open one in closed/ and a copy.
        (issues / f"closed/{legacy}.md").rename(issues / f"{legacy}.md")
        (issues / f"{reopened}.md").rename(issues / f"closed/{reopened}.md")
        (issues / f"{twice}.md").write_bytes(
            (issues / f"closed/{twice}.md").read_bytes()
        )
        status, value = self.run_check()
        self.assertEqual(1, status)
        self.assertEqual(
            sorted(
                [
                    f".concorde/issues/{legacy}.md holds closed Issue {legacy}, whose record "
                    f"belongs at .concorde/issues/closed/{legacy}.md; run `concorde issues "
                    "archive` in the primary worktree, which moves it there",
                    f".concorde/issues/closed/{reopened}.md holds open Issue {reopened}, whose "
                    f"record belongs at .concorde/issues/{reopened}.md; run `concorde issues "
                    "archive` in the primary worktree, which moves it there",
                    f".concorde/issues/{twice}.md holds closed Issue {twice}, whose record "
                    f"belongs at .concorde/issues/closed/{twice}.md; run `concorde issues "
                    "archive` in the primary worktree, which moves it there",
                    f"Issue {twice} is recorded twice, as .concorde/issues/{twice}.md and "
                    f".concorde/issues/closed/{twice}.md, but an Issue lives in exactly one "
                    "place: keep the record whose reports and dispositions begin with the "
                    "other's, remove the other with `git rm` and commit that removal alone",
                ]
            ),
            sorted(value["errors"]),
        )


if __name__ == "__main__":
    unittest.main()
