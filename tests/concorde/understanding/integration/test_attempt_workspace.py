import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


REMOVED = {"workspace_kind", "feature_abstract", "feature_implementation", "feature_" + "directory", "feature_" + "design", "module_summary", "module_design", "contracts_dir", "diagrams_dir", "parent_context"}


class AttemptWorkspaceIntegration(unittest.TestCase):
    def run_adapter(self, root: Path, phase: str, feature: str, persist: bool = False, feature_id: str | None = None) -> dict:
        command = [sys.executable, str(REPOSITORY_ROOT / "scripts/workspace.py"), "--project-root", str(root), "--phase", phase, "--feature-path", feature, "--allow-primary-worktree"]
        if feature_id is not None:
            command.extend(["--feature-id", feature_id])
        if persist:
            command.append("--persist")
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)




if __name__ == "__main__":
    unittest.main()
