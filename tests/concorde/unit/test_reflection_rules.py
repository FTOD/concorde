import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import reflection_entry, tree_hashes, write_reflection_log
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, operation_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402

EXAMPLE_LOG = REPOSITORY_ROOT / "specs/concorde/features/005-record-workflow-reflections/contracts/examples/reflections.md"


def reflect_rules(result) -> list[str]:
    return sorted(item.rule_id for item in result.findings if item.rule_id.startswith("CONCORDE-REFLECT-"))


class ReflectionRuleTests(unittest.TestCase):
    def project(self, temporary: str) -> Path:
        project = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, project)
        return project

    def test_absent_log_and_well_formed_log_report_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            self.assertEqual(reflect_rules(validate_project(project)), [])
            log = project / "specs/example/reflections.md"
            log.write_text(EXAMPLE_LOG.read_text(encoding="utf-8").replace("feature.example.api.health-check", "feature.example.deliver").replace(
                "specs/example/modules/api/features/002-add-health-check/spec.md#functional-requirements", "specs/example/features/001-deliver/spec.md#requirements"), encoding="utf-8")
            result = validate_project(project)
            self.assertEqual(reflect_rules(result), [], [item.message for item in result.findings])
            self.assertEqual(result.status, "success")

    def test_each_seeded_breach_yields_exactly_its_rule(self):
        cases = {
            "CONCORDE-REFLECT-001": [reflection_entry("R-001", Observed="")],
            "CONCORDE-REFLECT-002": [reflection_entry("R-001"), reflection_entry("R-001")],
            "CONCORDE-REFLECT-003": [reflection_entry("R-001", Effect="ignored")],
            "CONCORDE-REFLECT-004": [reflection_entry("R-001", Concerns="specs/example/missing.md")],
        }
        for rule, entries in cases.items():
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                write_reflection_log(project, entries)
                result = validate_project(project)
                self.assertEqual(reflect_rules(result), [rule])
                finding = next(item for item in result.findings if item.rule_id == rule)
                self.assertEqual(finding.source, "specs/example/reflections.md")
                self.assertEqual(finding.severity, "error")
                self.assertTrue(finding.remediation)
                self.assertEqual(result.status, "invalid")

    def test_feature_and_concerns_references(self):
        accepted = ["module.example.api", "feature.example.api.invoke", "contract.example.workflow", "scenario.example.deliver",
                    "specs/example/module.md#structure", "specs/example/architecture.json:3", "specs/example/features/001-deliver/spec.md"]
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            write_reflection_log(project, [reflection_entry(f"R-{index:03d}", Concerns=value) for index, value in enumerate(accepted, start=1)])
            self.assertEqual(reflect_rules(validate_project(project)), [])
        rejected = {"unknown feature": reflection_entry("R-001", Feature="feature.example.missing"),
                    "module as feature": reflection_entry("R-001", Feature="module.example"),
                    "unknown id": reflection_entry("R-001", Concerns="contract.example.missing"),
                    "unsafe path": reflection_entry("R-001", Concerns="../outside.md")}
        for name, entry in rejected.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                write_reflection_log(project, [entry])
                self.assertEqual(reflect_rules(validate_project(project)), ["CONCORDE-REFLECT-004"])

    def test_archive_entries_are_validated_and_runs_are_byte_equivalent_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            log = write_reflection_log(project, [reflection_entry("R-001")])
            log.write_text(log.read_text(encoding="utf-8") + "\n## Archive\n\n### R-002 · Old\n\n- **Phase**: plan\n- **Date**: 2026-01-01\n- **Feature**: feature.example.deliver\n- **Kind**: nonsense\n- **Concerns**: specs/example/module.md\n- **Expected**: a\n- **Observed**: b\n- **Effect**: assumed\n- **Action**: c\n- **Improvement**: d\n- **Status**: dismissed\n- **Note**: e\n", encoding="utf-8")
            before = tree_hashes(project)
            outputs = [canonical_json(operation_envelope(validate_project(project))) for _ in range(3)]
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(tree_hashes(project), before)
            self.assertEqual(reflect_rules(validate_project(project)), ["CONCORDE-REFLECT-003"])

    def test_symlinked_log_is_a_source_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            target = Path(temporary) / "outside.md"
            target.write_text("# Reflections: X\n", encoding="utf-8")
            (project / "specs/example/reflections.md").symlink_to(target)
            result = validate_project(project)
            self.assertEqual(result.status, "invalid")
            self.assertEqual([item.rule_id for item in result.findings], ["CONCORDE-SOURCE-001"])


if __name__ == "__main__":
    unittest.main()
