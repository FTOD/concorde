"""Architecture entity types replace the former parallel terminology ontology."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.validate import FOCUSED_VALIDATORS, validate_project  # noqa: E402


class TerminologyRemovalTests(unittest.TestCase):
    def test_terminology_validator_is_inactive_and_custom_types_need_local_definition(self):
        self.assertNotIn("validate_terminology", {validator.__name__ for validator in FOCUSED_VALIDATORS})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            architecture = root / "specs/example/architecture.md"
            architecture.write_text(architecture.read_text(encoding="utf-8").replace("| program | The workflow orchestrator", "| actor | The workflow orchestrator"), encoding="utf-8")
            self.assertIn("CONCORDE-ENTITY-005", {item.rule_id for item in validate_project(root).findings})
            architecture.write_text(architecture.read_text(encoding="utf-8") + "\n## Entity Types\n\n| Type | Definition |\n|---|---|\n| `actor` | A project-defined active architecture entity. |\n", encoding="utf-8")
            self.assertNotIn("CONCORDE-ENTITY-005", {item.rule_id for item in validate_project(root).findings})


if __name__ == "__main__":
    unittest.main()
