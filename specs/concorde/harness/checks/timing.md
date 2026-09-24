# Timing spans

The precise obligations, scenarios and record formats of the timing recorder in
`src/concorde/harness/timing.py`. The [entry](module.md#concept.checks.diagnostic-span) explains
what a diagnostic span is for.

## Span record

A span is a JSON object with these fields; all are present:

| Field | Content |
| --- | --- |
| `schema_version` | `1` |
| `trace_id`, `span_id` | UUIDs, unless the trace was opened with a given identity |
| `parent_id` | the enclosing span, or null |
| `layer` | `B` for host work recorded by this library, `C` for an interval measured by an external runner and adapted to this shape |
| `name` | the span name, such as `check.total` or `check.sandbox_setup` |
| `process_id` | the operating-system process identity |
| `session_id`, `task_id` | a session identity when known, else null; the task identity taken from the `change_id` label, else null |
| `started_at` | UTC wall time of the start, for correlation only |
| `start_ns` | process-local monotonic start |
| `duration_ns` | monotonic duration, or null when the work did not finish |
| `status` | `ok`, `error`, `cancelled` or `incomplete` |
| `metadata` | only the counts `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `prompt_bytes`, `context_bytes`, `items`, `returncode`, `probe_index`, and the labels `operation`, `stage`, `invocation_id`, `launch_invocation_id`, `target_id`, `change_id`, `context_id`; any other key is dropped |

A count must be a finite number below 10^18 and nonnegative, except `returncode`; otherwise it is
null. A label is kept only when it is a host-issued identifier of at most 160 characters drawn from
letters, digits and `-_.:`; otherwise it is null.

A finished trace handed to a sink is `{schema_version: 1, trace_id, complete, omitted, spans}`. A
trace keeps at most 20,000 spans; the rest are counted in `omitted`.

## Library entry points

| Entry point | Behaviour |
| --- | --- |
| `Span(name, **labels)` / `timed(name)` | mark a unit of work as a span; a no-op without an open trace or `CONCORDE_DIAGNOSTIC_TIMING_DIR` |
| `Trace(trace_id=None, sink=None, layer="B")` / `tracing(trace)` | open a trace in the current context; its sink receives the finished trace once |
| `notice_incomplete()` | write the one `CONCORDE_TIMING_INCOMPLETE` line of a sink that could not keep its trace |
| `diagnostic_sink(directory)` | a sink writing each trace as a new mode-0600 file in an existing directory |
| `interval_record(...)` | adapt an interval measured elsewhere to the span shape |
| `summarize(spans)` | the timing summary of finished span records |

The timing summary is `{complete, summed_span_seconds, covered_seconds_by_process, wall_seconds:
null, server_thinking_seconds: null}`.

## Requirements

### req.checks.timing-passive — Recording never changes the work

Recording, persisting or failing to persist a diagnostic span SHALL NOT change the outcome, the
retry behaviour or the authority of the work it describes.

A sink failure marks the trace incomplete and writes one `CONCORDE_TIMING_INCOMPLETE` line to
standard error; nothing else follows from it.

### req.checks.timing-no-content — Spans hold no content

A diagnostic span SHALL NOT contain prompts, source text, tool output, environment values, command
arguments or exception messages.

### req.checks.timing-unknown — Unreported figures stay unknown

A count, duration or context figure that the observed work did not report SHALL be recorded and
summarized as null, never as zero.

### req.checks.timing-per-process — Durations are never compared across processes

A timing summary SHALL NOT subtract timestamps taken in different processes.

Covered time is therefore computed per process, as the union of that process's intervals, and wall
timestamps are used only to correlate records.

## Scenarios

### scenario.checks.timing-spans — A span records nested work without its content

- GIVEN a trace is open and host code marks nested units of work as spans
- WHEN the work ends successfully, with an error or by cancellation
- THEN each span records its name, status, monotonic duration, wall start time, its own, parent, trace and process identities, and the host-issued labels given to it
- AND counts that the work did not report are null, and a span still open when the trace ends keeps a null duration
- BUT no prompt, source text, tool output, environment value, command argument or exception message is recorded

### scenario.checks.timing-no-trace — Marking a span outside a trace records nothing

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` is not set
- WHEN host code marks a unit of work as a span
- THEN the work runs and returns or raises exactly as unmarked work would
- AND no span is kept, nothing is written to standard error and no file is written

### scenario.checks.timing-standalone-directory — A standalone process writes its trace to a named directory

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` names an existing, absolute, canonical directory outside the working directory and outside any `.concorde/status` or `.concorde/runs` directory
- WHEN host code marks a unit of work as a span
- THEN a new trace file for that work is created in the directory with mode 0600, without following a symbolic link
- BUT a directory that does not meet these conditions receives nothing, the telemetry is marked incomplete and the work runs unchanged

### scenario.checks.timing-sink-failure — A failing sink marks the trace incomplete

- GIVEN a trace whose sink fails when it receives the finished trace
- WHEN the traced work ends
- THEN the trace is counted incomplete and one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work's result, status and error codes are the same as with a working sink
- BUT the sink is not retried

### scenario.checks.timing-trace-cap — A full trace counts what it omits

- GIVEN a trace that already holds 20,000 spans
- WHEN more spans finish
- THEN they are not stored, and the trace reports how many were omitted and that it is incomplete
- AND spans still open when the trace is handed to its sink are stored with status `incomplete` and counted as omitted

### scenario.checks.timing-concurrent-traces — Concurrent traces stay separate

- GIVEN several threads or asynchronous tasks each run work under their own trace
- WHEN their spans finish in interleaved order
- THEN every span is stored in the trace that was open where its work started, with that trace's identity and parent

### scenario.checks.timing-summary — A timing summary reports covered time per process

- GIVEN span records, some overlapping and some without a duration
- WHEN they are summarized
- THEN the summary reports the covered seconds of each process as the union of that process's intervals, and the summed span seconds separately
- AND spans without a duration make the summary incomplete instead of counting as zero
- AND wall time and model thinking time are reported as unknown
- BUT no span name, trace identity or label appears in the summary
