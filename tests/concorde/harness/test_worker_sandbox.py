"""The worker sandbox: the mount plan derived from a launch, and its real enforcement on Linux.

The enforcement tests deliberately fail, rather than skip, when the Linux boundary is unavailable:
a worker never runs unconfined, so a host that cannot enforce the boundary cannot run workers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import worker_sandbox
from concorde.harness.check_executor import CheckSandboxError
from concorde.harness.worker_sandbox import (
    WORKER_SANDBOX_POLICY,
    WorkerSandboxError,
    bubblewrap_argv,
    create_placeholders,
    plan_mounts,
    remove_untouched_placeholders,
    unavailable_reason,
)
from concorde.spec.verification import verifies


def git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments], check=True, capture_output=True
    )


class SandboxFixture(unittest.TestCase):
    def setUp(self) -> None:
        # The fixture lives inside the repository, not under /tmp: the sandbox replaces /tmp with
        # a private tmpfs, and the fixture's "home" must stay visible like a developer's own.
        base = Path(__file__).resolve().parents[1] / ".tmp"
        base.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(temporary.cleanup)
        self.temp = Path(temporary.name).resolve()
        self.home = self.temp / "home"
        (self.home / ".ssh").mkdir(parents=True)
        (self.home / ".ssh/id_ed25519").write_text("SECRET KEY\n")
        (self.home / ".netrc").write_text("machine example.invalid password hunter2\n")
        (self.home / ".pi/agent").mkdir(parents=True)
        (self.home / ".pi/agent/auth.json").write_text('{"token": "SECRET"}')
        (self.home / "toolchain").mkdir()
        (self.home / "toolchain/tool.txt").write_text("tool\n")
        self.primary = self.temp / "primary"
        self.primary.mkdir()
        (self.primary / "README.md").write_text("primary\n")
        (self.primary / "app.py").write_text("print('app')\n")
        (self.primary / "src").mkdir()
        (self.primary / "src/module.py").write_text("x = 1\n")
        git(self.primary, "init", "-q", "-b", "main")
        git(self.primary, "config", "user.name", "Concorde Test")
        git(self.primary, "config", "user.email", "concorde-test@example.invalid")
        git(self.primary, "add", "-A")
        git(self.primary, "commit", "-qm", "fixture")
        self.candidate = self.temp / "candidate"
        git(
            self.primary,
            "worktree",
            "add",
            "-q",
            "-b",
            "candidate",
            str(self.candidate),
        )
        self.run_dir = self.temp / "run"
        (self.run_dir / "home").mkdir(parents=True)
        (self.run_dir / "tmp").mkdir()
        self.write_paths = ["src/", "app.py", "pkg/new.py", "docs/"]


class MountPlanTests(SandboxFixture):
    @verifies("scenario.harness.worker-sandbox")
    def test_plan_masks_secrets_and_other_worktrees_and_binds_only_the_grant(self):
        plan = plan_mounts(
            self.candidate, self.write_paths, self.run_dir, home=self.home
        )
        self.assertEqual(WORKER_SANDBOX_POLICY, plan.policy)
        self.assertEqual(str(self.candidate), plan.workspace)
        self.assertEqual(str(self.run_dir / "home"), plan.home)
        self.assertEqual(
            {
                str(self.home / ".ssh"),
                str(self.home / ".netrc"),
                str(self.home / ".pi"),
            },
            set(plan.masks),
        )
        self.assertEqual((str(self.primary),), plan.other_worktrees)
        self.assertEqual(str(self.primary / ".git"), plan.git_common_dir)
        self.assertEqual(
            (str(self.candidate / "src"), str(self.candidate / "app.py")), plan.writable
        )
        self.assertEqual(
            (str(self.candidate / "pkg/new.py"), str(self.candidate / "docs") + "/"),
            plan.pending,
        )
        self.assertEqual(str(self.run_dir / "mask"), plan.mask_file)
        argv = bubblewrap_argv(plan, ["true"])
        self.assertTrue(argv[0].endswith("bwrap"), argv[0])
        text = " ".join(argv)
        self.assertIn("--ro-bind / /", text)
        self.assertIn(f"--tmpfs {self.home / '.ssh'}", text)
        self.assertIn(f"--ro-bind {self.run_dir / 'mask'} {self.home / '.netrc'}", text)
        self.assertEqual(0, (self.run_dir / "mask").stat().st_size)
        self.assertIn(f"--tmpfs {self.primary}", text)
        self.assertIn(
            f"--ro-bind {self.primary / '.git'} {self.primary / '.git'}", text
        )
        self.assertIn(f"--ro-bind {self.candidate} {self.candidate}", text)
        self.assertIn(f"--bind {self.run_dir} {self.run_dir}", text)
        self.assertIn(f"--bind {self.candidate / 'src'} {self.candidate / 'src'}", text)
        self.assertIn(
            f"--bind {self.candidate / 'app.py'} {self.candidate / 'app.py'}", text
        )
        # Later mounts stack on earlier ones: the shared Git directory reappears inside the
        # masked primary, and the workspace and run directory follow the private /tmp.
        self.assertLess(
            text.index(f"--tmpfs {self.primary}"),
            text.index(f"--ro-bind {self.primary / '.git'}"),
        )
        self.assertLess(
            text.index("--tmpfs /tmp"), text.index(f"--ro-bind {self.candidate}")
        )
        self.assertLess(
            text.index(f"--ro-bind {self.candidate}"),
            text.index(f"--bind {self.candidate / 'src'}"),
        )
        self.assertEqual(["--chdir", str(self.candidate), "--", "true"], argv[-4:])
        self.assertNotIn("--setenv", argv)

    @verifies("scenario.harness.worker-sandbox")
    def test_placeholders_are_created_for_pending_entries_and_removed_when_untouched(
        self,
    ):
        plan = plan_mounts(
            self.candidate, self.write_paths, self.run_dir, home=self.home
        )
        created = create_placeholders(plan)
        self.assertEqual(
            [
                str(self.candidate / "docs"),
                str(self.candidate / "pkg/new.py"),
                str(self.candidate / "pkg"),
            ],
            list(created),
        )
        self.assertTrue((self.candidate / "pkg/new.py").is_file())
        self.assertEqual(0, (self.candidate / "pkg/new.py").stat().st_size)
        self.assertTrue((self.candidate / "docs").is_dir())
        remove_untouched_placeholders(created)
        self.assertFalse((self.candidate / "pkg").exists())
        self.assertFalse((self.candidate / "docs").exists())
        created = create_placeholders(plan)
        (self.candidate / "pkg/new.py").write_text("print('new')\n")
        (self.candidate / "docs/index.md").write_text("# docs\n")
        remove_untouched_placeholders(created)
        self.assertEqual("print('new')\n", (self.candidate / "pkg/new.py").read_text())
        self.assertEqual("# docs\n", (self.candidate / "docs/index.md").read_text())

    @verifies("scenario.harness.worker-sandbox")
    def test_write_entries_outside_the_workspace_and_symlinks_are_refused(self):
        (self.candidate / "escape").symlink_to(self.temp)
        for entry in ("../primary/app.py", "escape/secret.txt", "escape"):
            with self.subTest(entry=entry):
                with self.assertRaises(WorkerSandboxError):
                    plan_mounts(self.candidate, [entry], self.run_dir, home=self.home)
        with self.assertRaises(WorkerSandboxError):
            plan_mounts(self.candidate, [], self.candidate / "run", home=self.home)


class SandboxEnforcementTests(SandboxFixture):
    PROBE = r"""
import json, os, sys
candidate, primary, home, run_dir = sys.argv[1:5]
out = {}
def attempt(name, action):
    try:
        out[name] = action()
    except OSError as error:
        out[name] = "error:" + error.__class__.__name__
def write(path, text):
    with open(path, "w") as stream:
        stream.write(text)
    return "written"
attempt("grant_dir", lambda: write(os.path.join(candidate, "src/new.txt"), "new"))
attempt("grant_file", lambda: write(os.path.join(candidate, "app.py"), "changed"))
attempt("pending_file", lambda: write(os.path.join(candidate, "pkg/new.py"), "pending"))
attempt("outside_grant", lambda: write(os.path.join(candidate, "other.txt"), "no"))
attempt("run_dir", lambda: write(os.path.join(run_dir, "note.txt"), "run"))
attempt("netrc", lambda: open(os.path.join(home, ".netrc")).read())
attempt("ssh", lambda: os.listdir(os.path.join(home, ".ssh")))
attempt("pi_auth", lambda: open(os.path.join(home, ".pi/agent/auth.json")).read())
attempt("toolchain", lambda: open(os.path.join(home, "toolchain/tool.txt")).read())
attempt("primary_file", lambda: os.path.exists(os.path.join(primary, "README.md")))
attempt("primary_git", lambda: os.path.isdir(os.path.join(primary, ".git")))
attempt("host_tmp", lambda: os.path.exists(os.environ["HOST_TMP_MARKER"]))
attempt("pid", lambda: os.getpid())
attempt("env_home", lambda: os.environ["HOME"])
attempt("cwd", lambda: os.getcwd())
print(json.dumps(out))
"""

    @verifies("scenario.harness.worker-sandbox")
    def test_the_process_writes_only_the_grant_and_sees_no_secret_or_other_worktree(
        self,
    ):
        plan = plan_mounts(
            self.candidate,
            self.write_paths,
            self.run_dir,
            home=self.home,
            # This fixture can itself be below /tmp in a candidate checkout. Restore
            # only its explicitly trusted toolchain asset, never its fake home tree.
            runtime_files=(self.home / "toolchain/tool.txt",),
        )
        created = create_placeholders(plan)
        with tempfile.NamedTemporaryFile(
            prefix="concorde-host-marker-", dir="/tmp"
        ) as marker:
            argv = bubblewrap_argv(
                plan,
                [
                    # This tests the OS boundary using only the standard library, not
                    # venv package semantics. Its /tmp venv alias is intentionally hidden.
                    str(Path(sys.executable).resolve()),
                    "-c",
                    self.PROBE,
                    str(self.candidate),
                    str(self.primary),
                    str(self.home),
                    str(self.run_dir),
                ],
            )
            process = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=60,
                env={
                    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                    "HOME": plan.home,
                    "LANG": "C.UTF-8",
                    "HOST_TMP_MARKER": marker.name,
                },
            )
        self.assertEqual(0, process.returncode, process.stderr)
        observed = json.loads(process.stdout)
        remove_untouched_placeholders(created)
        self.assertEqual("written", observed["grant_dir"])
        self.assertEqual("written", observed["grant_file"])
        self.assertEqual("written", observed["pending_file"])
        self.assertEqual("error:OSError", observed["outside_grant"])
        self.assertEqual("written", observed["run_dir"])
        self.assertEqual("", observed["netrc"])
        self.assertEqual([], observed["ssh"])
        self.assertEqual("error:FileNotFoundError", observed["pi_auth"])
        self.assertEqual("tool\n", observed["toolchain"])
        self.assertFalse(observed["primary_file"])
        self.assertTrue(observed["primary_git"])
        self.assertFalse(observed["host_tmp"])
        self.assertLess(observed["pid"], 100)
        self.assertEqual(plan.home, observed["env_home"])
        self.assertEqual(str(self.candidate), observed["cwd"])
        self.assertEqual("new", (self.candidate / "src/new.txt").read_text())
        self.assertEqual("changed", (self.candidate / "app.py").read_text())
        self.assertEqual("pending", (self.candidate / "pkg/new.py").read_text())
        self.assertFalse((self.candidate / "other.txt").exists())
        self.assertFalse((self.candidate / "docs").exists())
        self.assertEqual("SECRET KEY\n", (self.home / ".ssh/id_ed25519").read_text())

    @verifies("scenario.harness.worker-sandbox-unavailable")
    def test_an_unavailable_boundary_refuses_the_launch(self):
        plan = plan_mounts(
            self.candidate, self.write_paths, self.run_dir, home=self.home
        )
        with patch.object(
            worker_sandbox,
            "_bubblewrap",
            side_effect=CheckSandboxError("no bubblewrap"),
        ):
            self.assertIn("no bubblewrap", unavailable_reason() or "")
            with self.assertRaisesRegex(WorkerSandboxError, "no bubblewrap"):
                bubblewrap_argv(plan, ["true"])
        with patch.object(worker_sandbox.sys, "platform", "darwin"):
            self.assertIn("darwin", unavailable_reason() or "")
        self.assertIsNone(unavailable_reason())


if __name__ == "__main__":
    unittest.main()
