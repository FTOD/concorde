"""Issue operations through the real host gates, without a model."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.harness.host import OperationHost
from concorde.operations.dispatch import run_operation
from concorde.harness.change_worktree import ensure_change, read_change
from concorde.issue_solving.bookkeeping import select_target
from concorde.planning.gaps import open_gaps, record_task_gaps
from concorde.planning.records import gap_history
from concorde.issues.store import read_issue, report_issue
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.issue_reports import report, source
from tests.concorde.support.spec_project import (
    CONFIGURATION,
    PACKAGE,
    project,
)


class IssueGraphTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)
        self.ref = report_issue(
            self.root,
            report(
                type="bug",
                subtype=None,
                title="Transfer leaves balance unchanged",
                description="Transfer must subtract a valid amount.",
                owner_target_id="service.transfer",
                evidence=[],
            ),
            source(target_id="service.transfer"),
        )

    def call(self, action, **extra):
        host = OperationHost(
            self.root,
            PACKAGE,
            allow_primary_worktree=True,
        )
        payload = {
            "action": action,
            **({"issue_id": self.ref["issue_id"]} if action != "list" else {}),
            **extra,
        }
        return run_operation(
            "concorde-issues",
            CONFIGURATION,
            typed("concorde-issues-request", payload),
            host_context=host,
        )

    @verifies("scenario.issue-solving.inspect")
    def test_inspection_does_not_create_a_candidate_or_launch_a_worker(self):
        before = read_issue(self.root, self.ref["issue_id"])
        for action in ("list", "show"):
            result = self.call(action)
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual([before[0]], result["output"]["data"]["issues"])
            self.assertFalse((self.root / ".concorde/status").exists())
        self.assertEqual(before, read_issue(self.root, self.ref["issue_id"]))

    @verifies("scenario.issue-solving.spec-repair-handback")
    def test_every_solver_action_has_an_explicit_declared_route(self):
        from concorde.issue_solving.bookkeeping import DECISION_ROUTES
        from concorde.spec.typed_data import data_schema

        actions = data_schema("concorde-agent-stage-result")["properties"][
            "issue_decision"
        ]["properties"]["action"]["enum"]
        self.assertEqual(set(actions), set(DECISION_ROUTES))
        self.assertLessEqual(
            set(DECISION_ROUTES.values()), {"finish", "verify", "close"}
        )
        self.assertEqual("finish", DECISION_ROUTES["spec-repair"])
        self.assertEqual("finish", DECISION_ROUTES["develop"])

    @verifies("scenario.issue-solving.unknown-owner")
    def test_issue_of_a_removed_module_is_shown_but_not_solved_or_reopened(self):
        orphan = report_issue(
            self.root,
            report(
                report_key="orphan",
                type="bug",
                subtype=None,
                title="A removed Module's problem",
                description="The owner is no longer registered.",
                owner_target_id=None,
                evidence=[],
            ),
            source(target_id="module.removed"),
        )
        before = read_issue(self.root, orphan["issue_id"])
        shown = self.call("show", issue_id=orphan["issue_id"])
        self.assertEqual("succeeded", shown["status"], shown)
        self.assertEqual([before[0]], shown["output"]["data"]["issues"])
        self.assertEqual("module.removed", shown["output"]["data"]["target_id"])
        listed = self.call("list")
        self.assertIn(
            orphan["issue_id"],
            [record["id"] for record in listed["output"]["data"]["issues"]],
        )
        for action, extra in (("solve", {}), ("reopen", {"note": "Retry"})):
            refused = self.call(action, issue_id=orphan["issue_id"], **extra)
            self.assertEqual("blocked", refused["status"], refused)
            self.assertEqual("unknown_target", refused["errors"][0]["code"])
        self.assertEqual(before, read_issue(self.root, orphan["issue_id"]))
        self.assertFalse((self.root / ".concorde/status").exists())

    @verifies("scenario.issue-solving.stale-issue")
    def test_stale_selection_is_rejected_before_any_worker_runs(self):
        result = self.call("solve", expected_revision="sha256:" + "f" * 64)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("stale_issue", result["errors"][0]["code"])
        self.assertFalse((self.root / ".concorde/status").exists())

    @verifies("scenario.issue-solving.uncommitted-refused")
    def test_uncommitted_issue_is_refused_before_a_candidate_exists(self):
        def git(*arguments):
            subprocess.run(
                ["git", "-C", str(self.root), *arguments],
                check=True,
                capture_output=True,
            )

        git("init", "-q", "-b", "main")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "Fixture")
        git("add", "-A", "--", ".", ":!.concorde/issues")
        git("commit", "-q", "-m", "fixture")
        request = {"action": "solve", "issue_id": self.ref["issue_id"]}
        with self.assertRaises(SpecError) as refused:
            select_target(self.root, PACKAGE, request)
        self.assertEqual("uncommitted_issue", refused.exception.code)
        self.assertFalse((self.root / ".concorde/status").exists())
        git("add", "-A")
        git("commit", "-q", "-m", "issue")
        data, mutates = select_target(self.root, PACKAGE, request)
        self.assertTrue(mutates)
        self.assertEqual("service.transfer", data["target_id"])

    def test_issue_identity_outlives_task_wording_and_released_dependencies(self):
        ensure_change(self.root, allow_primary=True)
        blocker = {**self.ref, "blocked_step": "Implement transfer"}
        record_task_gaps(
            self.root,
            "service.transfer",
            "Old task text",
            "plan",
            [blocker],
            "old",
            scope_id="module:service.transfer",
        )
        original = gap_history(read_change(self.root, required=True))[0]
        record_task_gaps(
            self.root,
            "service.transfer",
            "Replanned text",
            "plan",
            [blocker],
            "old",
            scope_id="module:service.transfer",
        )
        self.assertEqual(
            original["id"],
            gap_history(read_change(self.root, required=True))[0]["id"],
        )
        self.assertEqual(
            [],
            [
                gap
                for gap in open_gaps(read_change(self.root))
                if gap["target_id"] == "module.ledger"
            ],
        )
        record_task_gaps(
            self.root,
            "service.transfer",
            "Replanned text",
            "plan",
            [],
            "new",
            scope_id="module:service.transfer",
        )
        self.assertEqual(
            "resolved",
            gap_history(read_change(self.root, required=True))[0]["status"],
        )
        self.assertEqual(
            "open", read_issue(self.root, self.ref["issue_id"])[0]["status"]
        )

    @verifies("scenario.issue-solving.inspect")
    def test_solving_an_already_closed_issue_does_not_prepare_a_worktree(self):
        from concorde.issues.store import dispose_issue

        _, revision = read_issue(self.root, self.ref["issue_id"])
        dispose_issue(
            self.root,
            self.ref["issue_id"],
            revision,
            reason="not-actionable",
            note="Fixture disposition",
            evidence=["fixture"],
            actor="test",
        )
        host = OperationHost(
            self.root, PACKAGE
        )  # no primary-write or candidate-creation override
        result = run_operation(
            "concorde-issues",
            CONFIGURATION,
            typed(
                "concorde-issues-request",
                {"action": "solve", "issue_id": self.ref["issue_id"]},
            ),
            host_context=host,
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertFalse((self.root / ".concorde/status").exists())
