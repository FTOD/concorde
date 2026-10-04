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
    entry_of,
    include_external,
    project,
    read_json,
    update_glossary_entry,
    update_module,
)

LEDGER = "specs/ledger/module.md"


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


if __name__ == "__main__":
    unittest.main()
