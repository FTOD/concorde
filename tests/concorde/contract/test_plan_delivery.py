import json
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


PACKAGE = REPOSITORY_ROOT
WORKSPACE_FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace"


class PlanDeliveryContractTests(unittest.TestCase):
    def test_plan_uses_feature_architecture_code_and_tests_as_inputs(self):
        body = (PACKAGE / "skills/concorde-plan/SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        for value in (
            "complete selected feature file",
            "providing module architecture",
            "current source code and executable tests",
            "executable_context",
            "compare desired behavior directly with code/tests",
            "Planning must leave durable sources byte-identical",
        ):
            self.assertIn(value, normalized, value)
        self.assertNotIn("attempt/contracts/", body)

    def test_plan_template_requires_explicit_durable_reconciliation_tasks(self):
        body = " ".join((PACKAGE / "templates/plan-template.md").read_text(encoding="utf-8").split())
        self.assertIn("selected direct feature file", body)
        self.assertIn("providing module's `architecture.md`", body)
        self.assertIn("current source code", body)
        self.assertIn("explicit task to reconcile", body)
        self.assertIn("Planning itself writes only under the returned `attempt_dir`", body)
        self.assertIn("cleanup-only delivery", body)

    def test_task_template_traces_architecture_feature_code_tests_and_delivery(self):
        body = " ".join((PACKAGE / "templates/tasks-template.md").read_text(encoding="utf-8").split())
        for value in (
            "module `architecture.md`",
            "direct feature file",
            "source code and executable tests/checks",
            "requirement ID or acceptance-outcome trace",
            "returned `validation` file",
            "cleanup-only delivery readiness",
        ):
            self.assertIn(value, body, value)

    def test_delivery_proposal9_is_cleanup_only_and_exactly_one_attempt(self):
        proposal = json.loads((WORKSPACE_FIXTURES / "deliver-proposal.json").read_text(encoding="utf-8"))
        self.assertEqual(proposal["proposal_version"], 9)
        self.assertEqual(set(proposal), {"proposal_version", "tool", "target", "source_digest", "remove"})
        self.assertEqual(len(proposal["remove"]), 1)
        self.assertTrue(proposal["remove"][0].startswith(".concorde/attempts/feature."))

    def test_delivery_guidance_never_authors_content(self):
        body = (REPOSITORY_ROOT / "skills/concorde-deliver/SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(body.split())
        self.assertIn("Delivery is cleanup-only", normalized)
        self.assertIn("writes no durable specification or implementation narrative", normalized)
        self.assertIn("`remove` must contain exactly", normalized)
        self.assertIn("do not draft content", normalized.lower())
        self.assertIn("never changes module architecture, the direct feature file, code, tests", normalized.lower())


if __name__ == "__main__":
    unittest.main()
