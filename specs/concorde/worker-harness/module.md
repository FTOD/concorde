# Worker harness

## Purpose

The Worker harness is the [part](../glossary.json#concept.part) of Concorde that runs one headless
[worker](../glossary.json#concept.worker). It runs the worker on Claude Code or on pi under a
[grant](../glossary.json#concept.grant) it is given. The Worker harness performs these actions:

- bounds what the worker may read, write and run
- audits what the worker changed
- resumes the worker with what its caller wants repaired
- records the worker run as a [trace node](../glossary.json#concept.trace-node)

It also keeps the [worker configuration](../glossary.json#concept.worker-configuration). This is
the tracked choice of each worker's settings:

- backend
- model
- reasoning level

The Worker harness reads the user's [model map](../glossary.json#concept.model-map) to reach those
models on one machine.

Whoever launches a worker relies on the Worker harness. In Concorde, these callers are the steps
of [Method](../method/module.md)'s Operations, through the
[standard worker sequence](../glossary.json#concept.standard-worker-sequence). Any program that
can hand over a grant and its instructions may use the Worker harness alone. The Worker harness
decides nothing about the job. It performs none of these actions:

- computing a grant
- reading a [Spec](../glossary.json#concept.spec)
- knowing an [Operation](../glossary.json#concept.operation) catalog
- running a check of its own

It depends on the [kernel](../kernel/module.md) part alone, for one collaboration.
[Workers](workers/module.md#uses-tracing) writes each worker run and each of its rounds as a trace
node through the library of Kernel's [Tracing](../kernel/tracing/module.md). Workers reports its
failures as links of Tracing's [error chain](../glossary.json#concept.error-chain). Workers relies
on the node and error contracts Tracing states.

What the Worker harness enforces guards against a worker's scope drift and mistakes, not against
a malicious agent. It is no complete isolation of the host. The deny rules cover these paths:

- the worktree
- the primary worktree
- the Git administrative paths
- the home

Since Bash needs them to run anything, system directories and every other path outside those
paths stay readable to every tool. On Claude Code, another process may create a Git-ignored file
in the worktree while the run lasts. The worker may read that file without anything failing.
Writes to Git-ignored paths are not audited. The [Harness's known limits](harness/module.md#known-limits-of-v1)
and [Workers](workers/module.md#why-the-run-is-built-this-way) state these boundaries exactly.

## Core concepts

The part has two children, and their terms carry it. The [Harness](harness/module.md) derives a
worker's [agent harness](../glossary.json#concept.agent-harness). On Claude Code, this is the
worker's [worker settings](../glossary.json#concept.worker-settings) with their
[deny rules](../glossary.json#concept.deny-rules) and [write hook](../glossary.json#concept.write-hook).
On pi, this is the worker's [permission extension](../glossary.json#concept.permission-extension).
[Workers](workers/module.md) launches the worker under that agent harness. Workers performs these
other actions:

- keeps the [run directory](../glossary.json#concept.run-directory)
- runs the [write audit](../glossary.json#concept.write-audit) and the
  [resume rounds](../glossary.json#concept.resume-round)
- writes the [run record](../glossary.json#concept.run-record)

What a launch is given is the one idea this entry adds.

### What a launch is given

A caller hands the worker harness everything a launch needs as data. The caller receives the run
record back. The caller supplies these inputs:

- **the grant**, in the worker harness's own input format, exactly as the
  [grant input contract](workers/contracts.md#grant-input) defines. The grant gives the paths the
  worker may write (`rw`), read (`ro`) and only know by name (`names`). It includes the
  [context identity](../glossary.json#concept.context-identity) that identifies them, and the
  [task type](../glossary.json#concept.task-type) it was computed for. In Concorde, Method computes
  the grant through the Spec tooling. Method projects these fields into this format:
  - `task_type`
  - `entries`
  - `context_identity`

  Method keeps the grant's [Modules](../glossary.json#concept.module) and glossary terms for its
  own instructions and validation. Those three fields have the same shape on both sides. A
  contract test keeps them so.
- **the task instructions**: the caller's prompt for the job. The worker harness appends the
  grant's lists and the rules of its boundary to make the [brief](../glossary.json#concept.brief).
- **who the worker is**: the Operation's name and the [worker id](../glossary.json#concept.worker-id)
  as labels, recorded with the run. The caller also supplies the settings the configuration reader
  resolved for them beforehand (see [A launch from start to end](#a-launch-from-start-to-end)).
  These settings are:
  - backend
  - model
  - reasoning level
  - limits

  The task type also selects the worker's tool set.
- **where it works**: the worktree and accompanying paths. The worktree must lie directly in
  `.claude/worktrees/` of its repository's primary worktree ([Placement](workers/launch.md#placement)).
  The caller supplies these paths:
  - the worktree
  - the runtime paths the worker may read beside the grant
  - the trace node folder in which its run directory is made

  With no `rw` path, a grant makes a worker that changes nothing.
- **the round validation**, optionally: a callback. After each round that ended with a valid `ok`
  [worker result](../glossary.json#concept.worker-result) and a clean audit, the worker harness
  calls the callback. Without a callback, such a round ends the run `ok`. The callback returns
  one of these answers:
  - the evidence to keep with the round, such as
    [check results](../glossary.json#concept.check-result), and what to repair
  - a violation that ends the run at once
  - that it could not validate, which fails the run

  While there is something to repair and rounds remain, the worker harness resumes the same
  worker session with what needs repair. The caller chooses the outcome of a repair still left
  after the last round. That repair either fails the run or leaves its result for the caller to
  judge ([Round validation](workers/launch.md#round-validation)).

Everything that depends on the Specs or on the job stays with the caller. These decisions are:

- which paths
- which instructions
- which checks
- what counts as done

Everything that depends on the agent program stays here. These responsibilities are:

- settings
- sandbox
- launch
- audit
- resume
- record

<a id="the-caller-isolates-the-worktree"></a>

**The caller isolates the worktree.** The [write audit](../glossary.json#concept.write-audit)
compares the worktree with a snapshot taken before the first round. The write audit attributes
every change since then to the worker. From before the launch until the run ends, the caller
guarantees that nothing else writes the worktree's files or its Git state. This interval includes
its round validations and the host's deletions. The Git state includes these items:

- `HEAD`
- index
- branch

Other processes may read the worktree meanwhile. The worker harness takes no lock for this. It
cannot tell another writer's change from the worker's. A change by another writer outside `rw`
fails the run as a violation. A change by another writer inside `rw` is recorded as the worker's.
In Concorde, Execution's runner holds the [workspace lock](../glossary.json#concept.workspace-lock)
for the whole run that launches the worker. An [unbound run](../glossary.json#concept.unbound-run)'s
worker works in a checkout no one else writes. A program that uses the worker harness alone must
give the same guarantee its own way.

### A launch from start to end

A caller that uses the worker harness alone, without Method, goes through two stages:

1. **Prepare and resolve.** With the worker's program installed, the caller prepares these inputs:
   - a worktree in its primary worktree's `.claude/worktrees/`
   - a committed worker configuration `.concorde/workers.json`
   - the user's model map

   The caller declares the Operations and worker ids it may launch. It asks the
   [configuration reader](workers/module.md#choosing-worker-models) for these worker settings:
   - backend
   - model
   - reasoning level
   - limits

   Optionally, the caller checks every worker of its job against the model map at once. A refusal
   here comes before any worker run exists. Such refusals include these codes:
   - `config_invalid`
   - `model_unmapped`
   - `backend_missing`

   No run directory or record is made. The caller turns the refusal into its own error link
   ([Refusals before a run](workers/launch.md#refusals-before-a-run)).
2. **Launch and read the record.** The caller hands the host the resolved inputs with these inputs:
   - the grant
   - the instructions
   - the worktree
   - the parent trace node folder
   - optionally, its round validation

   Once the run ends, the caller gets back the
   [returned run record](workers/contracts.md#contract.workers.worker-run-record). The record has
   one of these statuses:
   - `ok`
   - `blocked`
   - `failed`

   The record keeps the worker's own [worker result](../glossary.json#concept.worker-result)
   verbatim, as a claim, apart from the host's evidence. The host's evidence consists of these
   items:
   - each round's audit
   - the round validation's evidence
   - the rounds used
   - the transcript

   After the last round's validation, the host makes the deletions a worker proposes. That
   validation's evidence therefore describes the worktree before those deletions
   ([Proposed deletions](workers/launch.md#proposed-deletions)). When a run does not end `ok`, it
   carries Workers' error link with its causes.

### When a launch fails

Each child's failure becomes something the caller sees in one of three ways. Workers'
[Errors](workers/launch.md#errors) gives the exact codes. The caller sees these outcomes:

- **Before any run**: the configuration reader's refusals above, and nothing else.
- **In the run record**, `failed` with Workers' error link. This outcome covers these failures:
  - a run that could not start its worker
  - a round that timed out or reached its turn or budget limit, or ended with an invalid worker result
  - an [audit](workers/launch.md#audit) violation
  - a round validation that answers a violation, that cannot validate, or whose repair still stands
    when the rounds are used up and it says so
  - a proposed deletion that failed
  - an interruption from outside, which ends every worker process before it is reported

  A run cannot start its worker for these reasons:
  - a missing grant, which Workers refuses
  - a malformed grant, which the Harness refuses to generate settings from
  - a misplaced worktree
  - a runtime directory the deny rules would cover
  - a snapshot or a launch that failed
  - a backend program or runtime that is missing or fails
- **In the run record, with the worker's own status**: a worker that ended `blocked` or `failed`.
  The worker's link becomes the cause of Workers' own.

Only a clean `ok` round goes on to the round validation and may be resumed. Every other outcome
ends the run at once ([Rounds](workers/launch.md#rounds)). An audit violation is never retried.
Whatever the outcome, the host never reverts or commits what a worker wrote. What the run leaves
in the worktree is the caller's to keep or discard. The grant stays frozen for the whole run.
Before its validation, every round is audited ([Requirements](workers/launch.md#requirements)).

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

The worker harness and the Spec tooling change for different reasons and are useful apart. The
grant follows the Protocol. These aspects follow Claude Code and pi:

- settings
- sandboxes
- backends

If the worker harness computed the grant, it could not be installed without the Spec tooling.
Under that condition, a program that bounds workers by some other rule could not use it at all.
Taking the grant as data in its own format keeps the worker harness to what it enforces. A
contract test keeps these shared fields the same shape as Spec core's grant:

- `task_type`
- `entries`
- `context_identity`

This keeps Concorde's own path exact.

### Why the round validation is a callback

Whether a round needs repair is the job's question, not the worker's. An `implement` step asks
whether the project's checks pass on the changed code. A Spec-writing step asks whether the Specs
still validate. Both ask whether the worker changed glossary entries its Modules do not own. Such
a change is no repair but a violation that ends the run, as
[Method's round validation](../method/workers.md#the-round-validation) answers. Running those
checks here would tie the worker harness to Check execution and to the Specs. A callback keeps
the resume loop here, where the worker session lives. The callback keeps the judgement with the
caller, which returns both what it found and what the worker must repair. A resume round still
feeds the worker only what the round validation found. The worker harness's own stopping rule
depends only on outcomes. These outcomes are never resumed:

- a `blocked` or `failed` worker result
- an invalid result
- an audit violation

A clean `ok` round goes on as its round validation answers. What a
[Spec gap](../glossary.json#concept.spec-gap) or a path outside the grant means is the caller's to
say, in its instructions and its validation. In Concorde, workers handle both in these ways:

- An `understand` worker reports a gap and ends `ok`.
- A review worker reports a gap as a finding and goes on.
- A `code-to-spec` worker describes the code it reads and reports doubtful intent without promising
  it ([The brief](workers/module.md#the-brief)).
- Every other worker ends `blocked`, which no round resumes.

Method's round validation never asks a worker to repair a gap.

### Guidance

<a id="realization.worker-harness.guidance"></a>

The **Worker harness guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). The sections are kept in
`prompts/guidance/worker_harness/` and registered under `guidance` in the part's registration.
Wherever the part is installed,
[Distribution](../distribution/module.md#guidance-composition) composes these sections after
Coordination's working method. The sections are the project skill's "Worker models" and the
`CLAUDE.md` block's sentence on the worker configuration and the model map. "Worker models"
explains the worker configuration and the model map. Where a part a section mentions is not
installed, the section says what happens.

<a id="uses-distribution"></a>

**Distribution**, the installation host present in every installation, installs the part from its
[part registration](../glossary.json#concept.part-registration). Workers keeps this plain data,
which the [registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines. The registration specifies these items:

- the module that registers the worker run's trace types
- the guidance sections
- `scripts/available_models.py`
- the pi runtime

The worker harness relies on Distribution placing those and composing its guidance
([req.distribution.composed-guidance](../distribution/requirements.md#req.distribution.composed-guidance)).
The worker harness imports nothing of Distribution.

### The children

<a id="contains-harness"></a>

**Harness** turns one grant into the agent program's own configuration. On Claude Code, it
produces the worker settings with these components:

- deny rules
- the write hook
- the Bash sandbox

On pi, it produces the permission extension with the same sandbox engine. Harness also produces
the tool set of each task type. Before generating anything, Harness refuses a malformed grant
with `grant_malformed`. Workers reports that refusal as a run that failed before its worker
started. Harness does not perform these actions, which Workers performs:

- launch
- audit
- record

Harness serves only workers. A [task session](../glossary.json#concept.task-session)'s boundary is
Coordination's own.

<a id="contains-workers"></a>

**Workers** runs the launch. It performs these actions:

- resolves the worker's backend and model from the worker configuration and the model map
- prepares the [runtime directory](../glossary.json#concept.runtime-directory) and the brief
- launches and resumes the worker
- audits every round against the grant's `rw` list
- calls the caller's round validation
- writes the run record in the run directory it makes inside the trace node folder it was given

Workers keeps the grant frozen for the whole run
([req.workers.frozen-grant](workers/launch.md#req.workers.frozen-grant)). Only after a clean `ok`
round, Workers calls the round validation
([req.workers.validation-after-clean-round](workers/launch.md#req.workers.validation-after-clean-round)).
Workers never retries a violation
([req.workers.violation-ends-run](workers/launch.md#req.workers.violation-ends-run)). Workers
reports every failure as a link of the [error chain](../glossary.json#concept.error-chain)
([req.workers.error-chain](workers/launch.md#req.workers.error-chain)). Every run leaves a final
record ([req.workers.always-recorded](workers/launch.md#req.workers.always-recorded)), with the
outcomes [When a launch fails](#when-a-launch-fails) lists.
