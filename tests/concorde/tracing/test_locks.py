"""The lock library's holder line, the handing of a held lock to another process and the reading
of the kernel's lock table."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from concorde.kernel.tracing import locks
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class LockLineTests(unittest.TestCase):
    @verifies("scenario.tracing.lock-holder-line")
    def test_the_holder_line_names_session_and_task(self):
        path = Path(tempfile.mkdtemp()) / "merge.lock"
        with (
            patch.dict(os.environ, {locks.SESSION: "s-7"}),
            locks.hold(path, "`concorde task merge` of task t1", task="t1"),
        ):
            entry = locks.entry(path)
            self.assertIn("session s-7, task t1", locks.holder(path))
        self.assertEqual(
            ("`concorde task merge` of task t1", os.getpid(), "s-7", "t1"),
            (entry["holder"], entry["pid"], entry["session"], entry["task"]),
        )
        self.assertIsNone(locks.entry(path))

    @verifies("scenario.tracing.lock-handover")
    def test_a_process_adopts_a_lock_it_was_handed(self):
        path = Path(tempfile.mkdtemp()) / "workspace.lock"
        descriptor = locks.acquire(path)
        code = (
            "import sys, time\n"
            "from concorde.kernel.tracing import locks\n"
            f"with locks.hold({str(path)!r}, 'the merge', wait=0):\n"
            "    import os\n"
            f"    print(os.environ.get({locks.INHERITED!r}), flush=True)\n"
            "    sys.stdin.read()\n"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            pass_fds=[descriptor],
            env=child_environment(
                PYTHONPATH=str(REPOSITORY_ROOT / "src"),
                **{locks.INHERITED: json.dumps({str(path): descriptor})},
            ),
        )
        os.close(descriptor)
        self.addCleanup(child.wait)
        # It took the lock without waiting although the lock was held when it started, and
        # removed the variable so that its own children do not believe they inherited it.
        self.assertEqual("None", child.stdout.readline().strip())
        self.assertEqual(child.pid, locks.entry(path)["pid"])
        child.stdin.close()
        child.wait(10)
        self.assertFalse(locks.held(path))

    def test_a_holder_hands_on_a_lock_it_keeps_holding(self):
        path = Path(tempfile.mkdtemp()) / "merge.lock"
        code = (
            "import os\n"
            "from concorde.kernel.tracing import locks\n"
            f"with locks.hold({str(path)!r}, 'the Issue write', wait=0):\n"
            f"    print(locks.entry({str(path)!r})['pid'], flush=True)\n"
        )
        with locks.hold(path, "the merge", wait=0):
            with locks.handed_on(path) as (variables, descriptors):
                child = subprocess.run(
                    [sys.executable, "-c", code],
                    pass_fds=descriptors,
                    env=child_environment(
                        PYTHONPATH=str(REPOSITORY_ROOT / "src"), **variables
                    ),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
            # The child adopted the lock without waiting and wrote its own holder line; once it
            # ended, the holder still holds the lock and its line is its own again.
            self.assertEqual(0, child.returncode, child.stderr)
            self.assertNotEqual(str(os.getpid()), child.stdout.strip())
            self.assertEqual(
                ("the merge", os.getpid()), tuple(locks.entry(path).values())[:2]
            )
        self.assertFalse(locks.held(path))
        with self.assertRaises(ValueError):
            with locks.handed_on(path):
                pass

    @verifies("scenario.tracing.lock-handover-block")
    def test_a_handed_lock_goes_with_the_receiver_s_block(self):
        path = Path(tempfile.mkdtemp()) / "merge.lock"
        descriptor = locks.acquire(path)
        code = (
            "import sys\n"
            "from concorde.kernel.tracing import locks\n"
            f"with locks.hold({str(path)!r}, 'the merge', wait=0):\n"
            "    print('held', flush=True)\n"
            "    sys.stdin.readline()\n"
            "print('left', flush=True)\n"
            "sys.stdin.readline()\n"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            pass_fds=[descriptor],
            env=child_environment(
                PYTHONPATH=str(REPOSITORY_ROOT / "src"),
                **{locks.INHERITED: json.dumps({str(path): descriptor})},
            ),
        )
        os.close(descriptor)
        self.addCleanup(child.wait)
        self.assertEqual("held", child.stdout.readline().strip())
        self.assertEqual(child.pid, locks.entry(path)["pid"])
        child.stdin.write("\n")
        child.stdin.flush()
        # The receiver left its block and still runs: the lock is free and its file empty.
        self.assertEqual("left", child.stdout.readline().strip())
        self.assertIsNone(child.poll())
        self.assertFalse(locks.held(path))
        self.assertEqual("", path.read_text())
        with locks.hold(path, "the next merge", wait=0):
            self.assertEqual(os.getpid(), locks.entry(path)["pid"])
        child.stdin.close()
        child.wait(10)

    @verifies("scenario.tracing.lock-handed-onward")
    def test_an_adopted_lock_is_handed_on_only_explicitly(self):
        path = Path(tempfile.mkdtemp()) / "merge.lock"
        descriptor = locks.acquire(path)
        # The grandchild says whether it was named a lock and takes it without waiting.
        grandchild = (
            "import os\n"
            "from concorde.kernel.tracing import locks\n"
            f"named = {locks.INHERITED!r} in os.environ\n"
            "try:\n"
            f"    with locks.hold({str(path)!r}, 'the Issue write', wait=0):\n"
            "        print(named, 'held', os.getpid(), flush=True)\n"
            "except locks.LockBusy:\n"
            "    print(named, 'busy', os.getpid(), flush=True)\n"
        )
        # The child adopts the lock, starts one grandchild plainly and one with the lock handed
        # on, and says whose holder line the lock carries afterwards.
        code = (
            "import os, subprocess, sys\n"
            "from concorde.kernel.tracing import locks\n"
            f"path, grandchild = {str(path)!r}, {grandchild!r}\n"
            "def start(environment, descriptors=()):\n"
            "    done = subprocess.run([sys.executable, '-c', grandchild], env=environment,\n"
            "        pass_fds=descriptors, capture_output=True, text=True, timeout=60)\n"
            "    print(done.stdout.strip() or done.stderr, flush=True)\n"
            "with locks.hold(path, 'the merge', wait=0):\n"
            "    start(dict(os.environ))\n"
            "    with locks.handed_on(path) as (variables, descriptors):\n"
            "        start({**os.environ, **variables}, descriptors)\n"
            "    print(locks.entry(path)['pid'], os.getpid(), flush=True)\n"
        )
        child = subprocess.run(
            [sys.executable, "-c", code],
            pass_fds=[descriptor],
            env=child_environment(
                PYTHONPATH=str(REPOSITORY_ROOT / "src"),
                **{locks.INHERITED: json.dumps({str(path): descriptor})},
            ),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        os.close(descriptor)
        self.assertEqual(0, child.returncode, child.stderr)
        plain, handed, owner = (line.split() for line in child.stdout.splitlines())
        # Started plainly, a process is named no lock and inherits none: the take is busy.
        self.assertEqual(["False", "busy"], plain[:2])
        # Handed on explicitly, it adopts the adopted lock at once under its own line.
        self.assertEqual(["True", "held"], handed[:2])
        # Afterwards the adopter holds the lock under its own holder line again.
        self.assertEqual(owner[1], owner[0])
        self.assertNotEqual(owner[1], handed[2])
        self.assertFalse(locks.held(path))

    @verifies("scenario.tracing.lock-table-holders")
    def test_the_lock_table_names_holders_of_the_same_device_and_inode(self):
        path = Path(tempfile.mkdtemp()) / "run.lock"
        path.touch()
        status = os.stat(path)
        major, minor = os.major(status.st_dev), os.minor(status.st_dev)
        table = Path(tempfile.mkdtemp()) / "locks"
        table.write_text(
            f"1: FLOCK  ADVISORY  WRITE 101 {major:02x}:{minor:02x}:{status.st_ino} 0 EOF\n"
            f"2: FLOCK  ADVISORY  WRITE 102 {major + 1:02x}:{minor:02x}:{status.st_ino} 0 EOF\n"
            f"3: FLOCK  ADVISORY  WRITE 103 {major:02x}:{minor + 1:02x}:{status.st_ino} 0 EOF\n"
            f"4: FLOCK  ADVISORY  WRITE 104 {major:02x}:{minor:02x}:{status.st_ino + 1} 0 EOF\n"
            f"5: POSIX  ADVISORY  WRITE 105 {major:02x}:{minor:02x}:{status.st_ino} 0 EOF\n"
            f"1: -> FLOCK  ADVISORY  WRITE 106 {major:02x}:{minor:02x}:{status.st_ino} 0 EOF\n"
        )
        with patch.object(locks, "LOCK_TABLE", table):
            self.assertEqual([101], locks.holder_pids(path))

    def test_the_lock_table_names_this_process_as_holder(self):
        path = Path(tempfile.mkdtemp()) / "run.lock"
        with locks.hold(path, "the test"):
            self.assertEqual([os.getpid()], locks.holder_pids(path))

    @verifies("scenario.tracing.lock-table-settled")
    def test_the_lock_table_is_read_until_two_reads_agree(self):
        path, held, other = self.lock_and_lines()
        table = ChangingTable([other, held + held + other, held + other, held + other])
        with patch.object(locks, "LOCK_TABLE", table):
            self.assertEqual([101], locks.holder_pids(path))
        self.assertEqual(4, table.reads)

    @verifies("scenario.tracing.lock-table-unsettled")
    def test_a_lock_table_that_never_settles_is_refused(self):
        path, held, other = self.lock_and_lines()
        churn = ChurningTable([other, held + held + other, held + other])
        started = time.monotonic()
        with (
            patch.object(locks, "LOCK_TABLE", churn),
            self.assertRaises(locks.LockTableUnsettled) as refused,
        ):
            locks.holder_pids(path)
        self.assertGreaterEqual(time.monotonic() - started, 1.0)
        self.assertEqual([101], refused.exception.seen)
        self.assertGreater(refused.exception.reads, 2)

    def test_a_held_lock_is_named_once_while_other_processes_churn_locks(self):
        """Real processes take and release enough locks to keep the kernel's table over a page and
        changing; each answer names this process once, or refuses naming it once."""
        folder = Path(tempfile.mkdtemp())
        path = folder / "run.lock"
        churners = [
            subprocess.Popen([sys.executable, "-c", CHURN, str(folder), str(number)])
            for number in range(8)
        ]
        try:
            with locks.hold(path, "the test"):
                largest = 0
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    largest = max(largest, len(locks.LOCK_TABLE.read_text()))
                    try:
                        self.assertEqual([os.getpid()], locks.holder_pids(path))
                    except locks.LockTableUnsettled as unsettled:
                        self.assertEqual([os.getpid()], unsettled.seen)
        finally:
            for churner in churners:
                churner.kill()
                churner.wait()
        self.assertGreater(largest, 4096)

    def lock_and_lines(self) -> tuple[Path, str, str]:
        """A lock file, a table line naming process 101 as its holder and one for another inode."""
        path = Path(tempfile.mkdtemp()) / "run.lock"
        path.touch()
        status = os.stat(path)
        file = f"{os.major(status.st_dev):02x}:{os.minor(status.st_dev):02x}"
        held = f"1: FLOCK  ADVISORY  WRITE 101 {file}:{status.st_ino} 0 EOF\n"
        other = f"2: FLOCK  ADVISORY  WRITE 102 {file}:{status.st_ino + 1} 0 EOF\n"
        return path, held, other


class ChangingTable:
    """A lock table whose reads give the texts in turn, the last one ever after."""

    def __init__(self, texts: list[str]):
        self.texts = texts
        self.reads = 0

    def read_text(self) -> str:
        self.reads += 1
        return self.texts[min(self.reads, len(self.texts)) - 1]


class ChurningTable(ChangingTable):
    """A lock table whose reads cycle through the texts, each with a line of a lock taken just
    then, so no two reads are ever identical."""

    def read_text(self) -> str:
        self.reads += 1
        churn = (
            f"9: FLOCK  ADVISORY  WRITE {1000 + self.reads} 00:00:{self.reads} 0 EOF\n"
        )
        return self.texts[self.reads % len(self.texts)] + churn


# A process that takes and releases 40 locks of its own in a loop.
CHURN = """
import fcntl, os, sys, time
paths = [os.path.join(sys.argv[1], f"churn-{sys.argv[2]}-{i}") for i in range(40)]
while True:
    descriptors = [os.open(p, os.O_RDWR | os.O_CREAT) for p in paths]
    for descriptor in descriptors:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
    time.sleep(0.001)
    for descriptor in descriptors:
        os.close(descriptor)
"""


if __name__ == "__main__":
    unittest.main()
