# Operations

## Purpose

Operations is how bounded AI work gets done in a workspace. It holds the Operation catalog and
delegates each Operation to the Module that provides it (see [The providers](#the-providers)).
Every Operation combines host steps, Tool calls and one or more AI workers to complete one job,
and ends with one [run result](../module.md#concept.execution.run-result) that keeps what the host
steps established apart from what a worker claims. Work that needs no model is not an Operation:
it is a [recorded command](../module.md#concept.execution.recorded-command) of its own Module.

Operations never chooses the next Operation, runs one Operation from another, asks the developer
anything or changes a Spec on its own initiative: whoever works the workspace, directly or through
a [workflow](../workflows/module.md), orders the runs. How a run is started, recorded, locked and
reported is the [Execution runner](../module.md#concept.execution.runner)'s, which runs an
Operation's steps like any other definition's.

## Terminology

| Term | Definition |
| --- | --- |
| Operation | A named job that combines host steps, Tool calls and one or more AI worker runs under Spec-derived grants, started with `concorde run` in a workspace, and returns exactly one run result. |
| Operation catalog | The fixed list of Operations that gives, for each, its providing Module, its task type, the ids of its workers, whether it may run unbound, whether it may change the workspace and the contract of its output. |
| Standard worker sequence | The fixed sequence by which an Operation's step launches one worker: freeze the grant, prepare the brief and settings, launch through Workers, audit, run checks with resume rounds and record the worker run. |
| [Run](../module.md#concept.execution.run) | |
| [Run result](../module.md#concept.execution.run-result) | |
| [Unbound run](../module.md#concept.execution.unbound-run) | |
| [Workspace](../module.md#concept.execution.workspace) | |
| [Execution runner](../module.md#concept.execution.runner) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Tool](../../vocabulary.md#concept.concorde.tool) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Context identity](../../spec-tooling/spec/module.md#concept.spec.context-identity) | |
| [Worker result](../workers/module.md#concept.workers.worker-result) | |
| [Worker id](../workers/module.md#concept.workers.worker-id) | |
| [Brief](../workers/module.md#concept.workers.brief) | |
| [Write audit](../workers/module.md#concept.workers.audit) | |
| [Resume round](../workers/module.md#concept.workers.resume-round) | |
| [Run record](../workers/module.md#concept.workers.run-record) | |
| [Configured check](../tools/checks/module.md#concept.checks.configured-check) | |

The catalog lists Operations; the Execution runner runs one of them per process and returns its
run result. Read Operation and the catalog first; the imported worker terms matter for what a
worker-backed step does inside the run.

## Usage

An Operation hides the internal execution of one AI job from its caller. For `implement`, it
prepares a grant and brief, delegates code changes to a worker through Workers, and uses Tool
results to check the changes and drive bounded repair rounds. The caller receives one run result
without managing those rounds.

<a id="concept.operations.operation"></a>

Whoever works a workspace runs an **Operation** inside it, usually as a background command so it
can keep working while it runs:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

The run works on the workspace whose binding lies in the worktree it starts in; `--modules`,
`--input`, `--detach`, the run identity, the progress file, the workspace lock and the result are
the [Execution runner](../runner.md)'s, the same for every run. Each provider adds its own
arguments, such as `--goal` for `understand`. No Operation needs the developer's consent.

<a id="concept.operations.catalog"></a>

The **Operation catalog** of this version:

| Operation | Provider | Task type | Worker ids | Unbound | May write | Output |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | [Understanding](understanding/module.md) | `understand` | `worker` | yes | no | an assessment, with a plan when asked |
| `specify` | [Specification](specification/module.md) | `specify` | `worker` | no | Specs of the bound Modules | a Spec change |
| `implement` | [Implementation](implementation/module.md) | `implement` | `worker` | no | code of the bound Modules | a code change |
| `test` | [Implementation](implementation/module.md) | `test` | `worker` | no | no | a test report |
| `spec_review` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer`, `checker` | yes | no | review findings and a verdict |
| `spec_panel` | [Spec review](../../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer1` … `reviewer5`, `chair` | yes | no | a panel report merged from independent reviews, and a verdict |
| `code_review` | [Code review](code-review/module.md) | `review-code` | `worker` | yes (`--base`) | no | review findings and a verdict |
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, Specs withheld | `worker` | yes | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | no | Specs of the bound Modules and the registry mirror | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |

A typical task runs `understand`, `specify` if needed, `implement`, `test` and the reviews, then the
recorded commands `task-validation` and `delivery`, repeating or skipping steps as the results tell
it. Unbound, in the primary worktree, `understand` or a review answers a question before any change
is agreed. For a project whose code came before its Specs, `survey`, the recorded command
`scaffold` and `code_to_spec` describe the code in Specs, usually run by the
[brownfield workflow](../workflows/module.md).

Every worker an Operation may launch has a stable [worker
id](../workers/module.md#concept.workers.worker-id), which the catalog lists: `spec_review` has a
`reviewer` and a `checker`, `spec_panel` a `reviewer1` to `reviewer5`, one per seat its panel may
have, and a `chair`, and every other Operation a single `worker`. The same id keys the worker model
configuration, names the worker in its run record and labels the run's `worker-model` evidence,
so each worker may have its own backend, model and level.

A worker-backed run's result carries the worker's own
[worker result](../workers/module.md#concept.workers.worker-result) unchanged in `worker`, beside
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

A plan is one answer `understand` gives, not a separate Operation; readiness, delivery, scaffolding
and the worker model configuration are commands of their own Modules, not Operations.

## Design

An Operation exists because a model's answer must be checked by a program before anyone above
relies on it. Between the task level, which has the workspace's goal, and a worker, which has only a
narrow brief, an Operation's host steps freeze the grant, launch the worker through Workers, audit
what it changed, run checks themselves, and turn the outcome into a result whose facts they
produced. A worker's answer is a proposal until those steps have checked it, and the run result
keeps the two apart. Deterministic work, which needs no such check, is left to recorded commands,
so the catalog holds exactly the jobs that involve a model.

### Its place among the runs

Operations is called only through the [Execution runner](../module.md#concept.execution.runner):
by the task level with `concorde run`, or by a [workflow](../workflows/module.md) step that runs
the same command detached. The runner reads the workspace binding, holds the workspace lock and
writes the result; an Operation's steps call only downward, into Workers and the Tools. Nothing
below calls back up: a worker never runs an Operation, and a Tool call returns to the step that
made it.

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

**Workers** launches every worker. A worker-backed step hands it the frozen grant, the brief, the
worker id and the records directory, and Workers performs the standard worker sequence —
settings, launch, audit, resume rounds, run record — and returns the
[worker result](../workers/module.md#concept.workers.worker-result) with the evidence it gathered.
The Operation relies on Workers launching the worker only under that grant, auditing every write
against it and keeping the worker's claims apart from what it measured. It keeps the worker result
unchanged and decides what the outcome means for the run. A launch error, a timeout or an audit
violation ends the run `failed`, with Workers' link as a cause of the Operation's own.

<a id="uses-checks"></a>

**Check execution** is the deterministic Tool that runs
[configured checks](../tools/checks/module.md#concept.checks.configured-check) read-only, for the
resume rounds Workers drives and for providers that run checks themselves, returning each result's
command, exit code and log as evidence. An Operation relies on a check never changing the workspace
it measures and on a result being refused as `stale_evidence` when its input changed during the
run. It keeps each check result as its own evidence rather than a worker's claim, and ends the run
`failed` when the check boundary cannot be established or a check still fails after the last
resume round, with the check's error or log in the chain.

### Inside

<a id="concept.operations.standard-worker-sequence"></a>

Each Operation's control flow is a step table in its provider's Spec, which the runner runs in
order until one step stops the run. A worker-backed step follows the **standard worker
sequence**: compute the [grant](../../spec-tooling/spec/module.md#concept.spec.grant) for the task
type and Modules from the **workspace's** Specs and freeze it with its
[context identity](../../spec-tooling/spec/module.md#concept.spec.context-identity), pre-create the
pending files it makes writable, generate the worker's settings, tools and
[brief](../workers/module.md#concept.workers.brief), launch the worker, run the
[write audit](../workers/module.md#concept.workers.audit), run the bound Modules'
[configured checks](../tools/checks/module.md#concept.checks.configured-check) outside the worker,
feed failures back as a [resume round](../workers/module.md#concept.workers.resume-round) until they
pass or the rounds run out, and write the
[run record](../workers/module.md#concept.workers.run-record). Workers performs that sequence; the
step decides what its outcome means. See [How an Operation runs its workers](workers.md).

The grant always comes from the workspace's Specs, never the primary worktree's, so a task that
changes a Spec is bounded by the Spec as its workspace sees it; an unbound run reads the worktree it
runs in and may launch only reading workers, since only a bound workspace may change. One workspace
runs one run at a time, because two runs in one worktree would audit each other's writes as their
own, so parallelism comes from running workspaces side by side. No provider calls another
Operation: the task level or its workflow decides which runs next.

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
instruction to the runner. It may run unbound, which is how the main agent answers a question
before any change is agreed.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents,
including pending files, and the Operation validates the result. It is the only Operation that
writes Specs, so the task level routes every Spec repair through it or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable, and the Operation runs their checks
with resume rounds until they pass or the rounds run out, so its result says whether the checks
passed on the changed code. In `test` a read-only worker interprets the checks the Operation ran and
returns a test report; the check results, not the worker's reading of them, are the evidence. Both
need a bound workspace.

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges the workspace's code change against the
bound Modules' Specs and returns findings and a verdict, changing nothing. The Operation prepares
the change to review from the binding's base commit, or from `--base` when it runs unbound, and
keeps the verdict as the worker's claim; acting on a finding is the task level's decision.

<a id="contains-adoption"></a>

**Adoption** provides `survey` and `code_to_spec`, the Operations that describe existing code in
Specs for a project whose code came before them, and the recorded command `scaffold` between them:
a read-only survey proposes child Modules, the scaffold creates them, and `code-to-spec` workers
describe each Module's code. The [brownfield workflow](../workflows/module.md) usually runs them in
that order.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_review` and `spec_panel` from Spec tooling: reviewers read the bound
Modules' Specs and return findings and a verdict, listed in the catalog like a contained provider
but living in Spec tooling because it maintains Specs rather than changing a project. Its workers,
`spec_review`'s `reviewer` and `checker` and `spec_panel`'s reviewers and `chair`, run like any
other provider's, and it changes nothing; its verdict stays the reviewers' claim. `spec_panel` is
the one provider whose steps run a LangGraph graph inside the run, which the runner neither knows
nor needs: the provider still returns one run result through the ordinary steps.

### What every Operation relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, resolves the named Modules, and computes each worker's
[grant](../../spec-tooling/spec/module.md#concept.spec.grant) and
[context identity](../../spec-tooling/spec/module.md#concept.spec.context-identity). An Operation
relies on it computing the same grant from the same Specs, and freezes that grant before any worker
starts. A Spec that cannot be loaded is refused rather than partially read, ending the run
`failed`.

<a id="uses-execution"></a>

**Execution**'s runner runs every Operation: it reads the workspace binding, holds the workspace
lock, admits the Modules and inputs, runs the steps in order and writes the run result. An Operation
relies on it for everything about the run that is not the job itself, and knows nothing of tasks;
what it needs of its workspace, such as the goal a worker is briefed with or the base a review
compares against, it reads from the run context the runner fills from the binding.
