"""Protocol 4: Module-level requirement sections, ID anchors in links and test-declared scenarios."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from concorde.spec.initialize import protocol_binding
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.validation import validate_repository
from concorde.spec.verification import scan_declarations, verifies

PACKAGE = Path(__file__).resolve().parents[3]

ENTITIES = [{"id": "entity.shop.cart", "title": "Cart", "kind": "record",
             "responsibility": "Holds the lines a customer intends to buy.", "files": ["src/shop/"]},
            {"id": "entity.shop.tests", "title": "Shop tests", "kind": "tests",
             "responsibility": "Exercise the cart.", "files": ["tests/shop/"]}]
DIAGRAM = ('flowchart TB\n    accTitle: Shop\n    accDescr: The tests exercise the cart.\n'
           '    cart["Cart"]\n    tests["Shop tests"]\n    tests -->|exercise| cart')


def reading_entry(requirements, scenarios, extra=""):
    declaration = {"id": "document.shop", "owner": "module.shop", "main_visible": True}
    return ("```concorde-document\n" + json.dumps(declaration) + "\n```\n\n# Shop\n\n## Purpose\n\n"
            "Shop sells things.\n\n## Requirements\n\n" + requirements + "\n\n## Scenarios\n\n" + scenarios
            + "\n\n## Ontology\n\n### Entities\n\n```concorde-entities\n" + json.dumps(ENTITIES)
            + "\n```\n\n### Relationships\n\n```mermaid\n" + DIAGRAM + "\n```\n" + extra)


REQUIREMENT = ("### req.shop.single-order — One order per submission\n\n"
               "Shop SHALL create at most one order for a successfully\nsubmitted checkout request.\n\n"
               "A retried submission is answered from the existing order.\n")
SCENARIO = ("### scenario.shop.submit — Successful checkout\n\n- GIVEN a valid cart\n- WHEN it is submitted\n"
            "- THEN one order exists\n- AND the identifier is returned\n\nSee [the rule](#req.shop.single-order).\n")


class RequirementsAndVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        configuration = {"type_id": "concorde-capability-configuration", "schema_version": 1,
                         "data": {"integration": "claude", "enforcement": "native"}}
        self.write(".concorde/config.json", json.dumps({"profile_version": 12, "registry": ".concorde/specs.json",
            "protocol": protocol_binding(PACKAGE), "capability_configuration": configuration}))
        self.write(".concorde/specs.json", json.dumps({"schema_version": 4, "project_id": "project.shop",
            "entry_target": "module.shop", "checks": [], "targets": [
                {"id": "module.shop", "kind": "module", "title": "Shop", "documents": ["specs/shop/module.md", "specs/shop/notes.md"],
                 "parent": None, "uses": [], "files": ["src/shop/", "tests/shop/"], "checks": [], "references": []}]}))
        self.write("src/shop/cart.py", "def total(lines):\n    return sum(lines)\n")
        self.write("tests/shop/test_cart.py",
                   "from concorde.spec.verification import verifies\n\n"
                   "class CartTests:\n    @verifies('scenario.shop.submit')\n    def test_submit(self):\n        pass\n")
        self.write("specs/shop/module.md", reading_entry(REQUIREMENT, SCENARIO))
        self.write("specs/shop/notes.md", "```concorde-document\n" + json.dumps(
            {"id": "document.shop.notes", "owner": "module.shop", "main_visible": False})
            + "\n```\n\n# Notes\n\nSee [checkout](module.md#scenario.shop.submit) and [the cart](module.md#entity.shop.cart).\n")

    def write(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    def validate(self):
        return validate_repository(self.root, package_root=PACKAGE)

    def rules(self, report):
        return {(f.rule_id, f.severity) for f in report.findings}

    @verifies("scenario.spec.validate-success")
    def test_a_requirement_section_is_parsed_with_its_one_shall_statement(self):
        repository = SpecRepository(self.root, PACKAGE)
        target = repository.select("module.shop")
        (requirement,) = repository.requirements(target)
        self.assertEqual(("req.shop.single-order", "One order per submission"), (requirement.id, requirement.title))
        self.assertEqual("Shop SHALL create at most one order for a successfully submitted checkout request.",
                         requirement.statement)
        (scenario,) = repository.scenarios(target)
        self.assertEqual(4, len(scenario.steps))
        report = self.validate()
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))

    def test_a_statement_expresses_exactly_one_behavior(self):
        self.write("specs/shop/module.md", reading_entry(
            "### req.shop.double — Two things\n\nShop SHALL create one order and SHALL notify the customer.\n", SCENARIO))
        with self.assertRaisesRegex(SpecError, "exactly once"):
            SpecRepository(self.root, PACKAGE).requirements(SpecRepository(self.root, PACKAGE).select("module.shop"))
        self.write("specs/shop/module.md", reading_entry(
            "### req.shop.none — No statement\n\n- a list instead of a statement\n", SCENARIO))
        with self.assertRaisesRegex(SpecError, "before any list"):
            SpecRepository(self.root, PACKAGE).requirements(SpecRepository(self.root, PACKAGE).select("module.shop"))
        self.write("specs/shop/module.md", reading_entry("### req.shop.empty — Nothing\n", SCENARIO))
        with self.assertRaisesRegex(SpecError, "no statement"):
            SpecRepository(self.root, PACKAGE).requirements(SpecRepository(self.root, PACKAGE).select("module.shop"))

    def test_requirement_list_items_and_non_step_items_in_scenarios_are_rejected(self):
        self.write("specs/shop/module.md", reading_entry(
            "- req.shop.old: Shop SHALL not use the old form.\n", SCENARIO))
        with self.assertRaisesRegex(SpecError, "not a list item"):
            SpecRepository(self.root, PACKAGE).scenarios(SpecRepository(self.root, PACKAGE).select("module.shop"))
        self.write("specs/shop/module.md", reading_entry(REQUIREMENT, SCENARIO.replace(
            "- AND the identifier is returned", "- the identifier is returned")))
        with self.assertRaisesRegex(SpecError, "not a GIVEN/WHEN/THEN"):
            SpecRepository(self.root, PACKAGE).scenarios(SpecRepository(self.root, PACKAGE).select("module.shop"))

    @verifies("scenario.spec.validate-structural-errors")
    def test_the_reading_entry_needs_requirements_and_an_ontology_with_both_subsections(self):
        text = (self.root / "specs/shop/module.md").read_text()
        cases = {
            "## Requirements": "Purpose, Requirements, Scenarios and Ontology",
            "### Entities": "Entities and Relationships",
            "### Relationships": "Entities and Relationships",
        }
        for heading, expected in cases.items():
            with self.subTest(heading=heading):
                self.write("specs/shop/module.md", text.replace(heading, heading.replace("R", "X").replace("E", "X")))
                report = self.validate()
                self.assertIn(("CONCORDE-MODULE-001", "error"), self.rules(report))
                self.assertTrue(any(expected in f.message for f in report.findings), [f.message for f in report.findings])
        self.write("specs/shop/module.md", text.replace("### Relationships", "## Relationships"))
        report = self.validate()
        self.assertTrue(any("below the Ontology heading" in f.message for f in report.findings))
        self.write("specs/shop/module.md", text.replace("### Entities", "### Relationships").replace(
            "### Relationships\n\n```mermaid", "### Entities\n\n```mermaid"))
        report = self.validate()
        self.assertIn(("CONCORDE-MODULE-001", "error"), self.rules(report))

    @verifies("scenario.spec.link-anchors")
    def test_links_with_id_fragments_must_reach_the_defining_document(self):
        self.write("specs/shop/notes.md", "```concorde-document\n" + json.dumps(
            {"id": "document.shop.notes", "owner": "module.shop", "main_visible": False})
            + "\n```\n\n# Notes\n\n[wrong document](#scenario.shop.submit) and [unknown](module.md#req.shop.missing)\n"
              "and [plain heading](module.md#purpose).\n")
        report = self.validate()
        messages = [f.message for f in report.findings if f.rule_id == "CONCORDE-LINK-001"]
        self.assertEqual(2, len(messages), messages)
        self.assertTrue(any("defined in specs/shop/module.md" in m for m in messages))
        self.assertTrue(any("names no scenario" in m for m in messages))

    @verifies("scenario.spec.verification-declarations")
    def test_tests_declare_the_scenarios_they_verify_and_coverage_is_reported(self):
        declarations = scan_declarations(self.root, ["tests/shop/test_cart.py", "src/shop/cart.py"])
        self.assertEqual([("scenario.shop.submit", "tests/shop/test_cart.py", "CartTests.test_submit")],
                         [(d.scenario_id, d.path, d.name) for d in declarations])
        repository = SpecRepository(self.root, PACKAGE)
        self.assertEqual({"scenario.shop.submit": 1},
                         {k: len(v) for k, v in repository.scenario_verifications(repository.select("module.shop")).items()})
        self.write("tests/shop/test_cart.py", "def test_nothing():\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))
        self.assertEqual("success", report.status)
        self.write("tests/shop/test_cart.py",
                   "from concorde.spec.verification import verifies\n\n@verifies('scenario.shop.unknown')\ndef test_x():\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-001", "error"), self.rules(report))
        self.write("tests/shop/test_cart.py", "def broken(:\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-004", "error"), self.rules(report))
        self.write("tests/shop/test_cart.py",
                   "from concorde.spec.verification import verifies\n\n@verifies(name)\ndef test_x():\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-004", "error"), self.rules(report))

    def test_the_decorator_records_scenarios_and_returns_the_function(self):
        @verifies("scenario.shop.submit", "scenario.shop.other")
        def probe():
            return 1

        self.assertEqual(("scenario.shop.submit", "scenario.shop.other"), probe.concorde_scenarios)
        self.assertEqual(1, probe())
        with self.assertRaises(ValueError):
            verifies("req.shop.single-order")

    @verifies("scenario.spec.verification-declarations")
    def test_a_declaration_in_a_file_the_module_does_not_list_is_a_warning(self):
        registry = json.loads((self.root / ".concorde/specs.json").read_text())
        registry["targets"].append({"id": "module.other", "kind": "module", "title": "Other",
            "documents": ["specs/other/module.md"], "parent": None, "uses": [], "files": ["tests/other/"], "checks": [], "references": []})
        registry["targets"][0]["files"] = ["src/shop/"]
        (self.root / ".concorde/specs.json").write_text(json.dumps(registry))
        entities = [{"id": "entity.other.tests", "title": "Other tests", "kind": "tests",
                     "responsibility": "Exercise the shop from outside.", "files": ["tests/other/"]}]
        self.write("specs/other/module.md", "```concorde-document\n" + json.dumps(
            {"id": "document.other", "owner": "module.other", "main_visible": True})
            + "\n```\n\n# Other\n\n## Purpose\n\nOther.\n\n## Requirements\n\nNone.\n\n## Scenarios\n\nNone.\n\n"
              "## Ontology\n\n### Entities\n\n```concorde-entities\n" + json.dumps(entities)
            + "\n```\n\n### Relationships\n\n```mermaid\nflowchart TB\n    tests[\"Other tests\"]\n```\n")
        self.write("specs/shop/module.md", reading_entry(REQUIREMENT, SCENARIO).replace(
            json.dumps(ENTITIES), json.dumps(ENTITIES[:1])).replace('    tests["Shop tests"]\n    tests -->|exercise| cart', ''))
        self.write("tests/other/test_shop.py",
                   "from concorde.spec.verification import verifies\n\n@verifies('scenario.shop.submit')\ndef test_x():\n    pass\n")
        report = self.validate()
        self.assertIn(("CONCORDE-VERIFICATION-003", "warning"), self.rules(report))
        self.assertNotIn(("CONCORDE-VERIFICATION-002", "warning"), self.rules(report))


if __name__ == "__main__":
    unittest.main()
