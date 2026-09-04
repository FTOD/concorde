import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.repository import ProjectRepository  # noqa: E402


class OntologyWorkflowContractTests(unittest.TestCase):
    def test_profile_specs_templates_and_authoring_surfaces_share_the_contract(self):
        architecture = (REPOSITORY_ROOT / "specs/concorde/architecture.md").read_text(encoding="utf-8")
        self.assertIn("| Entity ID | Type | Definition | Locator |", architecture)
        self.assertIn("| Source | Predicate | Target | Description |", architecture)
        self.assertIn("| Interaction ID | Trigger | Steps | Result | Interfaces |", architecture)
        self.assertIn("module.concorde.understanding", architecture)
        self.assertIn("module.concorde.lifecycle", architecture)
        self.assertIn("module.concorde.capabilities", architecture)
        for retired in ("module.concorde.skills", "module.concorde.operations", "module.concorde.runtime", "module.concorde.workspace"):
            self.assertNotIn(retired, architecture)

        design = (REPOSITORY_ROOT / "specs/concorde/features/002-project-ontology.md").read_text(encoding="utf-8")
        for heading in ("Outcome and Scope", "Architecture Zoom", "Interfaces", "Requirements", "Edge Cases"):
            self.assertIn(f"## {heading}", design)
        for phrase in ("Module-centered specification profile", "Source code", "Delivery"):
            self.assertIn(phrase, design)

        sources = {
            "templates/feature-template.md": ("architecture zoom", "interfaces", "source code"),
            "skills/concorde-specify/SKILL.md": ("architecture.md", "feature_path", "interfaces"),
            "skills/concorde-plan-author/SKILL.md": ("module architecture", "feature file", "source code"),
            "skills/concorde-implement/SKILL.md": ("module architecture", "feature file", "source code"),
            "skills/concorde-fast-loop/SKILL.md": ("providing architecture", "selected feature file", "code/tests"),
            "skills/concorde-init/SKILL.md": ("architecture.md", "typed entity vocabulary", "directed relationship vocabulary"),
            "skills/concorde-deliver/SKILL.md": ("module architecture", "feature file", "code"),
        }
        for relative, required in sources.items():
            text = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8").lower()
            with self.subTest(source=relative):
                for phrase in required:
                    self.assertIn(phrase, text)

    def test_runtime_declares_profile7_entity_and_feature_diagnostics(self):
        entity_validator = (REPOSITORY_ROOT / "src/concorde/understanding/validation/entities.py").read_text(encoding="utf-8")
        feature_validator = (REPOSITORY_ROOT / "src/concorde/understanding/validation/features.py").read_text(encoding="utf-8")
        coordinator = (REPOSITORY_ROOT / "src/concorde/understanding/validate.py").read_text(encoding="utf-8")

        for family in ("CONCORDE-ENTITY-", "CONCORDE-RELATIONSHIP-", "CONCORDE-INTERACTION-"):
            self.assertIn(family, entity_validator)
        for family in ("CONCORDE-FEATURE-", "CONCORDE-INTERFACE-", "CONCORDE-ZOOM-"):
            self.assertIn(family, feature_validator)
        self.assertIn("validate_entities", coordinator)
        self.assertIn("validate_features", coordinator)
        self.assertIn("validate_capabilities", coordinator)

    def test_source_profile_uses_direct_feature_files_and_is_contract_free(self):
        root = REPOSITORY_ROOT / "specs/concorde"
        package = ProjectRepository(REPOSITORY_ROOT).load()
        self.assertEqual(package.profile_version, 7)
        self.assertEqual(package.specification_root, "specs/concorde")
        self.assertEqual(package.root_module_id, "module.concorde")

        root_module = package.modules[package.root_module_id]
        ontology = package.features["feature.concorde.define-project-ontology"]
        self.assertEqual(ontology.module, root_module.identifier)
        self.assertIn(ontology.identifier, root_module.features)
        self.assertEqual(
            set(root_module.features),
            {feature.identifier for feature in package.features.values() if feature.module == root_module.identifier},
        )
        self.assertEqual(ontology.provided_interfaces, ("contract.concorde.ontology",))
        self.assertEqual(ontology.required_interfaces, ("contract.understand-anything.knowledge-graph",))

        provided_interface = package.interfaces[ontology.provided_interfaces[0]]
        self.assertEqual(provided_interface.owner, ontology.identifier)
        for source, entity_ids in (
            ("architecture zoom", ontology.architecture_zoom),
            ("implementing entities", provided_interface.implementing_entities),
        ):
            self.assertTrue(entity_ids, source)
            for entity_id in entity_ids:
                with self.subTest(source=source, entity_id=entity_id):
                    self.assertIn(entity_id, package.entities)

        direct_features = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in root.rglob("features/*.md")
        }
        self.assertEqual(direct_features, {feature.path for feature in package.features.values()})
        self.assertEqual([path for path in root.glob("**/features/*") if path.is_dir()], [])
        for obsolete in ("module.md", "abstract.md", "implementation.md", "contract.md"):
            self.assertEqual(list(root.rglob(obsolete)), [], obsolete)
        self.assertEqual([path for path in root.rglob("subfeatures") if path.is_dir()], [])
        self.assertEqual([path for path in root.rglob("contracts") if path.is_dir()], [])

    def test_project_ontology_defines_module_entities_interfaces_and_ua_boundary(self):
        ontology = (REPOSITORY_ROOT / "specs/concorde/features/002-project-ontology.md").read_text(encoding="utf-8")
        for phrase in ("## Target Specification Model", "Architecture entity", "Entity relationship", "Feature interface", "Concorde Protocol", "Agent mutation worktree", "Protocol evolution", "Understand Anything"):
            self.assertIn(phrase, ontology)
        self.assertIn("adapts", ontology.lower())

    def test_concorde_protocol_evolution_is_one_root_attempt_free_feature(self):
        package = ProjectRepository(REPOSITORY_ROOT).load()
        root = package.modules[package.root_module_id]
        evolution = package.features["feature.concorde.evolve-protocol"]

        self.assertEqual(evolution.module, root.identifier)
        self.assertEqual(
            set(root.features),
            {
                "feature.concorde.workflow",
                "feature.concorde.define-project-ontology",
                "feature.concorde.evolve-protocol",
            },
        )
        self.assertEqual(evolution.provided_interfaces, ("interface.concorde.protocol-evolution",))
        self.assertEqual(evolution.required_interfaces, ("contract.concorde.ontology",))
        self.assertFalse(REPOSITORY_ROOT.joinpath(".concorde/attempts/feature.concorde.evolve-protocol").exists())

        architecture = (REPOSITORY_ROOT / "specs/concorde/architecture.md").read_text(encoding="utf-8")
        constitution = (REPOSITORY_ROOT / ".concorde/constitution.md").read_text(encoding="utf-8")
        design = (REPOSITORY_ROOT / evolution.path).read_text(encoding="utf-8")
        for entity in ("entity.concorde.protocol", "entity.concorde.protocol-cutover", "entity.concorde.git"):
            self.assertIn(entity, architecture)
        self.assertIn("**Version**: 8.3.0", constitution)
        self.assertIn("no attempt or checklist", constitution)
        self.assertIn("Agent Mutations Start in Isolated Worktrees", constitution)
        self.assertIn("committed `HEAD`", constitution)
        self.assertIn("one reviewable cutover commit", design)

        capabilities = (
            REPOSITORY_ROOT / "specs/concorde/modules/capabilities/architecture.md"
        ).read_text(encoding="utf-8")
        self.assertIn("entity.capabilities.worktree-gate", capabilities)


if __name__ == "__main__":
    unittest.main()
