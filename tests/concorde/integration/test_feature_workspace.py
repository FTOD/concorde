import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import propose_feature, select_feature  # noqa: E402


class FeatureWorkspaceIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(CONTEXT_PROJECT, root)
        return root

    def test_select_by_id_is_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            first = select_feature(root, "feature.example.deliver")
            self.assertEqual(first.status, "selected")
            self.assertEqual(first.result["workspace"]["implementation_state"], "absent")
            self.assertTrue(first.result["workspace"]["diagrams_dir"].endswith("/diagrams"))
            selected = root / ".specify/feature.json"
            first_bytes = selected.read_bytes()
            second = select_feature(root, "feature.example.deliver")
            self.assertEqual(second.status, "unchanged")
            self.assertEqual(selected.read_bytes(), first_bytes)
            self.assertEqual(json.loads(first_bytes)["feature_directory"], "specs/example/features/001-deliver")

    def test_select_requires_explicit_resume_for_nonempty_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            implementation = root / "specs/example/features/001-deliver/implementation"
            implementation.mkdir()
            (implementation / "plan.md").write_text("active", encoding="utf-8")
            blocked = select_feature(root, "feature.example.deliver")
            self.assertEqual(blocked.status, "conflict")
            self.assertFalse((root / ".specify/feature.json").exists())
            resumed = select_feature(root, "feature.example.deliver", resume=True)
            self.assertEqual(resumed.status, "selected")
            self.assertEqual(resumed.result["workspace"]["implementation_state"], "active")

    def test_invalid_selection_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            select_feature(root, "feature.example.deliver")
            state = root / ".specify/feature.json"
            before = state.read_bytes()
            result = select_feature(root, "feature.missing")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(state.read_bytes(), before)

    def test_create_and_select_immediate_subfeature(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(TWO_LEVEL_PROJECT, root)
            proposal = propose_feature(
                root,
                None,
                "feature.example.checkout.capture",
                "capture-payment",
                parent_feature="feature.example.checkout",
            )
            self.assertEqual(proposal.status, "proposal")
            self.assertEqual(proposal.result["workspace"]["workspace_kind"], "subfeature")
            self.assertTrue(proposal.result["workspace"]["feature_directory"].endswith("subfeatures/003-capture-payment"))
            child = select_feature(root, "feature.example.checkout.confirm", resume=True)
            self.assertEqual(child.status, "selected")
            self.assertEqual(child.result["workspace"]["workspace_kind"], "subfeature")
            self.assertEqual(child.result["workspace"]["parent_context"]["feature_id"], "feature.example.checkout")
            self.assertEqual([item["feature_id"] for item in child.result["workspace"]["siblings"]], ["feature.example.checkout.authorize"])

    def test_subfeature_cannot_parent_a_third_level(self):
        result = propose_feature(
            TWO_LEVEL_PROJECT,
            None,
            "feature.example.checkout.authorize.retry",
            "retry-authorization",
            parent_feature="feature.example.checkout.authorize",
        )
        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.findings[0].rule_id, "CONCORDE-WORKSPACE-014")


if __name__ == "__main__":
    unittest.main()
