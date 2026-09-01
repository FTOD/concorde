import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class CodexSkillsAcceptance(unittest.TestCase):
    def test_five_commands_register_in_codex_skills_mode_with_ask_parity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "codex", "--integration-options=--skills"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["specify", "extension", "add", str(REPOSITORY_ROOT / "extensions/concorde"), "--dev"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(root / ".specify/extensions/concorde/scripts/python/concorde.py"),
                    "--project-root",
                    str(root),
                    "agent-assets",
                    "sync",
                    "--integration",
                    "codex",
                    "--concorde-version",
                    "0.6.0",
                ],
                cwd=root,
                check=True,
                capture_output=True,
            )
            names = {path.parent.name for path in (root / ".agents/skills").glob("speckit-concorde-*/SKILL.md")}
            self.assertEqual(names, {
                "speckit-concorde-init",
                "speckit-concorde-deliver",
                "speckit-concorde-context",
                "speckit-concorde-validate",
                "speckit-concorde-ask",
            })
            source = (REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.ask.md").read_text(encoding="utf-8")
            installed = (root / ".agents/skills/speckit-concorde-ask/SKILL.md").read_text(encoding="utf-8")
            source_body = source.split("---", 2)[2].strip()
            self.assertIn(source_body, installed)
            self.assertNotIn(str(REPOSITORY_ROOT), installed)
            triage = (root / ".agents/skills/reflections-triage/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("reflection-triage/v1", triage)
            self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
            self.assertTrue((root / ".codex/agents/reflection_implementer.toml").is_file())
            self.assertNotIn(str(REPOSITORY_ROOT), triage)


if __name__ == "__main__":
    unittest.main()
