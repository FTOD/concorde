import json
import os
import subprocess
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


FEATURE_RELATIVE = "specs/concorde/features/001-concorde-workflow"


class ImplementationWorkspaceIntegration(unittest.TestCase):
    def test_feature_paths_separate_durable_intent_from_delivery_attempt(self):
        environment = os.environ.copy()
        environment["SPECIFY_FEATURE_DIRECTORY"] = FEATURE_RELATIVE

        completed = subprocess.run(
            [
                str(REPOSITORY_ROOT / ".specify/scripts/bash/check-prerequisites.sh"),
                "--json",
                "--paths-only",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = json.loads(completed.stdout)
        feature_root = REPOSITORY_ROOT / FEATURE_RELATIVE
        implementation = feature_root / "implementation"

        self.assertEqual(paths["FEATURE_SPEC"], str(feature_root / "spec.md"))
        self.assertEqual(paths["IMPLEMENTATION_DIR"], str(implementation))
        self.assertEqual(paths["IMPL_PLAN"], str(implementation / "plan.md"))
        self.assertEqual(paths["TASKS"], str(implementation / "tasks.md"))
        self.assertEqual(paths["CONTRACTS_DIR"], str(feature_root / "contracts"))
        self.assertEqual(paths["CHECKLISTS_DIR"], str(implementation / "checklists"))
        self.assertEqual(paths["DIAGRAMS_DIR"], str(feature_root / "diagrams"))
        self.assertFalse((feature_root / "plan.md").exists())
        self.assertFalse((feature_root / "tasks.md").exists())
        self.assertFalse((feature_root / "checklists").exists())
        self.assertEqual(paths["FEATURE_DESIGN"], str(feature_root / "design.md"))
        self.assertNotIn("FEATURE_IMPLEMENTATION", paths)

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
        self.assertEqual(payload["phase_root"], FEATURE_RELATIVE + "/implementation")

    def test_resume_after_hardening_starts_a_fresh_attempt_from_the_trio(self):
        import sys
        import tempfile
        from pathlib import Path

        from tests.concorde.support.feature_workspace import write_hardened_root, write_selection
        from tests.concorde.support.paths import RUNTIME_ROOT

        sys.path.insert(0, str(RUNTIME_ROOT))
        from concorde.feature_workspace import resolve_phase_paths  # noqa: E402
        from concorde.validation.layout import FORBIDDEN_ROOT_FILES  # noqa: E402

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            root = write_hardened_root(project, "specs/example/features/001-deliver", "feature.example.deliver")
            write_selection(project, "specs/example/features/001-deliver")
            hardened = resolve_phase_paths(project, "specs/example/features/001-deliver")
            self.assertEqual(hardened.implementation_state, "absent")
            self.assertEqual(hardened.feature_tldr, "specs/example/features/001-deliver/tldr.md")
            self.assertEqual(hardened.feature_design, "specs/example/features/001-deliver/design.md")
            self.assertIn("Hardened fixture milestone", (root / "design.md").read_text(encoding="utf-8"))
            (root / "implementation").mkdir()
            (root / "implementation/plan.md").write_text("# Plan\n", encoding="utf-8")
            resumed = resolve_phase_paths(project, "specs/example/features/001-deliver")
            self.assertEqual(resumed.implementation_state, "active")
            self.assertEqual(resumed.plan, "specs/example/features/001-deliver/implementation/plan.md")
            self.assertEqual((resumed.feature_tldr, resumed.feature_spec, resumed.feature_design), (hardened.feature_tldr, hardened.feature_spec, hardened.feature_design))
            self.assertFalse(any((root / name).exists() for name in FORBIDDEN_ROOT_FILES))


if __name__ == "__main__":
    unittest.main()
