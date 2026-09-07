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


class SelfDistributionLifecycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "checkout"
        self.root.mkdir()
        shutil.copy2(REPOSITORY_ROOT / "concorde.json", self.root / "concorde.json")
        for directory in ("agent-assets", "operations", "roles", "src", "templates"):
            shutil.copytree(REPOSITORY_ROOT / directory, self.root / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.root / "scripts/development").mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / SCRIPT_RELATIVE, self.root / SCRIPT_RELATIVE)

    def run_sync(
        self,
        tool: str,
        check: bool = True,
        *,
        root: Path | None = None,
        extra: tuple[str, ...] = (),
    ):
        target = root or self.root
        result = subprocess.run(
            [
                sys.executable,
                str(target / SCRIPT_RELATIVE),
                tool,
                "--project-root", str(target),
                "--format", "json",
                *extra,
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
        checked, check_value = self.run_sync("check", check=False)
        self.assertEqual(checked.returncode, 1)
        self.assertEqual(check_value["status"], "drift")
        _, applied = self.run_sync("apply")
        self.assertEqual(applied["status"], "current")
        self.assertEqual(applied["outputs"], 20)
        checked, check_value = self.run_sync("check")
        self.assertEqual(checked.returncode, 0)
        self.assertEqual(check_value["status"], "current")
        self.assertTrue((self.root / ".agents/skills/concorde-validate/SKILL.md").is_file())
        self.assertTrue((self.root / ".claude/skills/concorde-validate/SKILL.md").is_file())

    def test_status_is_read_only_and_apply_refreshes_one_drifted_output(self):
        self.run_sync("apply")
        skill = self.root / ".agents/skills/concorde-validate/SKILL.md"
        skill.write_text("stale\n")
        before = skill.read_bytes()
        _, status = self.run_sync("status")
        self.assertEqual(skill.read_bytes(), before)
        drift = [item for item in status["actions"] if item["action"] != "current"]
        self.assertEqual([(item["path"], item["action"]) for item in drift], [(".agents/skills/concorde-validate/SKILL.md", "update")])
        checked, value = self.run_sync("check", check=False)
        self.assertEqual(checked.returncode, 1)
        self.assertEqual(value["status"], "drift")
        self.run_sync("apply")
        self.assertIn("invocation", skill.read_text())

    def test_legacy_symlink_is_replaced_with_regular_native_surface(self):
        target = self.root / "legacy.md"
        target.write_text("legacy\n")
        skill = self.root / ".claude/skills/concorde-main/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.symlink_to(target)
        _, status = self.run_sync("status")
        action = next(item for item in status["actions"] if item["path"] == ".claude/skills/concorde-main/SKILL.md")
        self.assertEqual(action["action"], "replace-symlink")
        self.run_sync("apply")
        self.assertTrue(skill.is_file())
        self.assertFalse(skill.is_symlink())
        self.assertEqual(target.read_text(), "legacy\n")

    def test_non_file_output_conflict_stops_apply(self):
        blocked = self.root / ".agents/skills/concorde-validate/SKILL.md"
        blocked.mkdir(parents=True)
        result, value = self.run_sync("apply", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(value)
        self.assertIn("non-file conflict", result.stderr)

    def test_unexpected_concorde_projection_fails_check_and_is_not_deleted(self):
        self.run_sync("apply")
        unexpected = self.root / ".agents/skills/concorde-stale/SKILL.md"
        unexpected.parent.mkdir(parents=True)
        unexpected.write_text("stale generated projection\n")
        checked, value = self.run_sync("check", check=False)
        self.assertEqual(checked.returncode, 1)
        action = next(
            item for item in value["actions"] if item["path"].endswith("concorde-stale/SKILL.md")
        )
        self.assertEqual(action["action"], "unexpected")
        applied, value = self.run_sync("apply", check=False)
        self.assertEqual(applied.returncode, 1)
        self.assertEqual(value["status"], "drift")
        self.assertTrue(unexpected.is_file())

    def test_canonical_skill_change_updates_only_its_generated_integrations(self):
        self.run_sync("apply")
        skill = self.root / "operations/concorde-validate/SKILL.md"
        skill.write_text(skill.read_text() + "\nLifecycle marker.\n")
        _, status = self.run_sync("status")
        changed = {item["path"] for item in status["actions"] if item["action"] == "update"}
        self.assertEqual(changed, {
            ".agents/skills/concorde-validate/SKILL.md",
            ".claude/skills/concorde-validate/SKILL.md",
        })
        checked, check_value = self.run_sync("check", check=False)
        self.assertEqual(checked.returncode, 1)
        self.assertEqual(check_value["status"], "drift")
        self.run_sync("apply")
        self.assertIn(
            "Lifecycle marker.",
            (
                self.root / ".agents/skills/concorde-validate/SKILL.md"
            ).read_text(),
        )

    def test_agent_loaded_in_primary_must_be_reopened_in_the_linked_worktree(self):
        self.run_sync("apply")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            [
                "git",
                "-c", "user.name=Concorde Test",
                "-c", "user.email=concorde@example.invalid",
                "commit", "-qm", "base",
            ],
            cwd=self.root,
            check=True,
        )
        linked = Path(self.temporary.name) / "linked"
        subprocess.run(
            ["git", "worktree", "add", "-qb", "agent/test", str(linked), "HEAD"],
            cwd=self.root,
            check=True,
        )
        loaded = self.root / ".agents/skills/concorde-main/SKILL.md"

        rejected, _value = self.run_sync(
            "verify-worktree",
            check=False,
            root=linked,
            extra=("--loaded-skill-path", str(loaded)),
        )
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("loaded Concorde Skills from", rejected.stderr)
        self.assertIn("open a new agent", rejected.stderr)
        self.assertIn("worktree identity still differs", rejected.stderr)
        self.assertIn("```text", rejected.stderr)
        self.assertIn(str(linked), rejected.stderr)
        self.assertIn('"Branch": "agent/test"', rejected.stderr)
        self.assertIn("Unknown to the runtime", rejected.stderr)

        changed = linked / "operations/concorde-validate/SKILL.md"
        changed.write_text(changed.read_text() + "\nLinked marker.\n")
        primary_before = loaded.read_bytes()
        wrong_script = subprocess.run(
            [
                sys.executable,
                str(self.root / SCRIPT_RELATIVE),
                "apply",
                "--project-root", str(linked),
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(wrong_script.returncode, 2)
        self.assertIn("script from the same worktree", wrong_script.stderr)
        self.run_sync("apply", root=linked)
        self.assertEqual(loaded.read_bytes(), primary_before)
        rejected, _value = self.run_sync(
            "verify-worktree",
            check=False,
            root=linked,
            extra=("--loaded-skill-path", str(loaded)),
        )
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("Skill versions differ for concorde-validate", rejected.stderr)

        accepted, value = self.run_sync(
            "verify-worktree",
            root=linked,
            extra=(
                "--loaded-skill-path",
                str(linked / ".agents/skills/concorde-main/SKILL.md"),
            ),
        )
        self.assertEqual(accepted.returncode, 0)
        self.assertEqual(value["loaded_worktree"], str(linked))


if __name__ == "__main__":
    unittest.main()
