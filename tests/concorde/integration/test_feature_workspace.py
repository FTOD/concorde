import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import write_complete_attempt
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import WorkspaceError, persist_selection, resolve_phase_paths, resolve_selected_workspace  # noqa: E402


DELIVER = "specs/example/features/001-deliver.md"


class FeatureWorkspaceIntegrationTests(unittest.TestCase):
    def project_copy(self, temporary: str, fixture: Path = CONTEXT_PROJECT) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(fixture, root)
        return root

    def test_selection_is_atomic_idempotent_and_resolves_protocol_twelve_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            self.assertEqual(persist_selection(root, DELIVER), "selected")
            selected = root / ".concorde/feature.json"
            first = selected.read_bytes()
            self.assertEqual(json.loads(first), {"feature_path": DELIVER})
            self.assertEqual(persist_selection(root, DELIVER), "unchanged")
            self.assertEqual(selected.read_bytes(), first)
            paths = resolve_selected_workspace(root)
            self.assertEqual(paths.feature_id, "feature.example.deliver")
            self.assertEqual(paths.module_architecture, "specs/example/architecture.md")
            self.assertEqual(paths.attempt_dir, ".concorde/attempts/feature.example.deliver")
            self.assertEqual(paths.reflections, ".concorde/reflections")
            self.assertEqual(paths.attempt_state, "absent")

    def test_related_flat_features_are_bounded_and_exclude_attempt_bodies(self):
        paths = resolve_phase_paths(TWO_LEVEL_PROJECT, "specs/example/features/004-confirm-order.md")
        self.assertEqual([item["feature_id"] for item in paths.related_features], ["feature.example.checkout", "feature.example.checkout.authorize"])
        self.assertNotIn("Flat Feature Attempt", repr(paths.related_features))
        self.assertFalse(hasattr(paths, "parent_context"))
        self.assertFalse(hasattr(paths, "workspace_kind"))

    def test_complete_attempt_is_reported_without_gating_or_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            write_complete_attempt(root / DELIVER)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            paths = resolve_phase_paths(root, DELIVER)
            self.assertEqual(paths.attempt_state, "complete")
            self.assertEqual(before, {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()})

    def test_invalid_selection_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            persist_selection(root, DELIVER)
            state = root / ".concorde/feature.json"
            before = state.read_bytes()
            with self.assertRaises(WorkspaceError):
                persist_selection(root, "specs/example/features/009-missing.md")
            self.assertEqual(state.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
