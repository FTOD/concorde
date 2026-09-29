"""The locks under ``.concorde/locks/``: files locked with ``flock`` that hold only their holder.

A holder writes one line of JSON naming itself, ``{"holder", "pid", "since"}`` with ``session``,
the Claude Code session it works for when its environment names one, and ``task`` when the taker
names the task, once it holds the lock, and empties the file before it releases it, so a waiter
that gives up can say who holds it. The kernel releases a ``flock`` however its process ends. A
lock taken with ``remove`` (the run lock) is removed by its holder while still held; a lock whose
file was removed or replaced while a process waited for it is taken again on the file that is there
now, so no two processes ever believe they hold the same lock.

A lock may be handed to a process: its taker starts it with the locked descriptor inherited and
names it in the environment variable ``CONCORDE_INHERITED_LOCKS`` (``{"<lock path>": <fd>}``).
``hold`` in that process then adopts the descriptor instead of waiting, since a ``flock`` belongs
to the open file description, which the taker and the process share; once the taker closed its
own copy, the lock lives exactly as long as that process.

Waiting for a lock to be released blocks on the lock itself, shared, in a thread, and lets it go at
once, so a holder that dies wakes the waiter as surely as one that ends.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

POLL = 0.2
# The environment variable naming the locked descriptors a process inherited from its taker.
INHERITED = "CONCORDE_INHERITED_LOCKS"
# The environment variable naming the Claude Code session a process works for.
SESSION = "CLAUDE_CODE_SESSION_ID"


class LockBusy(Exception):
    """The lock stayed held by another process for the whole wait; ``holder`` names it and
    ``entry`` is its holder line as an object, or None when it cannot be read as one."""

    def __init__(
        self, path: Path, holder: str, waited: float, entry: dict | None = None
    ):
        super().__init__(f"{path} is held by {holder}")
        self.path = path
        self.holder = holder
        self.waited = waited
        self.entry = entry


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> dict | None:
    """A holder line as an object, or None when the text is not one."""
    try:
        entry = json.loads(text.strip())
    except ValueError:
        return None
    return entry if isinstance(entry, dict) else None


def describe(text: str) -> str:
    """The holder a lock file names, as text; the raw text when it is not a holder line."""
    text = text.strip()
    if not text:
        return "a holder that has not written its entry yet"
    entry = parse(text)
    if entry is None:
        return text
    extra = "".join(
        f", {name} {entry[name]}" for name in ("session", "task") if entry.get(name)
    )
    return (
        f"{entry.get('holder')} (process {entry.get('pid')}, since {entry.get('since')}"
        f"{extra})"
    )


def line(
    holder: str, pid: int, task: str | None = None, session: str | None = None
) -> bytes:
    """The holder line a process writes into a lock it holds."""
    entry = {"holder": holder, "pid": pid, "since": _now()}
    session = session if session is not None else os.environ.get(SESSION)
    if session:
        entry["session"] = session
    if task:
        entry["task"] = task
    return (json.dumps(entry) + "\n").encode()


def write_entry(descriptor: int, data: bytes) -> None:
    os.ftruncate(descriptor, 0)
    os.pwrite(descriptor, data, 0)


_inherited: dict[str, int] | None = None


def _inherited_locks() -> dict[str, int]:
    """The locked descriptors this process inherited, read from and removed from its environment
    once, so that no process it starts believes it inherited them too."""
    global _inherited
    if _inherited is None:
        _inherited = {}
        text = os.environ.pop(INHERITED, None)
        if text:
            try:
                value = json.loads(text)
            except ValueError:
                value = {}
            if isinstance(value, dict):
                _inherited = {
                    os.path.realpath(path): fd
                    for path, fd in value.items()
                    if isinstance(fd, int)
                }
    return _inherited


def _adopt(path: Path) -> int | None:
    """The inherited descriptor holding the lock ``path``, or None when none was inherited or it
    does not hold that lock; an adopted descriptor is no longer inherited by child processes."""
    descriptor = _inherited_locks().pop(os.path.realpath(path), None)
    if descriptor is None:
        return None
    try:
        # The same open file description already holds the lock, so this succeeds at once; it
        # fails only when the descriptor is not what the taker said.
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not _same_file(descriptor, path):
            raise OSError("the inherited descriptor is not the lock file there now")
        os.set_inheritable(descriptor, False)
    except OSError:
        try:
            os.close(descriptor)
        except OSError:
            pass
        return None
    return descriptor


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
    task: str | None = None,
):
    """Hold the lock ``path`` for the block; yield the seconds spent waiting for it.

    ``wait`` is how long to wait for a held lock before ``LockBusy``; None waits as long as it
    takes. ``waiting`` is told the current holder once when the wait begins. ``task`` is written
    into the holder line. The descriptor is not inherited by processes the holder starts, so none
    of them keeps the lock alive. A descriptor this process inherited for ``path`` is adopted
    without waiting.
    """
    path = Path(path)
    started = time.monotonic()
    told = False
    descriptor = _adopt(path)
    while descriptor is None:
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
                        text = os.pread(descriptor, 4096, 0).decode("utf-8", "replace")
                        current = describe(text)
                        waited = time.monotonic() - started
                        if waited >= wait:
                            raise LockBusy(path, current, waited, parse(text)) from None
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
        descriptor = None
    try:
        write_entry(descriptor, line(holder, os.getpid(), task))
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


def entry(path: Path) -> dict | None:
    """The holder line of the lock ``path`` as an object while a process holds it, else None."""
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return None
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            text = os.pread(descriptor, 4096, 0).decode("utf-8", "replace")
            return parse(text) or {"holder": describe(text)}
        except OSError:
            return None
        return None
    finally:
        os.close(descriptor)


def acquire(path: Path) -> int:
    """Take the lock ``path`` without waiting and return its descriptor, which the caller writes
    its holder line into (``write_entry``) and hands on or closes; ``LockBusy`` names the holder
    when another process holds it. The descriptor is not inheritable until the caller makes it."""
    path = Path(path)
    while True:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            text = os.pread(descriptor, 4096, 0).decode("utf-8", "replace")
            os.close(descriptor)
            raise LockBusy(path, describe(text), 0.0, parse(text)) from None
        except BaseException:
            os.close(descriptor)
            raise
        if _same_file(descriptor, path):
            return descriptor
        os.close(descriptor)


def release(descriptor: int) -> None:
    """Empty and release a lock ``acquire`` took and nobody was handed."""
    try:
        os.ftruncate(descriptor, 0)
    finally:
        os.close(descriptor)


def wait_released(path: Path, timeout: float | None = None) -> bool:
    """Block until no process holds the lock ``path``; False when ``timeout`` seconds passed first.

    It blocks on the lock itself, shared, in a thread, and lets it go at once, so the kernel wakes
    it when the holder releases the lock or dies. A missing file is a free lock; a file removed
    while its holder held it (a run lock) wakes it when that holder lets go.
    """
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return True
    done = threading.Event()

    def block():
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            done.set()
            os.close(descriptor)

    threading.Thread(target=block, name=f"wait {path.name}", daemon=True).start()
    return done.wait(timeout)


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
    "INHERITED",
    "POLL",
    "SESSION",
    "LockBusy",
    "acquire",
    "describe",
    "entry",
    "held",
    "hold",
    "holder",
    "holder_pids",
    "line",
    "parse",
    "release",
    "removing",
    "wait_released",
    "write_entry",
]
