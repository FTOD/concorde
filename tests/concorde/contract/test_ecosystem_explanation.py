import json
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


FEATURE_ROOT = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow"


class EcosystemExplanationContractTests(unittest.TestCase):
    def test_textual_explanations_name_every_ecosystem_role(self):
        sources = [
            FEATURE_ROOT / "spec.md",
            FEATURE_ROOT / "plan.md",
            FEATURE_ROOT / "quickstart.md",
            FEATURE_ROOT / "contracts/ecosystem-explanation.md",
            REPOSITORY_ROOT / "specs/concorde/module.md",
        ]
        required_terms = (
            "spec kit",
            "bundle",
            "preset",
            "extension",
            "catalog",
            "coding-agent integration",
            "architecture core",
        )
        for source in sources:
            text = source.read_text(encoding="utf-8").lower()
            with self.subTest(source=source.relative_to(REPOSITORY_ROOT)):
                for term in required_terms:
                    self.assertIn(term, text)

        specification = sources[0].read_text(encoding="utf-8").lower()
        self.assertIn("it is not executable behavior", specification)
        self.assertIn("it does not register commands", specification)
        self.assertIn("spec kit remains the host platform", specification)

    def test_component_view_separates_package_and_runtime_ownership(self):
        source = FEATURE_ROOT / "spec-kit-component-model.json"
        diagram = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(diagram["diagram_type"], "architecture")
        self.assertEqual(diagram["meta"]["quality_profile"], "showcase")
        component_ids = {component["id"] for component in diagram["components"]}
        self.assertTrue(
            {
                "catalogs",
                "specKit",
                "bundle",
                "preset",
                "extension",
                "featureLifecycle",
                "agentHost",
                "architectureCore",
                "specTree",
            }.issubset(component_ids)
        )
        edges = {(edge["from"], edge["to"], edge.get("label")) for edge in diagram["connections"]}
        self.assertIn(("bundle", "preset", "pins preset@0.1.0"), edges)
        self.assertIn(("bundle", "extension", "pins extension@0.1.0"), edges)
        self.assertIn(("preset", "featureLifecycle", "append guidance"), edges)
        self.assertIn(("extension", "agentHost", "register commands"), edges)
        self.assertIn(("agentHost", "architectureCore", "invoke services"), edges)

    def test_workflow_view_has_install_time_and_two_use_time_paths(self):
        source = FEATURE_ROOT / "starter-installation-flow.json"
        diagram = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(diagram["diagram_type"], "workflow")
        self.assertEqual(diagram["meta"]["quality_profile"], "showcase")
        node_ids = {node["id"] for node in diagram["nodes"]}
        self.assertTrue(
            {
                "componentSources",
                "releaseArtifacts",
                "catalogs",
                "inspectPlan",
                "installBundle",
                "componentsActive",
                "normalLifecycle",
                "concordeCommands",
            }.issubset(node_ids)
        )
        edges = {(edge["from"], edge["to"]) for edge in diagram["edges"]}
        self.assertIn(("componentsActive", "normalLifecycle"), edges)
        self.assertIn(("componentsActive", "concordeCommands"), edges)

    def test_supplemental_views_are_delivered_but_not_root_module_participants(self):
        root_view = json.loads(
            (REPOSITORY_ROOT / "specs/concorde/architecture.json").read_text(encoding="utf-8")
        )
        root_ids = {component["id"] for component in root_view["components"]}
        self.assertTrue({"distribution", "integration", "architectureCore"}.issubset(root_ids))
        self.assertTrue({"bundle", "preset", "extension", "catalogs"}.isdisjoint(root_ids))

        outputs = {
            "concorde-spec-kit-component-model.html": "How Concorde Fits into Spec Kit",
            "concorde-starter-installation-flow.html": "Concorde: Install and Use",
        }
        for filename, title in outputs.items():
            artifact = REPOSITORY_ROOT / "generated/architecture" / filename
            with self.subTest(artifact=filename):
                self.assertTrue(artifact.is_file())
                self.assertIn(title, artifact.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
