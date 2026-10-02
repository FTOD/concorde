"""``concorde task wait``: a task state, a run's end or a lock's release, without polling."""

from __future__ import annotations

import contextlib
import io
import json
import shlex
import subprocess
import sys
import threading
import time
import unittest

from concorde.kernel.errors import ERROR_SCHEMA
from tests.concorde.support.ignored import TRACES
from concorde.kernel.locking import workspace_lock
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.coordination.tasks import cli, store
from concorde.kernel.tracing import layout
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
            gitignore.read_text() + "".join(f"{path}\n" for path in TRACES)
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
        store_ = store.concorde(self.root)
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

    @verifies("scenario.tasks.wait-rebound")
    def test_a_rebind_wait_returns_the_new_main(self):
        store.rebind(self.root, "t1", "concorde-7d")
        self.later(0.3, lambda: store.rebind(self.root, "t1", "concorde-8e"))
        started = time.monotonic()
        status, value = self.command(
            "wait", "t1", "--rebound", "concorde-7d", "--timeout", "30"
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("concorde-8e", "concorde-7d"), (value["main"], value["former"])
        )
        self.assertLess(time.monotonic() - started, 20)
        # Already rebound: it answers at once.
        status, value = self.command("wait", "t1", "--rebound", "concorde-7d")
        self.assertEqual((0, "concorde-8e"), (status, value["main"]))

        # A task that ends meanwhile ends the wait once its record is closed, whether or not
        # the close can then commit its decision log in the fixture's primary worktree.
        def close():
            with contextlib.suppress(store.TaskError):
                store.close_task(self.root, "t1", "completed", note="done", errors=[])

        closing = threading.Timer(0.3, close)
        closing.start()
        status, value = self.command(
            "wait", "t1", "--rebound", "concorde-8e", "--timeout", "30"
        )
        closing.join()
        self.assertEqual(1, status, value)
        self.assertEqual("wait_unreachable", value["error"]["code"])
        status, value = self.command("wait", "--rebound", "concorde-8e")
        self.assertEqual("invalid_input", value["error"]["code"])

    @verifies("scenario.tasks.wait-lock")
    def test_a_lock_wait_returns_when_its_holder_dies(self):
        path = store.merge_lock_path(self.root)
        code = (
            "import sys\n"
            "from concorde.kernel.tracing import locks\n"
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

    @verifies("scenario.tasks.wait-merge")
    def test_a_merge_wait_returns_after_the_merge_not_its_workspace_lock(self):
        deliver(self.project.worktree("t1"))
        attempt_lock = store.attempt_lock_path(self.root, "t1")
        code = (
            "import sys\n"
            "from concorde.kernel.tracing import locks\n"
            f"with locks.hold({str(attempt_lock)!r}, 'a merge of t1', task='t1',"
            " remove=True):\n"
            "    print('held', flush=True)\n"
            "    sys.stdin.read()\n"
        )
        holder = subprocess.Popen(
            [sys.executable, "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=child_environment(PYTHONPATH=str(REPOSITORY_ROOT / "src")),
        )
        self.addCleanup(holder.wait)
        self.assertEqual("held", holder.stdout.readline().strip())
        # The close of a merge removes the workspace lock long before the merge ends.
        layout.lock_file(store.concorde(self.root), "workspace", "t1").unlink(
            missing_ok=True
        )
        self.later(0.3, holder.stdin.close)
        started = time.monotonic()
        status, value = self.command("wait", "t1", "--merge", "--timeout", "30")
        self.assertEqual(0, status, value)
        self.assertGreaterEqual(time.monotonic() - started, 0.25)
        self.assertEqual("a merge of t1", value["held_by"]["holder"])
        self.assertIsNone(value["attempt"])
        self.assertFalse(attempt_lock.exists())
        # A merge that ran keeps its output with its attempt, found also in the history.
        passing = shlex.join([sys.executable, "-c", "pass"])
        status, merged = self.command("merge", "t1", "--check", passing)
        self.assertEqual(0, status, merged)
        status, value = self.command("wait", "t1", "--merge")
        self.assertEqual(0, status, value)
        self.assertIsNone(value["held_by"])
        attempt = value["attempt"]
        self.assertEqual(
            (1, "ok", "merged"),
            tuple(attempt[key] for key in ("number", "status", "outcome")),
        )
        self.assertEqual(merged["merge"]["log"], attempt["node"])
        self.assertIsNone(attempt["output"])
        status, value = self.command("wait", "--merge")
        self.assertEqual("invalid_input", value["error"]["code"])

    @verifies("scenario.tasks.wait-timeout")
    def test_a_wait_that_times_out_says_so(self):
        store_ = store.concorde(self.root)
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
