import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class PresetWorkflowAcceptance(unittest.TestCase):
    def test_nested_module_workspace_uses_composed_single_spec(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde-core")],
                cwd=root,
                check=True,
                capture_output=True,
            )
            environment = os.environ.copy()
            environment.pop("VIRTUAL_ENV", None)
            environment["PATH"] = "/usr/local/bin:/usr/bin:/bin"
            workspace = root / "specs/example/modules/api/features/001-add-endpoint"
            implementation = workspace / "implementation"
            implementation.mkdir(parents=True)
            for artifact, template in (
                (workspace / "spec.md", "spec-template"),
                (implementation / "plan.md", "plan-template"),
                (implementation / "tasks.md", "tasks-template"),
            ):
                result = subprocess.run(
                    [str(root / ".specify/scripts/bash/resolve-template.sh"), template],
                    cwd=root,
                    env=environment,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                artifact.write_text(result.stdout)
            self.assertEqual(list(workspace.glob("spec.md")), [workspace / "spec.md"])
            self.assertIn("Concorde Architecture Alignment", (workspace / "spec.md").read_text())
            self.assertIn("Core feature diagram", (workspace / "spec.md").read_text())
            self.assertIn("Concorde Architecture Gate", (implementation / "plan.md").read_text())
            self.assertIn("Evaluate feature-owned diagrams", (implementation / "plan.md").read_text())
            self.assertIn("Concorde Task Coverage", (implementation / "tasks.md").read_text())
            self.assertIn("For each required feature-owned diagram", (implementation / "tasks.md").read_text())
            self.assertFalse((workspace / "plan.md").exists())
            self.assertFalse((workspace / "tasks.md").exists())
            self.assertFalse((root / "architecture").exists())


if __name__ == "__main__":
    unittest.main()
