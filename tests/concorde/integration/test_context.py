import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402


class ContextTests(unittest.TestCase):
    def test_module_and_feature_resolve_to_same_one_level_context(self):
        by_module = bounded_context(CONTEXT_PROJECT, "module.example")
        by_feature = bounded_context(CONTEXT_PROJECT, "feature.example.deliver")
        self.assertEqual(by_module.status, "success")
        self.assertEqual(by_feature.status, "success")
        module_context = by_module.result["context"]
        feature_context = by_feature.result["context"]
        self.assertEqual(module_context["current_module"], feature_context["current_module"])
        self.assertEqual([child["id"] for child in module_context["children"]], ["module.example.api"])
        self.assertNotIn("module.example.api.store", repr(module_context["children"]))
        self.assertIn("module.example.api", module_context["deeper_references"])
        self.assertTrue(module_context["children"][0]["contracts"]["provided"][0]["flow"])

    def test_unknown_target_is_invalid_and_context_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            result = bounded_context(root, "module.missing")
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(result.status, "invalid")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
