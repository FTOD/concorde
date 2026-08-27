import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_root, tree_hashes, write_selection
from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.feature_workspace import (  # noqa: E402
    WorkspaceError,
    phase_target,
    persist_selection,
    resolve_phase_paths,
    resolve_planned_phase_paths,
    resolve_selected_workspace,
)


class FeatureWorkspaceTests(unittest.TestCase):
    def test_routes_durable_and_temporal_phases_without_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = create_feature_root(project)
            paths = resolve_phase_paths(project, root.relative_to(project).as_posix())
            self.assertEqual(paths.feature_spec, "specs/example/features/001-deliver/spec.md")
            self.assertEqual(paths.feature_design, "specs/example/features/001-deliver/design.md")
            self.assertEqual(paths.contracts_dir, "specs/example/features/001-deliver/contracts")
            self.assertEqual(paths.checklists_dir, "specs/example/features/001-deliver/implementation/checklists")
            self.assertEqual(paths.diagrams_dir, "specs/example/features/001-deliver/diagrams")
            self.assertEqual(paths.plan, "specs/example/features/001-deliver/implementation/plan.md")
            self.assertEqual(paths.research, "specs/example/features/001-deliver/implementation/research.md")
            self.assertEqual(paths.data_model, "specs/example/features/001-deliver/implementation/data-model.md")
            self.assertEqual(paths.quickstart, "specs/example/features/001-deliver/implementation/quickstart.md")
            self.assertEqual(paths.tasks, "specs/example/features/001-deliver/implementation/tasks.md")
            self.assertEqual(paths.validation, "specs/example/features/001-deliver/implementation/validation.md")
            self.assertEqual(paths.implementation_state, "absent")
            self.assertEqual(phase_target(paths, "specify"), paths.feature_directory)
            self.assertEqual(phase_target(paths, "checklist"), paths.feature_directory)
            self.assertEqual(phase_target(paths, "plan"), paths.implementation_dir)
            self.assertEqual(phase_target(paths, "converge"), paths.implementation_dir)
            self.assertFalse((root / "plan.md").exists())
            self.assertFalse((root / "tasks.md").exists())
            self.assertFalse((root / "checklists").exists())

    def test_explicit_selection_precedes_persisted_state_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            first = create_feature_root(project)
            second = create_feature_root(project, "specs/example/features/002-observe", "feature.example.observe")
            state = write_selection(project, first.relative_to(project).as_posix())
            before = tree_hashes(project)
            resolved = resolve_selected_workspace(project, second.relative_to(project).as_posix())
            self.assertEqual(resolved.feature_directory, second.relative_to(project).as_posix())
            self.assertEqual(tree_hashes(project), before)
            self.assertEqual(json.loads(state.read_text())["feature_directory"], first.relative_to(project).as_posix())

    def test_specify_can_resolve_an_approved_missing_feature_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, project)
            planned = "specs/example/modules/api/features/002-observe-health"
            paths = resolve_planned_phase_paths(project, planned)
            self.assertEqual(paths.feature_spec, f"{planned}/spec.md")
            self.assertEqual(paths.feature_design, f"{planned}/design.md")
            self.assertEqual(paths.checklists_dir, f"{planned}/implementation/checklists")
            self.assertEqual(paths.implementation_state, "absent")
            self.assertFalse((project / planned).exists())
            with self.assertRaises(WorkspaceError):
                resolve_planned_phase_paths(project, "outside/002-observe-health")

            legacy = project / "specs/example/features/001-deliver/design.md"
            legacy.unlink()
            repair_paths = resolve_selected_workspace(
                project,
                "specs/example/features/001-deliver",
                allow_missing_spec=True,
            )
            self.assertEqual(repair_paths.feature_design, "specs/example/features/001-deliver/design.md")

    def test_atomic_persistence_is_idempotent_and_rejects_unsafe_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = create_feature_root(project)
            relative = root.relative_to(project).as_posix()
            self.assertEqual(persist_selection(project, relative), "selected")
            first = (project / ".specify/feature.json").read_bytes()
            self.assertEqual(persist_selection(project, relative), "unchanged")
            self.assertEqual((project / ".specify/feature.json").read_bytes(), first)
            with self.assertRaises(WorkspaceError):
                resolve_phase_paths(project, "../outside")


if __name__ == "__main__":
    unittest.main()
