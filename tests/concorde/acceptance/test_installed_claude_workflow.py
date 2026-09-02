from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_file, write_selection
from tests.concorde.support.paths import REPOSITORY_ROOT


class InstalledClaudeWorkflowAcceptance(unittest.TestCase):
    def test_native_claude_install_exposes_capabilities_agents_and_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "claude", "--apply", "--format", "json"],
                text=True, capture_output=True,
            )
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            self.assertEqual(len(list((root / ".claude/skills").glob("concorde-*/SKILL.md"))), 18)
            self.assertTrue((root / ".claude/agents/reflection-investigator.md").is_file())
            feature = create_feature_file(root)
            write_selection(root, feature.relative_to(root).as_posix())
            workspace = subprocess.run(
                [sys.executable, str(root / ".concorde/framework/scripts/workspace.py"), "--project-root", str(root), "--phase", "plan"],
                text=True, capture_output=True,
            )
            self.assertEqual(workspace.returncode, 0, workspace.stdout)
            self.assertEqual(json.loads(workspace.stdout)["workspace"]["feature_id"], "feature.example.deliver")
            skill = (root / ".claude/skills/concorde-plan/SKILL.md").read_text()
            self.assertIn("user-invocable: true", skill)
            self.assertIn(".concorde/framework/operations/concorde-plan/operation.py", skill)
            self.assertIn('kind: "operation"', skill)
            self.assertFalse((root / ".claude/skills/concorde-plan-context").exists())
            self.assertFalse((root / ".claude/skills/concorde-plan-author").exists())
            self.assertNotIn(".specify/", skill)


if __name__ == "__main__":
    unittest.main()
