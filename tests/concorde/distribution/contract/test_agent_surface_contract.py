from __future__ import annotations

import json
import subprocess
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT


class SourceCheckoutDistributionContractTests(unittest.TestCase):
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
        self.assertEqual(set(value), {"schema_version", "tool", "status", "outputs", "actions"})
        self.assertEqual((value["schema_version"], value["tool"], value["status"]), (2, "status", "current"))
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

    def test_contract_covers_both_integration_capabilities_and_reflection_agents(self):
        paths = {item["path"] for item in self.status()["actions"]}
        self.assertEqual(len([path for path in paths if path.startswith(".agents/skills/concorde-")]), 8)
        self.assertEqual(len([path for path in paths if path.startswith(".claude/skills/concorde-")]), 8)
        for required in (
            ".agents/skills/concorde-standard-dev-loop/SKILL.md",
            ".agents/skills/concorde-reflections-triage/SKILL.md",
            ".codex/agents/reflection_investigator.toml",
            ".claude/skills/concorde-standard-dev-loop/SKILL.md",
            ".claude/skills/concorde-reflections-triage/SKILL.md",
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
            self.assertNotIn("verify-worktree", text)
            self.assertNotIn("Source-Checkout Agent Policy", text)

    def test_check_is_a_current_machine_enforcement_entrypoint(self):
        result = subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/development/sync-agent-surfaces.py"),
                "check",
                "--project-root",
                str(REPOSITORY_ROOT),
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        value = json.loads(result.stdout)
        self.assertEqual((value["tool"], value["status"]), ("check", "current"))

    def test_worktree_verifier_accepts_only_the_skill_owning_checkout(self):
        command = [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/development/sync-agent-surfaces.py"),
            "verify-worktree",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--loaded-skill-path",
            str(REPOSITORY_ROOT / ".agents/skills/concorde-main/SKILL.md"),
        ]
        accepted = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(accepted.returncode, 0, accepted.stderr or accepted.stdout)
        self.assertIn("agent worktree: current", accepted.stdout)

        wrong_root_command = list(command)
        wrong_root_command[4] = str(REPOSITORY_ROOT.parent)
        wrong_root = subprocess.run(
            wrong_root_command, text=True, capture_output=True
        )
        self.assertNotEqual(wrong_root.returncode, 0)
        self.assertIn("script from the same worktree", wrong_root.stderr)

    def test_root_agent_policy_binds_sessions_and_keeps_sync_worktree_local(self):
        policy = (REPOSITORY_ROOT / "AGENTS.md").read_text()
        claude = (REPOSITORY_ROOT / "CLAUDE.md").read_text()
        normalized = " ".join(policy.split())
        self.assertIn("verify-worktree", policy)
        self.assertIn("open a new agent", normalized)
        self.assertIn("must stop after reporting its path and branch", normalized)
        self.assertIn("run `apply` in that same worktree", normalized)
        self.assertIn(
            "Never directly create, edit, delete, or rename `.agents/skills/concorde-*`",
            policy,
        )
        self.assertIn("`.claude/skills/concorde-*`", policy)
        self.assertIn("read and follow `AGENTS.md`", claude)

    def test_pull_requests_enforce_surface_freshness_and_affinity_contracts(self):
        workflow = (
            REPOSITORY_ROOT / ".github/workflows/validate-source-checkout.yml"
        ).read_text()
        self.assertIn("pull_request:", workflow)
        self.assertIn("sync-agent-surfaces.py check", workflow)
        self.assertIn("test_agent_surface_sync", workflow)
        self.assertIn("test_agent_surface_contract", workflow)
        self.assertIn("test_agent_surface_lifecycle", workflow)


if __name__ == "__main__":
    unittest.main()
