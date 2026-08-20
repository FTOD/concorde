import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, operation_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class ValidationIntegrationTests(unittest.TestCase):
    def test_three_runs_are_byte_equivalent_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            outputs = [canonical_json(operation_envelope(validate_project(root))) for _ in range(3)]
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(before, after)
            self.assertIn('"source_digest":"sha256:', outputs[0])

    def test_bounded_target_and_unknown_evidence_are_supported(self):
        result = validate_project(VALID_PROJECT, "module.example.api")
        self.assertEqual(result.status, "success")
        self.assertGreater(len(result.artifacts), 0)
        self.assertFalse(any(item.severity == "error" for item in result.findings))


if __name__ == "__main__":
    unittest.main()
