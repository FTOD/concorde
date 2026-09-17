"""Repository reading regressions, not a keyword-based terminology language rule."""

from __future__ import annotations

import copy
import json
import posixpath
import re
import unittest
from pathlib import Path

from concorde.spec.repository import SpecRepository
from concorde.spec.repository_base import walk_lines
from concorde.spec.validation import terminology_findings
from concorde.spec.verification import verifies

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "specs/concorde/"
LINK = re.compile(r"\[([^\]]+)\]\(([^\s)]+)\)")


def terminology_rows(text: str) -> dict[str, str | None]:
    """Only the first contiguous Term table, never later field tables or fences."""
    active = False
    table = False
    rows = {}
    for _, kind, line in walk_lines(text):
        if kind != "prose":
            continue
        if line == "## Terminology":
            active = True
            continue
        if not active:
            continue
        if line.startswith("#"):
            break
        if line.strip() == "| Term | Meaning / definition |":
            table = True
            continue
        if not table:
            continue
        if not line.startswith("|"):
            break
        cell = line.strip("|").split("|")[0].strip()
        if re.fullmatch(r":?-{3,}:?", cell):
            continue
        match = LINK.fullmatch(cell)
        term, href = match.groups() if match else (cell, None)
        if term in rows:
            raise AssertionError(f"Duplicate terminology row: {term}")
        rows[term] = href
    return rows


def destination(source: str, href: str) -> str:
    path, fragment = href.split("#")
    if fragment != "terminology":
        raise AssertionError(f"Not a direct terminology-table link: {href}")
    return posixpath.normpath(posixpath.join(posixpath.dirname(source), path))


class TerminologyReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / ".concorde/specs.json").read_text())
        cls.repository = SpecRepository(ROOT)
        cls.pages = {
            path: (ROOT / path).read_text()
            for module in cls.registry["targets"]
            for path in module["documents"]
        }
        cls.tables = {path: terminology_rows(body) for path, body in cls.pages.items()}

    def test_table_reader_ignores_fenced_examples_and_later_field_tables(self):
        text = """# Example
```markdown
## Terminology
| Term | Meaning / definition |
| --- | --- |
| Fake | Not a definition. |
```
## Terminology
| Term | Meaning / definition |
| --- | --- |
| Real | The actual definition. |

### Fields
| Field | Type |
| --- | --- |
| field | string |
"""
        self.assertEqual({"Real": None}, terminology_rows(text))

    @verifies("scenario.spec.reader-parts")
    def test_all_registered_roles_have_page_specific_orientation(self):
        roles = set()
        for path, text in self.pages.items():
            with self.subTest(path=path):
                roles.add(
                    json.loads((ROOT / (path + ".json")).read_text())["document"][
                        "role"
                    ]
                )
                self.assertIn("## Terminology", text)
                self.assertTrue(
                    self.tables[path] or "No specialized terminology." in text
                )
        self.assertEqual({"module", "implementation"}, roles)

    @verifies("scenario.spec.reference-invalid")
    def test_imports_reach_unique_definitions_not_forwarding_tables(self):
        canonical = {}
        for path, rows in self.tables.items():
            for term, href in rows.items():
                if href is None:
                    self.assertNotIn(term, canonical, f"Duplicate definition: {term}")
                    canonical[term] = path
        for path, rows in self.tables.items():
            for term, href in rows.items():
                if href is not None:
                    with self.subTest(path=path, term=term):
                        self.assertEqual(canonical[term], destination(path, href))

    @verifies("scenario.spec.reference-resolution")
    def test_every_selected_context_contains_definitions_for_included_reading(self):
        # Also check imported provider pages: their references do NOT expand for a consumer.
        for module in self.registry["targets"]:
            sources = set(self.repository.spec_files(module["id"]))
            for path in sources.intersection(self.pages):
                self.assertIn(path + ".json", sources)
                for term, href in self.tables[path].items():
                    if href is not None:
                        with self.subTest(module=module["id"], page=path, term=term):
                            self.assertIn(destination(path, href), sources)

    def test_removing_direct_reference_is_not_repaired_by_links_or_provider_references(
        self,
    ):
        registry = copy.deepcopy(self.registry)
        review = next(m for m in registry["targets"] if m["id"] == "module.review")
        defining_id = json.loads(
            (ROOT / (PREFIX + "issues/lifecycle.md.json")).read_text()
        )["document"]["id"]
        review["references"] = [
            r for r in review["references"] if r.get("id") != defining_id
        ]
        repository = SpecRepository(ROOT, registry_bytes=json.dumps(registry).encode())
        sources = repository.spec_files("module.review")
        self.assertIn(PREFIX + "issues/module.md", sources)
        self.assertNotIn(PREFIX + "issues/lifecycle.md", sources)
        self.assertTrue(
            any(
                f.rule_id == "CONCORDE-TERMINOLOGY-001"
                for f in terminology_findings(repository)
            )
        )

    def test_semantically_selected_reader_dependencies_have_definition_entries(self):
        # These are editorial cases, not a rule that every matching word needs a link.
        required = {
            "development/review-and-gaps.md": {"Issue", "Blocker", "Evidence"},
            "harness/graphs-and-loops.md": {"Flow"},
            "harness/host.md": {"Host", "Flow", "Skill"},
            "harness/module.md": {
                "Spec context",
                "Implementation context",
                "Capability context",
                "Task context",
            },
            "harness/execution.md": {"Issue", "Tool gate"},
            "harness/contracts.md": {
                "Spec context",
                "Implementation context",
                "Capability context",
                "Task context",
                "Capsule",
                "Issue",
                "Blocker",
            },
            "spec/module.md": {"Protocol binding"},
            "spec/contracts.md": {
                "Document unit",
                "Document role",
                "Source-member role",
            },
            "views/publication.md": {
                "Document role",
                "Promotion",
                "Publication candidate",
            },
            "views/contracts.md": {
                "Document role",
                "Promotion",
                "Publication candidate",
            },
            "views/ua-graph.md": {"Implementation context"},
            "planning/module.md": {
                "Acceptance task",
                "Spec context",
                "Reserved task ID",
            },
            "implementation/requirements.md": {"Acceptance task"},
            "issues/module.md": {"Disposition"},
            "issues/requirements.md": {"Disposition", "Ready"},
            "distribution/module.md": {"Protocol binding"},
            "distribution/build.md": {"Public capability", "Skill"},
            "spec-authoring/module.md": {
                "Module Specs",
                "Implementation Specs",
                "Ownership",
            },
            "review/review-result.md": {
                "Issue",
                "Blocker",
                "Disposition",
                "Review coverage",
            },
            "validation/module.md": {"Structural validation", "Semantic completeness"},
            "delivery/execution-reference.md": {
                "Delivery receipt",
                "Delivered branch",
                "Evidence",
            },
            "query-routing/module.md": {"Spec context"},
            "topology/module.md": {
                "Ownership",
                "Composition",
                "Reference",
                "Implementation binding",
            },
            "dev-loop/execution-reference.md": {
                "Spec context",
                "Acceptance task",
                "Reserved task ID",
            },
            "specify-loop/module.md": {"Blocker", "Ready"},
        }
        for path, terms in required.items():
            with self.subTest(path=path):
                self.assertLessEqual(terms, self.tables[PREFIX + path].keys())

    def test_unrelated_template_rows_do_not_return(self):
        forbidden = {
            "development/review-and-gaps.md": {
                "Capability",
                "Host",
                "Flow",
                "Candidate",
            },
            "harness/graphs-and-loops.md": {"Harness", "Context", "Grant", "Snapshot"},
            "implementation/requirements.md": {"Spec", "Worker", "Candidate", "Grant"},
            "views/viewer.md": {"Module Specs", "Implementation Specs", "Registry"},
        }
        for path, terms in forbidden.items():
            with self.subTest(path=path):
                self.assertFalse(terms.intersection(self.tables[PREFIX + path]))
        for path in self.pages:
            if path.startswith(PREFIX + "views/"):
                self.assertNotIn("Candidate", self.tables[path])

    def test_problem_definitions_and_module_navigation_are_distinct(self):
        path = PREFIX + "development/review-and-gaps.md"
        for term in ("Issue", "Blocker"):
            self.assertEqual("../concepts.md#terminology", self.tables[path][term])
        self.assertIn("[Issues Module](../issues/module.md)", self.pages[path])
        self.assertIn(
            "[Issues Module](../issues/module.md)",
            self.pages[PREFIX + "harness/execution.md"],
        )
        self.assertNotIn(
            "admitted [Spec Module]", self.pages[PREFIX + "planning/scenarios.md"]
        )
        self.assertIn(
            "execution profile and Harness under read-only permissions",
            self.pages[PREFIX + "review/execution-reference.md"],
        )
        self.assertIn(
            "both document roles and metadata",
            self.pages[PREFIX + "query-routing/module.md"],
        )

    def test_orientation_precedes_interface_fields_and_examples(self):
        markers = {
            "issues/interfaces.md": "| Action |",
            "review/review-result.md": "| Field |",
            "views/viewer.md": "```bash",
            "views/ua-graph.md": "```bash",
        }
        for path, marker in markers.items():
            text = self.pages[PREFIX + path]
            with self.subTest(path=path):
                self.assertLess(text.index("## Terminology"), text.index(marker))


if __name__ == "__main__":
    unittest.main()
