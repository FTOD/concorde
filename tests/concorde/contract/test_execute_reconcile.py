import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


COMMANDS = REPOSITORY_ROOT / "commands"


class ExecuteReconcileContractTests(unittest.TestCase):
    def test_implementation_requires_persisted_passed_evidence_before_completion(self):
        body = " ".join((COMMANDS / "concorde.implement.md").read_text(encoding="utf-8").split())
        for value in (
            "Before checking any task, append compact Attempt Evidence",
            "task ID and trace",
            "actual command/check",
            "`passed`/`failed`/truthful `skipped`",
            "evidence path, scope, and limitation",
            "Only a proportionate passed check permits `[X]`",
        ):
            self.assertIn(value, body, value)

    def test_implementation_can_reconcile_only_task_owned_durable_sources(self):
        body = " ".join((COMMANDS / "concorde.implement.md").read_text(encoding="utf-8").split())
        self.assertIn("every before/after change must match an executable task and its trace", body)
        self.assertIn("module `architecture.md` entity/type/locator", body)
        self.assertIn("related feature-file outcome, usage, embedded interface", body)
        self.assertIn("Do not make an unplanned durable edit", body)
        self.assertIn("An unexpected change stops completion marking", body)

    def test_setup_mutation_requires_task_bound_authority(self):
        body = " ".join((COMMANDS / "concorde.implement.md").read_text(encoding="utf-8").split())
        for value in (
            "setup/ignore files read-only",
            "dependency-ready task",
            "detected tool",
            "exact setup path",
            "authorized creation/edit",
        ):
            self.assertIn(value, body, value)

    def test_convergence_appends_only_unproven_remaining_work(self):
        body = " ".join((COMMANDS / "concorde.converge.md").read_text(encoding="utf-8").split())
        self.assertIn("appends only genuinely remaining executable work", body)
        self.assertIn("Preserve every existing task ID, text, marker, phase, and evidence entry", body)
        self.assertIn("Do not mark tasks complete or reopen them", body)
        self.assertIn("append dependency-ordered tasks with new monotonically increasing ids", body.lower())
        self.assertIn("If no work remains, leave the task file byte-identical", body)

    def test_reflections_capture_workarounds_and_provisional_prototype_choices(self):
        implement = " ".join((COMMANDS / "concorde.implement.md").read_text(encoding="utf-8").split())
        plan = " ".join((COMMANDS / "concorde.plan.md").read_text(encoding="utf-8").split())
        self.assertIn("every provisional prototype design choice", implement)
        self.assertIn("workaround", implement)
        self.assertIn("provisional or imperfect prototype choices", plan)
        self.assertIn("Continue with a bounded prototype", plan)


if __name__ == "__main__":
    unittest.main()
