"""Profile 7 replaces module summaries/design references with architecture.md."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.validate import FOCUSED_VALIDATORS, validate_project  # noqa: E402


class SummaryRemovalTests(unittest.TestCase):
    def test_summary_validator_is_inactive_and_module_pair_is_legacy_residue(self):
        self.assertNotIn("validate_summaries", {validator.__name__ for validator in FOCUSED_VALIDATORS})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            (root / "specs/example/module.md").write_text("legacy summary", encoding="utf-8")
            (root / "specs/example/design.md").write_text("legacy design reference", encoding="utf-8")
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-LEGACY" and item.source.endswith("module.md") for item in findings))
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-010" and item.source.endswith("design.md") for item in findings))
            self.assertFalse(any(item.rule_id.startswith("CONCORDE-SUMMARY-") for item in findings))


if __name__ == "__main__":
    unittest.main()
