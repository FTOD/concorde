import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


SKILLS = REPOSITORY_ROOT / "skills"


class ExecuteReconcileContractTests(unittest.TestCase):
    def test_implementation_requires_persisted_passed_evidence_before_completion(self):
        source = (SKILLS / "concorde-implement/SKILL.md").read_text(encoding="utf-8")
        body = " ".join(source.split())
        for value in (
            "Before checking any task, append compact Attempt Evidence",
            "task ID and trace",
            "actual command/check",
            "`passed`/`failed`/truthful `skipped`",
            "evidence path, scope, and limitation",
            "Only a proportionate passed check permits `[X]`",
        ):
            self.assertIn(value, body, value)
        self.assertIn("- **T### · <trace>**", source)
        self.assertIn("- **Outcome**: passed", source)
        self.assertIn("top-level", body)

    def test_task_and_convergence_guidance_share_delivery_readable_evidence_grammar(self):
        for relative in (
            "skills/concorde-tasks/SKILL.md",
            "skills/concorde-converge/SKILL.md",
            "templates/tasks-template.md",
        ):
            with self.subTest(relative=relative):
                source = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("- **T### · <trace>**", source)
                self.assertIn("- **Outcome**: passed", source)

    def test_implementation_can_reconcile_only_task_owned_durable_sources(self):
        body = " ".join((SKILLS / "concorde-implement/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("every before/after change must match an executable task and its trace", body)
        self.assertIn("module `architecture.md` entity/type/locator", body)
        self.assertIn("related feature-file outcome, usage, embedded interface", body)
        self.assertIn("Do not make an unplanned durable edit", body)
        self.assertIn("An unexpected change stops completion marking", body)

    def test_setup_mutation_requires_task_bound_authority(self):
        body = " ".join((SKILLS / "concorde-implement/SKILL.md").read_text(encoding="utf-8").split())
        for value in (
            "setup/ignore files read-only",
            "dependency-ready task",
            "detected tool",
            "exact setup path",
            "authorized creation/edit",
        ):
            self.assertIn(value, body, value)

    def test_convergence_appends_only_unproven_remaining_work(self):
        body = " ".join((SKILLS / "concorde-converge/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("appends only genuinely remaining executable work", body)
        self.assertIn("Preserve every existing task ID, text, marker, phase, and evidence entry", body)
        self.assertIn("Do not mark tasks complete or reopen them", body)
        self.assertIn("append dependency-ordered tasks with new monotonically increasing ids", body.lower())
        self.assertIn("If no work remains, leave the task file byte-identical", body)

    def test_reflection_recording_is_problem_only_until_triage(self):
        implement = " ".join((SKILLS / "concorde-implement/SKILL.md").read_text(encoding="utf-8").split())
        plan = " ".join((SKILLS / "concorde-plan-author/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Planning and task generation are the normal reflection-recording points", implement)
        self.assertIn("Fill only Context, Expected, Observed, Impact, and Evidence", implement)
        self.assertIn("do not analyze root cause or propose a resolution", implement)
        self.assertIn("Describe only the problem", plan)
        self.assertIn("decide whether human intervention is needed", plan)
        self.assertIn("Continue with a bounded prototype", plan)


if __name__ == "__main__":
    unittest.main()
