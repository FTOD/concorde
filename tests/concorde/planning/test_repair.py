"""Task repairs: from current code-review evidence and from the programmer's task scope."""

import unittest

from concorde.harness.status_store import run_path
from concorde.planning.records import save_target_state
from concorde.review.records import recorded
from concorde.review.review import verify_required
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import (
    NativeCandidate,
    task_item,
    tasks_digest,
)


class RepairTests(NativeCandidate, unittest.TestCase):
    def planned(self, *identities):
        self.own()
        self.accepted_plan()
        self.accepted_tasks([task_item(identity) for identity in identities])

    def code_review_reference(self):
        return recorded(self.change_state(), "reviews")["service.transfer"]["code"][
            "artifact"
        ]

    def reviewed(self):
        """Accepted tasks and a completed code review of them with a blocking finding."""
        self.planned("first")
        _, output = self.run_review("code", blocking={"service.transfer"})
        self.assertEqual("conflicting", output["outcome"], output)
        return self.code_review_reference()

    def repair_request(self, **fields):
        return {**self.task, **fields}

    def stage_inputs(self, prepared):
        return {
            value["type_id"]: value["data"]
            for value in self.descriptor(prepared)["stage_inputs"]
        }

    def author(self, request, tasks):
        prepared = self.prepare("concorde-tasks", request)
        self.assertEqual("prepared", prepared["state"], prepared)
        data = self.stage_result(prepared, outcome="completed", tasks=tasks)
        return prepared, data

    def repair(self, reference, identity):
        prepared, data = self.author(
            self.repair_request(repair_review=reference), [task_item(identity)]
        )
        value = self.complete(prepared, data)
        self.assertTrue(value["accepted"], value)
        return prepared

    @verifies("scenario.planning.repair-current")
    def test_a_current_blocking_code_review_admits_a_review_repair(self):
        reference = self.reviewed()
        prepared, data = self.author(
            self.repair_request(repair_review=reference), [task_item("second")]
        )
        inputs = self.stage_inputs(prepared)
        # The current list, the review result and the context of the Issues it cites.
        self.assertEqual(
            ["first"],
            [t["id"] for t in inputs["concorde-implementation-task"]["tasks"]],
        )
        review = inputs["concorde-review-result"]
        self.assertEqual(
            ("findings", "service.transfer"), (review["status"], review["target_id"])
        )
        cited = {issue["issue_id"] for issue in review["issues"]}
        self.assertEqual(
            cited,
            {
                item["receipt"]["issue_id"]
                for item in inputs["concorde-issue-context"]["observations"]
            },
        )
        value = self.complete(prepared, data)
        self.assertTrue(value["accepted"], value)
        record = self.target()
        self.assertEqual(["second"], [t["id"] for t in record["tasks"]])
        # The accepted list keeps the review reference for implementation.
        self.assertEqual(reference, record["repair_review"])
        self.assertEqual(
            ("review_feedback", ["first"]),
            (
                record["task_history"][-1]["reason"],
                [t["id"] for t in record["task_history"][-1]["tasks"]],
            ),
        )

    @verifies("scenario.planning.repair-stale")
    def test_a_review_repair_with_stale_evidence_is_refused_before_an_agent(self):
        reference = self.reviewed()
        before = self.target()
        report = run_path(self.change, reference["path"])
        original = report.read_bytes()

        def refused(value, codes):
            self.assertEqual("rejected", value["state"], value)
            self.assertNotIn("descriptor", value)
            self.assertLessEqual(
                {e["code"] for e in value["result"]["errors"]}, codes, value
            )
            self.assertEqual(before, self.target())

        with self.subTest(case="missing"):
            missing = {**reference, "path": reference["path"] + ".missing"}
            refused(
                self.prepare(
                    "concorde-tasks", self.repair_request(repair_review=missing)
                ),
                {"stale_evidence"},
            )
        with self.subTest(case="corrupt"):
            report.write_bytes(original.replace(b"findings", b"no_findings", 1))
            try:
                refused(
                    self.prepare(
                        "concorde-tasks", self.repair_request(repair_review=reference)
                    ),
                    {"stale_reference"},
                )
            finally:
                report.write_bytes(original)
        with self.subTest(case="changed code"):
            code = self.change / "app/transfer.py"
            source = code.read_bytes()
            code.write_bytes(source + b"# changed after the review\n")
            try:
                refused(
                    self.prepare(
                        "concorde-tasks", self.repair_request(repair_review=reference)
                    ),
                    {"stale_evidence"},
                )
            finally:
                code.write_bytes(source)
        # A later review without a blocking finding replaces the recorded one.
        self.run_review("code")
        later = self.code_review_reference()
        self.assertNotEqual(reference, later)
        before = self.target()
        with self.subTest(case="replaced"):
            refused(
                self.prepare(
                    "concorde-tasks", self.repair_request(repair_review=reference)
                ),
                {"stale_evidence"},
            )
        with self.subTest(case="no blocking finding"):
            refused(
                self.prepare(
                    "concorde-tasks", self.repair_request(repair_review=later)
                ),
                {"incompatible_handoff"},
            )

    @verifies("scenario.planning.repair-replacement")
    def test_replacing_repaired_tasks_drops_the_feedback_and_keeps_the_history(self):
        reference = self.reviewed()
        self.repair(reference, "second")
        self.assertEqual(reference, self.target()["repair_review"])
        # A replacement without repair feedback.
        self.accepted_tasks([task_item("third")])
        record = self.target()
        self.assertNotIn("repair_review", record)
        self.assertEqual("caller_replacement", record["task_history"][-1]["reason"])
        history = [t["id"] for entry in record["task_history"] for t in entry["tasks"]]
        self.assertEqual(["first", "second"], history)
        # A new plan after another repair.
        self.repair(reference, "fourth")
        self.accepted_plan("A new plan")
        record = self.target()
        self.assertNotIn("repair_review", record)
        self.assertEqual("replan", record["task_history"][-1]["reason"])
        prepared, _ = self.author(self.task, [])
        self.assertEqual(
            ["first", "fourth", "second", "third"],
            self.stage_inputs(prepared)["concorde-task-identity-constraints"][
                "reserved_task_ids"
            ],
        )
        # The required code review still needs fresh evidence.
        with self.assertRaises(SpecError) as raised:
            verify_required(self.invocation("concorde-validate"))
        self.assertEqual("review_required", raised.exception.code)

    @verifies("scenario.planning.scope-repair")
    def test_a_scope_repair_replaces_the_current_list_without_a_new_plan(self):
        self.planned("first", "second")
        current = self.target()["tasks"]
        request = self.repair_request(
            repair_task_scope={"tasks_digest": tasks_digest(current)}
        )
        prepared, data = self.author(request, [task_item("narrower")])
        inputs = self.stage_inputs(prepared)
        self.assertEqual(
            {
                "tasks_digest": tasks_digest(current),
                "reason": "implementation_boundary",
            },
            inputs["concorde-task-scope-feedback"],
        )
        self.assertEqual(current, inputs["concorde-implementation-task"]["tasks"])
        value = self.complete(prepared, data)
        self.assertTrue(value["accepted"], value)
        record = self.target()
        self.assertEqual([task_item("narrower")], record["tasks"])
        self.assertEqual("Accepted plan", record["plan"])
        entry = record["task_history"][-1]
        self.assertEqual(
            ("implementation_boundary", tasks_digest(current), current),
            (entry["reason"], entry["tasks_digest"], entry["tasks"]),
        )
        self.assertEqual(record["spec_digest"], entry["spec_digest"])

    @verifies("scenario.planning.scope-repair-refused")
    def test_an_invalid_scope_repair_changes_nothing(self):
        self.planned("first", "second")
        current = self.target()["tasks"]
        valid = {"tasks_digest": tasks_digest(current)}

        def refused(request, code):
            before = self.target()
            self.refused(self.prepare("concorde-tasks", request), code)
            self.assertEqual(before, self.target())

        with self.subTest(case="digest mismatch"):
            refused(
                self.repair_request(
                    repair_task_scope={"tasks_digest": tasks_digest(current[:1])}
                ),
                "incompatible_handoff",
            )
        with self.subTest(case="with a review repair"):
            reference = {
                "id": "review.service.transfer.code",
                "path": ".concorde/runs/fixture/review.json",
                "digest": "sha256:" + "d" * 64,
            }
            refused(
                self.repair_request(repair_task_scope=valid, repair_review=reference),
                "incompatible_handoff",
            )
        with self.subTest(case="stale plan"):
            spec = self.change / "specs/transfer/module.md"
            original = spec.read_bytes()
            spec.write_bytes(original + b"\nA later promise.\n")
            try:
                refused(self.repair_request(repair_task_scope=valid), "stale_context")
            finally:
                spec.write_bytes(original)
        with self.subTest(case="every task complete"):
            state = self.target()
            state["tasks"] = [dict(task, complete=True) for task in state["tasks"]]
            save_target_state(self.change, state)
            completed = {"tasks_digest": tasks_digest(state["tasks"])}
            refused(
                self.repair_request(repair_task_scope=completed),
                "incompatible_handoff",
            )


if __name__ == "__main__":
    unittest.main()
