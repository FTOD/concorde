"""``concorde task deliver`` and a project that installs only the kernel and coordination."""

from __future__ import annotations

import contextlib
import io
import json
import shlex
import subprocess
import sys
import unittest

from concorde.coordination.tasks import cli, merge, store
from concorde.distribution.install import TRACES
from concorde.kernel.errors import ERROR_SCHEMA
from concorde.kernel.locking import workspace_lock
from concorde.kernel.tracing import node as trace
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.support.installed_parts import without, without_spec
from tests.concorde.support.operation_project import OperationProject, commit

FIXED = "def add(a, b):\n    return a + b\n"
ISSUE = "I-0123456789abcdef0123456789abcdef"


def git(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def python(code: str) -> str:
    """A ``--check`` running ``code`` with this Python."""
    return shlex.join([sys.executable, "-c", code])


class ProjectCase(unittest.TestCase):
    """A committed fixture project whose task records Git ignores."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        # An installed project ignores Tracing's folders, and merges need an identity.
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            gitignore.read_text() + "".join(f"{path}\n" for path in TRACES)
        )
        commit(self.root, "ignore task records")

    def command(self, *argv, cwd=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(list(argv), cwd=cwd or self.root)
        return status, json.loads(output.getvalue())

    def refusal(self, *argv, cwd=None):
        status, value = self.command(*argv, cwd=cwd)
        self.assertEqual(1, status, value)
        validate(value["error"], ERROR_SCHEMA)
        return value["error"]

    def opened(self, *missing: str):
        """Task t1 of a project installed without the method part and ``missing``, its worktree
        holding a change."""
        without(self.root, "method", *missing)
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text(FIXED)
        return worktree

    def attempt(self, number=1):
        return store.task_folder(self.root, "t1") / "deliveries" / str(number)


class DeliverTests(ProjectCase):
    @verifies("scenario.tasks.deliver")
    def test_deliver_commits_after_its_checks_and_the_task_merges(self):
        worktree = self.opened()
        base = git(worktree, "rev-parse", "HEAD")
        status, value = self.command(
            "deliver",
            "t1",
            "--check",
            python("print('first')"),
            "--check",
            python("print('second')"),
            cwd=worktree,
        )
        self.assertEqual(0, status, value)
        head = git(worktree, "rev-parse", "HEAD")
        self.assertEqual(head, value["delivery"]["commit"])
        self.assertFalse(value["delivery"]["recovered"])
        self.assertEqual(
            "concorde: deliver t1\n\nFix A.", git(worktree, "log", "-1", "--format=%B")
        )
        self.assertEqual(
            [base], git(worktree, "rev-list", "--parents", "-n1", head).split()[1:]
        )
        self.assertEqual(FIXED, git(worktree, "show", f"{head}:src/a/calc.py") + "\n")
        self.assertEqual("", git(worktree, "status", "--porcelain"))
        self.assertEqual("delivered", value["record"]["state"])
        self.assertEqual(
            [0, 0], [item["exit_code"] for item in value["delivery"]["checks"]]
        )
        node = trace.read(self.attempt())
        self.assertEqual(
            ("delivery", "ok", "delivered"),
            (node["kind"], node["status"], node["outcome"]),
        )
        self.assertIn({"relation": "commit", "target": head}, node["references"])
        self.assertEqual(
            {"task": "t1", "branch": "concorde/t1", "commit": head}, node["metadata"]
        )
        check = trace.read(self.attempt() / "checks/2")
        self.assertEqual(("delivery-check", "ok"), (check["kind"], check["status"]))
        self.assertIn("second", (self.attempt() / "checks/2/output.log").read_text())
        # The task is delivered like any other and merges as usual.
        status, merged = self.command("merge", "t1", "--check", python("pass"))
        self.assertEqual(0, status, merged)
        self.assertEqual("closed", merged["record"]["state"])
        self.assertEqual(head, git(self.root, "rev-parse", "HEAD^2"))

    @verifies("scenario.tasks.deliver-check-failed")
    def test_a_failed_check_commits_nothing(self):
        worktree = self.opened()
        base = git(worktree, "rev-parse", "HEAD")
        error = self.refusal(
            "deliver",
            "t1",
            "--check",
            python("pass"),
            "--check",
            python("import sys; print('broken'); sys.exit(3)"),
            "--check",
            python("open('ran', 'w')"),
            cwd=worktree,
        )
        self.assertEqual("check_failed", error["code"])
        self.assertIn("exited 3", error["detail"])
        self.assertIn("broken", error["detail"])
        self.assertIn(str(self.attempt() / "checks/2/output.log"), error["detail"])
        self.assertEqual(base, git(worktree, "rev-parse", "HEAD"))
        self.assertIn("src/a/calc.py", git(worktree, "status", "--porcelain"))
        self.assertFalse((worktree / "ran").exists())
        node = trace.read(self.attempt())
        self.assertEqual(("failed", "check_failed"), (node["status"], node["outcome"]))
        self.assertEqual("active", store.show_task(self.root, "t1")["record"]["state"])

    @verifies("scenario.tasks.deliver-recovered")
    def test_a_delivered_head_is_reported_and_an_empty_delivery_still_marks(self):
        without(self.root, "method")
        self.project.open_task("t1")
        worktree = self.project.worktree("t1")
        base = git(worktree, "rev-parse", "HEAD")
        # Nothing changed: the delivery commit is made all the same, as the mark.
        status, first = self.command("deliver", "t1", cwd=worktree)
        self.assertEqual(0, status, first)
        made = first["delivery"]["commit"]
        self.assertEqual(
            [base], git(worktree, "rev-list", "--parents", "-n1", made).split()[1:]
        )
        status, again = self.command("deliver", "t1", cwd=worktree)
        self.assertEqual(0, status, again)
        self.assertEqual(
            (made, True), (again["delivery"]["commit"], again["delivery"]["recovered"])
        )
        self.assertEqual(made, git(worktree, "rev-parse", "HEAD"))
        node = trace.read(self.attempt(2))
        self.assertEqual(("ok", "recovered"), (node["status"], node["outcome"]))
        self.assertIn({"relation": "found_commit", "target": made}, node["references"])

    @verifies("scenario.tasks.deliver-refused")
    def test_deliver_is_refused_outside_its_place(self):
        # Where the method part is installed, Method's delivery delivers.
        self.project.open_task("t0")
        error = self.refusal("deliver", "t0", cwd=self.project.worktree("t0"))
        self.assertEqual("delivery_by_method", error["code"])
        self.assertIn("concorde delivery", error["detail"])
        worktree = self.opened()
        base = git(worktree, "rev-parse", "HEAD")
        self.assertEqual("not_task_worktree", self.refusal("deliver", "t1")["code"])
        with workspace_lock(store.concorde(self.root), "t1", "a run of t1"):
            busy = self.refusal("deliver", "t1", "--wait", "0.2", cwd=worktree)
        self.assertEqual("workspace_busy", busy["code"])
        git(worktree, "switch", "-q", "-c", "elsewhere")
        wrong = self.refusal("deliver", "t1", cwd=worktree)
        self.assertEqual("wrong_branch", wrong["code"])
        self.assertIn("elsewhere", wrong["detail"])
        self.assertEqual(base, git(worktree, "rev-parse", "HEAD"))


class CoordinationAloneTests(ProjectCase):
    """A project that installs the kernel and coordination alone."""

    @verifies("scenario.tasks.coordination-alone")
    def test_a_project_without_the_other_parts_opens_delivers_merges_and_closes(self):
        without(self.root, "execution", "method", "issues")
        without_spec(self.root)
        # Modules are plain labels without a registry.
        status, opened = self.command(
            "open", "t1", "--goal", "Fix A.", "--modules", "module.anything"
        )
        self.assertEqual(0, status, opened)
        self.assertEqual(["module.anything"], opened["record"]["modules"])
        missing = self.refusal(
            "open", "t2", "--goal", "g", "--modules", "module.m", "--resolves", ISSUE
        )
        self.assertEqual("part_missing", missing["code"])
        self.assertIn("issues part", missing["detail"])
        self.assertFalse(store.task_folder(self.root, "t2").exists())
        resolve = self.refusal("resolve", "t1", ISSUE)
        self.assertEqual("part_missing", resolve["code"])
        waited = self.refusal("wait", "--run", "r-20261003T101500-delivery-5f3a0000")
        self.assertEqual("part_missing", waited["code"])
        self.assertIn("execution part", waited["detail"])
        worktree = self.project.worktree("t1")
        (worktree / "src/a/calc.py").write_text(FIXED)
        self.assertEqual("active", store.show_task(self.root, "t1")["record"]["state"])
        status, delivered = self.command("deliver", "t1", cwd=worktree)
        self.assertEqual(0, status, delivered)
        self.assertEqual([], store.show_task(self.root, "t1")["runs"])
        # Without the spec part a merge given no check runs none, and says so.
        status, merged = self.command("merge", "t1")
        self.assertEqual(0, status, merged)
        self.assertEqual("closed", merged["record"]["state"])
        self.assertEqual([], merged["merge"]["checks"])
        self.assertIn(
            merge.NO_CHECK.format(registry=".concorde/specs.json"), merged["warnings"]
        )
        # A task closed without a merge ends as well.
        malformed = self.refusal("open", "t3", "--goal", "Try.", "--modules", "m")
        self.assertEqual("invalid_input", malformed["code"])
        self.assertFalse((self.root / ".claude/worktrees/t3").exists())
        status, opened = self.command(
            "open", "t3", "--goal", "Try.", "--modules", "module.m"
        )
        self.assertEqual(0, status, opened)
        status, closed = self.command("close", "t3", "--completed", "--note", "tried")
        self.assertEqual(0, status, closed)
        self.assertEqual("closed", closed["record"]["state"])


if __name__ == "__main__":
    unittest.main()
