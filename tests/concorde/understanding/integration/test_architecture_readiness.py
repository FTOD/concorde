import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.understanding.readiness import architecture_readiness  # noqa: E402


class ArchitectureReadinessTests(unittest.TestCase):
    def test_valid_feature_is_ready_with_entities_interfaces_and_digest(self):
        ready = architecture_readiness(CONTEXT_PROJECT, "feature.example.api.invoke")
        self.assertEqual(ready["status"], "ready", ready["findings"])
        self.assertEqual(ready["providing_module"], "module.example.api")
        self.assertEqual(ready["module_architecture"], "specs/example/modules/api/architecture.md")
        self.assertIn("entity.example.api.handler", ready["participating_entities"])
        self.assertEqual(ready["interfaces"]["provided"], ["contract.example.api"])
        self.assertRegex(ready["source_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_unresolved_zoom_entity_makes_readiness_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature = root / "specs/example/modules/api/features/001-invoke.md"
            feature.write_text(feature.read_text(encoding="utf-8").replace("entity.example.api.handler", "entity.example.api.missing"), encoding="utf-8")
            readiness = architecture_readiness(root, "feature.example.api.invoke")
            self.assertEqual(readiness["status"], "incomplete")
            self.assertIn("CONCORDE-ZOOM-002", {item["rule_id"] for item in readiness["findings"]})

    def test_unknown_feature_is_incomplete_without_mutation(self):
        before = {path.relative_to(CONTEXT_PROJECT): path.read_bytes() for path in CONTEXT_PROJECT.rglob("*") if path.is_file()}
        readiness = architecture_readiness(CONTEXT_PROJECT, "feature.example.missing")
        self.assertEqual(readiness["status"], "incomplete")
        self.assertEqual(readiness["findings"][0]["rule_id"], "CONCORDE-READY-002")
        self.assertEqual(before, {path.relative_to(CONTEXT_PROJECT): path.read_bytes() for path in CONTEXT_PROJECT.rglob("*") if path.is_file()})


if __name__ == "__main__":
    unittest.main()
