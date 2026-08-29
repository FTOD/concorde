import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_root, reflection_entry, tree_hashes, write_reflection_log, write_selection
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
    def test_reflection_log_path_is_project_level_and_open_count_is_per_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = create_feature_root(project)
            other = create_feature_root(project, "specs/example/features/002-other", "feature.example.other")
            paths = resolve_phase_paths(project, root.relative_to(project).as_posix())
            self.assertEqual(paths.reflections, "specs/example/reflections.md")
            self.assertEqual(paths.reflections_open, 0)
            self.assertIn("reflections", paths.to_dict())
            write_reflection_log(project, [reflection_entry("R-001"), reflection_entry("R-002", status="dismissed"), reflection_entry("R-003", feature="feature.example.other")])
            paths = resolve_phase_paths(project, root.relative_to(project).as_posix())
            self.assertEqual(paths.reflections_open, 1)
            self.assertEqual(resolve_phase_paths(project, other.relative_to(project).as_posix()).reflections_open, 1)
            planned = resolve_planned_phase_paths(project, "specs/example/features/003-planned")
            self.assertEqual(planned.reflections, "specs/example/reflections.md")
            self.assertEqual(planned.reflections_open, 0)

    def test_routes_durable_and_temporal_phases_without_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = create_feature_root(project)
            paths = resolve_phase_paths(project, root.relative_to(project).as_posix())
            self.assertEqual(paths.feature_spec, "specs/example/features/001-deliver/spec.md")
            self.assertEqual(paths.feature_tldr, "specs/example/features/001-deliver/tldr.md")
            self.assertEqual(paths.feature_design, "specs/example/features/001-deliver/design.md")
            self.assertEqual(paths.module_summary, "specs/example/module.md")
            self.assertEqual(paths.module_design, "specs/example/design.md")
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
            self.assertEqual(paths.feature_tldr, f"{planned}/tldr.md")
            self.assertEqual(paths.feature_design, f"{planned}/design.md")
            self.assertEqual(paths.module_summary, "specs/example/modules/api/module.md")
            self.assertEqual(paths.module_design, "specs/example/modules/api/design.md")
            self.assertEqual(paths.checklists_dir, f"{planned}/implementation/checklists")
            self.assertEqual(paths.implementation_state, "absent")
            self.assertFalse((project / planned).exists())
            with self.assertRaises(WorkspaceError):
                resolve_planned_phase_paths(project, "outside/002-observe-health")

            realization = project / "specs/example/features/001-deliver/design.md"
            realization.unlink()
            repair_paths = resolve_selected_workspace(
                project,
                "specs/example/features/001-deliver",
                allow_missing_spec=True,
            )
            self.assertEqual(repair_paths.feature_design, "specs/example/features/001-deliver/design.md")

    def test_legacy_and_ambiguous_realization_names_are_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = create_feature_root(project)
            relative = root.relative_to(project).as_posix()
            (root / "design.md").rename(root / "implementation.md")
            before = tree_hashes(project)
            with self.assertRaisesRegex(WorkspaceError, "legacy accepted-realization name implementation.md"):
                resolve_phase_paths(project, relative)
            (root / "design.md").write_text("# Feature Design Reference: Fixture\n", encoding="utf-8")
            with self.assertRaisesRegex(WorkspaceError, "both implementation.md and design.md"):
                resolve_phase_paths(project, relative)
            (root / "implementation.md").unlink()
            self.assertEqual(resolve_phase_paths(project, relative).feature_design, f"{relative}/design.md")
            before.pop("specs/example/features/001-deliver/implementation.md")
            self.assertEqual({k: v for k, v in tree_hashes(project).items() if k != "specs/example/features/001-deliver/design.md"},
                             {k: v for k, v in before.items() if k != "specs/example/features/001-deliver/design.md"})
            (root / "tldr.md").unlink()
            with self.assertRaisesRegex(WorkspaceError, "has no tldr.md"):
                resolve_phase_paths(project, relative)

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
