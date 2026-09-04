"""Profile 7 removes feature abstracts from the active validation ontology."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.validate import FOCUSED_VALIDATORS, validate_project  # noqa: E402


class AbstractRemovalTests(unittest.TestCase):
    def test_abstract_validator_is_not_active_and_legacy_file_is_layout_residue(self):
        self.assertNotIn("validate_abstracts", {validator.__name__ for validator in FOCUSED_VALIDATORS})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            abstract = root / "specs/example/features/abstract.md"
            abstract.write_text("# Legacy abstract\n", encoding="utf-8")
            findings = validate_project(root).findings
            self.assertTrue(any(item.rule_id == "CONCORDE-LAYOUT-LEGACY" and item.source.endswith("abstract.md") for item in findings))
            self.assertFalse(any(item.rule_id.startswith("CONCORDE-ABSTRACT-") for item in findings))


if __name__ == "__main__":
    unittest.main()
