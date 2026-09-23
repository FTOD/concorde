"""Required reviews recorded on a candidate: currentness, the Spec gate and no downgrade."""

import json
import unittest

from concorde.harness.change_worktree import save_change
from concorde.harness.revisions import target_revision
from concorde.harness.status_store import (
    read_record,
    record_artifact,
    run_path,
    write_run,
)
from concorde.issues.store import report_issue
from concorde.planning.gaps import record_task_gaps
from concorde.review.records import recorded, review_records
from concorde.review.review import (
    require_reviews,
    require_spec_review,
    verify_required,
)
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import canonical
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate
from tests.concorde.support.spec_project import update_module


class RequiredReviewTests(NativeCandidate, unittest.TestCase):
    def assert_required(self, run=None):
        with self.assertRaises(SpecError) as raised:
            require_spec_review(run or self.invocation("concorde-plan"))
        self.assertEqual("review_required", raised.exception.code)

    def consumer_record(self):
        return recorded(self.change_state(), "shared_spec_reviews")["service.transfer"][
            "scope.bank"
        ]

    def set_consumer_record(self, record):
        state = self.change_state()
        review_records(state)["shared_spec_reviews"]["service.transfer"][
            "scope.bank"
        ] = record
        save_change(self.change, state)

    def variant_artifact(self, record, **fields):
        """Save a modified copy of a consumer's report as a run record and reference it."""
        value = json.loads(read_record(self.change, record["artifact"]["path"]))
        value["data"].update(fields)
        path = ".concorde/runs/fixture/review-variant-" + str(len(fields)) + ".json"
        path = path.replace(".json", "-" + "-".join(sorted(fields)) + ".json")
        write_run(self.change, path, (canonical(value) + "\n").encode())
        return {**record, "artifact": record_artifact(self.change, "review", path)}

    def reviewed_consumers(self):
        """A required Spec review of Transfers and of its consumer Banking, both current."""
        self.own()
        spec = self.change / "specs/transfer/module.md"
        spec.write_bytes(spec.read_bytes() + b"\nTransfers round half to even.\n")
        workflow, _ = self.run_review("spec", self.task)
        self.assertEqual(["service.transfer", "scope.bank"], workflow.members())
        require_spec_review(self.invocation("concorde-plan"))
        return spec

    @verifies("scenario.review.consumer-currentness")
    def test_a_changed_document_metadata_or_intent_invalidates_the_review(self):
        spec = self.reviewed_consumers()
        with self.subTest(case="document"):
            spec.write_bytes(spec.read_bytes() + b"\nTransfers never round twice.\n")
            self.assert_required()
            # The Module and each current consumer need their own fresh result.
            self.run_review("spec", self.task)
            require_spec_review(self.invocation("concorde-plan"))
        with self.subTest(case="metadata and registration"):
            metadata = self.change / "specs/transfer/module.md.json"
            registry = self.change / ".concorde/specs.json"
            originals = metadata.read_bytes(), registry.read_bytes()
            update_module(self.change, "service.transfer", title="Money transfers")
            self.assert_required()
            metadata.write_bytes(originals[0])
            registry.write_bytes(originals[1])
            require_spec_review(self.invocation("concorde-plan"))
        with self.subTest(case="intent"):
            self.assert_required(
                self.invocation("concorde-plan", {**self.task, "constraints": ["New"]})
            )

    @verifies("scenario.review.consumer-currentness")
    def test_only_a_current_complete_consumer_result_satisfies_the_review(self):
        self.reviewed_consumers()
        record = self.consumer_record()
        report = run_path(self.change, record["artifact"]["path"])
        with self.subTest(case="missing consumer result"):
            state = self.change_state()
            reviews = review_records(state)["shared_spec_reviews"]["service.transfer"]
            reviews.pop("scope.bank")
            save_change(self.change, state)
            self.assert_required()
            self.set_consumer_record(record)
            require_spec_review(self.invocation("concorde-plan"))
        with self.subTest(case="corrupt consumer result"):
            original = report.read_bytes()
            report.write_bytes(original.replace(b"no_findings", b"findings", 1))
            self.assert_required()
            report.write_bytes(original)
            require_spec_review(self.invocation("concorde-plan"))
        issue = report_issue(
            self.change,
            {
                "report_key": "consumer-blocker",
                "type": "bug",
                "subtype": None,
                "title": "Banking misreads rounding",
                "description": "Banking assumes transfers never round.",
                "impact": "Banking totals drift.",
                "basis": "The changed transfer promise.",
                "owner_target_id": "scope.bank",
                "evidence": [],
            },
            {
                "invocation_id": "fixture",
                "agent": "spec_reviewer",
                "operation": "concorde-spec-review",
                "phase": "spec-review",
                "target_id": "scope.bank",
                "context_id": "sha256:" + "1" * 64,
                "change_id": self.change_state()["change_id"],
                "head": None,
            },
        )
        # An unmodified copy of the consumer's report satisfies the requirement.
        self.set_consumer_record(self.variant_artifact(record))
        require_spec_review(self.invocation("concorde-plan"))
        for case, fields in (
            ("incomplete", {"status": "incomplete"}),
            (
                "blocking",
                {
                    "status": "findings",
                    "issues": [
                        {**issue, "severity": "blocking", "affected_task": "Totals"}
                    ],
                },
            ),
            ("empty coverage", {"representative_tasks": []}),
            ("unrelated", {"target_id": "scope.audit"}),
        ):
            with self.subTest(case=case):
                self.set_consumer_record(self.variant_artifact(record, **fields))
                self.assert_required()
                self.set_consumer_record(record)
                require_spec_review(self.invocation("concorde-plan"))
        with self.subTest(case="open pending gap for the same input"):
            data = json.loads(report.read_text())["data"]
            repository = self.invocation("concorde-plan").repository
            record_task_gaps(
                self.change,
                "scope.bank",
                record["task"],
                "spec-review",
                [{**issue, "blocked_step": "Totals"}],
                target_revision(repository, repository.module("scope.bank")),
                review_input_digest=data["input_digest"],
            )
            self.assert_required()

    @verifies("scenario.review.spec-gate")
    def test_a_blocking_required_spec_review_gates_planning_and_implementation(self):
        self.own()
        _, output = self.run_review("spec", self.task, blocking={"service.transfer"})
        self.assertEqual("conflicting", output["outcome"], output)
        self.assertTrue(
            recorded(self.change_state(), "requirements")["service.transfer"]["spec"]
        )
        for operation in ("concorde-plan", "concorde-tasks", "concorde-implement"):
            with self.subTest(operation=operation):
                self.refused(self.prepare(operation), "review_required")
        assessed = self.prepare("concorde-context-solve")
        self.assertEqual("prepared", assessed["state"], assessed)

    @verifies("scenario.review.no-downgrade")
    def test_a_review_with_another_task_keeps_the_requirement(self):
        self.own()
        owner = self.invocation("concorde-code-review")
        require_reviews(owner, True, modes=["code"])
        other = {"target_id": "service.transfer", "task": "Check rounding only"}
        _, output = self.run_review("code", other)
        # The review runs and its result is saved as evidence.
        self.assertEqual("completed", output["outcome"])
        [artifact] = output["artifacts"]
        self.assertTrue(run_path(self.change, artifact["path"]).is_file())
        # The requirement stays recorded and the new result does not satisfy it.
        state = self.change_state()
        self.assertTrue(recorded(state, "requirements")["service.transfer"]["code"])
        self.assertNotIn("code", recorded(state, "reviews").get("service.transfer", {}))
        with self.assertRaises(SpecError) as raised:
            verify_required(owner)
        self.assertEqual("review_required", raised.exception.code)
        # An explicit request without the requirement cannot downgrade it either.
        require_reviews(owner, False, modes=["code"])
        self.assertTrue(
            recorded(self.change_state(), "requirements")["service.transfer"]["code"]
        )


if __name__ == "__main__":
    unittest.main()
