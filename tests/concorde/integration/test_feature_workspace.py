import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import (  # noqa: E402
    WorkspaceError,
    persist_selection,
    resolve_phase_paths,
    resolve_selected_workspace,
)

DELIVER = "specs/example/features/001-deliver"
CONFIRM = "specs/example/features/001-checkout/subfeatures/002-confirm-order"


class FeatureWorkspaceIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str, fixture: Path = CONTEXT_PROJECT) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(fixture, root)
        return root

    def test_persisting_the_standard_selection_is_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            self.assertEqual(persist_selection(root, DELIVER), "selected")
            selected = root / ".specify/feature.json"
            first_bytes = selected.read_bytes()
            self.assertEqual(json.loads(first_bytes), {"feature_directory": DELIVER})
            self.assertEqual(persist_selection(root, DELIVER), "unchanged")
            self.assertEqual(selected.read_bytes(), first_bytes)
            paths = resolve_selected_workspace(root)
            self.assertEqual(paths.feature_id, "feature.example.deliver")
            self.assertEqual(paths.providing_module, "module.example")
            self.assertEqual(paths.implementation_state, "absent")
            self.assertTrue(paths.diagrams_dir.endswith("/diagrams"))
            self.assertTrue(paths.plan.endswith("/implementation/plan.md"))

    def test_resolution_reports_an_active_attempt_without_gating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            implementation = root / DELIVER / "implementation"
            implementation.mkdir()
            (implementation / "plan.md").write_text("active", encoding="utf-8")
            persist_selection(root, DELIVER)
            paths = resolve_selected_workspace(root)
            self.assertEqual(paths.implementation_state, "active")
            self.assertEqual(paths.implementation_dir, f"{DELIVER}/implementation")

    def test_invalid_selection_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            persist_selection(root, DELIVER)
            state = root / ".specify/feature.json"
            before = state.read_bytes()
            with self.assertRaises(WorkspaceError):
                persist_selection(root, "specs/example/features/009-missing")
            with self.assertRaises(WorkspaceError):
                resolve_selected_workspace(root, "../outside")
            self.assertEqual(state.read_bytes(), before)
            self.assertEqual(resolve_selected_workspace(root).feature_directory, DELIVER)

    def test_selected_subfeature_exposes_parent_context_and_siblings_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, TWO_LEVEL_PROJECT)
            persist_selection(root, CONFIRM)
            child = resolve_selected_workspace(root)
            self.assertEqual(child.workspace_kind, "subfeature")
            self.assertEqual(child.feature_id, "feature.example.checkout.confirm")
            self.assertEqual(child.parent_context["feature_id"], "feature.example.checkout")
            self.assertEqual(child.parent_context["feature_directory"], "specs/example/features/001-checkout")
            self.assertEqual([item["feature_id"] for item in child.siblings], ["feature.example.checkout.authorize"])
            self.assertEqual(set(child.siblings[0]), {"feature_id", "title", "outcome", "evidence_status", "feature_directory"})

    def test_third_level_root_is_rejected(self):
        with self.assertRaises(WorkspaceError):
            resolve_phase_paths(TWO_LEVEL_PROJECT, f"{CONFIRM}/subfeatures/001-retry-confirmation")


if __name__ == "__main__":
    unittest.main()
