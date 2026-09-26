# Operations

## Purpose

Operations is how whoever works a task, the main agent inside it or a task session, gets bounded
work done. It is the fourth of Concorde's five levels, a program between the sessions above it and
the workers and Tools below it. It holds the Operation catalog, the `concorde run` command and the
Operation host, and delegates each Operation to the Module that provides it (see
[The providers](#the-providers)). Every Operation combines deterministic host control logic, Tool
calls and zero or more AI workers to complete one job, and ends with one Operation result that
keeps what the host established apart from what a worker claims. Operations never chooses the next
Operation, runs one Operation from another, asks the developer anything or changes a Spec on its
own initiative: the task level, directly or through a Workflow, orders the runs.

## Terminology

| Term | Definition |
| --- | --- |
| Operation | A named execution unit started from the task level, by the main agent, a task session or a Workflow, in a task unless its catalog entry allows none, that combines host control logic, Tool calls and zero or more worker runs to complete one job and return exactly one Operation result. |
| Run without a task | A run of an Operation whose catalog entry makes the task optional, started without `--task` in the primary worktree: it works on the primary worktree, begins no task record, and changes no Spec or code. |
| Worker role | A named worker an Operation launches, such as `spec_review`'s `reviewer` and `checker`; an Operation with a single worker has the role `worker`. |
| configure_workers | The Operation that lists the models an installed agent program offers workers and changes the model choices of a worktree's worker model configuration, with or without a task. |
| Operation catalog | The fixed list of Operations that gives, for each, its providing Module, its task type, its worker roles, whether it needs a task, whether it may change the task worktree and the contract of its output. |
| Operation host | The deterministic process started by `concorde run` that executes one Operation's step table for one task, or for none, and alone launches its workers, checks their work and writes its result. |
| Detached run | A run whose host `concorde run --detach` starts as a process of its own, printing the run identity at once instead of waiting for the result. |
| Operation progress file | The run's `status.json`, which the host keeps current with the Operation, task, current step and host process, and once finished with the status and summary. |
| Operation result | The structured envelope an Operation returns to the main agent, holding its status, identities, summary, output, the worker result kept as claims, the host's own evidence and, when it is not ok, its error chain. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Tool](../vocabulary.md#concept.concorde.tool) | |
| [Task type](../vocabulary.md#concept.concorde.task-type) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Grant](../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Context identity](../spec-tooling/spec/module.md#concept.spec.context-identity) | |
| [Worker result](../agents/workers/module.md#concept.workers.worker-result) | |
| [Brief](../agents/workers/module.md#concept.workers.brief) | |
| [Write audit](../agents/workers/module.md#concept.workers.audit) | |
| [Resume round](../agents/workers/module.md#concept.workers.resume-round) | |
| [Run record](../agents/workers/module.md#concept.workers.run-record) | |
| [Configured check](../checks/module.md#concept.checks.configured-check) | |
| [Task](../tasks/module.md#concept.tasks.task) | |
| [Task record](../tasks/module.md#concept.tasks.task-record) | |

The catalog lists Operations; the host runs one of them and returns its Operation result. Read
Operation and Operation result first; the imported worker terms matter only for worker-backed
Operations.

## Usage

An Operation hides the internal execution of one job from its caller. For `implement`, it
prepares a grant and brief, delegates code changes to a worker through Workers, and uses Tool
results to check the changes and drive bounded repair rounds. The caller receives one Operation
result without managing those rounds. `validate` and `delivery` use deterministic steps without
an AI worker; an Operation need not mix both kinds on every run.

A Workflow orders these jobs, passes admitted outputs between them and handles decision points.
It calls the same Operation interface as the main agent. Workers and Tools sit side by side below
that interface, at the bottom of the [five levels](../module.md#the-five-levels): Workers manages
AI runs; a Tool performs a specific action through programmed logic. A Tool call returns to the
current host step and starts no new Operation. Workers may also call Tools within a worker run,
such as Check execution after a round.

<a id="concept.operations.operation"></a>

The main agent runs an **Operation** for a [task](../tasks/module.md#concept.tasks.task) it
opened, as a background Bash command so it can keep working while it runs:

```text
concorde run <operation> [--task <task-id>] [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
```

`--modules` names the bound Modules (default: the task's) and adds any named here to the task;
`--input` admits an earlier `ok` run's output as task material; each provider adds its own
arguments, such as `--goal` for `understand`. The command returns when the run ends; the main agent
is woken by its exit and reads the printed Operation result, also saved under `.concorde/runs/`.
No Operation needs the developer's consent.

<a id="concept.operations.detached-run"></a>

With `--detach` the command instead starts the host as a **detached run**, a process of its own
that outlives the command, and prints the run identity and the path of its result once the run's
progress file exists, then exits with status 0. Everything else about the run is the same: it
checks and records the task, writes its progress file and its result, and a refusal still becomes
its result. A caller that cannot wait for a long run in one command, such as a
[workflow step](../workflows/module.md#concept.workflows.step), starts it this way and reads the
result when it appears. A command line refused with status 2 starts nothing, detached or not.

<a id="concept.operations.no-task"></a>

An Operation whose catalog entry makes the task optional may also run **without a task**, from the
primary worktree only: it then works on the primary worktree, with the Modules `--modules` names,
begins no task record, admits only inputs of other runs without a task, and may launch only reading
workers, so it changes no Spec or code. Started without `--task` inside a task's worktree, it is
refused with `task_worktree_without_task`, which names the task to pass with `--task`: there it
must run as a run of that task, under the task's lock.

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
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, Specs withheld | `worker` | optional | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `scaffold` | [Adoption](adoption/module.md) | none | none | required | the surveyed Module's documents, the new child Modules' documents and the registry | a [scaffold record](adoption/contracts.md#contract.adoption.scaffold-record) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | required | Specs of the bound Modules and the registry mirror | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |
| `configure_workers` | Operations | none | none | optional | the worktree's untracked [worker model configuration](../agents/workers/module.md#concept.workers.model-configuration) | the [worker configuration](contracts.md#contract.operations.worker-configuration) |

A typical task runs `understand`, `specify` if needed, `implement`, `test` and the reviews, then
`validate` and `delivery`, repeating or skipping steps as the results tell it. Without a task the
main agent may run `understand` or a review to answer a question before any change is agreed, and
`configure_workers` when the developer asks to choose worker models. For a project whose code came
before its Specs, `survey`, `scaffold` and `code_to_spec` describe the code in Specs, usually run by
the [brownfield workflow](../workflows/module.md).

<a id="concept.operations.worker-role"></a>

A **worker role** names one worker an Operation launches: `spec_review` has a `reviewer` and a
`checker`, every other worker-backed Operation a single `worker`. The catalog lists the roles, and
the worker model configuration may choose a model per Operation and per role.

<a id="concept.operations.configure-workers"></a>

**`configure_workers`** lists and changes the model choices of the worker model configuration:
without a model or level it outputs the candidates a program offers, the file's entries for that
program and the effective backend, model and level of every worker role of every Operation;
`--model`, `--reasoning` or both set them for the default, for `--operation <op>` or for
`--role <role>` of it; `--unset` removes that entry. The program is `--backend`, otherwise the
backend the named role, Operation or default resolves to, so a change reaches the section the
worker actually reads. The file's `backend` section, which chooses a worker's program, is edited by
hand only. Without a task it changes the primary worktree's file, which the
tasks opened from then on inherit, and with `--task` only that task's copy. It checks the
Operation and role against the catalog and every model and level against the program's listing
(`--allow-unlisted` admits a model the listing cannot show), and launches no worker. Its exact
behaviour is in [the host](host.md#configure-workers). A plan is one answer
`understand` gives, not a separate Operation; a project's first Spec, Issues and task commands are
ordinary commands of their own Modules, not Operations.

<a id="concept.operations.result"></a>

Every run ends with one **Operation result**: the Operation, task, Modules, run and a summary, plus
`status` and the provider's `output`. `status` is `ok` when the Operation did what it promises,
`blocked` when it needs a main-agent decision, such as a reported Spec gap or stale readiness, and
`failed` when something went wrong: a launch error, a write outside the grant, checks still failing
after the last resume round, or a host error. A worker-backed Operation also carries the worker's
own [worker result](../agents/workers/module.md#concept.workers.worker-result) unchanged, plus the
host's evidence — grant, context identity, write audit, each check's exit code and log, resume
rounds used, transcript path, worker stderr. When `status` is not `ok`, `error` is the run's
[error chain](../vocabulary.md#concept.concorde.error-chain): the Operation's own link, describing
the error and why it cannot handle it, over the unchanged errors it received — Workers'
link for a worker run, the worker's own link, a failing check, or the concerned Git,
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
file](../agents/workers/module.md#concept.workers.progress-file) with the same process identifier,
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

### Its place in the five levels

Operations is level 4 of the [five levels](../module.md#the-five-levels), the lower of the two
program levels. It is called from above only: by whoever works the task level, the main agent
inside a task or a task session, with `concorde run`, or by a [workflow](../workflows/module.md)
(level 3) that the task level started and that runs each of its steps as the same command. It
calls only downward, into level 5: its host launches workers through Workers and runs checks
through Check execution, a Tool. The Operation result goes back up to the caller, and when the run
did not end `ok` its error chain goes with it, with the host's link on top of what level 5
reported. Nothing below calls back up: a worker never runs an Operation, and a Tool call returns
to the host step that made it.

```d2
main: Main session
tasksession: Task sessions
workflows: Workflows
operations: Operations {
  host: Operation host
}
workers: Workers
checks: Check execution
main -> workflows
main -> operations
tasksession -> workflows
tasksession -> operations
workflows -> operations
operations.host -> workers: launches workers through
operations.host -> checks: runs checks through
```

The picture draws the callers whose Modules declare that they use Operations: the main session,
which also plays the task level when it works a task itself, a task session, which plays it when
the main agent delegates a task, and Workflows. End-to-end testing's headless sessions also start
Operations, to exercise them, but they are no level of a project's work. Level 5 is two Modules
side by side, the agent half and the program half, and only the host reaches either: an Operation
reaches a worker only through Workers, and Workers itself calls Check execution between a worker's
rounds, so a failing check can drive a repair loop inside one Operation.

<a id="uses-workers"></a>

**Workers** is the agent half of level 5. A worker-backed Operation hands it the frozen grant,
the brief and the worker role, and Workers performs the standard worker sequence — settings,
launch, audit, resume rounds, run record — and returns the
[worker result](../agents/workers/module.md#concept.workers.worker-result) with the evidence it
gathered. The host relies on Workers launching the worker only under that grant, auditing every
write against it and keeping the worker's claims apart from what it measured. The host keeps the
worker result unchanged in the Operation result and decides what the outcome means for the
Operation. A launch error, a timeout or an audit violation ends the run `failed`, with Workers'
link as a cause of the host's own.

<a id="uses-checks"></a>

**Check execution** is the program half of level 5: the deterministic Tool that runs
[configured checks](../checks/module.md#concept.checks.configured-check) read-only, for the resume
rounds Workers drives and for deterministic providers such as Validation, returning each result's
command, exit code and log as host evidence. The host relies on a check never changing the
worktree it measures and on a result being refused as `stale_evidence` when its input changed
during the run. It passes the logs' directory in the run directory, keeps each check result as the
host's own evidence rather than a worker's claim, and ends the run `failed` when the check boundary
cannot be established or a check still fails after the last resume round, with the check's error or
log in the chain.

### Inside

The catalog lists the Operations; the host, which the Catalog and runner realization implements,
runs one of them per process and returns its result:

```d2
operations: Operations {
  runner: Catalog and runner {
    "src/concorde/operations/"
    "tests/concorde/operations/"
  }
  catalog: Operation catalog
  operation: Operation
  host: Operation host
  result: Operation result
  runner -> host: implements
  catalog -> operation: lists
  host -> operation: runs
  host -> result: returns
}
```

The catalog names each Operation's provider, and the runner loads that provider's steps; a
provider never loads the catalog. The host runs one Operation per process, launches its workers
only through Workers, records the run through Tasks and returns exactly one Operation result.

Each Operation's control flow is a step table in its provider's Spec, run as an ordered list of
Python steps until one stops the run. A worker-backed Operation follows the standard worker
sequence: compute the [grant](../spec-tooling/spec/module.md#concept.spec.grant) for the task type
and Modules from the **task worktree's** Specs and freeze it with its
[context identity](../spec-tooling/spec/module.md#concept.spec.context-identity), pre-create the
pending files it makes writable, generate the worker's settings, tools and
[brief](../agents/workers/module.md#concept.workers.brief), launch the worker, run the
[write audit](../agents/workers/module.md#concept.workers.audit), run the bound Modules'
[configured checks](../checks/module.md#concept.checks.configured-check) outside the
worker, feed failures back as a
[resume round](../agents/workers/module.md#concept.workers.resume-round) until they pass or the
rounds run out, and write the [run record](../agents/workers/module.md#concept.workers.run-record).
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
bounded by the Spec as it sees it (a run without a task reads the primary worktree); results and
run records still go to the primary's `.concorde/runs/`, so the main agent finds every run in one
place and nothing the host writes for itself ends up in a task's diff. One task runs at most one
Operation at a time — two hosts in one worktree would audit each other's writes as their own — so
parallelism comes from running tasks side by side.

The host writes a result in every case it can, including its own failures, and records the run in
the [task record](../tasks/module.md#concept.tasks.task-record) at start and end, since the caller
is woken only by the process exit and every problem must travel up as an
[error chain](../vocabulary.md#concept.concorde.error-chain) with evidence. No provider calls
another Operation: the task level or its Workflow decides which Operation runs next. This leaves
internal Tool calls and worker repair rounds within the current Operation. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.operations.runner"></a>

The **Catalog and runner** realization holds the catalog (`catalog.py`), the provider interface and
standard worker sequence (`provider.py`) and the step runner (`host.py`), tested against test
providers and a fake worker. The `concorde` command itself belongs to
[Distribution](../distribution/module.md), which hands `run` to this Module.

### The providers

Each Operation's behaviour lives with the Module that provides it: seven children of Operations and
Spec review, which lives in Spec tooling. A provider supplies its steps, its worker roles and the
contract of its output; the host runs those steps inside the standard sequence, checks the output
against its contract and wraps it in the Operation result. A provider relies on the host freezing
the grant, launching workers only through Workers and recording the run; the host relies on each
provider's steps staying within its catalog entry. A step that raises ends the run `failed` with
`host-error` evidence naming the exception and where it was raised, and an output its contract
refuses ends it `failed` with `invalid-output` evidence, each with the host's link on top. Delivery
reuses Validation's steps rather than judging readiness itself.

<a id="contains-understanding"></a>

**Understanding** provides `understand`: a worker reads the bound Modules' Specs and file names and
returns an assessment, changing nothing; its output is advice to the main agent, never an
instruction to the host. It may run without a task, which is how the main agent answers a question
before any change is agreed.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents,
including pending files, and the host validates the result. It is the only Operation that writes
Specs, so the main agent routes every Spec repair through it or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable, and the host runs their checks with
resume rounds until they pass or the rounds run out, so its result says whether the checks passed on
the changed code. In `test` a read-only worker interprets the checks the host ran and returns a test
report; the host's check results, not the worker's reading of them, are the evidence. Both need a
task.

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges the task's code change against the bound
Modules' Specs and returns findings and a verdict, changing nothing. The host prepares the change to
review from the task, or from `--base` when it runs without one, and keeps the verdict as the
worker's claim; acting on a finding is the task level's decision.

<a id="contains-validation"></a>

**Validation** provides `validate`, the deterministic Operation that decides whether the task
worktree is ready to deliver, binding that readiness to the inputs it examined. It launches no
worker. Delivery relies on it.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only Operation that runs Git commands that change the
repository, committing the task worktree's changes once readiness is current.

<a id="contains-adoption"></a>

**Adoption** provides `survey`, `scaffold` and `code_to_spec`, the only Operations that describe
existing code in Specs, for a project whose code came before them: a read-only survey proposes child
Modules, the host scaffolds them, and `code-to-spec` workers describe each Module's code. The
[brownfield workflow](../workflows/module.md) usually runs them in that order.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_review` from Spec tooling: reviewers read the bound Modules' Specs
and return findings and a verdict, listed in the catalog like a contained provider but living in
Spec tooling because it maintains Specs rather than changing a project. The host runs its
`reviewer` and `checker` roles like any other provider's workers and relies on it changing nothing;
its verdict stays the reviewers' claim.

### What the host relies on

Two Modules serve every run, whatever the provider: Spec core, which every level relies on, and
Tasks, which keeps the task's workspace.

<a id="uses-spec"></a>

**Spec core** loads the task worktree's Specs, resolves the named Modules, and computes each
worker's [grant](../spec-tooling/spec/module.md#concept.spec.grant) and
[context identity](../spec-tooling/spec/module.md#concept.spec.context-identity). The host relies on
it computing the same grant from the same Specs, and freezes that grant before any worker starts.
A Spec that cannot be loaded is refused rather than partially read, ending the run `failed`.

<a id="uses-tasks"></a>

**Tasks** resolves a task to its worktree and records each run in the task record at start and end.
The host relies on that record as the lock that keeps one Operation running per task, and on Tasks
refusing an unknown, closed or busy task before any step; such a refusal becomes a `failed` result
not recorded in the task, with the Tasks refusal as its cause. A run without a task uses none of
this and is refused with `task_worktree_without_task` when started inside a task's worktree.
