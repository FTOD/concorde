"""Issue operations through the real host gates, without a model."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from concorde.harness.host import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import (
    ensure_change,
    read_change,
    record_task_gaps,
    workspace_context,
)
from concorde.issues.graph import copy_selection
from concorde.issues.store import read_issue, report_issue
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import report, source
from tests.concorde.spec.support import (
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

    @verifies("scenario.issues.inspect", "scenario.concorde.issues")
    def test_inspection_does_not_create_a_candidate_or_launch_a_worker(self):
        before = read_issue(self.root, self.ref["issue_id"])
        for action in ("list", "show"):
            result = self.call(action)
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual([before[0]], result["output"]["data"]["issues"])
            self.assertFalse((self.root / ".concorde/status").exists())
        self.assertEqual(before, read_issue(self.root, self.ref["issue_id"]))

    @verifies("scenario.issues.solve-spec-repair")
    def test_every_solver_action_has_an_explicit_declared_route(self):
        from concorde.issues.graph import DECISION_ROUTES, NODES
        from concorde.spec.typed_data import DATA_SCHEMAS

        actions = DATA_SCHEMAS["concorde-agent-stage-result"]["properties"][
            "issue_decision"
        ]["properties"]["action"]["enum"]
        self.assertEqual(set(actions), set(DECISION_ROUTES))
        self.assertLessEqual(set(DECISION_ROUTES.values()), set(NODES))
        self.assertEqual("finish", DECISION_ROUTES["spec-repair"])
        self.assertEqual("finish", DECISION_ROUTES["develop"])

    @verifies("scenario.issues.solve-stale")
    def test_stale_selection_is_rejected_before_any_worker_runs(self):
        result = self.call("solve", expected_revision="sha256:" + "f" * 64)
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("stale_issue", result["errors"][0]["code"])
        self.assertFalse((self.root / ".concorde/status").exists())

    @verifies("scenario.issues.solve-handoff")
    def test_selection_copy_preserves_uncommitted_bytes_and_no_unrelated_file(self):
        destination = self.root / "candidate"
        destination.mkdir()
        before, revision = read_issue(self.root, self.ref["issue_id"])
        (self.root / "unrelated.txt").write_text("private local edit")
        copy_selection(
            self.root,
            destination,
            {"issue_id": self.ref["issue_id"], "expected_revision": revision},
        )
        self.assertEqual(
            (before, revision), read_issue(destination, self.ref["issue_id"])
        )
        self.assertFalse((destination / "unrelated.txt").exists())
        with self.assertRaises(SpecError):
            copy_selection(
                self.root,
                destination,
                {
                    "issue_id": self.ref["issue_id"],
                    "expected_revision": "sha256:" + "f" * 64,
                },
            )

    @verifies("scenario.issues.blocker-history")
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
        original = read_change(self.root, required=True)["issue_blockers"][0]
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
            read_change(self.root, required=True)["issue_blockers"][0]["id"],
        )
        self.assertEqual(
            [], workspace_context(self.root, target_id="module.ledger")["blockers"]
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
            read_change(self.root, required=True)["issue_blockers"][0]["status"],
        )
        self.assertEqual(
            "open", read_issue(self.root, self.ref["issue_id"])[0]["status"]
        )

    @verifies("scenario.issues.inspect")
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
