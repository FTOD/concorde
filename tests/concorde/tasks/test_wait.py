"""``concorde task wait``: a task state, a run's end or a lock's release, without polling."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import threading
import time
import unittest

from concorde.errors import ERROR_SCHEMA
from concorde.execution.runs import workspace_lock
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from concorde.tracing import layout
from tests.concorde.support.environment import child_environment
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver, git


class WaitTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in layout.IGNORED)
        )
        git(self.root, "config", "user.name", "t")
        git(self.root, "config", "user.email", "t@t")
        commit(self.root, "ignore task records")
        self.project.open_task("t1")

    def command(self, *argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=self.root)
        return status, json.loads(output.getvalue())

    def later(self, seconds, action):
        timer = threading.Timer(seconds, action)
        timer.start()
        self.addCleanup(timer.cancel)

    @verifies("scenario.tasks.wait-task")
    def test_a_task_wait_returns_when_the_state_is_reached(self):
        store_ = store.workspace_store(self.root, "t1")
        entered, leave = threading.Event(), threading.Event()

        def delivery_run():
            with workspace_lock(store_, "t1", "a delivery run"):
                entered.set()
                leave.wait(30)
                deliver(self.project.worktree("t1"))

        runner = threading.Thread(target=delivery_run)
        runner.start()
        self.addCleanup(runner.join)
        entered.wait(10)
        self.later(0.3, leave.set)
        started = time.monotonic()
        status, value = self.command(
            "wait", "t1", "--until", "delivered", "--timeout", "30"
        )
        self.assertEqual(0, status, value)
        self.assertEqual("delivered", value["state"])
        self.assertLess(time.monotonic() - started, 20)
        # A task already in the state answers at once.
        status, value = self.command("wait", "t1", "--until", "delivered,closed")
        self.assertEqual((0, "delivered"), (status, value["state"]))

    @verifies("scenario.tasks.wait-task-unreachable")
    def test_a_task_that_ended_elsewhere_ends_the_wait(self):
        self.later(
            0.3,
            lambda: store.close_task(
                self.root, "t1", "completed", note="done", errors=[]
            ),
        )
        status, value = self.command(
            "wait", "t1", "--until", "delivered", "--timeout", "30"
        )
        self.assertEqual(1, status, value)
        validate(value["error"], ERROR_SCHEMA)
        self.assertEqual("wait_unreachable", value["error"]["code"])
        status, value = self.command("wait", "t1", "--until", "active")
        self.assertEqual("invalid_input", value["error"]["code"])

    @verifies("scenario.tasks.wait-lock")
    def test_a_lock_wait_returns_when_its_holder_dies(self):
        path = store.merge_lock_path(self.root)
        code = (
            "import sys\n"
            "from concorde.tracing import locks\n"
            f"with locks.hold({str(path)!r}, 'a test holder', task='t9'):\n"
            "    print('held', flush=True)\n"
            "    sys.stdin.read()\n"
        )
        holder = subprocess.Popen(
            [sys.executable, "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=child_environment(
                PYTHONPATH=str(REPOSITORY_ROOT / "src"), CLAUDE_CODE_SESSION_ID="s-1"
            ),
        )
        self.addCleanup(holder.wait)
        self.assertEqual("held", holder.stdout.readline().strip())
        self.later(0.3, holder.kill)
        status, value = self.command("wait", "--lock", "merge", "--timeout", "30")
        self.assertEqual(0, status, value)
        self.assertTrue(value["released"])
        self.assertEqual(
            ("s-1", "t9"), (value["held_by"]["session"], value["held_by"]["task"])
        )

    @verifies("scenario.tasks.wait-timeout")
    def test_a_wait_that_times_out_says_so(self):
        store_ = store.workspace_store(self.root, "t1")
        with workspace_lock(store_, "t1", "a long run"):
            status, value = self.command(
                "wait", "t1", "--lock", "workspace", "--timeout", "0.3"
            )
        self.assertEqual(1, status, value)
        self.assertEqual("wait_timeout", value["error"]["code"])
        self.assertEqual("environment", value["error"]["unhandled"]["reason"])
        status, value = self.command("wait", "--run", "r-nothing")
        self.assertEqual("unknown_run", value["error"]["code"])


if __name__ == "__main__":
    unittest.main()
