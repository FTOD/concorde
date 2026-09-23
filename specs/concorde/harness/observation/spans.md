# Observation spans

The precise obligations, scenarios and record formats of [Observation](module.md).

## Requirements

### req.observation.diagnostics-passive — Recording never changes the work

Recording, persisting or failing to persist a diagnostic span SHALL NOT change the outcome, the
retry behaviour or the authority of the work it describes.

A sink or observer failure marks the telemetry incomplete and writes one
`CONCORDE_TIMING_INCOMPLETE` line to standard error; nothing else follows from it.

### req.observation.no-content — Spans hold no content

A diagnostic span SHALL NOT contain prompts, source text, tool output, environment values, command
arguments or exception messages.

Labels are kept only when they are Host-issued identifiers of at most 160 characters drawn from
letters, digits and `-_.:`; any other label value is recorded as null.

### req.observation.unknown-stays-unknown — Unreported figures stay unknown

A count, duration or context figure that the observed work did not report SHALL be recorded and
summarized as null, never as zero.

### req.observation.per-process-clocks — Durations are never compared across processes

A timing summary SHALL NOT subtract timestamps taken in different processes.

Covered time is therefore computed per process, as the union of that process's intervals, and wall
timestamps are used only to correlate records.

## Scenarios

### scenario.observation.diagnostic-spans — A span records nested work without its content

- GIVEN a trace is open and Host code marks nested units of work as spans
- WHEN the work ends successfully, with an error or by cancellation
- THEN each span records its name, status, monotonic duration, wall start time, its own, parent, trace and process identities, and the Host-issued invocation identities given to it
- AND counts that the work did not report are null
- BUT no prompt, source text, tool output, environment value, command argument or exception message is recorded

See [passive](#req.observation.diagnostics-passive), [no content](#req.observation.no-content) and
[unknown stays unknown](#req.observation.unknown-stays-unknown).

### scenario.observation.no-trace — Marking a span outside a trace records nothing

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` is not set
- WHEN Host code marks a unit of work as a span
- THEN the work runs and returns exactly as unmarked work would
- AND no span is kept and no file is written

### scenario.observation.standalone-directory — A standalone process writes its trace to a named directory

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` names an existing, absolute, canonical directory outside the working directory and outside any `.concorde/status` or `.concorde/runs` directory
- WHEN Host code marks a unit of work as a span
- THEN a new trace file for that work is created in the directory with mode 0600, without following a symbolic link
- AND the directory grants nothing beyond receiving that file

A directory that does not meet these conditions receives nothing; the telemetry is marked
incomplete and the work runs unchanged.

### scenario.observation.sink-failure — A failing sink marks the trace incomplete

- GIVEN a trace whose sink fails when it receives the finished trace
- WHEN the traced work ends
- THEN the trace is counted incomplete and one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work's result, status and error codes are the same as with a working sink
- BUT the work is not retried

See [passive](#req.observation.diagnostics-passive).

### scenario.observation.trace-cap — A full trace counts what it omits

- GIVEN a trace that already holds 20,000 spans
- WHEN more spans finish
- THEN they are not stored, and the trace reports how many were omitted and that it is incomplete
- AND spans still open when the trace is handed to its sink are stored with status `incomplete` and counted as omitted

### scenario.observation.concurrent-traces — Concurrent traces stay separate

- GIVEN several threads or tasks each run work under their own trace
- WHEN their spans finish in interleaved order
- THEN every span is stored in the trace that was open where its work started, with that trace's identity

### scenario.observation.session-observation — A Pi session is observed without new authority

- GIVEN a user session or Task subagent session that loads the session observer
- WHEN the session makes model requests, calls tools, waits for the developer, compacts or starts asynchronous child runs
- THEN it appends `concorde.timing.v1` session entries with the measured intervals and the context, usage, cache, reserve and compaction figures Pi reported, with unreported figures null
- AND closed facts supplied by the user session are recorded with a reason and scope from their fixed vocabularies, and any other value is dropped
- BUT the observer registers no tool, changes no prompt or setting, starts no session and sends nothing over the network

### scenario.observation.summary — A timing summary reports covered time per process

- GIVEN a Pi session file or event log with observer spans, some overlapping and some without a duration
- WHEN the analysis script summarizes it
- THEN it reports the covered seconds of each process as the union of that process's intervals, and the summed span seconds separately
- AND spans without a duration make the summary incomplete instead of counting as zero
- AND wall time and model thinking time are reported as unknown
- BUT no message body, prompt, tool output or session identity appears in the output

See [per-process clocks](#req.observation.per-process-clocks).

### scenario.observation.summary-fallback — Without observer spans the summary uses Pi's own events

- GIVEN a session file or event log that holds no observer spans but timestamped tool events
- WHEN the analysis script summarizes it
- THEN it estimates tool durations from those timestamps and labels the source `native-wall-estimate`
- AND tool calls without an end are counted as open and make the summary incomplete

## Span record

A span is a JSON object with these fields; all are present:

| Field | Content |
| --- | --- |
| `schema_version` | `1` |
| `trace_id`, `span_id` | UUIDs; the trace of a Host request takes the request's root invocation identity |
| `parent_id` | the enclosing span, or null |
| `layer` | `A` for a Pi session observer, `B` for Host runtime work and tool spans, `C` for an interval measured by an external runner and adapted to this shape |
| `name` | the span name, such as `admission.request`, `session.turn` or `session.tool` |
| `process_id` | the operating-system process identity |
| `session_id`, `task_id` | the Pi session and task identities when known, else null |
| `started_at` | UTC wall time of the start, for correlation only |
| `start_ns` | process-local monotonic start |
| `duration_ns` | monotonic duration, or null when the work did not finish |
| `status` | `ok`, `error`, `cancelled` or `incomplete` |
| `metadata` | only the counts `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `prompt_bytes`, `context_bytes`, `items`, `returncode`, `probe_index`, and the labels `operation`, `stage`, `invocation_id`, `launch_invocation_id`, `target_id`, `change_id`, `context_id`; any other key is dropped |

A count must be a finite number below 10^18 and nonnegative, except `returncode`; otherwise it is
null. Session observer entries add `telemetry_incomplete`, the number of records the observer failed
to append so far, and may carry the context figures `context_capacity`, `current_context_estimate`,
`reserve_tokens` and the compaction state in `metadata`.

A finished trace handed to a sink is
`{schema_version: 1, trace_id, complete, omitted, spans}`. A trace keeps at most 20,000 spans; the
rest are counted in `omitted`. The session observer keeps at most 1,024 open spans and counts any
further start as incomplete telemetry.

## Library entry points

| Entry point | Behaviour |
| --- | --- |
| `Span(name, **labels)` / `timed(name)` | mark a unit of work as a span; a no-op without an open trace or `CONCORDE_DIAGNOSTIC_TIMING_DIR` |
| `Trace(trace_id=None, sink=None, layer="B")` / `tracing(trace)` | open a trace in the current context; its sink receives the finished trace once |
| `operation_trace(trace_id, sink)` / `traced_operation(sink_for)` | open one trace for a top-level request with the caller's sink, or join the trace already open; `sink_for(host)` supplies the sink of each decorated request |
| `notice_incomplete()` | write the one `CONCORDE_TIMING_INCOMPLETE` line of a sink that could not keep its trace |
| `diagnostic_sink(directory)` | a sink writing each trace as a new mode-0600 file in an existing directory |
| `interval_record(...)` | adapt an interval measured elsewhere to the span shape |
| `analyze_native(records)` / `summarize(spans)` | the timing summary of session entries, event records or spans |

The timing summary is
`{complete, summed_span_seconds, covered_seconds_by_process, wall_seconds: null,
server_thinking_seconds: null, source, observed_spans, open_tools, telemetry_incomplete,
latest_context, malformed_records}`, where `source` is `passive-monotonic` or
`native-wall-estimate` and `latest_context` holds the last known `context_capacity`,
`current_context_estimate`, `reserve_tokens`, `input_tokens`, `cache_read_tokens` and
`cache_write_tokens`, each possibly null.
