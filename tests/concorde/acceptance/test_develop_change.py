"""Acceptance: a change is developed through the stage capabilities in a candidate."""

import unittest

from concorde.harness.change_worktree import read_change, snapshot_tree
from concorde.harness.status_store import run_path
from concorde.issues.store import read_issue
from concorde.planning.records import target_state
from concorde.review.records import recorded
from concorde.spec.verification import verifies
from concorde.validation.records import validated_tree

from .develop_flow import DEBIT_ONLY, GUARDED, DevelopProject, programmer
from .develop_session import AgentFailed, review_result, stage_result

ROUNDING = {
    "report_key": "fractional-amounts",
    "type": "gap",
    "subtype": "missing-contract",
    "title": "Fractional amounts are unspecified",
    "description": "The transfer Module does not state whether a fractional amount is "
    "accepted, rounded or rejected.",
    "impact": "The guard for non-integer amounts cannot be planned.",
    "basis": "No requirement or scenario of the transfer Module mentions fractional amounts.",
    "owner_target_id": "service.transfer",
    "evidence": [
        {"path": "specs/transfer/module.md", "description": "The transfer purpose"}
    ],
}
WHOLE_AMOUNTS = (
    "\n### req.transfer.whole — Amounts are whole numbers\n\n"
    "transfer SHALL reject an amount that is not an integer.\n"
)


def missing_promise(child):
    """An assessor that finds the fractional-amount promise missing and reports it."""
    receipt = child.report(ROUNDING)
    return stage_result(
        child,
        "spec_incomplete",
        "The transfer Module does not state how fractional amounts behave.",
        blockers=[{**receipt, "blocked_step": "Plan the guarded transfer"}],
    )


class DevelopChangeAcceptance(DevelopProject, unittest.TestCase):
    """The user session develops the guarded transfer the transfer Module's Spec states."""

    @verifies("scenario.concorde.develop-change")
    def test_a_change_reaches_one_ready_candidate_and_nothing_is_delivered(self):
        self.assertEqual(0, self.run_check(self.primary))
        primary = self.primary_state()
        self.develop()
        result = self.validate()
        self.assertEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("ready", data["outcome"], result)
        self.assertEqual(
            [("check.transfer", "passed")],
            [(item["check_id"], item["status"]) for item in data["checks"]],
        )
        change = read_change(self.change, required=True)
        self.assertEqual(("ready", "ready"), (change["phase"], change["status"]))
        # The recorded evidence is bound to the candidate's exact files.
        self.assertEqual(snapshot_tree(self.change), validated_tree(change))
        state = target_state(self.change, "service.transfer", None)
        self.assertTrue(state["tasks"] and all(t["complete"] for t in state["tasks"]))
        self.assertEqual(0, self.run_check(self.change))
        self.assertEqual(primary, self.primary_state())
        self.assertEqual([], self.delivered_branches())

    def outcome(self, result) -> str:
        output = result["output"]
        self.assertIsNotNone(output, result)
        return output["data"]["outcome"]

    @verifies("scenario.concorde.develop-gap", "scenario.concorde.develop-gap-repaired")
    def test_a_missing_promise_stops_dependent_work_until_the_spec_states_it(self):
        self.develop()
        specs = self.spec_bytes(self.change)
        # The change now depends on how fractional amounts behave: the assessor finds a gap.
        assessed = self.context_solve(missing_promise)
        self.assertEqual("blocked", assessed["status"], assessed)
        self.assertEqual("spec_incomplete", self.outcome(assessed))
        (blocker,) = assessed["output"]["data"]["blockers"]
        issue, _ = read_issue(self.change, blocker["issue_id"])
        self.assertEqual("open", issue["status"])
        report = issue["reports"][-1]["report"]
        self.assertEqual("service.transfer", report["owner_target_id"])
        self.assertEqual(
            ("gap", "missing-contract"), (report["type"], report["subtype"])
        )
        self.assertIn("fractional", report["description"])
        # Planning, task writing and implementation refuse while the gap is pending.
        for name, result in (
            ("plan", self.plan()),
            ("tasks", self.write_tasks()),
            ("implement", self.implement()),
        ):
            with self.subTest(step=name):
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("spec_incomplete", self.outcome(result), result)
                self.assertIn(
                    blocker["issue_id"],
                    [item["issue_id"] for item in result["output"]["data"]["blockers"]],
                )
        self.assertEqual(specs, self.spec_bytes(self.change))
        self.assertNotEqual("ready", read_change(self.change, required=True)["status"])

        # The developer and the user session state the missing promise in the Spec.
        obligations = self.change / "specs/transfer/obligations.md"
        text = obligations.read_text()
        heading = "## Scenarios"
        obligations.write_text(text.replace(heading, WHOLE_AMOUNTS + "\n" + heading, 1))
        reassessed = self.context_solve()
        self.assertEqual("succeeded", reassessed["status"], reassessed)
        self.assertEqual("completed", self.outcome(reassessed), reassessed)
        self.assertEqual([], reassessed["output"]["data"]["blockers"])
        planned = self.plan()
        self.assertEqual("succeeded", planned["status"], planned)
        self.assertEqual("completed", self.outcome(planned), planned)

    @verifies("scenario.concorde.develop-failure")
    def test_a_failed_implementation_keeps_the_programmers_files(self):
        for name, result in (
            ("context-solve", self.context_solve()),
            ("plan", self.plan()),
            ("tasks", self.write_tasks()),
        ):
            self.assertEqual("completed", self.outcome(result), (name, result))
        primary = self.primary_state()

        def crash(child):
            (self.change / "app/transfer.py").write_text(GUARDED)
            raise AgentFailed("the model provider failed mid-run")

        result = self.implement(crash)
        self.assertEqual("failed", result["status"], result)
        self.assertIsNone(result["output"], result)
        (error,) = result["errors"]
        self.assertEqual("execution_failed", error["code"], result)
        self.assertEqual(GUARDED, (self.change / "app/transfer.py").read_text())
        change = read_change(self.change, required=True)
        self.assertNotEqual("ready", change["status"])
        state = target_state(self.change, "service.transfer", None)
        self.assertFalse(any(task["complete"] for task in state["tasks"]))
        self.assertEqual(primary, self.primary_state())
        self.assertEqual([], self.delivered_branches())

    @verifies("scenario.concorde.validate-failed-check")
    def test_a_failing_check_prevents_readiness_and_its_evidence_is_kept(self):
        # The programmer completes its task, but the guarded check fails on its code.
        self.develop(programmer(self.change, code=DEBIT_ONLY))
        result = self.validate()
        self.assertNotEqual("succeeded", result["status"], result)
        data = result["output"]["data"]
        self.assertEqual("failed", data["outcome"], result)
        self.assertEqual(
            [("check.transfer", "failed")],
            [(item["check_id"], item["status"]) for item in data["checks"]],
        )
        change = read_change(self.change, required=True)
        self.assertNotEqual("ready", change["status"])
        self.assertIsNone(validated_tree(change))
        state = target_state(self.change, "service.transfer", None)
        self.assertEqual(
            [("check.transfer", "failed")],
            [(item["check_id"], item["status"]) for item in state["checks"]],
        )
        self.assertEqual(DEBIT_ONLY, (self.change / "app/transfer.py").read_text())

    @verifies("scenario.concorde.review-required")
    def test_a_stale_required_code_review_blocks_readiness(self):
        self.develop()
        reviewed = self.session.workflow(
            "concorde-code-review",
            self.task,
            lambda key: (
                lambda child: review_result(
                    child, "no_findings", "The guarded transfer meets its contract."
                )
            ),
        )
        self.assertEqual("succeeded", reviewed["status"], reviewed)
        self.assertEqual("completed", self.outcome(reviewed), reviewed)
        (artifact,) = reviewed["output"]["data"]["artifacts"]
        # The Module's files change after the required review completed.
        changed = GUARDED + "# Clarified after review.\n"
        (self.change / "app/transfer.py").write_text(changed)
        result = self.validate()
        self.assertNotEqual("succeeded", result["status"], result)
        (error,) = result["errors"]
        self.assertEqual("review_required", error["code"], result)
        self.assertIn("review", error["message"])
        change = read_change(self.change, required=True)
        self.assertNotEqual("ready", change["status"])
        self.assertEqual(changed, (self.change / "app/transfer.py").read_text())
        self.assertTrue(run_path(self.change, artifact["path"]).is_file(), artifact)
        self.assertEqual(
            "no_findings",
            recorded(change, "reviews")["service.transfer"]["code"]["status"],
        )


if __name__ == "__main__":
    unittest.main()
