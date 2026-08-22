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
        self.assertEqual(module_context["scenarios"][0]["id"], "scenario.example.deliver")
        self.assertEqual(module_context["scenarios"][0]["interactions"][0]["contract"], "contract.example.workflow")

    def test_zooming_to_child_repeats_the_one_level_rule(self):
        root = bounded_context(CONTEXT_PROJECT, "module.example").result["context"]
        child = bounded_context(CONTEXT_PROJECT, "module.example.api").result["context"]
        self.assertEqual([item["id"] for item in root["children"]], ["module.example.api"])
        self.assertNotIn("module.example.api.store", repr(root))
        self.assertEqual(child["current_module"]["id"], "module.example.api")
        self.assertEqual([item["id"] for item in child["children"]], ["module.example.api.store"])
        self.assertNotIn("feature.example.api.invoke", repr(child["children"]))

    def test_unknown_target_is_invalid_and_context_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            result = bounded_context(root, "module.missing")
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(result.status, "invalid")
            self.assertEqual(before, after)

    def test_active_feature_context_contains_exact_workspace_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature = root / "specs/example/features/001-deliver/spec.md"
            feature.write_text(feature.read_text().replace(
                "evidence_status: unknown",
                "evidence_status: unknown\nevidence:\n  - kind: test\n    target: tests/example/test_delivery.py\n    status: unknown\n    producer: unittest",
            ))
            implementation = feature.parent / "implementation"
            implementation.mkdir()
            (implementation / "plan.md").write_text("# Plan\n")
            (implementation / "tasks.md").write_text("# Tasks\n")
            context = bounded_context(root, "feature.example.deliver").result["context"]
            workspace = context["feature_workspace"]
            self.assertEqual(workspace["feature_spec"], "specs/example/features/001-deliver/spec.md")
            self.assertEqual(workspace["implementation_artifacts"], [
                "specs/example/features/001-deliver/implementation/plan.md",
                "specs/example/features/001-deliver/implementation/tasks.md",
            ])
            self.assertEqual(context["evidence"][0]["status"], "unknown")
            self.assertIn("## Obligations", context["contracts"][0]["body"])
            self.assertNotIn("module.example.api.store", repr(workspace))


if __name__ == "__main__":
    unittest.main()
