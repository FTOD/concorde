import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import reflection_entry, write_reflection_log
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.reflections import (  # noqa: E402
    EFFECTS,
    KINDS,
    PHASES,
    REQUIRED_FIELDS,
    STATUSES,
    log_path,
    parse_reflection_log,
    strip_reference_suffix,
)


class ReflectionParserTests(unittest.TestCase):
    def test_contract_example_and_project_log_parse_without_problems(self):
        for relative in (
            "specs/concorde/features/005-record-workflow-reflections/contracts/examples/reflections.md",
            "specs/concorde/reflections.md",
        ):
            with self.subTest(log=relative):
                parsed = parse_reflection_log((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
                self.assertEqual(parsed.problems, ())
                self.assertGreaterEqual(len(parsed.entries), 2)
                for entry in parsed.entries:
                    self.assertTrue(all(entry.fields.get(name) for name in REQUIRED_FIELDS), entry.identifier)

    def test_vocabularies_match_the_contract(self):
        self.assertEqual(KINDS, {"specification", "architecture", "guidance", "tooling", "environment", "implementation"})
        self.assertEqual(EFFECTS, {"assumed", "worked-around", "deferred", "blocked"})
        self.assertEqual(STATUSES, {"open", "resolved", "dismissed"})
        self.assertIn("fast-loop", PHASES)
        self.assertEqual(log_path("specs/example/"), "specs/example/reflections.md")
        self.assertEqual(strip_reference_suffix("specs/x/design.md#functional-requirements"), "specs/x/design.md")
        self.assertEqual(strip_reference_suffix("src/api/invoke.py:42"), "src/api/invoke.py")
        self.assertEqual(strip_reference_suffix("feature.example.deliver"), "feature.example.deliver")

    def test_selection_by_feature_and_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            log = write_reflection_log(project, [
                reflection_entry("R-001"),
                reflection_entry("R-002", status="resolved"),
                reflection_entry("R-003", feature="feature.example.api.invoke"),
                reflection_entry("R-004", status="dismissed", occurrences=["analyze 2026-08-29 feature.example.api.invoke — seen again"]),
            ])
            parsed = parse_reflection_log(log.read_text(encoding="utf-8"))
            self.assertEqual(parsed.problems, ())
            self.assertEqual([entry.identifier for entry in parsed.entries_for("feature.example.deliver")], ["R-001", "R-002", "R-004"])
            self.assertEqual(parsed.open_count("feature.example.deliver"), 1)
            self.assertEqual(parsed.open_count("feature.example.api.invoke"), 1)
            self.assertEqual(parsed.open_count("feature.example.none"), 0)
            self.assertEqual(parsed.summary("feature.example.deliver"), {"entries": 3, "open": 1, "resolved": 1, "dismissed": 1})
            self.assertEqual(parsed.entries[3].occurrences, ("analyze 2026-08-29 feature.example.api.invoke — seen again",))

    def test_each_breach_is_reported_once_with_its_code(self):
        cases = {
            "shape": reflection_entry("R-001", Effect=""),
            "vocabulary": reflection_entry("R-001", Kind="bug"),
            "date": reflection_entry("R-001", Date="28/08/2026"),
            "note": reflection_entry("R-001", status="resolved", Note=""),
        }
        for name, entry in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                log = write_reflection_log(Path(temporary), [entry])
                parsed = parse_reflection_log(log.read_text(encoding="utf-8"))
                self.assertEqual(len(parsed.problems), 1, parsed.problems)
                self.assertEqual(parsed.problems[0].identifier, "R-001")
                self.assertTrue(parsed.problems[0].remediation)
        with tempfile.TemporaryDirectory() as temporary:
            log = write_reflection_log(Path(temporary), [reflection_entry("R-001"), reflection_entry("R-001")])
            parsed = parse_reflection_log(log.read_text(encoding="utf-8"))
            self.assertEqual([problem.code for problem in parsed.problems], ["duplicate"])
        parsed = parse_reflection_log("# Reflections: X\n\n### Not an entry\n\n- **Phase**: plan\n")
        self.assertEqual([problem.code for problem in parsed.problems], ["shape"])
        self.assertEqual(parsed.entries, ())

    def test_archive_section_continuations_and_fences_are_handled(self):
        text = (
            "# Reflections: X\n\nPreamble with a fence:\n\n```text\n### R-999 · not an entry\n```\n\n"
            "## Archive\n\n### R-001 · Archived\n\n- **Phase**: plan\n- **Date**: 2026-01-01\n- **Feature**: feature.example.deliver\n"
            "- **Kind**: guidance\n- **Concerns**: specs/example/module.md\n- **Expected**: One line\n  continued on the next.\n"
            "- **Observed**: Seen.\n- **Effect**: assumed\n- **Action**: Done.\n- **Improvement**: None.\n- **Status**: dismissed\n- **Note**: Old.\n"
        )
        parsed = parse_reflection_log(text)
        self.assertEqual(parsed.problems, ())
        self.assertEqual(parsed.entries[0].fields["Expected"], "One line continued on the next.")
        self.assertEqual(parsed.entries[0].line, 11)


if __name__ == "__main__":
    unittest.main()
