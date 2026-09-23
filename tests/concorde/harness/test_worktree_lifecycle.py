"""Real Git regressions for candidate guidance and change ownership."""

import unittest
from unittest.mock import patch

from concorde.harness import change_worktree
from concorde.harness.change_worktree import GUIDANCE_START, git_value, read_change
from concorde.spec.verification import verifies
from tests.concorde.support.worktree_project import WorktreeProject


class WorktreeLifecycleTests(WorktreeProject, unittest.TestCase):
    """Guidance and owner binding of a registered candidate."""

    @verifies("scenario.worktrees.guidance-appended")
    def test_new_guidance_preserves_existing_client_content_bytes_and_modes(self):
        agents = self.change / "AGENTS.md"
        agents.write_bytes(b"# User policy\r\nKeep these bytes.\r\n")
        agents.chmod(0o751)
        claude = self.change / "CLAUDE.md"
        # Even a guidance-looking block outside the saved ownership map is user content.
        original = (
            b"# User-owned client file\r\n"
            + (GUIDANCE_START + "User text\n" + change_worktree.GUIDANCE_END).encode()
        )
        claude.write_bytes(original)
        claude.chmod(0o740)
        before = agents.read_bytes()
        state = change_worktree.ensure_change(self.change, task=self.task)
        self.assertEqual({"AGENTS.md": {"created": False}}, state["guidance"])
        self.assertEqual(
            before,
            change_worktree.strip_guidance(agents.read_bytes().decode()).encode(),
        )
        self.assertEqual(0o751, agents.stat().st_mode & 0o777)
        self.assertEqual(original, claude.read_bytes())
        self.assertEqual(0o740, claude.stat().st_mode & 0o777)
        tree = change_worktree.snapshot_tree(self.change)
        self.assertEqual(original, self.tree_bytes(tree, "CLAUDE.md"))
        self.assertEqual(before, self.tree_bytes(tree, "AGENTS.md"))
        self.assertTrue(
            git_value(self.change, "ls-tree", tree, "AGENTS.md").startswith("100755 ")
        )

    @verifies("scenario.worktrees.guidance-appended")
    def test_new_guidance_creates_only_agents_and_excludes_its_empty_shell(self):
        (self.change / "AGENTS.md").unlink()
        state = change_worktree.ensure_change(self.change, task=self.task)
        self.assertEqual({"AGENTS.md": {"created": True}}, state["guidance"])
        self.assertTrue((self.change / "AGENTS.md").exists())
        self.assertFalse((self.change / "CLAUDE.md").exists())
        tree = change_worktree.snapshot_tree(self.change)
        self.assertEqual(
            "", git_value(self.change, "ls-tree", tree, "AGENTS.md", "CLAUDE.md")
        )

    @verifies("scenario.worktrees.guidance-appended")
    def test_ambiguous_guidance_blocks_snapshot_without_mutation(self):
        change_worktree.ensure_change(self.change, task=self.task)
        agents = self.change / "AGENTS.md"
        block = (
            GUIDANCE_START + "Owned guidance\n" + change_worktree.GUIDANCE_END
        ).encode()
        agents.write_bytes(block + block)
        saved = self.state_file().read_bytes()
        index = git_value(self.change, "write-tree")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            change_worktree.snapshot_tree(self.change)
        self.assertEqual(block + block, agents.read_bytes())
        self.assertEqual(saved, self.state_file().read_bytes())
        self.assertEqual(index, git_value(self.change, "write-tree"))

    @verifies("scenario.worktrees.guidance-appended")
    def test_guidance_and_initial_state_rollback_together(self):
        agents = self.change / "AGENTS.md"
        agents.write_bytes(b"# Existing policy\r\nKeep original newlines.\r\n")
        agents.chmod(0o751)
        before = agents.read_bytes()
        with patch.object(
            change_worktree,
            "write_status",
            side_effect=OSError("fixture state transaction failure"),
        ):
            result = self.call_operation(
                self.change,
                "concorde-context-solve",
                {"target_id": "scope.bank", "task": "Explain transfer"},
            )
        self.assertNotEqual("succeeded", result["status"], result)
        self.assertEqual(before, agents.read_bytes())
        self.assertEqual(0o751, agents.stat().st_mode & 0o777)
        self.assertFalse((self.change / "CLAUDE.md").exists())
        self.assertFalse(self.state_file().exists())

    @verifies("scenario.worktrees.owner-conflict")
    def test_owner_binding_missing_fields_returns_structured_error(self):
        from concorde.spec.repository import SpecError

        change_worktree.ensure_change(self.change, task=self.task)
        for field in ("target_id", "task"):
            task = dict(self.task)
            del task[field]
            with self.subTest(field=field), self.assertRaises(SpecError) as caught:
                change_worktree.bind_owner(self.change, task)
            self.assertEqual("invalid_input", caught.exception.code)
            self.assertEqual(field, caught.exception.field)
        self.assertIsNone(read_change(self.change, required=True)["target_id"])


if __name__ == "__main__":
    unittest.main()
