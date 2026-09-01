import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


COMMANDS = REPOSITORY_ROOT / "presets/concorde/commands"
TEMPLATES = REPOSITORY_ROOT / "presets/concorde/templates"
WORKFLOW_CONTRACT = (
    REPOSITORY_ROOT
    / "specs/concorde/features/001-concorde-workflow/contracts/agent-commands.md"
)


class PlanDeliveryContractTests(unittest.TestCase):
    def command(self, name: str) -> str:
        return (COMMANDS / f"speckit.{name}.md").read_text(encoding="utf-8")

    def test_plan_separates_orientation_behavior_baseline_and_bounded_context(self):
        plan = self.command("plan")
        normalized = " ".join(plan.split())
        for invariant in (
            "workspace.feature_abstract",
            "orientation only",
            "workspace.feature_design",
            "workspace.feature_implementation",
            "no accepted baseline",
            "workspace.module_summary",
            "workspace.module_design",
            "parent_context.feature_abstract",
            "parent_context.feature_design",
            "parent_context.feature_implementation",
            "sibling design/implementation body",
            "cite",
        ):
            self.assertIn(invariant, normalized, invariant)

    def test_plan_stages_contract_proposals_and_forbids_durable_phase_writes(self):
        plan = self.command("plan")
        normalized = " ".join(plan.split())
        for invariant in (
            "ATTEMPT_DIR/contracts/",
            "proposed contract",
            "compatibility",
            "implementation task",
            "MUST NOT update",
            "feature-root contract",
        ):
            self.assertIn(invariant, normalized, invariant)
        self.assertNotIn("feature-root `/contracts/*`", plan)

    def test_tasks_require_traceable_complete_dependency_ordered_work(self):
        tasks = self.command("tasks")
        normalized = " ".join(tasks.split())
        for invariant in (
            "requirement ID or acceptance-outcome",
            "dependency graph",
            "architecture",
            "contract",
            "validation",
            "documentation",
            "evidence",
            "ATTEMPT_DIR/contracts/",
            "parent_context.feature_abstract",
            "sibling design/implementation body",
        ):
            self.assertIn(invariant, normalized, invariant)

    def test_issue_projection_preserves_identity_order_dependencies_and_scope(self):
        issues = self.command("taskstoissues")
        normalized = " ".join(issues.split())
        for invariant in (
            "Invocation authorization",
            "matching GitHub remote",
            "task-file order",
            "selected feature",
            "source task path",
            "story or phase",
            "scope",
            "prerequisite task IDs",
            "issue links",
            "open and closed",
            "MUST NOT modify",
            "task checkbox",
            "attempt/tasks.md remains authoritative",
        ):
            self.assertIn(invariant, normalized, invariant)

    def test_templates_preserve_temporal_contract_and_task_trace_models(self):
        plan_template = (TEMPLATES / "plan-template.md").read_text(encoding="utf-8")
        tasks_template = (TEMPLATES / "tasks-template.md").read_text(encoding="utf-8")
        self.assertIn("attempt/contracts/", plan_template)
        self.assertIn("proposed contract", plan_template)
        self.assertIn("requirement ID or acceptance-outcome", tasks_template)
        self.assertIn("attempt/contracts/", tasks_template)

    def test_workflow_contract_defines_the_plan_delivery_handoff(self):
        contract = WORKFLOW_CONTRACT.read_text(encoding="utf-8")
        normalized = " ".join(contract.split())
        for invariant in (
            "Plan Delivery Handoff",
            "Implementation plan",
            "Task list",
            "Issue projection",
            "task identity",
            "dependency",
            "separate invocation",
            "attempt/tasks.md",
        ):
            self.assertIn(invariant, normalized, invariant)


if __name__ == "__main__":
    unittest.main()
