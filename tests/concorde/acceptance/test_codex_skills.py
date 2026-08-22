import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class CodexSkillsAcceptance(unittest.TestCase):
    def test_five_commands_register_in_codex_skills_mode(self):
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
            names = {path.parent.name for path in (root / ".agents/skills").glob("speckit-concorde-*/SKILL.md")}
            self.assertEqual(names, {
                "speckit-concorde-init",
                "speckit-concorde-feature-create",
                "speckit-concorde-feature-select",
                "speckit-concorde-context",
                "speckit-concorde-validate",
            })


if __name__ == "__main__":
    unittest.main()
