import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import write_accepted_root
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, TWO_LEVEL_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import (  # noqa: E402
    WorkspaceError,
    persist_selection,
    phase_target,
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
            self.assertEqual(paths.attempt_state, "absent")
            self.assertTrue(paths.diagrams_dir.endswith("/diagrams"))
            self.assertTrue(paths.plan.endswith("/attempt/plan.md"))

    def test_resolution_reports_an_active_attempt_without_gating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            attempt = root / DELIVER / "attempt"
            attempt.mkdir()
            (attempt / "plan.md").write_text("active", encoding="utf-8")
            persist_selection(root, DELIVER)
            paths = resolve_selected_workspace(root)
            self.assertEqual(paths.attempt_state, "active")
            self.assertEqual(paths.attempt_dir, f"{DELIVER}/attempt")

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
            self.assertEqual(set(child.siblings[0]), {"feature_id", "title", "outcome", "evidence_status", "feature_directory", "abstract", "design", "implementation"})
        self.assertEqual(child.siblings[0]["design"], child.siblings[0]["feature_directory"] + "/design.md")
        self.assertEqual(child.siblings[0]["abstract"], child.siblings[0]["feature_directory"] + "/abstract.md")

    def test_resume_after_acceptance_starts_a_fresh_attempt_from_durable_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = write_accepted_root(project, "specs/example/features/001-deliver", "feature.example.deliver")
            relative = root.relative_to(project).as_posix()
            accepted = resolve_phase_paths(project, relative)
            self.assertEqual(accepted.attempt_state, "absent")
            self.assertEqual(accepted.feature_implementation, f"{relative}/implementation.md")
            self.assertIn("Accepted fixture milestone", (root / "implementation.md").read_text(encoding="utf-8"))
            self.assertEqual(phase_target(accepted, "plan"), f"{relative}/attempt")
            (root / "attempt").mkdir()
            (root / "attempt/plan.md").write_text("# Plan for a later attempt\n", encoding="utf-8")
            resumed = resolve_phase_paths(project, relative)
            self.assertEqual(resumed.attempt_state, "active")
            self.assertEqual(resumed.feature_implementation, accepted.feature_implementation)
            self.assertEqual(resumed.module_design, accepted.module_design)
            for name in ("plan.md", "tasks.md", "checklists"):
                self.assertFalse((root / name).exists(), name)

    def test_resume_after_child_acceptance_keeps_parent_pair_and_module_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, TWO_LEVEL_PROJECT)
            child = root / "specs/example/features/001-checkout/subfeatures/001-authorize-payment"
            shutil.rmtree(child / "attempt")
            (child / "implementation.md").write_text(
                "# Feature Implementation: Authorize Payment\n\n**Realization status**: Accepted.\n", encoding="utf-8"
            )
            paths = resolve_phase_paths(root, child.relative_to(root).as_posix())
            self.assertEqual(paths.workspace_kind, "subfeature")
            self.assertEqual(paths.attempt_state, "absent")
            self.assertEqual(paths.parent_context["feature_implementation"], "specs/example/features/001-checkout/implementation.md")
            self.assertEqual(paths.parent_context["feature_abstract"], "specs/example/features/001-checkout/abstract.md")
            self.assertEqual(paths.module_summary, "specs/example/module.md")
            self.assertEqual(paths.module_design, "specs/example/design.md")
            (child / "attempt").mkdir()
            (child / "attempt/plan.md").write_text("# Next attempt\n", encoding="utf-8")
            self.assertEqual(resolve_phase_paths(root, child.relative_to(root).as_posix()).attempt_state, "active")

    def test_third_level_root_is_rejected(self):
        with self.assertRaises(WorkspaceError):
            resolve_phase_paths(TWO_LEVEL_PROJECT, f"{CONFIRM}/subfeatures/001-retry-confirmation")


if __name__ == "__main__":
    unittest.main()
