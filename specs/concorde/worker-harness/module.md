# Worker harness

## Purpose

The Worker harness is the worker harness [part](../glossary.json#concept.part): it runs one headless
[worker](../glossary.json#concept.worker) on Claude Code or on pi under a
[grant](../glossary.json#concept.grant) it is given, bounds what the worker may read, write and run,
audits what it changed, resumes it with what its caller wants repaired, and records the worker run
as a [trace node](../glossary.json#concept.trace-node). It also keeps the
[worker configuration](../glossary.json#concept.worker-configuration), the tracked choice of each
worker's backend, model and reasoning level, and reads the user's
[model map](../glossary.json#concept.model-map) to reach those models on one machine.

Whoever launches a worker relies on it: in Concorde, the steps of Method's Operations, through the
[standard worker sequence](../glossary.json#concept.standard-worker-sequence); but any program that
can hand over a grant and its instructions may use it alone. It decides nothing about the job: it
computes no grant, reads no [Spec](../glossary.json#concept.spec), knows no
[Operation](../glossary.json#concept.operation) catalog and runs no check of its own. It depends on
the kernel part alone.

## Core concepts

The part has two children, and their terms carry it: the [Harness](harness/module.md) derives a
worker's [agent harness](../glossary.json#concept.agent-harness) — its
[worker settings](../glossary.json#concept.worker-settings) with their
[deny rules](../glossary.json#concept.deny-rules) and [write hook](../glossary.json#concept.write-hook)
on Claude Code, its [permission extension](../glossary.json#concept.permission-extension) on pi —
and [Workers](workers/module.md) launches the worker under it, keeps its
[run directory](../glossary.json#concept.run-directory), runs the
[write audit](../glossary.json#concept.write-audit) and the
[resume rounds](../glossary.json#concept.resume-round), and writes the
[run record](../glossary.json#concept.run-record). What a launch is given is the one idea this entry
adds.

### What a launch is given

A caller hands the worker harness everything a launch needs as data, and receives the run record
back:

- **the grant**, in the worker harness's own input format: the paths the worker may write (`rw`),
  read (`ro`) and only know by name (`names`), with the
  [context identity](../glossary.json#concept.context-identity) that identifies them. In Concorde,
  Method computes it through the Spec tooling and converts it into this format; the two formats are
  the same shape, which a contract test keeps so;
- **the task instructions**: the caller's prompt for the job, to which the worker harness appends the
  grant's lists and the rules of its boundary to make the [brief](../glossary.json#concept.brief);
- **who the worker is**: the Operation's name and the [worker id](../glossary.json#concept.worker-id)
  as labels, which select its entry of the worker configuration, and the [task type](../glossary.json#concept.task-type), which selects its
  tool set;
- **where it works**: the worktree, whether the worker may write there at all, the runtime paths it
  may read beside the grant, and the trace node folder in which its run directory is made;
- **the round validation**: a callback the worker harness calls after each round that ended with a
  valid `ok` [worker result](../glossary.json#concept.worker-result) and a clean audit. It returns
  the evidence to keep with the round, such as [check results](../glossary.json#concept.check-result),
  and what to repair; while there is something to repair and rounds remain, the worker harness resumes
  the same worker session with it.

So everything that depends on the Specs or on the job — which paths, which instructions, which
checks and what counts as done — stays with the caller, and everything that depends on the agent
program — settings, sandbox, launch, audit, resume and record — stays here.

## Overview

```d2 illustrative
direction: right
caller: "Caller\n(in Concorde, a Method step)" {
  grant: "Grant as data"
  instructions: "Task instructions"
  validation: "Round validation"
}
wh: Worker harness {
  harness: "Harness:\nsettings or permission\nextension, tool set"
  workers: "Workers:\nbrief, launch, audit,\nresume, record"
  workers -> harness: "asks for the\nworker's harness"
}
program: "Worker\nclaude -p or pi -p"
record: "Run record\n(trace node)"
caller.grant -> wh.workers
caller.instructions -> wh.workers
wh.workers -> program: launches, resumes
wh.workers -> caller.validation: "after each clean round"
caller.validation -> wh.workers: "evidence, what to repair"
wh.workers -> record: writes
record -> caller: "returned"
```

## How it is built

### Why the grant arrives as data

The worker harness and the Spec tooling change for different reasons and are useful apart: the
grant follows the Protocol, while settings, sandboxes and backends follow Claude Code and pi. If the
worker harness computed the grant, it could not be installed without the Spec tooling, and a program
that bounds workers by some other rule could not use it at all. Taking the grant as data in its own
format keeps the worker harness to what it enforces, while the format's equality with Spec core's
grant, checked by a contract test, keeps Concorde's own path exact.

### Why the round validation is a callback

Whether a round needs repair is the job's question, not the worker's: an `implement` step asks
whether the project's checks pass on the changed code, a Spec-writing step whether the Specs still
validate, and both whether the worker changed glossary entries its Modules do not own. Running those
checks here would tie the worker harness to Check execution and to the Specs. A callback keeps the
resume loop here, where the worker session lives, and the judgement with the caller, which
returns both what it found and what the worker must repair. A resume round still feeds the worker
only what a program found; a [Spec gap](../glossary.json#concept.spec-gap) or a path outside the
grant is never repaired by another round, because the caller's validation never asks for it and
the worker harness stops when the worker reports one.

### The children

<a id="contains-harness"></a>

**Harness** turns one grant into the agent program's own configuration: on Claude Code the worker
settings, with deny rules, the write hook and the Bash sandbox; on pi the permission extension with
the same sandbox engine; and the tool set of each task type. It does not launch, audit or record,
which Workers does, and it serves only workers: a [task session](../glossary.json#concept.task-session)'s boundary is Coordination's own.

<a id="contains-workers"></a>

**Workers** runs the launch: it resolves the worker's backend and model from the worker
configuration and the model map, prepares the [runtime directory](../glossary.json#concept.runtime-directory) and the brief, launches and resumes
the worker, audits every round against the grant's `rw` list, calls the caller's round validation,
and writes the run record in the run directory it makes inside the trace node folder it was given.
