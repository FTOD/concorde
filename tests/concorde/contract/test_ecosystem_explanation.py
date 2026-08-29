import json
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


FEATURE_ROOT = REPOSITORY_ROOT / "specs/concorde/features/003-install-concorde-speckit"


class EcosystemExplanationContractTests(unittest.TestCase):
    def test_textual_explanations_name_every_ecosystem_role(self):
        sources = [
            FEATURE_ROOT / "design.md",
            FEATURE_ROOT / "design.md",
            FEATURE_ROOT / "contracts/ecosystem-explanation.md",
            REPOSITORY_ROOT / "specs/concorde/module.md",
            REPOSITORY_ROOT / "specs/concorde/architecture/contracts/spec-kit-installation/contract.md",
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
        self.assertIn("non-executable recipe", specification)
        self.assertIn("it does not register commands", specification)
        self.assertIn("spec kit is the host platform", specification)

        current_sources = [source for source in sources if source.name != "design.md"]
        for source in current_sources:
            text = source.read_text(encoding="utf-8").lower()
            with self.subTest(question_surface=source.relative_to(REPOSITORY_ROOT)):
                self.assertIn("five", text)
                self.assertIn("ask", text)
                self.assertIn("four", text)
                self.assertIn("read-only", text)

    def test_component_view_separates_package_and_runtime_ownership(self):
        source = FEATURE_ROOT / "diagrams" / "spec-kit-component-model.json"
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
                "selfHosting",
            }.issubset(component_ids)
        )
        edges = {(edge["from"], edge["to"], edge.get("label")) for edge in diagram["connections"]}
        self.assertIn(("bundle", "preset", "pins preset@0.1.0"), edges)
        self.assertIn(("bundle", "extension", "pins extension@0.1.0"), edges)
        self.assertIn(("preset", "featureLifecycle", "4 templates + 9 overrides"), edges)
        self.assertIn(("extension", "agentHost", "7 surfaces · 6 runtime-backed"), edges)
        self.assertIn(("selfHosting", "bundle", "excluded from release"), edges)
        self.assertIn(("featureLifecycle", "agentHost", "materialize winning layer"), edges)
        self.assertIn(("agentHost", "architectureCore", "invoke services"), edges)

    def test_workflow_view_has_install_time_and_two_use_time_paths(self):
        source = FEATURE_ROOT / "diagrams" / "bundle-installation-flow.json"
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
        labels = {edge.get("label") for edge in diagram["edges"]}
        self.assertIn("9 winning surfaces", labels)
        self.assertIn("7 surfaces · 6 runtime-backed", labels)

    def test_supplemental_views_are_delivered_but_not_root_module_participants(self):
        root_view = json.loads(
            (REPOSITORY_ROOT / "specs/concorde/architecture/diagrams/level-view.json").read_text(encoding="utf-8")
        )
        root_ids = {component["id"] for component in root_view["components"]}
        self.assertTrue({"distribution", "integration", "architectureCore"}.issubset(root_ids))
        self.assertTrue({"bundle", "preset", "extension", "catalogs"}.isdisjoint(root_ids))

        outputs = {
            "concorde-spec-kit-component-model.html": "How Concorde Commands Reach a Clean Project",
            "concorde-bundle-installation-flow.html": "Install, Materialize, and Prove Concorde",
        }
        for filename, title in outputs.items():
            artifact = REPOSITORY_ROOT / "generated/architecture" / filename
            with self.subTest(artifact=filename):
                self.assertTrue(artifact.is_file())
                self.assertIn(title, artifact.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
