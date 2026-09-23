"""Host-created candidate worktrees."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.spec.repository import SpecError  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )


class CreateWorktreeBuildsTests(unittest.TestCase):
    """A self-hosted candidate waits for its fresh writer to build with candidate-owned code."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "primary"
        self.root.mkdir()
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(
            REPOSITORY_ROOT / "pi",
            self.root / "pi",
            ignore=shutil.ignore_patterns("node_modules", "__pycache__"),
        )
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "add", "-A")
        _git(
            self.root,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        )

    def test_source_creation_leaves_the_build_to_the_fresh_candidate_writer(self):
        from concorde.harness.change_worktree import create_worktree, read_change

        self.assertFalse((self.root / "generated").exists())
        state = create_worktree(
            self.root, {"task": "Implement a change"}, package_root=self.root
        )
        created = Path(state["path"])
        self.addCleanup(
            lambda: _git(self.root, "worktree", "remove", "--force", str(created))
        )
        self.assertFalse((created / "generated").exists())
        self.assertFalse((created / ".agents/skills").exists())
        self.assertFalse((created / ".claude/skills").exists())
        self.assertFalse((created / ".pi/extensions/concorde-session.ts").exists())
        self.assertFalse((created / "CLAUDE.md").exists())
        self.assertEqual("maintenance", read_change(created, required=True)["mode"])
        self.assertEqual({}, read_change(created, required=True)["guidance"])

    def test_worktree_creation_for_an_unrelated_project_does_not_attempt_a_build(self):
        # package_root differs from the project root being managed (the ordinary, non-self-hosted
        # case): the created worktree is a "project" checkout without a Framework build of its own,
        # and create_worktree must not try (and fail) to build it.
        from concorde.harness.change_worktree import create_worktree

        other_package = Path(self.temporary.name) / "framework"
        other_package.mkdir()
        state = create_worktree(
            self.root, {"task": "Implement a change"}, package_root=other_package
        )
        created = Path(state["path"])
        self.addCleanup(
            lambda: _git(self.root, "worktree", "remove", "--force", str(created))
        )
        self.assertFalse((created / "generated").exists())

    def test_worktree_creation_without_a_package_root_does_not_attempt_a_build(self):
        from concorde.harness.change_worktree import create_worktree

        state = create_worktree(self.root, {"task": "Implement a change"})
        created = Path(state["path"])
        self.addCleanup(
            lambda: _git(self.root, "worktree", "remove", "--force", str(created))
        )
        self.assertFalse((created / "generated").exists())


class CreateCandidateTests(unittest.TestCase):
    """A candidate starts from the primary's committed HEAD on its own branch."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "primary"
        self.root.mkdir()
        (self.root / "shared.txt").write_text("committed\n")
        (self.root / ".gitmodules").write_text(
            '[submodule "reference/lib"]\n\tpath = reference/lib\n'
            "\turl = https://example.invalid/lib.git\n"
        )
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "add", "-A")
        _git(
            self.root,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        )
        # A vendored reference checkout that exists only in the primary's working tree.
        (self.root / "reference/lib").mkdir(parents=True)
        (self.root / "reference/lib/.git").write_text("gitdir: elsewhere\n")
        (self.root / "reference/lib/api.md").write_text("## connect(url)\n")

    def create(self, root: Path, task: dict) -> dict:
        from concorde.harness.change_worktree import create_worktree

        state = create_worktree(root, task)
        created = Path(state["path"])
        self.addCleanup(
            lambda: _git(self.root, "worktree", "remove", "--force", str(created))
        )
        return state

    @verifies("scenario.worktrees.create-candidate")
    def test_candidate_starts_at_committed_head_and_registers_the_change(self):
        from concorde.harness.change_worktree import read_change

        head = _git(self.root, "rev-parse", "HEAD").stdout.strip()
        (self.root / "shared.txt").write_text("uncommitted primary edit\n")
        task = {
            "target_id": "module.project",
            "task": "Implement a change",
            "constraints": ["Keep the API"],
        }
        state = self.create(self.root, task)
        created = Path(state["path"])
        self.assertRegex(state["branch"], r"^concorde/[0-9a-f-]{36}$")
        self.assertEqual(head, state["base_commit"])
        self.assertEqual(str(self.root.resolve()), state["primary_worktree"])
        self.assertEqual(
            state["branch"],
            _git(created, "branch", "--show-current").stdout.strip(),
        )
        self.assertEqual(head, _git(created, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual("committed\n", (created / "shared.txt").read_text())
        self.assertEqual(
            "## connect(url)\n", (created / "reference/lib/api.md").read_text()
        )
        self.assertFalse((created / "reference/lib/.git").exists())
        change = read_change(created, required=True)
        self.assertEqual(state["change_id"], change["change_id"])
        self.assertEqual(
            (task["task"], task["target_id"], task["constraints"]),
            (change["task"], change["target_hint"], change["constraints"]),
        )
        self.assertTrue(
            (self.root / ".concorde/status" / f"{state['change_id']}.json").is_file()
        )
        self.assertFalse((created / ".concorde/status").exists())

    @verifies("scenario.worktrees.create-candidate")
    def test_linked_worktree_or_detached_primary_cannot_create_a_candidate(self):
        state = self.create(self.root, {"task": "First change"})
        with self.assertRaises(SpecError) as linked:
            self.create(Path(state["path"]), {"task": "Nested change"})
        self.assertEqual("workspace_mismatch", linked.exception.code)
        _git(self.root, "checkout", "-q", "--detach")
        with self.assertRaises(SpecError) as detached:
            self.create(self.root, {"task": "Detached change"})
        self.assertEqual("workspace_mismatch", detached.exception.code)


if __name__ == "__main__":
    unittest.main()
