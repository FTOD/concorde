"""Host-created candidate worktrees for the self-hosted checkout."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


class CreateWorktreeBuildsTests(unittest.TestCase):
    """A self-hosted candidate worktree must build itself so the handoff opens on a fresh build."""

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
