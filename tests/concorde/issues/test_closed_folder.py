"""Closed Issues live in .concorde/issues/closed/: dispositions move records between the folders,
recovery puts back a move a killed write left, and archive moves misplaced records."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.issues import store
from concorde.issues.store import (
    IssueError,
    archive_issues,
    list_issues,
    locate_issue,
    read_issue,
    report_issue,
)
from concorde.kernel.tracing import locks
from concorde.spec.verification import verifies
from tests.concorde.issues import test_store as base
from tests.concorde.support.environment import child_environment
from tests.concorde.support.issue_reports import git, git_project, report, source

OPEN = ".concorde/issues/{}.md"
CLOSED = ".concorde/issues/closed/{}.md"
SCRIPT = Path(__file__).resolve().parents[3] / "scripts/issues.py"


class ClosedFolderTests(unittest.TestCase):
    setUp = base.IssueStoreTests.setUp
    issue_files = base.IssueStoreTests.issue_files
    close = base.IssueStoreTests.close

    def head(self):
        return git(self.root, "rev-parse", "HEAD").strip()

    def changed(self, commit="HEAD"):
        """The paths ``commit`` changed, a move as its two paths."""
        return sorted(
            git(
                self.root, "show", "--no-renames", "--name-only", "--format=", commit
            ).split()
        )

    def status(self):
        return git(
            self.root, "status", "--porcelain", "--ignored", "--", ".concorde/issues"
        )

    def recorded(self, key="first", closed=False):
        """An Issue reported, and closed when ``closed``; its identity."""
        identifier = report_issue(self.root, report(report_key=key), source())[
            "issue_id"
        ]
        if closed:
            self.close(identifier, read_issue(self.root, identifier)[1])
        return identifier

    def configure(self):
        """Make the repository an initialized Concorde project, as the command requires."""
        (self.root / ".concorde").mkdir(exist_ok=True)
        (self.root / ".concorde/config.json").write_text(
            json.dumps({"profile_version": 19})
        )
        git(self.root, "add", ".concorde/config.json")
        git(self.root, "commit", "-q", "-m", "config")

    def misplace(self, identifier):
        """Commit the record of ``identifier`` in the other folder, as no write leaves it: a
        closed record where an earlier Concorde kept it, or an open one moved by hand."""
        _, _, path = locate_issue(self.root, identifier)
        other = next(place for place in store.issue_paths(identifier) if place != path)
        (self.root / other).parent.mkdir(parents=True, exist_ok=True)
        git(self.root, "mv", path, other)
        git(self.root, "commit", "-q", "-m", f"misplace {identifier}")
        return other

    @verifies("scenario.issues.store-folders")
    def test_closing_moves_the_record_into_closed_and_reopening_moves_it_back(self):
        identifier = self.recorded()
        (self.root / "unrelated.txt").write_text("staged, not the store's\n")
        git(self.root, "add", "unrelated.txt")
        record, revision = read_issue(self.root, identifier)
        closed = self.close(identifier, revision)
        self.assertEqual(
            sorted([OPEN.format(identifier), CLOSED.format(identifier)]),
            self.changed(),
        )
        self.assertIn(
            f"concorde: close Issue {identifier} (resolved)\n\n"
            f"Concorde-Issue: {identifier}",
            git(self.root, "log", "-1", "--format=%B"),
        )
        self.assertEqual({f"closed/{identifier}.md"}, set(self.issue_files()))
        self.assertEqual(
            ("closed", closed, CLOSED.format(identifier)),
            (lambda r, v, p: (r["status"], v, p))(*locate_issue(self.root, identifier)),
        )
        self.assertEqual(
            [(identifier, "closed")],
            [(row["id"], row["status"]) for row in list_issues(self.root)],
        )
        reopened = store.dispose_issue(
            self.root,
            identifier,
            closed,
            reason="reopened",
            note="Regressed",
            evidence=["failing test"],
            actor="main-agent",
        )
        self.assertEqual(
            sorted([OPEN.format(identifier), CLOSED.format(identifier)]),
            self.changed(),
        )
        self.assertEqual({f"{identifier}.md"}, set(self.issue_files()))
        record, revision, path = locate_issue(self.root, identifier)
        self.assertEqual(
            ("open", reopened, OPEN.format(identifier)),
            (record["status"], revision, path),
        )
        # Appends find the reopened record where it lies and keep it there.
        receipt = report_issue(
            self.root,
            report(report_key="later", issue_id=identifier, expected_revision=revision),
            source(invocation_id="worker-2"),
        )
        self.assertEqual(OPEN.format(identifier), receipt["path"])
        self.assertEqual([OPEN.format(identifier)], self.changed())
        self.assertEqual("", self.status())
        self.assertEqual(
            "A  unrelated.txt\n",
            git(self.root, "status", "--porcelain", "unrelated.txt"),
        )

    @verifies("scenario.issues.store-folders-locked")
    def test_a_close_under_a_held_merge_lock_moves_the_record_too(self):
        self.configure()
        identifier = self.recorded()
        lock = self.root / ".concorde/locks/merge.lock"
        # A task merge closes the Issues its task resolves with `concorde issues close`, to
        # which it hands the merge lock it holds.
        with locks.hold(lock, "a task merge", wait=0):
            with locks.handed_on(lock) as (variables, descriptors):
                closed = subprocess.run(
                    [sys.executable, str(SCRIPT), "close", identifier]
                    + ["--reason", "resolved", "--note", "Merged"]
                    + ["--evidence", "merge commit abc123", "--root", str(self.root)],
                    cwd=self.root,
                    env=child_environment(**variables),
                    pass_fds=descriptors,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
            # The merge still holds the lock, and its holder line is its own again.
            self.assertEqual("a task merge", locks.entry(lock)["holder"])
        self.assertEqual(0, closed.returncode, closed.stdout + closed.stderr)
        answer = json.loads(closed.stdout)
        self.assertEqual(
            {"status": "closed", "path": CLOSED.format(identifier)},
            {key: answer[key] for key in ("status", "path")},
        )
        self.assertEqual(
            sorted([OPEN.format(identifier), CLOSED.format(identifier)]),
            self.changed(),
        )
        self.assertEqual("", self.status())

    @verifies("scenario.issues.store-interrupted-move")
    def test_a_move_a_killed_write_left_is_put_back(self):
        for stage in (False, True):
            with self.subTest(stage=stage):
                identifier = self.recorded(key=f"killed-{stage}")
                committed = (self.root / OPEN.format(identifier)).read_bytes()
                before, revision = self.head(), read_issue(self.root, identifier)[1]
                with (
                    base.killed_before_commit(stage=stage),
                    self.assertRaises(SystemExit),
                ):
                    self.close(identifier, revision)
                # The close published in closed/ and removed the open record, uncommitted.
                self.assertFalse((self.root / OPEN.format(identifier)).exists())
                self.assertTrue((self.root / CLOSED.format(identifier)).is_file())
                self.assertEqual(before, self.head())
                record, current = read_issue(self.root, identifier)
                self.assertEqual(("open", revision), (record["status"], current))
                recovery = store.recover_issues(self.root)
                self.assertEqual(
                    [
                        {"path": OPEN.format(identifier), "action": "restored"},
                        {"path": CLOSED.format(identifier), "action": "removed"},
                    ],
                    sorted(recovery["recovered"], key=lambda item: item["path"]),
                )
                self.assertEqual([], recovery["left"])
                self.assertEqual(
                    committed, (self.root / OPEN.format(identifier)).read_bytes()
                )
                self.assertEqual("", self.status())
                # The repeated close moves the record, at the committed revision.
                self.close(identifier, revision)
                self.assertEqual(
                    sorted([OPEN.format(identifier), CLOSED.format(identifier)]),
                    self.changed(),
                )

    @verifies("scenario.issues.store-interrupted-move")
    def test_the_next_write_puts_back_a_killed_move_first(self):
        identifier = self.recorded()
        revision = read_issue(self.root, identifier)[1]
        with base.killed_before_commit(stage=True), self.assertRaises(SystemExit):
            self.close(identifier, revision)
        other = self.recorded(key="other")
        self.assertEqual([OPEN.format(other)], self.changed())
        self.assertEqual("", self.status())
        self.assertEqual("open", read_issue(self.root, identifier)[0]["status"])

    @verifies("scenario.issues.store-interrupted-move")
    def test_a_deleted_record_without_its_move_is_left(self):
        identifier = self.recorded()
        (self.root / OPEN.format(identifier)).unlink()
        recovery = store.recover_issues(self.root)
        self.assertEqual([], recovery["recovered"])
        self.assertEqual(
            [
                {
                    "path": OPEN.format(identifier),
                    "reason": "the committed record was deleted",
                }
            ],
            recovery["left"],
        )
        with self.assertRaises(IssueError) as raised:
            self.close(identifier, read_issue(self.root, identifier)[1])
        self.assertEqual("uncommitted_change", raised.exception.code)

    @verifies("scenario.issues.store-archive")
    def test_archive_moves_every_misplaced_record_in_one_commit(self):
        legacy = self.recorded(key="legacy", closed=True)
        self.misplace(legacy)
        reopened = self.recorded(key="reopened")
        self.misplace(reopened)
        placed = self.recorded(key="placed", closed=True)
        still = self.recorded(key="still")
        revisions = {
            item: read_issue(self.root, item)[1] for item in (legacy, reopened)
        }
        (self.root / "unrelated.txt").write_text("staged, not the store's\n")
        git(self.root, "add", "unrelated.txt")
        before = self.head()
        answer = archive_issues(self.root)
        self.assertEqual(
            sorted(
                [
                    {
                        "issue_id": legacy,
                        "from": OPEN.format(legacy),
                        "to": CLOSED.format(legacy),
                    },
                    {
                        "issue_id": reopened,
                        "from": CLOSED.format(reopened),
                        "to": OPEN.format(reopened),
                    },
                ],
                key=lambda item: item["issue_id"],
            ),
            answer["moved"],
        )
        self.assertEqual([], answer["left"])
        self.assertEqual(before, git(self.root, "rev-parse", "HEAD~1").strip())
        self.assertEqual(
            sorted(
                [
                    OPEN.format(legacy),
                    CLOSED.format(legacy),
                    OPEN.format(reopened),
                    CLOSED.format(reopened),
                ]
            ),
            self.changed(),
        )
        message = git(self.root, "log", "-1", "--format=%B")
        self.assertTrue(message.startswith("concorde: archive 2 Issue records\n"))
        for identifier in (legacy, reopened):
            self.assertIn(f"Concorde-Issue: {identifier}", message)
            # The record moved unchanged: its revision stays.
            self.assertEqual(
                revisions[identifier], read_issue(self.root, identifier)[1]
            )
        self.assertEqual(
            {
                f"closed/{legacy}.md",
                f"{reopened}.md",
                f"closed/{placed}.md",
                f"{still}.md",
            },
            set(self.issue_files()),
        )
        self.assertEqual("", self.status())
        self.assertEqual(
            "A  unrelated.txt\n",
            git(self.root, "status", "--porcelain", "unrelated.txt"),
        )
        # Nothing left to move: no commit.
        head = self.head()
        self.assertEqual({"moved": [], "left": []}, archive_issues(self.root))
        self.assertEqual(head, self.head())

    @verifies("scenario.issues.store-archive-left")
    def test_archive_leaves_what_it_cannot_move(self):
        twice = self.recorded(key="twice", closed=True)
        copy = OPEN.format(twice)
        shutil.copyfile(self.root / CLOSED.format(twice), self.root / copy)
        git(self.root, "add", "-f", copy)
        git(self.root, "commit", "-q", "-m", "copy by hand")
        edited = self.recorded(key="edited", closed=True)
        path = self.misplace(edited)
        (self.root / path).write_text(
            (self.root / path).read_text().replace("Retry ownership", "Hand-edited")
        )
        movable = self.recorded(key="movable", closed=True)
        self.misplace(movable)
        # Reads refuse an Issue committed twice, naming both paths.
        for read in (
            lambda: read_issue(self.root, twice),
            lambda: list_issues(self.root),
        ):
            with self.assertRaises(IssueError) as raised:
                read()
            self.assertEqual("invalid_issue", raised.exception.code)
            self.assertIn(OPEN.format(twice), str(raised.exception))
            self.assertIn(CLOSED.format(twice), str(raised.exception))
        answer = archive_issues(self.root)
        self.assertEqual(
            [
                {
                    "issue_id": movable,
                    "from": OPEN.format(movable),
                    "to": CLOSED.format(movable),
                }
            ],
            answer["moved"],
        )
        self.assertEqual(
            sorted([OPEN.format(twice), CLOSED.format(twice), path]),
            sorted(item["path"] for item in answer["left"]),
        )
        self.assertTrue((self.root / path).is_file())
        self.assertIn("Hand-edited", (self.root / path).read_text())


class ArchiveCommandTests(unittest.TestCase):
    setUp = base.IssueStoreTests.setUp
    close = base.IssueStoreTests.close
    recorded = ClosedFolderTests.recorded
    configure = ClosedFolderTests.configure
    misplace = ClosedFolderTests.misplace

    def run_command(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--root", str(self.root)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return result.returncode, json.loads(result.stdout)

    @verifies("scenario.issues.command-archive")
    def test_archive_prints_what_it_moved_from_a_linked_worktree(self):
        self.configure()
        legacy = self.recorded(key="legacy", closed=True)
        self.misplace(legacy)
        linked = Path(os.path.realpath(tempfile.mkdtemp())) / "linked"
        self.addCleanup(shutil.rmtree, linked.parent, ignore_errors=True)
        git(self.root, "worktree", "add", "-q", "--detach", str(linked))
        root, self.root = self.root, linked
        status, value = self.run_command("archive")
        self.root = root
        self.assertEqual(
            (
                0,
                {
                    "moved": [
                        {
                            "issue_id": legacy,
                            "from": OPEN.format(legacy),
                            "to": CLOSED.format(legacy),
                        }
                    ],
                    "left": [],
                },
            ),
            (status, value),
        )
        self.assertTrue((root / CLOSED.format(legacy)).is_file())
        self.assertFalse((linked / CLOSED.format(legacy)).exists())
        self.assertEqual((0, {"moved": [], "left": []}), self.run_command("archive"))


if __name__ == "__main__":
    unittest.main()
