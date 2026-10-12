"""Loading keeps to its snapshot, refuses what the contract calls fatal and keeps every cause."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from concorde.spec.grants import context_identity, grant
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import (
    PACKAGE,
    block,
    entry_of,
    include_external,
    project,
    read_json,
    update_glossary_entry,
    update_module,
)

LEDGER = "specs/ledger/module.md"
LEDGER_OBLIGATIONS = "specs/ledger/obligations.md"
BANK = "specs/bank/module.md"
BANK_OBLIGATIONS = "specs/bank/obligations.md"
CONTRACT = {
    "id": "contract.ledger.balance",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"balance": {"type": "integer"}},
        "required": ["balance"],
    },
    "semantics": "The stored balance of one account.",
    "example": {"balance": 1},
}


class LoadingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        project(self.root)

    def repository(self, **options):
        return SpecRepository(self.root, PACKAGE, **options)

    def validate(self, **overrides):
        return validate_repository(
            self.root, package_root=PACKAGE, document_overrides=overrides or None
        )

    def metadata(self, path, change):
        value = read_json(self.root, path + ".json")
        change(value)
        return json.dumps(value).encode()

    @verifies("scenario.spec.validate-structural-errors")
    def test_malformed_entry_metadata_is_reported_not_raised(self):
        def bad_document(value):
            value["document"] = 5

        def bad_target(value):
            value["module"]["uses"] = [{"target": ["x"], "meaning": "#a"}]
            value["module"]["contains"] = [{"target": {"a": 1}, "meaning": "#a"}]

        for label, change in (("document", bad_document), ("target", bad_target)):
            with self.subTest(label):
                report = self.validate(
                    **{LEDGER + ".json": self.metadata(LEDGER, change)}
                )
                self.assertEqual("invalid", report.status)
                self.assertTrue(report.findings)

    def test_a_concept_whose_owner_is_no_module_refuses_the_repository(self):
        update_glossary_entry(self.root, "concept.ledger.account", owner="module.none")
        with self.assertRaises(SpecError) as raised:
            self.repository()
        self.assertIn("CHK.node.owner", str(raised.exception))
        self.assertIn("CHK.node.owner", {f.rule_id for f in self.validate().findings})

    def test_a_module_with_several_entries_refuses_the_repository(self):
        extra = "specs/ledger/extra/module.md"
        (self.root / extra).parent.mkdir()
        shutil.copy(self.root / LEDGER, self.root / extra)
        value = read_json(self.root, LEDGER + ".json")
        value["document"]["id"] = "document.ledger.extra"
        value["defines"] = []
        value.pop("module")
        (self.root / (extra + ".json")).write_text(json.dumps(value))
        owns = read_json(self.root, LEDGER + ".json")["module"]["owns"]
        update_module(self.root, "module.ledger", owns=[*owns, extra])
        with self.assertRaises(SpecError) as raised:
            self.repository()
        self.assertIn("CHK.document.entry", str(raised.exception))
        findings = [
            f for f in self.validate().findings if f.rule_id == "CHK.document.entry"
        ]
        self.assertEqual(1, len(findings), [f.message for f in findings])

    @verifies("scenario.spec.error-every-cause")
    def test_a_load_error_keeps_the_error_behind_each_problem(self):
        with self.assertRaises(SpecError) as raised:
            self.repository(
                document_overrides={
                    LEDGER: b"\xff\xfe",
                    "specs/bank/module.md.json": b'{"a": 1, "a": 2}',
                }
            )
        causes = {cause.path: cause for cause in raised.exception.causes}
        self.assertEqual(["invalid_spec"], [c.code for c in causes[LEDGER].causes])
        self.assertEqual(
            ["invalid_json"],
            [c.code for c in causes["specs/bank/module.md.json"].causes],
        )

    def test_the_digest_pins_documents_that_failed_admission(self):
        digests = {
            self.validate(**{LEDGER + ".json": text}).result["source_digest"]
            for text in (b"{", b"[")
        }
        self.assertEqual(2, len(digests))

    def test_queries_answer_from_the_loaded_snapshot(self):
        include_external(self.root, "module.ledger", "references/lib/")
        (self.root / "references/lib").mkdir(parents=True)
        (self.root / "references/lib/api.md").write_text("# API\n")
        repository = self.repository()
        identity = context_identity(repository, ["module.ledger"], True)
        files = repository.external_files("references/lib/")
        # The files change after loading: the repository's answers do not.
        (self.root / "references/lib/more.md").write_text("# More\n")
        entry = self.root / entry_of(self.root, "scope.audit")
        entry.write_text(entry.read_text() + "\nMore text.\n")
        self.assertEqual(
            identity, context_identity(repository, ["module.ledger"], True)
        )
        self.assertEqual(files, repository.external_files("references/lib/"))
        fresh = self.repository()
        self.assertNotEqual(
            fresh.external_digest("references/lib/"),
            repository.external_digest("references/lib/"),
        )

    def test_returned_records_do_not_share_the_repositorys_entries(self):
        repository = self.repository()
        before = json.dumps(repository.glossary_entries, sort_keys=True)
        value = grant(repository, ["module.ledger"], "implement").value
        for entry in value["terms"]:
            entry["definition"] = "changed"
        for record in repository.term_records("module.ledger"):
            record["entry"]["title"] = "changed"
        self.assertEqual(
            before, json.dumps(repository.glossary_entries, sort_keys=True)
        )

    @verifies("scenario.spec.validate-structural-errors")
    def test_a_document_identity_a_node_uses_is_refused_in_either_order(self):
        # The document reusing scenario.ledger.read loads before (a.md) or after (z.md) the
        # obligations document that defines the scenario.
        for name in ("a.md", "z.md"):
            with self.subTest(name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                project(root)
                path = f"specs/ledger/{name}"
                (root / path).write_text("# Extra\n\nMore about the ledger.\n")
                value = {
                    "schema_version": 3,
                    "document": {
                        "id": "scenario.ledger.read",
                        "owner": "module.ledger",
                        "role": "implementation",
                    },
                    "defines": [],
                    "relations": [],
                }
                (root / (path + ".json")).write_text(json.dumps(value))
                owns = read_json(root, LEDGER + ".json")["module"]["owns"]
                update_module(root, "module.ledger", owns=[*owns, path])
                report = validate_repository(root, package_root=PACKAGE)
                self.assertEqual("invalid", report.status)
                self.assertIn(
                    ("CHK.node.id", "scenario.ledger.read"),
                    {(f.rule_id, f.subject_id) for f in report.findings},
                )

    def test_returned_definitions_and_declarations_do_not_share_the_repositorys_records(
        self,
    ):
        with (self.root / LEDGER_OBLIGATIONS).open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", CONTRACT))
        update_glossary_entry(
            self.root,
            "concept.bank.request",
            relates=[{"verb": "names", "target": "concept.ledger.account"}],
        )
        update_module(
            self.root,
            "module.ledger",
            participates=[
                {
                    "contract": "contract.ledger.balance",
                    "version": 1,
                    "role": "provided",
                    "peer": "external",
                    "meaning": "#concept.ledger.account",
                }
            ],
        )
        repository = self.repository()
        contract = repository.contracts("module.ledger")[0]
        contract["version"] = 9
        contract["schema"]["properties"]["balance"]["type"] = "string"
        repository.definitions("module.ledger").contracts[0]["example"]["balance"] = 2
        repository.definitions("scope.bank").concepts[0].relates[0]["verb"] = "changed"
        repository.participations("module.ledger")[0]["version"] = 9
        declaration = repository.module_declaration("scope.bank")
        declaration.uses[0]["target"] = "module.none"
        declaration.block["title"] = "Changed"
        declaration.block["uses"].clear()
        declaration.record["entry"] = "specs/none/module.md"
        ledger = repository.module_declaration("module.ledger")
        ledger.participates[0]["version"] = 9
        # Asked again, the repository answers from its own records.
        self.assertEqual(
            {**CONTRACT, "source": LEDGER_OBLIGATIONS, "owner": "module.ledger"},
            repository.contracts("module.ledger")[0],
        )
        self.assertEqual(
            [{"verb": "names", "target": "concept.ledger.account"}],
            list(repository.concepts("scope.bank")[0].relates),
        )
        again = repository.module_declaration("scope.bank")
        self.assertEqual("service.transfer", again.uses[0]["target"])
        self.assertEqual("Banking", again.block["title"])
        self.assertEqual(3, len(again.block["uses"]))
        self.assertEqual(BANK, again.record["entry"])
        self.assertEqual(
            1, repository.module_declaration("module.ledger").participates[0]["version"]
        )
        self.assertEqual(1, repository.participations("module.ledger")[0]["version"])

    @verifies("scenario.spec.validate-structural-errors")
    def test_malformed_declaration_fields_are_findings_beside_an_independent_one(self):
        def ledger(change):
            return {
                LEDGER_OBLIGATIONS + ".json": self.metadata(LEDGER_OBLIGATIONS, change)
            }

        def bank(change):
            return {BANK + ".json": self.metadata(BANK, change)}

        def role(value):
            value["document"]["role"] = []

        def relies_on(value):
            value["module"]["uses"][0]["relies_on"] = None

        def relies_on_items(value):
            value["module"]["uses"][0]["relies_on"] = [["scenario.transfer.debit"], 5]

        def relates(value):
            value["relations"].append(
                {
                    "type": "relates",
                    "source": "realization.ledger.store",
                    "verb": "keeps",
                }
            )

        def relates_target(value):
            value["relations"].append(
                {
                    "type": "relates",
                    "source": "realization.ledger.store",
                    "verb": "keeps",
                    "target": ["concept.ledger.account"],
                }
            )

        def participates(value):
            value["module"]["participates"] = [
                {
                    "contract": "contract.bank.none",
                    "version": None,
                    "role": ["provided"],
                    "peer": {"id": "module.ledger"},
                    "meaning": None,
                }
            ]

        def includes(value):
            value["module"]["includes"] = [
                {"kind": ["module"], "target": "module.ledger", "reason": "x"}
            ]

        # The independent violation: a scenario of another Module without a THEN step.
        transfer = "specs/transfer/obligations.md"
        independent = {
            transfer: (self.root / transfer)
            .read_text()
            .replace("- THEN it returns 80\n", "")
            .encode()
        }
        cases = {
            "collection-valued role": (ledger(role), "CHK.document.role"),
            "null relies_on": (bank(relies_on), "CHK.document.schema"),
            "relies_on items": (bank(relies_on_items), "CHK.document.schema"),
            "relates missing target": (ledger(relates), "CHK.document.schema"),
            "relates collection target": (
                ledger(relates_target),
                "CHK.relation.endpoints",
            ),
            "participation fields": (bank(participates), "CHK.document.schema"),
            "includes kind": (bank(includes), "CHK.document.schema"),
        }
        for label, (overrides, rule) in cases.items():
            with self.subTest(label):
                report = self.validate(**overrides, **independent)
                rules = {f.rule_id for f in report.findings}
                self.assertEqual("invalid", report.status)
                self.assertIn(rule, rules)
                self.assertIn(
                    ("CHK.scenario.steps", transfer),
                    {(f.rule_id, f.source) for f in report.findings},
                )

    def test_a_null_relies_on_selects_no_more_than_the_entry(self):
        update_module(
            self.root,
            "scope.bank",
            uses=[
                {
                    "target": "service.transfer",
                    "meaning": "#uses-service-transfer",
                    "relies_on": None,
                }
            ],
        )
        repository = self.repository()
        self.assertEqual(
            [], repository.module_declaration("scope.bank").uses[0]["relies_on"]
        )
        self.assertEqual(
            ("specs/transfer/module.md",),
            repository.selection(repository.module_declaration("scope.bank").uses[0]),
        )

    def test_a_failed_load_pins_the_inputs_it_read(self):
        registries = {
            self.validate_bytes(registry_bytes=text).result["source_digest"]
            for text in (b"{", b"[", b'{"schema_version": 2, "modules": []}')
        }
        self.assertEqual(3, len(registries))
        config = self.root / ".concorde/config.json"
        configs = set()
        for text in (b"{", b"[1]", None):
            if text is None:
                config.unlink()
            else:
                config.write_bytes(text)
            report = self.validate()
            self.assertEqual("invalid", report.status)
            configs.add(report.result["source_digest"])
        self.assertEqual(3, len(configs))

    def validate_bytes(self, **options):
        report = validate_repository(self.root, package_root=PACKAGE, **options)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-SOURCE-008", {f.rule_id for f in report.findings})
        return report

    def test_definition_headings_define_only_at_levels_two_to_five(self):
        original = {
            path: (self.root / path).read_text()
            for path in (LEDGER_OBLIGATIONS, BANK_OBLIGATIONS)
        }
        for level in (1, 2, 5, 6):
            with self.subTest(level):
                marks = "#" * level
                overrides = {
                    LEDGER_OBLIGATIONS: original[LEDGER_OBLIGATIONS]
                    .replace(
                        "### scenario.ledger.read", f"{marks} scenario.ledger.read"
                    )
                    .encode(),
                    BANK_OBLIGATIONS: original[BANK_OBLIGATIONS]
                    .replace("### req.bank.retry", f"{marks} req.bank.retry")
                    .encode(),
                }
                report = self.validate(**overrides)
                malformed = {
                    (f.rule_id, f.source)
                    for f in report.findings
                    if f.message.startswith("malformed ")
                }
                repository = self.repository(document_overrides=overrides)
                defined = {
                    "scenario.ledger.read" in repository.scenario_nodes,
                    "req.bank.retry" in repository.requirement_nodes,
                }
                if level in (2, 5):
                    self.assertEqual(set(), malformed)
                    self.assertEqual({True}, defined)
                else:
                    self.assertEqual(
                        {
                            ("CHK.scenario.steps", LEDGER_OBLIGATIONS),
                            ("CHK.requirement.statement", BANK_OBLIGATIONS),
                        },
                        malformed,
                    )
                    self.assertEqual({False}, defined)
                    self.assertEqual("invalid", report.status)


if __name__ == "__main__":
    unittest.main()
