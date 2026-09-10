import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.reflection_triage import reflection_entry, write_reflection_collection
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.reflections.reflections import (  # noqa: E402
    BUCKETS,
    KINDS,
    PHASES,
    STATUSES,
    bucket_for_intervention,
    bucket_path,
    format_reflection_id,
    human_intervention_for,
    index_path,
    parse_reflection_document,
    parse_reflections,
    reflection_document_paths,
    reflection_number,
    reflection_path,
    reflections_path,
    split_reflection_path,
    strip_reference_suffix,
    triage_state,
)


def parse_collection(directory: Path):
    documents = {
        path.relative_to(directory.parents[1]).as_posix(): path.read_text(encoding="utf-8")
        for bucket in BUCKETS
        for path in (directory / bucket).glob("R-*.md")
    }
    return parse_reflections(documents, (directory / "index.json").read_text(encoding="utf-8"))


class ReflectionParserTests(unittest.TestCase):
    def test_contract_examples_parse_without_problems(self):
        directory = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/reflections"
        documents = {
            f".concorde/reflections/{path.parent.name}/{path.name}": path.read_text(encoding="utf-8")
            for bucket in BUCKETS
            for path in (directory / bucket).glob("R-*.md")
        }
        parsed = parse_reflections(documents, (directory / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(parsed.problems, ())
        self.assertEqual(len(parsed.entries), 2)

    def test_vocabularies_and_paths_match_the_contract(self):
        self.assertEqual(KINDS, {"specification", "architecture", "guidance", "tooling", "environment", "implementation"})
        self.assertEqual(STATUSES, {"open", "resolved", "dismissed"})
        self.assertIn("fast-loop", PHASES)
        self.assertEqual(reflections_path(), ".concorde/reflections")
        self.assertEqual(index_path(), ".concorde/reflections/index.json")
        self.assertEqual(BUCKETS, ("pending", "planned", "needs-comments"))
        self.assertEqual(bucket_path("planned"), ".concorde/reflections/planned")
        self.assertEqual(reflection_path("R-042"), ".concorde/reflections/pending/R-042.md")
        self.assertEqual(reflection_path("R-042", "needs-comments"), ".concorde/reflections/needs-comments/R-042.md")
        with self.assertRaises(ValueError):
            reflection_path("R-042", "plans")
        self.assertEqual(split_reflection_path(".concorde/reflections/planned/R-001.md"), ("planned", "R-001"))
        self.assertEqual(split_reflection_path(".concorde/reflections/R-001.md"), (None, "R-001"))
        self.assertIsNone(split_reflection_path(".concorde/reflections/plans/R-001.md"))
        self.assertIsNone(split_reflection_path(".concorde/reflections/pending/R-0001.md"))
        self.assertEqual(strip_reference_suffix("specs/x/design.md#functional-requirements"), "specs/x/design.md")
        self.assertEqual(strip_reference_suffix("src/api/invoke.py:42"), "src/api/invoke.py")
        self.assertEqual(format_reflection_id(1000), "R-1000")
        self.assertEqual(reflection_number("R-001"), 1)
        self.assertIsNone(reflection_number("R-0001"))

    def test_bucket_derivation_helpers_agree_with_the_bucket_table(self):
        # A completed triage's human_intervention decision selects exactly one bucket.
        self.assertEqual(bucket_for_intervention("not-required"), "planned")
        self.assertEqual(bucket_for_intervention("required"), "needs-comments")
        with self.assertRaises(ValueError):
            bucket_for_intervention("maybe")

        # triage_state/human_intervention_for are the inverse: derived from the bucket, never stored.
        self.assertEqual(triage_state("pending"), "pending")
        self.assertEqual(triage_state("planned"), "complete")
        self.assertEqual(triage_state("needs-comments"), "complete")
        self.assertEqual(triage_state(None), "")
        self.assertEqual(human_intervention_for("needs-comments"), "required")
        self.assertEqual(human_intervention_for("planned"), "not-required")
        self.assertEqual(human_intervention_for("pending"), "")
        self.assertEqual(human_intervention_for(None), "")

    def test_index_is_canonical_and_not_below_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-007")])
            parsed = parse_collection(directory)
            self.assertEqual(parsed.problems, ())
            self.assertEqual(parsed.high_water, 7)
            document = (directory / "pending" / "R-007.md").read_text()
            low = parse_reflections(
                {".concorde/reflections/pending/R-007.md": document},
                '{"schema_version": 1, "high_water": "R-006"}\n',
            )
            self.assertEqual([problem.code for problem in low.problems], ["shape"])
            missing = parse_reflections({".concorde/reflections/pending/R-007.md": document}, None)
            self.assertEqual([problem.code for problem in missing.problems], ["shape"])

    def test_selection_by_feature_status_and_occurrence(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [
                reflection_entry("R-001"),
                reflection_entry("R-002", status="resolved"),
                reflection_entry("R-003", feature="module.example.api"),
                reflection_entry("R-004", status="dismissed", occurrences=["analyze 2026-08-29 module.example — seen again"]),
            ])
            parsed = parse_collection(directory)
            self.assertEqual(parsed.problems, ())
            self.assertEqual([entry.identifier for entry in parsed.entries_for("module.example")], ["R-001", "R-002", "R-004"])
            self.assertEqual(parsed.open_count("module.example"), 1)
            self.assertEqual(parsed.summary("module.example"), {"entries": 3, "open": 1, "resolved": 1, "dismissed": 1})
            self.assertEqual(parsed.entries[3].occurrences, ("analyze 2026-08-29 module.example — seen again",))
            self.assertEqual([entry.identifier for entry in parsed.closed()], ["R-002", "R-004"])

    def test_pending_record_contains_only_problem_description(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001")])
            path = directory / "pending" / "R-001.md"
            entry, problems = parse_reflection_document(path.read_text(), ".concorde/reflections/pending/R-001.md")
            self.assertEqual(problems, ())
            self.assertEqual(entry.triage, "pending")
            self.assertEqual(entry.bucket, "pending")
            self.assertFalse(entry.misplaced)
            self.assertEqual(entry.fields["Human Intervention"], "")
            self.assertEqual(entry.fields["Triage Analysis"], "")
            self.assertIn("User Comments", entry.fields)

    def test_triage_and_human_intervention_front_matter_are_unsupported_fields(self):
        # The bucket directory is the only record of triage state; the two legacy front-matter keys
        # are no longer part of the Reflection Document model at all, however they are spelled.
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001")])
            body = (directory / "pending" / "R-001.md").read_text()

            with_triage = body.replace("status: open\n", "status: open\ntriage: pending\n", 1)
            _, problems = parse_reflection_document(with_triage, ".concorde/reflections/pending/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["shape"])
            self.assertIn("triage", problems[0].message)
            self.assertIn("bucket directory", problems[0].remediation)

            with_human = body.replace("status: open\n", "status: open\nhuman_intervention: required\n", 1)
            _, problems = parse_reflection_document(with_human, ".concorde/reflections/pending/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["shape"])
            self.assertIn("human_intervention", problems[0].message)
            self.assertIn("bucket directory", problems[0].remediation)

            with_both = body.replace("status: open\n", "status: open\ntriage: pending\nhuman_intervention: required\n", 1)
            _, problems = parse_reflection_document(with_both, ".concorde/reflections/pending/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["shape"])
            self.assertIn("triage", problems[0].message)
            self.assertIn("human_intervention", problems[0].message)

    def test_shape_vocabulary_filename_and_duplicate_breaches(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001")])
            body = (directory / "pending" / "R-001.md").read_text()
            _, problems = parse_reflection_document(body.replace("kind: tooling", "kind: bug"), ".concorde/reflections/pending/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["vocabulary"])
            _, problems = parse_reflection_document(body.replace("## Evidence\n\n`specs", "## Evidence\n\n<!-- blank -->\n\n`specs", 1), ".concorde/reflections/pending/R-002.md")
            self.assertIn("shape", [problem.code for problem in problems])
            duplicate = parse_reflections(
                {
                    ".concorde/reflections/pending/R-001.md": body,
                    ".concorde/reflections/pending/R-002.md": body.replace("# R-001", "# R-001"),
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
                "Intervention Rationale": "A developer must choose the contract.",
                "User Comments": "Keep the current public behavior.",
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [complete])
            path = directory / "needs-comments" / "R-007.md"
            before, _ = parse_reflection_document(path.read_text(), ".concorde/reflections/needs-comments/R-007.md")
            rewritten = path.read_text().replace("src/example.py", "src/other.py")
            after, problems = parse_reflection_document(rewritten, ".concorde/reflections/needs-comments/R-007.md")
            self.assertEqual(problems, ())
            self.assertEqual((after.identifier, after.status), (before.identifier, before.status))
            self.assertEqual(after.fields["User Comments"], before.fields["User Comments"])

    def test_bucket_counts_and_closure_follow_the_derived_properties(self):
        planned = reflection_entry(
            "R-002",
            Triage="complete",
            **{
                "Human Intervention": "not-required",
                "Triage Analysis": "The helper glob omitted the bucket directories.",
                "Proposed Resolution": "Glob every bucket.",
                "Intervention Rationale": "Automation can apply the bounded fix.",
            },
        )
        waiting = reflection_entry(
            "R-003",
            status="resolved",
            Triage="complete",
            **{
                "Human Intervention": "required",
                "Triage Analysis": "The public timeout is unspecified.",
                "Proposed Resolution": "Clarify the contract.",
                "Intervention Rationale": "A developer must choose the value.",
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(Path(temporary), [reflection_entry("R-001"), planned, waiting])
            self.assertTrue((directory / "pending" / "R-001.md").is_file())
            self.assertTrue((directory / "planned" / "R-002.md").is_file())
            self.assertTrue((directory / "needs-comments" / "R-003.md").is_file())
            parsed = parse_collection(directory)
            self.assertEqual(parsed.problems, ())
            self.assertEqual(parsed.bucket_counts(), {"pending": 1, "planned": 1, "needs-comments": 1})
            self.assertEqual(parsed.misplaced(), ())
            self.assertEqual([entry.bucket for entry in parsed.entries], ["pending", "planned", "needs-comments"])
            # Developer status never changes the bucket: a resolved record stays exactly where its
            # triage-section content and bucket already agree.
            self.assertEqual(parsed.entries[2].status, "resolved")
            self.assertEqual(parsed.entries[2].bucket, "needs-comments")
            self.assertEqual(parsed.entries[2].expected_path, ".concorde/reflections/needs-comments/R-003.md")
            self.assertEqual([entry.identifier for entry in parsed.closed()], ["R-003"])

        auxiliary = {
            ".concorde/reflections/R-001.md": "",
            ".concorde/reflections/pending/R-002.md": "",
            ".concorde/reflections/needs-comments/R-003.md": "",
            ".concorde/reflections/plans/R-004.md": "",
            ".concorde/reflections/archive/R-005.md": "",
            ".concorde/reflections/index.json": "",
            ".concorde/reflections/pending/notes.md": "",
        }
        self.assertEqual(
            reflection_document_paths(auxiliary),
            (
                ".concorde/reflections/R-001.md",
                ".concorde/reflections/needs-comments/R-003.md",
                ".concorde/reflections/pending/R-002.md",
            ),
        )

    def test_placement_requires_the_bucket_to_agree_with_triage_content(self):
        filled = reflection_entry(
            "R-002",
            Triage="complete",
            **{
                "Triage Analysis": "The helper glob omitted the bucket directories.",
                "Proposed Resolution": "Glob every bucket.",
                "Intervention Rationale": "Automation can apply the bounded fix.",
            },
        )
        partly_filled = reflection_entry(
            "R-003",
            Triage="complete",
            **{
                "Triage Analysis": "",
                "Proposed Resolution": "Glob every bucket.",
                "Intervention Rationale": "Automation can apply the bounded fix.",
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = write_reflection_collection(
                Path(temporary), [reflection_entry("R-001"), filled, partly_filled],
            )
            pending_text = (directory / "pending" / "R-001.md").read_text()
            filled_text = (directory / "needs-comments" / "R-002.md").read_text()
            partly_filled_text = (directory / "needs-comments" / "R-003.md").read_text()

            # (a) pending with content: a filled document filed under pending/.
            entry, problems = parse_reflection_document(filled_text, ".concorde/reflections/pending/R-002.md")
            self.assertEqual([problem.code for problem in problems], ["placement"])
            self.assertIn("pending/", problems[0].message)
            self.assertIn("filled", problems[0].message)
            self.assertIn("--relocate", problems[0].remediation)
            # Still bucketed, so relocation never touches it: there is nothing to move it to.
            self.assertFalse(entry.misplaced)
            self.assertEqual(entry.expected_path, ".concorde/reflections/pending/R-002.md")

            # (b) planned without content: an empty (or only partly filled) document filed under
            # planned/ or needs-comments/ — "any" empty section disagrees, not only "all" empty.
            _, problems = parse_reflection_document(pending_text, ".concorde/reflections/planned/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["placement"])
            self.assertIn("planned/", problems[0].message)
            self.assertIn("not all filled", problems[0].message)
            entry, problems = parse_reflection_document(partly_filled_text, ".concorde/reflections/needs-comments/R-003.md")
            self.assertEqual([problem.code for problem in problems], ["placement"])
            self.assertIn("needs-comments/", problems[0].message)
            self.assertFalse(entry.misplaced)

            # (c) flat: a legacy document outside every bucket.
            entry, problems = parse_reflection_document(pending_text, ".concorde/reflections/R-001.md")
            self.assertEqual([problem.code for problem in problems], ["placement"])
            self.assertIn("outside every bucket", problems[0].message)
            self.assertIsNone(entry.bucket)
            self.assertTrue(entry.misplaced)
            self.assertEqual(entry.expected_path, ".concorde/reflections/pending/R-001.md")
            # A flat document that is already triaged is still misplaced (outside every bucket),
            # even though it has no decidable relocation destination.
            entry, problems = parse_reflection_document(filled_text, ".concorde/reflections/R-002.md")
            self.assertEqual([problem.code for problem in problems], ["placement"])
            self.assertTrue(entry.misplaced)
            self.assertIsNone(entry.expected_path)

            # Agreement between content and bucket is never a breach.
            self.assertEqual(parse_reflection_document(pending_text, ".concorde/reflections/pending/R-001.md")[1], ())
            self.assertEqual(parse_reflection_document(filled_text, ".concorde/reflections/needs-comments/R-002.md")[1], ())
            # A filled document may live in either triaged bucket: the bucket alone decides which.
            self.assertEqual(parse_reflection_document(filled_text, ".concorde/reflections/planned/R-002.md")[1], ())

            mixed = parse_reflections(
                {
                    ".concorde/reflections/R-001.md": pending_text,
                    ".concorde/reflections/needs-comments/R-002.md": filled_text,
                },
                '{"schema_version": 1, "high_water": "R-002"}\n',
            )
            self.assertEqual([problem.code for problem in mixed.problems], ["placement"])
            self.assertEqual([entry.identifier for entry in mixed.misplaced()], ["R-001"])
            self.assertEqual(mixed.bucket_counts(), {"pending": 0, "planned": 0, "needs-comments": 1})


if __name__ == "__main__":
    unittest.main()
