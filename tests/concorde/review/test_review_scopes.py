"""Review scopes of a managed change: code-free parents, components and every edited Module."""

import unittest

from concorde.harness.change_worktree import git_value
from concorde.harness.revisions import implementation_digest, target_revision
from concorde.harness.status_store import run_path
from concorde.planning.records import save_target_state
from concorde.planning.scope import component_intent
from concorde.review.review import scope_members, verify_required
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.planning.native_steps import NativeCandidate, task_item

BANK = {"target_id": "scope.bank", "task": "Coordinate transfers with the ledger"}
COMPONENT_TASKS = [
    task_item("transfer-rounding", "service.transfer", complete=True),
    task_item("ledger-lock", "module.ledger", complete=True),
]


class ComponentReviewTests(NativeCandidate, unittest.TestCase):
    def completed_components(self):
        """Banking binds no files; its change recorded completed work of two components."""
        self.own(BANK)
        self.accepted_plan(data=BANK)
        tasks = [dict(task, complete=False) for task in COMPONENT_TASKS]
        self.accepted_tasks(tasks, data=BANK)
        state = self.target("scope.bank")
        state["tasks"] = COMPONENT_TASKS
        repository = self.invocation("concorde-validate", BANK).repository
        state["component_revisions"] = {
            target_id: {
                "spec": target_revision(repository, repository.module(target_id)),
                "implementation": implementation_digest(
                    repository, repository.module(target_id)
                ),
            }
            for target_id in ("module.ledger", "service.transfer")
        }
        save_target_state(self.change, state)
        return self.target("scope.bank")

    def validate(self):
        return self.call_operation(
            self.change, "concorde-validate", {**BANK, "run_checks": False}
        )

    def assert_stale(self):
        with self.assertRaises(SpecError) as raised:
            verify_required(self.invocation("concorde-validate", BANK))
        self.assertEqual("review_required", raised.exception.code)
        result = self.validate()
        self.assertEqual(
            ["review_required"], [e["code"] for e in result["errors"]], result
        )

    def reviewed(self):
        before = self.completed_components()
        workflow, output = self.run_review("code", BANK)
        return before, workflow, output

    @verifies("scenario.review.explicit-components")
    def test_a_code_free_parent_is_reviewed_through_its_components(self):
        before, workflow, output = self.reviewed()
        # Each recorded component that binds files has its own reviewer and component task.
        self.assertEqual(["module.ledger", "service.transfer"], workflow.members())
        for key in workflow.review_keys():
            descriptor = workflow.slot_descriptor(key)
            target_id = descriptor["snapshot"]["target_id"]
            self.assertEqual(
                component_intent(
                    [t for t in COMPONENT_TASKS if t["target_id"] == target_id]
                ),
                descriptor["snapshot"]["task"],
            )
        # The parent aggregates only the components' typed results.
        self.assertEqual("completed", output["outcome"])
        self.assertEqual(
            ["module.ledger", "service.transfer"],
            sorted(review["data"]["target_id"] for review in output["reviews"]),
        )
        for artifact in output["artifacts"]:
            self.assertTrue(run_path(self.change, artifact["path"]).is_file())
        # The required code review is satisfied without a local review of the parent.
        verify_required(self.invocation("concorde-validate", BANK))
        # Review never marks implementation work complete.
        after = self.target("scope.bank")
        self.assertEqual(
            (before["tasks"], before["phase"], before["status"]),
            (after["tasks"], after["phase"], after["status"]),
        )
        self.assertNotEqual("ready", self.change_state()["status"])

    @verifies("scenario.review.explicit-components-stale")
    def test_a_changed_component_or_parent_makes_the_aggregate_stale(self):
        _, _, output = self.reviewed()
        verify_required(self.invocation("concorde-validate", BANK))
        report = run_path(self.change, output["artifacts"][0]["path"])
        for case, path, change in (
            ("component code", self.change / "app/ledger.py", b"# locked\n"),
            (
                "component Spec",
                self.change / "specs/transfer/module.md",
                b"\nTransfers lock the ledger.\n",
            ),
            ("component report", report, None),
            (
                "parent intent",
                self.change / "specs/bank/module.md",
                b"\nBanking coordinates locked transfers.\n",
            ),
        ):
            with self.subTest(case=case):
                original = path.read_bytes()
                path.write_bytes(
                    original.replace(b"no_findings", b"findings", 1)
                    if change is None
                    else original + change
                )
                try:
                    self.assert_stale()
                finally:
                    path.write_bytes(original)
                verify_required(self.invocation("concorde-validate", BANK))


class ChangeScopeReviewTests(NativeCandidate, unittest.TestCase):
    def members(self, mode):
        run = self.invocation(f"concorde-{mode}-review")
        return [member["target_id"] for member in scope_members(run, mode)[2]]

    @verifies("scenario.review.multi-module")
    def test_the_changes_own_reviews_cover_every_module_it_edits(self):
        self.own()
        # The candidate also edits the ledger's Spec and code.
        ledger = self.change / "specs/ledger/module.md"
        ledger.write_bytes(ledger.read_bytes() + b"\nReads lock the account.\n")
        code = self.change / "app/ledger.py"
        code.write_bytes(code.read_bytes() + b"# locked read\n")
        # The Host's worktree guidance edits AGENTS.md, which the Workspace Module binds.
        self.assertIn("AGENTS.md", git_value(self.change, "status", "--porcelain"))
        spec = self.members("spec")
        self.assertEqual("service.transfer", spec[0])
        # The edited Module and every Module the changed definitions concern.
        self.assertEqual({"service.transfer", "module.ledger", "scope.bank"}, set(spec))
        code_members = self.members("code")
        # Every Module binding a changed file; guidance and control records do not count.
        self.assertEqual(["service.transfer", "module.ledger"], code_members)
        self.assertNotIn("module.workspace", code_members)
        # A describe-policy preview lists the same code scope.
        preview = self.prepare("concorde-code-review", mode="describe-policy")
        self.assertIn(
            "service.transfer, module.ledger",
            preview["result"]["output"]["data"]["answer"],
        )


if __name__ == "__main__":
    unittest.main()
