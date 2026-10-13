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

A count must meet all of these conditions:

- be a finite number
- be below 10^18
- be nonnegative, except for `returncode`

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
| `interval_record(*, name, trace_id, started_at, start_ns, end_ns, parent_id=None, layer="C", status="ok", process_id=None)` | adapt an interval measured elsewhere to the span shape ([Adapting an interval](#adapting-an-interval)) |
| `summarize(spans)` | the timing summary of finished span records |

The timing summary is `{complete, summed_span_seconds, covered_seconds_by_process}`: what the
spans measured, and nothing they cannot, such as elapsed wall time. When spans are given but none of
them has a duration, `summed_span_seconds` is null.

The directory conditions keep diagnostic files apart from the project and from Concorde's
lifecycle records and locks. Concorde keeps those records and locks under these paths:

- `.concorde/tasks`
- `.concorde/history`
- `.concorde/unbound`
- `.concorde/locks`

When called while no trace is open but `CONCORDE_DIAGNOSTIC_TIMING_DIR` is set, a function marked
with `timed` opens a trace of its own. The trace's sink is `diagnostic_sink` of that directory.
When the directory is refused, the trace has no sink. The `CONCORDE_TIMING_INCOMPLETE` line is
written instead. A `Span` used directly while no trace is open opens no trace, even when
`CONCORDE_DIAGNOSTIC_TIMING_DIR` is set. It records nothing.

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

## Adapting an interval

`interval_record` turns an interval that another runner measured into one span record. It takes
keyword arguments only. It opens no trace and needs none. Its arguments are these:

| Argument | Content |
| --- | --- |
| `name` | the span name |
| `trace_id` | the identity of the trace the record belongs to |
| `parent_id` | the enclosing span's `span_id`, or None |
| `layer` | the record's layer, `C` unless the caller says otherwise |
| `started_at` | the RFC 3339 UTC wall time of the start, for correlation only |
| `start_ns` | the start, in monotonic nanoseconds of the measuring process |
| `end_ns` | the end, in the same clock, or None when the work did not finish |
| `status` | `ok`, `error`, `cancelled` or `incomplete` |
| `process_id` | the measuring process, or None for the calling process |

`start_ns` and `end_ns` come from the monotonic clock of the process that `process_id` names. A
summary unions the intervals of each process apart
([req.checks.timing-per-process](#req.checks.timing-per-process)).
So a caller that adapts an interval another process measured names that process.

The record has a new `span_id` and `duration_ns` `end_ns - start_ns`. When `end_ns` is None,
`duration_ns` is null, which the caller marks with the status `incomplete`. `session_id`, `task_id`
and `metadata` are empty. A status a span cannot have, or an `end_ns` before `start_ns`, raises
`ValueError`. Nothing else is checked.

A test runner measured one test in its worker process 4242 and adapts it below its run's total
span:

```python
unit = interval_record(
    name="test.unit",
    trace_id=run_id,
    parent_id=total["span_id"],
    started_at="2026-10-13T09:00:00+00:00",
    start_ns=5_000_000_000,
    end_ns=7_500_000_000,
    process_id=4242,
)
# unit["duration_ns"] == 2_500_000_000, unit["layer"] == "C", unit["process_id"] == 4242
summary = summarize([total, unit])  # covers 2.5 seconds for process 4242
```

## Requirements

### req.checks.timing-passive — Recording never changes the work

Recording, persisting or failing to persist a diagnostic span SHALL NOT change the outcome, the
retry behaviour or the authority of the work it describes.

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

A count, duration or context figure that the observed work did not report SHALL be recorded and
summarized as null, never as zero.

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
- WHEN host code calls a function decorated with `timed`
- THEN a new trace file for that work is created in the directory with mode 0600, without following
  a symbolic link

### scenario.checks.timing-invalid-directory — A refused timing directory receives nothing

- GIVEN no trace is open
- AND `CONCORDE_DIAGNOSTIC_TIMING_DIR` names a directory that is relative, missing, a symbolic link,
  not canonical, the working directory or inside it, or inside a `.concorde/tasks`,
  `.concorde/history`, `.concorde/unbound` or `.concorde/locks` directory
- WHEN host code calls a function decorated with `timed`
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

### scenario.checks.timing-interval — An interval measured elsewhere becomes a span record

- GIVEN an interval that a process measured with its monotonic clock, from a start to an end
- WHEN a caller adapts it with `interval_record`, naming that process
- THEN the record has the span shape with layer `C`, that process and the interval's duration
- AND an interval without an end has a null duration
- BUT an end before the start, or a status a span cannot have, raises `ValueError`

### scenario.checks.timing-summary — A timing summary reports covered time per process

- GIVEN span records, some overlapping and some without a duration
- WHEN they are summarized
- THEN the summary reports the covered seconds of each process as the union of that process's
  intervals
- AND the summary reports the summed span seconds separately
- AND spans without a duration make the summary incomplete instead of counting as zero
- AND when no span has a duration, the summed span seconds are null
- BUT no span name appears in the summary
- AND no trace identity appears in the summary
- AND no label appears in the summary
