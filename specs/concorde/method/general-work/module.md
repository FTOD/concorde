# General work

## Purpose

General work lets a caller hand one free-form, bounded piece of AI work to a worker. The work
still gets the isolation, the [grant](../../glossary.json#concept.grant) and the record of every
other [Operation](../../glossary.json#concept.operation). It provides one Operation, `general`.
In `general`, the caller writes an instruction in its own words. The caller also names the
[task type](../../glossary.json#concept.task-type) whose grant bounds the work. Two workers then
run, one after the other:

- The **worker** does what the instruction asks, within the grant.
- The **reviewer**, an independent second worker, judges the result against the instruction.

The caller uses `general` for work that no other Operation fits. Examples are these:

- Rewrite one document in a new style and keep its meaning.
- Rename a term across the bound [Modules](../../glossary.json#concept.module)'
  [Specs](../../glossary.json#concept.spec).
- Answer a question that needs the code as well as the Specs.

Without this Operation, a caller would start an agent program, such as pi or Claude Code, itself.
Such a program takes the caller's own configuration. That configuration can load the caller's
packages, tools and project instructions, and nothing bounds its writes. `general` runs both
workers through the [worker harness](../../worker-harness/module.md), as every Operation of
[Method](../module.md) does. Each worker therefore gets only its grant, Concorde's own tools and the
model the [worker configuration](../../glossary.json#concept.worker-configuration) chooses.

General work never decides what the instruction should be. The reviewer reports its findings and
never fixes anything. The caller decides what to do with them. General work never runs a
[configured check](../../glossary.json#concept.configured-check) and never validates the Specs.
The caller validates the result, with `spec-validation` or `task-validation`, as for work it does
itself.

## Core concepts

### The instruction

The **instruction** is the caller's text that says what the worker does. The caller gives it on the
command line or in a file. The Operation keeps an exact copy of it as `instruction.md` in the run's
[trace node](../../glossary.json#concept.trace-node) and records its digest. The instruction goes
into the worker's [brief](../../glossary.json#concept.brief) as [task
context](../../glossary.json#concept.task-context), after this Module's fixed worker prompt. It
never replaces Concorde's own instructions to the worker, and it widens no grant. A sentence in the
instruction that asks for more than the grant allows is refused like any other write outside the
grant.

### The grant of a run

The caller names one of the eight task types with `--type`. The Operation computes that type's
grant for the run's Modules through Method's
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence). The run's
Modules are `--modules`, otherwise the binding's. The type decides what the worker may read and
write, exactly as for the Operation that normally uses that type. For example:

- `--type specify` lets the worker change the bound Modules' Spec documents.
- `--type implement` lets the worker change their code.
- `--type understand` lets the worker read their Specs and only the names of their code files.
- `--type review-code` lets the worker read their Specs and the whole project's code.

With `--read-only`, the Operation lowers every writable level of the grant to read. The worker
then changes nothing, whatever the type. A type that writes needs a bound
[workspace](../../glossary.json#concept.workspace). Without `--read-only`, an
[unbound run](../../glossary.json#concept.unbound-run) of such a type fails before any worker
launches.

### The observed change

The Operation observes the change itself, outside the worker. It records the worktree as a Git
tree before the worker launches and again after the worker ends. The difference between the two
trees is the **observed change**:

- The files the worker added, modified or deleted.
- A unified diff of the change, kept as `change.diff` in the run's trace node.
- The earlier content of every modified or deleted file, kept under `before/` in that node.

Files Git ignores are not observed, as in the
[write audit](../../glossary.json#concept.write-audit). The observed change is host evidence. The
worker's own account of what it did is its claim.

### The review

The reviewer is a second worker, [worker id](../../glossary.json#concept.worker-id) `reviewer`. It
shares no session and no transcript with the worker. It runs under the same task type's grant with
every writable level lowered to read. It therefore reads what the worker could read and changes
nothing. Its brief gives it this task context:

- The instruction.
- The observed change: the diff, and the earlier content of each changed file to read.
- The worker's answer, marked as a claim to check and never as a fact.

The reviewer judges whether the result does what the instruction asks. For a rewrite that must
keep its meaning, it judges whether the new text says what the old text said. It reports every
problem it can establish in one pass, as **findings**. Each finding names its kind:

- `instruction`: the result does not do what the instruction asks, or does only part of it.
- `meaning`: the change alters or loses meaning that the instruction asked to keep.
- `scope`: the change goes beyond what the instruction asks.
- `error`: the change introduces a mistake, such as a broken link, a wrong statement or an invalid
  format.
- `claim`: the worker's answer misstates what the worker did.

A finding is **blocking** when the caller cannot take the result as it is. Otherwise it is
**advisory**. The Operation derives the **verdict**. The verdict is `changes_required` exactly when
a finding is blocking, and `accepted` otherwise.

## Overview

```d2 illustrative
direction: down
instruction: "Read the instruction,\nkeep its copy"
before: "Record the worktree\nas a Git tree"
worker: "worker: does the work\nunder the --type grant"
after: "Record the worktree again,\nkeep the diff and the earlier files"
reviewer: "reviewer: judges the result\nagainst the instruction, read-only"
verdict: "Derive the verdict"
caller: "The caller decides:\nkeep, revise or revert" {shape: oval}
stop: "blocked or failed:\nno review" {shape: oval}
instruction -> before -> worker
worker -> after: "ok, audit clean"
worker -> stop: "blocked, failed\nor audit violation" {style.stroke-dash: 3}
after -> reviewer -> verdict -> caller
```

## Running general

```text
concorde run general --type <task type> (--instruction "<text>" | --instruction-file <file>)
                     [--read-only] [--modules <module-id>[,<module-id>…]] [--input <run-id>]…
```

The options are:

- `--type` names the task type whose grant bounds both workers. It is one of `understand`,
  `specify`, `implement`, `test`, `review-spec`, `review-code`, `code-to-spec` and
  `review-architecture`.
- `--instruction` gives the instruction as text.
- `--instruction-file` names a file that holds the instruction, relative to the worktree the run
  works on or absolute. Exactly one of `--instruction` and `--instruction-file` is given.
- `--read-only` lowers every writable level of the grant to read.
- `--modules` names the run's Modules (default: the binding's).
- `--input` admits an earlier `ok` run's output as material. The worker's brief carries it after
  the instruction.

In a bound workspace, the worker's brief also carries the workspace's goal. In a worktree without a
binding, such as the primary worktree, the run is unbound. It then works on the Modules `--modules`
names, and only with a type that writes nothing or with `--read-only`. For example, `--type specify
--instruction-file restyle.md` in a task worktree bound to `module.issues` has the worker rewrite
the Issues Specs as `restyle.md` says. The reviewer then checks that the rewrite kept every
promise.

The output is a [general work result](contracts.md#contract.general-work.result). It holds:

- The type and whether writes were withheld.
- The instruction's file, copy and digest.
- The worker's answer.
- The observed change.
- The review, with its findings and verdict.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | the worker ended `ok`, the reviewer reviewed the result, any verdict |
| `blocked` | `worker_blocked` | `decision` | the worker could not do the work, or the reviewer could not judge it; the worker's own link says why |
| `failed` | a code of the [worker sequence](../workers.md#errors-of-the-worker-sequence) | as that table gives | the grant could not be computed, a worker could not be run, an audit found a write outside the grant, or a writing type ran unbound (`unbound_write`) |
| `failed` | `instruction_unreadable` | `input` | the instruction file is missing, unreadable or not UTF-8 text, or the instruction is empty |
| `failed` | `change_unobservable` | `environment` | Git could not record the worktree as a tree before or after the worker |
| `failed` | `inconsistent_review` | `capability` | two findings of the review have the same id |

`instruction_unreadable` stops the run before any worker launches. When the worker does not end
`ok`, the reviewer does not launch. When the reviewer does not end `ok`, the worker's change stays
in the worktree. The run's host evidence then names the changed files and the kept diff. Only an
`ok` run carries an output. The `worker` field of the [run
result](../../glossary.json#concept.run-result) carries the [worker
result](../../glossary.json#concept.worker-result) of the last worker the run launched.

## How it is built

The Operation is worker-backed, with a task type each run names. Its definition therefore declares
no fixed task type ([Operations](../../execution/operations/module.md)).

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Read the instruction, keep its copy in the run's trace node and record its digest | Operation | unreadable or empty instruction (`failed`) |
| 2 | Record the worktree as a Git tree, with a temporary index | Operation, Git | Git fails (`failed`) |
| 3 | Run the worker through the standard worker sequence for the `--type` grant, writes withheld with `--read-only` | Operation, Spec core, Workers, worker | a code of the worker sequence (`failed`); `blocked` passed on |
| 4 | Record the worktree again; keep the diff and the earlier content of each changed file | Operation, Git | Git fails (`failed`) |
| 5 | Run the reviewer through the standard worker sequence for the same type, writes withheld | Operation, Spec core, Workers, reviewer | a code of the worker sequence (`failed`); `blocked` passed on |
| 6 | Check the review, derive the verdict and return the result | Operation, Execution runner | duplicate finding ids (`failed`) |

Neither worker gets configured checks or [resume rounds](../../glossary.json#concept.resume-round).
Nothing in this Operation validates a round, so a round never has anything to repair. The round
validation Method gives every worker still checks glossary ownership. The Operation keeps the
worker's answer and the reviewer's findings as their claims. It decides only these:

- The observed change.
- The distinct finding ids.
- The verdict that follows from the findings.

Recording the worktree as a tree writes Git objects but changes neither `HEAD` nor the index. The
write audit therefore sees nothing of it. The temporary index starts as a copy of the worktree's
index, so Git hashes only the files that changed.

<a id="realization.general-work.operation"></a>

The **General work Operation** realization holds the Operation's steps and result schemas in
`src/concorde/method/general_work/`. `operation.py` declares the `GENERAL` provider. The realization
uses the prompts `prompts/workers/general.md` for the worker and `prompts/workers/general-review.md`
for the reviewer. It is tested against a fake worker in `tests/concorde/general_work/`.

## What it relies on

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, is what `general` plugs into. Method registers its
definition, with these properties:

- It may run unbound.
- It may change the workspace through its worker's grant.
- It declares the workers `worker` and `reviewer`.
- Its task type is not fixed.

It names this Module as its provider
([Method](../module.md#the-operations-and-commands-it-provides)). The `general` Operation never
calls another Operation.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs the Operation's steps.
General work relies on it for these:

- The workspace's goal and Modules, from the
  [workspace binding](../../glossary.json#concept.workspace-binding).
- The run's trace node, where the Operation keeps the instruction, the diff and the earlier files.
- The [unbound checkout](../../glossary.json#concept.unbound-checkout) of an unbound run.
- Wrapping the result in the run result.

<a id="uses-workers"></a>

**Workers**, in the worker harness, launches both workers through Method's standard worker
sequence. For each worker, it does these:

- Turns the grant into settings.
- Launches the worker with this Module's instructions.
- Audits the worktree.
- Writes the [run record](../../glossary.json#concept.run-record).

Any audit violation is a failed run. The reviewer may also read the run's kept diff and earlier
files, which lie outside its grant, as host material.

<a id="uses-spec"></a>

**Spec core** computes the grant of the named type from the Specs of the worktree the run works
on. It also resolves the run's Modules.
