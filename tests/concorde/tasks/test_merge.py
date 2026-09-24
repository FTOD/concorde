"""``concorde task merge`` and the merge lock on a real Git repository."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import threading
import unittest

from concorde.errors import ERROR_SCHEMA
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT


def git(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def python(code: str) -> str:
    """A ``--check`` running ``code`` with this Python."""
    return shlex.join([sys.executable, "-c", code])


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        # An installed project ignores the task records, and merges need an identity.
        gitignore = self.root / ".gitignore"
        gitignore.write_text(gitignore.read_text() + ".concorde/tasks/\n")
        git(self.root, "config", "user.name", "t")
        git(self.root, "config", "user.email", "t@t")
        commit(self.root, "ignore task records")

    def command(self, *argv, cwd=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=cwd or self.root)
        return status, json.loads(output.getvalue())

    def refusal(self, *argv):
        status, value = self.command(*argv)
        self.assertEqual(1, status, value)
        validate(value["error"], ERROR_SCHEMA)
        return value["error"]

    def deliver(
        self,
        task_id="t1",
        path="src/a/calc.py",
        text="def add(a, b):\n    return a + b\n",
    ):
        worktree = self.project.worktree(task_id)
        (worktree / path).write_text(text)
        head = commit(worktree, "deliver")
        store.begin_run(
            self.root, task_id, "r-d", "delivery", ["module.a"], False, os.getpid()
        )
        store.record_delivery(
            self.root,
            task_id,
            "r-d",
            head,
            f".concorde/evidence/{task_id}/1.json",
            "r-v",
        )
        store.finish_run(self.root, task_id, "r-d", "ok")
        return head

    def head(self):
        return git(self.root, "rev-parse", "HEAD")

    def assert_untouched(self, before, task_id="t1"):
        self.assertEqual(before, self.head())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        record = store.load_task(self.root, task_id)
        self.assertEqual("delivered", record["state"])
        self.assertTrue(self.project.worktree(task_id).exists())

    @verifies("scenario.tasks.merge")
    def test_merge_a_delivered_task(self):
        # The default check validates the project, so bind the fixture's unbound files first.
        entry = self.root / "specs/a/module.md.json"
        metadata = json.loads(entry.read_text())
        for node in metadata["defines"]:
            if node["id"] == "realization.a.code":
                node["entries"] += [".gitignore", "checks/"]
        entry.write_text(json.dumps(metadata, indent=2) + "\n")
        commit(self.root, "bind every tracked file")
        self.project.open_task("t1")
        head = self.deliver()
        before = self.head()
        status, value = self.command("merge", "t1")
        self.assertEqual(0, status, value)
        self.assertEqual(head, self.head())
        self.assertEqual(
            ("closed", "merged"),
            (value["record"]["state"], value["record"]["closed"]["outcome"]),
        )
        self.assertTrue(value["record"]["closed"]["worktree_removed"])
        self.assertFalse(self.project.worktree("t1").exists())
        merge = value["merge"]
        self.assertEqual((before, head), (merge["before"], merge["after"]))
        self.assertEqual(
            [[sys.executable, "-m", "concorde", "validate"]],
            [check["argv"] for check in merge["checks"]],
        )
        self.assertEqual(0, merge["checks"][0]["exit_code"])
        self.assertGreaterEqual(merge["waited_seconds"], 0)
        log = (self.root / ".concorde/tasks/t1.merge.log").read_text()
        self.assertEqual(str(self.root / ".concorde/tasks/t1.merge.log"), merge["log"])
        self.assertIn('"tool":"validate"', log)
        self.assertIn("[exit 0 after", log)
        self.assertEqual("", store.merge_lock_path(self.root).read_text())

    @verifies("scenario.tasks.merge-checks")
    def test_the_named_checks_replace_the_default(self):
        self.project.open_task("t1")
        self.deliver()
        first, second = python("print('first check')"), python("print('second check')")
        status, value = self.command("merge", "t1", "--check", first, "--check", second)
        self.assertEqual(0, status, value)
        self.assertEqual(
            [shlex.split(first), shlex.split(second)],
            [check["argv"] for check in value["merge"]["checks"]],
        )
        log = (self.root / ".concorde/tasks/t1.merge.log").read_text()
        self.assertLess(log.index("first check"), log.index("second check"))
        self.assertNotIn("validate", log)

    @verifies("scenario.tasks.merge-waits")
    def test_a_second_merge_waits_for_the_first(self):
        self.project.open_task("t1")
        self.deliver()
        taken, release = threading.Event(), threading.Event()

        def hold():
            with store.merge_lock(self.root, "merge", "a", 0):
                taken.set()
                release.wait(10)

        holder = threading.Thread(target=hold)
        holder.start()
        self.assertTrue(taken.wait(10))
        busy = self.refusal("merge", "t1", "--wait", "0.3", "--check", python("pass"))
        self.assertEqual("merge_busy", busy["code"])
        self.assertIn("`concorde task merge` of task a", busy["detail"])
        self.assertIn(f"process {os.getpid()}", busy["detail"])
        self.assertIn("holding it since 20", busy["detail"])
        self.assertEqual("environment", busy["unhandled"]["reason"])
        self.assertEqual("delivered", store.load_task(self.root, "t1")["state"])
        threading.Timer(0.5, release.set).start()
        status, value = self.command(
            "merge", "t1", "--wait", "10", "--check", python("pass")
        )
        holder.join()
        self.assertEqual(0, status, value)
        self.assertGreaterEqual(value["merge"]["waited_seconds"], 0.3)

    @verifies("scenario.tasks.merge-lock-dies")
    def test_a_killed_holder_releases_the_lock(self):
        self.project.open_task("t1")
        self.deliver()
        code = (
            "import sys, time\n"
            f"sys.path.insert(0, {str(REPOSITORY_ROOT / 'src')!r})\n"
            "from pathlib import Path\n"
            "from concorde.tasks import store\n"
            f"with store.merge_lock(Path({str(self.root)!r}), 'merge', 'a', 0):\n"
            "    print('ready', flush=True)\n"
            "    time.sleep(60)\n"
        )
        holder = subprocess.Popen(
            [sys.executable, "-c", code], stdout=subprocess.PIPE, text=True
        )
        self.assertEqual("ready\n", holder.stdout.readline())
        with self.assertRaises(store.TaskError) as raised:
            store.close_task(self.root, "t1", "completed", note="n", wait=0)
        self.assertEqual("merge_busy", raised.exception.code)
        holder.kill()
        holder.wait()
        holder.stdout.close()
        status, value = self.command(
            "merge", "t1", "--wait", "0", "--check", python("pass")
        )
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "merged"),
            (value["record"]["state"], value["record"]["closed"]["outcome"]),
        )

    @verifies("scenario.tasks.merge-open-close-wait")
    def test_open_and_close_wait_for_the_lock(self):
        self.project.open_task("t1")
        before = store.load_task(self.root, "t1")
        with store.merge_lock(self.root, "merge", "a", 0):
            with self.assertRaises(store.TaskError) as opened:
                store.open_task(self.root, "t2", "g", ["module.a"], wait=0.2)
            with self.assertRaises(store.TaskError) as closed:
                store.close_task(self.root, "t1", "completed", note="n", wait=0.2)
        for raised in (opened, closed):
            self.assertEqual("merge_busy", raised.exception.code)
            self.assertIn("`concorde task merge` of task a", str(raised.exception))
        self.assertFalse((self.root / ".concorde/tasks/t2.json").exists())
        self.assertNotIn("concorde/t2", git(self.root, "branch", "--list"))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertTrue(self.project.worktree("t1").exists())

    @verifies("scenario.tasks.merge-conflict")
    def test_a_conflict_is_aborted(self):
        self.project.open_task("t1")
        self.deliver()
        (self.root / "src/a/calc.py").write_text("def add(a, b):\n    return b + a\n")
        before = commit(self.root, "a conflicting change on the primary branch")
        error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual("merge_conflict", error["code"])
        self.assertIn("src/a/calc.py", error["detail"])
        self.assertEqual("decision", error["unhandled"]["reason"])
        self.assertIn(
            "merge the primary branch into the task branch", error["options"][0]
        )
        self.assert_untouched(before)

    @verifies("scenario.tasks.merge-check-failed")
    def test_a_failed_check_undoes_the_merge(self):
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
        failing = python("import sys; print('boom'); sys.exit(1)")
        error = self.refusal("merge", "t1", "--check", failing)
        self.assertEqual("check_failed", error["code"])
        log = self.root / ".concorde/tasks/t1.merge.log"
        for part in ("exited 1", "boom", str(log), f"back at {before}, clean"):
            self.assertIn(part, error["detail"])
        self.assert_untouched(before)

    @verifies("scenario.tasks.merge-check-failed")
    def test_checks_that_leave_changes_undo_the_merge(self):
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
        writing = python("open('src/bmod/extra.py', 'w').write('x = 1\\n')")
        error = self.refusal("merge", "t1", "--check", writing)
        self.assertEqual("check_failed", error["code"])
        self.assertIn("left 1 uncommitted path(s)", error["detail"])
        self.assertIn("src/bmod/extra.py", error["detail"])
        self.assertEqual(before, self.head())
        self.assertEqual("delivered", store.load_task(self.root, "t1")["state"])

    @verifies("scenario.tasks.merge-refused-early")
    def test_a_merge_that_cannot_close_is_refused_before_merging(self):
        self.project.open_task("t1")
        before = self.head()
        self.assertEqual("not_merged", self.refusal("merge", "t1")["code"])
        self.deliver()
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text("changed after delivery\n")
        self.assertEqual("dirty_worktree", self.refusal("merge", "t1")["code"])
        git(worktree, "checkout", "--", "src/a/calc.py")
        (self.root / "notes.txt").write_text("the developer's notes\n")
        error = self.refusal("merge", "t1")
        self.assertEqual(
            ("primary_dirty", "decision"), (error["code"], error["unhandled"]["reason"])
        )
        self.assertIn("notes.txt", error["detail"])
        (self.root / "notes.txt").unlink()
        git(self.root, "checkout", "-q", "--detach")
        error = self.refusal("merge", "t1")
        self.assertEqual("primary_dirty", error["code"])
        self.assertIn("detached HEAD", error["detail"])
        git(self.root, "checkout", "-q", "-")
        self.assert_untouched(before)
        self.assertFalse((self.root / ".concorde/tasks/t1.merge.log").exists())


if __name__ == "__main__":
    unittest.main()
