import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import reflection_entry, write_reflection_collection
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.reflections import (  # noqa: E402
    HUMAN_INTERVENTIONS,
    KINDS,
    PHASES,
    STATUSES,
    TRIAGE_STATES,
    format_reflection_id,
    index_path,
    parse_reflection_document,
    parse_reflections,
    reflection_number,
    reflection_path,
    reflections_path,
    strip_reference_suffix,
)


def parse_collection(directory: Path):
    documents = {
        path.relative_to(directory.parents[1]).as_posix(): path.read_text(encoding="utf-8")
        for path in directory.glob("R-*.md")
    }
    return parse_reflections(documents, (directory / "index.json").read_text(encoding="utf-8"))


class ReflectionParserTests(unittest.TestCase):
    def test_feature_implementation_narratives_are_absent_from_profile_seven_specs(self):
        self.assertEqual(sorted((REPOSITORY_ROOT / "specs").rglob("implementation.md")), [])

    def test_contract_examples_parse_without_problems(self):
        directory = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/reflections"
        documents = {
            f".concorde/reflections/{path.name}": path.read_text(encoding="utf-8")
            for path in directory.glob("R-*.md")
        }
        parsed = parse_reflections(documents, (directory / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(parsed.problems, ())
        self.assertEqual(len(parsed.entries), 2)

    def test_vocabularies_and_paths_match_the_contract(self):
        self.assertEqual(KINDS, {"specification", "architecture", "guidance", "tooling", "environment", "implementation"})
        self.assertEqual(STATUSES, {"open", "resolved", "dismissed"})
        self.assertEqual(TRIAGE_STATES, {"pending", "complete"})
        self.assertEqual(HUMAN_INTERVENTIONS, {"required", "not-required"})
        self.assertIn("fast-loop", PHASES)
        self.assertEqual(reflections_path(), ".concorde/reflections")
        self.assertEqual(index_path(), ".concorde/reflections/index.json")
        self.assertEqual(reflection_path("R-042"), ".concorde/reflections/R-042.md")
        self.assertEqual(strip_reference_suffix("specs/x/design.md#functional-requirements"), "specs/x/design.md")
        self.assertEqual(strip_reference_suffix("src/api/invoke.py:42"), "src/api/invoke.py")
        self.assertEqual(format_reflection_id(1000), "R-1000")
        self.assertEqual(reflection_number("R-001"), 1)
        self.assertIsNone(reflection_number("R-0001"))

    def test_index_is_canonical_and_not_below_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-007")])
            parsed = parse_collection(directory)
            self.assertEqual(parsed.problems, ())
            self.assertEqual(parsed.high_water, 7)
            low = parse_reflections(
                {".concorde/reflections/R-007.md": (directory / "R-007.md").read_text()},
                '{"schema_version": 1, "high_water": "R-006"}\n',
            )
            self.assertEqual([problem.code for problem in low.problems], ["shape"])
            missing = parse_reflections(
                {".concorde/reflections/R-007.md": (directory / "R-007.md").read_text()}, None
            )
            self.assertEqual([problem.code for problem in missing.problems], ["shape"])

    def test_selection_by_feature_status_and_occurrence(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [
                reflection_entry("R-001"),
                reflection_entry("R-002", status="resolved"),
                reflection_entry("R-003", feature="feature.example.api.invoke"),
                reflection_entry("R-004", status="dismissed", occurrences=["analyze 2026-08-29 feature.example.deliver — seen again"]),
            ])
            parsed = parse_collection(directory)
            self.assertEqual(parsed.problems, ())
            self.assertEqual([entry.identifier for entry in parsed.entries_for("feature.example.deliver")], ["R-001", "R-002", "R-004"])
            self.assertEqual(parsed.open_count("feature.example.deliver"), 1)
            self.assertEqual(parsed.summary("feature.example.deliver"), {"entries": 3, "open": 1, "resolved": 1, "dismissed": 1})
            self.assertEqual(parsed.entries[3].occurrences, ("analyze 2026-08-29 feature.example.deliver — seen again",))

    def test_pending_record_contains_only_problem_description(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001")])
            path = directory / "R-001.md"
            entry, problems = parse_reflection_document(path.read_text(), ".concorde/reflections/R-001.md")
            self.assertEqual(problems, ())
            self.assertEqual(entry.triage, "pending")
            self.assertEqual(entry.fields["Human Intervention"], "")
            self.assertEqual(entry.fields["Triage Analysis"], "")
            self.assertIn("User Comments", entry.fields)

            invalid = path.read_text().replace("triage: pending", "triage: pending\nhuman_intervention: required")
            _, problems = parse_reflection_document(invalid, ".concorde/reflections/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["shape"])

    def test_completed_triage_requires_analysis_resolution_and_intervention_decision(self):
        complete = reflection_entry(
            "R-001",
            Triage="complete",
            **{
                "Human Intervention": "required",
                "Triage Analysis": "The command contract and implementation disagree at the cited path.",
                "Proposed Resolution": "Reconcile the command implementation with its owning contract.",
                "Intervention Rationale": "The maintainer must choose which behavior is authoritative.",
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [complete])
            self.assertEqual(parse_collection(directory).problems, ())
            path = directory / "R-001.md"
            invalid = path.read_text().replace("## Triage Analysis\n\nThe command contract and implementation disagree at the cited path.", "## Triage Analysis\n")
            _, problems = parse_reflection_document(invalid, ".concorde/reflections/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["shape"])

    def test_shape_vocabulary_filename_and_duplicate_breaches(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001")])
            body = (directory / "R-001.md").read_text()
            _, problems = parse_reflection_document(body.replace("kind: tooling", "kind: bug"), ".concorde/reflections/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["vocabulary"])
            _, problems = parse_reflection_document(body.replace("## Evidence\n\n`specs", "## Evidence\n\n<!-- blank -->\n\n`specs", 1), ".concorde/reflections/R-002.md")
            self.assertIn("shape", [problem.code for problem in problems])
            duplicate = parse_reflections(
                {
                    ".concorde/reflections/R-001.md": body,
                    ".concorde/reflections/R-002.md": body.replace("# R-001", "# R-001"),
                },
                '{"schema_version": 1, "high_water": "R-002"}',
            )
            self.assertIn("duplicate", [problem.code for problem in duplicate.problems])

    def test_controlled_rewrite_preserves_identity_status_and_user_comments(self):
        complete = reflection_entry(
            "R-007",
            Triage="complete",
            **{
                "Human Intervention": "required",
                "Triage Analysis": "Evidence establishes the mismatch.",
                "Proposed Resolution": "Update the owning contract.",
                "Intervention Rationale": "A maintainer must choose the contract.",
                "User Comments": "Keep the current public behavior.",
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [complete])
            path = directory / "R-007.md"
            before, _ = parse_reflection_document(path.read_text(), ".concorde/reflections/R-007.md")
            rewritten = path.read_text().replace("specs/example/architecture.md", "specs/example/features/001-deliver.md")
            after, problems = parse_reflection_document(rewritten, ".concorde/reflections/R-007.md")
            self.assertEqual(problems, ())
            self.assertEqual((after.identifier, after.status), (before.identifier, before.status))
            self.assertEqual(after.fields["User Comments"], before.fields["User Comments"])


if __name__ == "__main__":
    unittest.main()
