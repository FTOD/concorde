import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import reflection_entry, write_reflection_log
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402


class ContextTests(unittest.TestCase):
    def test_module_and_feature_resolve_to_the_same_one_module_context(self):
        by_module = bounded_context(CONTEXT_PROJECT, "module.example")
        by_feature = bounded_context(CONTEXT_PROJECT, "feature.example.deliver")
        self.assertEqual(by_module.status, "success")
        self.assertEqual(by_feature.status, "success")
        module = by_module.result["context"]
        feature = by_feature.result["context"]
        self.assertEqual(module["current_module"], feature["current_module"])
        self.assertEqual(module["current_module"]["architecture"], "specs/example/architecture.md")
        self.assertEqual([child["id"] for child in module["children"]], ["module.example.api"])
        self.assertNotIn("module.example.api.store", repr(module["children"]))
        self.assertIn("module.example.api", module["deeper_references"])
        self.assertTrue(module["current_module"]["entities"])
        self.assertTrue(module["current_module"]["relationships"])
        self.assertTrue(module["current_module"]["interactions"])

    def test_zooming_to_child_repeats_bounded_module_projection(self):
        root = bounded_context(CONTEXT_PROJECT, "module.example").result["context"]
        child = bounded_context(CONTEXT_PROJECT, "module.example.api").result["context"]
        self.assertEqual([item["id"] for item in root["children"]], ["module.example.api"])
        self.assertEqual([item["id"] for item in child["children"]], ["module.example.api.store"])
        self.assertEqual([item["id"] for item in child["module_ancestry"]], ["module.example"])
        self.assertNotIn("entity.example.store.records", repr(child["children"]))

    def test_feature_context_has_protocol_twelve_workspace_and_related_summaries(self):
        context = bounded_context(CONTEXT_PROJECT, "feature.example.api.invoke").result["context"]
        workspace = context["feature_workspace"]
        self.assertEqual(workspace["feature_path"], "specs/example/modules/api/features/001-invoke.md")
        self.assertEqual(workspace["attempt_dir"], ".concorde/attempts/feature.example.api.invoke")
        self.assertEqual(workspace["module_architecture"], "specs/example/modules/api/architecture.md")
        self.assertEqual([item["module_id"] for item in workspace["module_ancestry"]], ["module.example"])
        self.assertEqual([item["feature_id"] for item in workspace["related_features"]], ["feature.example.deliver"])
        for removed in ("feature_abstract", "feature_implementation", "feature_" + "directory", "feature_" + "design", "module_summary", "module_design", "contracts_dir", "parent_context"):
            self.assertNotIn(removed, workspace)
        self.assertNotIn("attempt/", repr(workspace["related_features"]))

    def test_flat_related_feature_context_never_exposes_parent_or_sibling_bodies(self):
        context = bounded_context(TWO_LEVEL_PROJECT, "feature.example.checkout.confirm").result["context"]
        self.assertEqual([item["feature_id"] for item in context["related_features"]], ["feature.example.checkout", "feature.example.checkout.authorize"])
        self.assertNotIn("Flat Feature Attempt", repr(context))
        self.assertNotIn("parent_feature", context)
        self.assertNotIn("siblings", context)

    def test_context_exposes_central_reflections_without_entry_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            write_reflection_log(root, [reflection_entry("R-001"), reflection_entry("R-002", feature="feature.example.api.invoke")])
            context = bounded_context(root, "module.example").result["context"]
            self.assertEqual(context["reflections"], {"path": ".concorde/reflections/log.md", "open": {"feature.example.api.invoke": 1, "feature.example.deliver": 1}})
            self.assertNotIn("R-001", repr(context))

    def test_unknown_target_is_invalid_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            result = bounded_context(root, "module.missing")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(before, {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()})


if __name__ == "__main__":
    unittest.main()
