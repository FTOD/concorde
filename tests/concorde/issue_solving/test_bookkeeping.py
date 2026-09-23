"""The bookkeeping actions of `concorde-issues` from a primary worktree, without any model."""

from __future__ import annotations

import unittest

from concorde.harness.change_worktree import git_value
from concorde.issues.store import dispose_issue, list_issues, read_issue, report_issue
from concorde.spec.verification import verifies
from tests.concorde.issue_solving.native_solve import commit_issues, transfer_report
from tests.concorde.support.issue_reports import source
from tests.concorde.support.worktree_project import WorktreeProject


class BookkeepingTests(WorktreeProject, unittest.TestCase):
    def setUp(self):
        super().setUp()
        receipt = report_issue(
            self.primary, transfer_report(), source(target_id="service.transfer")
        )
        self.issue = receipt["issue_id"]
        commit_issues(self.primary, "Record the overdraft Issue")
        self.worktrees = self.worktree_list()

    def worktree_list(self):
        return git_value(self.primary, "worktree", "list", "--porcelain")

    def call(self, **data):
        return self.call_operation(self.primary, "concorde-issues", data)

    def assert_nothing_created(self):
        self.assertEqual(self.worktrees, self.worktree_list())
        self.assertFalse((self.primary / ".concorde/status").exists())

    def close(self):
        _, revision = read_issue(self.primary, self.issue)
        dispose_issue(
            self.primary,
            self.issue,
            revision,
            reason="not-actionable",
            note="The contract permits it",
            evidence=["contract"],
            actor="concorde-issue-solver",
        )
        return read_issue(self.primary, self.issue)

    @verifies("scenario.issue-solving.report")
    def test_the_developer_report_is_saved_and_returned_without_a_candidate(self):
        result = self.call(
            action="report",
            target_id="service.transfer",
            report=transfer_report(
                "rounding",
                title="Rounding of cents is unstated",
                evidence=[
                    {"path": "specs/transfer/module.md", "description": "Purpose"}
                ],
            ),
        )
        self.assertEqual("succeeded", result["status"], result)
        (record,) = result["output"]["data"]["issues"]
        self.assertEqual(record, read_issue(self.primary, record["id"])[0])
        observation = record["reports"][0]
        self.assertEqual(
            ("developer", "report", "service.transfer"),
            (
                observation["source"]["agent"],
                observation["source"]["phase"],
                observation["source"]["target_id"],
            ),
        )
        self.assertEqual(
            "Rounding of cents is unstated", observation["report"]["title"]
        )
        self.assert_nothing_created()

    @verifies("scenario.issue-solving.report")
    def test_a_developer_report_outside_the_module_context_is_refused(self):
        result = self.call(
            action="report",
            target_id="service.transfer",
            report=transfer_report(
                "secret", evidence=[{"path": "secret.py", "description": "Private"}]
            ),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"])
        self.assertEqual([self.issue], [row["id"] for row in list_issues(self.primary)])

    @verifies("scenario.issue-solving.reopen")
    def test_reopening_a_closed_issue_records_the_developer_and_keeps_reports(self):
        closed, _ = self.close()
        result = self.call(action="reopen", issue_id=self.issue, note="It regressed")
        self.assertEqual("succeeded", result["status"], result)
        record, _ = read_issue(self.primary, self.issue)
        self.assertEqual([record], result["output"]["data"]["issues"])
        self.assertEqual("open", record["status"])
        last = record["dispositions"][-1]
        self.assertEqual(
            ("reopened", "developer", "It regressed"),
            (last["reason"], last["actor"], last["note"]),
        )
        self.assertEqual(closed["reports"], record["reports"])
        self.assert_nothing_created()

    @verifies("scenario.issue-solving.reopen-without-note")
    def test_reopening_without_a_note_is_refused(self):
        before = self.close()
        result = self.call(action="reopen", issue_id=self.issue)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("invalid_input", result["errors"][0]["code"])
        self.assertEqual(before, read_issue(self.primary, self.issue))
        self.assert_nothing_created()

    @verifies("scenario.issue-solving.foreign-target")
    def test_selecting_an_issue_for_another_module_is_refused(self):
        before = read_issue(self.primary, self.issue)
        for action, extra in (
            ("show", {}),
            ("solve", {}),
            ("reopen", {"note": "Retry"}),
        ):
            with self.subTest(action=action):
                result = self.call(
                    action=action,
                    issue_id=self.issue,
                    target_id="module.ledger",
                    **extra,
                )
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("permission_denied", result["errors"][0]["code"])
        self.assertEqual(before, read_issue(self.primary, self.issue))
        self.assert_nothing_created()


if __name__ == "__main__":
    unittest.main()
