import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import select_feature  # noqa: E402


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

    def test_invalid_selection_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            select_feature(root, "feature.example.deliver")
            state = root / ".specify/feature.json"
            before = state.read_bytes()
            result = select_feature(root, "feature.missing")
            self.assertEqual(result.status, "invalid")
            self.assertEqual(state.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
