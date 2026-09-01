"""Standalone specification contracts are replaced by embedded feature interfaces."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.repository import ProjectRepository  # noqa: E402
from concorde.validate import FOCUSED_VALIDATORS, validate_project  # noqa: E402


class ContractRemovalTests(unittest.TestCase):
    def test_standalone_contract_validator_is_inactive_and_interface_is_normalized_from_design(self):
        self.assertNotIn("validate_contracts", {validator.__name__ for validator in FOCUSED_VALIDATORS})
        package = ProjectRepository(VALID_PROJECT).load()
        self.assertEqual(package.interfaces["contract.example.workflow"].owner, "feature.example.deliver")

    def test_contract_directory_and_document_are_legacy_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            directory = root / "specs/example/contracts/workflow"
            directory.mkdir(parents=True)
            (directory / "contract.md").write_text("legacy", encoding="utf-8")
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-LEGACY" and item.source.endswith("contracts") for item in findings))
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-LEGACY" and item.source.endswith("contract.md") for item in findings))


if __name__ == "__main__":
    unittest.main()
