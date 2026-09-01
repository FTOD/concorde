import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, TWO_LEVEL_PROJECT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402
from concorde.validation.terminology import INHERITED_ONLY, normalize_expression  # noqa: E402


def ontology_findings(project: Path):
    return [item for item in validate_project(project).findings if item.rule_id.startswith("CONCORDE-ONTOLOGY-")]


def declaration(rows: str) -> str:
    return f"## Terminology\n\n| Term | Meaning | Relationships |\n|---|---|---|\n{rows}\n"


class TerminologyRuleTests(unittest.TestCase):
    def fixture(self, temporary: str, source: Path = VALID_PROJECT) -> Path:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        for design in project.glob("specs/**/design.md"):
            current = design.read_text(encoding="utf-8")
            if "## Terminology" in current:
                continue
            design.write_text(
                current.rstrip()
                + f"\n\n## Terminology\n\n{INHERITED_ONLY}\n",
                encoding="utf-8",
            )
        self.assertEqual(ontology_findings(project), [])
        return project

    def set_declaration(self, design: Path, content: str) -> None:
        text = design.read_text(encoding="utf-8")
        marker = "## Terminology\n\n"
        design.write_text(text[: text.index(marker)] + content, encoding="utf-8")

    def test_normalization_is_case_and_punctuation_stable_without_stemming(self):
        self.assertEqual(normalize_expression("  Workspace-File  "), "workspace file")
        self.assertEqual(normalize_expression("WORKSPACE_file"), "workspace file")
        self.assertNotEqual(normalize_expression("concept"), normalize_expression("concepts"))

    def test_valid_local_table_alias_and_inherited_relationship_resolve(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary)
            root = project / "specs/example/design.md"
            feature = project / "specs/example/features/001-deliver/design.md"
            self.set_declaration(root, declaration(
                "| `Workspace File`<br>Aliases: `Artifact` | A file with an explicit workflow role. | `belongs to` → `Module` |\n"
                "| `Module` | One architecture level. | `owns` → `Workspace File` |"
            ))
            self.set_declaration(feature, declaration(
                "| `Delivery` | One observable completed outcome. | `uses` → `Artifact` |"
            ))
            self.assertEqual(ontology_findings(project), [])

    def test_missing_malformed_and_incomplete_declarations_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary)
            design = project / "specs/example/features/001-deliver/design.md"
            design.write_text(design.read_text(encoding="utf-8").split("## Terminology", 1)[0], encoding="utf-8")
            self.assertEqual([item.rule_id for item in ontology_findings(project)], ["CONCORDE-ONTOLOGY-001"])

            design.write_text(design.read_text(encoding="utf-8").rstrip() + "\n\n## Terminology\n\n| Word | Definition | Links |\n|---|---|---|\n| `Delivery` | Outcome. | None |\n", encoding="utf-8")
            self.assertEqual([item.rule_id for item in ontology_findings(project)], ["CONCORDE-ONTOLOGY-002"])

            self.set_declaration(design, declaration("| `Delivery` |  | None |"))
            self.assertEqual([item.rule_id for item in ontology_findings(project)], ["CONCORDE-ONTOLOGY-006"])

    def test_duplicate_local_expression_and_inherited_redefinition_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary)
            root = project / "specs/example/design.md"
            child = project / "specs/example/architecture/modules/api/design.md"
            self.set_declaration(root, declaration("| `Module` | One architecture level. | None |"))
            self.set_declaration(child, declaration(
                "| `Endpoint`<br>Aliases: `Route` | One addressable operation. | None |\n"
                "| `route!` | A conflicting local expression. | None |\n"
                "| `Module` | An incompatible child meaning. | None |"
            ))
            rules = [item.rule_id for item in ontology_findings(project)]
            self.assertIn("CONCORDE-ONTOLOGY-003", rules)
            self.assertIn("CONCORDE-ONTOLOGY-004", rules)

    def test_unresolved_and_ambiguous_relationship_targets_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary)
            root = project / "specs/example/design.md"
            feature = project / "specs/example/features/001-deliver/design.md"
            self.set_declaration(root, declaration(
                "| `Module`<br>Aliases: `Owner` | One architecture level. | None |\n"
                "| `Maintainer`<br>Aliases: `Owner!` | A human reviewer. | None |"
            ))
            self.set_declaration(feature, declaration(
                "| `Delivery` | One outcome. | `uses` → `Missing term`; `owned by` → `Owner` |"
            ))
            findings = [item for item in ontology_findings(project) if item.rule_id == "CONCORDE-ONTOLOGY-005"]
            self.assertEqual(len(findings), 2)
            self.assertTrue(any("does not resolve" in item.message for item in findings))
            self.assertTrue(any("ambiguous" in item.message for item in findings))

    def test_same_surface_term_is_allowed_on_unrelated_branches(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary)
            root_feature = project / "specs/example/features/001-deliver/design.md"
            child_module = project / "specs/example/architecture/modules/api/design.md"
            self.set_declaration(root_feature, declaration("| `Context` | Delivery-local information. | None |"))
            self.set_declaration(child_module, declaration("| `Context` | API-local information. | None |"))
            self.assertEqual(ontology_findings(project), [])

    def test_subfeature_inherits_its_parent_feature_after_module_ancestors(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.fixture(temporary, TWO_LEVEL_PROJECT)
            parent = project / "specs/example/features/001-checkout/design.md"
            child = project / "specs/example/features/001-checkout/subfeatures/001-authorize-payment/design.md"
            self.set_declaration(parent, declaration("| `Checkout` | One correlated purchase outcome. | None |"))
            self.set_declaration(child, declaration("| `Authorization` | Permission to continue checkout. | `part of` → `Checkout` |"))
            self.assertEqual(ontology_findings(project), [])


if __name__ == "__main__":
    unittest.main()
