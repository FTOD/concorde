"""Requirements, scenarios and the scenario coverage tests declare, on a one-Module project."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import scan_declarations, verifies
from tests.concorde.spec.support import (
    DocumentSource,
    SpecProject,
    module_document,
    register_module,
    write_document,
)

NODES = [
    {
        "id": "realization.shop.cart",
        "type": "realization",
        "title": "Cart",
        "meaning": "Holds the lines a customer intends to buy.",
        "entries": ["src/shop/"],
    },
    {
        "id": "realization.shop.tests",
        "type": "realization",
        "title": "Shop tests",
        "meaning": "Exercise the cart.",
        "entries": ["tests/shop/"],
    },
]
RELATES = [
    {
        "type": "relates",
        "source": "realization.shop.tests",
        "verb": "exercise",
        "target": "realization.shop.cart",
    }
]
DIAGRAM = (
    "flowchart TB\n    accTitle: Shop\n    accDescr: The tests exercise the cart.\n"
    '    cart["Cart"]\n    tests["Shop tests"]\n    tests -->|exercise| cart'
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


def shop(requirements=REQUIREMENT, scenarios=SCENARIO, extra="", nodes=NODES):
    both = len(nodes) == 2
    diagram = DIAGRAM if both else 'flowchart TB\n    cart["Cart"]' if nodes else None
    return module_document(
        "document.shop",
        "module.shop",
        "Shop",
        "Shop sells things.",
        scenarios,
        ("Cart and verification.", nodes),
        "The cart holds lines and its tests exercise checkout.",
        diagram,
        requirements=requirements,
        trailer=extra,
        relations=RELATES if both else (),
        extra_owned=("notes.md",),
    )


NOTES = DocumentSource(
    "# Notes\n\nSee [checkout](obligations.md#scenario.shop.submit) and "
    "[the cart](module.md#realization.shop.cart).\n",
    {
        "schema_version": 3,
        "document": {
            "id": "document.shop.notes",
            "owner": "module.shop",
            "role": "module",
        },
        "defines": [],
        "relations": [],
    },
)


class RequirementsAndVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = SpecProject(self.root)
        self.write("src/shop/cart.py", "def total(lines):\n    return sum(lines)\n")
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n"
            "class CartTests:\n    @verifies('scenario.shop.submit')\n    def test_submit(self):\n        pass\n",
        )
        self.write("specs/shop/notes.md", NOTES)
        self.project.module("module.shop", "specs/shop/module.md", shop())

    def write(self, path, content):
        write_document(self.root, path, content)

    def rules(self, severity="error"):
        return self.project.rules(severity)

    @verifies("scenario.spec.validate-success")
    def test_a_requirement_section_is_parsed_with_its_one_shall_statement(self):
        repository = self.project.repository()
        target = repository.module("module.shop")
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
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertNotIn("CONCORDE-COVERAGE-001", self.rules("warning"))

    @verifies("scenario.spec.node-checks")
    def test_a_requirement_statement_is_one_sentence_with_one_shall(self):
        for requirements in (
            "### req.shop.double — Two things\n\nShop SHALL create one order and SHALL notify.\n",
            "### req.shop.two — Two sentences\n\nShop SHALL create one order. It notifies.\n",
            "### req.shop.none — No statement\n\n- a list instead of a statement\n",
            "### req.shop.empty — Nothing\n",
            "- req.shop.old: Shop SHALL not use the old form.\n",
            "### req.shop.nested — Nested\n\nShop SHALL nest.\n\n#### Detail\n\nMore.\n",
        ):
            with self.subTest(requirements=requirements):
                self.write("specs/shop/module.md", shop(requirements=requirements))
                self.assertIn("CHK.requirement.statement", self.rules())

    @verifies("scenario.spec.node-checks")
    def test_scenario_steps_follow_the_grammar(self):
        for replacement in (
            ("- AND the identifier is returned", "- the identifier is returned"),
            ("- GIVEN a valid cart\n", "- AND a valid cart\n"),
            ("- THEN one order exists\n", "- THEN one order exists\n- GIVEN again\n"),
            ("- THEN one order exists\n- AND the identifier is returned\n", ""),
        ):
            with self.subTest(replacement=replacement):
                self.write(
                    "specs/shop/module.md",
                    shop(scenarios=SCENARIO.replace(*replacement)),
                )
                self.assertIn("CHK.scenario.steps", self.rules())

    @verifies("scenario.spec.document-roles")
    def test_precise_definitions_belong_to_implementation_documents(self):
        path = self.root / "specs/shop/notes.md"
        path.write_text(
            path.read_text()
            + "\n## Extra\n\n"
            + REQUIREMENT.replace("single-order", "notes")
        )
        self.assertIn("CHK.defines.role", self.rules())
        path.write_text(NOTES)
        metadata = self.project.metadata("specs/shop/notes.md")
        metadata["document"]["role"] = "topic"
        self.project.save_metadata("specs/shop/notes.md", metadata)
        self.assertIn("CHK.document.role", self.rules())

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
        repository = self.project.repository()
        self.assertEqual(
            {"scenario.shop.submit": 1},
            {
                k: len(v)
                for k, v in repository.coverage(
                    repository.module("module.shop")
                ).items()
            },
        )
        self.assertEqual(1, len(repository.covered_by("scenario.shop.submit")))
        self.write("tests/shop/test_cart.py", "def test_nothing():\n    pass\n")
        self.assertIn("CONCORDE-COVERAGE-001", self.rules("warning"))
        self.assertEqual("success", self.project.validate().status)
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n@verifies('scenario.shop.unknown')\ndef test_x():\n    pass\n",
        )
        self.assertIn("CHK.verifies.resolves", self.rules())
        self.write("tests/shop/test_cart.py", "def broken(:\n    pass\n")
        self.assertIn("CONCORDE-COVERAGE-003", self.rules())
        self.write(
            "tests/shop/test_cart.py",
            "from concorde.spec.verification import verifies\n\n@verifies(name)\ndef test_x():\n    pass\n",
        )
        self.assertIn("CONCORDE-COVERAGE-003", self.rules())

    @verifies("scenario.spec.verification-declarations")
    def test_reading_never_carries_test_declarations(self):
        path = self.root / "specs/shop/notes.md"
        path.write_text(
            path.read_text() + '\nThe test uses @verifies("scenario.shop.submit").\n'
        )
        self.assertIn("CHK.evidence.no-spec-coverage", self.rules())
        path.write_text(
            str(NOTES)
            + '\n```python\n@verifies("scenario.shop.submit")\ndef test(): ...\n```\n'
        )
        self.assertNotIn("CHK.evidence.no-spec-coverage", self.rules())

    def test_the_decorator_records_scenarios_and_returns_the_function(self):
        @verifies("scenario.shop.submit", "scenario.shop.other")
        def probe():
            return 1

        self.assertEqual(
            ("scenario.shop.submit", "scenario.shop.other"),
            getattr(probe, "concorde_scenarios"),  # noqa: B009 - decorator-added metadata
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
        self.assertIn("CHK.verifies.resolves", self.rules())
        self.write(
            "tests/shop/cart.test.ts",
            "// verifies: scenario.shop.submit\nconst unused = 1;\n",
        )
        self.assertIn("CONCORDE-COVERAGE-003", self.rules())

    @verifies("scenario.spec.verification-declarations")
    def test_a_module_binding_nothing_reports_no_uncovered_scenario(self):
        self.write("tests/shop/test_cart.py", "def test_nothing():\n    pass\n")
        self.assertIn("CONCORDE-COVERAGE-001", self.rules("warning"))
        self.write("specs/shop/module.md", shop(nodes=[]))
        (self.root / "specs/shop/notes.md").write_text(
            "# Notes\n\nNothing is bound yet.\n"
        )
        report = self.project.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertNotIn("CONCORDE-COVERAGE-001", self.rules("warning"))

    @verifies("scenario.spec.verification-declarations")
    def test_a_declaration_in_a_file_the_owner_does_not_bind_is_a_warning(self):
        self.write(
            "specs/other/module.md",
            module_document(
                "document.other",
                "module.other",
                "Other",
                "Other tests exercise the shop.",
                "",
                (
                    "Verification program.",
                    [
                        {
                            "id": "realization.other.tests",
                            "type": "realization",
                            "title": "Other tests",
                            "meaning": "Exercise the shop from outside.",
                            "entries": ["tests/other/"],
                        }
                    ],
                ),
                "The tests exercise the shop boundary.",
                'flowchart TB\n    tests["Other tests"]',
            ),
        )
        register_module(self.root, "module.other", "specs/other/module.md")
        self.write("specs/shop/module.md", shop(nodes=NODES[:1]))
        self.write(
            "tests/other/test_shop.py",
            "from concorde.spec.verification import verifies\n"
            '@verifies("scenario.shop.submit")\ndef test_x():\n    pass\n',
        )
        (self.root / "tests/shop/test_cart.py").unlink()
        (self.root / "tests/shop").rmdir()
        report = self.project.validate()
        self.assertEqual(
            "success",
            report.status,
            [f.message for f in report.findings if f.severity == "error"],
        )
        self.assertIn("CONCORDE-COVERAGE-002", self.rules("warning"))
        self.assertNotIn("CONCORDE-COVERAGE-001", self.rules("warning"))


if __name__ == "__main__":
    unittest.main()
