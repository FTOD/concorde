import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.validate import validate_project  # noqa: E402


class ValidationRuleTests(unittest.TestCase):
    def project_copy(self, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, root)
        return root

    def test_valid_profile_seven_fixture_has_no_findings(self):
        result = validate_project(VALID_PROJECT)
        self.assertEqual(result.status, "success", result.findings)
        self.assertEqual(result.findings, ())

    def test_legacy_durable_artifacts_and_directories_are_migration_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            features = root / "specs/example/features"
            (features / "abstract.md").write_text("legacy", encoding="utf-8")
            (features / "implementation.md").write_text("legacy", encoding="utf-8")
            contracts = features / "contracts"
            contracts.mkdir()
            (contracts / "contract.md").write_text("legacy", encoding="utf-8")
            result = validate_project(root)
            legacy = [item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-LEGACY"]
            self.assertEqual(result.status, "invalid")
            self.assertEqual({Path(item.source).name for item in legacy}, {"abstract.md", "implementation.md", "contracts", "contract.md"})
            self.assertTrue(all(item.remediation for item in legacy))

    def test_artifact_type_module_names_are_advisory_findings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            modules = root / "specs/example/modules"
            (modules / "api").rename(modules / "utils")
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix in {".md", ".json"}:
                    text = path.read_text(encoding="utf-8")
                    if "module.example.api" in text or "modules/api/" in text:
                        path.write_text(
                            text.replace("module.example.api", "module.example.utils").replace("modules/api/", "modules/utils/"),
                            encoding="utf-8",
                        )
            result = validate_project(root)
            advisories = [item for item in result.findings if item.rule_id == "CONCORDE-MODULE-005"]
            self.assertEqual(result.status, "success", result.findings)
            self.assertEqual([item.severity for item in advisories], ["warning"])
            self.assertEqual(advisories[0].subject_id, "module.example.utils")
            self.assertIn("utils", advisories[0].message)
            self.assertEqual(result.result["summary"]["warnings"], 1)

    def test_module_and_feature_inventories_must_match_physical_children(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            architecture = root / "specs/example/architecture.md"
            architecture.write_text(architecture.read_text(encoding="utf-8").replace("  - module.example.api\n", "", 1).replace("  - feature.example.deliver\n", "", 1), encoding="utf-8")
            rules = {item.rule_id for item in validate_project(root).findings}
            self.assertIn("CONCORDE-MODULE-003", rules)
            self.assertIn("CONCORDE-MODULE-004", rules)

    def test_temporal_artifacts_stay_below_control_state_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            module = root / "specs/example"
            (module / "tasks.md").write_text("# Tasks", encoding="utf-8")
            result = validate_project(root)
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-001")
            self.assertEqual(finding.source, "specs/example/tasks.md")

    def test_specification_local_attempts_and_reflection_log_are_legacy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            attempt = root / "specs/example/attempts/001-deliver"
            attempt.mkdir(parents=True)
            (attempt / "plan.md").write_text("# Legacy plan\n", encoding="utf-8")
            (root / "specs/example/reflections.md").write_text("# Legacy reflections\n", encoding="utf-8")
            legacy = [
                item for item in validate_project(root).findings
                if item.rule_id == "CONCORDE-LAYOUT-LEGACY"
            ]
            self.assertEqual(
                {item.source for item in legacy},
                {"specs/example/attempts", "specs/example/reflections.md"},
            )

    def test_root_docs_tree_is_a_parallel_documentation_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("# Parallel guide\n", encoding="utf-8")
            result = validate_project(root)
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-DOCS")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(finding.source, "docs")
            self.assertIn("module architecture or direct feature design", finding.remediation)


if __name__ == "__main__":
    unittest.main()
