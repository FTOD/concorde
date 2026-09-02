import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


LIFECYCLE_COMMANDS = REPOSITORY_ROOT / "commands"
FRAMEWORK_COMMANDS = REPOSITORY_ROOT / "commands"
WORKSPACE_COMMANDS = (
    "concorde.analyze.md",
    "concorde.checklist.md",
    "concorde.clarify.md",
    "concorde.converge.md",
    "concorde.fast-loop.md",
    "concorde.implement.md",
    "concorde.plan.md",
    "concorde.specify.md",
    "concorde.tasks.md",
    "concorde.taskstoissues.md",
)


def read(directory: Path, name: str) -> str:
    return (directory / name).read_text(encoding="utf-8")


class AgentCommandContractTests(unittest.TestCase):
    def test_every_phase_resolves_protocol12_before_path_sensitive_work(self):
        for name in WORKSPACE_COMMANDS:
            path = LIFECYCLE_COMMANDS / name
            with self.subTest(path=path.name):
                body = path.read_text(encoding="utf-8")
                self.assertIn("Protocol 12", body)
                self.assertIn("workspace.py --phase", body)

    def test_phase_guidance_uses_feature_path_architecture_attempt_and_executable_context(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in LIFECYCLE_COMMANDS.glob("*.md"))
        for value in (
            "feature_path",
            "module_architecture",
            "module_ancestry",
            "related_features",
            "executable_context",
            "attempt_dir",
            "attempt_state",
            "checklists_dir",
            "reflections",
        ):
            self.assertIn(value, combined, value)
        for removed in (
            "feature_" + "directory",
            "feature_" + "design",
            "feature_" + "abstract",
            "feature_" + "implementation",
            "module_" + "summary",
            "module_" + "design",
            "contracts_" + "dir",
            "parent_" + "context",
            "workspace_" + "kind",
        ):
            self.assertNotIn(removed, combined, removed)

    def test_specify_authors_one_direct_feature_file_with_embedded_interfaces(self):
        body = read(LIFECYCLE_COMMANDS, "concorde.specify.md")
        normalized = " ".join(body.split())
        for value in (
            "complete durable feature file",
            "never a hierarchy container",
            "direct `features/<NNN-name>.md` file",
            "one `## Interfaces` section",
            "one `## Architecture Zoom`",
            "Existing `contract.*` identifiers may remain as interface identities",
            "Do not create a separate interface document or directory",
            "reconcile only the providing architecture's immediate feature inventory",
            "attempt_state: unresolved",
            "run `{SCRIPT}` again",
            ".concorde/attempts/<stable-feature-id>/",
        ):
            self.assertIn(value, normalized, value)

    def test_source_only_diagram_checks_survive_as_module_architecture_checks(self):
        specify = " ".join(read(LIFECYCLE_COMMANDS, "concorde.specify.md").split())
        plan = " ".join(read(LIFECYCLE_COMMANDS, "concorde.plan.md").split())
        for body in (specify, plan):
            self.assertIn("normalized project-relative `.html`", body)
            self.assertIn("`meta.output`", body)
            self.assertIn("same unique target", body)
            self.assertIn("`meta.legend.mode`", body)
        self.assertIn("Route an invalid module declaration to architecture work", specify)
        self.assertIn("Invalid declarations must return to architecture authority", plan)

    def test_plan_and_tasks_cover_complete_authority_delta_without_durable_planning_writes(self):
        plan = " ".join(read(LIFECYCLE_COMMANDS, "concorde.plan.md").split())
        tasks = " ".join(read(LIFECYCLE_COMMANDS, "concorde.tasks.md").split())
        self.assertIn("current source code and executable tests", plan)
        self.assertIn("must leave durable sources byte-identical", plan)
        self.assertIn("There is no prose implementation baseline", plan)
        self.assertIn("writes only temporal", plan)
        self.assertIn("module architecture, feature file/interfaces, code, tests, and projections", tasks)
        self.assertIn("Tests precede their implementation work", tasks)
        self.assertIn("stable task ID", tasks)
        self.assertIn("requirement or acceptance-outcome trace", tasks)
        self.assertIn("Architecture/feature-file edits are valid implementation tasks", tasks)

    def test_implementation_requires_task_authority_and_passed_attempt_evidence(self):
        body = " ".join(read(LIFECYCLE_COMMANDS, "concorde.implement.md").split())
        for value in (
            "Code is implementation authority",
            "tests and deterministic checks are evidence",
            "every before/after change must match an executable task and its trace",
            "Do not make an unplanned durable edit",
            "Before checking any task, append compact Attempt Evidence",
            "Only a proportionate passed check permits `[X]`",
            "unexpected change stops completion marking",
            "confirm the selected attempt still exists for explicit delivery",
        ):
            self.assertIn(value, body, value)

    def test_analysis_convergence_and_reflections_preserve_boundaries(self):
        analyze = " ".join(read(LIFECYCLE_COMMANDS, "concorde.analyze.md").split())
        converge = " ".join(read(LIFECYCLE_COMMANDS, "concorde.converge.md").split())
        implement = " ".join(read(LIFECYCLE_COMMANDS, "concorde.implement.md").split())
        self.assertIn("read-only semantic audit", analyze.lower())
        self.assertIn("only permitted write is a centralized reflection entry", analyze)
        self.assertIn("appends only genuinely remaining executable work", converge)
        self.assertIn("Preserve every existing task ID, text, marker, phase, and evidence entry", converge)
        for body in (implement, converge):
            self.assertIn("provisional", body)
            self.assertIn("reflection", body)

    def test_every_entry_writing_phase_allocates_ids_atomically(self):
        for name in (
            "concorde.plan.md", "concorde.tasks.md", "concorde.implement.md",
            "concorde.analyze.md", "concorde.converge.md", "concorde.fast-loop.md",
        ):
            with self.subTest(name=name):
                body = read(LIFECYCLE_COMMANDS, name)
                self.assertIn("--allocate-id", body)
                self.assertIn("allocated_id", body)
                self.assertIn("never derive", body)

    def test_fast_loop_is_direct_bounded_and_never_creates_attempt_memory(self):
        body = " ".join(read(LIFECYCLE_COMMANDS, "concorde.fast-loop.md").split())
        self.assertIn("direct, no-attempt path", body)
        self.assertIn("Reject fast-loop when an attempt already exists", body)
        self.assertIn("Never create `.concorde/attempts/<stable-feature-id>/` artifacts", body)
        self.assertIn("one selected feature and one providing module", body)
        self.assertIn("no new module, feature, entity type, cross-module relationship", body)
        self.assertIn("recommend specification/clarification followed by plan, tasks, implementation, and delivery", body)

    def test_framework_commands_expose_profile7_context_validation_and_cleanup_delivery(self):
        init = " ".join(read(FRAMEWORK_COMMANDS, "concorde.init.md").split())
        context = " ".join(read(FRAMEWORK_COMMANDS, "concorde.context.md").split())
        validate = " ".join(read(FRAMEWORK_COMMANDS, "concorde.validate.md").split())
        deliver = " ".join(read(FRAMEWORK_COMMANDS, "concorde.deliver.md").split())
        ask = " ".join(read(FRAMEWORK_COMMANDS, "concorde.ask.md").split())
        self.assertIn("Architecture Source Profile 7", init)
        self.assertIn("Initialization Proposal 3", init)
        self.assertIn("diagrams/system-overview.json", init)
        self.assertIn("Archify showcase", init)
        self.assertIn(".concorde/reflections/log.md", init)
        self.assertIn("Do not invent product modules", init)
        self.assertIn("typed current-level entities", context)
        self.assertIn("Never expand a child module's internal inventory", context)
        self.assertIn("recursive acyclic module tree", validate)
        self.assertIn("complete embedded interface semantics", validate)
        self.assertIn("one Archify `architecture` system overview per module", validate)
        self.assertIn("nine artifact checks", validate)
        self.assertIn("Delivery Proposal 8", deliver)
        self.assertIn("Delivery is cleanup-only", deliver)
        self.assertIn("removes only the selected attempt", deliver)
        self.assertIn("Protocol 12", deliver)
        self.assertIn("writes no durable specification or implementation narrative", deliver)
        self.assertIn("strictly read-only", ask)
        self.assertIn("Basis", ask)
        self.assertIn("Sources", ask)


if __name__ == "__main__":
    unittest.main()
