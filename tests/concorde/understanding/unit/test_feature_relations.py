import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import (
    CONTEXT_PROJECT,
    REPOSITORY_ROOT,
    RUNTIME_ROOT,
    TWO_LEVEL_PROJECT,
    VALID_PROJECT,
)

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.model import FeatureRelation  # noqa: E402
from concorde.understanding.repository import ProjectRepository  # noqa: E402
from concorde.understanding.validate import validate_project  # noqa: E402


PERMISSION_PLANNING_PROJECT = REPOSITORY_ROOT / "tests/concorde/fixtures/permission-planning-project"


class FeatureRelationTests(unittest.TestCase):
    def copy(self, source: Path, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(source, root)
        return root

    def test_plain_string_entries_parse_as_relates_to(self):
        package = ProjectRepository(VALID_PROJECT).load()
        feature = package.features["feature.example.deliver"]
        self.assertEqual(feature.relations, (FeatureRelation("feature.example.api.invoke", "relates_to"),))
        self.assertEqual(feature.related_features, ("feature.example.api.invoke",))

    def test_typed_mapping_entries_parse_with_their_declared_relation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - id: feature.example.api.invoke\n    relation: depends_on\n",
                ),
                encoding="utf-8",
            )
            package = ProjectRepository(root).load()
            feature = package.features["feature.example.deliver"]
            self.assertEqual(feature.relations, (FeatureRelation("feature.example.api.invoke", "depends_on"),))
            self.assertEqual(feature.related_features, ("feature.example.api.invoke",))
            result = validate_project(root)
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual(result.findings, ())

    def test_unknown_relation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - id: feature.example.api.invoke\n    relation: orbits\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-006")
            self.assertIn("vocabulary", finding.message)
            self.assertEqual(finding.subject_id, "feature.example.deliver")

    def test_self_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - id: feature.example.deliver\n    relation: relates_to\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-006")
            self.assertIn("itself", finding.message.lower())
            self.assertEqual(finding.subject_id, "feature.example.deliver")

    def test_malformed_mapping_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - id: feature.example.api.invoke\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-003")
            self.assertEqual(finding.subject_id, "feature.example.deliver")

    def test_extra_key_mapping_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - id: feature.example.api.invoke\n    relation: relates_to\n    note: extra\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            self.assertTrue(any(item.rule_id == "CONCORDE-FEATURE-003" for item in result.findings))

    def test_duplicate_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(VALID_PROJECT, temporary)
            feature_path = root / "specs/example/features/001-deliver.md"
            feature_path.write_text(
                feature_path.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.api.invoke\n",
                    "related_features:\n  - feature.example.api.invoke\n  - feature.example.api.invoke\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-003")
            self.assertIn("duplicate", finding.message.lower())

    def test_two_feature_composes_cycle_is_reported_on_both_features(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(TWO_LEVEL_PROJECT, temporary)
            checkout = root / "specs/example/features/001-checkout.md"
            checkout.write_text(
                checkout.read_text(encoding="utf-8").replace(
                    "  - feature.example.atomic\n",
                    "  - id: feature.example.atomic\n    relation: composes\n",
                ),
                encoding="utf-8",
            )
            atomic = root / "specs/example/features/002-atomic.md"
            atomic.write_text(
                atomic.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.checkout\n",
                    "related_features:\n  - id: feature.example.checkout\n    relation: composes\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            cycle_findings = [item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-007"]
            subjects = {item.subject_id for item in cycle_findings}
            self.assertEqual(subjects, {"feature.example.checkout", "feature.example.atomic"})
            self.assertTrue(all("composes" in item.message for item in cycle_findings))

    def test_composes_and_its_inverse_form_from_the_other_side_is_not_a_cycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(TWO_LEVEL_PROJECT, temporary)
            checkout = root / "specs/example/features/001-checkout.md"
            checkout.write_text(
                checkout.read_text(encoding="utf-8").replace(
                    "  - feature.example.atomic\n",
                    "  - id: feature.example.atomic\n    relation: composes\n",
                ),
                encoding="utf-8",
            )
            atomic = root / "specs/example/features/002-atomic.md"
            atomic.write_text(
                atomic.read_text(encoding="utf-8").replace(
                    "related_features:\n  - feature.example.checkout\n",
                    "related_features:\n  - id: feature.example.checkout\n    relation: composed_by\n",
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual(result.findings, ())

    def test_requires_cycle_via_interfaces_is_reported_on_both_features(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(TWO_LEVEL_PROJECT, temporary)
            authorize = root / "specs/example/features/003-authorize-payment.md"
            authorize.write_text(
                authorize.read_text(encoding="utf-8").replace(
                    "  required: []\n",
                    "  required:\n    - contract.example.confirmation\n",
                    1,
                ),
                encoding="utf-8",
            )
            result = validate_project(root)
            self.assertEqual(result.status, "invalid")
            cycle_findings = [item for item in result.findings if item.rule_id == "CONCORDE-FEATURE-007"]
            subjects = {item.subject_id for item in cycle_findings}
            self.assertEqual(subjects, {"feature.example.checkout.authorize", "feature.example.checkout.confirm"})
            self.assertTrue(all("requires" in item.message for item in cycle_findings))

    def test_fully_valid_fixtures_still_validate_with_zero_findings(self):
        for project in (VALID_PROJECT, CONTEXT_PROJECT, TWO_LEVEL_PROJECT):
            with self.subTest(project=project.name):
                result = validate_project(project)
                self.assertEqual(result.status, "success", result.findings)
                self.assertEqual(result.findings, ())

    def test_permission_planning_fixture_gains_no_related_feature_findings(self):
        # This fixture is intentionally imperfect elsewhere (permission-boundary scenarios), so it
        # is checked for the relation rules this change adds rather than for zero findings overall.
        related_feature_rules = {
            "CONCORDE-FEATURE-003", "CONCORDE-FEATURE-004", "CONCORDE-FEATURE-006", "CONCORDE-FEATURE-007",
        }
        result = validate_project(PERMISSION_PLANNING_PROJECT)
        offending = [item for item in result.findings if item.rule_id in related_feature_rules]
        self.assertEqual(offending, [])


if __name__ == "__main__":
    unittest.main()
