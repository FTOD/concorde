# Worker harness

## Purpose

The Worker harness is the [part](../glossary.json#concept.part) of Concorde that runs one headless
[worker](../glossary.json#concept.worker) on Claude Code or on pi under a
[grant](../glossary.json#concept.grant) it is given, bounds what the worker may read, write and run,
audits what it changed, resumes it with what its caller wants repaired, and records the worker run
as a [trace node](../glossary.json#concept.trace-node). It also keeps the
[worker configuration](../glossary.json#concept.worker-configuration), the tracked choice of each
worker's backend, model and reasoning level, and reads the user's
[model map](../glossary.json#concept.model-map) to reach those models on one machine.

Whoever launches a worker relies on it: in Concorde, the steps of [Method](../method/module.md)'s
Operations, through the
[standard worker sequence](../glossary.json#concept.standard-worker-sequence); but any program that
can hand over a grant and its instructions may use it alone. It decides nothing about the job: it
computes no grant, reads no [Spec](../glossary.json#concept.spec), knows no
[Operation](../glossary.json#concept.operation) catalog and runs no check of its own. It depends on
the [kernel](../kernel/module.md) part alone.

What it enforces guards against a worker's scope drift and mistakes, not against a malicious agent,
and it is no complete isolation of the host. The deny rules cover the worktree, the primary
worktree, the Git administrative paths and the home; system directories and every other path outside
them stay readable to every tool, since Bash needs them to run anything; on Claude Code a Git-ignored file another process
creates in the worktree while the run lasts may be read without anything failing; and writes to
Git-ignored paths are not audited. The [Harness's known limits](harness/module.md#known-limits-of-v1)
and [Workers](workers/module.md#why-the-run-is-built-this-way) state these boundaries exactly.

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
  [context identity](../glossary.json#concept.context-identity) that identifies them, and the
  [task type](../glossary.json#concept.task-type) it was computed for, exactly as the
  [grant input contract](workers/contracts.md#grant-input) defines. In Concorde, Method computes the
  grant through the Spec tooling and projects its `task_type`, `entries` and `context_identity`
  into this format, keeping the grant's Modules and glossary terms for its own instructions and
  validation; those three fields have the same shape on both sides, which a contract test keeps so;
- **the task instructions**: the caller's prompt for the job, to which the worker harness appends the
  grant's lists and the rules of its boundary to make the [brief](../glossary.json#concept.brief);
- **who the worker is**: the Operation's name and the [worker id](../glossary.json#concept.worker-id)
  as labels, recorded with the run, and the backend, model, reasoning level and limits the
  configuration reader resolved for them beforehand (see [A launch from start to end](#a-launch-from-start-to-end));
  the task type also selects the worker's tool set;
- **where it works**: the worktree, which must lie directly in `.claude/worktrees/` of its
  repository's primary worktree ([Placement](workers/launch.md#placement)), the runtime paths it may
  read beside the grant, and the trace node folder in which its run directory is made; a grant
  with no `rw` path makes a worker that changes nothing;
- **the round validation**: a callback the worker harness calls after each round that ended with a
  valid `ok` [worker result](../glossary.json#concept.worker-result) and a clean audit. It returns
  the evidence to keep with the round, such as [check results](../glossary.json#concept.check-result),
  and what to repair, or a violation that ends the run at once; while there is something to repair
  and rounds remain, the worker harness resumes the same worker session with it
  ([Round validation](workers/launch.md#round-validation)).

So everything that depends on the Specs or on the job — which paths, which instructions, which
checks and what counts as done — stays with the caller, and everything that depends on the agent
program — settings, sandbox, launch, audit, resume and record — stays here.

<a id="the-caller-isolates-the-worktree"></a>

**The caller isolates the worktree.** The [write audit](../glossary.json#concept.write-audit)
compares the worktree with a snapshot taken before the first round and attributes every change
since then to the worker. So the caller guarantees that nothing else writes the worktree's files or
its Git state, `HEAD`, index and branch, from before the launch until the run has ended, its round
validations and the host's deletions included; other processes may read it meanwhile. The worker
harness takes no lock for this and cannot tell another writer's change from the worker's: a change
by another writer outside `rw` fails the run as a violation, and one inside `rw` is recorded as the
worker's. In Concorde, Execution's runner holds the
[workspace lock](../glossary.json#concept.workspace-lock) for the whole run that launches the
worker, and an [unbound run](../glossary.json#concept.unbound-run)'s worker works in a checkout no one else writes; a program that uses the
worker harness alone must give the same guarantee its own way.

### A launch from start to end

A caller that uses the worker harness alone, without Method, goes through two stages:

1. **Prepare and resolve.** It prepares a worktree in its primary worktree's `.claude/worktrees/`,
   a committed worker configuration `.concorde/workers.json` and the user's model map, with the
   worker's program installed. It declares the Operations and worker ids it may launch and asks the
   [configuration reader](workers/module.md#choosing-worker-models) for the worker's backend, model,
   reasoning level and limits, optionally checking every worker of its job against the model map at
   once. A refusal here, such as `config_invalid`, `model_unmapped` or `backend_missing`, comes
   before any worker run exists: no run directory or record is made, and the caller turns it into
   its own error link ([Refusals before a run](workers/launch.md#refusals-before-a-run)).
2. **Launch and read the record.** It hands the host the resolved inputs with the grant, the
   instructions, the worktree, the parent trace node folder and, optionally, its round validation,
   and gets back the [returned run record](workers/contracts.md#contract.workers.worker-run-record)
   once the run has ended. The record's status is `ok`, `blocked` or `failed`; it keeps the
   worker's own [worker result](../glossary.json#concept.worker-result) verbatim, as a claim, apart
   from the host's evidence: each round's audit, the round validation's evidence, the rounds used,
   the transcript. The deletions a worker proposes are made by the host after the last round's
   validation, so that validation's evidence describes the worktree before them
   ([Proposed deletions](workers/launch.md#proposed-deletions)). A run that does not end `ok`
   carries Workers' error link with its causes.

### When a launch fails

Each child's failure becomes something the caller sees in one of three ways; the exact codes are
Workers' [Errors](workers/launch.md#errors):

- **Before any run**: the configuration reader's refusals above, and nothing else.
- **In the run record**, `failed` with Workers' error link: a run that could not start its worker —
  a missing grant, which Workers refuses, a malformed one, which the Harness refuses to generate
  settings from, a misplaced worktree, a runtime directory the deny rules would cover, a snapshot or
  a launch that failed, a backend program or runtime that is missing or fails; a round that timed out
  or reached its turn or budget limit, or ended with an invalid worker result; an
  [audit](workers/launch.md#audit) violation; a round validation that answers a violation, that
  cannot validate, or whose repair still stands when the rounds are used up and it says so; a
  proposed deletion that failed; and an interruption from outside, which ends every worker process
  before it is reported.
- **In the run record, with the worker's own status**: a worker that ended `blocked` or `failed`,
  whose link becomes the cause of Workers' own.

Only a clean `ok` round goes on to the round validation and may be resumed; every other outcome ends
the run at once ([Rounds](workers/launch.md#rounds)), and an audit violation is never retried. The
host never reverts or commits what a worker wrote, whatever the outcome: what the run leaves in the
worktree is the caller's to keep or discard. The grant stays frozen for the whole run, and every
round is audited before its validation ([Requirements](workers/launch.md#requirements)).

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
wh.workers -> caller: "returned run record"
```

## How it is built

### Why the grant arrives as data

The worker harness and the Spec tooling change for different reasons and are useful apart: the
grant follows the Protocol, while settings, sandboxes and backends follow Claude Code and pi. If the
worker harness computed the grant, it could not be installed without the Spec tooling, and a program
that bounds workers by some other rule could not use it at all. Taking the grant as data in its own
format keeps the worker harness to what it enforces, while a contract test keeps the shared fields,
`task_type`, `entries` and `context_identity`, the same shape as Spec core's grant, so that
Concorde's own path stays exact.

### Why the round validation is a callback

Whether a round needs repair is the job's question, not the worker's: an `implement` step asks
whether the project's checks pass on the changed code, a Spec-writing step whether the Specs still
validate, and both whether the worker changed glossary entries its Modules do not own, which is no
repair but a violation that ends the run, as
[Method's round validation](../method/workers.md#the-round-validation) answers. Running those checks
here would tie the worker harness to Check execution and to the Specs. A callback keeps the
resume loop here, where the worker session lives, and the judgement with the caller, which
returns both what it found and what the worker must repair. A resume round still feeds the worker
only what the round validation found. The worker harness's own stopping rule depends only on
outcomes: a `blocked` or `failed` worker result, an invalid result and an audit violation are never
resumed, and a clean `ok` round goes on as its round validation answers. What a
[Spec gap](../glossary.json#concept.spec-gap) or a path outside the grant means is the caller's to
say, in its instructions and its validation: in Concorde an `understand` worker reports a gap and
ends `ok`, a review worker reports one as a finding and goes on, a `code-to-spec` worker describes
the code it reads and reports doubtful intent without promising it
([The brief](workers/module.md#the-brief)), and every other worker ends `blocked`, which no round
resumes; Method's round validation never asks a worker to repair a gap.

### Guidance

<a id="realization.worker-harness.guidance"></a>

The **Worker harness guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance), kept in
`prompts/guidance/worker_harness/` and registered under `guidance` in the part's registration, which
[Distribution](../distribution/module.md#guidance-composition) composes after Coordination's working
method wherever the part is installed: the project skill's "Worker models", which explains the
worker configuration and the model map, and the `CLAUDE.md` block's sentence on them. Each section
says what happens where a part it mentions is not installed.

<a id="uses-distribution"></a>

**Distribution**, the installation host present in every installation, installs the part from its
[part registration](../glossary.json#concept.part-registration), the plain data its
[registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines and Workers keeps: the module that registers the worker run's trace types, the guidance
sections, `scripts/available_models.py` and the pi runtime. The worker harness relies on
Distribution placing those and composing its guidance
([req.distribution.composed-guidance](../distribution/requirements.md#req.distribution.composed-guidance)),
and imports nothing of it.

### The children

<a id="contains-harness"></a>

**Harness** turns one grant into the agent program's own configuration: on Claude Code the worker
settings, with deny rules, the write hook and the Bash sandbox; on pi the permission extension with
the same sandbox engine; and the tool set of each task type. It refuses a malformed grant with
`grant_malformed` before generating anything, which Workers reports as a run that failed before
its worker started. It does not launch, audit or record, which Workers does, and it serves only workers: a [task session](../glossary.json#concept.task-session)'s boundary is Coordination's own.

<a id="contains-workers"></a>

**Workers** runs the launch: it resolves the worker's backend and model from the worker
configuration and the model map, prepares the [runtime directory](../glossary.json#concept.runtime-directory) and the brief, launches and resumes
the worker, audits every round against the grant's `rw` list, calls the caller's round validation,
and writes the run record in the run directory it makes inside the trace node folder it was given.
It keeps the grant frozen for the whole run
([req.workers.frozen-grant](workers/launch.md#req.workers.frozen-grant)), calls the round
validation only after a clean `ok` round
([req.workers.validation-after-clean-round](workers/launch.md#req.workers.validation-after-clean-round)),
never retries a violation ([req.workers.violation-ends-run](workers/launch.md#req.workers.violation-ends-run))
and reports every failure as a link of the [error chain](../glossary.json#concept.error-chain)
([req.workers.error-chain](workers/launch.md#req.workers.error-chain)); every run leaves a final
record ([req.workers.always-recorded](workers/launch.md#req.workers.always-recorded)), with the
outcomes [When a launch fails](#when-a-launch-fails) lists.
