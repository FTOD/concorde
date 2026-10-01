# Execution

## Purpose

Execution is Concorde's execution core, the lower of its two halves: given one bound workspace, it
gets Spec-bounded work done there and returns checked results. It holds the workflows that order
that work, the Operations that combine AI workers with host logic, the execution commands that do
deterministic work such as deciding readiness and delivering, the workers themselves and Check
execution, which runs the project's checks for them. Everything in it learns what it works on from
one place, the [workspace binding](../glossary.json#concept.workspace-binding) in the worktree it
starts in, and records what it did as [trace nodes](../glossary.json#concept.trace-node) in the
workspace folder that binding names, its [run store](../glossary.json#concept.run-store).
Whoever prepares a workspace and reads those records relies on it: in Concorde that is the task
level of [Coordination](../coordination/module.md), which binds each task worktree and derives the
task's state from what Execution recorded.

Execution never opens, merges or closes a task, never reads or writes a
[task record](../glossary.json#concept.task-record), never switches branches and never asks the
developer anything; it does not know that tasks exist. It chooses no next step on its own: whoever
started a run, or the workflow that orders runs, decides what runs next.

## Core concepts

Execution rests on three ideas: a workspace that a binding file names, a run that works on it and
ends with one result, and the run store where every run is kept. It builds on the
[Operation](../glossary.json#concept.operation), the [grant](../glossary.json#concept.grant) and the
[error chain](../glossary.json#concept.error-chain) of other Modules.

### Workspaces

<a id="concept.workspace"></a><a id="concept.workspace-binding"></a>

A **workspace** exists once its **workspace binding** does. Whoever prepares it writes
`.concorde/workspace.json` at the worktree's root, as the
[binding contract](contracts.md#contract.execution.workspace-binding) defines: the workspace's
name, the absolute root it lies in, its goal, the Modules it works on, the branch and base commit it
works from, the **workspace folder** where its runs are traced and the `.concorde` directory whose
`locks/` holds its locks. In Concorde, [`concorde task open`](../coordination/tasks/module.md) writes
it into each new task worktree, naming the workspace after the task and placing the workspace folder
inside the task's own folder of the primary worktree, `.concorde/tasks/<task>/workspace/`, so that a
task's [trace](../glossary.json#concept.trace) holds every run of its workspace. Execution never
learns that the folder belongs to a task: another preparer may place it anywhere. Git ignores the
file. Execution reads it and never writes it; a binding that breaks its contract, or that names a
root other than the worktree it lies in, is refused rather than trusted, since a copied binding
would bind the wrong workspace.

<a id="concept.workspace-lock"></a>

A bound run holds the **[workspace lock](../glossary.json#concept.workspace-lock)** from before its
admission until after its result is written, so a workspace runs one run at a time: a second run
started while the first holds it is refused with `workspace_busy`, naming the run that holds it, or
waits for it with `--wait` ([Waiting for a busy workspace](#waiting-for-a-busy-workspace)). The lock
is a file under `locks/workspaces/` of the binding's `.concorde`, apart from every record and
outside the workspace, so a run that only reads the workspace leaves it untouched.

### Runs and their results

<a id="concept.run"></a>

A **run** is one execution of an Operation or of an execution command in one worktree. An
[Operation](../glossary.json#concept.operation) launches AI workers under a
[grant](../glossary.json#concept.grant), the per-path access list its
[task type](../glossary.json#concept.task-type) assigns, computed from the workspace's Specs; the
catalog of [Operations](operations/module.md) lists them. An
[execution command](../glossary.json#concept.execution-command) is deterministic and launches no
worker: [`task-validation`](commands/validation/module.md) decides whether the workspace is ready to
deliver, [`delivery`](commands/delivery/module.md) decides that readiness again and commits the
workspace, and [`scaffold`](commands/scaffold/module.md) creates the child Modules a survey proposed;
the catalog of [Commands](commands/module.md) lists them. Both kinds are **runs**: the same runner
parses their command line, resolves the workspace, takes the workspace lock, runs their steps and
writes one run result, so a workflow, the task level or an observer treats them alike.

<a id="concept.execution-runner"></a>

The **Execution runner** is that runner: the deterministic process that runs one run, an
Operation's or an execution command's, from its command line to its written result, and launches
workers only through the steps that ask for them. [The life of a run](#the-life-of-a-run) shows its
steps.

<a id="concept.run-result"></a>

Every run ends with one **[run result](../glossary.json#concept.run-result)**: its kind (`operation` or `command`), name, workspace,
Modules, run identity, status, summary and output. `status` is `ok` when the run did what it
promises, `blocked` when it needs a decision above it, such as a reported
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

### Unbound runs

<a id="concept.unbound-run"></a>

An Operation whose catalog entry allows it may also run
**[unbound](../glossary.json#concept.unbound-run)**, in a worktree without a binding such as the
primary worktree: `understand`, `survey`, `spec_review`, `spec_panel` and `code_review` (a change
review with `--base`, a Module review without). It works with the Modules `--modules` names,
records `workspace` null, admits only unbound inputs, takes no workspace lock, having no workspace
to lock, though it takes its run lock like every run, and may launch only reading workers, so it
changes no [Spec](../glossary.json#concept.spec) or code. Every other Operation and every execution
command is refused unbound with `binding_required`.

<a id="concept.unbound-checkout"></a>

An unbound run never works in the worktree it starts in. The runner checks out that worktree's
`HEAD` detached in a private temporary directory, the
**[unbound checkout](../glossary.json#concept.unbound-checkout)**, where the run's steps and workers
work, and removes it before it writes the result, which names the commit examined as `commit`. What
the run examines is that commit, never uncommitted changes; [Running unbound](#running-unbound)
says what else the checkout holds.

### Long runs

<a id="concept.detached-run"></a><a id="concept.run-progress-file"></a><a id="concept.run-lock"></a>

With `--detach` the command starts the runner as a
**[detached run](../glossary.json#concept.detached-run)**, a process of its own that outlives the
command, and prints the run identity and the path of its result as soon as the run's
**[run progress file](../glossary.json#concept.run-progress-file)** exists; everything else about
the run is the same. The run progress file names what runs, in which workspace and step, and the
**[run lock](../glossary.json#concept.run-lock)**, `locks/runs/<run-id>.lock`, tells whether the
runner still lives. [Following a long run](#following-a-long-run) explains how an observer uses
both.

<a id="detached-namespace"></a>

**A detached run lives only as long as the PID namespace it started in.** The runner is a new
session and process group, which frees it from the command and its terminal, but no process leaves
the PID namespace it was started in, and when the first process of a PID namespace ends, the kernel
kills every other one in it at once. Claude Code's Bash sandbox runs every call of a session's Bash
tool, foreground or background, in a PID namespace of its own whose first process is the sandbox's
own wrapper around the call's shell: the call's namespace ends when its command ends. So a runner
detached from a sandboxed Bash call is killed, without a word, when that call returns, and leaves a
run with no result whose run lock nobody holds; the same holds for any process that call started.
A sandboxed command cannot hand the run to a process outside either, since the sandbox refuses it
even Unix sockets. Whoever needs a run to outlive a sandboxed call starts it from a process outside
the sandbox, as a [workflow step](../glossary.json#concept.workflow-step) does through the
[project MCP server](../glossary.json#concept.project-mcp-server)
([Workflows](workflows/module.md#steps-in-claude-code)), or keeps the call alive as long as the run.
Which callers those are is not Execution's to say: a worker's Bash is sandboxed on the Claude Code
backend ([req.workers.bash-sandbox](workers/launch.md#req.workers.bash-sandbox)) and a
[main agent](../glossary.json#concept.main-agent)'s own session may be, while a
[task session](../glossary.json#concept.task-session)'s calls are not
([req.task-session.no-sandbox](../coordination/task-session/requirements.md#req.task-session.no-sandbox)),
so no namespace of theirs ends with them; a task session starts its runs in background Bash rather
than detached all the same, because Claude Code may end the processes of a call that returned.
Execution itself does not see which namespace it was started in and promises no more than this.

### The run store

<a id="concept.run-store"></a>

Every run is a [trace node](../glossary.json#concept.trace-node) of
[Tracing](../tracing/module.md): a folder with its `trace.json`, its
[run progress file](../glossary.json#concept.run-progress-file), its result and, below it, the nodes
of the checks it ran and of the worker runs it launched, each worker run with its
[run record](../glossary.json#concept.run-record) and rounds. The **run store** is where those
folders lie: a run started directly lies in `runs/<run-id>/` of the workspace folder, a run a
[workflow step](../glossary.json#concept.workflow-step) started inside that step's node of
[Workflows](workflows/module.md)' workflow node in the same folder, and an unbound run in
`.concorde/unbound/<run-id>/` of the worktree it started in, never in its checkout. A bound run that
does not hold its workspace's lock yet lies in the lobby, `.concorde/lobby/<run-id>/` of the
`.concorde` its binding names, and stays there when it is refused before it holds it, so that
nothing is written into a workspace folder by a run that has not entered it. Git ignores all of
them. Whoever prepared a workspace reads its runs in its workspace folder, and the runs waiting in
the lobby for its lock, to know what happened in it, and `concorde trace` finds any run by its
identity.

## Overview

Three pictures give the whole of Execution: the seam through which the upper half reaches it, the
children that carry its levels of work, and the life of one run.

### One narrow seam

The upper half of Concorde decides what to work on and in which workspace; this half does the work.
Execution keeps the two apart with one narrow seam: a file the upper half writes and Execution only
reads, the binding, and records Execution writes and the upper half only reads, the run store and
the [delivery commits](../glossary.json#concept.delivery-commit). Nothing in Execution imports or
writes the task store, so a change of how tasks are managed, parallelized or merged never reaches
the code that bounds, launches and checks workers, and the execution core can run in any workspace
someone prepared, not only in a task.

```d2 illustrative
direction: right
preparer: "Whoever prepares the workspace\n(in Concorde, the task level)"
binding: "Workspace binding\n.concorde/workspace.json"
execution: "Execution\nin the bound workspace"
records: "Run store and\ndelivery commits"
preparer -> binding: writes
binding -> execution: is read by
execution -> records: writes
records -> preparer: are read by
```

[Why a binding file](#why-a-binding-file) explains what the binding holds and what it leaves to the
records.

### Five children

Execution is the composition of five children. Workflows is level 3 of Concorde's
[levels of work](../module.md#the-levels-of-work); level 4, the runs, has an AI half, Operations,
and a deterministic half, Commands; Workers manages level 5, the workers. Check execution is no
level: it is a service the runs' steps and the Workers host code call in-process.

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

A run is something the task level or a workflow starts and waits for, and its result is recorded;
a worker or a service is started or called by a run's step and answers only to that step. So
deterministic work that is taken and recorded as a step of its own is an execution command, and
deterministic work that a step calls is a service. [The children](#the-children) explains each
child's part.

### The life of a run

The Execution runner runs one run per process. It parses the command line, reads the binding,
creates the run's trace node, in the lobby for a bound run, and takes its run lock, takes the
workspace lock for a bound run, checks that the workspace was not retired meanwhile and moves the
node into the workspace folder, or checks out the worktree's `HEAD` for an unbound one, checks the
Modules and inputs, runs the
definition's steps in their declared order until one stops the run, removes an unbound run's
checkout, composes the run result, checks it against its contract and, when it is `ok`, the
definition's output contract, and writes it while it still holds the lock, so that a run that takes
the lock after it finds that result written, and writes its trace node again with its end.
Seeing the result alone does not tell that the workspace is free: the runner may still hold
the lock.
A refusal before the steps, a step that raises, a signal or an invalid result each still end in a
written result with the runner's link on top. Its exact behaviour is in
[How a run is executed](runner.md).

```d2 illustrative
direction: down
parse: "Parse the command line"
bind: "Read the workspace binding"
node: "Create the run's trace node\n(in the lobby when bound),\ntake its run lock"
lock: "Take the workspace lock\n(or wait for it with --wait)"
enter: "Check the binding again,\nmove the node into\nthe workspace folder"
checkout: "Check out HEAD detached:\nthe unbound checkout"
admit: "Check the Modules and inputs"
work: "Run the definition's steps in order\nuntil one stops the run"
remove: "Remove the unbound checkout"
compose: "Compose the run result, check it\nagainst its contract and,\nwhen ok, the output contract"
write: "Write the result\nwhile still holding the lock"
end: "Write the trace node's end"
parse -> bind -> node
node -> lock: bound
node -> checkout: unbound
lock -> enter -> admit
checkout -> admit
admit -> work
work -> compose: bound
work -> remove: unbound
remove -> compose
compose -> write -> end
lock -> compose: "busy: workspace_busy" {style.stroke-dash: 3}
enter -> compose: "retired: workspace_retired" {style.stroke-dash: 3}
admit -> compose: "refused: the runner's link on top" {style.stroke-dash: 3}
```

A step that raises, a signal or an invalid result takes the same dashed way: the run still ends in a
written result with the runner's link on top, and an unbound run's checkout is removed first.

## Running work

Inside a bound workspace, every run works on that workspace without naming it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [operation arguments]
concorde task-validation [--modules …] [--input …] [--detach] [--wait <s>]
concorde delivery        [--adoption] [--detach] [--wait <s>]
concorde scaffold        --input <survey run> [--detach] [--wait <s>]
```

`--modules` names the Modules the run works on (default: the binding's, less any the workspace no
longer registers); `--input` admits the output of an earlier `ok` run of the same workspace, such
as a plan or a survey. `concorde workflow step|report …` also works on the bound workspace without
naming it, but is not itself a run: it starts and awaits runs through
[Workflows](workflows/module.md).

A run of `implement` in a task worktree, for example, reads the binding (workspace `retry`,
[Module](../glossary.json#concept.module) `module.http`, base `4be1…`), takes the lock of `retry`,
computes the implement grant for `module.http` from the worktree's Specs, launches one worker
through [Workers](workers/module.md), audits and checks its change, and prints its run result and
saves it in the run's trace node, `<workspace folder>/runs/<run-id>/result.json`. The command exits
0 for `ok`, 1 for `blocked` or `failed`, and 2 for a malformed command line, which starts nothing.

### Waiting for a busy workspace

A [workflow step](../glossary.json#concept.workflow-step) waits for the workspace lock to be free
before it starts its run. `--wait <seconds>` queues any run instead: the runner waits for the lock
inside its own process, its run progress file naming the run it waits for, starts the moment that
run ends, and is refused with `workspace_busy` only when the lock is still held after that many
seconds. A caller that wants a `delivery` after an `implement` thus asks once, and never polls the
lock. The run waits in the lobby, outside the workspace folder, and enters the workspace only once
it holds the lock and finds the binding it started from unchanged: a task closed meanwhile has
removed the binding and, holding the lock, its lock file, and the run is refused with
`workspace_retired` in the lobby instead of writing into the folder the close moved to the
history. The lock is a file lock held by the runner's process, so the kernel releases it however the
run ends. The runner writes a run's result before it releases the lock, so a run admitted after it
finds that result written, unless the runner was killed before it could write one and the run is
lost; a result on disk, though, does not mean the lock is free yet.

### Running unbound

Main sessions merge tasks into the primary worktree while an unbound run lasts, and since the run
reads, and Workers audits, only its checkout, such a merge can neither change what the run reads
nor make a worker's audit fail. The run is still recorded in the worktree it started in, in
`.concorde/unbound/<run-id>/`, a trace of its own, while its workers' backends and models come from
the [worker configuration](../glossary.json#concept.worker-configuration) committed in the checkout,
like every other input of the run. The environments the project configuration names as runtime
paths and Git ignores, such as `.venv` and `node_modules`, are linked from that worktree into the
checkout, so the checks a review runs there find them, and submodules it has checked out are checked
out in the checkout too. However the run ends, the runner removes the checkout before it writes the
result.

### Following a long run

While a run lives, its run progress file names what runs, in which workspace and step, with the
runner's process identifier, and every worker run it launches records the run's identity, so an
observer, such as a workflow step or the run state of a task, follows a run and its worker without
asking the runner. Whether the runner still lives is told by its run lock, which the runner locks
from before its first run progress file until after its result and removes as it exits, and that
the kernel releases however the runner ends: a run without a result whose run lock nobody holds
ended without writing one. No observer decides it by the recorded process identifier, which is only
meaningful in the PID namespace the runner ran in: a runner started in a sandboxed shell may record
2, a number that names an unrelated, living process on the host.

## How it is built

### Why a binding file

A run needs five facts about its workspace: which Modules it works on, which branch it may commit
on, which commit its changes are measured from, the goal a worker is briefed with, and where its
traces and locks go. Asking every caller to pass them on every command line would make each command
long and easy to get wrong, and would let two runs in the same workspace disagree on its base.
Asking the task store for them would tie the execution core to tasks. A file in the workspace,
written once when the workspace is prepared, gives every run the same facts from where it already
is, and confines the knowledge of tasks to whoever writes the file. The file names its own root so
that a copy in another worktree is refused, and it lives beside the workspace's other Git-ignored
Concorde state so that it never enters a commit.

Some state is deliberately not in the binding. The binding never records what a run did: which
runs happened, whether the workspace was delivered, which workflow runs in it. Those facts are the
traces themselves, read where they are, so there is no second copy that could disagree. The binding
names the workspace folder rather than letting Execution derive it, so that the preparer decides
where a workspace's traces belong; Coordination places them inside the task, which is how a task's
trace reaches its runs without anything in Execution naming the task.

### Why commands are runs

An Operation exists to combine AI workers with host logic that checks them. Deciding readiness,
delivering and scaffolding need no model, so they are not Operations; but a workflow must be able to
take them as steps, and a caller must be able to wait for them, read their evidence and receive
their error chain like any Operation's. Running execution commands with the same runner gives them all of that without the
[Operation catalog](../glossary.json#concept.operation-catalog) or any worker machinery: the only
difference a caller sees is the result's `kind` and the error link's level, `command` instead of
`operation`. Being a run is also what tells an execution command from a deterministic service such
as [Check execution](checks/module.md): a service is called by a run's step and answers it, while an
execution command is itself the run, with a workspace, a lock and a recorded result.

### Why an unbound run works in a checkout

The primary worktree is where main sessions merge delivered tasks, and several may do so while an
unbound review of it is still running. A run that read the primary worktree directly would see the
Specs and the code it reads change under its workers, and Workers' audit, which compares `HEAD` and
the index before and after each round, would report the merge as the worker's own write. Locking the
primary worktree against merges for a review's whole life would stall every other session, and
tolerating changes would make the audit meaningless. A checkout of one commit gives the run a fixed
input that no other session touches, and naming that commit in the result tells the caller exactly
what was examined. The checkout is Git's own linked worktree (`git worktree add --detach`), which
shares the repository's objects, so it costs no clone and needs no copying code; it lives outside
the project in a private temporary directory, and the runner removes it through Git again. What a
commit never holds, the environments Git ignores and the checkouts of submodules, comes from the
worktree the run started in: the environments linked, since the run only reads them, and each
submodule checked out from its own repository at the commit the checkout records.

### The runner and run store

<a id="realization.execution.runner"></a>

The **Runner and run store** realization binds the binding reader, the run store, the unbound
checkout, the run context and definitions that steps work with and the runner itself, with their
tests; the runner finds an execution command by name in the catalog of
[Commands](commands/module.md). The `concorde` command belongs to
[Distribution](../distribution/module.md), which hands `run`, the execution commands and `workflow`
to this Module's parts.

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
  checkout: Unbound checkout
  runner -> binding: reads
  runner -> lock: holds for each bound run
  runner -> checkout: works in for each unbound run
  runner -> result: writes
  store -> result: keeps
}
```

## The children

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
workspace's changes on the bound branch; and Scaffold's `scaffold`, which
creates the child Modules a survey proposed. The runner runs their steps like an Operation's.

<a id="contains-workers"></a>

**Workers** runs one headless worker under a frozen grant for the Operation that asked, audits it,
runs its checks and records the worker run in the run store, and owns the tracked worker
configuration.

<a id="contains-checks"></a>

**Check execution** runs the project's
[configured checks](../glossary.json#concept.configured-check) in a read-only boundary and returns
each result with its log. Operations' steps, execution commands' steps and the Workers host code
call it in-process; it starts no run and no worker.

## What Execution relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, so the runner can check that the named Modules are
registered and leave out the binding's Modules the workspace no longer registers. The runner
relies on it refusing Specs that cannot be loaded rather than reading them in part; a run then ends
`failed` with `specs_unloadable`, unless its definition diagnoses the Specs itself, as
`task-validation` and `delivery` do.

<a id="uses-tracing"></a>

**Tracing** gives every run its trace node's shape and place and every lock its file: the runner
writes the run's node at its start and its end through Tracing's library, takes the run lock and the
workspace lock under `locks/`, and reports its errors in the error contract. Execution relies on the
[node contract](../tracing/contracts.md#contract.tracing.node), the
[layout](../tracing/contracts.md#layout) and the [locks](../tracing/contracts.md#locks), and
records nothing that Tracing's node contract refuses.

Execution relies on no Module of the upper half. The task level of Coordination uses it: it writes
the binding and reads the run store and the delivery commits, as its own Spec explains.
