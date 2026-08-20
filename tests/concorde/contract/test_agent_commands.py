import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, VALID_PROJECT


class AgentCommandContractTests(unittest.TestCase):
    def test_all_canonical_commands_have_portable_runtime_references(self):
        commands = REPOSITORY_ROOT / "extensions/concorde/commands"
        expected = {"speckit.concorde.init.md", "speckit.concorde.context.md", "speckit.concorde.validate.md"}
        self.assertEqual({path.name for path in commands.glob("*.md")}, expected)
        for path in commands.glob("*.md"):
            content = path.read_text()
            self.assertIn(".specify/extensions/concorde/scripts/", content)
            self.assertNotIn(str(REPOSITORY_ROOT), content)

    def test_python_launcher_preserves_exit_and_handles_quoted_root(self):
        launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/python/concorde.py"
        result = subprocess.run(
            [sys.executable, str(launcher), "--project-root", str(VALID_PROJECT), "validate", "--format", "json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"operation":"validate"', result.stdout)
        self.assertGreaterEqual(sys.version_info, (3, 11))

    @unittest.skipUnless(os.name != "nt", "POSIX launcher test")
    def test_posix_launcher_is_relative_and_executable(self):
        launcher = REPOSITORY_ROOT / "extensions/concorde/scripts/bash/concorde.sh"
        self.assertTrue(os.access(launcher, os.X_OK))
        result = subprocess.run([str(launcher), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_powershell_launcher_uses_join_path_and_propagates_exit(self):
        content = (REPOSITORY_ROOT / "extensions/concorde/scripts/powershell/concorde.ps1").read_text()
        self.assertIn("Join-Path $PSScriptRoot", content)
        self.assertIn("@args", content)
        self.assertIn("exit $LASTEXITCODE", content)


if __name__ == "__main__":
    unittest.main()
