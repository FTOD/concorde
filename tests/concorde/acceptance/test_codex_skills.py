from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class CodexSkillsAcceptance(unittest.TestCase):
    def test_native_install_exposes_complete_codex_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "codex", "--apply", "--format", "json"],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            manifest = json.loads((root / ".concorde/framework/concorde.json").read_text())
            skills = sorted((root / ".agents/skills").glob("speckit-*/SKILL.md"))
            self.assertEqual(len(skills), len(manifest["commands"]))
            for phase in ("specify", "plan", "tasks", "implement", "fast-loop"):
                body = (root / f".agents/skills/speckit-{phase}/SKILL.md").read_text()
                self.assertIn("Protocol 12", body)
                self.assertIn(f"--phase {phase}", body)
                self.assertIn('author: "concorde"', body)
            deliver = (root / ".agents/skills/speckit-concorde-deliver/SKILL.md").read_text()
            self.assertIn("Delivery Proposal 8", deliver)
            self.assertIn(".concorde/framework/scripts/concorde.py deliver", deliver)
            self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
            self.assertFalse((root / ".specify").exists())


if __name__ == "__main__":
    unittest.main()
