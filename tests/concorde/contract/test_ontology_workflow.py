import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class OntologyWorkflowContractTests(unittest.TestCase):
    def test_profile_specs_templates_and_authoring_surfaces_share_the_contract(self):
        architecture = (REPOSITORY_ROOT / "specs/concorde/architecture.md").read_text(encoding="utf-8")
        self.assertIn("| Entity ID | Type | Definition | Locator |", architecture)
        self.assertIn("| Source | Predicate | Target | Description |", architecture)
        self.assertIn("| Interaction ID | Trigger | Steps | Result | Interfaces |", architecture)
        self.assertIn("module.concorde.skills", architecture)

        design = (REPOSITORY_ROOT / "specs/concorde/features/007-project-ontology.md").read_text(encoding="utf-8")
        for heading in ("Outcome and Scope", "Architecture Zoom", "Interfaces", "Requirements", "Edge Cases"):
            self.assertIn(f"## {heading}", design)
        for phrase in ("Module-centered specification profile", "Source code", "Delivery"):
            self.assertIn(phrase, design)

        sources = {
            "presets/concorde/templates/design-template.md": ("architecture zoom", "interfaces", "source code"),
            "presets/concorde/commands/speckit.specify.md": ("architecture.md", "feature_path", "interfaces"),
            "presets/concorde/commands/speckit.plan.md": ("module architecture", "feature file", "source code"),
            "presets/concorde/commands/speckit.implement.md": ("module architecture", "feature file", "source code"),
            "presets/concorde/commands/speckit.fast-loop.md": ("providing architecture", "selected feature file", "code/tests"),
            "extensions/concorde/commands/speckit.concorde.init.md": ("architecture.md", "typed entity vocabulary", "directed relationship vocabulary"),
            "extensions/concorde/commands/speckit.concorde.deliver.md": ("module architecture", "feature file", "code"),
        }
        for relative, required in sources.items():
            text = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8").lower()
            with self.subTest(source=relative):
                for phrase in required:
                    self.assertIn(phrase, text)

    def test_runtime_declares_profile6_entity_and_feature_diagnostics(self):
        entity_validator = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/validation/entities.py").read_text(encoding="utf-8")
        feature_validator = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/validation/features.py").read_text(encoding="utf-8")
        coordinator = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/validate.py").read_text(encoding="utf-8")

        for family in ("CONCORDE-ENTITY-", "CONCORDE-RELATIONSHIP-", "CONCORDE-INTERACTION-"):
            self.assertIn(family, entity_validator)
        for family in ("CONCORDE-FEATURE-", "CONCORDE-INTERFACE-", "CONCORDE-ZOOM-"):
            self.assertIn(family, feature_validator)
        self.assertIn("validate_entities", coordinator)
        self.assertIn("validate_features", coordinator)

    def test_self_hosted_profile_uses_direct_feature_files_and_is_contract_free(self):
        root = REPOSITORY_ROOT / "specs/concorde"
        self.assertEqual(len(list(root.rglob("architecture.md"))), 6)
        self.assertEqual(len(list(root.glob("features/*.md"))) + len(list((root / "modules").glob("*/features/*.md"))), 24)
        self.assertEqual([path for path in root.glob("**/features/*") if path.is_dir()], [])
        for obsolete in ("module.md", "abstract.md", "implementation.md", "contract.md"):
            self.assertEqual(list(root.rglob(obsolete)), [], obsolete)
        self.assertEqual([path for path in root.rglob("subfeatures") if path.is_dir()], [])
        self.assertEqual([path for path in root.rglob("contracts") if path.is_dir()], [])
        self.assertEqual([path for path in root.rglob("diagrams") if path.is_dir()], [])

    def test_project_ontology_defines_module_entities_interfaces_and_ua_boundary(self):
        ontology = (REPOSITORY_ROOT / "docs/ontology.md").read_text(encoding="utf-8")
        for phrase in ("## Module", "Architecture entity", "Entity relationship", "Feature interface", "Understand Anything"):
            self.assertIn(phrase, ontology)
        self.assertIn("adapts", ontology.lower())


if __name__ == "__main__":
    unittest.main()
