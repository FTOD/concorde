import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class SlashCommandAcceptance(unittest.TestCase):
    def test_gemini_registration_and_primary_runtime_behavior(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(
                ["specify", "init", "--here", "--force", "--ignore-agent-tools", "--integration", "gemini"],
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
            registered = list((root / ".gemini").rglob("*concorde*"))
            self.assertEqual(len([path for path in registered if path.is_file()]), 7)
            ask = next(path for path in registered if path.is_file() and "ask" in path.name)
            source = (REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.ask.md").read_text(encoding="utf-8")
            installed = ask.read_text(encoding="utf-8")
            self.assertIn("$ARGUMENTS", source)
            self.assertIn("{{args}}", installed)
            for semantic in (
                "smallest relevant set",
                ".specify/extensions/concorde/",
                ".specify/presets/concorde-core/",
                "project-relative citation",
                "focused clarification",
                "strictly read-only",
                "do not silently normalize",
            ):
                self.assertIn(semantic, source)
                self.assertIn(semantic, installed)
            launcher = root / ".specify/extensions/concorde/scripts/bash/concorde.sh"
            result = subprocess.run([str(launcher), "init", "--propose", "--module-id", "module.slash"], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('"status":"proposal"', result.stdout)


if __name__ == "__main__":
    unittest.main()
