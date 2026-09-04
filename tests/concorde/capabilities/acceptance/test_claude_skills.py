from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class ClaudeSkillsAcceptance(unittest.TestCase):
    def test_claude_capabilities_are_regular_project_files_with_native_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "claude", "--apply"],
                text=True, capture_output=True, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            skills = list((root / ".claude/skills").glob("concorde-*/SKILL.md"))
            self.assertEqual(len(skills), 18)
            for skill in skills:
                self.assertTrue(skill.is_file())
                self.assertFalse(skill.is_symlink())
                content = skill.read_text()
                self.assertIn("user-invocable: true", content)
                self.assertNotIn(".specify/", content)
                self.assertNotIn(str(REPOSITORY_ROOT), content)
            ask = (root / ".claude/skills/concorde-ask/SKILL.md").read_text()
            self.assertIn(".concorde/framework/concorde.json", ask)
            self.assertIn("strictly read-only", " ".join(ask.split()))
            operation = (
                root / ".claude/skills/concorde-reflections-triage/SKILL.md"
            ).read_text()
            self.assertIn('kind: "operation"', operation)
            self.assertIn("user-invocable: true", operation)

    def test_portable_powershell_and_posix_launchers_are_packaged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            subprocess.run([sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "claude", "--apply"], check=True, capture_output=True, text=True, env=environment)
            scripts = root / ".concorde/framework/scripts"
            self.assertIn("concorde.py", (scripts / "concorde.sh").read_text())
            self.assertIn("concorde.py", (scripts / "concorde.ps1").read_text())


if __name__ == "__main__":
    unittest.main()
