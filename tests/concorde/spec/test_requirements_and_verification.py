"""Protocol 6: reader parts, normative definitions, identity and test-declared scenarios."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from tests.concorde.spec.support import (
    DocumentSource,
    module_document,
    write_document,
    source_pairs,
)

from concorde.spec.initialize import protocol_binding
from concorde.distribution.project_defaults import write_protocol_copy
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.validation import validate_repository
from concorde.spec.verification import scan_declarations, verifies

PACKAGE = Path(__file__).resolve().parents[3]

ENTITIES = [
    {
        "id": "entity.shop.cart",
        "title": "Cart",
        "kind": "record",
        "responsibility": "Holds the lines a customer intends to buy.",
        "files": ["src/shop/"],
    },
    {
        "id": "entity.shop.tests",
        "title": "Shop tests",
        "kind": "tests",
        "responsibility": "Exercise the cart.",
        "files": ["tests/shop/"],
    },
]
DIAGRAM = (
    "flowchart TB\n    accTitle: Shop\n    accDescr: The tests exercise the cart.\n"
    '    cart["Cart"]\n    tests["Shop tests"]\n    tests -->|exercise| cart'
)


def reading_entry(requirements, scenarios, extra=""):
    return module_document(
        "document.shop",
        "module.shop",
        "Shop",
        "Shop sells things.",
        scenarios,
        ("Cart and verification.", ENTITIES),
        "The cart holds lines and its tests exercise checkout.",
        DIAGRAM,
        requirements=requirements,
        trailer=extra,
    )


REQUIREMENT = (
    "### req.shop.single-order — One order per submission\n\n"
    "Shop SHALL create at most one order for a successfully\nsubmitted checkout request.\n\n"
    "A retried submission is answered from the existing order.\n"
)
SCENARIO = (
    "### scenario.shop.submit — Successful checkout\n\n- GIVEN a valid cart\n- WHEN it is submitted\n"
    "- THEN one order exists\n- AND the identifier is returned\n\nSee [the rule](#req.shop.single-order).\n"
)


class RequirementsAndVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        configuration = {
            "type_id": "concorde-capability-configuration",
            "schema_version": 1,
            "data": {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
        }
        self.write(
            ".concorde/config.json",
            json.dumps(
                {
                    "profile_version": 14,
                    "registry": ".concorde/specs.json",
                    "protocol": protocol_binding(PACKAGE),
                    "capability_configuration": configuration,
                }
            ),
        )
        write_protocol_copy(self.root, PACKAGE)
        self.write(
            ".concorde/specs.json",
            json.dumps(
                {
                    "schema_version": 5,
                    "project_id": "project.shop",
                    "entry_target": "module.shop",
                    "checks": [],
                    "targets": [
                        {
                            "id": "module.shop",
                            "kind": "module",
                            "title": "Shop",
                            "documents": [
                                "specs/shop/module.md",
                                "specs/shop/notes.md",
                            ],
                            "parent": None,
                            "uses": [],
                            "files": ["src/shop/", "tests/shop/"],
                            "checks": [],
                            "references": [],
                        }
                    ],
                }
            ),
        )
        self.write("src/shop/cart.py", "def total(lines):\n    return sum(lines)\n")
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n"
            "class CartTests:\n    @verifies('scenario.shop.submit')\n    def test_submit(self):\n        pass\n",
        )
        self.write("specs/shop/module.md", reading_entry(REQUIREMENT, SCENARIO))
        self.write(
            "specs/shop/notes.md",
            DocumentSource(
                "# Notes\n\n\nSee [checkout](obligations.md#scenario.shop.submit) and [the cart](module.md#entity.shop.cart).\n",
                {
                    "schema_version": 2,
                    "document": {
                        "id": "document.shop.notes",
                        "owner": "module.shop",
                        "role": "module",
                    },
                    "entities": [],
                    "dependencies": [],
                    "bindings": [],
                },
            ),
        )

    def write(self, path, content):
        write_document(self.root, path, content)

    def validate(self):
        return validate_repository(self.root, package_root=PACKAGE)

    def rules(self, report):
        return {(f.rule_id, f.severity) for f in report.findings}

    @verifies("scenario.spec.validate-success")
    def test_a_requirement_section_is_parsed_with_its_one_shall_statement(self):
        repository = SpecRepository(self.root, PACKAGE)
        target = repository.select("module.shop")
        (requirement,) = repository.requirements(target)
        self.assertEqual(
            ("req.shop.single-order", "One order per submission"),
            (requirement.id, requirement.title),
        )
        self.assertEqual(
            "Shop SHALL create at most one order for a successfully submitted checkout request.",
            requirement.statement,
        )
        (scenario,) = repository.scenarios(target)
        self.assertEqual(4, len(scenario.steps))
        report = self.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))

    def test_a_statement_expresses_exactly_one_behavior(self):
        self.write(
            "specs/shop/module.md",
            reading_entry(
                "### req.shop.double — Two things\n\nShop SHALL create one order and SHALL notify the customer.\n",
                SCENARIO,
            ),
        )
        with self.assertRaisesRegex(SpecError, "exactly once"):
            SpecRepository(self.root, PACKAGE).requirements(
                SpecRepository(self.root, PACKAGE).select("module.shop")
            )
        self.write(
            "specs/shop/module.md",
            reading_entry(
                "### req.shop.none — No statement\n\n- a list instead of a statement\n",
                SCENARIO,
            ),
        )
        with self.assertRaisesRegex(SpecError, "before any list"):
            SpecRepository(self.root, PACKAGE).requirements(
                SpecRepository(self.root, PACKAGE).select("module.shop")
            )
        self.write(
            "specs/shop/module.md",
            reading_entry("### req.shop.empty — Nothing\n", SCENARIO),
        )
        with self.assertRaisesRegex(SpecError, "no statement"):
            SpecRepository(self.root, PACKAGE).requirements(
                SpecRepository(self.root, PACKAGE).select("module.shop")
            )

    def test_requirement_list_items_and_non_step_items_in_scenarios_are_rejected(self):
        self.write(
            "specs/shop/module.md",
            reading_entry(
                "- req.shop.old: Shop SHALL not use the old form.\n", SCENARIO
            ),
        )
        with self.assertRaisesRegex(SpecError, "not a list item"):
            SpecRepository(self.root, PACKAGE).scenarios(
                SpecRepository(self.root, PACKAGE).select("module.shop")
            )
        self.write(
            "specs/shop/module.md",
            reading_entry(
                REQUIREMENT,
                SCENARIO.replace(
                    "- AND the identifier is returned", "- the identifier is returned"
                ),
            ),
        )
        with self.assertRaisesRegex(SpecError, "not a GIVEN/WHEN/THEN"):
            SpecRepository(self.root, PACKAGE).scenarios(
                SpecRepository(self.root, PACKAGE).select("module.shop")
            )

    @verifies("scenario.spec.validate-structural-errors")
    def test_the_reading_entry_requires_the_four_reading_sections(self):
        text = (self.root / "specs/shop/module.md").read_text()
        for heading in ("## Purpose", "## Usage", "## Design", "## Relationships"):
            with self.subTest(heading=heading):
                self.write(
                    "specs/shop/module.md", text.replace(heading, "## Missing section")
                )
                self.assertIn(
                    ("CONCORDE-MODULE-001", "error"), self.rules(self.validate())
                )
        self.write(
            "specs/shop/module.md",
            text.replace("## Relationships", "### Relationships"),
        )
        self.assertIn(("CONCORDE-MODULE-001", "error"), self.rules(self.validate()))

    @verifies("scenario.spec.reader-parts-invalid")
    def test_reading_structure_rejects_legacy_duplicates_wrong_levels_and_empty_explanations(
        self,
    ):
        text = str(reading_entry(REQUIREMENT, SCENARIO))
        cases = [
            text.replace("## Usage", "## Usage & Contract"),
            text.replace("## Design", "## Architecture & Realization"),
            text + "\n## Purpose\n\nDuplicate.\n",
            text + "\n## Entities\n\nInventory chapter.\n",
            text.replace("## Usage", "### Usage"),
            text.replace("## Design", "#### Design"),
            text.replace("## Purpose", "## Purpose\n\n### Nested title"),
            text.replace(
                "Use the declared boundary for the cases below; rejected input has no implicit retry.",
                "",
            ),
            text.replace("The cart holds lines and its tests exercise checkout.", "")
            .replace("Holds the lines a customer intends to buy.", "")
            .replace("Exercise the cart.", ""),
            text.replace("## Usage", "~~~~markdown\n## Usage\n~~~~"),
            text + "\n```concorde-entities\n[]\n```\n",
            re.sub(r"(```mermaid\n[\s\S]*?\n```)", r"~~~~markdown\n\1\n~~~~", text),
            text.replace("## Purpose", "## Premature detail\n\nExtra.\n\n## Purpose"),
        ]
        for index, invalid in enumerate(cases):
            with self.subTest(case=index):
                self.write("specs/shop/module.md", invalid)
                self.assertIn(
                    ("CONCORDE-MODULE-001", "error"), self.rules(self.validate())
                )

    @verifies("scenario.spec.reader-parts")
    def test_closed_atx_headings_and_no_final_newline_are_valid(self):
        text = (
            reading_entry(REQUIREMENT, SCENARIO)
            .replace("## Purpose\n", "## Purpose ##\n")
            .rstrip()
        )
        self.write("specs/shop/module.md", text)
        self.assertEqual("success", self.validate().status)

    @verifies("scenario.spec.reader-parts", "scenario.spec.reader-parts-invalid")
    def test_companions_use_topic_reading_without_an_entry_template(self):
        for body in (
            "Consumer notes.",
            "## Design\n\nInternal notes.",
            "## Use\n\nConsumer notes.\n\n## Implementation\n\nInternal notes.",
        ):
            with self.subTest(body=body):
                self.write("specs/shop/notes.md", "# Notes\n\n" + body)
                self.assertEqual("success", self.validate().status)
        for body in (
            "",
            "# Notes\n\n## Usage & Contract\n\nRetired.",
            "# Notes\n\n```concorde-document\n{}\n```",
        ):
            with self.subTest(body=body):
                self.write("specs/shop/notes.md", body)
                self.assertIn(
                    ("CONCORDE-MODULE-001", "error"), self.rules(self.validate())
                )

    @verifies("scenario.spec.internal-contract-context")
    def test_internal_definitions_keep_owner_full_context_and_verification_identity(
        self,
    ):
        internal = (
            "\n### Internal constraints and verification\n\n"
            "#### req.shop.lock — Serialize order persistence\n\n"
            "Shop SHALL hold its lock during order persistence.\n\n"
            "#### scenario.shop.lock — Persistence holds the lock\n\n"
            "- GIVEN a valid order\n- WHEN persistence writes it\n- THEN the lock is held\n"
        )
        self.write(
            "specs/shop/module.md", reading_entry(REQUIREMENT, SCENARIO, internal)
        )
        self.write(
            "tests/shop/test_lock.py",
            "from concorde.spec.verification import verifies\n"
            "@verifies('scenario.shop.lock')\ndef test_lock():\n    pass\n",
        )
        repository = SpecRepository(self.root, PACKAGE)
        target = repository.select("module.shop")
        self.assertEqual(
            {"req.shop.single-order", "req.shop.lock"},
            {r.id for r in repository.requirements(target)},
        )
        scenario = next(
            s for s in repository.scenarios(target) if s.id == "scenario.shop.lock"
        )
        self.assertEqual("module.shop", scenario.owner)
        resolution = repository.spec_context(scenario.id)
        self.assertEqual(
            repository.spec_files(target.id), repository.spec_files(scenario.id)
        )
        self.assertEqual(6, len(resolution.sources))
        self.assertEqual(1, len(repository.scenario_verifications(target)[scenario.id]))
        self.assertEqual("success", self.validate().status)
        self.assertIn("## Usage", repository.document("specs/shop/module.md").body)
        self.assertIn("## Design", repository.document("specs/shop/module.md").body)

    @verifies("scenario.spec.link-anchors")
    def test_links_with_id_fragments_must_reach_the_defining_document(self):
        self.write(
            "specs/shop/notes.md",
            "# Notes\n\n[wrong document](#scenario.shop.submit) and "
            "[unknown](module.md#req.shop.missing) and [plain heading](module.md#purpose).\n",
        )
        report = self.validate()
        messages = [
            f.message for f in report.findings if f.rule_id == "CONCORDE-LINK-001"
        ]
        self.assertEqual(2, len(messages), messages)
        self.assertTrue(
            any("defined in specs/shop/obligations.md" in m for m in messages)
        )
        self.assertTrue(any("names no scenario" in m for m in messages))

    @verifies("scenario.spec.verification-declarations")
    def test_tests_declare_the_scenarios_they_verify_and_coverage_is_reported(self):
        declarations = scan_declarations(
            self.root, ["tests/shop/test_cart.py", "src/shop/cart.py"]
        )
        self.assertEqual(
            [
                (
                    "scenario.shop.submit",
                    "tests/shop/test_cart.py",
                    "CartTests.test_submit",
                )
            ],
            [(d.scenario_id, d.path, d.name) for d in declarations],
        )
        repository = SpecRepository(self.root, PACKAGE)
        self.assertEqual(
            {"scenario.shop.submit": 1},
            {
                k: len(v)
                for k, v in repository.scenario_verifications(
                    repository.select("module.shop")
                ).items()
            },
        )
        self.write("tests/shop/test_cart.py", "def test_nothing():\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))
        self.assertEqual("success", report.status)
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n@verifies('scenario.shop.unknown')\ndef test_x():\n    pass\n",
        )
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-001", "error"), self.rules(report))
        self.write("tests/shop/test_cart.py", "def broken(:\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-004", "error"), self.rules(report))
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n@verifies(name)\ndef test_x():\n    pass\n",
        )
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-004", "error"), self.rules(report))

    def test_the_decorator_records_scenarios_and_returns_the_function(self):
        @verifies("scenario.shop.submit", "scenario.shop.other")
        def probe():
            return 1

        self.assertEqual(
            ("scenario.shop.submit", "scenario.shop.other"),
            getattr(probe, "concorde_scenarios"),
        )
        self.assertEqual(1, probe())
        with self.assertRaises(ValueError):
            verifies("req.shop.single-order")

    @verifies("scenario.spec.verification-declarations")
    def test_typescript_tests_declare_their_scenarios_in_a_comment_above_the_test(self):
        self.write(
            "tests/shop/cart.test.ts",
            "describe('cart', () => {\n"
            "  // verifies: scenario.shop.submit scenario.shop.other\n"
            "  it('submits once', () => {});\n"
            "  // verifies: scenario.shop.lock\n"
            "  it.each([\n    ['empty', 0],\n  ])(\n"
            "    'rejects %s carts',\n    (label, total) => {},\n  );\n"
            "  it('carries no declaration', () => {});\n"
            "});\n",
        )
        declarations = scan_declarations(self.root, ["tests/shop/cart.test.ts"])
        self.assertEqual(
            [
                ("scenario.shop.submit", 2, "submits once"),
                ("scenario.shop.other", 2, "submits once"),
                ("scenario.shop.lock", 4, "rejects %s carts"),
            ],
            [(d.scenario_id, d.line, d.name) for d in declarations],
        )
        report = self.validate()
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))
        self.assertIn(("CONCORDE-VERIFICATION-001", "error"), self.rules(report))
        self.write(
            "tests/shop/cart.test.ts",
            "// verifies: scenario.shop.submit\nconst unused = 1;\n",
        )
        self.assertIn(
            ("CONCORDE-VERIFICATION-004", "error"), self.rules(self.validate())
        )
        self.write(
            "tests/shop/cart.test.ts",
            "// verifies: req.shop.single-order\nit('x', () => {});\n",
        )
        self.assertIn(
            ("CONCORDE-VERIFICATION-004", "error"), self.rules(self.validate())
        )

    @verifies("scenario.spec.verification-declarations")
    def test_a_module_binding_no_implementation_entry_reports_no_uncovered_scenario(
        self,
    ):
        self.write("tests/shop/test_cart.py", "def test_nothing():\n    pass\n")
        self.assertIn(
            ("CONCORDE-VERIFICATION-002", "warning"), self.rules(self.validate())
        )
        registry = json.loads((self.root / ".concorde/specs.json").read_text())
        registry["targets"][0]["files"] = []
        (self.root / ".concorde/specs.json").write_text(json.dumps(registry))
        metadata = json.loads((self.root / "specs/shop/module.md.json").read_text())
        for entity in metadata["entities"]:
            entity.pop("files", None)
        (self.root / "specs/shop/module.md.json").write_text(json.dumps(metadata))
        report = self.validate()
        self.assertEqual("success", report.status)
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))

    @verifies("scenario.spec.verification-declarations")
    def test_a_declaration_in_a_file_the_module_does_not_list_is_a_warning(self):
        registry = json.loads((self.root / ".concorde/specs.json").read_text())
        registry["targets"].append(
            {
                "id": "module.other",
                "kind": "module",
                "title": "Other",
                "documents": ["specs/other/module.md"],
                "parent": None,
                "uses": [],
                "files": ["tests/other/"],
                "checks": [],
                "references": [],
            }
        )
        registry["targets"][0]["files"] = ["src/shop/"]
        (self.root / ".concorde/specs.json").write_text(json.dumps(registry))
        self.write(
            "specs/other/module.md",
            module_document(
                "document.other",
                "module.other",
                "Other",
                "Other tests exercise the shop.",
                "No local scenarios.",
                (
                    "Verification program.",
                    [
                        {
                            "id": "entity.other.tests",
                            "title": "Other tests",
                            "kind": "tests",
                            "responsibility": "Exercise the shop from outside.",
                            "files": ["tests/other/"],
                        }
                    ],
                ),
                "The tests exercise the shop boundary.",
                'flowchart TB\n    tests["Other tests"]',
            ),
        )
        metadata = json.loads((self.root / "specs/shop/module.md.json").read_text())
        metadata["entities"][1].pop("files")
        (self.root / "specs/shop/module.md.json").write_text(json.dumps(metadata))
        self.write(
            "tests/other/test_shop.py",
            "from concorde.spec.verification import verifies\n"
            '@verifies("scenario.shop.submit")\ndef test_x():\n    pass\n',
        )
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-003", "warning"), self.rules(report))
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))


if __name__ == "__main__":
    unittest.main()
