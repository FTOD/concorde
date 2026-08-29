import json
import os
import subprocess
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


FEATURE_RELATIVE = "specs/concorde/features/001-concorde-workflow"


class AttemptWorkspaceIntegration(unittest.TestCase):
    def test_feature_paths_separate_durable_intent_from_delivery_attempt(self):
        completed = subprocess.run(
            [
                str(REPOSITORY_ROOT / ".venv/bin/python"),
                str(REPOSITORY_ROOT / "extensions/concorde/scripts/python/workspace.py"),
                "--phase",
                "plan",
                "--feature-directory",
                FEATURE_RELATIVE,
            ],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        paths = payload["workspace"]
        feature_root = FEATURE_RELATIVE
        attempt = feature_root + "/attempt"

        self.assertEqual(payload["schema_version"], 8)
        self.assertEqual(paths["feature_design"], feature_root + "/design.md")
        self.assertEqual(paths["feature_implementation"], feature_root + "/implementation.md")
        self.assertEqual(paths["attempt_dir"], attempt)
        self.assertEqual(paths["plan"], attempt + "/plan.md")
        self.assertEqual(paths["tasks"], attempt + "/tasks.md")
        self.assertEqual(paths["contracts_dir"], feature_root + "/contracts")
        self.assertEqual(paths["checklists_dir"], attempt + "/checklists")
        self.assertEqual(paths["diagrams_dir"], feature_root + "/diagrams")
        feature_path = REPOSITORY_ROOT / feature_root
        self.assertFalse((feature_path / "plan.md").exists())
        self.assertFalse((feature_path / "tasks.md").exists())
        self.assertFalse((feature_path / "checklists").exists())

    def test_adapter_exposes_the_project_reflection_log_and_open_count(self):
        completed = subprocess.run(
            [str(REPOSITORY_ROOT / ".venv/bin/python"), str(REPOSITORY_ROOT / "extensions/concorde/scripts/python/workspace.py"), "--phase", "plan", "--feature-directory", FEATURE_RELATIVE],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["workspace"]["reflections"], "specs/concorde/reflections.md")
        self.assertIsInstance(payload["workspace"]["reflections_open"], int)
        self.assertEqual(payload["phase_root"], FEATURE_RELATIVE + "/attempt")

    def test_resume_after_acceptance_starts_a_fresh_attempt_from_the_trio(self):
        import sys
        import tempfile
        from pathlib import Path

        from tests.concorde.support.feature_workspace import write_accepted_root, write_selection
        from tests.concorde.support.paths import RUNTIME_ROOT

        sys.path.insert(0, str(RUNTIME_ROOT))
        from concorde.feature_workspace import resolve_phase_paths  # noqa: E402
        from concorde.validation.layout import FORBIDDEN_ROOT_FILES  # noqa: E402

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = write_accepted_root(project, "specs/example/features/001-deliver", "feature.example.deliver")
            write_selection(project, "specs/example/features/001-deliver")
            accepted = resolve_phase_paths(project, "specs/example/features/001-deliver")
            self.assertEqual(accepted.attempt_state, "absent")
            self.assertEqual(accepted.feature_abstract, "specs/example/features/001-deliver/abstract.md")
            self.assertEqual(accepted.feature_implementation, "specs/example/features/001-deliver/implementation.md")
            self.assertIn("Accepted fixture milestone", (root / "implementation.md").read_text(encoding="utf-8"))
            (root / "attempt").mkdir()
            (root / "attempt/plan.md").write_text("# Plan\n", encoding="utf-8")
            resumed = resolve_phase_paths(project, "specs/example/features/001-deliver")
            self.assertEqual(resumed.attempt_state, "active")
            self.assertEqual(resumed.plan, "specs/example/features/001-deliver/attempt/plan.md")
            self.assertEqual((resumed.feature_abstract, resumed.feature_design, resumed.feature_implementation), (accepted.feature_abstract, accepted.feature_design, accepted.feature_implementation))
            self.assertFalse(any((root / name).exists() for name in FORBIDDEN_ROOT_FILES))


if __name__ == "__main__":
    unittest.main()
