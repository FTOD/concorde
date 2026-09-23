"""The solve workflow of `concorde-issues`, run through the native driver without a model.

Each test prepares a solve in the candidate, runs its Host steps and scripts the solver's and the
reviewers' structured answers; see ``native_solve`` for what is synthetic.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import native_driver
from concorde.harness.change_worktree import git_value, read_change, save_change
from concorde.issue_solving import solve as solve_service
from concorde.issue_solving.records import solutions, store_solution
from concorde.issues.store import dispose_issue, read_issue, report_issue
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.issue_solving.native_solve import (
    SolveCandidate,
    commit_issues,
    transfer_report,
)
from tests.concorde.support.issue_reports import source
from tests.concorde.support.spec_project import PACKAGE


class SolveTests(SolveCandidate, unittest.TestCase):
    def files(self):
        """The candidate's working files as Git sees them, apart from the Issue records."""
        return (
            git_value(self.change, "rev-parse", "HEAD"),
            git_value(
                self.change,
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                ".",
                ":!.concorde/issues",
            ),
            git_value(self.change, "diff", "--", ".", ":!.concorde/issues"),
        )

    def first_decision(self, action, **extra):
        workflow = self.start()
        self.assertEqual("decide", workflow.host_step("next-0")["route"])
        workflow.decision(0, action, **extra)
        return workflow

    def assert_open(self, before=None):
        record, _ = self.record()
        self.assertEqual("open", record["status"])
        if before is not None:
            self.assertEqual(before, self.issue_bytes())

    def assert_closed_by_solver(self, reason, output):
        record, revision = self.record()
        self.assertEqual("closed", record["status"])
        last = record["dispositions"][-1]
        self.assertEqual(
            (reason, "concorde-issue-solver"), (last["reason"], last["actor"])
        )
        self.assertEqual([record], output["issues"])
        self.assertEqual(("ready", reason), (output["outcome"], output["decision"]))
        self.assertTrue(output["checks"])
        self.assertTrue(all(check["status"] == "passed" for check in output["checks"]))
        solution = self.solution()
        self.assertEqual(
            ("completed", reason, revision),
            (solution["status"], solution["disposition"], solution["closed_revision"]),
        )
        self.assertNotIn("pending_disposition", solution)
        change = self.change_state()
        self.assertEqual("ready", change["status"])
        # Nothing is delivered or merged: no delivery branch, the primary branch is unchanged.
        self.assertEqual(
            "", git_value(self.primary, "branch", "--list", "concorde/delivered/*")
        )
        self.assertEqual(
            self.primary_head, git_value(self.primary, "rev-parse", "HEAD")
        )
        return record

    def setUp(self):
        super().setUp()
        self.primary_head = git_value(self.primary, "rev-parse", "HEAD")

    # --- starting a solve -------------------------------------------------------------------

    @verifies("scenario.issue-solving.relay")
    def test_a_committed_issue_is_solved_in_a_new_candidate(self):
        self.issue = self.file_issue(self.primary, "primary-overdraft")
        self.primary_head = git_value(self.primary, "rev-parse", "HEAD")
        relayed = []

        def in_process(host, invocation, candidate, payload):
            """The candidate's own preparation, run in this process instead of a subprocess."""
            os.chdir(candidate)
            value = native_driver.execute(
                PACKAGE,
                "prepare",
                {**payload, "invocation": invocation},
                **self.context,
            )
            relayed.append((Path(candidate), value))
            return value

        with patch.object(native_driver, "relay_prepare", side_effect=in_process):
            prepared = self.prepare(root=self.primary)
        self.assertEqual("prepared", prepared["state"], prepared)
        ((candidate, inner),) = relayed
        self.assertNotIn(
            candidate.resolve(), {self.primary.resolve(), self.change.resolve()}
        )
        self.assertEqual(inner["result"], prepared["result"])
        self.assertEqual(
            str(candidate.resolve()), prepared["result"]["workspace"]["path"]
        )
        descriptor = json.loads(Path(prepared["descriptor"]).read_text())
        self.assertEqual(str(candidate.resolve()), descriptor["project_root"])
        self.assertEqual("concorde-issues", descriptor["operation"])
        self.assertIn("next-0", prepared["workflow"]["steps"])
        # The candidate was created from the primary branch, which stays unchanged.
        self.assertEqual(self.primary_head, git_value(candidate, "rev-parse", "HEAD"))
        self.assertEqual(
            self.primary_head, git_value(self.primary, "rev-parse", "HEAD")
        )
        self.assertIsNotNone(self.solution(candidate))
        self.assertEqual("open", read_issue(self.primary, self.issue)[0]["status"])

    @verifies("scenario.issue-solving.already-closed")
    def test_solving_a_closed_issue_replays_nothing(self):
        self.issue = self.file_issue(self.primary, "primary-overdraft")
        _, revision = self.record(self.primary)
        dispose_issue(
            self.primary,
            self.issue,
            revision,
            reason="not-actionable",
            note="The contract permits it",
            evidence=["contract"],
            actor="developer",
        )
        commit_issues(self.primary, "Close the Issue")
        worktrees = git_value(self.primary, "worktree", "list", "--porcelain")
        value = self.prepare(root=self.primary)
        self.assertEqual("not-run", value["state"], value)
        self.assertNotIn("descriptor", value)
        data = value["result"]["output"]["data"]
        self.assertEqual("already-closed", data["decision"])
        self.assertEqual([self.record(self.primary)[0]], data["issues"])
        self.assertEqual(
            "not-actionable", data["issues"][0]["dispositions"][-1]["reason"]
        )
        self.assertEqual(
            worktrees, git_value(self.primary, "worktree", "list", "--porcelain")
        )
        self.assertFalse((self.primary / ".concorde/status").exists())
        self.assertEqual(
            [], list((self.directory / "scratch").glob("concorde-native-*"))
        )

    @verifies("scenario.issue-solving.preview")
    def test_a_policy_preview_prepares_nothing(self):
        before = self.issue_bytes()
        value = self.prepare(mode="describe-policy")
        self.assertEqual("described", value["state"], value)
        self.assertNotIn("descriptor", value)
        answer = value["result"]["output"]["data"]["answer"]
        for word in ("bounded", "review", "journal"):
            self.assertIn(word, answer)
        self.assertIsNone(read_change(self.change))
        self.assertEqual(before, self.issue_bytes())
        self.assertEqual(
            [], list((self.directory / "scratch").glob("concorde-native-*"))
        )

    # --- decisions --------------------------------------------------------------------------

    @verifies(
        "scenario.issue-solving.develop-handback",
        "scenario.issue-solving.spec-repair-handback",
    )
    def test_a_hand_back_stops_unsupported_and_changes_nothing(self):
        for action in ("develop", "spec-repair"):
            with self.subTest(action=action):
                workflow = self.start()
                before = (self.issue_bytes(), self.files())
                workflow.host_step("next-0")
                workflow.decision(0, action)
                self.assertEqual("finished", workflow.host_step("decision-0")["route"])
                output = workflow.output()
                self.assertEqual(
                    ("unsupported", action), (output["outcome"], output["decision"])
                )
                for text in (
                    "service.transfer",
                    "Settle the overdraft Issue by " + action,
                    "scenario.transfer.reject requires ValueError",
                ):
                    self.assertIn(text, output["answer"])
                history = self.solution()["history"]
                self.assertEqual(action, history[-1]["decision"]["action"])
                self.assertEqual(before, (self.issue_bytes(), self.files()))
                self.assert_open()

    @verifies("scenario.issue-solving.needs-decision")
    def test_an_open_choice_stops_with_the_question(self):
        workflow = self.first_decision("needs-decision")
        before = self.issue_bytes()
        self.assertEqual("finished", workflow.host_step("decision-0")["route"])
        output = workflow.output()
        self.assertEqual(
            ("conflicting", "needs-decision"), (output["outcome"], output["decision"])
        )
        self.assertEqual(
            "scenario.transfer.reject requires ValueError; needs-decision",
            output["answer"],
        )
        self.assert_open(before)

    @verifies("scenario.issue-solving.clarification")
    def test_a_clarification_restarts_the_attempts_and_reaches_the_solver(self):
        workflow = self.first_decision("needs-decision")
        workflow.host_step("decision-0")
        self.assertEqual(1, self.solution()["attempts"])
        again = self.start(note="Refuse the overdraft with ValueError.")
        self.assertEqual(0, self.solution()["attempts"])
        again.host_step("next-0")
        self.assertEqual(1, self.solution()["attempts"])
        self.assertIn(
            "Developer clarification: Refuse the overdraft with ValueError.",
            again.selection(0)["feedback"],
        )
        self.assertEqual(
            "Refuse the overdraft with ValueError.", self.solution()["clarification"]
        )

    @verifies("scenario.issue-solving.limit")
    def test_the_solver_is_not_asked_a_seventh_time(self):
        workflow = self.first_decision("needs-decision")
        workflow.host_step("decision-0")
        # Five more asks on the same inputs and clarification leave the count at six.
        change = self.change_state()
        solution = self.solution()
        solution["attempts"] = 6
        store_solution(change, self.issue, solution)
        save_change(self.change, change)
        history = solution["history"]
        again = self.start()
        self.assertEqual("finished", again.host_step("next-0")["route"])
        self.assertEqual([], again.keys("d-"))
        output = again.output()
        self.assertEqual(
            ("conflicting", "limit-exhausted"), (output["outcome"], output["decision"])
        )
        self.assertEqual(history, self.solution()["history"])
        self.assertEqual(6, self.solution()["attempts"])
        self.assert_open()

    @verifies(
        "scenario.issue-solving.resolved-unverified",
        "scenario.issue-solving.verification-passes",
        "scenario.issue-solving.resolved-ready",
    )
    def test_a_resolution_is_verified_first_and_then_closed_at_ready(self):
        workflow = self.first_decision("resolved")
        before = self.issue_bytes()
        verify = workflow.host_step("decision-0")
        # No current verification: the Host verifies instead of closing.
        self.assertEqual(("verify", [1, 1, 1, 1]), (verify["route"], verify["groups"]))
        self.assertEqual(
            ["v-0-0-0", "v-0-1-0", "v-0-2-0", "v-0-3-0"], workflow.keys("v-")
        )
        self.assert_open(before)
        workflow.review_all(0)
        self.assertEqual("decide", workflow.host_step("verified-0")["route"])
        solution = self.solution()
        self.assertEqual(solution["inputs"], solution["verified_inputs"])
        self.assertEqual(4, len(solution["verification"]))
        workflow.host_step("next-1")
        selection = workflow.selection(1)
        for digest in solution["verification"]:
            self.assertIn(digest, selection["verification"])
        self.assert_open(before)
        workflow.decision(1, "resolved")
        self.assertEqual("finished", workflow.host_step("decision-1")["route"])
        record = self.assert_closed_by_solver("resolved", workflow.output())
        self.assertEqual(
            set(solution["verification"]),
            set(record["dispositions"][-1]["evidence"][1:]),
        )

    # --- verification -----------------------------------------------------------------------

    @verifies("scenario.issue-solving.verification-blocking")
    def test_blocking_findings_send_the_solver_back_with_feedback(self):
        workflow = self.first_decision("verify")
        self.assertEqual("verify", workflow.host_step("decision-0")["route"])
        findings = []
        for key in workflow.keys("v-0-"):
            proposal = workflow.review(key, blocking=key == "v-0-1-0")
            findings.extend(proposal["result"]["data"]["issues"])
        self.assertEqual("decide", workflow.host_step("verified-0")["route"])
        solution = self.solution()
        self.assertIsNone(solution["verified_inputs"])
        self.assertNotIn("verification", solution)
        workflow.host_step("next-1")
        selection = workflow.selection(1)
        self.assertIn("still reports blocking Issues", selection["feedback"])
        self.assertEqual("", selection["verification"])
        # The next solver call also reads the reports of the blocking findings.
        [finding] = findings
        inputs = workflow.slot_descriptor("d-1")["snapshot"]["stage_inputs"]
        self.assertEqual(
            ["concorde-issue-selection", "concorde-issue-context"],
            [item["type_id"] for item in inputs],
        )
        [observation] = inputs[1]["data"]["observations"]
        self.assertEqual(
            {
                k: v
                for k, v in finding.items()
                if k not in {"severity", "affected_task"}
            },
            observation["receipt"],
        )
        self.assertEqual(transfer_report()["description"], observation["description"])
        self.assert_open()

    @verifies("scenario.issue-solving.reviewer-failed")
    def test_a_reviewer_that_fails_to_complete_stops_the_solve(self):
        workflow = self.first_decision("verify")
        workflow.host_step("decision-0")
        before = self.issue_bytes()
        for key in workflow.keys("v-0-"):
            if key == "v-0-2-0":
                descriptor = workflow.slot_descriptor(key)
                review = descriptor["review_input"]
                workflow.child(
                    key,
                    {
                        "context_id": descriptor["snapshot"]["context_id"],
                        "input_digest": review["input_digest"],
                        "review_mode": review["review_mode"],
                        "status": "incomplete",
                        "representative_tasks": [],
                        "issues": [],
                        "answer": "The review could not complete.",
                    },
                )
            else:
                workflow.review(key)
        self.assertEqual("finished", workflow.host_step("verified-0")["route"])
        output = workflow.output()
        self.assertEqual(("failed", "failed"), (output["outcome"], output["decision"]))
        self.assert_open(before)

    # --- closing ----------------------------------------------------------------------------

    @verifies("scenario.issue-solving.duplicate-close")
    def test_a_duplicate_of_an_offered_issue_is_closed_and_the_other_stays_open(self):
        other = report_issue(
            self.change,
            transfer_report("same-overdraft", description="Overdrafts are accepted."),
            source(invocation_id="other-reviewer", target_id="service.transfer"),
        )["issue_id"]
        commit_issues(self.change, "Record the same problem again")
        workflow = self.start()
        workflow.host_step("next-0")
        offered = workflow.selection(0)["duplicates"]
        self.assertEqual([other], [item["issue_id"] for item in offered])
        workflow.decision(0, "duplicate", duplicate_of=other)
        self.assertEqual("finished", workflow.host_step("decision-0")["route"])
        record = self.assert_closed_by_solver("duplicate", workflow.output())
        self.assertEqual(other, record["dispositions"][-1]["duplicate_of"])
        self.assertEqual("open", read_issue(self.change, other)[0]["status"])

    @verifies("scenario.issue-solving.not-actionable-close")
    def test_a_mistaken_report_is_closed_as_not_actionable(self):
        workflow = self.first_decision("not-actionable")
        self.assertEqual("finished", workflow.host_step("decision-0")["route"])
        record = self.assert_closed_by_solver("not-actionable", workflow.output())
        self.assertEqual(
            "scenario.transfer.reject requires ValueError; not-actionable",
            record["dispositions"][-1]["note"],
        )

    @verifies("scenario.issue-solving.validation-fails")
    def test_a_close_that_fails_final_validation_is_undone(self):
        # Other, uncommitted work in the candidate that makes the configured check fail.
        broken = "def transfer(balance, amount):\n    return balance\n"
        (self.change / "app/transfer.py").write_text(broken)
        workflow = self.first_decision("not-actionable")
        before = self.issue_bytes()
        workflow.host_step("decision-0")
        output = workflow.output()
        self.assertEqual(
            ("failed", "verification-failed"), (output["outcome"], output["decision"])
        )
        self.assertEqual(before, self.issue_bytes())
        solution = self.solution()
        self.assertEqual("verification-failed", solution["status"])
        self.assertNotIn("pending_disposition", solution)
        self.assertEqual("blocked", self.change_state()["status"])
        self.assertEqual(broken, (self.change / "app/transfer.py").read_text())

    # --- staleness --------------------------------------------------------------------------

    @verifies("scenario.issue-solving.stale-inputs")
    def test_changed_module_inputs_stop_the_step(self):
        for path in ("app/transfer.py", "specs/transfer/module.md"):
            with self.subTest(path=path):
                workflow = self.first_decision("not-actionable")
                before = self.issue_bytes()
                file = self.change / path
                original = file.read_bytes()
                file.write_bytes(original + b"\n# changed during the step\n")
                try:
                    with self.assertRaises(SpecError) as refused:
                        workflow.host_step("decision-0")
                    self.assertEqual("stale_context", refused.exception.code)
                    self.assert_open(before)
                    self.assertEqual([], self.solution()["history"])
                finally:
                    file.write_bytes(original)

    @verifies("scenario.issue-solving.duplicate-changed")
    def test_a_changed_or_unoffered_duplicate_is_refused(self):
        other = report_issue(
            self.change,
            transfer_report("same-overdraft"),
            source(invocation_id="other-reviewer", target_id="service.transfer"),
        )["issue_id"]
        unoffered = report_issue(
            self.change,
            transfer_report("rounding", title="Rounding is unstated"),
            source(invocation_id="third-reviewer", target_id="service.transfer"),
        )["issue_id"]
        commit_issues(self.change, "Record related problems")
        for duplicate in (other, unoffered):
            with self.subTest(duplicate=duplicate):
                workflow = self.start()
                workflow.host_step("next-0")
                workflow.decision(0, "duplicate", duplicate_of=duplicate)
                if duplicate == other:
                    _, revision = read_issue(self.change, other)
                    report_issue(
                        self.change,
                        transfer_report(
                            "later", issue_id=other, expected_revision=revision
                        ),
                        source(invocation_id="later", target_id="service.transfer"),
                    )
                before = self.issue_bytes()
                with self.assertRaises(SpecError) as refused:
                    workflow.host_step("decision-0")
                self.assertEqual("stale_issue", refused.exception.code)
                self.assert_open(before)
                self.assertNotIn("pending_disposition", self.solution())

    @verifies("scenario.issue-solving.step-replayed")
    def test_a_stale_or_duplicated_host_step_is_refused(self):
        workflow = self.start()
        workflow.host_step("next-0")
        workflow.decision(0, "needs-decision")
        for name in ("next-0", "verified-0", "decision-1"):
            with self.subTest(step=name):
                with self.assertRaises(SpecError) as refused:
                    workflow.host_step(name)
                self.assertEqual("invalid_completion", refused.exception.code)
                self.assertEqual([], self.solution()["history"])
        self.assertEqual("finished", workflow.host_step("decision-0")["route"])
        with self.assertRaises(SpecError) as refused:
            workflow.host_step("decision-0")
        self.assertEqual("invalid_completion", refused.exception.code)
        self.assertEqual(1, len(self.solution()["history"]))

    @verifies("scenario.issue-solving.uncorrelated-child")
    def test_a_result_without_its_native_child_is_not_admitted(self):
        workflow = self.start()
        workflow.host_step("next-0")
        before = self.issue_bytes()
        descriptor = workflow.slot_descriptor("d-0")
        workflow.child(
            "d-0",
            {
                "context_id": descriptor["snapshot"]["context_id"],
                "outcome": "completed",
                "answer": "Decided",
                "blockers": [],
                "documents": [],
                "plan": "",
                "tasks": [],
                "issue_decision": {
                    "action": "not-actionable",
                    "intent": "Close",
                    "rationale": "Mistaken",
                    "duplicate_of": None,
                },
            },
            publish=False,
        )
        with self.assertRaises(SpecError):
            workflow.host_step("decision-0")
        # A second terminal child for the same slot is not exactly one child either.
        workflow.status["workflow"]["emits"].extend(
            [
                {"kind": "concorde.child-terminal", "key": "d-0", "runId": "run-a"},
                {"kind": "concorde.child-terminal", "key": "d-0", "runId": "run-b"},
            ]
        )
        workflow.save()
        with self.assertRaises(SpecError):
            workflow.host_step("decision-0")
        self.assert_open(before)
        self.assertEqual([], self.solution()["history"])

    # --- recovery ---------------------------------------------------------------------------

    def interrupted_close(self, point):
        """Run a not-actionable close that the process loses at ``point``."""
        workflow = self.first_decision("not-actionable")
        dispose = solve_service.dispose_issue
        store = solve_service.store_solution

        def before_write(*args, **kwargs):
            raise OSError("process lost before the disposition")

        def after_write(*args, **kwargs):
            dispose(*args, **kwargs)
            raise OSError("process lost after the disposition")

        def before_completion(change, identifier, solution):
            if solution.get("status") == "completed":
                raise OSError("process lost before completion was saved")
            return store(change, identifier, solution)

        target, replacement = {
            "before-write": ("dispose_issue", before_write),
            "after-write": ("dispose_issue", after_write),
            "before-completion": ("store_solution", before_completion),
        }[point]
        with (
            patch.object(solve_service, target, side_effect=replacement),
            self.assertRaises(OSError),
        ):
            workflow.host_step("decision-0")
        self.assertIn("pending_disposition", self.solution())

    @verifies("scenario.issue-solving.recover-close")
    def test_an_interrupted_close_is_recovered_in_the_same_candidate(self):
        open_bytes = self.issue_bytes()
        for point in ("before-write", "after-write", "before-completion"):
            with self.subTest(point=point):
                self.interrupted_close(point)
                if point == "before-completion":
                    self.assertEqual("ready", self.change_state()["status"])
                worktrees = git_value(self.primary, "worktree", "list", "--porcelain")
                workflow = self.start()
                # Recovery restored the exact open bytes and withdrew any ready state.
                self.assertEqual(open_bytes, self.issue_bytes())
                change = self.change_state()
                self.assertNotEqual("ready", change["status"])
                solution = self.solution()
                self.assertNotIn("pending_disposition", solution)
                self.assertEqual(
                    ("active", None), (solution["status"], solution["verified_inputs"])
                )
                self.assertEqual(
                    worktrees,
                    git_value(self.primary, "worktree", "list", "--porcelain"),
                )
                workflow.host_step("next-0")
                workflow.decision(0, "not-actionable")
                workflow.host_step("decision-0")
                self.assert_closed_by_solver("not-actionable", workflow.output())
                self.reset_candidate()
                self.assertEqual(open_bytes, self.issue_bytes())

    @verifies("scenario.issue-solving.recovery-unprovable")
    def test_an_unprovable_recovery_is_refused_without_overwriting(self):
        for case in ("foreign-bytes", "corrupt-journal", "no-journal"):
            with self.subTest(case=case):
                if case == "no-journal":
                    workflow = self.first_decision("needs-decision")
                    workflow.host_step("decision-0")
                    context = self.solution()["history"][-1]["context_id"]
                    _, revision = self.record()
                    dispose_issue(
                        self.change,
                        self.issue,
                        revision,
                        reason="not-actionable",
                        note="Closed by a lost solve",
                        evidence=[context],
                        actor="concorde-issue-solver",
                    )
                else:
                    self.interrupted_close("after-write")
                    if case == "foreign-bytes":
                        _, revision = self.record()
                        dispose_issue(
                            self.change,
                            self.issue,
                            revision,
                            reason="reopened",
                            note="Concurrent edit",
                            evidence=["edit"],
                            actor="developer",
                        )
                    else:
                        change = self.change_state()
                        solution = self.solution()
                        solution["pending_disposition"]["after"] += " "
                        store_solution(change, self.issue, solution)
                        save_change(self.change, change)
                before = self.issue_bytes()
                value = self.prepare()
                self.assertEqual("rejected", value["state"], value)
                self.assertEqual(
                    "stale_issue"
                    if case == "foreign-bytes"
                    else "invalid_worktree_state",
                    value["result"]["errors"][0]["code"],
                )
                self.assertNotIn("descriptor", value)
                self.assertEqual(before, self.issue_bytes())
                # Start the next case from a fresh candidate state.
                self.reset_candidate()

    def reset_candidate(self):
        """Return to the committed open Issue and a change without a solve of it."""
        git_value(self.change, "checkout", "--", ".concorde/issues")
        change = read_change(self.change)
        if change is not None:
            solutions(change).pop(self.issue, None)
            change.update(status="active", outcome=None)
            save_change(self.change, change)
        self.assertEqual("open", self.record()[0]["status"])


if __name__ == "__main__":
    unittest.main()
