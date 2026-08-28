import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

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
        self.assertEqual(module_context["current_module"]["summary"], "specs/example/module.md")
        self.assertEqual(module_context["current_module"]["design_reference"], "specs/example/design.md")
        self.assertEqual(module_context["current_module"]["view"], "specs/example/architecture.json")
        self.assertIn("specs/example/design.md", by_module.artifacts)
        self.assertNotIn("No implementation detail", repr(module_context))
        self.assertNotIn("Realization status", repr(feature_context))
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

    def test_context_on_legacy_tree_reports_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, root)
            feature = root / "specs/example/features/001-deliver"
            (feature / "design.md").rename(feature / "implementation.md")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            result = bounded_context(root, "feature.example.deliver")
            self.assertEqual(result.status, "success")
            self.assertIsNone(result.result["context"]["feature_workspace"])
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

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
            self.assertEqual(workspace["feature_tldr"], "specs/example/features/001-deliver/tldr.md")
            self.assertEqual(workspace["feature_design"], "specs/example/features/001-deliver/design.md")
            self.assertEqual(workspace["module_summary"], "specs/example/module.md")
            self.assertEqual(workspace["module_design"], "specs/example/design.md")
            self.assertIn("specs/example/features/001-deliver/design.md", workspace["durable_artifacts"])
            self.assertIn("specs/example/features/001-deliver/tldr.md", workspace["durable_artifacts"])
            self.assertNotIn("Realization status", repr(context))
            self.assertEqual(workspace["implementation_artifacts"], [
                "specs/example/features/001-deliver/implementation/plan.md",
                "specs/example/features/001-deliver/implementation/tasks.md",
            ])
            self.assertEqual(context["evidence"][0]["status"], "unknown")
            self.assertEqual(context["feature_diagrams"], [{
                "source": "specs/example/features/001-deliver/diagrams/delivery-sequence.json",
                "role": "supplemental",
                "kind": "sequence",
                "scenarios": ["scenario.example.deliver"],
                "output": "generated/architecture/example-delivery-sequence.html",
                "title": "Example Delivery Invocation",
            }])
            self.assertIn("specs/example/features/001-deliver/diagrams/delivery-sequence.json", workspace["durable_artifacts"])
            self.assertIn("## Obligations", context["contracts"][0]["body"])
            self.assertNotIn("module.example.api.store", repr(workspace))

    def test_parent_and_child_context_are_bounded_to_one_containment_level(self):
        parent = bounded_context(TWO_LEVEL_PROJECT, "feature.example.checkout").result["context"]
        self.assertEqual(
            [item["feature_id"] for item in parent["subfeatures"]],
            ["feature.example.checkout.authorize", "feature.example.checkout.confirm"],
        )
        self.assertNotIn("implementation/plan.md", repr(parent["subfeatures"]))
        self.assertEqual(
            parent["subfeatures"][0]["design"],
            "specs/example/features/001-checkout/subfeatures/001-authorize-payment/design.md",
        )
        self.assertNotIn("Realization status", repr(parent["subfeatures"]))
        child = bounded_context(TWO_LEVEL_PROJECT, "feature.example.checkout.authorize").result["context"]
        self.assertEqual(child["parent_feature"]["feature_id"], "feature.example.checkout")
        self.assertEqual(child["parent_feature"]["design"], "specs/example/features/001-checkout/design.md")
        self.assertEqual(child["parent_feature"]["tldr"], "specs/example/features/001-checkout/tldr.md")
        self.assertEqual(child["feature_workspace"]["parent_context"]["feature_design"], "specs/example/features/001-checkout/design.md")
        self.assertEqual([item["feature_id"] for item in child["siblings"]], ["feature.example.checkout.confirm"])
        self.assertNotIn("Confirmation preserves", repr(child["siblings"]))


if __name__ == "__main__":
    unittest.main()
