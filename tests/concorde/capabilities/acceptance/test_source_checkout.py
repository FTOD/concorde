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
        self.assertEqual((value["schema_version"], value["tool"]), (2, "status"))
        self.assertEqual(value["outputs"], 40)
        self.assertEqual(len(list((REPOSITORY_ROOT / ".agents/skills").glob("concorde-*/SKILL.md"))), 18)
        self.assertEqual(len(list((REPOSITORY_ROOT / ".claude/skills").glob("concorde-*/SKILL.md"))), 18)
        self.assertFalse((REPOSITORY_ROOT / ".concorde/framework").exists())
        self.assertFalse((REPOSITORY_ROOT / ".specify").exists())

    def test_root_skills_are_the_projection_provenance(self):
        for integration_root in (".agents/skills", ".claude/skills"):
            plan = (REPOSITORY_ROOT / integration_root / "concorde-plan/SKILL.md").read_text()
            self.assertIn('source: "operations/concorde-plan/SKILL.md"', plan)
            self.assertIn('kind: "operation"', plan)
            self.assertIn(
                "python3 scripts/run-operation.py operations/concorde-plan/operation.py",
                plan,
            )
            self.assertNotIn(".concorde/framework", plan)


if __name__ == "__main__":
    unittest.main()
