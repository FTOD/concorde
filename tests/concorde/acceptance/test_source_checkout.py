from __future__ import annotations

import json
import subprocess
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class SourceCheckoutAcceptance(unittest.TestCase):
    def test_checkout_projects_both_agent_surfaces_without_duplicate_framework(self):
        result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "scripts/development/sync-agent-surfaces.py"), "status", "--project-root", str(REPOSITORY_ROOT), "--format", "json"],
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "current")
        self.assertEqual(value["outputs"], 38)
        self.assertEqual(len(list((REPOSITORY_ROOT / ".agents/skills").glob("speckit-*/SKILL.md"))), 16)
        self.assertEqual(len(list((REPOSITORY_ROOT / ".claude/skills").glob("speckit-*/SKILL.md"))), 16)
        self.assertFalse((REPOSITORY_ROOT / ".concorde/framework").exists())
        self.assertFalse((REPOSITORY_ROOT / ".specify").exists())

    def test_root_commands_are_the_projection_provenance(self):
        for integration_root in (".agents/skills", ".claude/skills"):
            plan = (REPOSITORY_ROOT / integration_root / "speckit-plan/SKILL.md").read_text()
            self.assertIn('source: "commands/speckit.plan.md"', plan)
            self.assertIn("python3 scripts/workspace.py --phase plan", plan)
            self.assertNotIn(".concorde/framework", plan)


if __name__ == "__main__":
    unittest.main()
