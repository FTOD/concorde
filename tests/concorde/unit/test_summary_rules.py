import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_root
from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, operation_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402
from concorde.validation.summary import READING_BUDGET_WORDS, body_words  # noqa: E402


def rules(result) -> list[str]:
    return [item.rule_id for item in result.findings]


def summary_rules(result) -> list[str]:
    return [rule for rule in rules(result) if rule.startswith(("CONCORDE-SUMMARY-", "CONCORDE-MODULE-002"))]


class SummaryRuleTests(unittest.TestCase):
    def fixture(self, temporary: str) -> tuple[Path, Path]:
        project = Path(temporary)
        create_feature_root(project)
        return project, project / "specs/example/module.md"

    def test_writer_fixture_and_checked_in_fixture_pass_every_summary_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _ = self.fixture(temporary)
            self.assertEqual(summary_rules(validate_project(project)), [])
        result = validate_project(VALID_PROJECT)
        self.assertEqual(summary_rules(result), [])
        self.assertEqual(result.status, "success", result.findings)

    def test_missing_required_section_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, module = self.fixture(temporary)
            module.write_text(module.read_text().replace("## Representative Scenario", "## Scenario"), encoding="utf-8")
            result = validate_project(project)
            self.assertIn("CONCORDE-SUMMARY-001", rules(result))
            self.assertEqual(result.status, "invalid")

    def test_structure_must_link_the_declared_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, module = self.fixture(temporary)
            module.write_text(module.read_text().replace("[level-view.json](architecture/diagrams/level-view.json)", "the level view"), encoding="utf-8")
            self.assertIn("CONCORDE-SUMMARY-002", rules(validate_project(project)))

    def test_leaf_without_view_records_a_rationale_instead_of_a_link(self):
        leaf = (VALID_PROJECT / "specs/example/architecture/modules/api/module.md").read_text(encoding="utf-8")
        self.assertNotIn("view:", leaf.split("---")[1])
        self.assertIn("## Structure", leaf)
        self.assertNotIn("CONCORDE-SUMMARY-002", rules(validate_project(VALID_PROJECT)))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            module = root / "specs/example/architecture/modules/api/module.md"
            module.write_text(re.sub(r"## Structure\n\n.*?\n\n## Features", "## Structure\n\n## Features", module.read_text(encoding="utf-8"), flags=re.S), encoding="utf-8")
            self.assertIn("CONCORDE-SUMMARY-001", rules(validate_project(root)))

    def test_inventory_sections_need_a_table_or_none(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, module = self.fixture(temporary)
            text = module.read_text(encoding="utf-8")
            text = text.replace("## Submodules\n\nNone.", "## Submodules\n\nThere are no submodules right now.")
            module.write_text(text, encoding="utf-8")
            self.assertIn("CONCORDE-SUMMARY-003", rules(validate_project(project)))

    def test_design_reference_must_be_reachable_from_the_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, module = self.fixture(temporary)
            module.write_text(module.read_text().replace("[design reference](design.md)", "the design reference"), encoding="utf-8")
            self.assertIn("CONCORDE-SUMMARY-004", rules(validate_project(project)))

    def test_missing_module_design_reference_is_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _ = self.fixture(temporary)
            (project / "specs/example/design.md").unlink()
            result = validate_project(project)
            self.assertIn("CONCORDE-MODULE-002", rules(result))
            self.assertEqual(result.status, "invalid")
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-MODULE-002")
            self.assertEqual(finding.source, "specs/example/design.md")
            self.assertEqual(finding.severity, "error")

    def test_reading_budget_overrun_is_a_warning_that_keeps_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            self.assertEqual(validate_project(root).status, "success")
            module = root / "specs/example/module.md"
            filler = "\n\n" + " ".join(["word"] * (READING_BUDGET_WORDS + 50)) + "\n"
            module.write_text(module.read_text(encoding="utf-8") + filler, encoding="utf-8")
            result = validate_project(root)
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-SUMMARY-005")
            self.assertEqual(finding.severity, "warning")
            self.assertIn("4000-word", finding.message)
            self.assertEqual(result.status, "success")
            self.assertEqual(result.result["summary"]["warnings"], 1)
            self.assertEqual(result.result["summary"]["errors"], 0)

    def test_body_words_ignores_front_matter_fences_and_comments(self):
        body = "# T\n\n```json\n{\"a\": 1, \"b\": 2}\n```\n\n<!-- hidden words here -->\n\nfour words are here\n"
        self.assertEqual(body_words(body), 6)  # "# T" (2) + "four words are here" (4); fence and comment ignored

    def test_repeated_validation_is_byte_equivalent(self):
        outputs = [canonical_json(operation_envelope(validate_project(VALID_PROJECT))) for _ in range(2)]
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
