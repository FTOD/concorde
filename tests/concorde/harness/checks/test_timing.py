from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import sys
import threading
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
    @verifies("scenario.checks.timing-spans")
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

    @verifies("scenario.checks.timing-summary")
    def test_overlap_and_missing_are_not_wall_or_thinking(self):
        spans = [
            {
                "process_id": 1,
                "start_ns": 0,
                "duration_ns": 10e9,
                "status": "ok",
                "name": "SPAN-NAME-SECRET",
                "trace_id": "TRACE-SECRET",
                "metadata": {"invocation_id": "LABEL-SECRET"},
            },
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
        self.assertNotIn("SECRET", json.dumps(result))

    @verifies("scenario.checks.timing-spans")
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

    @verifies("scenario.checks.timing-spans")
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


class ObservationScenarioTests(unittest.TestCase):
    @verifies("scenario.checks.timing-no-trace")
    def test_span_outside_a_trace_changes_nothing_and_writes_nothing(self):
        calls = []

        @timed("fixture.unmarked")
        def work(value, *, prompt=None):
            calls.append((value, prompt))
            if value == "fail":
                raise LookupError("SECRET")
            return {"value": value}

        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                with patch.dict(os.environ, {}, clear=True):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        self.assertEqual({"value": 1}, work(1, prompt="p"))
                        with self.assertRaises(LookupError) as caught:
                            work("fail")
                        with Span("fixture.bare", invocation_id="id-1") as bare:
                            inside = "ran"
                        bare.finish("error")
            finally:
                os.chdir(previous)
            self.assertEqual([], list(Path(directory).iterdir()))
        self.assertEqual("SECRET", str(caught.exception))
        self.assertEqual([(1, "p"), ("fail", None)], calls)
        self.assertEqual("ran", inside)
        self.assertIsNone(bare.record)
        self.assertIsNone(bare.trace)
        self.assertEqual("", stderr.getvalue())

    @verifies("scenario.checks.timing-standalone-directory")
    def test_standalone_directory_receives_one_private_file_or_nothing(self):
        @timed("fixture.standalone")
        def work():
            return "done"

        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            good = base / "timing"
            good.mkdir()
            with patch.dict(os.environ, {"CONCORDE_DIAGNOSTIC_TIMING_DIR": str(good)}):
                self.assertEqual("done", work())
                self.assertEqual("done", work())
            files = sorted(good.iterdir())
            self.assertEqual(2, len(files))  # one new trace file per standalone call
            for path in files:
                self.assertFalse(path.is_symlink())
                self.assertEqual(0o600, path.stat().st_mode & 0o777)
                trace = json.loads(path.read_text())
                self.assertEqual(
                    ["fixture.standalone"], [s["name"] for s in trace["spans"]]
                )
                self.assertTrue(trace["complete"])

            # A new file is created exclusively and never through a symbolic link.
            target = base / "elsewhere.json"
            sink = diagnostic_sink(good)
            with patch("concorde.harness.timing.uuid.uuid4", return_value="planted"):
                os.symlink(target, good / "planted.json")
                with self.assertRaises(OSError):
                    sink({"spans": []})
            self.assertFalse(target.exists())

            link = base / "link"
            link.symlink_to(good)
            status = base / "project/.concorde/status"
            status.mkdir(parents=True)
            runs = base / "project/.concorde/runs/r1"
            runs.mkdir(parents=True)
            inside_cwd = Path.cwd().resolve()
            refused = {
                "relative": "timing",
                "missing": str(base / "missing"),
                "symlink": str(link),
                "non-canonical": str(good / ".." / "timing"),
                "status": str(status),
                "runs": str(runs),
                "working-directory": str(inside_cwd),
            }
            before = {p for p in base.rglob("*")}
            cwd_before = set(os.listdir(inside_cwd))
            for label, value in refused.items():
                with self.subTest(label):
                    stderr = io.StringIO()
                    with (
                        patch.dict(
                            os.environ, {"CONCORDE_DIAGNOSTIC_TIMING_DIR": value}
                        ),
                        contextlib.redirect_stderr(stderr),
                    ):
                        self.assertEqual("done", work())
                    self.assertEqual("CONCORDE_TIMING_INCOMPLETE\n", stderr.getvalue())
            self.assertEqual(before, {p for p in base.rglob("*")})
            self.assertEqual(cwd_before, set(os.listdir(inside_cwd)))

    @verifies("scenario.checks.timing-sink-failure")
    def test_failing_sink_counts_incomplete_once_and_changes_no_outcome(self):
        received = []
        attempts = []

        def failing(value):
            attempts.append(value)
            raise OSError("disk full SECRET")

        sinks = {"working": received.append, "failing": failing}

        @timed("admission.request")
        def request(outcome):
            if outcome["status"] == "raised":
                raise LookupError("boundary_violation")
            return outcome

        def run(kind, outcome):
            trace = Trace(sink=sinks[kind])
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                try:
                    with tracing(trace):
                        result = request(outcome)
                except LookupError as error:
                    result = ("raised", str(error))
            return result, stderr.getvalue(), trace

        for outcome in (
            {"status": "succeeded", "invocation_id": "x"},
            {"status": "failed", "errors": [{"code": "boundary_violation"}]},
            {"status": "raised"},
        ):
            with self.subTest(outcome["status"]):
                received.clear()
                attempts.clear()
                expected, quiet, kept = run("working", json.loads(json.dumps(outcome)))
                actual, noisy, lost = run("failing", json.loads(json.dumps(outcome)))
                self.assertEqual(expected, actual)
                self.assertEqual("", quiet)
                self.assertEqual("CONCORDE_TIMING_INCOMPLETE\n", noisy)
                self.assertEqual(0, kept.incomplete)
                self.assertEqual(1, lost.incomplete)
                self.assertEqual(1, len(received))
                self.assertEqual(1, len(attempts))  # never retried

    @verifies("scenario.checks.timing-trace-cap")
    def test_full_trace_counts_omitted_and_open_spans(self):
        received = []
        trace = Trace(sink=received.append)
        with tracing(trace):
            for _ in range(20000):
                with Span("filler"):
                    pass
            with Span("beyond-cap") as beyond:
                pass
            late = Span("late")
            with late:
                pass
        [value] = received
        self.assertEqual(20000, len(value["spans"]))
        self.assertNotIn("beyond-cap", {s["name"] for s in value["spans"]})
        self.assertIsNone(beyond.record)
        self.assertEqual(2, value["omitted"])
        self.assertFalse(value["complete"])

        received.clear()
        trace = Trace(sink=received.append)
        with tracing(trace):
            with Span("closed"):
                pass
            Span("still-open", stage="plan")
        [value] = received
        open_span = next(s for s in value["spans"] if s["name"] == "still-open")
        self.assertEqual("incomplete", open_span["status"])
        self.assertIsNone(open_span["duration_ns"])
        self.assertEqual(1, value["omitted"])
        self.assertFalse(value["complete"])

    @verifies("scenario.checks.timing-concurrent-traces")
    def test_interleaved_threads_and_tasks_keep_their_own_traces(self):
        barrier = threading.Barrier(4)

        def thread_worker(index):
            trace = Trace(f"thread-{index}")
            with tracing(trace):
                with Span("outer", invocation_id=f"t{index}"):
                    barrier.wait(timeout=10)  # every trace is open before any span ends
                    with Span("inner"):
                        barrier.wait(timeout=10)
            return trace

        with ThreadPoolExecutor(max_workers=4) as pool:
            traces = list(pool.map(thread_worker, range(4)))
        for index, trace in enumerate(traces):
            self.assertEqual(["inner", "outer"], [s["name"] for s in trace.records])
            self.assertEqual(
                {f"thread-{index}"}, {s["trace_id"] for s in trace.records}
            )
            self.assertEqual(f"t{index}", trace.records[1]["metadata"]["invocation_id"])
            self.assertEqual(trace.records[1]["span_id"], trace.records[0]["parent_id"])

        async def task_worker(index, gates):
            trace = Trace(f"task-{index}")
            with tracing(trace):
                with Span("outer"):
                    await gates[index].wait()
                    with Span("inner"):
                        await asyncio.sleep(0)
            return trace

        async def interleave():
            gates = [asyncio.Event() for _ in range(3)]
            tasks = [asyncio.create_task(task_worker(i, gates)) for i in range(3)]
            await asyncio.sleep(0)
            for gate in reversed(gates):  # finish in the opposite order of starting
                gate.set()
                await asyncio.sleep(0)
            return await asyncio.gather(*tasks)

        for index, trace in enumerate(asyncio.run(interleave())):
            self.assertEqual({f"task-{index}"}, {s["trace_id"] for s in trace.records})
            self.assertEqual(["inner", "outer"], [s["name"] for s in trace.records])
            self.assertEqual(trace.records[1]["span_id"], trace.records[0]["parent_id"])
