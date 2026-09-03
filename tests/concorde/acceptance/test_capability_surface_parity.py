from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class CapabilitySurfaceParityAcceptance(unittest.TestCase):
    def test_codex_and_claude_share_capability_identity_and_body_markers(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(base))
            roots = {}
            for integration in ("codex", "claude"):
                root = base / integration
                result = subprocess.run(
                    [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--integration", integration, "--apply"],
                    text=True, capture_output=True, env=environment,
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                roots[integration] = root
            for capability in ("concorde-plan", "concorde-specify", "concorde-fast-loop", "concorde-deliver", "concorde-constitution", "concorde-standard-dev-loop", "concorde-reflections-triage"):
                codex = (roots["codex"] / f".agents/skills/{capability}/SKILL.md").read_text()
                claude = (roots["claude"] / f".claude/skills/{capability}/SKILL.md").read_text()
                codex_body = codex.split("---", 2)[-1]
                claude_body = claude.split("---", 2)[-1]
                normalized_codex = re.sub(r"\.concorde/framework/", "<framework>/", codex_body)
                normalized_claude = re.sub(r"\.concorde/framework/", "<framework>/", claude_body)
                self.assertEqual(normalized_codex, normalized_claude, capability)

    def test_all_installed_capabilities_resolve_package_tokens(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            subprocess.run([sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--apply"], check=True, capture_output=True, text=True, env=environment)
            for path in (root / ".agents/skills").glob("concorde-*/SKILL.md"):
                body = path.read_text()
                self.assertNotIn("{SCRIPT}", body)
                self.assertNotIn("{FRAMEWORK}", body)
                self.assertNotIn("{OPERATION}", body)
                self.assertNotIn(".specify/", body)


if __name__ == "__main__":
    unittest.main()
