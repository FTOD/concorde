from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.feature_workspace import create_feature_file, write_complete_attempt, write_selection
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class InstalledCodexWorkflowAcceptance(unittest.TestCase):
    def test_installed_runtime_resolves_validates_and_delivers_one_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            install = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", "codex", "--apply", "--format", "json"],
                text=True, capture_output=True, env=environment,
            )
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            feature = create_feature_file(root)
            write_selection(root, feature.relative_to(root).as_posix())
            attempt = write_complete_attempt(feature)
            workspace = subprocess.run(
                [sys.executable, str(root / ".concorde/framework/scripts/workspace.py"), "--project-root", str(root), "--phase", "implement", "--allow-primary-worktree"],
                text=True, capture_output=True,
            )
            self.assertEqual(workspace.returncode, 0, workspace.stdout)
            value = json.loads(workspace.stdout)
            self.assertEqual(value["workspace"]["attempt_state"], "complete")
            launcher = root / ".concorde/framework/scripts/concorde.py"
            validation = subprocess.run([sys.executable, str(launcher), "--project-root", str(root), "validate"], text=True, capture_output=True)
            self.assertEqual(validation.returncode, 0, validation.stdout)
            proposal = subprocess.run([sys.executable, str(launcher), "--project-root", str(root), "deliver", "--propose", "--allow-primary-worktree"], text=True, capture_output=True)
            self.assertEqual(proposal.returncode, 0, proposal.stdout)
            payload = json.loads(proposal.stdout)
            self.assertEqual(payload["status"], "eligible")
            proposal_path = payload["proposal_path"]
            self.assertEqual(json.loads((root / proposal_path).read_text(encoding="utf-8")), {
                "proposal_version": 9,
                "tool": "deliver",
                "target": payload["target"],
                "source_digest": payload["source_digest"],
                "remove": [payload["workspace"]["attempt_dir"]],
            })
            apply = subprocess.run([sys.executable, str(launcher), "--project-root", str(root), "deliver", "--apply", "--proposal", proposal_path, "--allow-primary-worktree"], text=True, capture_output=True)
            self.assertEqual(apply.returncode, 0, apply.stdout)
            self.assertFalse(attempt.exists())
            self.assertTrue(feature.is_file())


if __name__ == "__main__":
    unittest.main()
