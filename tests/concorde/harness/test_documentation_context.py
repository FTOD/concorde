"""Declared reference documentation is capability context: granted to the phases that need it."""
import unittest

from concorde.harness.context import resolve_context, recheck_context
from concorde.spec.repository import SpecError, digest
from concorde.spec.verification import verifies
from tests.concorde.spec.test_module_model import ModuleImplementationTests, PACKAGE


class DocumentationContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ModuleImplementationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    @verifies("scenario.harness.documentation-context")
    def test_documentation_contents_reach_only_the_phases_that_plan_task_write_or_review(self):
        from concorde.harness.agent_model import agent_definition, mode_definition
        self.fixture.write("docs/vendor/lib/api.md", "## connect(url)\n")
        self.fixture.declare_documentation()
        repository = self.fixture.repository()
        spec_engineer = agent_definition("spec_engineer")
        programmer = agent_definition("programmer")
        expected_entries = [{"path": "docs/vendor/lib/", "entity_id": "entity.a.lib", "directory": True}]
        artifact = {"id": "docs/vendor/lib/api.md", "path": "docs/vendor/lib/api.md",
                    "digest": digest((self.fixture.root / "docs/vendor/lib/api.md").read_bytes())}
        for phase, mode, contents in (("specify", mode_definition(spec_engineer, "specify"), False),
                                      ("context-solve", mode_definition(spec_engineer, "context-solve"), False),
                                      ("plan", mode_definition(spec_engineer, "plan"), True),
                                      ("tasks", mode_definition(spec_engineer, "tasks"), True),
                                      ("implementation", mode_definition(programmer, "implementation"), True),
                                      ("code-review", mode_definition(programmer, "code-review"), True),
                                      ("spec-review", mode_definition(spec_engineer, "spec-review"), False)):
            with self.subTest(phase=phase):
                inputs = ()
                if phase == "tasks":
                    inputs = ({"type_id": "concorde-plan-artifact", "schema_version": 1, "data": {"plan": "Plan"}},
                              {"type_id": "concorde-task-identity-constraints", "schema_version": 1,
                               "data": {"reserved_task_ids": []}})
                elif phase == "implementation":
                    inputs = ({"type_id": "concorde-implementation-task", "schema_version": 1,
                               "data": {"plan": "Plan", "tasks": []}},)
                snapshot = resolve_context(repository, "module.a", phase=phase, task="Adapt", mode=mode,
                                           stage_inputs=inputs).value
                self.assertEqual(3, snapshot["schema_version"])
                self.assertEqual(expected_entries, snapshot["documentation_entries"])
                self.assertEqual([artifact] if contents else [], snapshot["documentation_artifacts"])
        # A phase without a mode still receives contents only where the phase admits them.
        self.assertEqual([artifact], resolve_context(repository, "module.a", phase="plan", task="Adapt")
                         .value["documentation_artifacts"])
        self.assertEqual([], resolve_context(repository, "module.a", phase="ask", task="Adapt")
                         .value["documentation_artifacts"])
        # Changed documentation bytes stale a snapshot that received contents, not one that did not.
        plan = resolve_context(repository, "module.a", phase="plan", task="Adapt")
        ask = resolve_context(repository, "module.a", phase="ask", task="Adapt")
        self.fixture.write("docs/vendor/lib/api.md", "## connect(url, timeout)\n")
        recheck_context(self.fixture.repository(), ask)
        with self.assertRaises(SpecError) as raised:
            recheck_context(self.fixture.repository(), plan)
        self.assertEqual("stale_context", raised.exception.code)
        # A changed declaration stales every phase.
        entities, save = self.fixture.entity_block("specs/a/module.md")
        entities[-1]["documentation"] = ["docs/vendor/lib/api.md"]
        save(entities)
        with self.assertRaises(SpecError):
            recheck_context(self.fixture.repository(), ask)

    @verifies("scenario.harness.documentation-context")
    def test_planner_and_programmer_are_granted_the_declared_documentation_only(self):
        from concorde.development.capability_host import CapabilityHost, run_capability
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import ModelProcessDouble
        self.fixture.write("docs/vendor/lib/api.md", "## connect(url)\n")
        self.fixture.write("docs/vendor/other/api.md", "undeclared\n")
        self.fixture.declare_documentation()
        seen = {}
        def inspect(stage, snapshot, result, cwd):
            granted = (cwd / "docs/vendor/lib/api.md")
            seen[stage] = {"copy": granted.read_text() if granted.exists() else None,
                           "undeclared": (cwd / "docs/vendor/other/api.md").exists(),
                           "artifacts": [item["path"] for item in snapshot["documentation_artifacts"]],
                           "cwd_is_project": cwd == self.fixture.root}
            if stage == "plan":
                result["plan"] = "Use connect(url) as documented."
        double = ModelProcessDouble(inspect)
        self.addCleanup(double.runtime_directory.cleanup)
        host = CapabilityHost(self.fixture.root, PACKAGE, executor=double.executor, allow_primary_worktree=True)
        result = run_capability("concorde-plan", self.fixture.configuration,
                                typed("concorde-plan-request", {"target_id": "module.a", "task": "Adapt the value"}),
                                host_context=host)
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual({"copy": None, "undeclared": False, "artifacts": [], "cwd_is_project": False},
                         seen["context-solve"])
        self.assertEqual({"copy": "## connect(url)\n", "undeclared": False, "artifacts": ["docs/vendor/lib/api.md"],
                          "cwd_is_project": False}, seen["plan"])
        policies = {item["phase"]: item for item in host.descriptions}
        self.assertIn("docs/vendor/lib/api.md", policies["plan"]["read_paths"])
        self.assertNotIn("docs/vendor/lib/api.md", policies["context-solve"]["read_paths"])
        self.assertTrue(all("docs/vendor/other" not in path for path in policies["plan"]["read_paths"]))


if __name__ == "__main__":
    unittest.main()
