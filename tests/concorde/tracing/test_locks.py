"""The lock library's holder line and the handing of a held lock to another process."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
