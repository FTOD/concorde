"""File transactions refuse stale inputs, and two Spec revisions compare by their definitions."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from concorde.spec.changes import apply_files, file_change
from concorde.spec.impact import changed_documents, changed_nodes
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import PACKAGE, project


class FileTransactionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    @verifies("scenario.spec.transaction-stale")
    def test_a_changed_file_stops_the_transaction_before_any_write(self):
        (self.root / "a.txt").write_text("a\n")
        (self.root / "b.txt").write_text("b\n")
        changes = [
            file_change(self.root, "a.txt", "A\n"),
            file_change(self.root, "b.txt", "B\n"),
            file_change(self.root, "c.txt", "C\n"),
        ]
        # Another writer changes b.txt after the transaction was planned.
        (self.root / "b.txt").write_text("b, edited elsewhere\n")
        with self.assertRaises(SpecError) as raised:
            apply_files(self.root, changes, {"a.txt", "b.txt", "c.txt"})
        self.assertEqual("stale_proposal", raised.exception.code)
        self.assertEqual("a\n", (self.root / "a.txt").read_text())
        self.assertEqual("b, edited elsewhere\n", (self.root / "b.txt").read_text())
        self.assertFalse((self.root / "c.txt").exists())
        self.assertEqual(
            ["a.txt", "b.txt"], sorted(p.name for p in self.root.iterdir())
        )


class ChangedDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.old_root = Path(self.directory.name) / "old"
        self.old_root.mkdir()
        project(self.old_root)
        self.new_root = Path(self.directory.name) / "new"
        shutil.copytree(self.old_root, self.new_root)

    @verifies("scenario.spec.changed-definitions")
    def test_changed_documents_and_nodes_between_two_revisions(self):
        path = self.new_root / "specs/transfer/obligations.md"
        text = path.read_text()
        statement = "transfer SHALL NOT alter any stored balance."
        self.assertIn(statement, text)
        path.write_text(
            text.replace(
                statement, "transfer SHALL NOT alter or read any stored balance."
            )
        )
        old = SpecRepository(self.old_root, PACKAGE)
        new = SpecRepository(self.new_root, PACKAGE)
        documents = changed_documents(old, new)
        self.assertEqual(("specs/transfer/obligations.md",), documents)
        self.assertEqual(("req.transfer.pure",), changed_nodes(old, new, documents))
        # Every node kind compares by its own definition: a concept's definition row, a
        # realization record and an entry's module block.
        entry = self.new_root / "specs/ledger/module.md"
        entry.write_text(
            entry.read_text().replace(
                "| Account | The identity of exactly one stored balance. |",
                "| Account | The identity of one stored balance. |",
            )
        )
        metadata = self.new_root / "specs/ledger/module.md.json"
        metadata.write_text(
            metadata.read_text().replace('"Balance store"', '"Balance table"')
        )
        new = SpecRepository(self.new_root, PACKAGE)
        documents = changed_documents(old, new)
        self.assertEqual(
            ("specs/ledger/module.md", "specs/transfer/obligations.md"), documents
        )
        self.assertEqual(
            (
                "concept.ledger.account",
                "realization.ledger.store",
                "req.transfer.pure",
            ),
            changed_nodes(old, new, documents),
        )
        # An entry's module block is the Module's own definition.
        entry_block = self.new_root / "specs/audit/module.md.json"
        value = json.loads(entry_block.read_text())
        value["module"]["includes"] = [
            {
                "kind": "document",
                "target": "document.transfer.promises",
                "reason": "the transfer amount rules",
            }
        ]
        entry_block.write_text(json.dumps(value, indent=2) + "\n")
        new = SpecRepository(self.new_root, PACKAGE)
        self.assertIn(
            "scope.audit",
            changed_nodes(new=new, old=old, paths=["specs/audit/module.md"]),
        )
        self.assertEqual(
            (),
            changed_nodes(
                old, new, ["specs/bank/module.md", "specs/transfer/module.md"]
            ),
        )


if __name__ == "__main__":
    unittest.main()
