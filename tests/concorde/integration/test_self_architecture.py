import json
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class SelfArchitectureTests(unittest.TestCase):
    def test_concorde_hierarchy_validates_and_projects_one_level(self):
        validation = validate_project(REPOSITORY_ROOT)
        self.assertEqual(validation.status, "success", validation.findings)
        context = bounded_context(REPOSITORY_ROOT, "module.concorde")
        self.assertEqual(context.status, "success", context.findings)
        projection = context.result["context"]
        self.assertEqual(len(projection["children"]), 5)
        self.assertTrue(all("contracts" in child for child in projection["children"]))
        participants = {
            participant
            for scenario in projection["scenarios"]
            for participant in scenario["participants"]
        }
        self.assertTrue(
            {
                "module.concorde.skills",
                "module.concorde.scripts",
                "module.concorde.workspace-files",
                "module.concorde.distribution",
                "module.concorde.auto-docs",
            }.issubset(participants)
        )
        self.assertFalse(any(participant.startswith("feature.") for participant in participants))
        self.assertNotIn("feature.auto-docs.publish-project-docsite", repr(projection["children"]))
        refinements = {(item["from"], item["to"]) for item in projection["refinement_links"]}
        self.assertIn(("feature.distribution.package-concorde-bundle", "feature.concorde.install-with-spec-kit"), refinements)
        self.assertIn(("feature.scripts.run-workflow-operations", "feature.concorde.workflow"), refinements)
        self.assertIn(("feature.workspace-files.manage-feature-workspace", "feature.concorde.workflow"), refinements)

    def test_question_surface_is_visible_but_not_a_runtime_operation(self):
        manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(encoding="utf-8")
        command_names = [
            line.split('"', 2)[1]
            for line in manifest.splitlines()
            if line.strip().startswith('- name: "speckit.concorde.')
        ]
        self.assertEqual(len(command_names), 5)
        self.assertIn("speckit.concorde.ask", command_names)

        diagram = json.loads((
            REPOSITORY_ROOT
            / "specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json"
        ).read_text(encoding="utf-8"))
        command_component = next(item for item in diagram["components"] if item["id"] == "concordeCommands")
        self.assertIn("5 Concorde Surfaces", command_component["label"])
        self.assertIn("4 operations", command_component["sublabel"])

        cli_source = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/cli.py").read_text(encoding="utf-8")
        self.assertNotIn('add_parser("ask")', cli_source)


if __name__ == "__main__":
    unittest.main()
