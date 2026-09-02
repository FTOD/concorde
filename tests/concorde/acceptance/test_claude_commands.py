from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class ClaudeCommandsAcceptance(unittest.TestCase):
    def test_claude_commands_are_regular_project_files_with_native_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "claude", "--apply"],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            for skill in (root / ".claude/skills").glob("concorde-*/SKILL.md"):
                self.assertTrue(skill.is_file())
                self.assertFalse(skill.is_symlink())
                content = skill.read_text()
                self.assertIn("user-invocable: true", content)
                self.assertNotIn(".specify/", content)
                self.assertNotIn(str(REPOSITORY_ROOT), content)
            ask = (root / ".claude/skills/concorde-ask/SKILL.md").read_text()
            self.assertIn(".concorde/framework/concorde.json", ask)
            self.assertIn("strictly read-only", " ".join(ask.split()))

    def test_portable_powershell_and_posix_launchers_are_packaged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run([sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "claude", "--apply"], check=True, capture_output=True, text=True)
            scripts = root / ".concorde/framework/scripts"
            self.assertIn("concorde.py", (scripts / "concorde.sh").read_text())
            self.assertIn("concorde.py", (scripts / "concorde.ps1").read_text())


if __name__ == "__main__":
    unittest.main()
