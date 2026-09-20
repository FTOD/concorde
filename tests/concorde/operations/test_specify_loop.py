"""Retained owner/consumer evidence guarantees, without the deleted specification loop."""

import json
import unittest
from pathlib import Path
from typing import Any

from concorde.harness.change_worktree import (
    bind_owner,
    ensure_change,
    read_change,
    save_change,
)
from concorde.harness.invocation import Invocation
from concorde.review.review import current_spec_scope, verify_required
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import artifact, canonical
from concorde.spec.verification import verifies
from tests.concorde.operations import test_review as fixtures


class SpecReviewFreshnessTests(unittest.TestCase):
    root: Path
    task: dict[str, Any]
    configuration: dict[str, Any]
    model: fixtures.ModelProcessDouble
    host: fixtures.OperationHost
    setUp = fixtures.ReviewTests.setUp
    double = fixtures.ReviewTests.double
    call_operation = fixtures.ReviewTests.call_operation
    missing = fixtures.ReviewTests.missing
    gap = staticmethod(fixtures.ReviewTests.gap)

    def add_spec_consumer(self):
        path = self.root / ".concorde/specs.json"
        registry = json.loads(path.read_text())
        bank = next(t for t in registry["targets"] if t["id"] == "scope.bank")
        bank["references"].append({"kind": "module", "id": "service.transfer"})
        path.write_text(json.dumps(registry))
        ensure_change(self.root, task=self.task, allow_primary=True)
        bind_owner(self.root, self.task)

    def invocation(self):
        return Invocation(
            "concorde-spec-review", self.configuration, self.task, self.host
        )

    def spec_review_targets(self):
        return [
            c["snapshot"]["target_id"]
            for c in self.model.calls
            if c["stage"] == "spec-review"
        ]

    @staticmethod
    def consumer_finding(severity):
        return {
            "id": "consumer-note",
            "severity": severity,
            "target_id": "scope.bank",
            "document": "specs/bank/module.md",
            "contract": "The bank contract",
            "location": {"path": "specs/bank/module.md", "line": 1},
            "problem": "Controlled consumer review finding.",
            "affected_task": "Review bank reliance",
        }

    @verifies("scenario.review.consumer-currentness")
    def test_explicit_review_is_fresh_and_current_scope_reuses_only_evidence(self):
        self.add_spec_consumer()

        def advisory(stage, snapshot, data, cwd):
            if snapshot["target_id"] == "scope.bank":
                data.update(
                    status="findings", issues=[self.consumer_finding("advisory")]
                )

        first = self.call_operation("concorde-spec-review", callback=advisory)
        self.assertEqual("succeeded", first["status"], first)
        self.assertCountEqual(
            ["service.transfer", "scope.bank"], self.spec_review_targets()
        )
        evidence = current_spec_scope(self.invocation())
        self.assertEqual(first["output"]["data"]["artifacts"], evidence)
        verify_required(self.invocation())
        fresh = self.call_operation("concorde-spec-review")
        self.assertEqual("succeeded", fresh["status"], fresh)
        self.assertCountEqual(
            ["service.transfer", "scope.bank"], self.spec_review_targets()
        )
        self.assertNotEqual(evidence, current_spec_scope(self.invocation()))
        # Historical report bytes remain accessible after the new assessment.
        self.assertTrue(all((self.root / ref["path"]).is_file() for ref in evidence))

    @verifies("scenario.review.consumer-currentness")
    def test_direct_paired_edit_requires_complete_owner_and_consumer_review(self):
        self.add_spec_consumer()
        self.assertEqual(
            "succeeded", self.call_operation("concorde-spec-review")["status"]
        )
        old = current_spec_scope(self.invocation())
        document = self.root / "specs/transfer/module.md"
        document.write_text(
            document.read_text() + "\nTransfer rounds amounts to cents.\n"
        )
        metadata = Path(str(document) + ".json")
        metadata.write_text(metadata.read_text() + "\n")
        self.assertIsNone(current_spec_scope(self.invocation()))
        with self.assertRaises(SpecError):
            verify_required(self.invocation())
        blocked = self.call_operation("concorde-plan")
        self.assertEqual("review_required", blocked["errors"][0]["code"], blocked)
        self.assertEqual([], self.model.calls)
        fresh = self.call_operation("concorde-spec-review")
        self.assertEqual("succeeded", fresh["status"], fresh)
        self.assertCountEqual(
            ["service.transfer", "scope.bank"], self.spec_review_targets()
        )
        for call in self.model.calls:
            paths = {s["path"] for s in call["snapshot"]["spec_resolution"]["sources"]}
            self.assertTrue(
                {"specs/transfer/module.md", "specs/transfer/module.md.json"} <= paths
            )
            self.assertEqual([], call["snapshot"]["implementation_artifacts"])
            self.assertEqual((), call["launch"].write_paths)
        self.assertNotEqual(old, current_spec_scope(self.invocation()))
        verify_required(self.invocation())
        record = read_change(self.root, required=True)["shared_spec_reviews"][
            "service.transfer"
        ]["scope.bank"]
        self.assertEqual(
            "Review this Module's reliance on the changed canonical Spec. "
            + self.task["task"],
            record["task"],
        )

    @verifies("scenario.review.consumer-currentness")
    def test_changed_consumer_metadata_or_reference_requires_fresh_scope_review(self):
        self.add_spec_consumer()
        for edit in ("metadata", "reference"):
            with self.subTest(edit=edit):
                self.assertEqual(
                    "succeeded", self.call_operation("concorde-spec-review")["status"]
                )
                if edit == "metadata":
                    path = self.root / "specs/bank/module.md.json"
                    path.write_text(path.read_text() + "\n")
                else:
                    path = self.root / ".concorde/specs.json"
                    registry = json.loads(path.read_text())
                    bank = next(
                        t for t in registry["targets"] if t["id"] == "scope.bank"
                    )
                    bank["references"].append(
                        {"kind": "document", "id": "document.transfer.promises"}
                    )
                    path.write_text(json.dumps(registry))
                self.assertIsNone(current_spec_scope(self.invocation()))
                with self.assertRaises(SpecError):
                    verify_required(self.invocation())
                result = self.call_operation("concorde-spec-review")
                self.assertEqual("succeeded", result["status"], result)
                self.assertIn("scope.bank", self.spec_review_targets())
                verify_required(self.invocation())

    @verifies("scenario.review.consumer-currentness")
    def test_missing_corrupt_or_incomplete_consumer_evidence_cannot_be_reused(self):
        for defect in (
            "missing_record",
            "missing_file",
            "corrupt",
            "incomplete",
            "skipped",
            "empty_coverage",
            "blocking",
            "blockers",
            "old_task",
            "old_constraints",
        ):
            with self.subTest(defect=defect):
                fixture = SpecReviewFreshnessTests()
                fixture.setUp()
                try:
                    fixture.add_spec_consumer()
                    self.assertEqual(
                        "succeeded",
                        fixture.call_operation("concorde-spec-review")["status"],
                    )
                    state = read_change(fixture.root, required=True)
                    records = state["shared_spec_reviews"]["service.transfer"]
                    record = records["scope.bank"]
                    reference = record["artifact"]
                    path = fixture.root / reference["path"]
                    if defect == "missing_record":
                        records.pop("scope.bank")
                    elif defect == "missing_file":
                        path.unlink()
                    elif defect == "corrupt":
                        path.write_text(path.read_text() + "\n")
                    elif defect == "old_task":
                        record["task"] = "A different consumer task"
                    elif defect == "old_constraints":
                        record["constraints"] = ["A different constraint"]
                    else:
                        value = json.loads(path.read_text())
                        if defect == "empty_coverage":
                            value["data"]["representative_tasks"] = []
                        elif defect == "blocking":
                            value["data"].update(
                                status="findings",
                                issues=[self.consumer_finding("blocking")],
                            )
                        elif defect == "blockers":
                            value["data"]["blockers"] = [
                                {"needed_contract": "Bank promise"}
                            ]
                        else:
                            value["data"]["status"] = defect
                        path.write_text(canonical(value) + "\n")
                        record["artifact"] = artifact(
                            fixture.root, reference["id"], reference["path"]
                        )
                    save_change(
                        fixture.root, state
                    )  # Deliberately corrupt fixture evidence only.
                    self.assertIsNone(current_spec_scope(fixture.invocation()))
                    with self.assertRaises(SpecError):
                        verify_required(fixture.invocation())
                    rejected = fixture.call_operation("concorde-plan")
                    self.assertEqual(
                        "review_required", rejected["errors"][0]["code"], rejected
                    )
                    self.assertEqual([], fixture.model.calls)
                    result = fixture.call_operation("concorde-spec-review")
                    self.assertEqual("succeeded", result["status"], result)
                    self.assertIn("scope.bank", fixture.spec_review_targets())
                    verify_required(fixture.invocation())
                finally:
                    fixture.doCleanups()

    @verifies("scenario.review.consumer-currentness")
    def test_failed_consumer_review_needs_explicit_fresh_success(self):
        self.add_spec_consumer()

        def fail(stage, snapshot, data, cwd):
            if snapshot["target_id"] == "scope.bank":
                raise RuntimeError("controlled failed consumer")

        first = self.call_operation("concorde-spec-review", callback=fail)
        self.assertEqual("failed", first["status"], first)
        self.assertIsNone(current_spec_scope(self.invocation()))
        with self.assertRaises(SpecError):
            verify_required(self.invocation())
        retry = self.call_operation("concorde-spec-review")
        self.assertEqual("succeeded", retry["status"], retry)
        self.assertIn("scope.bank", self.spec_review_targets())
        self.assertIsNotNone(current_spec_scope(self.invocation()))
        verify_required(self.invocation())

    @verifies(
        "scenario.review.consumer-currentness",
        "scenario.planning.historical-author-gap",
    )
    def test_consumer_historical_gap_is_task_attributed_for_reuse_and_readiness(self):
        from concorde.harness.change_worktree import record_task_gaps
        from concorde.issues.store import report_issue
        from tests.concorde.issues.test_store import report, source

        self.add_spec_consumer()
        self.assertEqual(
            "succeeded", self.call_operation("concorde-spec-review")["status"]
        )
        state = read_change(self.root, required=True)
        peer = state["shared_spec_reviews"]["service.transfer"]["scope.bank"]
        consumer_task = {
            "target_id": "scope.bank",
            "task": peer["task"],
            "constraints": peer["constraints"],
        }
        run = Invocation(
            "concorde-context-solve", self.configuration, consumer_task, self.host
        )
        ref = report_issue(
            self.root,
            report(owner_target_id="scope.bank", evidence=[]),
            source(
                target_id="scope.bank", operation="concorde-specify", phase="specify"
            ),
        )
        record_task_gaps(
            self.root,
            "scope.bank",
            peer["task"] + " Unrelated",
            "specify",
            [{**ref, "blocked_step": "Independent question"}],
            run.blocker_revision("specify"),
        )
        self.assertIsNotNone(current_spec_scope(self.invocation()))
        verify_required(self.invocation())
        record_task_gaps(
            self.root,
            "scope.bank",
            peer["task"],
            "specify",
            [{**ref, "blocked_step": "Review bank reliance"}],
            run.blocker_revision("specify"),
        )
        history = read_change(self.root, required=True)["issue_blockers"]
        self.assertIsNone(current_spec_scope(self.invocation()))
        with self.assertRaises(SpecError):
            verify_required(self.invocation())
        path = self.root / "specs/bank/module.md"
        path.write_text(path.read_text() + "\nBank owns retry decisions.\n")
        result = self.call_operation("concorde-context-solve", consumer_task)
        self.assertEqual("succeeded", result["status"], result)
        updated = read_change(self.root, required=True)["issue_blockers"]
        self.assertEqual("open", updated[0]["status"])
        self.assertEqual("superseded", updated[1]["status"])
        self.assertEqual(history[1]["contexts"], updated[1]["contexts"])
        self.assertEqual(
            "succeeded", self.call_operation("concorde-spec-review")["status"]
        )
        verify_required(self.invocation())


if __name__ == "__main__":
    unittest.main()
