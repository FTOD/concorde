from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_file, write_selection
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


PHASES = {
    "analyze": "attempt",
    "checklist": "feature",
    "clarify": "feature",
    "converge": "attempt",
    "fast-loop": "feature",
    "implement": "attempt",
    "plan": "attempt",
    "specify": "feature",
    "tasks": "attempt",
    "taskstoissues": "attempt",
}


class CleanPhaseMatrixIntegrationTests(unittest.TestCase):
    def test_every_phase_adapter_routes_one_native_selected_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            feature = create_feature_file(root)
            write_selection(root, feature.relative_to(root).as_posix())
            install = subprocess.run(
                [
                    sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"),
                    "--target", str(root), "--integration", "codex", "--apply", "--format", "json",
                ],
                text=True,
                capture_output=True,
                env=environment,
            )
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            adapter = root / ".concorde/framework/scripts/workspace.py"
            for phase, root_kind in PHASES.items():
                with self.subTest(phase=phase):
                    result = subprocess.run(
                        [sys.executable, str(adapter), "--project-root", str(root), "--phase", phase],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                    value = json.loads(result.stdout)
                    self.assertEqual(value["schema_version"], 13)
                    self.assertEqual(value["workspace"]["feature_path"], feature.relative_to(root).as_posix())
                    expected = value["workspace"]["feature_path"] if root_kind == "feature" else value["workspace"]["attempt_dir"]
                    self.assertEqual(value["phase_root"], expected)

    def test_every_phase_skill_names_the_same_phase(self):
        for phase in PHASES:
            path = REPOSITORY_ROOT / ".agents/skills" / f"concorde-{phase}/SKILL.md"
            with self.subTest(phase=phase):
                self.assertTrue(path.is_file())
                body = path.read_text()
                if phase == "plan":
                    self.assertIn('kind: "operation"', body)
                    self.assertIn("operations/concorde-plan/operation.py", body)
                    self.assertNotIn("scripts/workspace.py --phase plan", body)
                else:
                    self.assertIn(f"scripts/workspace.py --phase {phase}", body)


if __name__ == "__main__":
    unittest.main()
