from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))
from concorde.harness.timing import (
    Span,
    Trace,
    diagnostic_sink,
    metadata,
    summarize,
    timed,
    tracing,
)
from concorde.spec.verification import verifies


class TimingTests(unittest.TestCase):
    @verifies("scenario.observation.diagnostic-spans")
    def test_success_error_cancel_unknown_privacy(self):
        trace = Trace()
        with tracing(trace):
            with Span("outer", prompt="SECRET", input_tokens=None) as outer:
                with Span("inner"):
                    pass
                try:
                    with Span("failure"):
                        raise ValueError("SECRET")
                except ValueError:
                    pass
                try:
                    with Span("cancel"):
                        raise KeyboardInterrupt
                except KeyboardInterrupt:
                    pass
        self.assertEqual(
            [s["status"] for s in trace.records], ["ok", "error", "cancelled", "ok"]
        )
        self.assertTrue(all(s["duration_ns"] >= 0 for s in trace.records))
        self.assertEqual(trace.records[0]["parent_id"], outer.record["span_id"])
        self.assertIsNone(trace.records[-1]["metadata"]["input_tokens"])
        self.assertNotIn("SECRET", json.dumps(trace.records))
        self.assertEqual(
            metadata({"argv": "SECRET", "env": "SECRET", "output": "SECRET"}), {}
        )

    @verifies("scenario.observation.diagnostic-spans")
    def test_overlap_and_missing_are_not_wall_or_thinking(self):
        spans = [
            {"process_id": 1, "start_ns": 0, "duration_ns": 10e9, "status": "ok"},
            {"process_id": 1, "start_ns": 2e9, "duration_ns": 4e9, "status": "ok"},
            {"process_id": 1, "start_ns": 8e9, "duration_ns": 4e9, "status": "ok"},
            {
                "process_id": 2,
                "start_ns": 0,
                "duration_ns": None,
                "status": "incomplete",
            },
        ]
        result = summarize(spans)
        self.assertEqual(result["covered_seconds_by_process"], {"1": 12})
        self.assertEqual(result["summed_span_seconds"], 18)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["wall_seconds"])
        self.assertIsNone(result["server_thinking_seconds"])

    @verifies("scenario.observation.diagnostic-spans")
    def test_concurrency_sink_failure_and_cap(self):
        def worker(index):
            trace = Trace(
                str(index), sink=lambda _: (_ for _ in ()).throw(OSError("secret"))
            )
            with tracing(trace):
                with Span("work"):
                    pass
            return trace

        with ThreadPoolExecutor(max_workers=4) as pool:
            traces = list(pool.map(worker, range(12)))
        self.assertEqual(len({t.records[0]["trace_id"] for t in traces}), 12)
        self.assertTrue(all(t.incomplete == 1 for t in traces))
        trace = Trace()
        trace.records = [{}] * 20000
        trace.emit({})
        self.assertEqual(trace.incomplete, 1)

    @verifies(
        "scenario.observation.session-observation",
        "scenario.observation.diagnostic-spans",
    )
    def test_native_analysis_omits_payloads(self):
        from concorde.harness.timing import analyze_native

        native = [
            {
                "type": "tool_execution_start",
                "toolCallId": "a",
                "timestamp": 1000,
                "args": {"secret": "PRIVATE"},
            },
            {
                "type": "tool_execution_end",
                "toolCallId": "a",
                "timestamp": 3000,
                "result": "PRIVATE",
            },
        ]
        result = analyze_native(native)
        self.assertEqual(result["covered_seconds_by_process"], {"native-wall-clock": 2})
        self.assertIsNone(result["latest_context"]["context_capacity"])
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertFalse(analyze_native([])["complete"])

    @verifies("scenario.observation.diagnostic-spans")
    def test_cancelled_root_preserves_pending_span_identity_without_persistence(self):
        from types import SimpleNamespace
        from concorde.harness.timing import traced_operation

        events = []
        with tempfile.TemporaryDirectory() as directory:
            host = SimpleNamespace(
                project_root=Path(directory),
                archive_root=None,
                mode="execute",
                invocation_id="initial",
                root_invocation_id=None,
                depth=0,
                observe=lambda event, **value: events.append(value),
            )

            def sink_for(host):
                return lambda value: host.observe("timing", **value)

            @traced_operation(sink_for)
            def cancelled(*, host_context):
                Span("unfinished.prepare")
                return {
                    "invocation_id": "bound-root",
                    "status": "failed",
                    "errors": [{"code": "execution_cancelled"}],
                }

            result = cancelled(host_context=host)
            self.assertEqual(result["status"], "failed")
            # The caller's sink decides where a trace goes; the recorder writes nothing itself.
            self.assertFalse((Path(directory) / ".concorde/runs").exists())
        [trace] = events
        self.assertFalse(trace["complete"])
        self.assertTrue(all(s["trace_id"] == "bound-root" for s in trace["spans"]))
        self.assertEqual(
            "cancelled",
            next(s for s in trace["spans"] if s["name"] == "operation.total")["status"],
        )
        self.assertIsNone(
            next(s for s in trace["spans"] if s["name"] == "unfinished.prepare")[
                "duration_ns"
            ]
        )

    @verifies("scenario.observation.diagnostic-spans")
    def test_standalone_diagnostics_and_disabled_fast_path(self):
        @timed("fixture.install")
        def mutation():
            return 42

        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mutation(), 42)
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"CONCORDE_DIAGNOSTIC_TIMING_DIR": directory}):
                self.assertEqual(mutation(), 42)
            paths = list(Path(directory).glob("*.json"))
            self.assertEqual(len(paths), 1)
            self.assertEqual(paths[0].stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                json.loads(paths[0].read_text())["spans"][0]["name"], "fixture.install"
            )
        with self.assertRaises(ValueError):
            diagnostic_sink(Path("relative"))
