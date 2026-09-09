"""Worktree affinity (moved from the retired scripts/development/sync-agent-surfaces.py).

These assertions were previously exercised in
tests/concorde/distribution/integration/test_agent_surface_lifecycle.py
(test_agent_loaded_in_primary_must_be_reopened_in_the_linked_worktree), against the old
sync-based drift check. They are carried over here against the new build-based freshness check.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.host.build import write_build  # noqa: E402
from concorde.host.worktree_affinity import (  # noqa: E402
    WorktreeAffinityError,
    verify_worktree_affinity,
)
from tests.concorde.support.build_fixture import build_package_copy  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


class WorktreeAffinityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "primary"
        self.root.mkdir()
        build_package_copy(self.root)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "commit", "-qm", "Fixture")

    def test_same_worktree_current_build_is_accepted(self):
        loaded = self.root / ".agents/skills/concorde-main/SKILL.md"
        verified = verify_worktree_affinity(self.root, loaded)
        self.assertEqual(verified["project_root"], str(self.root))
        self.assertEqual(verified["loaded_worktree"], str(self.root))
        self.assertEqual(verified["integration"], "codex")
        self.assertEqual(verified["capability"], "concorde-main")
        self.assertTrue(verified["surface_match"])

    def test_stale_build_is_rejected_with_a_maintenance_handoff(self):
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "One more sentence.\n", encoding="utf-8")
        loaded = self.root / ".agents/skills/concorde-main/SKILL.md"
        with self.assertRaises(WorktreeAffinityError) as failure:
            verify_worktree_affinity(self.root, loaded)
        message = str(failure.exception)
        self.assertIn("build is stale", message)
        self.assertIn("scripts/concorde.py build", message)
        self.assertIn("```text", message)

    def test_agent_loaded_in_primary_must_be_reopened_in_the_linked_worktree(self):
        linked = Path(self.temporary.name) / "linked"
        _git(self.root, "worktree", "add", "-qb", "agent/test", str(linked), "HEAD")
        loaded = self.root / ".agents/skills/concorde-main/SKILL.md"

        with self.assertRaises(WorktreeAffinityError) as failure:
            verify_worktree_affinity(linked, loaded)
        message = str(failure.exception)
        self.assertIn("loaded Concorde Skills from", message)
        self.assertIn("open a new agent", message)
        self.assertIn(str(linked), message)
        self.assertIn("```text", message)

        # The linked worktree's own build (copied at worktree-creation time) is untouched, so
        # its Skill bytes still match the primary's; affinity is rejected purely on identity.
        self.assertIn("worktree identity still differs", message)

        accepted = verify_worktree_affinity(linked, linked / ".agents/skills/concorde-main/SKILL.md")
        self.assertEqual(accepted["loaded_worktree"], str(linked))

    def test_diverged_linked_worktree_reports_which_skill_versions_differ(self):
        linked = Path(self.temporary.name) / "linked"
        _git(self.root, "worktree", "add", "-qb", "agent/test2", str(linked), "HEAD")
        # Diverge the linked worktree's own build deterministically and independently of the
        # primary, exactly as a developer editing concorde-main's own skill source and
        # rebuilding there would.
        edited = linked / "skills/concorde-main/SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nLinked-only change.\n", encoding="utf-8")
        write_build(linked)

        loaded = self.root / ".agents/skills/concorde-main/SKILL.md"
        with self.assertRaises(WorktreeAffinityError) as failure:
            verify_worktree_affinity(linked, loaded)
        message = str(failure.exception)
        self.assertIn("Skill versions differ for concorde-main", message)


class CreateWorktreeBuildsTests(unittest.TestCase):
    """A self-hosted candidate worktree must build itself so the handoff is ready (item 7)."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "primary"
        self.root.mkdir()
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "commit", "-qm", "Fixture")

    def test_self_hosted_worktree_creation_builds_the_new_worktree(self):
        from concorde.host.build import verify_fresh
        from concorde.host.change_worktree import create_worktree

        self.assertFalse((self.root / "generated").exists())
        state = create_worktree(self.root, {"task": "Implement a change"}, package_root=self.root)
        created = Path(state["path"])
        self.addCleanup(lambda: _git(self.root, "worktree", "remove", "--force", str(created)))
        self.assertTrue((created / "generated/build-manifest.json").is_file())
        self.assertTrue((created / ".agents/skills/concorde-main/SKILL.md").is_file())
        verify_fresh(created)  # must not raise

    def test_worktree_creation_for_an_unrelated_project_does_not_attempt_a_build(self):
        # package_root differs from the project root being managed (the ordinary, non-self-hosted
        # case): the created worktree is a "project" checkout with no prompts/skills of its own,
        # and create_worktree must not try (and fail) to build it.
        from concorde.host.change_worktree import create_worktree

        other_package = Path(self.temporary.name) / "framework"
        other_package.mkdir()
        state = create_worktree(self.root, {"task": "Implement a change"}, package_root=other_package)
        created = Path(state["path"])
        self.addCleanup(lambda: _git(self.root, "worktree", "remove", "--force", str(created)))
        self.assertFalse((created / "generated").exists())

    def test_worktree_creation_without_a_package_root_does_not_attempt_a_build(self):
        from concorde.host.change_worktree import create_worktree

        state = create_worktree(self.root, {"task": "Implement a change"})
        created = Path(state["path"])
        self.addCleanup(lambda: _git(self.root, "worktree", "remove", "--force", str(created)))
        self.assertFalse((created / "generated").exists())


if __name__ == "__main__":
    unittest.main()
