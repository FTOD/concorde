"""Being told when a lock file changes, without polling: Linux inotify on a directory of locks.

A holder writes its holder line into a lock file when it takes the lock and empties the file before
it releases it, and a close removes the locks of the task it moves, so every taking, releasing and
removal of a lock is a change of its file that the kernel reports. ``Changes`` watches one
directory under ``.concorde/locks/`` and waits until one of the named files changed; a waiter that
must also learn of a holder that dies blocks on the lock itself (``locks.wait_released``), since a
dying holder changes no file. The kernel interface is reached through ``ctypes``, so this needs no
package beyond Python's own.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import select
import struct
import time
from pathlib import Path

IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_NONBLOCK = 0o4000
IN_CLOEXEC = 0o2000000
MASK = (
    IN_MODIFY
    | IN_ATTRIB
    | IN_CLOSE_WRITE
    | IN_MOVED_FROM
    | IN_MOVED_TO
    | IN_CREATE
    | IN_DELETE
    | IN_DELETE_SELF
    | IN_MOVE_SELF
)
_EVENT = struct.Struct("iIII")


class WatchError(Exception):
    """The kernel refused to watch a directory; the message says why."""


def _libc():
    name = ctypes.util.find_library("c") or "libc.so.6"
    library = ctypes.CDLL(name, use_errno=True)
    library.inotify_init1.argtypes = [ctypes.c_int]
    library.inotify_add_watch.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint32,
    ]
    return library


class Changes:
    """The changes of the files ``names`` in ``directory``, from the moment it was created.

    ``wait(timeout)`` returns True once one of them changed since the last call (or since the
    watch began), False when ``timeout`` seconds passed without a change; ``None`` waits as long
    as it takes. A change that happened between two calls is not lost: the kernel queues it.
    """

    def __init__(self, directory: Path, names: set[str] | None = None):
        self.directory = Path(directory)
        self.names = set(names) if names is not None else None
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            self.library = _libc()
        except OSError as error:
            raise WatchError(f"the C library offers no inotify: {error}") from error
        self.descriptor = self.library.inotify_init1(IN_NONBLOCK | IN_CLOEXEC)
        if self.descriptor < 0:
            number = ctypes.get_errno()
            raise WatchError(f"inotify_init1 failed: {os.strerror(number)}")
        watched = self.library.inotify_add_watch(
            self.descriptor, os.fsencode(self.directory), MASK
        )
        if watched < 0:
            number = ctypes.get_errno()
            os.close(self.descriptor)
            raise WatchError(
                f"inotify cannot watch {self.directory}: {os.strerror(number)}"
            )

    def _drain(self) -> bool:
        """Read every queued event; whether one concerned a watched name or the directory."""
        found = False
        while True:
            try:
                data = os.read(self.descriptor, 65536)
            except BlockingIOError:
                return found
            offset = 0
            while offset + _EVENT.size <= len(data):
                _, mask, _, length = _EVENT.unpack_from(data, offset)
                raw = data[offset + _EVENT.size : offset + _EVENT.size + length]
                offset += _EVENT.size + length
                name = raw.rstrip(b"\0").decode("utf-8", "replace")
                if (
                    mask & (IN_DELETE_SELF | IN_MOVE_SELF)
                    or self.names is None
                    or name in self.names
                ):
                    found = True

    def wait(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self._drain():
                return True
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                return False
            select.select([self.descriptor], [], [], remaining)

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


__all__ = ["Changes", "WatchError"]
