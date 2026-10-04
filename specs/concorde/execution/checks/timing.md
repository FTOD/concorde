# Timing spans

The precise obligations, scenarios and record formats of the timing recorder in
`src/concorde/execution/checks/timing.py`. The entry explains
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
| `metadata` | only the counts `prompt_bytes`, `context_bytes`, `items`, `returncode`, `probe_index`, and the labels `stage`, `target_id`, `change_id`, `context_id`; any other key is dropped |

A count must be a finite number below 10^18 and nonnegative, except `returncode`; otherwise it is
null. A label is kept only when it is a host-issued identifier of at most 160 characters drawn from
letters, digits and `-_.:`; otherwise it is null.

A finished trace handed to a sink is `{schema_version: 1, trace_id, complete, omitted, spans}`. A
trace keeps at most 20,000 spans, open ones included, so an open span holds its place until it
finishes; a span marked while the trace is full is not stored. `omitted` counts the spans not
stored together with the spans still open when the trace is handed to its sink, which are stored
with status `incomplete`, and `complete` is false whenever `omitted` is not zero. The sink receives
a copy of the trace, which is then sealed: a span that finishes or starts afterwards changes nothing
handed over and is not recorded.

## Library entry points

| Entry point | Behaviour |
| --- | --- |
| `Span(name, **labels)` / `timed(name)` | mark a unit of work, or every call of a function, as a span; a no-op without an open trace, except that `timed` then opens one when `CONCORDE_DIAGNOSTIC_TIMING_DIR` is set |
| `Trace(trace_id=None, *, sink=None, layer="B")` / `tracing(trace)` | open a trace in the current context; its sink receives the finished trace once |
| `notice_incomplete()` | write the one `CONCORDE_TIMING_INCOMPLETE` line of a sink that could not keep its trace |
| `diagnostic_sink(directory)` | a sink writing each trace as a new mode-0600 file, never through a symbolic link, in a directory that exists and is absolute, canonical and outside both the working directory and any `.concorde/tasks`, `.concorde/history`, `.concorde/unbound` or `.concorde/locks` directory; any other directory is refused |
| `interval_record(...)` | adapt an interval measured elsewhere to the span shape |
| `summarize(spans)` | the timing summary of finished span records |

The timing summary is `{complete, summed_span_seconds, covered_seconds_by_process}`: what the
spans measured, and nothing they cannot, such as elapsed wall time.

The directory conditions keep diagnostic files apart from the project and from the lifecycle
records and locks Concorde keeps under `.concorde/tasks`, `.concorde/history`, `.concorde/unbound` and `.concorde/locks`. A function marked with
`timed` and called while no trace is open but `CONCORDE_DIAGNOSTIC_TIMING_DIR` is set opens a trace
of its own whose sink is `diagnostic_sink` of that directory; when the directory is refused, the
trace has no sink and the `CONCORDE_TIMING_INCOMPLETE` line is written instead.

A caller opens a trace with a sink, marks nested work and summarizes what the sink received:

```python
received = []

@timed("check.sandbox_setup")  # marks every call of set_up as a span
def set_up():
    ...

with tracing(Trace(sink=received.append)):
    with Span("check.total"):
        set_up()  # its span's parent is check.total

summary = summarize(received[0]["spans"])
```

The sink receives the finished trace once, when the `tracing` block ends; `summarize` reads the span
records of that trace.

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

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` names an existing, absolute, canonical directory outside the working directory and outside any `.concorde/tasks`, `.concorde/history`, `.concorde/unbound` or `.concorde/locks` directory
- WHEN host code marks a unit of work as a span
- THEN a new trace file for that work is created in the directory with mode 0600, without following a symbolic link

### scenario.checks.timing-invalid-directory — A refused timing directory receives nothing

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` names a directory that is relative, missing, a symbolic link, not canonical, the working directory or inside it, or inside a `.concorde/tasks`, `.concorde/history`, `.concorde/unbound` or `.concorde/locks` directory
- WHEN host code marks a unit of work as a span
- THEN nothing is written to that directory or to the working directory
- AND one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work returns exactly as unmarked work would

### scenario.checks.timing-sink-failure — A failing sink marks the trace incomplete

- GIVEN a trace whose sink fails when it receives the finished trace
- WHEN the traced work ends
- THEN the trace is counted incomplete and one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work's result, status and error codes are the same as with a working sink
- BUT the sink is not retried

### scenario.checks.timing-trace-cap — A full trace counts what it omits

- GIVEN a trace that already holds 20,000 spans, finished or open
- WHEN more spans are marked
- THEN they are not stored, and the trace reports how many were omitted and that it is incomplete
- AND spans still open when the trace is handed to its sink are stored within the cap with status `incomplete` and also counted in `omitted`

### scenario.checks.timing-concurrent-traces — Concurrent traces stay separate

- GIVEN several threads or asynchronous tasks each run work under their own trace
- WHEN their spans finish in interleaved order
- THEN every span is stored in the trace that was open where its work started, with that trace's identity and parent

### scenario.checks.timing-summary — A timing summary reports covered time per process

- GIVEN span records, some overlapping and some without a duration
- WHEN they are summarized
- THEN the summary reports the covered seconds of each process as the union of that process's intervals, and the summed span seconds separately
- AND spans without a duration make the summary incomplete instead of counting as zero
- BUT no span name, trace identity or label appears in the summary
