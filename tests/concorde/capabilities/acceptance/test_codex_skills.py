from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class CodexSkillsAcceptance(unittest.TestCase):
    def test_native_install_exposes_complete_codex_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "codex", "--apply", "--format", "json"],
                text=True, capture_output=True, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            manifest = json.loads((root / ".concorde/framework/concorde.json").read_text())
            skills = sorted((root / ".agents/skills").glob("concorde-*/SKILL.md"))
            self.assertEqual(len(skills), 18)
            for phase in ("specify", "tasks", "implement", "fast-loop"):
                body = (root / f".agents/skills/concorde-{phase}/SKILL.md").read_text()
                self.assertIn("Protocol 13", body)
                self.assertIn(f"--phase {phase}", body)
                self.assertIn('author: "concorde"', body)
            plan = (root / ".agents/skills/concorde-plan/SKILL.md").read_text()
            self.assertIn('kind: "operation"', plan)
            self.assertIn(
                ".concorde/framework/operations/concorde-plan/operation.py",
                plan,
            )
            self.assertFalse((root / ".agents/skills/concorde-plan-context").exists())
            self.assertFalse((root / ".agents/skills/concorde-plan-author").exists())
            deliver = (root / ".agents/skills/concorde-deliver/SKILL.md").read_text()
            self.assertIn("Delivery Proposal 9", deliver)
            self.assertIn(".concorde/framework/scripts/concorde.py deliver", deliver)
            self.assertTrue((root / ".codex/agents/reflection_investigator.toml").is_file())
            standard = (
                root / ".agents/skills/concorde-standard-dev-loop/SKILL.md"
            ).read_text()
            self.assertIn('kind: "operation"', standard)
            self.assertIn(
                ".concorde/framework/operations/concorde-standard-dev-loop/operation.py",
                standard,
            )
            self.assertFalse((root / ".specify").exists())


if __name__ == "__main__":
    unittest.main()
