from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.operation_config import apply_configuration, load_configuration, propose_configuration
from concorde.capabilities.operation_data import OperationDataError, artifact, decode, typed, validate_typed, verify_artifacts
from concorde.understanding.initialize import apply_proposal, propose_initialization
from tests.concorde.support.operation_json import CONFIGURATION


class OperationDataTests(unittest.TestCase):
    def test_triage_conditional_fields_are_enforced(self):
        valid = [
            {"action": "status", "reflection_ids": []},
            {"action": "close", "reflection_ids": ["R-001"]},
            {"action": "investigate", "reflection_ids": ["R-001"], "feature_path": "specs/example/features/001-change.md", "request": "Investigate"},
            {"action": "implement", "reflection_ids": ["R-001"], "feature_path": "specs/example/features/001-change.md", "request": "Implement", "route": "plan"},
        ]
        for data in valid:
            typed("concorde-reflections-triage-context", data)
        invalid = [
            {"action": "close", "reflection_ids": []},
            {"action": "status", "reflection_ids": [], "feature_path": "specs/example/features/001-change.md"},
            {"action": "status", "reflection_ids": ["R-001", "R-001"]},
            {"action": "investigate", "reflection_ids": ["R-001"]},
            {**valid[2], "route": "plan"},
            {key: value for key, value in valid[3].items() if key != "route"},
            {**valid[3], "constraints": None},
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(OperationDataError):
                typed("concorde-reflections-triage-context", data)

    def test_artifact_references_detect_staleness_missing_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "artifact.md"
            path.write_text("original")
            reference = artifact(root, "artifact.fixture", "artifact.md")
            verify_artifacts(root, reference)
            path.write_text("modified")
            with self.assertRaisesRegex(OperationDataError, "changed"):
                verify_artifacts(root, reference)
            path.unlink()
            with self.assertRaisesRegex(OperationDataError, "does not exist"):
                verify_artifacts(root, reference)
            (root / "other.md").write_text("original")
            path.symlink_to(root / "other.md")
            with self.assertRaisesRegex(OperationDataError, "symlink"):
                verify_artifacts(root, reference)

    def test_json_rejects_duplicate_fields_and_non_finite_numbers(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(OperationDataError):
                decode(value)

    def test_new_initialization_requires_explicit_configuration_and_applies_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(propose_initialization(root).status, "invalid")
            proposed = propose_initialization(root, "module.sample", "Sample", CONFIGURATION)
            self.assertEqual(proposed.status, "proposal", proposed.findings)
            self.assertEqual(proposed.result["proposal"]["proposal_version"], 4)
            self.assertEqual(len(proposed.result["proposal"]["files"]), 5)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            applied = apply_proposal(root, "accepted.json")
            self.assertEqual(applied.status, "success", applied.findings)
            self.assertEqual(load_configuration(root), CONFIGURATION)
            self.assertTrue((root / ".concorde/reflections/config.json").is_file())
            self.assertEqual(apply_proposal(root, "accepted.json").status, "unchanged")

    def test_existing_configuration_migration_preserves_fields_and_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".concorde/config.json"
            path.parent.mkdir()
            original = {"profile_version": 7, "root_module_id": "module.example", "specification_root": "specs/example", "project_setting": {"keep": True}}
            path.write_text(json.dumps(original))
            with self.assertRaises(OperationDataError):
                load_configuration(root)
            proposed = propose_configuration(root, CONFIGURATION)
            self.assertEqual(json.loads(path.read_text()), original)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            path.write_text(json.dumps({**original, "new_setting": True}))
            self.assertEqual(apply_configuration(root, "accepted.json").status, "invalid")
            proposed = propose_configuration(root, CONFIGURATION)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            self.assertEqual(apply_configuration(root, "accepted.json").status, "success")
            self.assertEqual(json.loads(path.read_text())["project_setting"], {"keep": True})
            self.assertTrue(json.loads(path.read_text())["new_setting"])
            self.assertEqual(load_configuration(root), CONFIGURATION)
            self.assertEqual(apply_configuration(root, "accepted.json").status, "unchanged")


if __name__ == "__main__":
    unittest.main()
