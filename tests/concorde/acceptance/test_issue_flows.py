"""Acceptance: Issues reported by Agents, handed back by the solver, and solved in a candidate."""

import unittest

from concorde.harness.change_worktree import git, read_change
from concorde.issues.store import read_issue
from concorde.spec.verification import verifies

from tests.concorde.support.worktree_project import WorktreeProject

from .develop_flow import GUARDED
from .develop_session import AgentFailed, ScriptedSession, review_result, stage_result

BALANCE = {
    "report_key": "ledger-balance-kind",
    "type": "gap",
    "subtype": "spec-conflict",
    "title": "The ledger does not say whether balances may be negative",
    "description": "The ledger Module stores integer balances but does not state whether "
    "a negative balance can be stored.",
    "impact": "Callers cannot rely on the sign of a stored balance.",
    "basis": "The ledger read scenario names an integer balance only.",
    "owner_target_id": "module.ledger",
    "evidence": [
        {"path": "specs/ledger/module.md", "description": "The ledger purpose"}
    ],
}
UNCHANGED_BALANCE = {
    "report_key": "unchanged-balance",
    "type": "bug",
    "subtype": None,
    "title": "Transfer leaves the balance unchanged",
    "description": "transfer(100, 20) returns 100 instead of 80.",
    "impact": "Every transfer keeps the sender's full balance.",
    "basis": "The transfer debit scenario requires 80.",
    "owner_target_id": "service.transfer",
    "evidence": [{"path": "app/transfer.py", "description": "The transfer result"}],
}


def decision(action: str, intent: str, rationale: str):
    def answer(child):
        return stage_result(
            child,
            "completed",
            rationale,
            issue_decision={
                "action": action,
                "intent": intent,
                "rationale": rationale,
                "duplicate_of": None,
            },
        )

    return answer


def no_findings(child):
    return review_result(child, "no_findings", "The transfer debits valid amounts.")


class IssueAcceptance(WorktreeProject, unittest.TestCase):
    """The user session and its Agents record Issues and solve them through `concorde-issues`."""

    def setUp(self):
        super().setUp()
        self.session = ScriptedSession(self, self.change)

    def issues(self, root, action, **extra):
        return self.call_operation(root, "concorde-issues", {"action": action, **extra})

    def committed_issue(self) -> tuple[str, str]:
        """The developer reports the unchanged-balance bug and commits it on the primary branch."""
        reported = self.issues(
            self.primary,
            "report",
            target_id="service.transfer",
            report=UNCHANGED_BALANCE,
        )
        self.assertEqual("succeeded", reported["status"], reported)
        (record,) = reported["output"]["data"]["issues"]
        self.commit(self.primary, "Report the unchanged balance")
        git(self.change, "merge", "-q", "--ff-only", "integration")
        return record["id"], read_issue(self.change, record["id"])[1]

    def tree(self, root) -> dict:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for folder in ("specs", "app", "checks")
            for path in sorted((root / folder).rglob("*"))
            if path.is_file()
        }

    def solve(self, issue_id, revision, answers):
        return self.session.workflow(
            "concorde-issues",
            {"action": "solve", "issue_id": issue_id, "expected_revision": revision},
            answers,
        )

    @verifies("scenario.concorde.issue-reported")
    def test_an_agent_report_outlives_its_failed_review(self):
        def reviewer(child):
            self.receipt = child.report(BALANCE)
            raise AgentFailed("the reviewer's model failed after reporting")

        request = {"target_id": "service.transfer", "task": "Review the transfer code"}
        reviewed = self.session.workflow(
            "concorde-code-review", request, lambda key: reviewer
        )
        self.assertEqual("failed", reviewed["status"], reviewed)
        data = reviewed["output"]["data"]
        self.assertEqual("failed", data["outcome"], reviewed)
        (review,) = data["reviews"]
        self.assertEqual("incomplete", review["data"]["status"])
        self.assertIn("could not complete", review["data"]["answer"])
        issue, _ = read_issue(self.change, self.receipt["issue_id"])
        source = issue["reports"][-1]["source"]
        self.assertEqual(
            ("service.transfer", "code-review", "concorde-code-review"),
            (source["target_id"], source["phase"], source["operation"]),
        )
        self.assertEqual(
            "module.ledger", issue["reports"][-1]["report"]["owner_target_id"]
        )
        listed = self.issues(self.change, "list")
        self.assertEqual("succeeded", listed["status"], listed)
        self.assertIn(
            self.receipt["issue_id"],
            [record["id"] for record in listed["output"]["data"]["issues"]],
        )

    @verifies("scenario.concorde.issue-handback")
    def test_solving_hands_a_code_fix_back_without_editing(self):
        issue_id, revision = self.committed_issue()
        before = self.tree(self.change)
        intent = "Subtract a valid amount from the balance in app/transfer.py."
        result = self.solve(
            issue_id,
            revision,
            lambda key: decision(
                "develop", intent, "The fix is a code change to the transfer."
            ),
        )
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("unsupported", data["outcome"], result)
        self.assertEqual("develop", data["decision"])
        self.assertIn(intent, data["answer"])
        self.assertEqual("open", read_issue(self.change, issue_id)[0]["status"])
        self.assertEqual(before, self.tree(self.change))

    @verifies("scenario.concorde.issue-solved")
    def test_a_verified_fix_closes_the_issue_in_its_candidate(self):
        issue_id, revision = self.committed_issue()
        # The user session made the fix in the candidate.
        (self.change / "app/transfer.py").write_text(GUARDED)
        fixed = "Transfer now subtracts a valid amount."

        def answers(key):
            if key.startswith("d-"):
                return decision("resolved", "Close the fixed Issue.", fixed)
            return no_findings

        result = self.solve(issue_id, revision, answers)
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("ready", data["outcome"], result)
        self.assertEqual("resolved", data["decision"])
        issue = read_issue(self.change, issue_id)[0]
        self.assertEqual("closed", issue["status"])
        self.assertEqual("resolved", issue["dispositions"][-1]["reason"])
        self.assertEqual(fixed, issue["dispositions"][-1]["note"])
        change = read_change(self.change, required=True)
        self.assertEqual("ready", change["status"])
        self.assertEqual("open", read_issue(self.primary, issue_id)[0]["status"])


if __name__ == "__main__":
    unittest.main()
