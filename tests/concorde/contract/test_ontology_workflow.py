import json
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class OntologyWorkflowContractTests(unittest.TestCase):
    def test_profile_templates_and_authoring_surfaces_share_the_contract(self):
        profile = (REPOSITORY_ROOT / "specs/concorde/features/007-project-ontology/contracts/terminology-table.md").read_text(encoding="utf-8")
        self.assertIn("| Term | Meaning | Relationships |", profile)
        self.assertIn("`predicate` → `Target term`", profile)
        self.assertIn("No local terminology. This level uses inherited terminology unchanged.", profile)
        self.assertIn("<defining-level-id>#<normalized-preferred-term>", profile)
        self.assertIn("Modules inherit parent-module terminology", profile)
        self.assertIn("Sub-features inherit", profile)
        self.assertIn("## Compatibility", profile)

        sources = (
            "presets/concorde/templates/design-template.md",
            "presets/concorde/commands/speckit.specify.md",
            "presets/concorde/commands/speckit.clarify.md",
            "presets/concorde/commands/speckit.fast-loop.md",
            "extensions/concorde/commands/speckit.concorde.init.md",
            "extensions/concorde/commands/speckit.concorde.deliver.md",
        )
        for relative in sources:
            text = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(source=relative):
                self.assertIn("Terminology", text)
                self.assertIn("inherited", text.lower())

    def test_runtime_diagnostics_and_contract_are_declared(self):
        validator = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/validation/terminology.py").read_text(encoding="utf-8")
        for number in range(1, 7):
            self.assertIn(f"CONCORDE-ONTOLOGY-{number:03d}", validator)
        coordinator = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/validate.py").read_text(encoding="utf-8")
        self.assertIn("validate_terminology", coordinator)

        contract = (REPOSITORY_ROOT / "specs/concorde/architecture/contracts/ontology/contract.md").read_text(encoding="utf-8")
        for heading in ("Purpose", "Information", "Obligations", "Failure Semantics", "Compatibility", "Evidence"):
            self.assertIn(f"## {heading}", contract)
        self.assertIn("contract.concorde.ontology", contract)

    def test_core_diagram_is_architecture_hidden_legend_and_text_backed(self):
        source = REPOSITORY_ROOT / "specs/concorde/features/007-project-ontology/diagrams/concorde-ontology-model.json"
        diagram = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(diagram["diagram_type"], "architecture")
        self.assertEqual(diagram["meta"]["legend"], {"mode": "hidden"})
        self.assertEqual(diagram["meta"]["quality_profile"], "showcase")
        design = (source.parent.parent / "design.md").read_text(encoding="utf-8")
        self.assertIn(source.relative_to(REPOSITORY_ROOT).as_posix(), design)
        self.assertIn("role: core", design)
        self.assertIn("## Terminology", design)

    def test_project_ontology_defines_inheritance_and_qualified_identity(self):
        ontology = (REPOSITORY_ROOT / "docs/ontology.md").read_text(encoding="utf-8")
        for phrase in ("Terminology table", "Terminology inheritance", "Qualified concept identity"):
            self.assertIn(phrase, ontology)


if __name__ == "__main__":
    unittest.main()
