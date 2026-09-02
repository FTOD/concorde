from __future__ import annotations

import json
import subprocess
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class AgentSurfaceContractTests(unittest.TestCase):
    def status(self):
        result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/development/sync-agent-surfaces.py"),
                "status", "--project-root", str(REPOSITORY_ROOT), "--format", "json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_status_envelope_is_closed_current_and_sorted(self):
        value = self.status()
        self.assertEqual(set(value), {"schema_version", "operation", "status", "outputs", "actions"})
        self.assertEqual((value["schema_version"], value["operation"], value["status"]), (1, "status", "current"))
        self.assertEqual(value["outputs"], len(value["actions"]))
        self.assertEqual([item["path"] for item in value["actions"]], sorted(item["path"] for item in value["actions"]))

    def test_every_action_has_safe_path_action_and_digest(self):
        for item in self.status()["actions"]:
            self.assertEqual(set(item), {"path", "action", "sha256"})
            self.assertFalse(item["path"].startswith("/"))
            self.assertNotIn("..", item["path"].split("/"))
            self.assertNotIn("\\", item["path"])
            self.assertEqual(item["action"], "current")
            self.assertRegex(item["sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_contract_covers_both_integration_commands_and_reflection_agents(self):
        paths = {item["path"] for item in self.status()["actions"]}
        self.assertEqual(len([path for path in paths if path.startswith(".agents/skills/concorde-")]), 16)
        self.assertEqual(len([path for path in paths if path.startswith(".claude/skills/concorde-")]), 16)
        for required in (
            ".agents/skills/reflections-triage/SKILL.md",
            ".codex/agents/reflection_investigator.toml",
            ".claude/skills/reflections-triage/SKILL.md",
            ".claude/agents/reflection-investigator.md",
        ):
            self.assertIn(required, paths)

    def test_generated_outputs_are_regular_and_native(self):
        for item in self.status()["actions"]:
            path = REPOSITORY_ROOT / item["path"]
            self.assertTrue(path.is_file())
            self.assertFalse(path.is_symlink())
            text = path.read_text()
            self.assertNotIn(".specify/", text)


if __name__ == "__main__":
    unittest.main()
