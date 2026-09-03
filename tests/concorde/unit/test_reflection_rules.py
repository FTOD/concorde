import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import reflection_entry, tree_hashes, write_reflection_collection
from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, tool_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


def reflect_rules(result) -> list[str]:
    return sorted(item.rule_id for item in result.findings if item.rule_id.startswith("CONCORDE-REFLECT-"))


class ReflectionRuleTests(unittest.TestCase):
    def project(self, temporary: str) -> Path:
        project = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, project)
        return project

    def test_absent_collection_and_well_formed_documents_report_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            self.assertEqual(reflect_rules(validate_project(project)), [])
            write_reflection_collection(project, [reflection_entry("R-001")])
            result = validate_project(project)
            self.assertEqual(reflect_rules(result), [], [item.message for item in result.findings])
            self.assertEqual(result.status, "success")

    def test_each_seeded_breach_yields_its_rule_and_document_path(self):
        cases = {
            "CONCORDE-REFLECT-001": reflection_entry("R-001", Observed=""),
            "CONCORDE-REFLECT-003": reflection_entry("R-001", Kind="bug"),
            "CONCORDE-REFLECT-004": reflection_entry("R-001", Concerns="specs/example/missing.md"),
        }
        for rule, entry in cases.items():
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                write_reflection_collection(project, [entry])
                result = validate_project(project)
                self.assertEqual(reflect_rules(result), [rule])
                finding = next(item for item in result.findings if item.rule_id == rule)
                self.assertEqual(finding.source, ".concorde/reflections/R-001.md")
                self.assertEqual(finding.severity, "error")
                self.assertTrue(finding.remediation)
                self.assertEqual(result.status, "invalid")

    def test_feature_and_concerns_references(self):
        accepted = [
            "module.example.api",
            "feature.example.api.invoke",
            "contract.example.workflow",
            "interaction.example.deliver",
            "specs/example/architecture.md#relationships",
            "specs/example/diagrams/level-view.json:3",
            "specs/example/features/001-deliver.md",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            write_reflection_collection(project, [reflection_entry(f"R-{index:03d}", Concerns=value) for index, value in enumerate(accepted, start=1)])
            self.assertEqual(reflect_rules(validate_project(project)), [])
        rejected = {
            "unknown feature": reflection_entry("R-001", Feature="feature.example.missing"),
            "module as feature": reflection_entry("R-001", Feature="module.example"),
            "unknown id": reflection_entry("R-001", Concerns="contract.example.missing"),
            "unsafe path": reflection_entry("R-001", Concerns="../outside.md"),
        }
        for name, entry in rejected.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                write_reflection_collection(project, [entry])
                self.assertEqual(reflect_rules(validate_project(project)), ["CONCORDE-REFLECT-004"])

    def test_runs_are_byte_equivalent_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            write_reflection_collection(project, [reflection_entry("R-001")])
            before = tree_hashes(project)
            outputs = [canonical_json(tool_envelope(validate_project(project))) for _ in range(3)]
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(tree_hashes(project), before)

    def test_symlinked_reflection_document_is_a_source_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            collection = write_reflection_collection(project, [])
            target = Path(temporary) / "outside.md"
            target.write_text("outside\n", encoding="utf-8")
            (collection / "R-001.md").symlink_to(target)
            result = validate_project(project)
            self.assertEqual(result.status, "invalid")
            self.assertEqual([item.rule_id for item in result.findings], ["CONCORDE-SOURCE-001"])


if __name__ == "__main__":
    unittest.main()
