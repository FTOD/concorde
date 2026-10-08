"""The reference initializer writes the shared Git configuration only to register a submodule."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


def load_script():
    spec = importlib.util.spec_from_file_location(
        "init_references", REPOSITORY_ROOT / "scripts/development/init-references.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", "-c", "protocol.file.allow=always", *arguments),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


class InitReferencesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        identity = ("-c", "user.name=t", "-c", "user.email=t@example.com")
        upstream = root / "upstream"
        git(root, "init", "--quiet", "-b", "main", upstream.as_posix())
        (upstream / "README.md").write_text("reference\n")
        git(upstream, "add", "README.md")
        git(upstream, *identity, "commit", "--quiet", "-m", "reference")
        self.primary = root / "primary"
        git(root, "init", "--quiet", "-b", "main", self.primary.as_posix())
        for path in ("references/r", "references/s"):
            git(
                self.primary,
                "submodule",
                "add",
                "--quiet",
                upstream.as_posix(),
                path,
            )
        # As in this checkout, Git ignores the skill links the script makes.
        (self.primary / ".gitignore").write_text(
            "".join(
                f".claude/skills/{name}\n"
                for name in ("concorde", "concorde-development")
            )
        )
        git(self.primary, "add", ".gitignore")
        git(self.primary, *identity, "commit", "--quiet", "-m", "vendor")
        self.worktree = root / "task"
        git(self.primary, "worktree", "add", "--quiet", self.worktree.as_posix())
        self.upstream = upstream
        self.identity = identity
        self.config = self.primary / ".git/config"
        self.lock = self.primary / ".git/config.lock"
        self.script = load_script()

    def run_script(self) -> str:
        output = io.StringIO()
        with (
            patch.object(self.script, "ROOT", self.worktree),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(self.script.main([]), 0)
        return output.getvalue()

    @verifies("scenario.concorde.references-registered-once")
    def test_registered_submodule_is_checked_out_while_the_lock_is_held(self):
        before = self.config.read_bytes()
        self.lock.write_bytes(b"")
        self.lock.chmod(0o444)
        output = self.run_script()
        for path in ("references/r", "references/s"):
            self.assertIn(f"{path}: initialized", output)
            self.assertEqual(
                (self.worktree / path / "README.md").read_text(), "reference\n"
            )
        self.assertEqual(self.config.read_bytes(), before)
        self.assertTrue(self.lock.exists())

    @verifies("scenario.concorde.references-unregistered-refused")
    def test_unregistered_submodule_under_a_held_lock_is_refused_in_detail(self):
        git(self.primary, "config", "--remove-section", "submodule.references/r")
        before = self.config.read_bytes()
        self.lock.write_bytes(b"")
        self.lock.chmod(0o444)
        with (
            patch.object(self.script, "ROOT", self.worktree),
            self.assertRaises(SystemExit) as refused,
        ):
            self.script.main([])
        message = str(refused.exception.code)
        self.assertIn("references/r", message)
        self.assertIn(self.lock.as_posix(), message)
        self.assertIn("writing the shared configuration", message)
        self.assertIn("never delete the lock", message)
        self.assertTrue(self.lock.exists())
        self.assertEqual(self.config.read_bytes(), before)
        # The registered submodule is not checked out either.
        for path in ("references/r", "references/s"):
            self.assertFalse((self.worktree / path / ".git").exists())

    @verifies("scenario.concorde.references-registered-when-free")
    def test_unregistered_submodule_is_registered_when_the_lock_is_free(self):
        git(self.primary, "config", "--remove-section", "submodule.references/r")
        output = self.run_script()
        self.assertIn("references/r: initialized", output)
        self.assertEqual(
            git(self.primary, "config", "--get", "submodule.references/r.active"),
            "true",
        )
        for path in ("references/r", "references/s"):
            self.assertTrue((self.worktree / path / "README.md").is_file())

    @verifies("scenario.concorde.references-completed")
    def test_a_clone_whose_fetch_failed_is_completed_on_the_next_run(self):
        recorded = git(self.worktree, "ls-files", "--stage", "references/r").split()[1]
        # The upstream moved on, so a clone left unchecked out sits on another commit.
        (self.upstream / "NEWS.md").write_text("later\n")
        git(self.upstream, "add", "NEWS.md")
        git(self.upstream, *self.identity, "commit", "--quiet", "-m", "later")
        later = git(self.upstream, "rev-parse", "HEAD")
        real = self.script.git

        def failing_fetch(*arguments, **options):
            if arguments[0] == "fetch":
                return subprocess.CompletedProcess(
                    arguments, 128, "", "connection reset"
                )
            return real(*arguments, **options)

        with (
            patch.object(self.script, "ROOT", self.worktree),
            patch.object(self.script, "git", failing_fetch),
            self.assertRaises(SystemExit) as failed,
        ):
            self.script.main([])
        self.assertIn("cannot fetch", str(failed.exception.code))
        reference = self.worktree / "references/r"
        self.assertTrue((reference / ".git").exists())
        self.assertFalse((reference / "README.md").exists())
        output = io.StringIO()
        with (
            patch.object(self.script, "ROOT", self.worktree),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(1, self.script.main(["--check"]))
        self.assertIn(
            f"references/r: not at the recorded commit (at {later}) @ {recorded}",
            output.getvalue(),
        )
        output = self.run_script()
        self.assertIn(f"references/r: completed @ {recorded} (was at {later})", output)
        self.assertEqual(recorded, git(reference, "rev-parse", "HEAD"))
        self.assertEqual("reference\n", (reference / "README.md").read_text())
        self.assertEqual("", git(self.worktree, "status", "--porcelain"))
        self.assertIn(f"references/r: checked out @ {recorded}", self.run_script())

    @verifies("scenario.concorde.skill-links-prepared")
    def test_skill_links_are_made_and_a_real_directory_is_left(self):
        skills = self.worktree / ".claude/skills"
        skills.mkdir(parents=True)
        (skills / "concorde-development").symlink_to("../../elsewhere")
        output = io.StringIO()
        with (
            patch.object(self.script, "ROOT", self.worktree),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(1, self.script.main(["--check"]))
        self.assertIn(
            ".claude/skills/concorde: missing, not linked to ../../generated/skills/concorde",
            output.getvalue(),
        )
        self.assertIn(
            ".claude/skills/concorde-development: links to ../../elsewhere, not "
            "../../generated/skills/concorde-development",
            output.getvalue(),
        )
        self.assertFalse((skills / "concorde").is_symlink())
        self.assertEqual(
            "../../elsewhere", os.readlink(skills / "concorde-development")
        )
        output = self.run_script()
        self.assertIn(
            ".claude/skills/concorde-development: relinked to "
            "../../generated/skills/concorde-development (was ../../elsewhere)",
            output,
        )
        for name in ("concorde", "concorde-development"):
            self.assertEqual(
                f"../../generated/skills/{name}", os.readlink(skills / name)
            )
        again = self.run_script()
        for name in ("concorde", "concorde-development"):
            self.assertIn(
                f".claude/skills/{name}: linked to ../../generated/skills/{name}", again
            )
        self.assertNotIn("relinked", again)
        self.assertEqual("", git(self.worktree, "status", "--porcelain"))
        # A real directory in the place of a link is never replaced.
        (skills / "concorde").unlink()
        (skills / "concorde").mkdir()
        (skills / "concorde" / "SKILL.md").write_text("own\n")
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            self.run_script()
        self.assertIn(
            ".claude/skills/concorde: a directory stands where the link to "
            "../../generated/skills/concorde goes and is left as it is",
            errors.getvalue(),
        )
        self.assertFalse((skills / "concorde").is_symlink())
        self.assertEqual("own\n", (skills / "concorde" / "SKILL.md").read_text())


if __name__ == "__main__":
    unittest.main()
