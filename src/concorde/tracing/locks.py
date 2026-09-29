"""The locks under ``.concorde/locks/``: files locked with ``flock`` that hold only their holder.

A holder writes one line of JSON naming itself, ``{"holder", "pid", "since"}``, once it holds the
lock, and empties the file before it releases it, so a waiter that gives up can say who holds it.
The kernel releases a ``flock`` however its process ends. A lock taken with ``remove`` (the run
lock) is removed by its holder while still held; a lock whose file was removed or replaced while a
process waited for it is taken again on the file that is there now, so no two processes ever
believe they hold the same lock.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

POLL = 0.2


class LockBusy(Exception):
    """The lock stayed held by another process for the whole wait; ``holder`` names it."""

    def __init__(self, path: Path, holder: str, waited: float):
        super().__init__(f"{path} is held by {holder}")
        self.path = path
        self.holder = holder
        self.waited = waited


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def describe(text: str) -> str:
    """The holder a lock file names, as text; the raw text when it is not a holder line."""
    text = text.strip()
    if not text:
        return "a holder that has not written its entry yet"
    try:
        entry = json.loads(text)
    except ValueError:
        return text
    if not isinstance(entry, dict):
        return text
    return f"{entry.get('holder')} (process {entry.get('pid')}, since {entry.get('since')})"


def _same_file(descriptor: int, path: Path) -> bool:
    try:
        current = os.stat(path)
    except OSError:
        return False
    mine = os.fstat(descriptor)
    return (mine.st_dev, mine.st_ino) == (current.st_dev, current.st_ino)


@contextmanager
def hold(
    path: Path,
    holder: str,
    *,
    wait: float | None = 0.0,
    remove: bool = False,
    waiting: Callable[[str], None] | None = None,
):
    """Hold the lock ``path`` for the block; yield the seconds spent waiting for it.

    ``wait`` is how long to wait for a held lock before ``LockBusy``; None waits as long as it
    takes. ``waiting`` is told the current holder once when the wait begins. The descriptor is
    not inherited by processes the holder starts, so none of them keeps the lock alive.
    """
    path = Path(path)
    started = time.monotonic()
    told = False
    while True:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            if wait is None:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
            else:
                while True:
                    try:
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        current = describe(
                            os.pread(descriptor, 4096, 0).decode("utf-8", "replace")
                        )
                        waited = time.monotonic() - started
                        if waited >= wait:
                            raise LockBusy(path, current, waited) from None
                        if waiting is not None and not told:
                            waiting(current)
                            told = True
                        time.sleep(POLL)
        except BaseException:
            os.close(descriptor)
            raise
        if _same_file(descriptor, path):
            break
        # The file was removed or replaced while this process waited: take the current one.
        os.close(descriptor)
    try:
        entry = json.dumps({"holder": holder, "pid": os.getpid(), "since": _now()})
        os.ftruncate(descriptor, 0)
        os.pwrite(descriptor, (entry + "\n").encode(), 0)
        yield round(time.monotonic() - started, 3)
    finally:
        try:
            os.ftruncate(descriptor, 0)
            if remove and _same_file(descriptor, path):
                path.unlink(missing_ok=True)
        finally:
            os.close(descriptor)


def holder(path: Path) -> str | None:
    """Who holds the lock ``path`` now, or None when its file is missing or nobody holds it."""
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return None
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return describe(os.pread(descriptor, 4096, 0).decode("utf-8", "replace"))
        except OSError:
            return None
        return None
    finally:
        # Closing the descriptor releases the probe's own shared lock.
        os.close(descriptor)


def held(path: Path) -> bool:
    return holder(path) is not None


def holder_pids(path: Path) -> list[int]:
    """The processes the kernel's lock table ``/proc/locks`` names as holding a ``flock`` on the
    file ``path``, as seen from this PID namespace; empty where the table is unavailable or the
    holder is not visible from here."""
    try:
        inode = os.stat(path).st_ino
        table = Path("/proc/locks").read_text()
    except OSError:
        return []
    found = []
    for line in table.splitlines():
        fields = line.split()
        # "1: FLOCK ADVISORY WRITE <pid> <major>:<minor>:<inode> <start> <end>"; a waiter's line
        # carries "->" before its type.
        if "->" in fields or len(fields) < 6 or fields[1] != "FLOCK":
            continue
        try:
            pid = int(fields[4])
            number = int(fields[5].rsplit(":", 1)[1])
        except (ValueError, IndexError):
            continue
        if number == inode and pid > 0:
            found.append(pid)
    return found


@contextmanager
def removing(path: Path, holder_name: str, *, wait: float | None = 0.0):
    """Hold a lock that is removed while still held, as a close removes a task's locks."""
    with hold(path, holder_name, wait=wait, remove=True) as waited:
        yield waited


__all__ = [
    "POLL",
    "LockBusy",
    "describe",
    "held",
    "hold",
    "holder",
    "holder_pids",
    "removing",
]
