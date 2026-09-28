"""``concorde task merge`` and the merge lock on a real Git repository."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.errors import ERROR_SCHEMA
from concorde.execution.runs import workspace_lock
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import cli, store
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.tasks.deliveries import deliver


def git(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def python(code: str) -> str:
    """A ``--check`` running ``code`` with this Python."""
    return shlex.join([sys.executable, "-c", code])


def killing(marker: Path, then: int = 0) -> str:
    """A ``--check`` that, the first time, kills the merge running it and, once ``marker``
    exists, exits with ``then``."""
    return python(
        "import os, pathlib, signal, sys\n"
        f"marker = pathlib.Path({str(marker)!r})\n"
        "if not marker.exists():\n"
        "    marker.write_text('killed')\n"
        "    os.kill(os.getppid(), signal.SIGKILL)\n"
        f"sys.exit({then})\n"
    )


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
        return deliver(self.project.worktree(task_id), path, text)

    def state(self, task_id="t1"):
        return store.show_task(self.root, task_id)["record"]["state"]

    def head(self):
        return git(self.root, "rev-parse", "HEAD")

    def interrupted(self, then: int = 0):
        """Merge task t1 in a process its check kills; the commits before and after."""
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
        marker = Path(tempfile.mkdtemp()) / "killed"
        self.addCleanup(marker.unlink, missing_ok=True)
        environment = dict(os.environ, PYTHONPATH=str(REPOSITORY_ROOT / "src"))
        merged = subprocess.run(
            [sys.executable, "-m", "concorde", "task", "merge", "t1"]
            + ["--check", killing(marker, then)],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(-signal.SIGKILL, merged.returncode, merged.stdout)
        return before, self.head()

    def assert_untouched(self, before, task_id="t1"):
        self.assertEqual(before, self.head())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertEqual("delivered", self.state(task_id))
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
            [[sys.executable, "-m", "concorde", "spec-validation"]],
            [check["argv"] for check in merge["checks"]],
        )
        self.assertEqual(0, merge["checks"][0]["exit_code"])
        self.assertGreaterEqual(merge["waited_seconds"], 0)
        log = (self.root / ".concorde/tasks/t1.merge.log").read_text()
        self.assertEqual(str(self.root / ".concorde/tasks/t1.merge.log"), merge["log"])
        self.assertIn('"tool":"spec-validation"', log)
        self.assertIn("[exit 0 after", log)
        self.assertEqual("", store.merge_lock_path(self.root).read_text())

    @verifies("scenario.tasks.merge-empty-log")
    def test_a_merge_warns_of_an_unwritten_decision_log(self):
        passing = ["--check", python("")]
        self.project.open_task("t1")
        self.deliver()
        status, value = self.command("merge", "t1", *passing)
        self.assertEqual(0, status, value)
        self.assertEqual("merged", value["record"]["closed"]["outcome"])
        log = self.root / ".concorde/tasks/t1.decisions.md"
        (warning,) = value["warnings"]
        self.assertIn(str(log), warning)
        self.assertIn("holds only its heading and goal", warning)
        # The close still appends how the task ended.
        self.assertIn("## Closed: merged", log.read_text())
        # A log with an entry of its own merges without a warning.
        self.project.open_task("t2")
        with (self.root / ".concorde/tasks/t2.decisions.md").open("a") as stream:
            stream.write(
                "\n## Decisions\n\n- Kept the old name; nothing depends on it.\n"
            )
        self.deliver("t2", path="src/a/other.py")
        status, value = self.command("merge", "t2", *passing)
        self.assertEqual(0, status, value)
        self.assertEqual([], value["warnings"])

    def test_a_task_whose_workspace_ran_merges(self):
        # A bound run leaves its run store and workspace lock in the primary worktree's records
        # directory; an installed project ignores them, so they never block a merge.
        self.project.open_task("t1")
        _, value = self.project.run("task-validation", "--task", "t1")
        self.assertEqual("t1", value["workspace"], value)
        head = self.deliver()
        status, value = self.command("merge", "t1", "--check", python("pass"))
        self.assertEqual(0, status, value)
        self.assertEqual(head, self.head())

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
        self.assertNotIn("spec-validation", log)

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
        self.assertEqual("delivered", self.state())
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
        self.assertEqual("delivered", self.state())

    @verifies("scenario.tasks.merge-sandbox-masks")
    def test_a_path_a_sandbox_masks_in_the_primary_worktree_is_no_change(self):
        bwrap = shutil.which("bwrap")
        sandbox = [bwrap, "--dev-bind", "/", "/"] if bwrap else []
        if not bwrap or subprocess.run([*sandbox, "true"], check=False).returncode != 0:
            self.skipTest("bubblewrap cannot create a sandbox here")
        self.project.open_task("t1")
        self.deliver()
        masked = (".bashrc", ".mcp.json")
        # bwrap leaves each mount point behind as an empty file once the sandbox ends.
        for path in masked:
            self.addCleanup((self.root / path).unlink, missing_ok=True)
        binds = [
            item
            for path in masked
            for item in ("--bind", "/dev/null", str(self.root / path))
        ]
        environment = dict(os.environ, PYTHONPATH=str(REPOSITORY_ROOT / "src"))
        merged = subprocess.run(
            [*sandbox, *binds, sys.executable, "-m", "concorde", "task", "merge", "t1"]
            + ["--check", python("pass")],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertEqual(0, merged.returncode, merged.stdout + merged.stderr)
        self.assertEqual("closed", self.state())

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

    @verifies("scenario.tasks.delivery-unverified")
    def test_a_delivery_commit_that_does_not_verify_is_not_merged(self):
        self.project.open_task("t1")
        head = deliver(self.project.worktree("t1"), bundle_run="r-other")
        before = self.head()
        record = store.load_task(self.root, "t1")
        error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual(
            ("delivery_unverified", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn(head, error["detail"])
        self.assertIn(".concorde/evidence/t1/1.json", error["detail"])
        self.assertIn("readiness run r-other", error["detail"])
        self.assertTrue(error["options"])
        self.assertEqual(before, self.head())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertEqual(record, store.load_task(self.root, "t1"))
        self.assertEqual("active", self.state())
        self.assertFalse((self.root / ".concorde/tasks/t1.merge.log").exists())

    @verifies("scenario.tasks.merge-exact-commit")
    def test_the_merge_merges_the_commit_it_checked(self):
        self.project.open_task("t1")
        checked = self.deliver()
        worktree = self.project.worktree("t1")
        mergeable = store.mergeable
        moved = []

        def moving(primary, task_id):
            found = mergeable(primary, task_id)
            if not moved:
                (worktree / "src/a/late.py").write_text("late = 1\n")
                moved.append(commit(worktree, "a commit after the checks"))
            return found

        store.mergeable = moving
        self.addCleanup(setattr, store, "mergeable", mergeable)
        error = self.refusal("merge", "t1", "--check", python("pass"))
        # The merge took the checked commit, not the branch's new head, and closing refused.
        self.assertEqual("not_merged", error["code"])
        self.assertIn("stays merging", error["detail"])
        self.assertIn("--resume", error["detail"])
        head = self.head()
        self.assertEqual(checked, head)
        self.assertNotEqual(
            0,
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", moved[0], head], cwd=self.root
            ).returncode,
        )
        self.assertEqual("merging", self.state())

    @verifies("scenario.tasks.merge-waits-for-run")
    def test_a_merge_waits_for_the_tasks_run_without_the_merge_lock(self):
        self.project.open_task("t1")
        self.deliver()
        taken, release = threading.Event(), threading.Event()
        held_during_wait = []

        def hold():
            with workspace_lock(self.root / ".concorde", "t1", "run r-1 (delivery)"):
                taken.set()
                release.wait(10)
                # The merge is waiting now; other tasks' merges could take the merge lock.
                held_during_wait.append(store.merge_lock_held(self.root))

        holder = threading.Thread(target=hold)
        holder.start()
        self.assertTrue(taken.wait(10))
        threading.Timer(0.5, release.set).start()
        status, value = self.command(
            "merge", "t1", "--wait", "10", "--check", python("pass")
        )
        holder.join()
        self.assertEqual(0, status, value)
        self.assertEqual([False], held_during_wait)
        self.assertGreaterEqual(value["merge"]["waited_seconds"], 0.4)
        self.assertEqual("closed", value["record"]["state"])

    @verifies("scenario.tasks.merge-workspace-busy")
    def test_merge_and_close_refuse_a_busy_workspace(self):
        self.project.open_task("t1")
        self.deliver()
        before, record = self.head(), store.load_task(self.root, "t1")
        with workspace_lock(self.root / ".concorde", "t1", "run r-1 (delivery)"):
            merged = self.refusal(
                "merge", "t1", "--wait", "0.3", "--check", python("pass")
            )
            closed = self.refusal(
                "close", "t1", "--completed", "--note", "n", "--wait", "0.3"
            )
        for error in (merged, closed):
            self.assertEqual(
                ("workspace_busy", "environment"),
                (error["code"], error["unhandled"]["reason"]),
            )
            self.assertIn("run r-1 (delivery)", error["detail"])
            self.assertIn("after waiting 0 s", error["detail"])
            self.assertIn("longer --wait", " ".join(error["options"]))
        self.assertEqual(record, store.load_task(self.root, "t1"))
        self.assert_untouched(before)
        self.assertFalse(store.merge_lock_held(self.root))

    @verifies("scenario.tasks.merge-interrupted")
    def test_an_interrupted_merge_refuses_every_mutating_command(self):
        before, after = self.interrupted()
        self.assertNotEqual(before, after)
        record = store.load_task(self.root, "t1")
        self.assertEqual("merging", record["state"])
        merging = record["merging"]
        self.assertEqual(
            (before, after, self.project.worktree("t1").exists()),
            (merging["before"], merging["after"], True),
        )
        self.assertEqual(git(self.root, "rev-parse", "concorde/t1"), merging["checked"])
        # Reading still works.
        self.assertEqual("merging", self.state())
        status, listed = self.command("list", "--state", "merging")
        self.assertEqual((0, ["t1"]), (status, [item["id"] for item in listed]))
        # Every mutating command is refused, naming the task, the commits and the recovery.
        attempts = [
            ("open", "t2", "--goal", "g", "--modules", "module.a"),
            ("merge", "t1", "--check", python("pass")),
            ("close", "t1", "--completed", "--note", "n"),
            ("session", "t1", "--main", "main"),
            ("escalate", "t1", "--code", "c", "--detail", "d", "--reason", "decision")
            + ("--explanation", "e", "--error-file", "missing.json"),
        ]
        for argv in attempts:
            error = self.refusal(*argv)
            self.assertEqual(
                ("merge_incomplete", "decision"),
                (error["code"], error["unhandled"]["reason"]),
                argv,
            )
            for part in ("task t1", before, after, "--resume", "--abort"):
                self.assertIn(part, error["detail"])
        self.assertNotIn(
            "merge_incomplete", json.dumps(self.command("session", "t1", "--stop")[1])
        )
        self.assertFalse((self.root / ".concorde/tasks/t2.json").exists())
        self.assertEqual(after, self.head())

    @verifies("scenario.tasks.merge-resume")
    def test_resume_checks_the_merge_again_and_closes(self):
        before, after = self.interrupted()
        # Without the recorded commit, the merge is recognized from its parents.
        store.update(
            self.root,
            "t1",
            lambda record: record["merging"].update(after=None) or record,
        )
        self.assertEqual(
            after,
            store.merge_commit(self.root, store.load_task(self.root, "t1")["merging"]),
        )
        self.assertEqual(
            "invalid_input",
            self.refusal("merge", "t1", "--resume", "--check", python("pass"))["code"],
        )
        status, value = self.command("merge", "t1", "--resume")
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "merged", None),
            (
                value["record"]["state"],
                value["record"]["closed"]["outcome"],
                value["record"]["merging"],
            ),
        )
        self.assertEqual(
            (before, after), (value["merge"]["before"], value["merge"]["after"])
        )
        self.assertEqual(after, self.head())
        self.assertIn("resumed the merge", Path(value["merge"]["log"]).read_text())

    @verifies("scenario.tasks.close-rerun")
    def test_a_merge_whose_close_stopped_part_way_is_finished(self):
        self.project.open_task("t1")
        self.deliver()
        worktree = self.project.worktree("t1")
        real = store.update

        def refusing_the_close(primary, task_id, change):
            if change(store.load_task(primary, task_id))["state"] == "closed":
                raise store.TaskError("record_conflict", "changed concurrently")
            return real(primary, task_id, change)

        with patch.object(store, "update", refusing_the_close):
            error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual("record_conflict", error["code"])
        self.assertIn(f"already removed the worktree {worktree}", error["detail"])
        self.assertIn("`concorde task merge t1 --resume`", error["detail"])
        self.assertFalse(worktree.exists())
        self.assertEqual("merging", store.load_task(self.root, "t1")["state"])
        status, value = self.command("merge", "t1", "--resume")
        self.assertEqual(0, status, value)
        self.assertEqual("closed", value["record"]["state"])
        # The merge closes the task but the decision log refuses the closing.
        self.project.open_task("t2")
        self.deliver("t2", "src/a/other.py", "OTHER = 1\n")
        log = self.root / ".concorde/tasks/t2.decisions.md"
        log.chmod(0o444)
        self.addCleanup(log.chmod, 0o644)
        error = self.refusal("merge", "t2", "--check", python("pass"))
        self.assertEqual("decision_log_failed", error["code"])
        self.assertIn("the task is closed as merged", error["detail"])
        self.assertIn("`concorde task close t2 --merged`", error["detail"])
        stored = store.load_task(self.root, "t2")
        self.assertEqual(("closed", None), (stored["state"], stored["merging"]))
        log.chmod(0o644)
        status, value = self.command("close", "t2", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(stored, store.load_task(self.root, "t2"))
        self.assertIn(f"## Closed: merged, {stored['closed']['at']}", log.read_text())

    @verifies("scenario.tasks.merge-resume")
    def test_resume_undoes_a_merge_whose_check_fails(self):
        before, _ = self.interrupted(then=1)
        error = self.refusal("merge", "t1", "--resume")
        self.assertEqual("check_failed", error["code"])
        self.assertIn(f"back at {before}, clean", error["detail"])
        self.assert_untouched(before)
        self.assertIsNone(store.load_task(self.root, "t1")["merging"])

    @verifies("scenario.tasks.merge-resume")
    def test_resume_refuses_a_merge_that_is_not_the_head(self):
        self.project.open_task("t1")
        checked = self.deliver()
        before = self.head()
        self.assertEqual("not_merging", self.refusal("merge", "t1", "--resume")["code"])
        store.begin_merge(
            self.root,
            "t1",
            {
                "before": before,
                "checked": checked,
                "branch": git(self.root, "symbolic-ref", "--short", "HEAD"),
                "after": None,
                "checks": [[sys.executable, "-c", "pass"]],
                "since": store.now(),
                "pid": 1,
            },
        )
        error = self.refusal("merge", "t1", "--resume")
        self.assertEqual("not_resumable", error["code"])
        self.assertIn("the commit before the merge", error["detail"])
        self.assertEqual("merging", self.state())
        # Abort returns it to delivered without touching the branch.
        status, value = self.command("merge", "t1", "--abort")
        self.assertEqual(0, status, value)
        self.assertEqual(
            (before, None), (value["abort"]["before"], value["abort"]["undone"])
        )
        self.assert_untouched(before)

    @verifies("scenario.tasks.merge-abort")
    def test_abort_resets_the_primary_branch_and_returns_the_task(self):
        before, after = self.interrupted()
        status, value = self.command("merge", "t1", "--abort")
        self.assertEqual(0, status, value)
        self.assertEqual("delivered", value["record"]["state"])
        self.assertEqual(
            {"before": before, "undone": after, "left": []},
            {key: value["abort"][key] for key in ("before", "undone", "left")},
        )
        self.assert_untouched(before)
        # Nothing is refused any more: the task merges again.
        status, value = self.command("merge", "t1", "--check", python("pass"))
        self.assertEqual(0, status, value)
        self.assertEqual("merged", value["record"]["closed"]["outcome"])

    @verifies("scenario.tasks.merge-abort")
    def test_abort_refuses_a_primary_branch_that_moved_on(self):
        before, after = self.interrupted()
        (self.root / "notes.txt").write_text("committed on top of the merge\n")
        moved = commit(self.root, "a commit on top of the unchecked merge")
        error = self.refusal("merge", "t1", "--abort")
        self.assertEqual(
            ("merge_diverged", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        for part in (moved, before, after):
            self.assertIn(part, error["detail"])
        self.assertEqual((moved, "merging"), (self.head(), self.state()))

    @verifies("scenario.tasks.merge-live-busy")
    def test_a_merge_still_running_answers_busy(self):
        self.project.open_task("t1")
        checked = self.deliver()
        self.project.open_task("t2")
        taken, release = threading.Event(), threading.Event()

        def merging():
            with store.merge_lock(self.root, "merge", "t1", 0):
                store.begin_merge(
                    self.root,
                    "t1",
                    {
                        "before": self.head(),
                        "checked": checked,
                        "branch": git(self.root, "symbolic-ref", "--short", "HEAD"),
                        "after": None,
                        "checks": [[sys.executable, "-c", "pass"]],
                        "since": store.now(),
                        "pid": os.getpid(),
                    },
                )
                taken.set()
                release.wait(10)
                store.end_merge(self.root, "t1")

        holder = threading.Thread(target=merging)
        holder.start()
        try:
            self.assertTrue(taken.wait(10))
            with self.assertRaises(store.TaskError) as opened:
                store.open_task(self.root, "t3", "g", ["module.a"], wait=0.2)
            self.assertEqual("merge_busy", opened.exception.code)
            escalation = ("--code", "c", "--detail", "d", "--reason", "decision")
            escalation += ("--explanation", "e")
            for argv in (
                ("session", "t1", "--main", "m"),
                ("escalate", "t1", *escalation),
            ):
                error = self.refusal(*argv)
                self.assertEqual("merge_busy", error["code"], argv)
                self.assertIn("`concorde task merge` of task t1", error["detail"])
            # Another task's escalation passes the guard and is recorded.
            status, value = self.command("escalate", "t2", *escalation)
            self.assertEqual((0, 1), (status, value.get("number")), value)
        finally:
            release.set()
            holder.join()
        self.assertEqual("delivered", self.state())


if __name__ == "__main__":
    unittest.main()
