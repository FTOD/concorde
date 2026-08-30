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
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde")],
                cwd=root,
                check=True,
                capture_output=True,
            )
            environment = os.environ.copy()
            environment.pop("VIRTUAL_ENV", None)
            environment["PATH"] = "/usr/local/bin:/usr/bin:/bin"
            workspace = root / "specs/example/architecture/modules/api/features/001-add-endpoint"
            implementation = workspace / "implementation"
            implementation.mkdir(parents=True)
            for artifact, template in (
                (workspace / "design.md", "spec-template"),
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
            self.assertEqual(list(workspace.glob("design.md")), [workspace / "design.md"])
            self.assertIn("Concorde Architecture Alignment", (workspace / "design.md").read_text())
            self.assertIn("Core feature diagram", (workspace / "design.md").read_text())
            self.assertIn("Concorde Architecture Gate", (implementation / "plan.md").read_text())
            self.assertIn("Evaluate feature-owned diagrams", (implementation / "plan.md").read_text())
            self.assertIn("Concorde Task Coverage", (implementation / "tasks.md").read_text())
            self.assertIn("For each required feature-owned diagram", (implementation / "tasks.md").read_text())
            for artifact in (workspace / "design.md", implementation / "plan.md", implementation / "tasks.md"):
                self.assertIn("meta.legend.mode", artifact.read_text(encoding="utf-8"))
            self.assertFalse((workspace / "plan.md").exists())
            self.assertFalse((workspace / "tasks.md").exists())
            self.assertFalse((workspace / "checklists").exists())
            self.assertFalse((root / "architecture").exists())
            for skill in ("speckit-specify", "speckit-clarify", "speckit-checklist", "speckit-implement"):
                content = (root / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("FEATURE_DIR/checklists", content)
                self.assertIn("CHECKLISTS_DIR", content)
            for skill in ("speckit-specify", "speckit-plan", "speckit-tasks", "speckit-implement"):
                content = (root / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("meta.legend.mode", content)


if __name__ == "__main__":
    unittest.main()
