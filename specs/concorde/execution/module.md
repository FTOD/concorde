# Execution

## Purpose

Execution is Concorde's execution core, the lower of its two halves: given one bound workspace, it
gets Spec-bounded work done there and returns checked results. It holds the workflows that order
that work, the Operations that combine AI workers with host logic, the execution commands that do
deterministic work such as deciding readiness and delivering, the workers themselves and Check
execution, which runs the project's checks for them. Everything in it learns what it works on from
one place, the [workspace binding](../glossary.json#concept.workspace-binding) in the worktree it
starts in, and records what it did in its own [run store](../glossary.json#concept.run-store).
Whoever prepares a workspace and reads those records relies on it: in Concorde that is the task
level of [Coordination](../coordination/module.md), which binds each task worktree and derives the
task's state from what Execution recorded.

Execution never opens, merges or closes a task, never reads or writes a
[task record](../glossary.json#concept.task-record), never switches branches and never asks the
developer anything; it does not know that tasks exist. It chooses no next step on its own: whoever
started a run, or the workflow that orders runs, decides what runs next.

## Usage

<a id="concept.workspace"></a><a id="concept.workspace-binding"></a>

**Binding a workspace.** A **workspace** exists once its **workspace binding** does. Whoever
prepares it writes `.concorde/workspace.json` at the worktree's root, as the
[binding contract](contracts.md#contract.execution.workspace-binding) defines: the workspace's
name, the absolute root it lies in, its goal, the Modules it works on, the branch and base commit it
works from, and the records directory where its runs are kept. In Concorde,
[`concorde task open`](../coordination/tasks/module.md) writes it into each new task worktree,
naming the workspace after the task and pointing the records directory at the primary worktree's
`.concorde`, so that the runs of every task are found in one place. Git ignores the file. Execution
reads it and never writes it; a binding that breaks its contract, or that names a root other than
the worktree it lies in, is refused rather than trusted, since a copied binding would bind the
wrong workspace.

<a id="concept.run"></a>

**Running work.** Inside a bound workspace, every run works on that workspace without naming it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [operation arguments]
concorde task-validation [--modules …] [--input …] [--detach]
concorde delivery        [--adoption] [--detach]
concorde scaffold        --input <survey run> [--detach]
concorde workflow step|report …
```

An [Operation](../glossary.json#concept.operation) launches AI workers under a grant computed from
the workspace's Specs; the catalog of [Operations](operations/module.md) lists them. An
[execution command](../glossary.json#concept.execution-command) is deterministic and launches no
worker: [`task-validation`](commands/validation/module.md) decides whether the workspace is ready to
deliver, [`delivery`](commands/delivery/module.md) validates it again and commits it with its
evidence, and [`scaffold`](commands/scaffold/module.md) creates the child Modules a survey proposed;
the catalog of [Commands](commands/module.md) lists them. Both kinds are **runs**: the same runner
parses their command line, resolves the workspace, takes the
[workspace lock](../glossary.json#concept.workspace-lock), runs their steps and writes one
[run result](../glossary.json#concept.run-result), so a workflow, the task level or an observer
treats them alike. `--modules` names the Modules the run works on (default: the binding's, less any
the workspace no longer registers); `--input` admits the output of an earlier `ok` run of the same
workspace, such as a plan or a survey.

A run of `implement` in a task worktree, for example, reads the binding (workspace `retry`,
[Module](../glossary.json#concept.module) `module.http`, base `4be1…`), takes the lock of `retry`,
computes the implement grant for `module.http` from the worktree's Specs, launches one worker
through [Workers](workers/module.md), audits and checks its change, and prints and saves its run
result as `<records>/runs/<run-id>/result.json`. The command exits 0 for `ok`, 1 for `blocked` or
`failed`, and 2 for a malformed command line, which starts nothing.

<a id="concept.run-result"></a>

**Reading the result.** Every run ends with one **run result**: its kind (`operation` or `command`),
name, workspace, Modules, run identity, status, summary and output. `status` is `ok` when the run
did what it promises, `blocked` when it needs a decision above it, such as a reported
[Spec gap](../glossary.json#concept.spec-gap) or a workspace that is not ready, and `failed` when
something went wrong: a refusal, a write outside the grant, checks still failing after the last
[resume round](../glossary.json#concept.resume-round), a Git refusal or a runner error. A
worker-backed run also carries the worker's own
[worker result](../glossary.json#concept.worker-result) unchanged, beside the runner's own evidence,
so a caller always tells what the runner observed from what a worker claims. When `status` is not
`ok`, `error` is the run's [error chain](../glossary.json#concept.error-chain), the run's own link
over the unchanged errors it received. The
[run result contract](contracts.md#contract.execution.run-result) defines the envelope and
[How a run is executed](runner.md) how the runner fills it.

<a id="concept.workspace-lock"></a>

**One run at a time.** A bound run holds the **workspace lock** for its whole life. A second run
started in the same workspace while the first holds it is refused with `workspace_busy`, naming the
run that holds it, and a [workflow step](../glossary.json#concept.workflow-step) waits for the
lock to be free before it starts its run. The kernel releases the lock however the run ends. The
lock lies in the run store, not in the workspace, so a run that only reads the workspace
leaves it untouched.

<a id="concept.unbound-run"></a>

**[Unbound runs](../glossary.json#concept.unbound-run).** An Operation whose catalog entry allows it
may also run **unbound**, in a worktree without a binding such as the primary worktree:
`understand`, `survey`, `spec_review`, `spec_panel` and `code_review` (with `--base`). It works on
that worktree with the Modules `--modules` names, records `workspace` null, admits only unbound
inputs, takes no lock and may launch only reading workers, so it changes no
[Spec](../glossary.json#concept.spec) or code. Every other Operation and every execution command is
refused unbound with `binding_required`.

<a id="concept.detached-run"></a><a id="concept.run-progress-file"></a>

**Long runs.** With `--detach` the command starts the runner as a
**[detached run](../glossary.json#concept.detached-run)**, a process of its own that outlives the
command, and prints the run identity and the path of its result as soon as the run's
**[run progress file](../glossary.json#concept.run-progress-file)** exists. Everything else about
the run is the same, including a refusal, which still becomes its result. While a run lives, its run
progress file names what runs, in which workspace and step, with the runner's process identifier,
which every worker run it launches records too, so an observer such as the main session's
[run view](../glossary.json#concept.run-view) follows a run and its worker without asking the
runner.

<a id="concept.run-store"></a>

**Where runs are kept.** The **run store** is the `runs/` directory of the records directory: each
run's directory with its [progress file](../glossary.json#concept.progress-file) and result, the
[run records](../glossary.json#concept.run-record) of the workers it launched, and
[Workflows](workflows/module.md)' own records under `runs/workflows/`. A bound run records in the
directory its binding names; an unbound run in its own worktree's `.concorde`. The store is ignored
by Git. Whoever prepared a workspace reads its runs there, by the workspace's name, to know what
happened in it.

## Design

The upper half of Concorde decides what to work on and in which workspace; this half does the work.
Execution keeps the two apart with one narrow seam: a file the upper half writes and Execution only
reads, the binding, and records Execution writes and the upper half only reads, the run store and
the [delivery commits](../glossary.json#concept.delivery-commit). Nothing in Execution imports or
writes the task store, so a change of how tasks are managed, parallelized or merged never reaches
the code that bounds, launches and checks workers, and the execution core can run in any workspace
someone prepared, not only in a task.

### Why a binding file

A run needs five facts about its workspace: which Modules it works on, which branch it may commit
on, which commit its changes are measured from, the goal a worker is briefed with, and where to
record. Asking every caller to pass them on every command line would make each command long and
easy to get wrong, and would let two runs in the same workspace disagree on its base. Asking the
task store for them would tie the execution core to tasks. A file in the workspace, written once
when the workspace is prepared, gives every run the same facts from where it already is, and
confines the knowledge of tasks to whoever writes the file. The file names its own root so that a
copy in another worktree is refused, and it lives beside the workspace's other Git-ignored
Concorde state so that it never enters a commit.

Some state is deliberately not in the binding. The binding never records what a run did: which
runs happened, whether the workspace was delivered, which workflow runs in it. Those facts are the
records themselves, read where they are, so there is no second copy that could disagree.

### Why commands are runs

An Operation exists to combine AI workers with host logic that checks them. Deciding readiness,
delivering and scaffolding need no model, so they are not Operations; but a workflow must be able to
take them as steps, delivery must cite the run that decided the readiness it committed, and a caller
must be able to wait for them, read their evidence and receive their error chain like any
Operation's. Running execution commands with the same runner gives them all of that without the
[Operation catalog](../glossary.json#concept.operation-catalog) or any worker machinery: the only
difference a caller sees is the result's `kind` and the error link's level, `command` instead of
`operation`. Being a run is also what tells an execution command from a deterministic service such
as [Check execution](checks/module.md): a service is called by a run's step and answers it, while an
execution command is itself the run, with a workspace, a lock and a recorded result.

### The runner

<a id="concept.execution-runner"></a><a id="realization.execution.runner"></a>

The **Execution runner** runs one run per process. It parses the command line, reads the binding,
takes the workspace lock for a bound run, checks the Modules and inputs, runs the definition's
steps in their declared order until one stops the run, composes the run result, checks it against
its contract and the definition's output contract, and writes it while it still holds the lock, so
that whoever sees the result never finds the workspace busy with that run. A refusal before the
steps, a step that raises, a signal or an invalid result each still end in a written result with
the runner's link on top. Its exact behaviour is in [How a run is executed](runner.md).

The **Runner and run store** realization binds the binding reader, the run store, the run context
and definitions that steps work with and the runner itself, with their tests; the runner finds an
execution command by name in the catalog of [Commands](commands/module.md). The `concorde` command
belongs to [Distribution](../distribution/module.md), which hands `run`, the execution commands and
`workflow` to this Module's parts.

```d2
execution: Execution {
  runner: Runner and run store {
    "src/concorde/execution/"
    "tests/concorde/execution/"
  }
  binding: Workspace binding
  result: Run result
  lock: Workspace lock
  store: Run store
  runner -> binding: reads
  runner -> lock: holds for each bound run
  runner -> result: writes
  store -> result: keeps
}
```

### The children

Execution is the composition of five children. Workflows is level 3 of Concorde's
[levels of work](../module.md#the-levels-of-work); level 4, the runs, has an AI half, Operations,
and a deterministic half, Commands; Workers manages level 5, the workers. Check execution is no
level: it is a service the runs' steps and the Workers host code call in-process.

A run is something the task level or a workflow starts and waits for, and its result is recorded;
a worker or a service is started or called by a run's step and answers only to that step. So
deterministic work that is taken and cited as a step of its own is an execution command, and
deterministic work that a step calls is a service.

```d2 illustrative
execution: Execution {
  workflows: Workflows
  operations: Operations
  commands: Commands
  workers: Workers
  checks: Check execution
  workflows -> operations: runs
  workflows -> commands: runs
  operations -> workers: launches workers through
  operations -> checks: runs checks through
  commands -> checks: runs checks through
  workers -> checks: runs checks through
}
```

<a id="contains-workflows"></a>

**Workflows** orders one workspace's runs for a known procedure, such as describing existing code,
and handles their [decision points](../glossary.json#concept.decision-point). Each step is an
ordinary run of this runner, started detached and awaited; the workflow keeps its own record in the
run store and never reaches into a task.

<a id="contains-operations"></a>

**Operations** holds the catalog of Operations and their providers. Each Operation combines host
steps with workers launched through Workers and calls of Check execution; the runner runs its
steps like any other definition's.

<a id="contains-commands"></a>

**Commands** holds the catalog of execution commands and their Modules: Validation's
`task-validation`, which decides whether the bound workspace is ready to deliver; Delivery's
`delivery`, the only run that commits, which decides the readiness again and commits the
workspace's changes with their evidence on the bound branch; and Scaffold's `scaffold`, which
creates the child Modules a survey proposed. The runner runs their steps like an Operation's.

<a id="contains-workers"></a>

**Workers** runs one headless worker under a frozen grant for the Operation that asked, audits it,
runs its checks and records the worker run in the run store, and owns the worker model
configuration and the `configure-workers` command that changes it.

<a id="contains-checks"></a>

**Check execution** runs the project's
[configured checks](../glossary.json#concept.configured-check) in a read-only boundary and returns
each result with its log. Operations' steps, execution commands' steps and the Workers host code
call it in-process; it starts no run and no worker.

### What Execution relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, so the runner can check that the named Modules are
registered and leave out the binding's Modules the workspace no longer registers. The runner
relies on it refusing Specs that cannot be loaded rather than reading them in part; a run then ends
`failed` with `specs_unloadable`, unless its definition diagnoses the Specs itself, as
`task-validation` and `delivery` do.

Execution relies on no Module of the upper half. The task level of Coordination uses it: it writes
the binding and reads the run store and the delivery commits, as its own Spec explains.
