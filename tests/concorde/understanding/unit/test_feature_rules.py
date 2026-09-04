import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, TWO_LEVEL_PROJECT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.validate import validate_project  # noqa: E402


class FeatureRuleTests(unittest.TestCase):
    def copy(self, source: Path, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(source, root)
        return root

    def test_related_features_are_flat_summaries_not_containment(self):
        result = validate_project(TWO_LEVEL_PROJECT)
        self.assertEqual(result.status, "success", result.findings)
        self.assertFalse(list((TWO_LEVEL_PROJECT / "specs/example").rglob("subfeatures")))

    def test_missing_design_sections_are_reported_from_the_single_document(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature = root / "specs/example/features/001-deliver.md"
            feature.write_text(feature.read_text(encoding="utf-8").replace("## Usage Scenarios", "## Missing Usage"), encoding="utf-8")
            findings = [item for item in validate_project(root).findings if item.rule_id == "CONCORDE-FEATURE-002"]
            self.assertEqual(len(findings), 1)
            self.assertIn("Usage Scenarios", findings[0].message)

    def test_unknown_related_feature_is_rejected_without_implying_a_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature = root / "specs/example/features/001-deliver.md"
            feature.write_text(feature.read_text(encoding="utf-8").replace("feature.example.api.invoke", "feature.example.missing", 1), encoding="utf-8")
            finding = next(item for item in validate_project(root).findings if item.rule_id == "CONCORDE-FEATURE-004")
            self.assertIn("does not resolve", finding.message)
            self.assertNotIn("parent", finding.message.lower())

    def test_nested_subfeatures_directory_is_legacy_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            nested = root / "specs/example/features/subfeatures/001-retry"
            nested.mkdir(parents=True)
            (nested / "design.md").write_text("---\nid: feature.example.retry\nkind: feature\n---\n# Retry\n", encoding="utf-8")
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-LEGACY" and item.source.endswith("subfeatures") for item in findings))

    def test_feature_id_grammar_matches_safe_attempt_component_grammar(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature = root / "specs/example/features/001-deliver.md"
            feature.write_text(
                feature.read_text(encoding="utf-8").replace(
                    "id: feature.example.deliver",
                    "id: feature.example..deliver",
                    1,
                ),
                encoding="utf-8",
            )
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-FEATURE-001" for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
