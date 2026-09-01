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
            module = root / "specs/example/modules/api"
            feature = module / "features/001-add-endpoint.md"
            attempt = root / ".concorde/attempts/feature.example.api.add-endpoint"
            feature.parent.mkdir(parents=True)
            attempt.mkdir(parents=True)
            for artifact, template in (
                (feature, "spec-template"),
                (attempt / "plan.md", "plan-template"),
                (attempt / "tasks.md", "tasks-template"),
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
            self.assertEqual(list((module / "features").glob("*.md")), [feature])
            self.assertIn("Concorde Feature Profile", feature.read_text())
            self.assertIn("Architecture Zoom", feature.read_text())
            self.assertIn("Concorde Architecture Gate", (attempt / "plan.md").read_text())
            self.assertIn("architecture-owned diagram", (attempt / "plan.md").read_text())
            self.assertIn("Concorde Task Coverage", (attempt / "tasks.md").read_text())
            self.assertIn("architecture-owned diagrams", (attempt / "tasks.md").read_text())
            for artifact in (feature, attempt / "plan.md", attempt / "tasks.md"):
                self.assertIn("meta.legend.mode", artifact.read_text(encoding="utf-8"))
            self.assertFalse((module / "features/001-add-endpoint").exists())
            self.assertFalse((module / "attempts/001-add-endpoint").exists())
            self.assertFalse((module / "attempt/plan.md").exists())
            self.assertFalse((root / "architecture").exists())
            for skill in ("speckit-specify", "speckit-clarify", "speckit-checklist", "speckit-implement"):
                content = (root / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("FEATURE_DIR/checklists", content)
                self.assertIn("checklists_dir", content.lower())
            for skill in ("speckit-specify", "speckit-plan", "speckit-tasks", "speckit-implement"):
                content = (root / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("meta.legend.mode", content)


if __name__ == "__main__":
    unittest.main()
