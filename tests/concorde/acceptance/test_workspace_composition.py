import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.installed_command_surface import CONCORDE_COMMANDS, registered_artifact
from tests.concorde.support.paths import REPOSITORY_ROOT


class WorkspaceCompositionAcceptance(unittest.TestCase):
    def test_public_preset_composes_routing_in_skills_and_slash_modes(self):
        for integration, skills, artifact in (
            ("codex", True, ".agents/skills/speckit-plan/SKILL.md"),
            ("gemini", False, ".gemini/commands/speckit.plan.toml"),
        ):
            with self.subTest(integration=integration), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                init = ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", integration]
                if skills:
                    init.append("--integration-options=--skills")
                subprocess.run(init, cwd=root, check=True, capture_output=True)
                subprocess.run(
                    ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
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
                rendered = (root / artifact).read_text(encoding="utf-8")
                self.assertIn("Concorde Installed Workspace Gate", rendered)
                self.assertIn("workspace.attempt_dir", rendered)
                self.assertIn("attempt_state", rendered)
                self.assertIn(".specify/extensions/concorde/scripts/python/workspace.py", rendered)
                self.assertNotIn("Concorde selected-workspace routing", rendered)
                self.assertTrue((root / ".specify/extensions/concorde/scripts/python/workspace.py").is_file())
                # Every phase after specification carries the byte-identical Reflection Recording block.
                block_start = rendered.index("## Reflection Recording")
                block = rendered[block_start:rendered.index("## Mandatory Post-Execution Hooks", block_start)]
                self.assertIn("workspace.reflections", block)
                self.assertIn("Reflections added:", block)
                for phase in ("tasks", "implement", "analyze", "converge"):
                    surface = registered_artifact(root, integration, f"speckit.{phase}").read_text(encoding="utf-8")
                    self.assertIn(block, surface, phase)
                analyze_surface = registered_artifact(root, integration, "speckit.analyze").read_text(encoding="utf-8")
                self.assertIn("READ-ONLY EXCEPT REFLECTION RECORDING", analyze_surface)
                self.assertIn("Every other file MUST remain byte-identical", analyze_surface)
                self.assertIn("no recordable problem MUST make zero filesystem changes", analyze_surface)
                self.assertNotIn("**STRICTLY READ-ONLY**", analyze_surface)
                implement_surface = registered_artifact(root, integration, "speckit.implement").read_text(encoding="utf-8")
                self.assertIn("`Effect: blocked`", implement_surface)
                resolved = subprocess.run(["specify", "preset", "resolve", "reflections-template"], cwd=root, check=True, capture_output=True, text=True)
                self.assertIn("reflections-template.md", resolved.stdout.replace("\n", ""))
                surfaces = {registered_artifact(root, integration, command) for command in CONCORDE_COMMANDS}
                self.assertEqual(len(surfaces), 5)
                self.assertTrue(all(path.is_file() for path in surfaces))


if __name__ == "__main__":
    unittest.main()
