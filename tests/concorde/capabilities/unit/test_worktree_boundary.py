import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.worktree import (
    WorktreeBoundaryError,
    inspect_worktree,
    require_isolated_worktree,
)


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class WorktreeBoundaryTests(unittest.TestCase):
    def create_repository(self, parent: Path) -> Path:
        root = parent / "primary"
        root.mkdir()
        git(root, "init", "-q")
        (root / "tracked.txt").write_text("committed\n", encoding="utf-8")
        git(root, "add", "tracked.txt")
        git(
            root,
            "-c",
            "user.name=Concorde Test",
            "-c",
            "user.email=concorde@example.invalid",
            "commit",
            "-qm",
            "initial",
        )
        return root

    def test_primary_worktree_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.create_repository(Path(directory))
            boundary = inspect_worktree(root)

            self.assertFalse(boundary.isolated)
            self.assertEqual(boundary.head, git(root, "rev-parse", "HEAD"))
            with self.assertRaisesRegex(
                WorktreeBoundaryError, "not allowed in the primary Git worktree"
            ):
                require_isolated_worktree(root)
            self.assertEqual(
                require_isolated_worktree(
                    root, allow_primary_worktree=True
                ),
                boundary,
            )

    def test_linked_worktree_uses_only_committed_base(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            primary = self.create_repository(parent)
            committed = git(primary, "rev-parse", "HEAD")
            (primary / "tracked.txt").write_text("another programmer\n", encoding="utf-8")
            (primary / "untracked.txt").write_text("another programmer\n", encoding="utf-8")
            linked = parent / "isolated"
            git(primary, "worktree", "add", "-qb", "agent/test", str(linked), committed)

            boundary = require_isolated_worktree(linked)

            self.assertTrue(boundary.isolated)
            self.assertEqual(boundary.head, committed)
            self.assertEqual(
                (linked / "tracked.txt").read_text(encoding="utf-8"), "committed\n"
            )
            self.assertFalse((linked / "untracked.txt").exists())

    def test_non_git_directory_has_no_mutation_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(WorktreeBoundaryError):
                require_isolated_worktree(directory)
            explicit = require_isolated_worktree(
                directory, allow_primary_worktree=True
            )
            self.assertFalse(explicit.isolated)
            self.assertEqual(explicit.head, "")

    def test_workspace_adapter_rejects_primary_and_accepts_linked_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            primary = parent / "primary"
            shutil.copytree(CONTEXT_PROJECT, primary)
            git(primary, "init", "-q")
            git(primary, "add", "-f", ".")
            git(
                primary,
                "-c",
                "user.name=Concorde Test",
                "-c",
                "user.email=concorde@example.invalid",
                "commit",
                "-qm",
                "fixture",
            )
            adapter = REPOSITORY_ROOT / "scripts/workspace.py"
            command = (
                sys.executable,
                str(adapter),
                "--project-root",
                str(primary),
                "--phase",
                "plan",
                "--feature-path",
                "specs/example/features/001-deliver.md",
            )

            rejected = subprocess.run(command, capture_output=True, text=True)

            self.assertEqual(rejected.returncode, 1)
            self.assertIn("primary Git worktree", json.loads(rejected.stdout)["error"])

            linked = parent / "isolated"
            git(primary, "worktree", "add", "-qb", "agent/adapter", str(linked), "HEAD")
            accepted = subprocess.run(
                (*command[:3], str(linked), *command[4:]),
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr or accepted.stdout)
            self.assertEqual(json.loads(accepted.stdout)["status"], "resolved")

    def test_actual_operation_execution_rejects_primary_before_agent_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            primary = self.create_repository(Path(directory))
            from tests.concorde.support.operation_json import configure, invocation
            (primary / ".concorde").mkdir()
            (primary / ".concorde/config.json").write_text("{}")
            configure(primary)
            for name in ("concorde-plan", "concorde-standard-dev-loop", "concorde-reflections-triage"):
                with self.subTest(operation=name):
                    data = {"feature_path": "specs/example/features/001-deliver.md", "request": "Apply the bounded change"}
                    if name == "concorde-reflections-triage":
                        data.update(action="investigate", reflection_ids=["R-001"])
                    result = subprocess.run(
                        [sys.executable, str(REPOSITORY_ROOT / "operations" / name / "operation.py")],
                        cwd=primary, capture_output=True, text=True,
                        input=json.dumps(invocation(name, data, mode="execute")),
                    )
                    self.assertEqual(result.returncode, 3)
                    payload = json.loads(result.stdout)
                    self.assertIsNone(payload["output"])
                    self.assertIn("primary Git worktree", payload["errors"][0]["message"])
                    self.assertNotIn("codex exec", result.stderr)



if __name__ == "__main__":
    unittest.main()
