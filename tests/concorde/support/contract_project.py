"""The transfer fixture project with helpers that define contracts and their participants."""

import tempfile
from pathlib import Path

from concorde.spec.repository import SpecRepository

from .spec_project import PACKAGE, block, entry_of, project, update_module

LEDGER_ENTRY = "specs/ledger/module.md"
LEDGER_OBLIGATIONS = "specs/ledger/obligations.md"
READ_CONTRACT = {
    "id": "contract.ledger.read",
    "version": 2,
    "schema": {"type": "integer"},
    "semantics": "Return the stored balance.",
    "example": 42,
}


class ContractProject:
    """Test-case mixin: the transfer fixture project with helpers to define and join contracts."""

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
