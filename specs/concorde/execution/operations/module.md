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

## Core concepts

<a id="concept.operation"></a>

An **Operation** hides the internal execution of one AI job from its caller. For `implement`, it
prepares a grant and brief, delegates code changes to a worker through Workers, and uses check
results to check the changes and drive bounded repair rounds; the caller receives one run result
without managing those rounds. An Operation exists because a model's answer must be checked by a
program before anyone above relies on it, so the catalog holds exactly the jobs that involve a
model. A plan stays one answer `understand` gives, not a separate Operation, and its review is the
Operation `plan_review`, in which a model judges a plan the caller wrote; readiness, delivery and
scaffolding are commands of their own Modules, not Operations, and the
[worker configuration](../../glossary.json#concept.worker-configuration) is a tracked file edited
directly.

Every worker an Operation may launch has a stable [worker
id](../../glossary.json#concept.worker-id), which the catalog lists: `spec_review` has a `reviewer`
and a `checker`, `spec_panel` a `reviewer1` to `reviewer5`, one per seat its panel may have, an
`architect1` and an `architect2`, one per architect it may have, and a `chair`, `plan_review` a
single `reviewer`, and every other Operation a single `worker`. The same id keys the worker
configuration, names the worker in its run record and labels the run's `worker-model` evidence, so
each worker may have its own backend, model and level.

<a id="concept.operation-catalog"></a>

The **Operation catalog** of this version:

| Operation | Provider | [Task type](../../glossary.json#concept.task-type) | [Worker ids](../../glossary.json#concept.worker-id) | Unbound | May change | Output |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | [Understanding](understanding/module.md) | `understand` | `worker` | yes | no | [an assessment](understanding/contracts.md#contract.understanding.assessment), with a plan when asked |
| `plan_review` | [Understanding](understanding/module.md) | `review-code` | `reviewer` | no | no | a [plan review report](understanding/contracts.md#contract.understanding.plan-review) with findings and a verdict |
| `specify` | [Specification](specification/module.md) | `specify` | `worker` | no | Specs of the bound Modules, including documents it creates, and the registry mirror | a [Spec change](../../glossary.json#concept.spec-change) ([contract](specification/contracts.md#contract.specification.spec-change)) |
| `implement` | [Implementation](implementation/module.md) | `implement` | `worker` | no | code of the bound Modules | [a code change](implementation/contracts.md#contract.implementation.code-change) |
| `test` | [Implementation](implementation/module.md) | `test` | `worker` | no | no | a test report ([contract](implementation/contracts.md#contract.implementation.test-report)) |
| `spec_review` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer`, `checker` | yes | no | [review findings](../../glossary.json#concept.review-finding) and a verdict ([contract](../../spec-tooling/spec-review/operation.md#contract.spec-review.payload)) |
| `spec_panel` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec`; `review-architecture` for its architects, and for its chair when it has an architect | `reviewer1` … `reviewer5`, `architect1`, `architect2`, `chair` | yes | no | a panel report merged from independent reviews, and a verdict ([contract](../../spec-tooling/spec-review/panel.md#contract.spec-review.panel-payload)) |
| `code_review` | [Code review](code-review/module.md) | `review-code` | `worker` | yes (`--base` for a change review) | no | a code review report of a change or of whole Modules, each finding reported as an [Issue](../../glossary.json#concept.issue), and a verdict ([contract](code-review/contracts.md#contract.code-review.review)) |
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, Specs withheld | `worker` | yes | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | no | Specs of the bound Modules, the registry mirror and the `verifies` links of the existing tests it describes | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |

"May change" covers both what a worker's grant makes writable and what the provider's own host
steps change in the workspace; each provider's Spec gives the rule.

<a id="concept.standard-worker-sequence"></a>

Each Operation's control flow is a step table in its provider's Spec, which the runner runs in
order until one step stops the run. A worker-backed step follows the
**[standard worker sequence](../../glossary.json#concept.standard-worker-sequence)**: compute the
[grant](../../glossary.json#concept.grant) for the task type and Modules from the **workspace's**
Specs and freeze it with its [context identity](../../glossary.json#concept.context-identity),
generate the worker's settings, tools and [brief](../../glossary.json#concept.brief), launch the
worker, run the [write audit](../../glossary.json#concept.write-audit), then, when the worker ended
`ok` with a clean audit, run the [configured checks](../../glossary.json#concept.configured-check)
of the bound Modules and of every Module that uses one of them outside the worker if the step asks
for them, and the step's own validation if it has one, feed what fails back as a [resume
round](../../glossary.json#concept.resume-round) until nothing needs repair or the rounds run out,
and write the [run record](../../glossary.json#concept.run-record). The step computes and freezes
the grant through Spec core and hands it to Workers, which performs the rest; the step decides what
the outcome means. Configured checks are the project's commands for a Module's code, such as an
`implement` step asks for; a step's own validation is the provider's check of what its worker
wrote, such as the structural validation a Spec-writing step runs instead of configured checks.
See [How an Operation runs its workers](workers.md).

## Overview

### How a worker-backed step runs

The [standard worker sequence](../../glossary.json#concept.standard-worker-sequence): the step
freezes the grant and decides what the outcome means, and Workers does everything between. Each
provider's step table says which of these steps it takes, and what stops the run at each.

```d2 illustrative
direction: down
grant: "Operation step: compute the grant from the\nworkspace's Specs and freeze it with its context identity"
workers: Workers {
  prepare: "Generate settings, tools and brief"
  launch: "Launch or resume the worker"
  audit: "Write audit against the grant"
  checks: "Run the configured checks, when the step asks,\nand the step's own validation, when it has one"
  record: "Write the run record"
  prepare -> launch -> audit
  audit -> checks: "worker ended ok, audit clean"
  launch <- checks: "a check fails or validation reports a repair,\nrounds left: resume round" {style.stroke-dash: 3}
  checks -> record: "nothing to repair or none asked for,\nor rounds used up"
  audit -> record: "worker blocked or failed, invalid result,\ntimeout or audit violation" {style.stroke-dash: 3}
}
decide: "Operation step: decide what\nthe outcome means for the run"
grant -> workers.prepare: "the frozen grant"
workers.record -> decide: "worker result and evidence"
```

### Claims and evidence

A worker-backed run's result carries the worker's own
[worker result](../../glossary.json#concept.worker-result) unchanged in `worker`, beside
the evidence the run's steps produced — grant, context identity, write audit, each check's exit
code and log, resume rounds used, transcript path, worker stderr — so the caller reads the claim as
a claim and the evidence as fact. For example, an `implement` worker claims the goal is done, but
one check still fails after the last resume round:

```d2 illustrative
direction: right
worker: Worker {
  claim: "Returns its worker result:\nclaims the goal is done"
}
op: "Operation (in the Execution runner)" {
  direction: down
  measure: "Audit clean; 3 resume rounds;\none check still fails"
  result: "Run result failed: the claim unchanged\nin worker, the evidence beside it;\nchain: Operation (rounds used up, decide)\n< Workers (rounds) < check (log)"
  measure -> result
}
caller: "Task level" {
  decide: "Reads the claim as a claim,\nthe evidence as fact;\ndecides the next step"
}
worker.claim -> op.measure
op.result -> caller.decide
```

### Where Operations sits

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

## Running an Operation

Whoever works a workspace runs an Operation inside it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

The run works on the workspace whose binding lies in the worktree it starts in; `--modules`,
`--input`, `--detach`, the run identity, the
[run progress file](../../glossary.json#concept.run-progress-file), the
[workspace lock](../../glossary.json#concept.workspace-lock) and the result are the
[Execution runner](../runner.md)'s, the same for every run. Each provider adds its own arguments,
such as `--goal` for `understand`. No Operation needs the developer's consent.

At the task level, the [task session](../../glossary.json#concept.task-session) of a task runs its
Operations, directly or through a workflow, in its task worktree, and handles their results and
chooses the next step within its authority, following its decision and escalation rules. A typical
task runs `understand`, optionally `plan_review` on the plan it settles on, `specify` if needed,
`implement`, `test` and the reviews, then the execution commands `task-validation` and `delivery`,
repeating or skipping steps as the results tell it. The
[main agent](../../glossary.json#concept.main-agent) never works inside a task worktree: it runs
only [unbound runs](../../glossary.json#concept.unbound-run) of Operations, from the primary
worktree, where `understand` or a review answers a question about its `HEAD` before any change is
agreed. For a project whose code came before its Specs, `survey`, the execution
command `scaffold` and `code_to_spec` describe the code in Specs, usually run by the
[brownfield workflow](../workflows/module.md).

## How it is built

Between the task level, which has the workspace's goal, and a worker, which has only a narrow
brief, an Operation's host steps freeze the grant, launch the worker through Workers, audit what it
changed, run checks themselves, and turn the outcome into a result whose facts they produced. A
worker's answer is a proposal until those steps have checked it, and the run result keeps the two
apart. Deterministic work, which needs no such check, is left to execution commands.

The grant always comes from the workspace's Specs, never the primary worktree's, so a task that
changes a Spec is bounded by the Spec as its workspace sees it; an
[unbound run](../../glossary.json#concept.unbound-run) reads its
[unbound checkout](../../glossary.json#concept.unbound-checkout) of the worktree it started in and
may launch only reading workers, since only a bound workspace may change. One workspace runs one run
at a time, because two runs in one worktree would audit each other's writes as their own, so
parallelism comes from running workspaces side by side. No provider calls another Operation: the
task level or its workflow decides which runs next.

<a id="realization.operations.catalog"></a>

The **Catalog and worker steps** realization holds the catalog (`catalog.py`), the step it puts
first in every Operation that launches workers, checking them all against the
[model map](../../glossary.json#concept.model-map) (`admission.py`), the prompt and
brief helpers of worker-backed providers (`provider.py`) and the review providers' shared handling
of their Issues (`review_issues.py`): reading a reviewed Module's earlier Issues by the Operations
that reported them, settling which a review names, resolves or carries, and reporting each finding
through the Issue store, so that every review treats its earlier Issues by the same rules; the
standard worker sequence itself is
the run context's worker launch, which the
[Runner and run store](../module.md#realization.execution.runner) realization binds. The providers'
own code lives with their Modules.

<a id="realization.operations.tests"></a>

The **Operations tests**, under `tests/concorde/operations/`, run an Operation through the runner in
a real task worktree with a stand-in provider and show that the catalog's first step checks all its
workers against the model map before any of the provider's own steps; the worker sequence's own
scenarios are verified with the runner's tests.

### Workers and Check execution

<a id="uses-workers"></a>

**Workers** launches every worker. A worker-backed step hands it the grant it froze, the brief, the
worker id and the [trace node](../../glossary.json#concept.trace-node) folder of the run, and
Workers performs the rest of the standard worker sequence — settings, launch, audit, checks and resume rounds, run record — and returns the worker result with the evidence it gathered.
The Operation relies on Workers launching the worker only under that grant, auditing every write
against it and keeping the worker's claims apart from what it measured. It keeps the worker result
unchanged and decides what the outcome means for the run. A launch error, a timeout or an audit
violation ends the run `failed`, with Workers' link as a cause of the Operation's own.

<a id="uses-checks"></a>

**Check execution** is the deterministic service that runs configured checks read-only, for the
resume rounds Workers drives and for providers that run checks themselves, returning each result's
command, exit code and log as evidence. An Operation relies on a check writing nothing in the
workspace outside its check scratch, and on a result being refused as `stale_evidence` when the
input it measured changed during the run, whatever changed it. It keeps each
[check result](../../glossary.json#concept.check-result) as its own evidence rather than a worker's
claim, and ends the run `failed` when the check boundary cannot be established or a check still
fails after the last resume round, with the check's error or log in the chain.

### The providers

Each Operation's behaviour lives with the Module that provides it: five children of Operations and
Spec review, which lives in Spec tooling. A provider supplies its steps, its worker ids and the
contract of its output; the runner runs those steps, checks the output against its contract and
wraps it in the run result. A provider relies on its worker-backed steps freezing the grant and
launching workers only through Workers; the runner relies on each provider's steps staying within
its catalog entry.

<a id="contains-understanding"></a>

**Understanding** provides `understand` and `plan_review`. In `understand` a worker reads the bound
Modules' Specs and file names and returns an assessment, changing nothing; its output is advice to
the task level, never an instruction to the runner. It may run unbound, which is how the main agent
answers a question before any change is agreed. In the optional `plan_review` a reviewer reads the
Specs and the code and judges a plan the task level wrote, changing nothing; the task level answers
its findings in the next run, with the previous run as `--input`, until the verdict is `accepted`.
It needs a bound workspace, whose goal the plan is judged against.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents and the
Operation validates the result. It is the Operation that changes what a Module promises:
`code_to_spec` writes Specs only to describe existing code, and `implement` changes no Spec, so the
task level routes every Spec repair through `specify` or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable, and the Operation runs their checks
with resume rounds until they pass or the rounds run out, so its result says whether the checks
passed on the changed code. In `test` a read-only worker interprets the checks the Operation ran and
returns a test report; the check results, not the worker's reading of them, are the evidence. Both
need a bound workspace.

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges code against the Specs and returns
findings, changing nothing, either a workspace's change since the binding's base commit, or since
`--base` when it runs unbound, or, with `--scope module`, each named Module's whole code, one worker
per Module. The Operation keeps the findings as the workers' claims, checks their evidence, reports
each as an Issue of the project and derives the verdict from the tiers of the Issues that stand;
acting on an Issue is the task level's decision.

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
`spec_review`'s `reviewer` and `checker` and `spec_panel`'s reviewers, architects and `chair`, run
like any other provider's and change nothing. The findings stay the workers' claims, while the
provider derives the verdict from them and reports each as an
[Issue](../../glossary.json#concept.issue) from its own host, in bound and unbound runs alike; the primary worktree keeps those Issues, so the
workspace does not change. `spec_panel` is the one provider whose steps run a LangGraph graph inside
the run, which the runner neither knows nor needs: the provider still returns one run result
through the ordinary steps.

### What every Operation relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, resolves the named Modules, and computes each worker's
grant and context identity. An Operation relies on it computing the same grant from the same Specs,
and freezes that grant before any worker starts. A Spec that cannot be loaded is refused rather than
partially read, ending the run `failed`.

<a id="uses-execution"></a>

**Execution**'s runner runs every Operation: it reads the workspace binding, holds the workspace
lock, admits the Modules and inputs, runs the steps in order and writes the run result. An Operation
relies on it for everything about the run that is not the job itself, and knows nothing of tasks;
what it needs of its workspace, such as the goal a worker is briefed with or the base a review
compares against, it reads from the run context the runner fills from the binding.
