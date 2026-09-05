from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT_RELATIVE = "scripts/development/sync-agent-surfaces.py"


class AgentSurfaceLifecycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "checkout"
        self.root.mkdir()
        shutil.copy2(REPOSITORY_ROOT / "concorde.json", self.root / "concorde.json")
        for directory in ("agent-assets", "operations", "skills", "src", "templates"):
            shutil.copytree(REPOSITORY_ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.root / "scripts/development").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / SCRIPT_RELATIVE, self.root / SCRIPT_RELATIVE)

    def run_sync(self, tool: str, check: bool = True):
        result = subprocess.run(
            [
                sys.executable,
                str(self.root / SCRIPT_RELATIVE),
                tool,
                "--project-root", str(self.root),
                "--format", "json",
            ],
            text=True,
            capture_output=True,
        )
        if check and result.returncode:
            self.fail(result.stderr or result.stdout)
        return result, json.loads(result.stdout) if result.stdout else None

    def test_missing_checkout_surfaces_are_detected_and_both_integrations_apply(self):
        _, before = self.run_sync("status")
        self.assertEqual(before["status"], "drift")
        self.assertEqual({item["action"] for item in before["actions"]}, {"create"})
        _, applied = self.run_sync("apply")
        self.assertEqual(applied["status"], "current")
        self.assertEqual(applied["outputs"], 48)
        self.assertTrue((self.root / ".agents/skills/concorde-plan/SKILL.md").is_file())
        self.assertTrue((self.root / ".claude/skills/concorde-plan/SKILL.md").is_file())

    def test_status_is_read_only_and_apply_refreshes_one_drifted_output(self):
        self.run_sync("apply")
        skill = self.root / ".agents/skills/concorde-plan/SKILL.md"
        skill.write_text("stale\n")
        before = skill.read_bytes()
        _, status = self.run_sync("status")
        self.assertEqual(skill.read_bytes(), before)
        drift = [item for item in status["actions"] if item["action"] != "current"]
        self.assertEqual([(item["path"], item["action"]) for item in drift], [(".agents/skills/concorde-plan/SKILL.md", "update")])
        self.run_sync("apply")
        self.assertIn("invocation", skill.read_text())

    def test_legacy_symlink_is_replaced_with_regular_native_surface(self):
        target = self.root / "legacy.md"
        target.write_text("legacy\n")
        skill = self.root / ".claude/skills/concorde-context/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.symlink_to(target)
        _, status = self.run_sync("status")
        action = next(item for item in status["actions"] if item["path"] == ".claude/skills/concorde-context/SKILL.md")
        self.assertEqual(action["action"], "replace-symlink")
        self.run_sync("apply")
        self.assertTrue(skill.is_file())
        self.assertFalse(skill.is_symlink())
        self.assertEqual(target.read_text(), "legacy\n")

    def test_non_file_output_conflict_stops_apply(self):
        blocked = self.root / ".agents/skills/concorde-plan/SKILL.md"
        blocked.mkdir(parents=True)
        result, value = self.run_sync("apply", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(value)
        self.assertIn("non-file conflict", result.stderr)

    def test_canonical_skill_change_updates_only_its_generated_integrations(self):
        self.run_sync("apply")
        skill = self.root / "operations/concorde-checklist/SKILL.md"
        skill.write_text(skill.read_text() + "\nLifecycle marker.\n")
        _, status = self.run_sync("status")
        changed = {item["path"] for item in status["actions"] if item["action"] == "update"}
        self.assertEqual(changed, {
            ".agents/skills/concorde-checklist/SKILL.md",
            ".claude/skills/concorde-checklist/SKILL.md",
        })


if __name__ == "__main__":
    unittest.main()
