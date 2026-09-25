# Operations

## Purpose

Operations is how the main agent gets bounded work done in a task. It holds the Operation
catalog, the `concorde run` command and the Operation host, and delegates each Operation to the
Module that provides it (see Relationships). Every Operation combines deterministic host steps
with zero or more workers and ends with one Operation result that keeps what the host established
apart from what a worker claims. Operations never chooses what runs next, never runs one Operation
from another, never asks the developer anything and never changes a Spec on its own initiative:
the main agent decides.

## Terminology

| Term | Definition |
| --- | --- |
| Operation | A named job the main agent runs for one task, or for no task when its catalog entry allows it, made of deterministic host steps and zero or more workers, that ends with exactly one Operation result. |
| Run without a task | A run of an Operation whose catalog entry makes the task optional, started without `--task`: it works on the worktree it was started in, begins no task record, and changes no Spec or code. |
| Worker role | A named worker an Operation launches, such as `spec_review`'s `reviewer` and `checker`; an Operation with a single worker has the role `worker`. |
| configure_workers | The Operation that lists the models the main session's program offers workers and changes a worktree's worker model configuration, with or without a task. |
| Operation catalog | The fixed list of Operations that gives, for each, its providing Module, its task type, its worker roles, whether it needs a task, whether it may change the task worktree and the contract of its output. |
| Operation host | The deterministic process started by `concorde run` that executes one Operation's step table for one task, or for none, and alone launches its workers, checks their work and writes its result. |
| Operation progress file | The run's `status.json`, which the host keeps current with the Operation, task, current step and host process, and once finished with the status and summary. |
| Operation result | The structured envelope an Operation returns to the main agent, holding its status, identities, summary, output, the worker result kept as claims, the host's own evidence and, when it is not ok, its error chain. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Task type](../vocabulary.md#concept.concorde.task-type) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Grant](../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Context identity](../spec-tooling/spec/module.md#concept.spec.context-identity) | |
| [Worker result](../harness/workers/module.md#concept.workers.worker-result) | |
| [Brief](../harness/workers/module.md#concept.workers.brief) | |
| [Write audit](../harness/workers/module.md#concept.workers.audit) | |
| [Resume round](../harness/workers/module.md#concept.workers.resume-round) | |
| [Run record](../harness/workers/module.md#concept.workers.run-record) | |
| [Configured check](../harness/checks/module.md#concept.checks.configured-check) | |
| [Task](../tasks/module.md#concept.tasks.task) | |
| [Task record](../tasks/module.md#concept.tasks.task-record) | |

The catalog lists Operations; the host runs one of them and returns its Operation result. Read
Operation and Operation result first; the imported worker terms matter only for worker-backed
Operations.

## Usage

<a id="concept.operations.operation"></a>

The main agent runs an **Operation** for a [task](../tasks/module.md#concept.tasks.task) it
opened, as a background Bash command so it can keep working while it runs:

```text
concorde run <operation> [--task <task-id>] [--modules <id>[,<id>…]] [--input <run-id>]… [operation arguments]
```

`--modules` names the bound Modules (default: the task's) and adds any named here to the task;
`--input` admits an earlier `ok` run's output as task material; each provider adds its own
arguments, such as `--goal` for `understand`. The command returns when the run ends; the main agent
is woken by its exit and reads the printed Operation result, also saved under `.concorde/runs/`.
No Operation needs the developer's consent.

<a id="concept.operations.no-task"></a>

An Operation whose catalog entry makes the task optional may also run **without a task**: it then
works on the worktree the command is started in, usually the primary worktree, with the Modules
`--modules` names, begins no task record, admits only inputs of other runs without a task, and may
launch only reading workers, so it changes no Spec or code.

<a id="concept.operations.catalog"></a>

The **Operation catalog** of this version:

| Operation | Provider | Task type | Worker roles | Task | May write | Output |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | [Understanding](understanding/module.md) | `understand` | `worker` | optional | no | an assessment, with a plan when asked |
| `specify` | [Specification](specification/module.md) | `specify` | `worker` | required | Specs of the bound Modules | a Spec change |
| `implement` | [Implementation](implementation/module.md) | `implement` | `worker` | required | code of the bound Modules | a code change |
| `test` | [Implementation](implementation/module.md) | `test` | `worker` | required | no | a test report |
| `spec_review` | [Spec review](../spec-tooling/spec-review/module.md) | `review-spec` | `reviewer`, `checker` | optional | no | review findings and a verdict |
| `code_review` | [Code review](code-review/module.md) | `review-code` | `worker` | optional (`--base` without one) | no | review findings and a verdict |
| `validate` | [Validation](validation/module.md) | none | none | required | no | [readiness](validation/module.md#concept.validation.readiness) |
| `delivery` | [Delivery](delivery/module.md) | none | none | required | commits on the task branch | a [delivery commit](delivery/module.md#concept.delivery.delivery-commit) |
| `configure_workers` | Operations | none | none | optional | the worktree's untracked [worker model configuration](../harness/workers/module.md#concept.workers.model-configuration) | the [worker configuration](contracts.md#contract.operations.worker-configuration) |

A typical task runs `understand`, `specify` if needed, `implement`, `test` and the reviews, then
`validate` and `delivery`, repeating or skipping steps as the results tell it. Without a task the
main agent may run `understand` or a review to answer a question before any change is agreed, and
`configure_workers` when the developer asks to choose worker models.

<a id="concept.operations.worker-role"></a>

A **worker role** names one worker an Operation launches: `spec_review` has a `reviewer` and a
`checker`, every other worker-backed Operation a single `worker`. The catalog lists the roles, and
the worker model configuration may choose a model per Operation and per role.

<a id="concept.operations.configure-workers"></a>

**`configure_workers`** lists and changes the worker model configuration: without a model or
level it outputs the candidates the main session's program offers, the file's entries and the
effective model and level of every worker role of every Operation; `--model`, `--reasoning` or
both set them for the default, for `--operation <op>` or for `--role <role>` of it;
`--unset` removes that entry. Without a task it changes the worktree it runs in — in the primary
worktree the tasks opened from then on — and with `--task` only that task's copy. It checks the
Operation and role against the catalog and every model and level against the program's listing
(`--allow-unlisted` admits a model the listing cannot show), and launches no worker. Its exact
behaviour is in [the host](host.md#configure-workers). A plan is one answer
`understand` gives, not a separate Operation; a project's first Spec, Issues and task commands are
ordinary commands of their own Modules, not Operations.

How the pieces fit together:

```d2
catalog: Operation catalog
operation: Operation
host: Operation host
result: Operation result
workers: Workers
tasks: Tasks
runner: Catalog and runner
catalog -> operation: lists
host -> operation: runs
host -> result: returns
host -> workers: launches workers through
host -> tasks: records runs in
runner -> host: implements
```

<a id="concept.operations.result"></a>

Every run ends with one **Operation result**: the Operation, task, Modules, run and a summary, plus
`status` and the provider's `output`. `status` is `ok` when the Operation did what it promises,
`blocked` when it needs a main-agent decision, such as a reported Spec gap or stale readiness, and
`failed` when something went wrong: a launch error, a write outside the grant, checks still failing
after the last resume round, or a host error. A worker-backed Operation also carries the worker's
own [worker result](../harness/workers/module.md#concept.workers.worker-result) unchanged, plus the
host's evidence — grant, context identity, write audit, each check's exit code and log, resume
rounds used, transcript path, worker stderr. When `status` is not `ok`, `error` is the run's
[error chain](../vocabulary.md#concept.concorde.error-chain): the Operation's own link, describing
the error and why it cannot handle it, over the unchanged errors it received — the Workers
harness's link for a worker run, the worker's own link, a failing check, or the concerned Git,
Tasks or Spec core error. See the [result contract](contracts.md#contract.operations.result).

```d2 illustrative
shape: sequence_diagram
worker: Worker
host: Operation host
mainagent: Main agent
worker -> host: implement result: claims the goal is done
host -> host: audit clean; 3 resume rounds; one check still fails
host -> mainagent: failed - chain: Operation (rounds used up, decide) < Workers (rounds) < check (log)
mainagent -> mainagent: reads the claim as a claim, the evidence as fact; decides the next step
```

<a id="concept.operations.progress-file"></a>

While it runs, the host keeps the run's **progress file** `.concorde/runs/<run-id>/status.json`
current: the Operation, task and Modules, the step it is in, and, once finished, the status and
summary, with the host's process identifier. Each worker the run launches keeps its own [progress
file](../harness/workers/module.md#concept.workers.progress-file) with the same process identifier,
so an observer such as the main session's run view can follow a run and its worker without asking
the host. It is an observation aid; the Operation result is the run's answer.

`concorde run` exits with status 0 for an `ok` result and 1 for `blocked` or `failed`. A command
line that names no known Operation or no task is refused with status 2 and no result. A task the
run cannot accept — unknown, closed or already running — still gets a `failed` result naming the
refusal. Each run is new, with a new run identity.

## Design

<a id="concept.operations.host"></a>

Between the main agent, which has the global view, and a worker, which has only a narrow one,
stands the **Operation host**: a plain Python process that runs one Operation's step table,
freezes the grant, launches workers, audits what they changed, runs checks itself, and turns the
outcome into a result whose facts it produced. A worker's answer is a proposal until the host has
checked it, and the envelope keeps the two apart.

How Operations is built:

```d2
operations: Operations {
  runner: Catalog and runner {
    "src/concorde/operations/"
    "tests/concorde/operations/"
  }
  understanding: Understanding
  specification: Specification
  implementation: Implementation
  codereview: Code review
  validation: Validation
  delivery: Delivery
}
```

Each Operation's control flow is a step table in its provider's Spec, run as an ordered list of
Python steps until one stops the run. A worker-backed Operation follows the standard worker
sequence: compute the [grant](../spec-tooling/spec/module.md#concept.spec.grant) for the task type
and Modules from the **task worktree's** Specs and freeze it with its
[context identity](../spec-tooling/spec/module.md#concept.spec.context-identity), pre-create the
pending files it makes writable, generate the worker's settings, tools and
[brief](../harness/workers/module.md#concept.workers.brief), launch the worker, run the
[write audit](../harness/workers/module.md#concept.workers.audit), run the bound Modules'
[configured checks](../harness/checks/module.md#concept.checks.configured-check) outside the
worker, feed failures back as a
[resume round](../harness/workers/module.md#concept.workers.resume-round) until they pass or the
rounds run out, and write the [run record](../harness/workers/module.md#concept.workers.run-record).
Workers performs that sequence; the host decides what its outcome means. See
[How the host runs an Operation](host.md).

<a id="design.operations.task-binding"></a>

**Why most Operations need a task.** A task gives an Operation three things it cannot do without
when it changes files: a worktree whose Specs the grant comes from, so a change is bounded by the
Specs as the task sees them; the task record as the lock that lets one Operation at a time audit
that worktree, since two hosts would take each other's writes for violations; and the thread that
ties runs, their `--input`s and the delivery evidence together. An Operation that changes no Spec
or code needs none of them: its reading workers write nothing to audit, and a Spec it reads in the
primary worktree is the project as merged. So a catalog entry may make the task optional for such
an Operation, and the host then refuses a writing worker in the run, whatever the provider asks.

The grant always comes from the task worktree, never the primary, so a task that changes a Spec is
bounded by the Spec as it sees it (a run without a task reads the worktree it started in); results and run records still go to the primary's
`.concorde/runs/`, so the main agent finds every run in one place and nothing the host writes for
itself ends up in a task's diff. One task runs at most one Operation at a time — two hosts in one
worktree would audit each other's writes as their own — so parallelism comes from running tasks
side by side.

The host writes a result in every case it can, including its own failures, and records the run in
the [task record](../tasks/module.md#concept.tasks.task-record) at start and end, since the main
agent is woken only by the process exit and every problem must travel up as an
[error chain](../vocabulary.md#concept.concorde.error-chain) with evidence. No provider calls
another Operation: deciding the next step needs the global view only the main agent has. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.operations.runner"></a>

The **Catalog and runner** realization holds the catalog (`catalog.py`), the provider interface and
standard worker sequence (`provider.py`) and the step runner (`host.py`), tested against test
providers and a fake worker. The `concorde` command itself belongs to
[Distribution](../distribution/module.md), which hands `run` to this Module.

## Relationships

```d2
operations: Operations {
  understanding: Understanding
  specification: Specification
  implementation: Implementation
  codereview: Code review
  validation: Validation
  delivery: Delivery
}
spec: Spec core
harness: Harness {
  workers: Workers
  checks: Check execution
}
tasks: Tasks
specreview: Spec review
operations -> spec
operations -> harness.workers
operations -> harness.checks
operations -> tasks
operations -> specreview
```

The catalog names each Operation's provider, and the runner loads that provider's steps; a
provider never loads the catalog. The host runs one Operation per process, launches its workers
only through Workers, records the run through Tasks and returns exactly one Operation result.

<a id="contains-understanding"></a>

**Understanding** provides `understand`: a worker reads the bound Modules' Specs and file names and
returns an assessment, changing nothing; its output is advice to the main agent, never an
instruction to the host.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents,
including pending files, and the host validates the result. It is the only Operation that writes
Specs, so the main agent routes every Spec repair through it or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` (a worker changes code, the host runs checks with resume
rounds) and `test` (a read-only worker interprets the host's checks).

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges the task's code change against the bound
Modules' Specs and returns findings and a verdict, changing nothing.

<a id="contains-validation"></a>

**Validation** provides `validate`, the deterministic Operation that decides whether the task
worktree is ready to deliver, binding that readiness to the inputs it examined. Delivery relies on
it.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only Operation that runs Git commands that change the
repository, committing the task worktree's changes once readiness is current.

<a id="uses-spec"></a>

**Spec core** loads the task worktree's Specs, resolves the named Modules, and computes each
worker's [grant](../spec-tooling/spec/module.md#concept.spec.grant) and
[context identity](../spec-tooling/spec/module.md#concept.spec.context-identity). A Spec that
cannot be loaded is refused rather than partially read, ending the run `failed`.

<a id="uses-workers"></a>

**Workers** performs the standard worker sequence — settings, launch, audit, resume rounds, run
record — and returns the
[worker result](../harness/workers/module.md#concept.workers.worker-result) with the evidence it
gathered. A launch error, a timeout or an audit violation ends the run `failed`.

<a id="uses-checks"></a>

**Check execution** runs
[configured checks](../harness/checks/module.md#concept.checks.configured-check) read-only, for
the resume rounds Workers drives and for deterministic providers such as Validation, returning each
result's command, exit code and log as host evidence.

<a id="uses-tasks"></a>

**Tasks** resolves a task to its worktree and records each run, refusing an unknown, closed or busy
task before any step; such a refusal becomes a `failed` result not recorded in the task.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_review` from Spec tooling: reviewers read the bound Modules' Specs
and return findings and a verdict, listed in the catalog like a contained provider but living in
Spec tooling because it maintains Specs rather than changing a project.
