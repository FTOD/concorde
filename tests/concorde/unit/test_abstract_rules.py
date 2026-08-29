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
from concorde.validation.summary import body_words  # noqa: E402
from concorde.validation.abstract import REQUIRED_ABSTRACT_SECTIONS, ABSTRACT_BUDGET_WORDS  # noqa: E402


FEATURE = "specs/example/features/001-deliver"


def abstract_rules(result) -> list[str]:
    return [item.rule_id for item in result.findings if item.rule_id.startswith("CONCORDE-ABSTRACT-")]


def abstract_findings(result, rule: str):
    return [item for item in result.findings if item.rule_id == rule]


class AbstractRuleTests(unittest.TestCase):
    def fixture(self, temporary: str) -> tuple[Path, Path, Path]:
        project = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, project)
        design = project / FEATURE / "design.md"
        if "**FR-001**" not in design.read_text(encoding="utf-8"):
            design.write_text(
                design.read_text(encoding="utf-8").rstrip() + "\n\n## Requirements\n\n- **FR-001**: Delivery is observable.\n- **FR-002**: Delivery never mutates sources.\n",
                encoding="utf-8",
            )
        abstract = project / FEATURE / "abstract.md"
        abstract.write_text(
            "# Feature Abstract: Deliver\n\n`feature.example.deliver` · specified at `module.example`.\n\n"
            "## Purpose\n\nDeliver the fixture outcome.\n\n"
            "## Functionality\n\nOne observable outcome through the workflow contract.\n\n"
            "## Structure\n\nThe level view is [level-view.json](../../architecture/diagrams/level-view.json).\n\n"
            "## Logic\n\n1. Invoke.\n2. Deliver.\n\n**Rules the implementation must keep**\n\n- Delivery is observable and read-only (FR-001, FR-002).\n\n"
            "## Read Next\n\n- [design.md](design.md) and [implementation.md](implementation.md).\n",
            encoding="utf-8",
        )
        return project, design, abstract

    def test_writer_fixture_and_checked_in_fixture_pass_every_abstract_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            create_feature_root(project)
            self.assertEqual(abstract_rules(validate_project(project)), [])
        result = validate_project(VALID_PROJECT)
        self.assertEqual(abstract_rules(result), [])
        self.assertEqual(result.status, "success", result.findings)
        self.assertEqual(REQUIRED_ABSTRACT_SECTIONS, ("Purpose", "Functionality", "Structure", "Logic", "Read Next"))

    def test_section_shape_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _, abstract = self.fixture(temporary)
            self.assertEqual(abstract_rules(validate_project(project)), [])
            good = abstract.read_text(encoding="utf-8")
            # missing section
            abstract.write_text(good.replace("## Functionality\n\nOne observable outcome through the workflow contract.\n\n", ""), encoding="utf-8")
            findings = abstract_findings(validate_project(project), "CONCORDE-ABSTRACT-001")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].source, f"{FEATURE}/abstract.md")
            self.assertIn("Purpose, Structure, Logic, Read Next", findings[0].message)
            # extra section
            abstract.write_text(good + "\n## Notes\n\nExtra.\n", encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), ["CONCORDE-ABSTRACT-001"])
            # out of order
            reordered = good.replace("## Purpose\n\nDeliver the fixture outcome.\n\n", "").replace("## Read Next", "## Purpose\n\nDeliver the fixture outcome.\n\n## Read Next")
            abstract.write_text(reordered, encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), ["CONCORDE-ABSTRACT-001"])
            # empty section
            abstract.write_text(good.replace("Deliver the fixture outcome.\n", "\n"), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), ["CONCORDE-ABSTRACT-001"])
            # a fenced ## inside a code block is not a heading
            abstract.write_text(good.replace("## Read Next", "```text\n## not a heading\n```\n\n## Read Next"), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), [])

    def test_structure_needs_a_diagram_link_view_link_or_text_sketch(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _, abstract = self.fixture(temporary)
            good = abstract.read_text(encoding="utf-8")
            abstract.write_text(good.replace("The level view is [level-view.json](../../architecture/diagrams/level-view.json).", "Parts collaborate."), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), ["CONCORDE-ABSTRACT-002"])
            abstract.write_text(good.replace("The level view is [level-view.json](../../architecture/diagrams/level-view.json).", "```text\nmaintainer -> module\n```"), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), [])
            abstract.write_text(good.replace("The level view is [level-view.json](../../architecture/diagrams/level-view.json).", 'See <a href="/architecture/example.html">the view</a>.'), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), [])
            abstract.write_text(good.replace("[level-view.json](../../architecture/diagrams/level-view.json)", "[the view](specs/example/architecture/diagrams/level-view.json)"), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), [])

    def test_logic_citations_must_resolve_in_the_adjacent_design(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, design, abstract = self.fixture(temporary)
            good = abstract.read_text(encoding="utf-8")
            abstract.write_text(good.replace("(FR-001, FR-002)", "(FR-001, FR-999)"), encoding="utf-8")
            findings = abstract_findings(validate_project(project), "CONCORDE-ABSTRACT-003")
            self.assertEqual(len(findings), 1)
            self.assertIn("FR-999", findings[0].message)
            abstract.write_text(good.replace(" (FR-001, FR-002)", ""), encoding="utf-8")
            findings = abstract_findings(validate_project(project), "CONCORDE-ABSTRACT-003")
            self.assertEqual(len(findings), 1)
            self.assertIn("without citing", findings[0].message)
            # A design without FR-NNN identifiers only forbids unknown citations.
            design.write_text(design.read_text(encoding="utf-8").replace("**FR-001**", "FR-001").replace("**FR-002**", "FR-002"), encoding="utf-8")
            self.assertEqual(abstract_rules(validate_project(project)), [])

    def test_reading_budget_is_a_warning_that_keeps_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _, abstract = self.fixture(temporary)
            good = abstract.read_text(encoding="utf-8")
            padding = " ".join(["word"] * (ABSTRACT_BUDGET_WORDS + 1))
            abstract.write_text(good.replace("Deliver the fixture outcome.", padding), encoding="utf-8")
            self.assertGreater(body_words(abstract.read_text(encoding="utf-8")), ABSTRACT_BUDGET_WORDS)
            result = validate_project(project)
            findings = abstract_findings(result, "CONCORDE-ABSTRACT-004")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].severity, "warning")
            self.assertEqual(result.status, "success")
            self.assertEqual(abstract_rules(validate_project(project)), ["CONCORDE-ABSTRACT-004"])

    def test_abstract_findings_are_deterministic_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _, abstract = self.fixture(temporary)
            abstract.write_text(abstract.read_text(encoding="utf-8").replace("(FR-001, FR-002)", "(FR-999)"), encoding="utf-8")
            before = {path: path.read_bytes() for path in project.rglob("*") if path.is_file()}
            first = canonical_json(operation_envelope(validate_project(project)))
            second = canonical_json(operation_envelope(validate_project(project)))
            self.assertEqual(first, second)
            self.assertEqual({path: path.read_bytes() for path in project.rglob("*") if path.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
