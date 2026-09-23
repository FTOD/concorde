"""The review workflow through the native driver, with scripted reviewers and synthetic evidence."""

import tempfile
import unittest
from pathlib import Path

from concorde.harness.change_worktree import git_value, read_change
from concorde.harness.status_store import run_path
from concorde.review.records import recorded
from concorde.review.review import require_spec_review
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate, failure_codes

REVIEW = {"target_id": "service.transfer", "task": "Review the transfer contract"}
READ_ONLY = {"read", "grep", "find", "ls", "run_checks", "report_issue"}


def front_matter(path: Path) -> dict:
    """The fields of a prepared native Agent file."""
    text = path.read_text()
    header = text.split("---\n")[1]
    return dict(line.split(": ", 1) for line in header.splitlines())


class ReviewWorkflowTests(NativeCandidate, unittest.TestCase):
    def reports(self, root):
        directory = run_path(root, ".concorde/runs/x").parent
        return sorted(directory.glob("*/review-*.json"))

    def recorded_reviews(self):
        return recorded(self.change_state(), "reviews").get("service.transfer", {})

    def edit_transfer_spec(self):
        """A candidate edit of a document Banking selects, so Banking is a consumer."""
        spec = self.change / "specs/transfer/module.md"
        spec.write_bytes(spec.read_bytes() + b"\nTransfers round half to even.\n")

    @verifies("scenario.review.standalone")
    def test_a_standalone_review_saves_a_report_and_changes_nothing(self):
        (self.primary / "app/transfer.py").write_text(
            "def transfer(balance, amount):\n    return balance - amount\n"
        )
        (self.primary / "secret.py").write_text("PRIVATE = 'changed'\n")
        status = git_value(self.primary, "status", "--porcelain")
        request = {**REVIEW, "focus_id": "scenario.transfer.debit"}
        for mode in ("spec", "code"):
            with self.subTest(mode=mode):
                workflow, output = self.run_review(mode, request, root=self.primary)
                # Without a change, every Module selecting the Spec is a Spec consumer.
                self.assertEqual(
                    ["service.transfer", *(["scope.bank"] if mode == "spec" else [])],
                    workflow.members(),
                )
                descriptor = workflow.slot_descriptor("review-0")
                snapshot = descriptor["snapshot"]
                # The Module's complete context, focused on the requested scenario.
                self.assertEqual(
                    ("service.transfer", "scenario.transfer.debit"),
                    (snapshot["target_id"], snapshot["focus_id"]),
                )
                self.assertIn(
                    "specs/transfer/module.md", snapshot["spec_resolution"]["documents"]
                )
                changes = [c["path"] for c in descriptor["review_input"]["changes"]]
                # Code review sees only the Module's bound files changed since HEAD.
                self.assertEqual(["app/transfer.py"] if mode == "code" else [], changes)
                # No write, edit, shell or delegation tools.
                agent = front_matter(
                    Path(descriptor["directory"])
                    / "context/.pi/agents"
                    / (descriptor["external"] + ".md")
                )
                self.assertLessEqual(set(agent["tools"].split(", ")), READ_ONLY)
                self.assertEqual("false", agent["allowNestedSubagents"])
                # Coverage, findings and outcome, and a saved report.
                self.assertEqual("completed", output["outcome"])
                review = output["reviews"][0]
                self.assertEqual(
                    (["Review the transfer contract"], [], "no_findings"),
                    (
                        review["data"]["representative_tasks"],
                        review["data"]["issues"],
                        review["data"]["status"],
                    ),
                )
                for artifact in output["artifacts"]:
                    self.assertTrue(run_path(self.primary, artifact["path"]).is_file())
        # No change was created and no Spec document or implementation file changed.
        self.assertIsNone(read_change(self.primary))
        self.assertEqual(status, git_value(self.primary, "status", "--porcelain"))

    @verifies("scenario.review.preview")
    def test_a_preview_lists_the_scope_without_a_reviewer_or_report(self):
        self.own()
        self.edit_transfer_spec()
        before = self.change_state()
        value = self.prepare("concorde-spec-review", REVIEW, mode="describe-policy")
        self.assertEqual(("described", False), (value["state"], value["accepted"]))
        self.assertNotIn("descriptor", value)
        output = value["result"]["output"]["data"]
        self.assertEqual("described", output["outcome"])
        self.assertIn("service.transfer, scope.bank", output["answer"])
        self.assertEqual([], self.reports(self.change))
        self.assertEqual(
            [], list(Path(tempfile.gettempdir()).glob("concorde-native-*"))
        )
        self.assertEqual(before, self.change_state())

    @verifies("scenario.review.terminology-consistency")
    def test_the_spec_reviewer_compares_imported_terms_with_their_definitions(self):
        # Transfers imports the ledger's Account; the defining document is in its context.
        workflow = self.start_review("spec", REVIEW, root=self.primary)
        descriptor = workflow.slot_descriptor("review-0")
        sources = descriptor["snapshot"]["spec_resolution"]["sources"]
        self.assertIn(
            ("specs/ledger/module.md", "module.ledger"),
            [(source["path"], source["owner"]) for source in sources],
        )
        capsule = Path(descriptor["directory"]) / "context"
        self.assertTrue((capsule / "specs/ledger/module.md").is_file())
        # The comparison is a mandatory part of every Spec review.
        instructions = (
            capsule / ".pi/agents" / (descriptor["external"] + ".md")
        ).read_text()
        self.assertIn(
            "Terminology semantic consistency is a mandatory check", instructions
        )
        # A changed obligation is reported with both locations; coverage names the term.
        slot = workflow.slot("review-0")
        issue = self.report(
            slot,
            key="account-meaning",
            type="gap",
            subtype="spec-conflict",
            title="Account explained with another obligation",
            description="Transfers explains an Account as possibly several balances.",
            impact="Readers of Transfers misread the ledger promise.",
            basis="concept.ledger.account is exactly one stored balance.",
            owner_target_id="service.transfer",
            evidence=[
                {
                    "path": "specs/transfer/module.md",
                    "description": "The local explanation of Account",
                },
                {
                    "path": "specs/ledger/module.md",
                    "description": "The canonical definition of concept.ledger.account",
                },
            ],
        )
        result = self.review_result(
            workflow,
            "review-0",
            status="findings",
            issues=[
                {**issue, "severity": "advisory", "affected_task": "Explain Account"}
            ],
            representative_tasks=["Compare the imported term Account"],
        )
        workflow.child("review-0", result)
        for key in workflow.review_keys()[1:]:
            workflow.child(key, self.review_result(workflow, key))
        self.assertTrue(workflow.host_step("finalize")["accepted"])
        review = workflow.result()["output"]["data"]["reviews"][0]
        self.assertEqual(
            ["Compare the imported term Account"],
            review["data"]["representative_tasks"],
        )
        self.assertEqual(
            [issue["issue_id"]], [i["issue_id"] for i in review["data"]["issues"]]
        )

    @verifies("scenario.review.reviewer-failure")
    def test_a_failed_reviewer_makes_every_member_incomplete(self):
        self.own()
        self.edit_transfer_spec()
        for native_state in ("failed", "stopped"):
            with self.subTest(native_state=native_state):
                workflow = self.start_review("spec", self.task)
                self.assertEqual(["service.transfer", "scope.bank"], workflow.members())
                # The first reviewer completed; the second failed, so the workflow stopped.
                key = workflow.review_keys()[0]
                workflow.child(key, self.review_result(workflow, key))
                workflow.stop_native(native_state)
                with self.assertRaises(SpecError):
                    workflow.host_step("finalize")
                result = workflow.result()
                self.assertEqual(
                    ("failed", False), (result["state"], result["accepted"])
                )
                output = result["output"]["data"]
                self.assertEqual("failed", output["outcome"])
                self.assertEqual(
                    ["incomplete", "incomplete"],
                    [review["data"]["status"] for review in output["reviews"]],
                )
                records = recorded(self.change_state(), "reviews")
                self.assertEqual(
                    "incomplete", records["service.transfer"]["spec"]["status"]
                )
                with self.assertRaises(SpecError) as raised:
                    require_spec_review(self.invocation("concorde-plan"))
                self.assertEqual("review_required", raised.exception.code)

    def reviewed_scope(self):
        """A managed change whose Spec review scope holds Transfers and Banking."""
        self.own()
        self.edit_transfer_spec()

    @verifies("scenario.review.native-scope-rejected")
    def test_a_wrong_context_mode_or_receipt_is_not_accepted(self):
        self.reviewed_scope()
        foreign = {
            "issue_id": "I-" + "0" * 32,
            "report_id": "sha256:" + "e" * 64,
            "path": ".concorde/issues/I-" + "0" * 32 + ".md",
        }
        for case, wrong, code in (
            ("context", {"context_id": "sha256:" + "f" * 64}, "incompatible_handoff"),
            ("mode", {"review_mode": "code"}, "invalid_completion"),
            (
                "receipt",
                {
                    "status": "findings",
                    "issues": [
                        {**foreign, "severity": "blocking", "affected_task": "X"}
                    ],
                },
                "permission_denied",
            ),
        ):
            with self.subTest(case=case):
                workflow = self.start_review("spec", self.task)
                key = workflow.review_keys()[0]
                slot = workflow.slot(key)
                data = self.review_result(workflow, key, **wrong)
                value = self.action(slot, "submit", self.proposal(slot, data))
                self.assertEqual("rejected", value["state"])
                self.assertEqual([code], [e["code"] for e in value["result"]["errors"]])
                with self.assertRaises(SpecError):
                    workflow.host_step("finalize")
                self.assertNotIn("spec", self.recorded_reviews())
        self.assertEqual([], self.reports(self.change))

    @verifies("scenario.review.native-scope-rejected")
    def test_a_scope_without_complete_coverage_is_not_accepted(self):
        self.reviewed_scope()
        workflow = self.start_review("spec", self.task)
        key = workflow.review_keys()[0]
        workflow.child(key, self.review_result(workflow, key))
        with self.assertRaises(SpecError) as raised:
            workflow.host_step("finalize")
        self.assertTrue(
            {"invalid_completion", "stale_evidence"} & failure_codes(raised.exception)
        )
        self.assertNotIn("spec", self.recorded_reviews())
        self.assertEqual([], self.reports(self.change))

    @verifies("scenario.review.native-scope-rejected")
    def test_a_scope_whose_member_input_changed_is_stale(self):
        self.reviewed_scope()
        workflow = self.start_review("spec", self.task)
        for key in workflow.review_keys():
            workflow.child(key, self.review_result(workflow, key))
        self.edit_transfer_spec()
        with self.assertRaises(SpecError) as raised:
            workflow.host_step("finalize")
        self.assertIn("stale_context", failure_codes(raised.exception))
        workflow.stop_native("failed")
        result = workflow.result()
        self.assertEqual(("stale", False), (result["state"], result["accepted"]))
        self.assertNotIn("output", result)
        self.assertNotIn("spec", self.recorded_reviews())
        self.assertEqual([], self.reports(self.change))

    @verifies("scenario.review.explicit-review-fresh")
    def test_an_explicit_review_always_runs_fresh_reviewers(self):
        self.own()
        first, output = self.run_review("spec", self.task)
        [earlier] = output["artifacts"]
        second = self.start_review("spec", self.task)
        # Fresh reviewers for every member, not the recorded result.
        self.assertNotEqual(first.prepared["ticket"], second.prepared["ticket"])
        self.assertEqual(first.members(), second.members())
        for key in second.review_keys():
            second.child(key, self.review_result(second, key))
        self.assertTrue(second.host_step("finalize")["accepted"])
        [later] = second.result()["output"]["data"]["artifacts"]
        self.assertNotEqual(earlier["path"], later["path"])
        # The earlier report stays saved as history.
        self.assertTrue(run_path(self.change, earlier["path"]).is_file())
        self.assertEqual(
            later,
            recorded(self.change_state(), "reviews")["service.transfer"]["spec"][
                "artifact"
            ],
        )


if __name__ == "__main__":
    unittest.main()
