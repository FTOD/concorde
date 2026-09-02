import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class CodexSkillsAcceptance(unittest.TestCase):
    def test_profile7_preset_extension_and_agent_assets_materialize_in_codex_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root, check=True, capture_output=True,
            )
            subprocess.run(
                ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
                cwd=root, check=True, capture_output=True,
            )
            subprocess.run(
                ["specify", "preset", "add", "--dev", str(REPOSITORY_ROOT / "presets/concorde")],
                cwd=root, check=True, capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(root / ".specify/extensions/concorde/scripts/python/concorde.py"),
                    "--project-root", str(root), "agent-assets", "sync", "--integration", "codex",
                    "--concorde-version", "0.9.0",
                ],
                cwd=root, check=True, capture_output=True,
            )

            extension_names = {path.parent.name for path in (root / ".agents/skills").glob("speckit-concorde-*/SKILL.md")}
            self.assertEqual(extension_names, {
                "speckit-concorde-init", "speckit-concorde-deliver", "speckit-concorde-context",
                "speckit-concorde-validate", "speckit-concorde-ask",
            })
            for phase in ("specify", "clarify", "checklist", "plan", "tasks", "implement", "analyze", "converge", "taskstoissues", "fast-loop"):
                body = (root / f".agents/skills/speckit-{phase}/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("Protocol 12", body, phase)
                self.assertNotIn(str(REPOSITORY_ROOT), body)
            delivery = (root / ".agents/skills/speckit-concorde-deliver/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Delivery Proposal 8", delivery)
            self.assertNotIn(str(REPOSITORY_ROOT), delivery)

            source = (REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.ask.md").read_text(encoding="utf-8")
            installed = (root / ".agents/skills/speckit-concorde-ask/SKILL.md").read_text(encoding="utf-8")
            self.assertIn(source.split("---", 2)[2].strip(), installed)
            triage = (root / ".agents/skills/reflections-triage/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("reflection-triage/v3", triage)
            self.assertIn("--allocate-id", triage)
            self.assertIn("--remove-merged", triage)
            self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
            self.assertTrue((root / ".codex/agents/reflection_implementer.toml").is_file())


if __name__ == "__main__":
    unittest.main()
