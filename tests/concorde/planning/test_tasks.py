"""Native task authoring in a managed candidate: acceptance, refusals and reserved identities."""

import json
import unittest
from pathlib import Path

from concorde.harness.change_worktree import git_value
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate, task_item


class TaskAuthoringTests(NativeCandidate, unittest.TestCase):
    def stage_inputs(self, prepared):
        return {
            value["type_id"]: value["data"]
            for value in self.descriptor(prepared)["stage_inputs"]
        }

    def author(self, tasks):
        """Prepare a fresh task author and submit ``tasks`` as its completed answer."""
        prepared = self.prepare("concorde-tasks")
        self.assertEqual("prepared", prepared["state"], prepared)
        data = self.stage_result(prepared, outcome="completed", tasks=tasks)
        return prepared, data

    def submit(self, prepared, data):
        return self.action(prepared, "submit", self.proposal(prepared, data))

    @verifies("scenario.planning.tasks-from-plan")
    def test_an_accepted_plan_yields_a_saved_task_list(self):
        self.own()
        self.accepted_plan()
        tracked = git_value(self.change, "status", "--porcelain")
        tasks = [
            task_item("transfer-rounding"),
            task_item("ledger-read", "module.ledger"),
        ]
        prepared, data = self.author(tasks)
        value = self.complete(prepared, data)
        self.assertEqual(("accepted", True), (value["state"], value["accepted"]))
        output = value["result"]["output"]["data"]
        self.assertEqual("completed", output["outcome"])
        record = self.target()
        self.assertEqual(tasks, record["tasks"])
        self.assertEqual("tasks", record["phase"])
        # The result references the candidate's change record holding the list.
        change_id = self.change_state()["change_id"]
        self.assertEqual(
            [f".concorde/status/{change_id}.json"],
            [item["path"] for item in output["artifacts"]],
        )
        # The task author completed nothing and wrote no project file.
        self.assertFalse(any(task["complete"] for task in record["tasks"]))
        self.assertEqual(tracked, git_value(self.change, "status", "--porcelain"))

    @verifies("scenario.planning.tasks-missing-plan")
    def test_task_authoring_without_a_plan_is_refused_before_an_agent(self):
        self.own()
        before = self.change_state()
        self.refused(self.prepare("concorde-tasks"), "missing_plan")
        self.assertIsNone(self.target())
        after = self.change_state()
        self.assertEqual(before.get("sections"), after.get("sections"))

    @verifies("scenario.planning.tasks-foreign-target")
    def test_a_task_outside_the_change_scope_is_refused(self):
        self.own()
        self.accepted_plan()
        before = self.target()
        # Audit is registered but outside the transfer Module's change scope.
        prepared, data = self.author(
            [task_item("transfer-rounding"), task_item("audit-log", "scope.audit")]
        )
        submitted = self.submit(prepared, data)
        self.assertEqual("rejected", submitted["state"], submitted)
        self.assertEqual(
            ["permission_denied"], [e["code"] for e in submitted["result"]["errors"]]
        )
        # The invalidated call accepts nothing and no list is saved.
        staged = self.action(prepared, "stage")
        self.assertEqual("rejected", staged["state"])
        self.assertEqual(before, self.target())
        self.assertEqual([], self.target()["tasks"])

    @verifies("scenario.planning.task-history-identities")
    def test_the_task_author_receives_every_reserved_identity(self):
        self.own()
        self.accepted_plan()
        self.accepted_tasks([task_item("first")])
        # A replacement moves the first list to the history; a new plan moves the second.
        self.accepted_tasks([task_item("second")])
        prepared, _ = self.author([])
        inputs = self.stage_inputs(prepared)
        self.assertEqual(
            ["first", "second"],
            inputs["concorde-task-identity-constraints"]["reserved_task_ids"],
        )
        self.accepted_plan("A new plan")
        prepared, _ = self.author([])
        inputs = self.stage_inputs(prepared)
        self.assertEqual(
            ["first", "second"],
            inputs["concorde-task-identity-constraints"]["reserved_task_ids"],
        )
        # The identities constrain naming only: no current list or feedback is work to do.
        self.assertEqual(
            {"concorde-plan-artifact", "concorde-task-identity-constraints"},
            set(inputs),
        )
        self.assertEqual({"plan": "A new plan"}, inputs["concorde-plan-artifact"])

    @verifies("scenario.planning.tasks-id-conflict")
    def test_a_reused_reserved_identity_is_refused_with_the_collisions(self):
        self.own()
        self.accepted_plan()
        self.accepted_tasks([task_item("first")])
        self.accepted_tasks([task_item("second")])
        before = self.target()
        for reused in (["first"], ["second"], ["first", "second"]):
            with self.subTest(reused=reused):
                tasks = [task_item(identity) for identity in [*reused, "fresh"]]
                prepared, data = self.author(tasks)
                submitted = self.submit(prepared, data)
                self.assertEqual("rejected", submitted["state"], submitted)
                [error] = submitted["result"]["errors"]
                self.assertEqual("invalid_completion", error["code"])
                self.assertTrue(
                    error["message"].endswith(": " + ", ".join(sorted(reused))),
                    error["message"],
                )
                # The Agent's answer is kept as submitted, never rewritten to fit.
                self.assertEqual(
                    self.proposal(prepared, data),
                    json.loads(
                        (
                            Path(prepared["descriptor"]).parent / "proposal.json"
                        ).read_text()
                    ),
                )
                self.assertEqual(before, self.target())


if __name__ == "__main__":
    unittest.main()
