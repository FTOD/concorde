"""A change scope holds every Module that may have to change with the changed one."""

import json
import unittest

from concorde.planning.scope import change_scope
from concorde.spec.verification import verifies
from tests.concorde.support.contract_project import (
    LEDGER_ENTRY,
    READ_CONTRACT,
    ContractProject,
)


class ChangeScopeTests(ContractProject, unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
