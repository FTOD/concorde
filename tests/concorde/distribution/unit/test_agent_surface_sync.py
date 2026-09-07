from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


SCRIPT = REPOSITORY_ROOT / "scripts/development/sync-agent-surfaces.py"
SPEC = importlib.util.spec_from_file_location("concorde_agent_surface_sync", SCRIPT)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync
SPEC.loader.exec_module(sync)


class SourceCheckoutDistributionTests(unittest.TestCase):
    def test_repository_surfaces_are_current(self):
        desired = sync.expected_outputs(REPOSITORY_ROOT)
        actions = sync.inspect_checkout(REPOSITORY_ROOT, desired)
        self.assertEqual(len(desired), 20)
        self.assertEqual({item["action"] for item in actions}, {"current"})

    def test_inventory_contains_all_capabilities_for_both_integrations(self):
        desired = sync.expected_outputs(REPOSITORY_ROOT)
        codex = {path for path in desired if path.startswith(".agents/skills/concorde-")}
        claude = {path for path in desired if path.startswith(".claude/skills/concorde-")}
        self.assertEqual(len(codex), 8)
        self.assertEqual(len(claude), 8)
        self.assertIn(
            ".agents/skills/concorde-standard-dev-loop/SKILL.md", codex
        )
        self.assertIn(
            ".claude/skills/concorde-reflections-triage/SKILL.md", claude
        )
        for content in desired.values():
            self.assertNotIn(b".specify/", content)
            self.assertNotIn(b"github-spec-kit", content)

    def test_loaded_skill_identity_resolves_the_owning_worktree_and_integration(self):
        for integration, relative in (
            ("codex", ".agents/skills/concorde-main/SKILL.md"),
            ("claude", ".claude/skills/concorde-main/SKILL.md"),
        ):
            with self.subTest(integration=integration):
                root, observed_integration, capability = sync._loaded_skill_identity(
                    REPOSITORY_ROOT / relative
                )
                self.assertEqual(root, REPOSITORY_ROOT)
                self.assertEqual(observed_integration, integration)
                self.assertEqual(capability, "concorde-main")

    def test_worktree_affinity_accepts_a_current_skill_from_the_same_worktree(self):
        verified = sync.verify_worktree_affinity(
            REPOSITORY_ROOT,
            REPOSITORY_ROOT / ".agents/skills/concorde-main/SKILL.md",
        )
        self.assertEqual(verified["project_root"], str(REPOSITORY_ROOT))
        self.assertEqual(verified["loaded_worktree"], str(REPOSITORY_ROOT))
        self.assertTrue(verified["surface_match"])

    def test_loaded_skill_path_must_be_an_absolute_checkout_capability(self):
        with self.assertRaisesRegex(sync.WorktreeAffinityError, "absolute path"):
            sync._loaded_skill_identity(".agents/skills/concorde-main/SKILL.md")

    def test_inspect_classifies_create_update_symlink_and_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            desired = {
                "missing.txt": b"new\n",
                "stale.txt": b"new\n",
                "linked.txt": b"new\n",
                "blocked.txt": b"new\n",
            }
            (root / "stale.txt").write_text("old\n")
            (root / "target.txt").write_text("old\n")
            (root / "linked.txt").symlink_to("target.txt")
            (root / "blocked.txt").mkdir()
            actions = {item["path"]: item["action"] for item in sync.inspect(root, desired)}
            self.assertEqual(actions, {
                "blocked.txt": "conflict",
                "linked.txt": "replace-symlink",
                "missing.txt": "create",
                "stale.txt": "update",
            })

    def test_apply_refreshes_generated_files_and_replaces_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            desired = {"nested/a.txt": b"a\n", "nested/b.txt": b"b\n"}
            (root / "nested").mkdir()
            (root / "source.txt").write_text("source\n")
            (root / "nested/a.txt").symlink_to("../source.txt")
            actions = sync.inspect(root, desired)
            sync.apply(root, desired, actions)
            self.assertEqual({item["action"] for item in sync.inspect(root, desired)}, {"current"})
            self.assertFalse((root / "nested/a.txt").is_symlink())

    def test_non_file_conflict_blocks_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "blocked").mkdir()
            desired = {"blocked": b"file\n"}
            with self.assertRaisesRegex(ValueError, "non-file conflict"):
                sync.apply(root, desired, sync.inspect(root, desired))


if __name__ == "__main__":
    unittest.main()
