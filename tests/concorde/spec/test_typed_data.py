from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.development.configuration import apply_configuration, load_configuration, propose_configuration
from concorde.spec.typed_data import TypedDataError, artifact, decode, verify_artifacts
from concorde.spec.verification import verifies
from tests.concorde.support.operation_json import CONFIGURATION


class TypedDataTests(unittest.TestCase):
    def test_artifact_references_detect_staleness_missing_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "artifact.md"
            path.write_text("original")
            reference = artifact(root, "artifact.fixture", "artifact.md")
            verify_artifacts(root, reference)
            path.write_text("modified")
            with self.assertRaisesRegex(TypedDataError, "changed"):
                verify_artifacts(root, reference)
            path.unlink()
            with self.assertRaisesRegex(TypedDataError, "does not exist"):
                verify_artifacts(root, reference)
            (root / "other.md").write_text("original")
            path.symlink_to(root / "other.md")
            with self.assertRaisesRegex(TypedDataError, "symlink"):
                verify_artifacts(root, reference)

    @verifies("scenario.harness.typed-reject")
    def test_json_rejects_duplicate_fields_and_non_finite_numbers(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                decode(value)

    def test_existing_configuration_migration_preserves_fields_and_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".concorde/config.json"
            path.parent.mkdir()
            original = {"profile_version": 11, "registry": ".concorde/specs.json", "project_setting": {"keep": True}}
            path.write_text(json.dumps(original))
            with self.assertRaises(TypedDataError):
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
