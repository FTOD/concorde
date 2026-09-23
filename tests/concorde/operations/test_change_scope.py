"""Multi-Module changes (change scope) and promise-level Spec review impact."""

import json
import tempfile
import unittest
from pathlib import Path

from concorde.planning.scope import change_scope
from concorde.review.impact import review_impact
from concorde.spec.impact import changed_nodes
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    PACKAGE,
    block,
    entry_of,
    project,
    update_module,
    uses,
)

LEDGER_ENTRY = "specs/ledger/module.md"
LEDGER_OBLIGATIONS = "specs/ledger/obligations.md"
READ_CONTRACT = {
    "id": "contract.ledger.read",
    "version": 2,
    "schema": {"type": "integer"},
    "semantics": "Return the stored balance.",
    "example": 42,
}


class Fixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def repository(self, **options):
        return SpecRepository(self.root, PACKAGE, **options)

    def explain(self, module_id, anchor, text):
        path = self.root / entry_of(self.root, module_id)
        path.write_text(path.read_text() + f'\n<a id="{anchor}"></a>\n\n{text}\n')

    def participate(self, module_id, role, peer, version=2, contract=READ_CONTRACT):
        anchor = "participates-" + contract["id"].replace(".", "-")
        self.explain(module_id, anchor, "Balance reads follow the read contract.")
        update_module(
            self.root,
            module_id,
            participates=[
                {
                    "contract": contract["id"],
                    "version": version,
                    "role": role,
                    "peer": peer,
                    "meaning": "#" + anchor,
                }
            ],
        )

    def define_contract(self, path=LEDGER_OBLIGATIONS, contract=READ_CONTRACT):
        with (self.root / path).open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", contract))

    def snapshot(self, *paths):
        """Both members of each document, as a baseline override."""
        return {
            member: (self.root / member).read_bytes()
            for path in paths
            for member in (path, path + ".json")
        }

    def replace(self, path, old, new):
        file = self.root / path
        text = file.read_text()
        self.assertIn(old, text)
        file.write_text(text.replace(old, new))


class ChangeScopeTests(Fixture):
    @verifies("scenario.planning.change-scope")
    def test_scope_spans_composition_dependencies_references_contracts_and_shared_files(
        self,
    ):
        repository = self.repository()
        # Transfer uses the ledger; Banking relates its request concept to Transfers.
        self.assertEqual(
            ("module.ledger", "scope.bank", "service.transfer"),
            change_scope(repository, "service.transfer"),
        )
        # Transfer imports the ledger's Account concept, and Banking uses the ledger: a Module that
        # selects the owner's documents may have to follow its change.
        self.assertEqual(
            ("module.ledger", "scope.bank", "service.transfer"),
            change_scope(repository, "module.ledger"),
        )
        # Banking uses Audit, so it may have to follow an Audit change.
        self.assertEqual(
            ("scope.audit", "scope.bank"), change_scope(repository, "scope.audit")
        )
        # A contract Audit defines brings every participant, though Audit uses nobody.
        record = {**READ_CONTRACT, "id": "contract.audit.record"}
        self.define_contract("specs/audit/obligations.md", record)
        self.participate("scope.audit", "provided", "scope.bank", contract=record)
        self.participate("scope.bank", "required", "scope.audit", contract=record)
        repository = self.repository()
        self.assertEqual(
            ("scope.audit", "scope.bank"), change_scope(repository, "scope.audit")
        )
        # A participant's scope brings the contract's owner.
        self.assertIn("scope.audit", change_scope(repository, "scope.bank"))
        # A file bound by two Modules puts each in the other's scope.
        metadata = self.root / (LEDGER_ENTRY + ".json")
        value = json.loads(metadata.read_text())
        store = next(
            item
            for item in value["defines"]
            if item["id"] == "realization.ledger.store"
        )
        store["entries"].append("shared.txt")
        metadata.write_text(json.dumps(value, indent=2) + "\n")
        self.assertIn(
            "module.workspace", change_scope(self.repository(), "module.ledger")
        )
        self.assertIn(
            "module.ledger", change_scope(self.repository(), "module.workspace")
        )


class ReviewImpactTests(Fixture):
    def narrow_transfer(self):
        """Transfer relies only on the ledger's Account concept."""
        update_module(
            self.root,
            "service.transfer",
            uses=[
                uses(
                    "module.ledger",
                    "#uses-module-ledger",
                    relies_on=["concept.ledger.account"],
                )
            ],
        )

    def impact(self, *paths, edit):
        baseline = self.snapshot(*paths)
        edit()
        old = self.repository(document_overrides=baseline)
        return review_impact(old, self.repository(), None)

    @verifies("scenario.review.promise-impact")
    def test_narrowed_selection_of_unchanged_nodes_needs_no_review(self):
        self.narrow_transfer()
        # Prose outside every node definition: only whole-document selectors are concerned.
        impact = self.impact(
            LEDGER_ENTRY,
            edit=lambda: self.replace(
                LEDGER_ENTRY,
                "answers one read per account identity.",
                "answers exactly one read per account identity.",
            ),
        )
        self.assertEqual(("module.ledger", "scope.bank"), impact)

    @verifies("scenario.review.promise-impact")
    def test_a_changed_relied_on_definition_concerns_the_narrowed_consumer(self):
        self.narrow_transfer()
        impact = self.impact(
            LEDGER_ENTRY,
            edit=lambda: self.replace(
                LEDGER_ENTRY,
                "The identity of exactly one stored balance.",
                "The identity of one or more stored balances.",
            ),
        )
        self.assertEqual(("module.ledger", "scope.bank", "service.transfer"), impact)

    @verifies("scenario.review.promise-impact")
    def test_an_unselected_changed_document_concerns_only_whole_selectors(self):
        self.narrow_transfer()
        baseline = self.snapshot(LEDGER_OBLIGATIONS)
        self.replace(
            LEDGER_OBLIGATIONS, "THEN it raises KeyError", "THEN it raises LookupError"
        )
        old = self.repository(document_overrides=baseline)
        new = self.repository()
        self.assertEqual(
            ("scenario.ledger.unknown",), changed_nodes(old, new, [LEDGER_OBLIGATIONS])
        )
        self.assertEqual(("module.ledger", "scope.bank"), review_impact(old, new, None))
        # An unchanged document concerns nobody, whoever selects it.
        self.assertEqual((), review_impact(old, new, ["specs/transfer/module.md"]))

    @verifies("scenario.review.promise-impact")
    def test_a_changed_module_block_concerns_modules_relating_to_the_module(self):
        # Banking relates its request concept to Transfers and selects the transfer documents whole;
        # Audit, which uses nobody, is never concerned.
        impact = self.impact(
            "specs/transfer/module.md",
            edit=lambda: update_module(
                self.root, "service.transfer", title="Money transfers"
            ),
        )
        self.assertEqual(("scope.bank", "service.transfer"), impact)


if __name__ == "__main__":
    unittest.main()
