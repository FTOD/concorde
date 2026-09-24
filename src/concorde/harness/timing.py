"""Small bounded diagnostic spans shared by sessions, runtime and tests; never authority.

Durations use a process-local monotonic clock. Wall timestamps correlate processes, not clocks.
No argument, environment value, prompt, source body, output or exception message is collected.
"""

from __future__ import annotations

import contextvars
import functools
import json
import os
import time
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_CURRENT = contextvars.ContextVar("concorde_trace", default=None)
_PARENT = contextvars.ContextVar("concorde_span", default=None)
COUNTS = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "prompt_bytes",
        "context_bytes",
        "items",
        "returncode",
        "probe_index",
    }
)
LABELS = frozenset(
    {
        "operation",
        "stage",
        "invocation_id",
        "launch_invocation_id",
        "target_id",
        "change_id",
        "context_id",
    }
)


def notice_incomplete():
    try:
        sys.stderr.write("CONCORDE_TIMING_INCOMPLETE\n")
    except Exception:
        pass


def metadata(values):
    result = {}
    for key, value in values.items():
        if key in COUNTS:
            result[key] = (
                value
                if type(value) in (int, float)
                and abs(value) < 1e18
                and (value >= 0 or key == "returncode")
                else None
            )
        elif key in LABELS:
            # Host-issued identifiers only, never caller task text.
            result[key] = (
                value
                if isinstance(value, str)
                and len(value) <= 160
                and all(c.isalnum() or c in "-_.:" for c in value)
                else None
            )
    return result


class Trace:
    def __init__(self, trace_id=None, *, sink=None, layer="B"):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.sink = sink
        self.layer = layer
        self.records = []
        self.pending = {}
        self.incomplete = 0

    def emit(self, record):
        if len(self.records) < 20000:
            self.records.append(record)
        else:
            self.incomplete += 1

    def flush(self):
        for record in tuple(self.pending.values()):
            self.emit(record)
            self.incomplete += 1
        self.pending.clear()
        if self.sink is not None:
            try:
                self.sink(
                    {
                        "schema_version": 1,
                        "trace_id": self.trace_id,
                        "complete": not self.incomplete,
                        "omitted": self.incomplete,
                        "spans": self.records,
                    }
                )
            except Exception:
                self.incomplete += 1
                notice_incomplete()


class Span:
    def __init__(self, name, **values):
        self.trace = _CURRENT.get()
        self.record = None
        self.token = None
        if (
            self.trace is not None
            and len(self.trace.records) + len(self.trace.pending) >= 20000
        ):
            self.trace.incomplete += 1
            return
        if self.trace is not None:
            self.record = {
                "schema_version": 1,
                "trace_id": self.trace.trace_id,
                "span_id": str(uuid.uuid4()),
                "parent_id": _PARENT.get(),
                "layer": self.trace.layer,
                "name": name,
                "process_id": os.getpid(),
                "session_id": None,
                "task_id": metadata(values).get("change_id"),
                "started_at": datetime.now(timezone.utc).isoformat(),
                "start_ns": time.monotonic_ns(),
                "duration_ns": None,
                "status": "incomplete",
                "metadata": metadata(values),
            }
            self.trace.pending[self.record["span_id"]] = self.record

    def __enter__(self):
        if self.record is not None:
            self.token = _PARENT.set(self.record["span_id"])
        return self

    def finish(self, status="ok", **values):
        if self.record is not None and self.record["duration_ns"] is None:
            self.record.update(
                duration_ns=max(0, time.monotonic_ns() - self.record["start_ns"]),
                status=status,
            )
            self.record["metadata"].update(metadata(values))
            self.trace.pending.pop(self.record["span_id"], None)
            self.trace.emit(self.record)

    def __exit__(self, kind, error, traceback):
        status = (
            "ok"
            if kind is None
            else "cancelled"
            if isinstance(error, (KeyboardInterrupt, SystemExit))
            or getattr(error, "outcome", None) == "cancelled"
            else "error"
        )
        self.finish(status)
        if self.token is not None:
            _PARENT.reset(self.token)


@contextmanager
def tracing(trace):
    token = _CURRENT.set(trace)
    parent = _PARENT.set(None)
    try:
        yield trace
    finally:
        _PARENT.reset(parent)
        _CURRENT.reset(token)
        trace.flush()


def diagnostic_sink(directory):
    """An explicitly supplied external directory, not inferred primary execution authority."""
    root = Path(directory)
    if (
        not root.is_absolute()
        or root.is_symlink()
        or not root.is_dir()
        or root.resolve() != root
    ):
        raise ValueError(
            "diagnostic directory must be existing, canonical and absolute"
        )
    lifecycle = ".concorde" in root.parts and any(
        part in {"status", "runs"}
        for part in root.parts[root.parts.index(".concorde") + 1 :]
    )
    if root.is_relative_to(Path.cwd().resolve()) or lifecycle:
        raise ValueError("diagnostic scratch cannot be project or lifecycle storage")

    def save(value):
        path = root / (str(uuid.uuid4()) + ".json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, separators=(",", ":"))

    return save


def timed(name):
    """Instrument a deterministic service without serializing its arguments or return value."""

    def decorate(function):
        @functools.wraps(function)
        def call(*args, **kwargs):
            if _CURRENT.get() is None:
                directory = os.environ.get("CONCORDE_DIAGNOSTIC_TIMING_DIR")
                if not directory:
                    return function(*args, **kwargs)
                try:
                    sink = diagnostic_sink(directory)
                except Exception:
                    sink = None
                    notice_incomplete()
                with tracing(Trace(sink=sink)):
                    with Span(name, **metadata(kwargs)):
                        return function(*args, **kwargs)
            with Span(name, **metadata(kwargs)):
                return function(*args, **kwargs)

        return call

    return decorate


def interval_record(
    *,
    name,
    trace_id,
    parent_id=None,
    layer="C",
    started_at,
    start_ns,
    end_ns,
    status="ok",
):
    """Adapt an already measured runner interval to the same diagnostic record."""
    return {
        "schema_version": 1,
        "trace_id": trace_id,
        "span_id": str(uuid.uuid4()),
        "parent_id": parent_id,
        "layer": layer,
        "name": name,
        "process_id": os.getpid(),
        "session_id": None,
        "task_id": None,
        "started_at": started_at,
        "start_ns": start_ns,
        "duration_ns": end_ns - start_ns if end_ns is not None else None,
        "status": status,
        "metadata": {},
    }


def summarize(spans):
    """Union intervals per process; summed span time is explicitly not elapsed wall time."""
    groups = {}
    summed = 0
    complete = True
    for s in spans:
        duration = s.get("duration_ns")
        if not isinstance(duration, (int, float)) or duration < 0:
            complete = False
            continue
        summed += duration
        complete &= s.get("status") != "incomplete"
        groups.setdefault(s.get("process_id"), []).append(
            (s["start_ns"], s["start_ns"] + duration)
        )
    unions = {}
    for process, intervals in groups.items():
        total = 0
        end = None
        for start, stop in sorted(intervals):
            total += max(0, stop - max(start, end if end is not None else start))
            end = max(end if end is not None else stop, stop)
        unions[str(process)] = total / 1e9
    return {
        "complete": complete,
        "summed_span_seconds": summed / 1e9,
        "covered_seconds_by_process": unions,
        "wall_seconds": None,
        "server_thinking_seconds": None,
    }
