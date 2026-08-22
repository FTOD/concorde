import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.readiness import architecture_readiness  # noqa: E402


class ArchitectureReadinessTests(unittest.TestCase):
    def test_cross_boundary_feature_is_incomplete_then_ready(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            view_path = root / "specs/example/architecture.json"
            view = json.loads(view_path.read_text())
            contract = view["connections"][0].pop("contract")
            view_path.write_text(json.dumps(view))
            incomplete = architecture_readiness(root, "feature.example.deliver")
            self.assertEqual(incomplete["status"], "incomplete")
            self.assertIn("contract", " ".join(item["message"] for item in incomplete["findings"]).lower())
            view["connections"][0]["contract"] = contract
            view_path.write_text(json.dumps(view))
            ready = architecture_readiness(root, "feature.example.deliver")
            self.assertEqual(ready["status"], "ready")
            self.assertEqual(ready["providing_module"], "module.example")
            self.assertEqual(ready["source_digest"].split(":", 1)[0], "sha256")


if __name__ == "__main__":
    unittest.main()
