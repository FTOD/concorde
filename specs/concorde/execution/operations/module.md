# Operations

## Purpose

Operations is how bounded AI work gets done in a workspace. It holds the
[Operation catalog](../../glossary.json#concept.operation-catalog) and delegates each
[Operation](../../glossary.json#concept.operation) to the
[Module](../../glossary.json#concept.module) that provides it (see [The providers](#the-providers)).
Every Operation combines host steps, service calls and one or more AI workers to complete one job,
and ends with one [run result](../../glossary.json#concept.run-result) that keeps what the host
steps established apart from what a worker claims. Work that needs no model is not an Operation: it
is an [execution command](../../glossary.json#concept.execution-command) of its own Module.

Operations never chooses the next Operation, runs one Operation from another, asks the developer
anything or changes a [Spec](../../glossary.json#concept.spec) on its own initiative: whoever works
the workspace, directly or through a [workflow](../workflows/module.md), orders the runs. How a run
is started, recorded, locked and reported is the
[Execution runner](../../glossary.json#concept.execution-runner)'s, which runs an Operation's steps
like any other definition's.

## Usage

An Operation hides the internal execution of one AI job from its caller. For `implement`, it
prepares a grant and brief, delegates [code changes](../../glossary.json#concept.code-change) to a
worker through Workers, and uses check results to check the changes and drive bounded repair rounds.
The caller receives one run result without managing those rounds. At the task level, either the
[main agent](../../glossary.json#concept.main-agent) or a
[task session](../../glossary.json#concept.task-session) can invoke Operations directly or through
a workflow in its task worktree. The caller handles results and chooses the next step within its
authority, following its existing decision and escalation rules.

<a id="concept.operation"></a>

Whoever works a workspace runs an **Operation** inside it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

The run works on the workspace whose binding lies in the worktree it starts in; `--modules`,
`--input`, `--detach`, the run identity, the
[run progress file](../../glossary.json#concept.run-progress-file), the
[workspace lock](../../glossary.json#concept.workspace-lock) and the result are the
[Execution runner](../runner.md)'s, the same for every run. Each provider adds its own arguments,
such as `--goal` for `understand`. No Operation needs the developer's consent.

<a id="concept.operation-catalog"></a>

The **Operation catalog** of this version:

| Operation | Provider | [Task type](../../glossary.json#concept.task-type) | [Worker ids](../../glossary.json#concept.worker-id) | Unbound | May change | Output |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | [Understanding](understanding/module.md) | `understand` | `worker` | yes | no | [an assessment](understanding/contracts.md#contract.understanding.assessment), with a plan when asked |
| `specify` | [Specification](specification/module.md) | `specify` | `worker` | no | Specs of the bound Modules, including documents it creates, and the registry mirror | a [Spec change](../../glossary.json#concept.spec-change) ([contract](specification/contracts.md#contract.specification.spec-change)) |
| `implement` | [Implementation](implementation/module.md) | `implement` | `worker` | no | code of the bound Modules, and the pending markers of the entries whose files now exist | [a code change](implementation/contracts.md#contract.implementation.code-change) |
| `test` | [Implementation](implementation/module.md) | `test` | `worker` | no | no | a [test report](../../glossary.json#concept.test-report) ([contract](implementation/contracts.md#contract.implementation.test-report)) |
| `spec_review` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer`, `checker` | yes | a bound run: the reviewed Modules' [review memory](../../glossary.json#concept.review-memory); unbound: no | [review findings](../../glossary.json#concept.review-finding) and a verdict ([contract](../../spec-tooling/spec-review/operation.md#contract.spec-review.payload)) |
| `spec_panel` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer1` … `reviewer5`, `chair` | yes | no | a [panel report](../../glossary.json#concept.panel-report) merged from independent reviews, and a verdict ([contract](../../spec-tooling/spec-review/panel.md#contract.spec-review.panel-payload)) |
| `code_review` | [Code review](code-review/module.md) | `review-code` | `worker` | yes (`--base`) | no | a [code review report](../../glossary.json#concept.code-review-report) with findings and a verdict ([contract](code-review/contracts.md#contract.code-review.review)) |
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, Specs withheld | `worker` | yes | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | no | Specs of the bound Modules, the registry mirror and the `verifies` links of the existing tests it describes | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |

"May change" covers both what a worker's grant makes writable and what the provider's own host
steps change in the workspace; each provider's Spec gives the rule.

A typical task runs `understand`, `specify` if needed, `implement`, `test` and the reviews, then the
execution commands `task-validation` and `delivery`, repeating or skipping steps as the results tell
it. Unbound, started in the primary worktree, `understand` or a review answers a question about its
`HEAD` before any change is agreed. For a project whose code came before its Specs, `survey`, the execution command
`scaffold` and `code_to_spec` describe the code in Specs, usually run by the
[brownfield workflow](../workflows/module.md).

Every worker an Operation may launch has a stable [worker
id](../../glossary.json#concept.worker-id), which the catalog lists: `spec_review` has a
`reviewer` and a `checker`, `spec_panel` a `reviewer1` to `reviewer5`, one per seat its panel may
have, and a `chair`, and every other Operation a single `worker`. The same id keys the worker
configuration, names the worker in its run record and labels the run's `worker-model` evidence,
so each worker may have its own backend, model and level.

A worker-backed run's result carries the worker's own
[worker result](../../glossary.json#concept.worker-result) unchanged in `worker`, beside
the evidence the run's steps produced — grant, context identity, write audit, each check's exit
code and log, resume rounds used, transcript path, worker stderr — so the caller reads the claim as
a claim and the evidence as fact:

```d2 illustrative
shape: sequence_diagram
worker: Worker
op: Operation (in the Execution runner)
caller: Task level
worker -> op: implement result: claims the goal is done
op -> op: audit clean; 3 resume rounds; one check still fails
op -> caller: failed - chain: Operation (rounds used up, decide) < Workers (rounds) < check (log)
caller -> caller: reads the claim as a claim, the evidence as fact; decides the next step
```

A plan is one answer `understand` gives, not a separate Operation; readiness, delivery and
scaffolding are commands of their own Modules, not Operations, and the
[worker configuration](../../glossary.json#concept.worker-configuration) is a tracked file edited
directly.

## Design

An Operation exists because a model's answer must be checked by a program before anyone above
relies on it. Between the task level, which has the workspace's goal, and a worker, which has only a
narrow brief, an Operation's host steps freeze the grant, launch the worker through Workers, audit
what it changed, run checks themselves, and turn the outcome into a result whose facts they
produced. A worker's answer is a proposal until those steps have checked it, and the run result
keeps the two apart. Deterministic work, which needs no such check, is left to execution commands,
so the catalog holds exactly the jobs that involve a model.

### Its place among the runs

Operations is called only through the
[Execution runner](../../glossary.json#concept.execution-runner): by the task level with
`concorde run`, or by a [workflow](../workflows/module.md) step that runs the same command detached.
The runner reads the [workspace binding](../../glossary.json#concept.workspace-binding), holds the
workspace lock and writes the result; an Operation's steps call only downward, into Workers and
services such as Check execution. Nothing below calls back up: a worker never runs an Operation, and
a service call returns to the step that made it.

```d2
operations: Operations {
  catalog: Operation catalog
  operation: Operation
  catalog -> operation: lists
}
workers: Workers
checks: Check execution
operations.operation -> workers: launches workers through
operations.operation -> checks: runs checks through
```

<a id="uses-workers"></a>

**Workers** launches every worker. A worker-backed step hands it the grant it froze, the brief, the
worker id and the records directory, and Workers performs the rest of the
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence) — settings,
pending files, launch, audit, checks and resume rounds, run record — and returns the
[worker result](../../glossary.json#concept.worker-result) with the evidence it gathered. The
Operation relies on Workers launching the worker only under that grant, auditing every write against
it and keeping the worker's claims apart from what it measured. It keeps the worker result unchanged
and decides what the outcome means for the run. A launch error, a timeout or an audit violation ends
the run `failed`, with Workers' link as a cause of the Operation's own.

<a id="uses-checks"></a>

**Check execution** is the deterministic service that runs
[configured checks](../../glossary.json#concept.configured-check) read-only, for the resume rounds
Workers drives and for providers that run checks themselves, returning each result's command, exit
code and log as evidence. An Operation relies on a check writing nothing in the workspace outside
its [check scratch](../../glossary.json#concept.check-scratch), and on a result being refused as
`stale_evidence` when the input it measured changed during the run, whatever changed it. It keeps
each [check result](../../glossary.json#concept.check-result) as its own evidence rather than a
worker's claim, and ends the run `failed` when the check boundary cannot be established or a check
still fails after the last resume round, with the check's error or log in the chain.

### Inside

<a id="concept.standard-worker-sequence"></a>

Each Operation's control flow is a step table in its provider's Spec, which the runner runs in
order until one step stops the run. A worker-backed step follows the **standard worker
sequence**: compute the [grant](../../glossary.json#concept.grant) for the task
type and Modules from the **workspace's** Specs and freeze it with its
[context identity](../../glossary.json#concept.context-identity), generate the worker's settings,
tools and [brief](../../glossary.json#concept.brief), pre-create the pending files the grant makes
writable, launch the worker, run the [write audit](../../glossary.json#concept.write-audit), run
the [configured checks](../../glossary.json#concept.configured-check) of the bound Modules and of
every Module that uses one of them outside the worker when it ended `ok`, feed failures back as a
[resume round](../../glossary.json#concept.resume-round) until they pass or the rounds run out,
and write the [run record](../../glossary.json#concept.run-record). The step computes and freezes
the grant through Spec core and hands it to Workers, which performs the rest; the step decides
what the outcome means. See [How an Operation runs its workers](workers.md).

The grant always comes from the workspace's Specs, never the primary worktree's, so a task that
changes a Spec is bounded by the Spec as its workspace sees it; an
[unbound run](../../glossary.json#concept.unbound-run) reads its
[unbound checkout](../../glossary.json#concept.unbound-checkout) of the worktree it started in and
may launch only reading workers, since only a bound workspace may change. One workspace runs one run at a time,
because two runs in one worktree would audit each other's writes as their own, so parallelism comes
from running workspaces side by side. No provider calls another Operation: the task level or its
workflow decides which runs next.

<a id="realization.operations.catalog"></a>

The **Catalog and worker steps** realization holds the catalog (`catalog.py`) and the prompt and
brief helpers of worker-backed providers (`provider.py`); the standard worker sequence itself is
the run context's worker launch, which the
[Runner and run store](../module.md#realization.execution.runner) realization binds. The providers'
own code lives with their Modules.

### The providers

Each Operation's behaviour lives with the Module that provides it: five children of Operations and
Spec review, which lives in Spec tooling. A provider supplies its steps, its worker ids and the
contract of its output; the runner runs those steps, checks the output against its contract and
wraps it in the run result. A provider relies on its worker-backed steps freezing the grant and
launching workers only through Workers; the runner relies on each provider's steps staying within
its catalog entry.

<a id="contains-understanding"></a>

**Understanding** provides `understand`: a worker reads the bound Modules' Specs and file names and
returns an assessment, changing nothing; its output is advice to the task level, never an
instruction to the runner. It may run unbound, which is how the
[main agent](../../glossary.json#concept.main-agent) answers a question before any change is agreed.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents,
including pending files, and the Operation validates the result. It is the Operation that changes
what a Module promises: `code_to_spec` writes Specs only to describe existing code, and
`implement`'s host only clears pending markers, so the task level routes every Spec repair through
`specify` or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable, and the Operation runs their checks
with resume rounds until they pass or the rounds run out, so its result says whether the checks
passed on the changed code. In `test` a read-only worker interprets the checks the Operation ran and
returns a test report; the check results, not the worker's reading of them, are the evidence. Both
need a bound workspace.

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges the workspace's code change against the
bound Modules' Specs and returns findings, changing nothing. The Operation prepares the change to
review from the binding's base commit, or from `--base` when it runs unbound, keeps the findings as
the worker's claims and derives the verdict from their severities itself; acting on a finding is
the task level's decision.

<a id="contains-adoption"></a>

**Adoption** provides `survey` and `code_to_spec`, the Operations that describe existing code in
Specs for a project whose code came before them: a read-only survey proposes child Modules, the
execution command `scaffold` of [Scaffold](../commands/scaffold/module.md) creates them between the
two, and `code-to-spec` workers describe each Module's code. The
[brownfield workflow](../workflows/module.md) usually runs them in that order.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_review` and `spec_panel` from Spec tooling: reviewers read the bound
Modules' Specs and return findings, listed in the catalog like a contained provider
but living in Spec tooling because it maintains Specs rather than changing a project. Its workers,
`spec_review`'s `reviewer` and `checker` and `spec_panel`'s reviewers and `chair`, run like any
other provider's and change nothing. The findings stay the reviewers' claims, while the provider
derives the verdict from them and, in a bound `spec_review` run, keeps them in the reviewed
Modules' [review memory](../../glossary.json#concept.review-memory). `spec_panel` is
the one provider whose steps run a LangGraph graph inside the run, which the runner neither knows
nor needs: the provider still returns one run result through the ordinary steps.

### What every Operation relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, resolves the named Modules, and computes each worker's
[grant](../../glossary.json#concept.grant) and
[context identity](../../glossary.json#concept.context-identity). An Operation
relies on it computing the same grant from the same Specs, and freezes that grant before any worker
starts. A Spec that cannot be loaded is refused rather than partially read, ending the run
`failed`.

<a id="uses-execution"></a>

**Execution**'s runner runs every Operation: it reads the workspace binding, holds the workspace
lock, admits the Modules and inputs, runs the steps in order and writes the run result. An Operation
relies on it for everything about the run that is not the job itself, and knows nothing of tasks;
what it needs of its workspace, such as the goal a worker is briefed with or the base a review
compares against, it reads from the run context the runner fills from the binding.
