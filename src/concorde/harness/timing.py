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


def mark_incomplete():
    trace = _CURRENT.get()
    if trace is not None:
        trace.incomplete += 1


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


@contextmanager
def operation_trace(trace_id, sink):
    """Open a trace for one top-level unit of work with the caller's ``sink``.

    Inside an open trace the work joins it and ``sink`` is not used.
    """
    if _CURRENT.get() is not None:
        yield _CURRENT.get()
        return
    with tracing(Trace(trace_id, sink=sink)) as trace:
        yield trace


def traced_operation(sink_for):
    """Trace each call of a request function taking ``host_context`` in its own trace.

    ``sink_for(host)`` supplies the sink that receives the finished trace; Observation never
    decides where a trace is kept.
    """

    def decorate(function):
        @functools.wraps(function)
        def call(*args, **kwargs):
            host = kwargs["host_context"]
            with operation_trace(
                host.root_invocation_id or host.invocation_id, sink_for(host)
            ) as trace:
                with Span("operation.total") as span:
                    result = function(*args, **kwargs)
                    span.finish(
                        "ok"
                        if result.get("status") in {"succeeded", "described"}
                        else "cancelled"
                        if any(
                            error.get("code") == "execution_cancelled"
                            for error in result.get("errors", [])
                        )
                        else "error",
                        invocation_id=result.get("invocation_id"),
                    )
                if host.depth == 0:
                    trace.trace_id = result["invocation_id"]
                    for record in [*trace.records, *trace.pending.values()]:
                        record["trace_id"] = trace.trace_id
                return result

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


def analyze_native(records):
    """Prefer passive monotonic spans; native timestamped tool events fill absent instrumentation.

    Session cumulative spend never stands in for current context. Uninstrumented request duration,
    reserve and capacity remain unknown. This analysis returns no raw session bodies or identities.
    """
    spans = []
    pending = {}
    context = {
        k: None
        for k in (
            "context_capacity",
            "current_context_estimate",
            "reserve_tokens",
            "input_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
        )
    }
    incomplete = 0
    losses = {}
    fallback = []
    for entry in records:
        if not isinstance(entry, dict):
            incomplete += 1
            continue
        if (
            entry.get("type") == "custom"
            and entry.get("customType") == "concorde.timing.v1"
        ):
            record = entry.get("data", {})
            if (
                isinstance(record, dict)
                and record.get("schema_version") == 1
                and type(record.get("process_id")) is int
                and type(record.get("start_ns")) in (int, float)
                and 0 <= record["start_ns"] < 1e30
                and (
                    record.get("duration_ns") is None
                    or (
                        type(record.get("duration_ns")) in (int, float)
                        and 0 <= record["duration_ns"] < 1e30
                    )
                )
                and record.get("status") in {"ok", "error", "cancelled", "incomplete"}
            ):
                spans.append(
                    {
                        key: record.get(key)
                        for key in ("process_id", "start_ns", "duration_ns", "status")
                    }
                )
                meta = record.get("metadata", {})
                if not isinstance(meta, dict):
                    incomplete += 1
                    continue
                for key in context:
                    if key in meta:
                        n = meta[key]
                        context[key] = n if type(n) in (int, float) and n >= 0 else None
                loss = record.get("telemetry_incomplete", 0)
                trace_id = record.get("trace_id")
                if isinstance(trace_id, str) and type(loss) is int and loss >= 0:
                    losses[trace_id] = max(losses.get(trace_id, 0), loss)
            else:
                incomplete += 1
            continue
        if entry.get("type") == "message" and isinstance(entry.get("message"), dict):
            message = entry["message"]
            timestamp = message.get("timestamp")
            if message.get("role") == "assistant":
                usage = message.get("usage") or {}
                if isinstance(usage, dict):
                    for target, source in (
                        ("input_tokens", "input"),
                        ("cache_read_tokens", "cacheRead"),
                        ("cache_write_tokens", "cacheWrite"),
                    ):
                        n = usage.get(source)
                        context[target] = (
                            n if type(n) in (int, float) and n >= 0 else None
                        )
                blocks = message.get("content")
                for block in blocks if isinstance(blocks, list) else []:
                    if (
                        isinstance(block, dict)
                        and block.get("type") == "toolCall"
                        and isinstance(block.get("id"), str)
                    ):
                        pending[block["id"]] = timestamp
            elif message.get("role") == "toolResult":
                key = message.get("toolCallId")
                start = pending.pop(key, None) if isinstance(key, str) else None
                duration = (
                    (timestamp - start) * 1e6
                    if type(start) in (int, float)
                    and type(timestamp) in (int, float)
                    and timestamp >= start
                    else None
                )
                fallback.append(
                    {
                        "process_id": "native-wall-clock",
                        "start_ns": (start or 0) * 1e6,
                        "duration_ns": duration,
                        "status": "ok" if duration is not None else "incomplete",
                    }
                )
            continue
        event = entry.get("event", entry)
        if not isinstance(event, dict):
            continue
        timestamp = entry.get("timestamp", entry.get("ts", event.get("timestamp")))
        if isinstance(timestamp, str):
            try:
                timestamp = (
                    datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
                    * 1000
                )
            except ValueError:
                timestamp = None
        kind = event.get("type")
        key = event.get("toolCallId")
        if kind == "tool_execution_start" and isinstance(key, str):
            pending[key] = timestamp
        elif kind == "tool_execution_end" and isinstance(key, str):
            start = pending.pop(key, None)
            duration = (
                (timestamp - start) * 1e6
                if type(start) in (int, float)
                and type(timestamp) in (int, float)
                and timestamp >= start
                else None
            )
            fallback.append(
                {
                    "process_id": "native-wall-clock",
                    "start_ns": (start or 0) * 1e6,
                    "duration_ns": duration,
                    "status": "ok" if duration is not None else "incomplete",
                }
            )
    selected = spans if spans else fallback
    incomplete += sum(losses.values())
    return {
        **summarize(selected),
        "source": "passive-monotonic" if spans else "native-wall-estimate",
        "observed_spans": len(selected),
        "open_tools": len(pending),
        "telemetry_incomplete": incomplete,
        "latest_context": context,
        "complete": bool(selected)
        and not pending
        and not incomplete
        and summarize(selected)["complete"],
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
