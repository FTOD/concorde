"""``concorde task session``: the boundary it writes and the session it starts and records."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from concorde.tasks import session, store
from tests.concorde.support.operation_project import OperationProject


class FakeClaude:
    """Stands in for ``claude --bg``: records the call and answers like Claude Code."""

    def __init__(self, returncode=0, stdout="backgrounded · 33afbc14 · task-t1\n"):
        self.returncode, self.stdout = returncode, stdout
        self.calls = []

    def __call__(self, command, **options):
        self.calls.append((command, options))
        return subprocess.CompletedProcess(command, self.returncode, self.stdout, "")


class TaskSessionTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.project.open_task("t1", goal="Let reports carry a severity.")
        self.worktree = self.project.worktree("t1")

    @verifies("scenario.tasks.session-start")
    def test_start_a_task_session(self):
        claude = FakeClaude()
        started = session.start(
            self.root, "t1", "concorde-7d", run=claude, home=self.project.home
        )
        directory = self.root / ".concorde/tasks/t1.session"
        self.assertTrue((directory / "settings.json").is_file())
        self.assertTrue((directory / "write_hook.py").is_file())
        [(command, options)] = claude.calls
        self.assertEqual(self.worktree, Path(options["cwd"]))
        self.assertEqual(["claude", "--bg", "--name", "task-t1"], command[:4])
        self.assertIn("--settings", command)
        self.assertEqual(
            str(directory / "settings.json"), command[command.index("--settings") + 1]
        )
        mode = command[command.index("--permission-mode") + 1]
        self.assertEqual("auto", mode)
        self.assertNotIn("--allow-dangerously-skip-permissions", command)
        brief = command[-1]
        self.assertIn("You are a task session", brief)
        self.assertIn("Let reports carry a severity.", brief)
        self.assertIn("`concorde-7d`", brief)
        self.assertIn(str(self.worktree), brief)
        self.assertEqual(
            ("33afbc14", "task-t1", "concorde-7d"),
            (started["id"], started["name"], started["main"]),
        )
        self.assertEqual([started], store.load_task(self.root, "t1")["sessions"])

    @verifies("scenario.tasks.session-start")
    def test_a_session_claude_code_did_not_start_is_refused(self):
        claude = FakeClaude(
            returncode=1, stdout="Workspace not trusted. Run `claude` in ... once."
        )
        before = store.load_task(self.root, "t1")
        with self.assertRaises(store.TaskError) as raised:
            session.start(self.root, "t1", "m", run=claude, home=self.project.home)
        self.assertEqual("session_failed", raised.exception.code)
        self.assertIn("Workspace not trusted", str(raised.exception))
        self.assertEqual(before, store.load_task(self.root, "t1"))

    @verifies("scenario.tasks.session-start")
    def test_a_closed_task_starts_no_session(self):
        store.close_task(self.root, "t1", "completed", note="tried it")
        with self.assertRaises(store.TaskError) as raised:
            session.start(
                self.root, "t1", "m", run=FakeClaude(), home=self.project.home
            )
        self.assertEqual("task_closed", raised.exception.code)

    def hook(self, target: Path) -> dict | None:
        """The written hook's decision on an Edit of ``target``: None allows."""
        hook = self.root / ".concorde/tasks/t1.session/write_hook.py"
        decided = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(
                {
                    "tool_name": "Edit",
                    "cwd": str(self.worktree),
                    "tool_input": {"file_path": str(target)},
                }
            ),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(decided.stdout) if decided.stdout.strip() else None

    @verifies("scenario.tasks.session-boundary")
    def test_the_boundary_confines_the_session_to_its_task(self):
        shown = session.start(
            self.root, "t1", "m", dry_run=True, home=self.project.home
        )
        self.assertEqual(str(self.worktree), shown["cwd"])
        self.assertIsNone(self.hook(self.worktree / "src/a/calc.py"))
        self.assertIsNone(self.hook(self.root / ".concorde/tasks/t1.decisions.md"))
        denied = self.hook(self.root / "src/a/calc.py")
        self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])
        self.assertIn(
            str(self.worktree), denied["hookSpecificOutput"]["permissionDecisionReason"]
        )
        settings = json.loads(Path(shown["settings"]).read_text())
        sandbox = settings["sandbox"]
        self.assertTrue(sandbox["enabled"])
        self.assertFalse(sandbox["allowUnsandboxedCommands"])
        self.assertEqual({"allowedDomains": ["*"]}, sandbox["network"])
        home = Path(os.path.realpath(self.project.home))
        self.assertEqual(
            sorted(
                str(Path(os.path.realpath(path)))
                for path in (
                    self.worktree,
                    self.root / ".git",
                    self.root / ".concorde/runs",
                    self.root / ".concorde/tasks",
                    home / ".cache",
                    home / ".npm",
                )
            ),
            sandbox["filesystem"]["allowWrite"],
        )
        self.assertEqual([], store.load_task(self.root, "t1")["sessions"])


if __name__ == "__main__":
    unittest.main()
