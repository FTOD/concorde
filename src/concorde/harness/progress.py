"""The progress file of a worker run: ``status.json``, kept current while the run goes on.

The host rewrites it atomically at every phase change and at most once a second for the worker's
activity, so an observer such as the main session's run view can show what a run is doing. It is
an observation aid only; the run record is the run's evidence.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from .runs import now

PHASES = ("preparing", "worker", "audit", "checks", "finished")
TARGET_KEYS = ("file_path", "path", "notebook_path", "pattern", "command", "url")
TARGET_LIMIT = 200


def describe(tool: str, arguments) -> dict:
    """A tool call as ``tool`` and a short ``target``: its path, pattern or command's first line."""
    target = ""
    if isinstance(arguments, dict):
        for key in TARGET_KEYS:
            value = arguments.get(key)
            if isinstance(value, str) and value:
                target = value.strip().splitlines()[0] if value.strip() else ""
                break
    return {"tool": str(tool), "target": target[:TARGET_LIMIT], "at": now()}


class Progress:
    """Writes one run's ``status.json``; safe to call from the stream-reading thread."""

    def __init__(self, root: Path, **identity):
        self.path = root / "status.json"
        self._lock = threading.Lock()
        self._last_action_write = 0.0
        self.state = {
            **identity,
            "phase": "preparing",
            "round": 0,
            "last_action": None,
            "status": None,
            "host_pid": os.getpid(),
            "started_at": now(),
            "updated_at": now(),
        }
        self._write()

    def phase(self, phase: str, **fields) -> None:
        if phase not in PHASES:
            raise ValueError(f"unknown progress phase {phase!r}")
        with self._lock:
            self.state.update(fields, phase=phase)
            self._write()

    def action(self, tool: str, arguments) -> None:
        """Record the worker's latest tool call, writing at most once a second."""
        with self._lock:
            self.state["last_action"] = describe(tool, arguments)
            if time.monotonic() - self._last_action_write >= 1.0:
                self._write()

    def finish(self, status: str) -> None:
        self.phase("finished", status=status)

    def _write(self) -> None:
        self.state["updated_at"] = now()
        self._last_action_write = time.monotonic()
        temporary = self.path.with_suffix(".json.tmp")
        try:
            temporary.write_text(
                json.dumps(self.state, indent=2, sort_keys=True) + "\n"
            )
            temporary.replace(self.path)
        except OSError:
            # Progress is an observation aid; a failed write never changes the run.
            pass


__all__ = ["PHASES", "Progress", "describe"]
