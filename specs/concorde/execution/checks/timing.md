# Timing spans

This document states the precise details of the timing recorder in
`src/concorde/execution/checks/timing.py`:

- obligations
- scenarios
- record formats

The entry explains what a diagnostic span is for.

## Span record

A span is a JSON object. All of these fields are present:

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

Except for `returncode`, a count must meet all of these conditions:

- be a finite number
- be below 10^18
- be nonnegative

Otherwise, the count is null. Only when a label is a host-issued identifier of at most 160
characters drawn from these characters is it kept:

- letters
- digits
- `-_.:`

Otherwise, the label is null.

A finished trace handed to a sink is `{schema_version: 1, trace_id, complete, omitted, spans}`. A
trace keeps at most 20,000 spans, open ones included. An open span therefore holds its place until it
finishes. While the trace is full, a span marked is not stored. `omitted` counts the spans not
stored together with the spans still open when the trace is handed to its sink. The spans still
open are stored with status `incomplete`. Whenever `omitted` is not zero, `complete` is false.
The sink receives a copy of the trace. The trace is then sealed. Afterwards, a span that finishes
or starts changes nothing handed over. The span is not recorded.

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

The directory conditions keep diagnostic files apart from the project and from Concorde's
lifecycle records and locks. Concorde keeps those records and locks under these paths:

- `.concorde/tasks`
- `.concorde/history`
- `.concorde/unbound`
- `.concorde/locks`

When called while no trace is open but `CONCORDE_DIAGNOSTIC_TIMING_DIR` is set, a function marked
with `timed` opens a trace of its own. The trace's sink is `diagnostic_sink` of that directory.
When the directory is refused, the trace has no sink. The `CONCORDE_TIMING_INCOMPLETE` line is
written instead.

A caller performs these steps:

- opens a trace with a sink
- marks nested work
- summarizes what the sink received

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

When the `tracing` block ends, the sink receives the finished trace once. `summarize` reads the span
records of that trace.

## Requirements

### req.checks.timing-passive — Recording never changes the work

When recording, persisting or failing to persist a diagnostic span, the timing recorder SHALL NOT
change these aspects of the work the span describes:

- the outcome
- the retry behaviour
- the authority

A sink failure marks the trace incomplete. The sink failure writes one
`CONCORDE_TIMING_INCOMPLETE` line to standard error. Nothing else follows from the sink failure.

### req.checks.timing-no-content — Spans hold no content

A diagnostic span SHALL NOT contain any of this content:

- prompts
- source text
- tool output
- environment values
- command arguments
- exception messages

### req.checks.timing-unknown — Unreported figures stay unknown

For any of these figures that the observed work did not report, the timing recorder SHALL record
and summarize the figure as null, never as zero:

- a count
- a duration
- a context figure

### req.checks.timing-per-process — Durations are never compared across processes

A timing summary SHALL NOT subtract timestamps taken in different processes.

Covered time is therefore computed per process, as the union of that process's intervals. Wall
timestamps are used only to correlate records.

## Scenarios

### scenario.checks.timing-spans — A span records nested work without its content

- GIVEN a trace is open
- AND host code marks nested units of work as spans
- WHEN the work ends successfully, with an error or by cancellation
- THEN each span records its name and status
- AND each span records its monotonic duration and wall start time
- AND each span records its own and parent identities
- AND each span records its trace and process identities
- AND each span records the host-issued labels given to it
- AND counts that the work did not report are null
- AND when the trace ends, a span still open keeps a null duration
- BUT no prompt or source text is recorded
- AND no tool output or environment value is recorded
- AND no command argument or exception message is recorded

### scenario.checks.timing-no-trace — Marking a span outside a trace records nothing

- GIVEN no trace is open
- AND `CONCORDE_DIAGNOSTIC_TIMING_DIR` is not set
- WHEN host code marks a unit of work as a span
- THEN the work runs and returns or raises exactly as unmarked work would
- AND no span is kept
- AND nothing is written to standard error
- AND no file is written

### scenario.checks.timing-standalone-directory — A standalone process writes its trace to a named directory

- GIVEN no trace is open
- AND `CONCORDE_DIAGNOSTIC_TIMING_DIR` names an existing directory
- AND the directory is absolute and canonical
- AND the directory is outside the working directory
- AND the directory is outside any `.concorde/tasks` directory
- AND the directory is outside any `.concorde/history` directory
- AND the directory is outside any `.concorde/unbound` directory
- AND the directory is outside any `.concorde/locks` directory
- WHEN host code marks a unit of work as a span
- THEN a new trace file for that work is created in the directory with mode 0600, without following
  a symbolic link

### scenario.checks.timing-invalid-directory — A refused timing directory receives nothing

- GIVEN no trace is open
- AND `CONCORDE_DIAGNOSTIC_TIMING_DIR` names a directory that is relative, missing, a symbolic link,
  not canonical, the working directory or inside it, or inside a `.concorde/tasks`,
  `.concorde/history`, `.concorde/unbound` or `.concorde/locks` directory
- WHEN host code marks a unit of work as a span
- THEN nothing is written to that directory or to the working directory
- AND one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work returns exactly as unmarked work would

### scenario.checks.timing-sink-failure — A failing sink marks the trace incomplete

- GIVEN a trace whose sink fails when it receives the finished trace
- WHEN the traced work ends
- THEN the trace is counted incomplete
- AND one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work's result is the same as with a working sink
- AND the work's status is the same as with a working sink
- AND the work's error codes are the same as with a working sink
- BUT the sink is not retried

### scenario.checks.timing-trace-cap — A full trace counts what it omits

- GIVEN a trace that already holds 20,000 spans, finished or open
- WHEN more spans are marked
- THEN they are not stored
- AND the trace reports how many were omitted
- AND the trace reports that it is incomplete
- AND when the trace is handed to its sink, spans still open are stored within the cap with status
  `incomplete`
- AND those spans still open are also counted in `omitted`

### scenario.checks.timing-concurrent-traces — Concurrent traces stay separate

- GIVEN several threads or asynchronous tasks each run work under their own trace
- WHEN their spans finish in interleaved order
- THEN every span is stored in the trace that was open where its work started
- AND every span is stored with that trace's identity and parent

### scenario.checks.timing-summary — A timing summary reports covered time per process

- GIVEN span records, some overlapping and some without a duration
- WHEN they are summarized
- THEN the summary reports the covered seconds of each process as the union of that process's
  intervals
- AND the summary reports the summed span seconds separately
- AND spans without a duration make the summary incomplete instead of counting as zero
- BUT no span name appears in the summary
- AND no trace identity appears in the summary
- AND no label appears in the summary
