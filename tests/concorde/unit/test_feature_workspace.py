import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import attempt_path, create_feature_file, reflection_entry, tree_hashes, write_complete_attempt, write_reflection_log, write_selection
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


REMOVED_FIELDS = {
    "workspace_kind", "feature_abstract", "feature_implementation", "module_summary", "module_design",
    "contracts_dir", "diagrams_dir", "parent_context", "siblings", "feature_" + "directory", "feature_" + "design",
}


class FeatureWorkspaceTests(unittest.TestCase):
    def test_protocol_twelve_exposes_feature_architecture_control_state_and_executable_context_only(self):
        paths = resolve_phase_paths(CONTEXT_PROJECT, "specs/example/features/001-deliver.md")
        payload = paths.to_dict()
        self.assertEqual(paths.feature_path, "specs/example/features/001-deliver.md")
        self.assertEqual(paths.module_architecture, "specs/example/architecture.md")
        self.assertEqual(paths.attempt_dir, ".concorde/attempts/feature.example.deliver")
        self.assertEqual(paths.checklists_dir, paths.attempt_dir + "/checklists")
        self.assertEqual(paths.reflections, ".concorde/reflections/log.md")
        self.assertEqual(paths.executable_context, {"source_roots": (), "test_roots": ()})
        self.assertTrue(REMOVED_FIELDS.isdisjoint(payload))
        self.assertEqual(phase_target(paths, "specify"), paths.feature_path)
        self.assertEqual(phase_target(paths, "plan"), paths.attempt_dir)

    def test_child_module_workspace_has_bounded_ancestry_and_related_feature_summaries(self):
        paths = resolve_phase_paths(CONTEXT_PROJECT, "specs/example/modules/api/features/001-invoke.md")
        self.assertEqual(paths.providing_module, "module.example.api")
        self.assertEqual(paths.module_architecture, "specs/example/modules/api/architecture.md")
        self.assertEqual([item["module_id"] for item in paths.module_ancestry], ["module.example"])
        self.assertEqual([item["feature_id"] for item in paths.related_features], ["feature.example.deliver"])
        self.assertEqual(set(paths.related_features[0]), {"feature_id", "title", "module", "feature_path", "outcome", "evidence_status", "reflections_open"})
        self.assertNotIn("attempt", repr(paths.related_features))

    def test_attempt_state_distinguishes_absent_active_and_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            feature = create_feature_file(project)
            relative = feature.relative_to(project).as_posix()
            self.assertEqual(resolve_phase_paths(project, relative).attempt_state, "absent")
            attempt = attempt_path(feature)
            attempt.mkdir(parents=True)
            (attempt / "plan.md").write_text("# Plan\n", encoding="utf-8")
            self.assertEqual(resolve_phase_paths(project, relative).attempt_state, "active")
            write_complete_attempt(feature)
            self.assertEqual(resolve_phase_paths(project, relative).attempt_state, "complete")

    def test_reflections_are_root_scoped_and_counted_per_feature(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            first = create_feature_file(project)
            second = create_feature_file(project, "specs/example/features/002-other.md", "feature.example.other")
            write_reflection_log(project, [reflection_entry("R-001"), reflection_entry("R-002", feature="feature.example.other")])
            self.assertEqual(resolve_phase_paths(project, first.relative_to(project).as_posix()).reflections_open, 1)
            self.assertEqual(resolve_phase_paths(project, second.relative_to(project).as_posix()).reflections_open, 1)

    def test_planned_feature_first_pass_has_unresolved_control_paths_without_creating_files(self):
        planned = "specs/example/modules/api/features/002-observe-health.md"
        before = tree_hashes(CONTEXT_PROJECT)
        paths = resolve_planned_phase_paths(CONTEXT_PROJECT, planned)
        self.assertEqual(paths.feature_path, planned)
        self.assertEqual(paths.providing_module, "module.example.api")
        self.assertEqual(paths.module_architecture, "specs/example/modules/api/architecture.md")
        self.assertIsNone(paths.feature_id)
        self.assertEqual(paths.attempt_state, "unresolved")
        for field in (
            "attempt_dir", "checklists_dir", "plan", "research", "data_model",
            "quickstart", "tasks", "validation",
        ):
            self.assertIsNone(getattr(paths, field), field)
        self.assertEqual(phase_target(paths, "specify"), planned)
        with self.assertRaisesRegex(WorkspaceError, "stable feature ID"):
            phase_target(paths, "plan")
        self.assertEqual(tree_hashes(CONTEXT_PROJECT), before)
        with self.assertRaises(WorkspaceError):
            resolve_planned_phase_paths(CONTEXT_PROJECT, "outside/002-observe-health")

    def test_planned_feature_explicit_id_preflight_returns_absent_paths_and_rejects_adoption(self):
        planned = "specs/example/modules/api/features/002-observe-health.md"
        feature_id = "feature.example.api.observe-health"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(CONTEXT_PROJECT, project)
            paths = resolve_planned_phase_paths(project, planned, feature_id)
            self.assertEqual(paths.feature_id, feature_id)
            self.assertEqual(paths.attempt_state, "absent")
            self.assertEqual(paths.attempt_dir, f".concorde/attempts/{feature_id}")
            self.assertEqual(paths.checklists_dir, f".concorde/attempts/{feature_id}/checklists")

            orphan = project / paths.attempt_dir
            orphan.mkdir(parents=True)
            with self.assertRaisesRegex(WorkspaceError, "adopt"):
                resolve_planned_phase_paths(project, planned, feature_id)

            with self.assertRaisesRegex(WorkspaceError, "already exists"):
                resolve_planned_phase_paths(project, planned, "feature.example.deliver")
            with self.assertRaises(WorkspaceError):
                resolve_planned_phase_paths(project, planned, "feature.example..unsafe")

    def test_explicit_selection_precedes_persisted_state_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            first = create_feature_file(project)
            second = create_feature_file(project, "specs/example/features/002-observe.md", "feature.example.observe")
            state = write_selection(project, first.relative_to(project).as_posix())
            before = tree_hashes(project)
            resolved = resolve_selected_workspace(project, second.relative_to(project).as_posix())
            self.assertEqual(resolved.feature_path, second.relative_to(project).as_posix())
            self.assertEqual(tree_hashes(project), before)
            self.assertEqual(json.loads(state.read_text()), {"feature_path": first.relative_to(project).as_posix()})

    def test_atomic_persistence_is_idempotent_and_rejects_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            feature = create_feature_file(project)
            relative = feature.relative_to(project).as_posix()
            self.assertEqual(persist_selection(project, relative), "selected")
            first = (project / ".specify/feature.json").read_bytes()
            self.assertEqual(persist_selection(project, relative), "unchanged")
            self.assertEqual((project / ".specify/feature.json").read_bytes(), first)
            with self.assertRaises(WorkspaceError):
                resolve_phase_paths(project, "../outside")

    def test_stable_id_resolves_but_persistence_canonicalizes_to_feature_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            feature = create_feature_file(project)
            self.assertEqual(resolve_phase_paths(project, "feature.example.deliver").feature_path, feature.relative_to(project).as_posix())
            self.assertEqual(persist_selection(project, "feature.example.deliver"), "selected")
            self.assertEqual(json.loads((project / ".specify/feature.json").read_text(encoding="utf-8")), {"feature_path": feature.relative_to(project).as_posix()})

    def test_legacy_selection_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            create_feature_file(project)
            state = project / ".specify/feature.json"
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({"feature_" + "directory": "specs/example/features/001-deliver"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(WorkspaceError, "feature_path"):
                resolve_selected_workspace(project)


if __name__ == "__main__":
    unittest.main()
