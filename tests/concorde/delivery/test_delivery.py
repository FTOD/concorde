"""The ``concorde delivery`` execution command end to end on a fixture task."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from concorde.kernel.errors import codes
from concorde.method.delivery.command import (
    DELIVERY,
    OUTPUT_SCHEMA,
    IndexRecord,
    State,
    undo,
)
from concorde.method.validation.measurement import measure
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import read_json, write_checks, write_json
from tests.concorde.validation.project import (
    ValidationProject,
    evidence_of,
    git,
    run_folder,
    status_lines,
    workspace_run,
)

FIXED = "def add(a, b):\n    return a + b\n"


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.project = ValidationProject(self)
        self.worktree = self.project.task()
        self.base = git(self.worktree, "rev-parse", "HEAD")

    def validated(self) -> dict:
        status, envelope = self.project.validate()
        self.assertEqual(status, 0, envelope)
        self.assertTrue(envelope["output"]["ready"], envelope["output"]["blocking"])
        return envelope

    def head(self) -> str:
        return git(self.worktree, "rev-parse", "HEAD")

    def committed(self, path: str, commit: str = "HEAD") -> str:
        return git(self.worktree, "show", f"{commit}:{path}")

    def committed_tree(self, commit: str) -> str:
        return git(self.worktree, "rev-parse", f"{commit}^{{tree}}")

    def commit_step(self, message: str = "A verified step") -> str:
        git(self.worktree, "add", "-A")
        git(self.worktree, "commit", "-q", "-m", message)
        return self.head()

    def saved_readiness(self, envelope: dict) -> dict:
        """The readiness the run saved in its trace node, in the task's workspace folder."""
        path = workspace_run(self.project.root, envelope) / "readiness.json"
        return json.loads(path.read_text())

    def node(self, envelope: dict) -> dict:
        """The run's trace node."""
        return json.loads((run_folder(envelope) / "trace.json").read_text())

    def index_state(self) -> tuple[str, ...]:
        """The index as Git shows it: status, entries, entry flags and staged content."""
        return (
            status_lines(self.worktree),
            git(self.worktree, "ls-files", "-s"),
            git(self.worktree, "ls-files", "-v"),
            git(self.worktree, "diff", "--cached"),
        )

    def stage_before_delivery(self) -> tuple[str, ...]:
        """Prepare the index as the task level may before delivering; return its state.

        A staged new file, a staged version of calc.py that the worktree changed again since
        (which only the index holds), an intent-to-add path, and skip-worktree and
        assume-unchanged flags: none of which a reset to the head would keep.
        """
        (self.worktree / "src/a/added.py").write_text("ADDED = 1\n")
        (self.worktree / "src/a/calc.py").write_text(
            "def add(a, b):\n    return b + a\n"
        )
        git(self.worktree, "add", "src/a/added.py", "src/a/calc.py")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        (self.worktree / "src/a/later.py").write_text("LATER = 1\n")
        git(self.worktree, "add", "-N", "src/a/later.py")
        git(self.worktree, "update-index", "--skip-worktree", "src/bmod/secret.py")
        git(self.worktree, "update-index", "--assume-unchanged", "checks/a_check.py")
        state = self.index_state()
        self.assertIn("MM src/a/calc.py", state[0])
        self.assertIn(" A src/a/later.py", state[0])
        self.assertIn("S src/bmod/secret.py", state[2])
        self.assertIn("h checks/a_check.py", state[2])
        return state

    def assert_undone(self, envelope: dict, index: tuple[str, ...]):
        """Nothing was committed and the workspace is again what the readiness examined."""
        self.assertIn(
            "the index was restored as the readiness examined it; the worktree is as the "
            "readiness examined it",
            envelope["summary"],
        )
        self.assertEqual(self.index_state(), index)
        self.assertEqual(self.head(), self.base)
        digest = self.saved_readiness(envelope)["inputs"]["digest"]
        self.assertEqual(measure(self.worktree, self.base)["digest"], digest)
        self.assertEqual(self.project.deliveries(), [])
        self.assertEqual(self.project.state(), "active")
        self.assertEqual(self.commit_references(envelope), [])

    def commit_references(self, envelope: dict) -> list[tuple[str, str]]:
        """The run node's references to commits, created or found."""
        return [
            (item["relation"], item["target"])
            for item in self.node(envelope)["references"]
            if item["relation"] in {"commit", "found_commit"}
        ]

    def assert_found(self, envelope: dict, commit: str):
        """The run node leads to the delivery it found, which an earlier run created."""
        self.assertEqual(self.commit_references(envelope), [("found_commit", commit)])

    def assert_inert(self, envelope: dict, code: str, deliveries: int = 0):
        self.assertEqual(envelope["status"], "blocked", envelope)
        self.assertIsNone(envelope["output"])
        refs = [item["ref"] for item in envelope["host_evidence"]]
        self.assertIn(code, refs)
        self.assertEqual(
            (envelope["error"]["level"], envelope["error"]["code"]), ("command", code)
        )
        self.assertEqual(
            envelope["error"]["actor"],
            f"Command delivery {envelope['run_id']} (workspace t1)",
        )
        self.assertEqual(envelope["error"]["unhandled"]["reason"], "decision")
        self.assertEqual(len(self.project.deliveries()), deliveries)

    @verifies("scenario.delivery.sandbox-masks")
    def test_deliver_inside_a_sandbox_that_masks_a_path(self):
        bwrap = shutil.which("bwrap")
        sandbox = [bwrap, "--dev-bind", "/", "/"] if bwrap else []
        if not bwrap or subprocess.run([*sandbox, "true"], check=False).returncode != 0:
            self.skipTest("bubblewrap cannot create a sandbox here")
        # The check boundary would need a second sandbox inside this one; what is under test is
        # the measurement and the staging, so the task runs without configured checks.
        write_checks(self.worktree, [])
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        masked = self.worktree / ".bashrc"
        done = subprocess.run(
            [
                *sandbox,
                "--bind",
                "/dev/null",
                str(masked),
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/concorde.py"),
                "delivery",
            ],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        envelope = json.loads(done.stdout.split("\n}\n", 1)[0] + "\n}")
        self.assertEqual("ok", envelope["status"], envelope)
        readiness = self.saved_readiness(envelope)
        changed = [item["path"] for item in readiness["inputs"]["changed"]]
        self.assertEqual([".concorde/checks/module.a.json", "src/a/calc.py"], changed)
        committed = git(self.worktree, "show", "--name-only", "--format=", "HEAD")
        self.assertIn("src/a/calc.py", committed.splitlines())
        self.assertNotIn(".bashrc", committed.splitlines())

    @verifies("scenario.delivery.deliver")
    def test_deliver_a_validated_task(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        validation = self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        output = envelope["output"]
        commit = self.head()
        self.assertEqual(
            output,
            {
                "commit": commit,
                "branch": "concorde/t1",
                "sequence": 1,
                "recovered": False,
            },
        )
        self.assertEqual(git(self.worktree, "rev-parse", "concorde/t1"), commit)
        self.assertEqual(
            git(self.worktree, "rev-list", "--parents", "-n1", commit).split()[1:],
            [self.base],
        )
        self.assertEqual(
            sorted(
                git(
                    self.worktree, "diff", "--name-only", self.base, commit
                ).splitlines()
            ),
            ["src/a/calc.py", "src/a/extra.py"],
        )
        self.assertEqual(self.committed("src/a/calc.py") + "\n", FIXED)
        message = git(self.worktree, "log", "-1", "--format=%B")
        self.assertEqual(message, "concorde: deliver t1\n\nFix A.")
        self.assertEqual(
            git(self.worktree, "log", "-1", "--format=%an <%ae>"),
            "Delivery Test <delivery@test>",
        )
        # Delivery decides the readiness itself, over the same inputs an earlier validate run
        # measured, and keeps it in its own trace node.
        readiness = self.saved_readiness(envelope)
        self.assertTrue(readiness["ready"])
        self.assertEqual(
            readiness["inputs"]["digest"], validation["output"]["inputs"]["digest"]
        )
        # The delivery run's node leads to what was committed.
        node = self.node(envelope)
        self.assertEqual(("run", envelope["run_id"]), (node["kind"], node["id"]))
        self.assertEqual(self.commit_references(envelope), [("commit", commit)])
        # The delivery commit is the only record of the delivery: the task record is untouched
        # and the task level reads the delivery back from Git.
        self.assertEqual(self.project.record()["state"], "open")
        self.assertEqual(self.project.state(), "delivered")
        self.assertEqual(
            self.project.deliveries(), [{"commit": commit, "mismatches": []}]
        )
        self.assertEqual(status_lines(self.worktree), "")
        self.assertEqual(
            ("command", "delivery", "t1"),
            (envelope["kind"], envelope["name"], envelope["workspace"]),
        )
        self.assertIsNone(envelope["worker"])
        self.assertEqual(envelope["worker_runs"], [])

    @verifies(
        "scenario.delivery.unverified-scenarios",
        "scenario.delivery.verified-scenarios",
    )
    def test_a_code_change_with_an_untested_new_scenario_is_refused(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        detail = envelope["error"]["detail"]
        self.assertIn("scenario.a.sum (specs/a/obligations.md)", detail)
        # A scenario the task did not touch is not its to verify.
        self.assertNotIn("scenario.a.answer", detail)
        (self.worktree / "src/a/test_calc.py").write_text(
            "def verifies(*scenarios):\n    return lambda test: test\n\n\n"
            '@verifies("scenario.a.sum")\ndef test_sum():\n    pass\n'
        )
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)

    @verifies("scenario.delivery.spec-only-scenarios")
    def test_a_spec_only_change_needs_no_test(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)

    @verifies("scenario.delivery.second")
    def test_deliver_again_after_further_work(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.validated()
        first = self.project.deliver()[1]["output"]["commit"]
        (self.worktree / "src/a/more.py").write_text("MORE = 1\n")
        self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 0, envelope)
        output = envelope["output"]
        self.assertEqual(output["sequence"], 2)
        self.assertEqual(
            git(
                self.worktree, "rev-list", "--parents", "-n1", output["commit"]
            ).split()[1:],
            [first],
        )
        self.assertEqual(
            [item["commit"] for item in self.project.deliveries()],
            [first, output["commit"]],
        )

    @verifies("scenario.delivery.committed")
    def test_deliver_a_task_whose_steps_are_committed(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        step = self.commit_step()
        self.assertEqual(status_lines(self.worktree), "")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        commit = envelope["output"]["commit"]
        self.assertEqual(
            git(self.worktree, "rev-list", "--parents", "-n1", commit).split()[1:],
            [step],
        )
        # Nothing was left to commit: the commit changes no file and its subject marks it.
        self.assertEqual(
            git(self.worktree, "diff", "--name-only", step, commit).splitlines(), []
        )
        self.assertEqual(
            git(self.worktree, "log", "-1", "--format=%s", commit),
            "concorde: deliver t1",
        )
        readiness = self.saved_readiness(envelope)
        self.assertEqual(
            [item["path"] for item in readiness["inputs"]["changed"]], ["src/a/calc.py"]
        )
        self.assertEqual(status_lines(self.worktree), "")
        self.assertEqual(self.project.state(), "delivered")

    @verifies("scenario.delivery.not-ready")
    def test_refuse_a_task_that_is_not_ready(self):
        (self.worktree / "stray.txt").write_text("unbound\n")
        step = self.commit_step()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 1)
        self.assert_inert(envelope, "not_ready")
        # Delivery's own Validation link is the cause, down to the committed stray file.
        self.assertEqual(
            ["not_ready", "not_deliverable", "unbound_finding"],
            codes(envelope["error"]),
        )
        self.assertIn("stray.txt", envelope["error"]["detail"])
        self.assertIn("never repairs", envelope["error"]["unhandled"]["explanation"])
        self.assertFalse(self.saved_readiness(envelope)["ready"])
        self.assertEqual((self.head(), status_lines(self.worktree)), (step, ""))

    @verifies("scenario.delivery.nothing")
    def test_nothing_to_deliver(self):
        self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 1)
        self.assert_inert(envelope, "nothing_to_deliver")
        self.assertIn("base commit", envelope["error"]["detail"])
        self.assertIn("new work only", envelope["error"]["unhandled"]["explanation"])

    @verifies("scenario.delivery.redeliver")
    def test_nothing_new_after_a_delivery(self):
        # Delivering again what was delivered reports the delivery commit and commits nothing.
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.commit_step()
        first = self.project.deliver()[1]
        self.assertEqual(first["status"], "ok", first)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(envelope["output"], {**first["output"], "recovered": True})
        self.assertIn("already delivered", envelope["summary"])
        # The found commit is validated again, as new work would be, before it is reported.
        readiness = self.saved_readiness(envelope)
        self.assertTrue(readiness["ready"])
        self.assertEqual(
            [item["path"] for item in readiness["inputs"]["changed"]], ["src/a/calc.py"]
        )
        self.assertEqual(self.head(), first["output"]["commit"])
        self.assertEqual(len(self.project.deliveries()), 1)
        self.assert_found(envelope, first["output"]["commit"])

    @verifies("scenario.delivery.commit-refused")
    def test_git_refuses_the_commit(self):
        hook = self.project.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
        hook.chmod(0o755)
        index = self.stage_before_delivery()
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertIn("hook says no", evidence_of(envelope, "git")[-1]["detail"])
        self.assertEqual(["commit_failed", "git_failed"], codes(envelope["error"]))
        self.assertIn("hook says no", envelope["error"]["causes"][0]["detail"])
        self.assert_undone(envelope, index)

    @verifies("scenario.delivery.hook-changed-commit")
    def test_a_commit_hook_that_changes_the_content_is_caught(self):
        # The hook changes a validated file and stages it again, so the worktree stays clean
        # and only the commit's tree shows what was not validated.
        hook = self.project.root / ".git/hooks/pre-commit"
        hook.write_text(
            "#!/bin/sh\nprintf 'def add(a, b):\\n    return 0\\n' > src/a/calc.py\n"
            "git add src/a/calc.py\n"
        )
        hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["commit_unverified"], codes(error))
        self.assertEqual(error["unhandled"]["reason"], "decision")
        self.assertIn("is not the staged tree", error["detail"])
        self.assertIn("M src/a/calc.py", error["detail"])
        # The rejected commit is taken off the branch, so its subject marks no delivery; the
        # run's node still leads to the commit it created.
        [(relation, commit)] = self.commit_references(envelope)
        self.assertEqual(relation, "commit")
        self.assertIn(commit, error["detail"])
        self.assertIn("took the commit off concorde/t1", error["detail"])
        self.assertIn("taken off", envelope["summary"])
        self.assertEqual(self.head(), self.base)
        self.assertEqual(
            git(self.worktree, "log", "-1", "--format=%s", commit),
            "concorde: deliver t1",
        )
        self.assertEqual(
            self.committed("src/a/calc.py", commit), "def add(a, b):\n    return 0"
        )
        # The index and the worktree hold what the commit held, the hook's change staged.
        self.assertEqual(git(self.worktree, "write-tree"), self.committed_tree(commit))
        self.assertEqual(status_lines(self.worktree), "M  src/a/calc.py\n")
        self.assertEqual(
            (self.worktree / "src/a/calc.py").read_text(),
            "def add(a, b):\n    return 0\n",
        )
        self.assertEqual(self.project.deliveries(), [])
        self.assertNotEqual(self.project.state(), "delivered")
        self.assertIsNone(envelope["output"])

    def test_a_rejected_commit_a_hook_committed_on_stays(self):
        # A post-commit hook commits again, so the head is not the commit Delivery made on the
        # validated head; Delivery takes off the branch only its own commit, so nothing moves.
        hook = self.project.root / ".git/hooks/post-commit"
        hook.write_text(
            '#!/bin/sh\n[ -n "$AGAIN" ] && exit 0\necho "hook output"\n'
            "AGAIN=1 git commit --allow-empty -m 'A hook step'\n"
        )
        hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["commit_unverified", "git_failed"], codes(error))
        self.assertIn("the commit stays", error["detail"])
        self.assertIn("stays on concorde/t1", envelope["summary"])
        # Neither the hook's commit nor the delivery commit below it was taken off.
        self.assertEqual(git(self.worktree, "log", "-1", "--format=%s"), "A hook step")
        delivered = git(self.worktree, "rev-parse", "HEAD~1")
        self.assertEqual(
            git(self.worktree, "log", "-1", "--format=%s", delivered),
            "concorde: deliver t1",
        )
        self.assertEqual(git(self.worktree, "rev-parse", "HEAD~2"), self.base)
        # The run names the commit it created, not the hook's on top of it.
        self.assertEqual(self.commit_references(envelope), [("commit", delivered)])
        self.assertIn(
            f"the delivery commit {delivered} on concorde/t1", error["detail"]
        )
        self.assertIn(f"no longer points at it but at {self.head()}", error["detail"])
        self.assertIn("the new commit is not the branch head", error["detail"])

    def test_a_refused_move_of_the_branch_says_it_still_points_at_the_commit(self):
        # A content-changing hook makes the commit fail to verify, and a stale lock of the
        # branch, left by a post-commit hook, makes Git refuse to move the branch back.
        lock = self.project.root / ".git/refs/heads/concorde/t1.lock"
        for name, body in (
            (
                "pre-commit",
                (
                    "printf 'def add(a, b):\\n    return 0\\n' > src/a/calc.py\n"
                    "git add src/a/calc.py\n"
                ),
            ),
            ("post-commit", f"touch '{lock}'\n"),
        ):
            hook = self.project.root / ".git/hooks" / name
            hook.write_text("#!/bin/sh\n" + body)
            hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        try:
            status, envelope = self.project.deliver()
        finally:
            lock.unlink(missing_ok=True)
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["commit_unverified", "git_failed"], codes(error))
        [(_, commit)] = self.commit_references(envelope)
        self.assertEqual(self.head(), commit)
        self.assertIn("since Git refused to move the branch back", envelope["summary"])
        self.assertIn(
            "Git refused to move concorde/t1, which still points at it", error["detail"]
        )
        self.assertNotIn("no longer points", error["detail"])
        self.assertEqual(error["causes"][0]["actor"], "git update-ref")
        self.assertIn(".lock", error["causes"][0]["detail"])

    @verifies("scenario.delivery.hook-changed-message")
    def test_a_commit_message_hook_that_changes_the_subject_is_caught(self):
        hook = self.project.root / ".git/hooks/commit-msg"
        hook.write_text("#!/bin/sh\nsed -i '1s/^/[T-1] /' \"$1\"\n")
        hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["commit_unverified"], codes(error))
        self.assertIn(
            "it is '[T-1] concorde: deliver t1' instead of 'concorde: deliver t1'",
            error["detail"],
        )
        [(_, commit)] = self.commit_references(envelope)
        self.assertIn(commit, error["detail"])
        self.assertIn("taken off", envelope["summary"])
        self.assertEqual(self.head(), self.base)
        self.assertEqual(status_lines(self.worktree), "M  src/a/calc.py\n")
        self.assertEqual(self.project.deliveries(), [])

    def test_a_commit_message_hook_that_adds_a_trailer_is_accepted(self):
        hook = self.project.root / ".git/hooks/commit-msg"
        hook.write_text("#!/bin/sh\nprintf '\\nChange-Id: I1\\n' >> \"$1\"\n")
        hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        message = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertTrue(message.startswith("concorde: deliver t1\n"), message)
        self.assertIn("Change-Id: I1", message)

    @verifies("scenario.delivery.hook-edits-kept")
    def test_a_failing_hooks_worktree_edits_are_kept_and_named(self):
        # Like a formatter hook: it rewrites a file and then rejects the commit.
        hook = self.project.root / ".git/hooks/pre-commit"
        hook.write_text(
            "#!/bin/sh\nprintf 'def add(a, b):\\n    return a+b\\n' > src/a/calc.py\n"
            "echo 'files were reformatted' >&2\nexit 1\n"
        )
        hook.chmod(0o755)
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        index = self.index_state()
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertEqual(["commit_failed", "git_failed"], codes(envelope["error"]))
        told = (
            "the index was restored as the readiness examined it; the worktree files "
            "src/a/calc.py are not as the readiness examined them"
        )
        self.assertIn(told, envelope["summary"])
        self.assertIn(told, envelope["error"]["detail"])
        self.assertIn("Delivery kept them", envelope["summary"])
        # The index is given back; the hook's edit stays in the worktree.
        self.assertEqual(index[1:], self.index_state()[1:])
        self.assertEqual(
            (self.worktree / "src/a/calc.py").read_text(),
            "def add(a, b):\n    return a+b\n",
        )
        self.assertEqual(self.head(), self.base)
        self.assertEqual(self.project.deliveries(), [])

    def test_the_scenario_gate_reads_paths_git_would_quote(self):
        # A code path Git quotes without -z still counts as changed code.
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/\u00e9t\u00e9 calc.py").write_text("SUM = 1\n")
        _, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        self.assertIn("src/a/\u00e9t\u00e9 calc.py", envelope["error"]["detail"])
        self.assertIn(
            "scenario.a.sum (specs/a/obligations.md)", envelope["error"]["detail"]
        )

    def test_the_scenario_gate_decodes_paths_the_measurement_quotes(self):
        # A code path that is not valid UTF-8 is recorded quoted, and still counts as changed
        # code once decoded.
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        with open(os.fsencode(self.worktree / "src/a") + b"/\xe9.py", "wb") as file:
            file.write(b"SUM = 1\n")
        _, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        self.assertIn('"src/a/\\351.py"', envelope["error"]["detail"])
        self.assertIn(
            "scenario.a.sum (specs/a/obligations.md)", envelope["error"]["detail"]
        )

    @verifies("scenario.delivery.unverified-scenarios")
    def test_scenarios_at_every_heading_level_need_a_test(self):
        # Spec core accepts scenario headings at levels 2 to 5, so the gate reads them all, and
        # not a scenario heading shown inside a fence.
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### More cases\n\n#### scenario.a.diff — A subtracts\n\n"
            "- GIVEN two numbers\n- WHEN A subtracts them\n- THEN it returns the difference\n"
            "\n## scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        _, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        detail = envelope["error"]["detail"]
        self.assertIn("scenario.a.diff (specs/a/obligations.md)", detail)
        self.assertIn("scenario.a.sum (specs/a/obligations.md)", detail)
        self.assertNotIn("scenario.a.answer", detail)

    def test_a_changed_scenario_step_needs_a_test(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text().replace(
                "THEN it answers", "THEN it answers at once"
            )
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        _, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        self.assertIn(
            "scenario.a.answer (specs/a/obligations.md)", envelope["error"]["detail"]
        )

    @verifies("scenario.delivery.unrealized-scenarios")
    def test_a_scenario_of_a_module_without_files_needs_a_test(self):
        # Module B binds no file, so structural validation warns about none of its
        # scenarios; Delivery still requires a test for the one the workspace added.
        metadata = read_json(self.worktree, "specs/b/module.md.json")
        metadata["defines"] = []
        write_json(self.worktree, "specs/b/module.md.json", metadata)
        shutil.rmtree(self.worktree / "src/bmod")
        obligations = self.worktree / "specs/b/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.b.more — B does more\n\n- GIVEN a request\n"
            "- WHEN B is asked for more\n- THEN it gives more\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        _, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        detail = envelope["error"]["detail"]
        self.assertIn("scenario.b.more (specs/b/obligations.md)", detail)
        self.assertNotIn("scenario.b.answer", detail)
        # A test of Module A may verify it.
        (self.worktree / "src/a/test_more.py").write_text(
            "def verifies(*scenarios):\n    return lambda test: test\n\n\n"
            '@verifies("scenario.b.more")\ndef test_more():\n    pass\n'
        )
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)

    @verifies("scenario.delivery.staged-unvalidated")
    def test_staging_that_changes_validated_content_is_refused(self):
        # A clean filter that rewrites a changed file succeeds, so git add stages content the
        # readiness never examined, while Git still sees the worktree as clean.
        (self.project.root / ".git/info").mkdir(exist_ok=True)
        (self.project.root / ".git/info/attributes").write_text(
            "src/a/extra.py filter=rewrite\n"
        )
        git(self.project.root, "config", "filter.rewrite.clean", "sed s/1/2/")
        index = self.stage_before_delivery()
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        index = (status_lines(self.worktree), *index[1:])
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["staged_unvalidated"], codes(error))
        self.assertEqual(error["unhandled"]["reason"], "decision")
        self.assertIn(
            "src/a/extra.py is staged with content a checkout would not give back",
            error["detail"],
        )
        self.assertNotIn("src/a/calc.py", error["detail"])
        self.assert_undone(envelope, index)

    @verifies("scenario.delivery.staged-filtered")
    def test_staging_through_a_filter_a_checkout_reverses_is_delivered(self):
        # Git LFS and line-ending conversion stage other bytes than the worktree holds, which a
        # checkout turns back into the validated content.
        (self.project.root / ".git/info").mkdir(exist_ok=True)
        (self.project.root / ".git/info/attributes").write_text(
            "src/a/extra.py filter=reverse\n"
        )
        git(self.project.root, "config", "filter.reverse.clean", "rev")
        git(self.project.root, "config", "filter.reverse.smudge", "rev")
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(self.committed("src/a/extra.py"), "1 = ARTXE")

    @verifies("scenario.delivery.stage-refused")
    def test_git_refuses_to_stage_a_change(self):
        # A required clean filter that fails refuses a new file while git add stages the others,
        # so the index must be given back, not merely left alone.
        (self.project.root / ".git/info").mkdir(exist_ok=True)
        (self.project.root / ".git/info/attributes").write_text(
            "src/a/extra.py filter=refuse\n"
        )
        git(self.project.root, "config", "filter.refuse.clean", "false")
        git(self.project.root, "config", "filter.refuse.required", "true")
        index = self.stage_before_delivery()
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        index = (status_lines(self.worktree), *index[1:])
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertEqual(["stage_failed", "git_failed"], codes(envelope["error"]))
        self.assertIn("refuse", envelope["error"]["causes"][0]["detail"])
        self.assert_undone(envelope, index)

    def test_a_failed_undo_names_what_it_could_not_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            worktree = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=worktree, check=True)
            # Reading a missing tree back into the index fails.
            ctx = SimpleNamespace(
                worktree=worktree,
                delivery=State(index=IndexRecord("0" * 40, ["later.py"], [], [])),
            )
            undone = undo(ctx)
        self.assertEqual([name for name, _ in undone.failed], ["the index"])
        # Entries apply only to an index that was read back, so none was attempted.
        self.assertEqual(undone.skipped, ["the intent-to-add entries"])
        self.assertEqual(
            [(link["actor"], link["code"]) for link in undone.causes],
            [(f"git read-tree {'0' * 40}", "git_failed")],
        )
        self.assertIn(
            "restoring the index failed, so the index is not as the readiness examined it "
            "(see the causes); the intent-to-add entries were not restored, since they apply "
            "only to an index that was read back",
            str(undone),
        )
        self.assertNotIn("the rest of the index was restored", str(undone))

    @verifies("scenario.delivery.unmerged-index")
    def test_an_unmerged_index_is_refused_before_anything_changes(self):
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        blob = git(self.worktree, "hash-object", "-w", "src/a/calc.py")
        git(self.worktree, "update-index", "--force-remove", "src/a/calc.py")
        subprocess.run(
            ["git", "update-index", "--index-info"],
            cwd=self.worktree,
            input="".join(
                f"100644 {blob} {stage}\tsrc/a/calc.py\n" for stage in (1, 2, 3)
            ),
            text=True,
            check=True,
        )
        index = self.index_state()
        metadata = (self.worktree / "specs/a/module.md.json").read_bytes()
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["index_unrecorded", "git_failed"], codes(error))
        self.assertEqual(error["unhandled"]["reason"], "decision")
        self.assertIn("src/a/calc.py", error["detail"])
        self.assertIn("abort the merge", " ".join(error["options"]))
        cause = error["causes"][0]
        self.assertEqual(cause["actor"], "git write-tree")
        self.assertIn("unmerged", cause["detail"])
        self.assertEqual(self.index_state(), index)
        self.assertEqual(
            (self.worktree / "specs/a/module.md.json").read_bytes(), metadata
        )
        self.assertEqual(self.head(), self.base)
        self.assertEqual(self.project.deliveries(), [])

    @verifies("scenario.delivery.recover")
    def test_a_delivery_interrupted_after_its_commit_needs_no_repair(self):
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.validated()
        _, first = self.project.deliver()
        delivered = first["output"]
        self.assertNotIn("confirmed", delivered)
        # The run ended after its commit without leaving its result: the commit alone records
        # the delivery.
        (workspace_run(self.project.root, first) / "result.json").unlink()
        self.assertEqual(self.project.state(), "delivered")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(self.head(), delivered["commit"])
        self.assertEqual(
            envelope["output"],
            {**delivered, "recovered": True},
        )
        self.assertEqual(
            [d["commit"] for d in self.project.deliveries()], [delivered["commit"]]
        )
        self.assertTrue(self.saved_readiness(envelope)["ready"])
        self.assertEqual(status_lines(self.worktree), "")
        self.assert_found(envelope, delivered["commit"])

    @verifies("scenario.delivery.recover-not-ready")
    def test_a_delivered_head_whose_workspace_is_not_ready_is_not_reported(self):
        # A commit with the subject and one parent, holding a file no Module binds: only
        # validating it again shows that it holds no deliverable workspace.
        (self.worktree / "stray.txt").write_text("unbound\n")
        head = self.commit_step("concorde: deliver t1")
        self.assertEqual(
            self.project.deliveries(), [{"commit": head, "mismatches": []}]
        )
        status, envelope = self.project.deliver()
        self.assertEqual(status, 1)
        self.assert_inert(envelope, "not_ready", deliveries=1)
        self.assertEqual(
            ["not_ready", "not_deliverable", "unbound_finding"],
            codes(envelope["error"]),
        )
        self.assertIn("stray.txt", envelope["error"]["detail"])
        self.assertIn(
            f"the delivery commit {head} at the head of concorde/t1 is not reported",
            envelope["error"]["detail"],
        )
        self.assertEqual((self.head(), status_lines(self.worktree)), (head, ""))
        self.assertEqual(self.commit_references(envelope), [])

    @verifies("scenario.delivery.recover-unverified")
    def test_a_head_that_only_looks_delivered_is_not_reported(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        step = self.commit_step()
        # A side branch merged with the subject of a delivery commit: two parents.
        git(self.worktree, "checkout", "-q", "-b", "side", self.base)
        (self.worktree / "src/a/more.py").write_text("MORE = 1\n")
        self.commit_step("A side step")
        git(self.worktree, "checkout", "-q", "concorde/t1")
        git(
            self.worktree,
            "merge",
            "-q",
            "--no-ff",
            "-m",
            "concorde: deliver t1",
            "side",
        )
        head = self.head()
        self.assertEqual(
            git(self.worktree, "rev-list", "--parents", "-n1", head).split()[1:],
            [step, git(self.worktree, "rev-parse", "side")],
        )
        self.assertEqual(status_lines(self.worktree), "")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        error = envelope["error"]
        self.assertEqual(["commit_unverified"], codes(error))
        self.assertEqual(error["unhandled"]["reason"], "decision")
        self.assertIn("it has 2 parent(s)", error["detail"])
        self.assertIn(head, error["detail"])
        self.assertIsNone(envelope["output"])
        self.assertEqual((self.head(), status_lines(self.worktree)), (head, ""))
        self.assertEqual(self.commit_references(envelope), [])
        self.assertNotEqual(self.project.state(), "delivered")

    @verifies("scenario.delivery.unbound")
    def test_a_delivery_needs_a_bound_workspace(self):
        (self.project.root / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.run("delivery", cwd=self.project.root)
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertIsNone(envelope["workspace"])
        self.assertEqual(["refused", "binding_required"], codes(envelope["error"]))
        self.assertEqual("command", envelope["error"]["level"])
        self.assertEqual(
            git(self.project.root, "rev-parse", "HEAD"), self.project.base_commit
        )

    @verifies("scenario.delivery.adoption")
    def test_an_adoption_delivery_needs_no_scenario_test(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver("t1", "--adoption")
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertIn(
            "exempt", [item["ref"] for item in evidence_of(envelope, "scenario-tests")]
        )


class ContractTests(unittest.TestCase):
    def test_the_schemas_are_the_delivery_contracts(self):
        contracts = SpecRepository(REPOSITORY_ROOT).contract_nodes
        self.assertNotIn("contract.delivery.evidence-bundle", contracts)
        self.assertEqual(contracts["contract.delivery.output"]["schema"], OUTPUT_SCHEMA)

    def test_delivery_is_a_recorded_command_of_a_bound_workspace(self):
        self.assertIs(DELIVERY.output_schema, OUTPUT_SCHEMA)
        self.assertEqual(
            ("command", "required", None, ()),
            (DELIVERY.kind, DELIVERY.binding, DELIVERY.task_type, DELIVERY.workers),
        )
        self.assertTrue(DELIVERY.writes)


if __name__ == "__main__":
    unittest.main()
