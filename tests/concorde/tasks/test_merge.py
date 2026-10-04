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

from concorde.kernel.errors import ERROR_SCHEMA
from tests.concorde.support.ignored import TRACES
from concorde.kernel.locking import workspace_lock
from concorde.spec.schema import validate
from concorde.kernel.refusal import KernelError
from concorde.kernel.schema import validate_typed
from concorde.spec.verification import verifies
from concorde.coordination.tasks import checks, cli, merge, parts, store
from concorde.kernel.tracing import node as trace
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
        # An installed project ignores Tracing's folders (the task folders, the history, the
        # unbound runs and the locks), and merges need an identity.
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in TRACES)
        )
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

    def history(self, key="t1"):
        return self.root / ".concorde/history" / key

    def parents(self, commit="HEAD"):
        return git(self.root, "rev-list", "--parents", "-n", "1", commit).split()[1:]

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
        worktree = self.project.worktree("t1")
        head = self.deliver()
        before = self.head()
        log = (self.root / ".concorde/tasks/t1/decisions.md").read_text()
        status, value = self.command("merge", "t1")
        self.assertEqual(0, status, value)
        # Always a merge commit, of the commit before and the delivery commit, which adds the
        # task's decision log as it stood with the closing the close appends, and names the task.
        after = self.head()
        self.assertEqual([before, head], self.parents(after))
        self.assertEqual(
            [".concorde/decisions/t1.md", "src/a/calc.py"],
            sorted(git(self.root, "diff", "--name-only", before, after).splitlines()),
        )
        closed_at = value["record"]["closed"]["at"]
        self.assertEqual(
            f"{log}\n## Closed: merged, {closed_at}\n",
            git(self.root, "show", f"{after}:.concorde/decisions/t1.md") + "\n",
        )
        # The copy is the log as the task ended, so the close committed nothing more.
        self.assertEqual(
            (self.history() / "decisions.md").read_text(),
            (self.root / ".concorde/decisions/t1.md").read_text(),
        )
        self.assertEqual(
            f"Merge branch 'concorde/t1' at {head}\n\nConcorde-Task: t1",
            git(self.root, "log", "-1", "--format=%B", after),
        )
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertEqual(
            ("closed", "merged", "t1"),
            (
                value["record"]["state"],
                value["record"]["closed"]["outcome"],
                value["record"]["closed"]["history"],
            ),
        )
        self.assertTrue(value["record"]["closed"]["worktree_removed"])
        self.assertFalse(worktree.exists())
        merge = value["merge"]
        self.assertEqual((before, after), (merge["before"], merge["after"]))
        self.assertEqual(
            [[sys.executable, "-m", "concorde", "spec-validation"]],
            [check["argv"] for check in merge["checks"]],
        )
        self.assertEqual(0, merge["checks"][0]["exit_code"])
        self.assertGreaterEqual(merge["waited_seconds"], 0)
        # The attempt is a node of the task's trace, which the close moved to the history.
        attempt = self.history() / "merges/1"
        self.assertEqual(str(attempt), merge["log"])
        self.assertFalse((self.root / ".concorde/tasks/t1").exists())
        node = trace.read(attempt)
        self.assertEqual(
            ("merge", "ok", "merged", after),
            (node["kind"], node["status"], node["outcome"], node["metadata"]["commit"]),
        )
        data = node["content"]["data"]
        self.assertEqual(
            ("merge", before, head, after),
            (data["attempt"], data["before"], data["checked"], data["after"]),
        )
        # The merge trace types waited_seconds as a non-negative number.
        self.assertEqual(node["content"], validate_typed(node["content"]))
        for wrong in (-0.5, "0.4", True, None):
            with self.subTest(waited_seconds=wrong), self.assertRaises(KernelError):
                validate_typed(
                    {**node["content"], "data": {**data, "waited_seconds": wrong}}
                )
        check = trace.read(attempt / "checks/1")
        self.assertEqual(
            ("merge-check", "ok", 0),
            (check["kind"], check["status"], check["content"]["data"]["exit_code"]),
        )
        log = (attempt / "checks/1/output.log").read_text()
        self.assertIn('"tool":"spec-validation"', log)
        self.assertIn("[exit 0 after", log)
        self.assertEqual("", store.merge_lock_path(self.root).read_text())

    @verifies("scenario.tasks.merge-settles-reports")
    def test_merging_a_task_answers_its_unanswered_reports(self):
        self.project.open_task("t1")
        head = self.deliver()
        branch = git(self.root, "branch", "--show-current")
        report = store.report(self.root, "t1", "Delivered.", [])["report"]
        status, value = self.command("merge", "t1", "--check", python(""))
        self.assertEqual(0, status, value)
        closed_at = value["record"]["closed"]["at"]
        answer = store.load_any(self.root, "t1")[0]["reports"][0]["answer"]
        self.assertEqual(
            {
                "at": closed_at,
                "text": "The task ended before the main agent answered: `concorde task "
                f"merge` merged its delivery commit {head} into {branch} and closed it as "
                "merged. Nobody answers a report after that.",
                "by": "merge",
            },
            answer,
        )
        self.assertEqual(1, report["number"])
        # The merge commit's copy already holds the answer, so the close committed nothing.
        after = value["merge"]["after"]
        self.assertEqual(after, self.head())
        copy = git(self.root, "show", f"{after}:.concorde/decisions/t1.md") + "\n"
        self.assertEqual((self.history() / "decisions.md").read_text(), copy)
        self.assertTrue(
            copy.endswith(
                f"## Closed: merged, {closed_at}\n\nThe merge answered report(s) 1 of the "
                f"task session, unanswered until then: {answer['text']}\n"
            ),
            copy,
        )
        self.assertEqual(
            "task_closed",
            self.refusal("answer", "t1", "--report", "1", "--text", "late")["code"],
        )

    def issue(self, key):
        from concorde.issues import command as issues
        from tests.concorde.support.issue_reports import report

        answer = issues.report_action(
            self.root,
            report=report(report_key=key, owner_target_id="module.a", evidence=[]),
        )
        return answer["receipt"]["issue_id"]

    @verifies("scenario.tasks.merge-closes-resolved-issues")
    def test_a_merge_closes_the_issues_its_task_resolves(self):
        from concorde.issues import command as issues
        from concorde.issues.store import read_issue

        fixed, gone, later = (
            self.issue("fixed"),
            self.issue("gone"),
            self.issue("later"),
        )
        self.assertEqual(
            "invalid_issue",
            self.refusal(
                "open",
                "t0",
                "--goal",
                "g",
                "--modules",
                "module.a",
                "--resolves",
                "I-" + "0" * 32,
            )["code"],
        )
        status, value = self.command(
            "open",
            "t1",
            "--goal",
            "Fix A.",
            "--modules",
            "module.a",
            "--resolves",
            fixed,
        )
        self.assertEqual(0, status, value)
        self.assertEqual([fixed], value["record"]["resolves"])
        status, value = self.command("resolve", "t1", gone, later)
        self.assertEqual(0, status, value)
        self.assertEqual([fixed, gone, later], value["resolves"])
        self.assertEqual(
            "invalid_issue", self.refusal("resolve", "t1", "I-bad")["code"]
        )
        # An Issue closed meanwhile is left as it is, with a warning.
        issues.dispose(
            self.root, gone, "not-actionable", "no longer needed", ["decided"]
        )
        self.deliver()
        status, value = self.command("merge", "t1", "--check", python(""))
        self.assertEqual(0, status, value)
        after = value["merge"]["after"]
        self.assertEqual(
            [fixed, later], [item["issue_id"] for item in value["resolved"]]
        )
        for issue in (fixed, later):
            record, _ = read_issue(self.root, issue)
            self.assertEqual("closed", record["status"])
            disposition = record["dispositions"][-1]
            self.assertEqual(
                ("resolved", "main-agent", [f"merge commit {after}", "task t1"]),
                (disposition["reason"], disposition["actor"], disposition["evidence"]),
            )
        warned = [text for text in value["warnings"] if gone in text]
        self.assertEqual(1, len(warned), value["warnings"])
        self.assertIn("closed_issue", warned[0])
        # Each closure is a commit of its own on the primary branch, after the merge.
        self.assertEqual(after, git(self.root, "rev-parse", "HEAD~2"))
        self.assertEqual("", git(self.root, "status", "--porcelain"))

    @verifies("scenario.tasks.merge-issues-unavailable")
    def test_a_merge_whose_issues_command_fails_still_closes_and_answers(self):
        from concorde.issues.store import read_issue

        fixed = self.issue("fixed")
        self.project.open_task("t1")
        status, value = self.command("resolve", "t1", fixed)
        self.assertEqual(0, status, value)
        self.deliver()
        # The project's own `concorde` fails before it answers, as a broken installation does.
        broken = [sys.executable, "-c", "import sys; sys.exit('concorde is broken')"]
        with (
            patch.object(parts, "concorde_command", return_value=broken),
            patch.object(store, "end_sessions", wraps=store.end_sessions) as ending,
        ):
            status, value = self.command("merge", "t1", "--check", python(""))
        self.assertEqual(0, status, value)
        self.assertEqual("closed", value["record"]["state"])
        self.assertEqual([], value["resolved"])
        self.assertEqual(self.head(), value["merge"]["after"])
        warned = [text for text in value["warnings"] if fixed in text]
        self.assertEqual(1, len(warned), value["warnings"])
        self.assertIn("issues_unavailable", warned[0])
        self.assertIn("concorde is broken", warned[0])
        ending.assert_called_once()
        record, _ = read_issue(self.root, fixed)
        self.assertEqual("open", record["status"])

    @verifies("scenario.tasks.merge-empty-log")
    def test_a_merge_warns_of_an_unwritten_decision_log(self):
        passing = ["--check", python("")]
        self.project.open_task("t1")
        self.deliver()
        status, value = self.command("merge", "t1", *passing)
        self.assertEqual(0, status, value)
        self.assertEqual("merged", value["record"]["closed"]["outcome"])
        (warning,) = value["warnings"]
        self.assertIn(str(self.root / ".concorde/tasks/t1/decisions.md"), warning)
        self.assertIn("holds only its heading and goal", warning)
        # The close still appends how the task ended, and the log moved with the task.
        self.assertIn(
            "## Closed: merged", (self.history() / "decisions.md").read_text()
        )
        # A log with an entry of its own merges without a warning.
        self.project.open_task("t2")
        with (self.root / ".concorde/tasks/t2/decisions.md").open("a") as stream:
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
        self.assertEqual(head, self.parents()[1])

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
        attempt = Path(value["merge"]["log"])
        first_log, second_log = (
            (attempt / f"checks/{number}/output.log").read_text() for number in (1, 2)
        )
        self.assertIn("first check", first_log)
        self.assertIn("second check", second_log)
        self.assertNotIn("spec-validation", first_log + second_log)
        self.assertFalse((attempt / "checks/3").exists())

    @verifies("scenario.tasks.merge-update-validated")
    def test_an_unvalidated_update_adds_the_default_check(self):
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
        # An update not validated since: the project's validation fails until it is repaired.
        mark = self.root / ".concorde/update.json"
        # An installed project ignores the mark, as Distribution's installer arranges.
        with (self.root / ".git/info/exclude").open("a") as exclude:
            exclude.write("/.concorde/update.json\n")
        mark.write_text('{"state": "unvalidated", "from": "1.0.0", "to": "2.0.0"}\n')
        passing = python("pass")
        busy = self.refusal("merge", "t1", "--check", passing)
        self.assertEqual("check_failed", busy["code"], busy)
        self.assertIn("spec-validation", busy["detail"])
        self.assertEqual(before, self.head())
        self.assertTrue(mark.is_file())
        record = store.show_task(self.root, "t1")["record"]
        self.assertEqual("delivered", record["state"])
        attempt = store.task_folder(self.root, "t1") / "merges/1"
        self.assertEqual(
            [shlex.split(passing), merge.SPEC_VALIDATION],
            trace.read(attempt)["content"]["data"]["checks"],
        )
        # Without the mark, the named checks alone run again.
        mark.unlink()
        status, value = self.command("merge", "t1", "--check", passing)
        self.assertEqual(0, status, value)
        self.assertEqual(
            [shlex.split(passing)],
            [check["argv"] for check in value["merge"]["checks"]],
        )

    @verifies("scenario.tasks.merge-waits", "scenario.tasks.merge-busy")
    def test_a_second_merge_waits_for_the_first(self):
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
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
        self.assertIn(f"process {os.getpid()}, since 20", busy["detail"])
        self.assertEqual("environment", busy["unhandled"]["reason"])
        self.assert_untouched(before)
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
            "from concorde.coordination.tasks import store\n"
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
        self.assertFalse((self.root / ".concorde/tasks/t2").exists())
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
        attempt = self.root / ".concorde/tasks/t1/merges/1"
        for part in ("exited 1", "boom", str(attempt), f"back at {before}, clean"):
            self.assertIn(part, error["detail"])
        self.assert_untouched(before)
        self.assertFalse((self.root / ".concorde/decisions/t1.md").exists())
        node = trace.read(attempt)
        self.assertEqual(
            ("failed", "check_failed", "check_failed"),
            (node["status"], node["outcome"], node["error"]["code"]),
        )
        check = trace.read(attempt / "checks/1")
        self.assertEqual(
            ("failed", 1), (check["status"], check["content"]["data"]["exit_code"])
        )
        self.assertIn("boom", (attempt / "checks/1/output.log").read_text())

    @verifies("scenario.tasks.merge-commit-refused")
    def test_a_refused_merge_commit_is_undone(self):
        self.project.open_task("t1")
        self.deliver()
        before = self.head()
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
        hook.chmod(0o755)
        self.addCleanup(hook.unlink)
        error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual("git_failed", error["code"])
        for part in ("hook says no", ".concorde/decisions/t1.md", f"back at {before}"):
            self.assertIn(part, error["detail"])
        self.assert_untouched(before)
        self.assertFalse((self.root / ".concorde/decisions/t1.md").exists())
        self.assertIsNone(store.load_task(self.root, "t1")["merging"])
        self.assertEqual(
            ("failed", "git_failed"),
            (lambda node: (node["status"], node["outcome"]))(
                trace.read(self.root / ".concorde/tasks/t1/merges/1")
            ),
        )

    @verifies("scenario.tasks.merge-check-failed")
    def test_a_check_stopped_after_its_time_keeps_its_output(self):
        folder = Path(tempfile.mkdtemp()) / "check"
        self.addCleanup(shutil.rmtree, folder.parent, True)
        argv = [
            sys.executable,
            "-c",
            "import sys, time; print('diagnostic', flush=True); time.sleep(30)",
        ]
        with patch.object(checks, "TIMEOUT", 1):
            result, problem = checks.run(
                self.root,
                argv,
                folder,
                identity="check-1",
                kind="merge-check",
                content_type=merge.MERGE_CHECK_TRACE,
            )
        self.assertEqual(-1, result["exit_code"])
        self.assertIn("was stopped after 1 s", problem)
        self.assertIn("diagnostic", problem)
        self.assertIn("diagnostic", (folder / "output.log").read_text())

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
        self.assertFalse((self.root / ".concorde/tasks/t1/merges").exists())

    @verifies("scenario.tasks.merge-recovers-issue-records")
    def test_a_merge_puts_back_what_a_killed_issue_write_left(self):
        from concorde.issues import store as issues

        edited = issues.issue_path(self.issue("edited"))
        self.project.open_task("t1")
        self.deliver()
        records = self.root / issues.DIRECTORY
        before = set(records.iterdir())
        # The write dies after publishing its record and before Git commits it, so nothing puts
        # the record back.
        with (
            patch("concorde.issues.store._commit", side_effect=SystemExit("killed")),
            patch("concorde.issues.store._put_back", return_value="killed"),
            self.assertRaises(SystemExit),
        ):
            self.issue("killed")
        (killed,) = set(records.iterdir()) - before
        (self.root / edited).write_text(
            (self.root / edited).read_text() + "edited by hand\n"
        )
        head = self.head()
        error = self.refusal("merge", "t1")
        self.assertEqual("primary_dirty", error["code"])
        self.assertIn(edited, error["detail"])
        self.assertIn("no Issue write made", error["detail"])
        self.assertFalse(killed.exists())
        self.assertEqual(head, self.head())
        git(self.root, "checkout", "--", edited)
        status, value = self.command("merge", "t1", "--check", python(""))
        self.assertEqual(0, status, value)
        self.assertEqual("closed", self.state())

    @verifies("scenario.tasks.merge-nothing-outside")
    def test_a_change_outside_every_tasks_reach_refuses_the_merge(self):
        self.project.open_task("t1")
        self.project.open_task("t2")
        self.project.open_task("t3")
        self.deliver()
        self.deliver("t2", path="src/a/other.py", text="OTHER = 1\n")
        ended = self.project.worktree("t3")
        status, closed = self.command("close", "t3", "--completed", "--note", "done")
        self.assertEqual(0, status, closed)
        # The close removes the worktree; one it could not remove outlives its task.
        git(self.root, "worktree", "add", str(ended), "concorde/t3")
        before = self.head()
        (ended / "stray.txt").write_text("written from outside\n")
        error = self.refusal("merge", "t1")
        self.assertEqual(
            ("changed_outside", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn("stray.txt", error["detail"])
        self.assertIn("t3", error["detail"])
        self.assertIn(str(ended), error["detail"])
        self.assert_untouched(before)
        self.assertFalse((self.root / ".concorde/tasks/t1/merges").exists())
        (ended / "stray.txt").unlink()
        # A task that has delivered and waits only warns: its own session may have written it.
        other = self.project.worktree("t2")
        (other / "late.txt").write_text("after delivering\n")
        status, merged = self.command("merge", "t1", "--check", python("pass"))
        self.assertEqual(0, status, merged)
        self.assertEqual("closed", self.state())
        self.assertTrue(
            any(
                "late.txt" in warning and str(other) in warning
                for warning in merged["warnings"]
            ),
            merged["warnings"],
        )

    @verifies("scenario.tasks.delivery-unverified")
    def test_a_delivery_commit_that_does_not_verify_is_not_merged(self):
        self.project.open_task("t1")
        head = deliver(self.project.worktree("t1"), verifies=False)
        before = self.head()
        record = store.load_task(self.root, "t1")
        error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual(
            ("delivery_unverified", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn(head, error["detail"])
        self.assertIn("it has 2 parent(s)", error["detail"])
        self.assertTrue(error["options"])
        self.assertEqual(before, self.head())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertEqual(record, store.load_task(self.root, "t1"))
        self.assertEqual("active", self.state())
        self.assertFalse((self.root / ".concorde/tasks/t1/merges").exists())

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
        self.assertEqual(checked, self.parents(head)[1])
        self.assertNotEqual(
            0,
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", moved[0], head],
                cwd=self.root,
                check=False,
            ).returncode,
        )
        self.assertEqual("merging", self.state())

    @verifies("scenario.tasks.merge-already-contained")
    def test_a_head_already_merged_is_checked_and_closed(self):
        self.project.open_task("t1")
        checked = self.deliver()
        git(self.root, "merge", "--ff-only", "concorde/t1")
        before = self.head()
        self.assertEqual(checked, before)
        status, value = self.command("merge", "t1", "--check", python("pass"))
        self.assertEqual(0, status, value)
        self.assertEqual(
            ("closed", "merged"),
            (value["record"]["state"], value["record"]["closed"]["outcome"]),
        )
        self.assertEqual(
            (before, before, True),
            (
                value["merge"]["before"],
                value["merge"]["after"],
                value["merge"]["contained"],
            ),
        )
        self.assertEqual(
            [0], [check["exit_code"] for check in value["merge"]["checks"]]
        )
        self.assertEqual(
            "contained", trace.read(Path(value["merge"]["log"]))["outcome"]
        )
        # No merge commit: the decision log is committed alone on top of the merged head.
        self.assertEqual([before], self.parents(self.head()))
        self.assertTrue(
            (self.root / ".concorde/decisions/t1.md").is_file(),
        )

    @verifies("scenario.tasks.merge-waits-for-run")
    def test_a_merge_waits_for_the_tasks_run_without_the_merge_lock(self):
        self.project.open_task("t1")
        self.deliver()
        taken, release = threading.Event(), threading.Event()
        held_during_wait = []

        def hold():
            with workspace_lock(store.concorde(self.root), "t1", "run r-1 (delivery)"):
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
        with workspace_lock(store.concorde(self.root), "t1", "run r-1 (delivery)"):
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
        self.assertFalse((self.root / ".concorde/tasks/t2").exists())
        self.assertEqual(after, self.head())
        # A close is refused before it stops any task session or run of the task.
        with patch.object(store, "stop_task", side_effect=AssertionError("stopped")):
            error = self.refusal(
                "close", "t1", "--failed", "--reason", "r", "--no-error"
            )
        self.assertEqual("merge_incomplete", error["code"])
        # The killed merge's attempt node still says it runs; nothing ended it.
        self.assertEqual(
            "running", trace.read(self.root / ".concorde/tasks/t1/merges/1")["status"]
        )

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
        # The killed attempt is ended as interrupted; the resume is an attempt of its own.
        merges = self.history() / "merges"
        self.assertEqual(str(merges / "2"), value["merge"]["log"])
        killed, resumed = trace.read(merges / "1"), trace.read(merges / "2")
        self.assertEqual(
            ("failed", "interrupted"), (killed["status"], killed["outcome"])
        )
        self.assertEqual(
            ("resume", "ok", "merged", after),
            (
                resumed["content"]["data"]["attempt"],
                resumed["status"],
                resumed["outcome"],
                resumed["content"]["data"]["after"],
            ),
        )
        self.assertEqual(
            0, trace.read(merges / "2/checks/1")["content"]["data"]["exit_code"]
        )

    @verifies("scenario.tasks.merge-log-changed")
    def test_a_log_changed_after_the_merge_commit_is_committed_again(self):
        before, after = self.interrupted()
        log = self.root / ".concorde/tasks/t1/decisions.md"
        with log.open("a") as stream:
            stream.write("\n## Main agent: the merge was interrupted; resuming\n")
        status, value = self.command("merge", "t1", "--resume")
        self.assertEqual(0, status, value)
        # The merge commit's copy lacks the entry; a commit of the log alone keeps it.
        self.assertEqual(after, value["merge"]["after"])
        self.assertEqual([after], self.parents())
        self.assertEqual(
            [".concorde/decisions/t1.md"],
            git(self.root, "diff", "--name-only", after, "HEAD").splitlines(),
        )
        self.assertEqual(
            "concorde: keep the decision log of t1\n\nTask t1 ended merged.\n\n"
            "Concorde-Task: t1",
            git(self.root, "log", "-1", "--format=%B"),
        )
        ended = (self.history() / "decisions.md").read_text()
        self.assertEqual(
            ended.strip(), git(self.root, "show", "HEAD:.concorde/decisions/t1.md")
        )
        self.assertTrue(
            ended.endswith(f"\n## Closed: merged, {value['record']['closed']['at']}\n")
        )
        self.assertEqual("", git(self.root, "status", "--porcelain"))

    @verifies("scenario.tasks.close-rerun")
    def test_a_merge_whose_close_stopped_part_way_is_finished(self):
        self.project.open_task("t1")
        self.deliver()
        worktree = self.project.worktree("t1")
        real = store.update

        def refusing_the_close(primary, task_id, change, *, locked=False):
            if change(store.load_task(primary, task_id))["state"] == "closed":
                raise store.TaskError("record_conflict", "changed concurrently")
            return real(primary, task_id, change, locked=locked)

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
        log = self.root / ".concorde/tasks/t2/decisions.md"
        log.chmod(0o444)
        self.addCleanup(lambda: log.exists() and log.chmod(0o644))
        error = self.refusal("merge", "t2", "--check", python("pass"))
        self.assertEqual("decision_log_failed", error["code"])
        self.assertIn("the task is closed as merged", error["detail"])
        self.assertIn("`concorde task close t2 --merged`", error["detail"])
        stored = store.load_task(self.root, "t2")
        self.assertEqual(("closed", None), (stored["state"], stored["merging"]))
        log.chmod(0o644)
        # The folder moves only once the decision log holds the closing.
        self.assertTrue(log.parent.is_dir())
        status, value = self.command("close", "t2", "--merged")
        self.assertEqual(0, status, value)
        self.assertEqual(stored, store.load_any(self.root, "t2")[0])
        self.assertFalse(log.parent.exists())
        self.assertIn(
            f"## Closed: merged, {stored['closed']['at']}",
            (self.history("t2") / "decisions.md").read_text(),
        )

    @verifies("scenario.tasks.close-merged-ends-attempt")
    def test_closing_a_merged_task_ends_the_merge_attempt_left_running(self):
        self.project.open_task("t1")
        self.deliver()
        log = self.root / ".concorde/tasks/t1/decisions.md"
        log.chmod(0o444)
        self.addCleanup(lambda: log.exists() and log.chmod(0o644))
        original = trace.write

        def refusing_the_end(folder, record):
            if record["kind"] == "merge" and record["status"] != "running":
                raise OSError(28, "No space left on device")
            return original(folder, record)

        # The merge commits, its close refuses the closing and the attempt's end is not written.
        with patch.object(trace, "write", refusing_the_end):
            error = self.refusal("merge", "t1", "--check", python("pass"))
        self.assertEqual("decision_log_failed", error["code"])
        self.assertIn("No space left on device", error["detail"])
        attempt = self.root / ".concorde/tasks/t1/merges/1"
        self.assertEqual("running", trace.read(attempt)["status"])
        log.chmod(0o644)
        status, value = self.command("close", "t1", "--merged")
        self.assertEqual(0, status, value)
        self.assertFalse(any("merges/1" in text for text in value["warnings"]))
        ended = trace.read(self.history() / "merges/1")
        self.assertEqual(("ok", "merged"), (ended["status"], ended["outcome"]))
        self.assertIsNotNone(ended["ended_at"])

        # An attempt left running before it made its merge commit was interrupted.
        self.project.open_task("t2")
        self.deliver("t2", "src/a/other.py", "OTHER = 1\n")
        branch = git(self.root, "rev-parse", "--abbrev-ref", "HEAD")
        merge.Attempt(
            self.root, "t2", "merge", {"branch": branch, "before": self.head()}, 0
        )
        git(self.root, "merge", "--no-ff", "-m", "merged by hand", "concorde/t2")
        status, value = self.command("close", "t2", "--merged")
        self.assertEqual(0, status, value)
        ended = trace.read(self.history("t2") / "merges/1")
        self.assertEqual(("failed", "interrupted"), (ended["status"], ended["outcome"]))

    @verifies("scenario.tasks.merge-resume-check-failed")
    def test_resume_undoes_a_merge_whose_check_fails(self):
        before, _ = self.interrupted(then=1)
        error = self.refusal("merge", "t1", "--resume")
        self.assertEqual("check_failed", error["code"])
        self.assertIn(f"back at {before}, clean", error["detail"])
        self.assert_untouched(before)
        self.assertIsNone(store.load_task(self.root, "t1")["merging"])

    @verifies("scenario.tasks.merge-resume-refused")
    def test_resume_refuses_a_merge_that_is_not_the_head(self):
        self.project.open_task("t1")
        checked = self.deliver()
        before = self.head()
        delivered = store.load_task(self.root, "t1")
        self.assertEqual("not_merging", self.refusal("merge", "t1", "--resume")["code"])
        self.assertEqual(
            (before, delivered), (self.head(), store.load_task(self.root, "t1"))
        )
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
        merging = store.load_task(self.root, "t1")
        self.assertEqual(before, self.head())
        self.assertEqual(
            "not_resumable", self.refusal("merge", "t1", "--resume")["code"]
        )
        self.assertEqual(
            (before, merging), (self.head(), store.load_task(self.root, "t1"))
        )
        self.assertEqual(
            "invalid_input",
            self.refusal("merge", "t1", "--resume", "--check", python("pass"))["code"],
        )
        self.assertEqual(
            (before, merging), (self.head(), store.load_task(self.root, "t1"))
        )
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

    @verifies("scenario.tasks.merge-abort-diverged")
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
        # A merge in progress that is not the task's is refused before Git aborts it.
        git(self.root, "reset", "--hard", before)
        git(self.root, "branch", "side", before)
        git(self.root, "checkout", "-q", "side")
        (self.root / "side.txt").write_text("a merge made by hand\n")
        side = commit(self.root, "a side commit")
        git(self.root, "checkout", "-q", "-")
        git(self.root, "merge", "--no-commit", "--no-ff", "side")
        error = self.refusal("merge", "t1", "--abort")
        self.assertEqual("merge_diverged", error["code"])
        self.assertIn(f"a merge of {side}", error["detail"])
        self.assertEqual(
            side, git(self.root, "rev-parse", "-q", "--verify", "MERGE_HEAD")
        )
        self.assertEqual("merging", self.state())

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


class FrozenSourcesTests(unittest.TestCase):
    """A merge's process keeps the sources of the package it started with."""

    def package(self, name: str) -> Path:
        """A package ``name`` whose ``command`` imports from ``shapes``, its ``shapes``
        imported, on ``sys.path`` until the test ends."""
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        package = root / name
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "shapes.py").write_text("SHAPES = ('old',)\n")
        (package / "command.py").write_text("from .shapes import SHAPES\n")
        sys.path.insert(0, str(root))
        self.addCleanup(sys.path.remove, str(root))
        self.addCleanup(
            lambda: [
                sys.modules.pop(module)
                for module in list(sys.modules)
                if module == name or module.startswith(name + ".")
            ]
        )
        __import__(f"{name}.shapes")
        return package

    def merged(self, package: Path) -> None:
        """What a merge does to the package's files: ``command`` now needs a name that only
        the new ``shapes`` has."""
        (package / "shapes.py").write_text("SHAPES = ('old',)\nNEW = 1\n")
        (package / "command.py").write_text("from .shapes import NEW, SHAPES\n")

    @verifies("scenario.tasks.merge-own-sources")
    def test_a_module_imported_after_the_merge_is_the_one_the_merge_started_with(self):
        package = self.package("concorde_frozen_probe")
        merge.freeze_sources("concorde_frozen_probe")
        self.addCleanup(
            lambda: sys.meta_path.remove(
                next(
                    finder
                    for finder in sys.meta_path
                    if getattr(finder, "name", None) == "concorde_frozen_probe"
                )
            )
        )
        merge.freeze_sources("concorde_frozen_probe")  # a second freeze changes nothing
        self.merged(package)
        from concorde_frozen_probe import command

        self.assertEqual(("old",), command.SHAPES)
        self.assertFalse(hasattr(command, "NEW"))
        self.assertEqual(str(package / "command.py"), command.__file__)
        # The kept source is never cached as the file's new contents.
        self.assertEqual([], list(package.glob("__pycache__/command.*")))

    @verifies("scenario.tasks.merge-own-sources")
    def test_without_the_freeze_the_two_versions_do_not_import(self):
        package = self.package("concorde_unfrozen_probe")
        self.merged(package)
        with self.assertRaises(ImportError):
            __import__("concorde_unfrozen_probe.command")


if __name__ == "__main__":
    unittest.main()
