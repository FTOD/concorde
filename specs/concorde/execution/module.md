# Execution

## Purpose

Execution is the execution [part](../glossary.json#concept.part): given one bound
[workspace](../glossary.json#concept.workspace), it runs work there and returns checked results. It
runs [Operations](../glossary.json#concept.operation), whose steps combine AI workers with host
logic, and [execution commands](../glossary.json#concept.execution-command), which do deterministic
work such as deciding readiness and delivering, both from the definitions the installed parts
register; and it provides Check execution, which runs the project's checks for those steps.
Everything in it learns what it works on from one place, the
[workspace binding](../glossary.json#concept.workspace-binding) in the worktree it starts in, and
records what it did as [trace nodes](../glossary.json#concept.trace-node) in the workspace folder
that binding names, its [run store](../glossary.json#concept.run-store). Whoever prepares a
workspace and reads those records relies on it: in Concorde that is the task level of
[Coordination](../coordination/module.md), which binds each task worktree and derives the task's
state from what Execution recorded. What a run does is its definition's: in Concorde,
[Method](../method/module.md) registers the Operations and commands of Concorde's way of working, and
[Workflows](../workflows/module.md) orders runs for a known procedure.

Execution never opens, merges or closes a task, never reads or writes a
[task record](../glossary.json#concept.task-record), never switches branches and never asks the
developer anything; it does not know that tasks exist. It reads no
[Spec](../glossary.json#concept.spec), computes no grant and launches no worker itself: a
definition's steps do whatever needs the Specs or a worker, through the parts they depend on. It
chooses no next step on its own: whoever started a run, or the workflow that orders runs, decides
what runs next. It depends on the kernel part alone.

## Core concepts

Execution rests on three ideas: a run that works on a workspace and ends with one result, the
definitions that say what a run does, and the run store where every run is kept. It builds on the
Kernel's [workspace](../glossary.json#concept.workspace), whose
[binding](../glossary.json#concept.workspace-binding) it reads and whose
[workspace lock](../glossary.json#concept.workspace-lock) each bound run holds, and on Tracing's
[trace node](../glossary.json#concept.trace-node) and
[error chain](../glossary.json#concept.error-chain).

### Runs and their definitions

<a id="concept.run"></a>

A **run** is one execution of an Operation or of an execution command in one worktree. An
[Operation](../glossary.json#concept.operation) is a definition whose steps launch AI workers; the
[Operation catalog](../glossary.json#concept.operation-catalog) of [Operations](operations/module.md)
lists the ones the installed parts register. An
[execution command](../glossary.json#concept.execution-command) is a definition whose steps are
deterministic and launch no worker, such as Method's `task-validation`, `delivery` and `scaffold`;
the catalog of [Commands](commands/module.md) lists them. Both kinds are **runs**: the same runner
parses their command line, resolves the workspace, takes the workspace lock, runs their steps and
writes one run result, so a workflow, the task level or an observer treats them alike. The
Operation or execution command a run names is the run's **definition**: it supplies the steps the
runner runs, the arguments they take, whether the run may be unbound, the runtime paths an unbound
run's checkout links, and the contract its output must satisfy.

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

The [Modules](../glossary.json#concept.module) a run works on are, for the runner, names: the ones
`--modules` gives, or else the binding's. A definition whose steps read the Specs checks them in its
own admission, as Method's do through the Spec tooling, leaving out the binding's Modules the
workspace no longer registers and refusing a named one it does not; a definition that reads no Spec
takes them as labels.

### Unbound runs

<a id="concept.unbound-run"></a>

A definition that allows it may also run
**[unbound](../glossary.json#concept.unbound-run)**, in a worktree without a binding such as the
primary worktree; in Concorde these are Method's reading Operations `understand`, `survey`,
`spec_review`, `spec_panel` and `code_review`. It works with the Modules `--modules` names, records
`workspace` null, admits only unbound inputs, takes no workspace lock, having no workspace to lock,
though it takes its run lock like every run, and may launch only reading workers, so it changes no
Spec or code. The one lasting change it may make besides its own record is publishing
[Issues](../glossary.json#concept.issue), as a Spec or code review reports its findings where the
issues part is installed: only through the [Issues](../issues/module.md) store, which commits each on
the primary branch as a commit of its own under the
[merge lock](../glossary.json#concept.merge-lock), never through the checkout it examines
([req.execution.unbound-origin-untouched](requirements.md#req.execution.unbound-origin-untouched)).
Every other definition is refused unbound with `binding_required`.

<a id="concept.unbound-checkout"></a>

An unbound run never works in the worktree it starts in. The runner checks out that worktree's
`HEAD` detached as `.claude/worktrees/unbound-<run-id>` of the repository's primary worktree, the
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
the PID namespace it was started in, and when the first process of a PID namespace ends, the
operating system kills every other one in it at once. Claude Code's Bash sandbox runs every call of a
session's Bash tool, foreground or background, in a PID namespace of its own whose first process is
the sandbox's own wrapper around the call's shell: the call's namespace ends when its command ends.
So a runner detached from a sandboxed Bash call is killed, without a word, when that call returns,
and leaves a run with no result whose run lock nobody holds; the same holds for any process that
call started. A sandboxed command cannot hand the run to a process outside either, since the sandbox
refuses it even Unix sockets. Whoever needs a run to outlive a sandboxed call starts it from a
process outside the sandbox, as a [workflow step](../glossary.json#concept.workflow-step) does
through the [project MCP server](../glossary.json#concept.project-mcp-server)
([Workflows](../workflows/module.md#steps-in-claude-code)), or keeps the call alive as long as the
run. Which callers those are is not Execution's to say: a worker's Bash is sandboxed on the Claude
Code backend ([req.workers.bash-sandbox](../worker-harness/workers/launch.md#req.workers.bash-sandbox))
and a [main agent](../glossary.json#concept.main-agent)'s own session may be, while a
[task session](../glossary.json#concept.task-session)'s calls are not
([req.task-session.no-sandbox](../coordination/task-session/requirements.md#req.task-session.no-sandbox)),
so no namespace of theirs ends with them; a task session starts its runs in background Bash rather
than detached all the same, because Claude Code may end the processes of a call that returned.
Execution itself does not see which namespace it was started in and promises no more than this.

### The run store

<a id="concept.run-store"></a>

Every run is a [trace node](../glossary.json#concept.trace-node) of
[Tracing](../kernel/tracing/module.md): a folder with its `trace.json`, its
[run progress file](../glossary.json#concept.run-progress-file), its result and, below it, the nodes
of the checks it ran and of the worker runs its steps launched. The **run store** is where those
folders lie: a run started directly lies in `runs/<run-id>/` of the workspace folder, a run a
[workflow step](../glossary.json#concept.workflow-step) started inside that step's node of
[Workflows](../workflows/module.md)' workflow node in the same folder, and an unbound run in
`.concorde/unbound/<run-id>/` of the worktree it started in, never in its checkout. A bound run that
does not hold its workspace's lock yet lies in the lobby, `.concorde/lobby/<run-id>/` of the
`.concorde` its binding names, and stays there when it is refused before it holds it, so that
nothing is written into a workspace folder by a run that has not entered it. Git ignores all of
them. Execution registers the unbound runs and the lobby with Tracing as
[trace roots](../kernel/tracing/contracts.md#trace-roots), each kept 7 days after its run ended unless
the project configures otherwise. Whoever prepared a workspace reads its runs in its workspace
folder, and the runs waiting in the lobby for its lock, to know what happened in it. `concorde trace`
finds a run by its identity among the registered roots, which hold every run of a workspace
Concorde's task level prepared; a run of a workspace whose folder another preparer placed elsewhere
is found by the path of its node folder instead.

## Overview

Three pictures give the whole of Execution: the seam through which whoever prepares a workspace
reaches it, the children that carry its runs, and the life of one run.

### One narrow seam

The upper half of Concorde decides what to work on and in which workspace; the parts that work in a
workspace do the work. Execution keeps the two apart with one narrow seam: a file the upper half
writes and Execution only reads, the Kernel's binding, and records Execution writes and the upper
half only reads, the run store and the
[delivery commits](../glossary.json#concept.delivery-commit) a delivering definition makes. Nothing
in Execution imports or writes the task store, so a change of how tasks are managed, parallelized or
merged never reaches the code that runs work, and Execution can run in any workspace someone
prepared, not only in a task.

```d2 illustrative
direction: right
preparer: "Whoever prepares the workspace\n(in Concorde, the task level)"
binding: "Workspace binding\n.concorde/workspace.json\n(Kernel)"
execution: "Execution\nin the bound workspace"
records: "Run store and\ndelivery commits"
preparer -> binding: writes
binding -> execution: is read by
execution -> records: writes
records -> preparer: are read by
```

### Three children, and the parts around them

Execution is the composition of three children. Operations and Commands are the frameworks of
level 4 of Concorde's [levels of work](../module.md#the-levels-of-work), the runs: the AI half and
the deterministic half. Check execution is no level: it is a service the runs' steps call
in-process. The definitions themselves come from the installed parts: Method registers Concorde's
Operations and commands, whose worker-backed steps launch their workers through the worker harness;
Workflows, a part of its own above Execution, starts runs as the steps of a procedure.

```d2 illustrative
execution: Execution {
  operations: Operations
  commands: Commands
  checks: Check execution
}
method: "Method\n(registers definitions)"
workflows: "Workflows\n(starts runs)"
harness: "Worker harness\n(launches workers)"
method -> execution.operations: registers Operations
method -> execution.commands: registers commands
workflows -> execution.operations: runs
workflows -> execution.commands: runs
method -> harness: "its steps launch\nworkers through"
method -> execution.checks: "its steps run\nchecks through"
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
node into the workspace folder, or checks out the worktree's `HEAD` for an unbound one, admits the
inputs and runs the definition's own admission of its Modules, runs the definition's steps in their
declared order until one stops the run, removes an unbound run's checkout, composes the run result,
checks it against its contract and, when it is `ok`, the definition's output contract, and writes it
while it still holds the lock, so that a run that takes the lock after it finds that result written.
The runner then writes its run's trace node again, with the run's end. Seeing the result alone does
not tell that the workspace is free: the runner may still hold the lock. A refusal before the steps,
a step that raises, a signal or an invalid result each still end in a written result with the
runner's link on top. Its exact behaviour is in [How a run is executed](runner.md).

```d2 illustrative
direction: down
parse: "Parse the command line"
bind: "Read the workspace binding"
node: "Create the run's trace node\n(in the lobby when bound),\ntake its run lock"
lock: "Take the workspace lock\n(or wait for it with --wait)"
enter: "Check the binding again,\nmove the node into\nthe workspace folder"
checkout: "Check out HEAD detached:\nthe unbound checkout"
admit: "Admit the inputs; the definition\nadmits its Modules"
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
concorde <execution command> [--modules …] [--input …] [--detach] [--wait <s>] [command arguments]
```

These are the usual forms, not the whole syntax: every run takes the common options `--modules`,
`--input`, `--detach`, `--wait` and `--trace-at`, which a workflow step uses to place its run's
node, even where a line above leaves them out, as [Command lines](runner.md#command-lines) gives
them in full. Execution registers `concorde run` with Distribution's `concorde` command, and one
command for each execution command the installed parts define, such as Method's
`concorde task-validation`, `concorde delivery` and `concorde scaffold`. `--modules` names the
Modules the run works on (default: the binding's); `--input` admits the output of an earlier `ok`
run of the same workspace, such as a plan or a survey. `concorde workflow step|report …` also works
on the bound workspace without naming it, but is not itself a run: it starts and awaits runs through
[Workflows](../workflows/module.md).

A run of Method's `implement` in a task worktree, for example, reads the binding (workspace `retry`,
Module `module.http`, base `4be1…`), takes the lock of `retry`, and runs the definition's steps: they
admit `module.http` against the worktree's Specs, compute the implement grant for it, launch one
worker through the [worker harness](../worker-harness/module.md), and audit and check its change.
The runner prints its run result and saves it in the run's trace node,
`<workspace folder>/runs/<run-id>/result.json`. The command exits 0 for `ok`, 1 for `blocked` or
`failed`, and 2 for a malformed command line, which starts nothing.

### Waiting for a busy workspace

A [workflow step](../glossary.json#concept.workflow-step) waits for the workspace lock to be free
before it starts its run. `--wait <seconds>` queues any run instead: the runner waits for the lock
inside its own process, its run progress file naming the lock's holder, a run or, in Concorde, a
task's merge or close, starts the moment that holder lets go, and is refused with `workspace_busy`
only when the lock is still held after that many seconds. A caller that wants a `delivery` after
an `implement` thus asks once, and never polls the lock. The run waits in the lobby, outside the
workspace folder, and enters the workspace only once it holds the lock and finds the binding it
started from unchanged: a task closed meanwhile has
removed the binding and, holding the lock, its lock file, and the run is refused with
`workspace_retired` in the lobby instead of writing into the folder the close moved to the
history. The lock is a file lock held by the runner's process, so the operating system releases it
however the run ends. The runner writes a run's result before it releases the lock, so a run admitted
after it finds that result written, unless the runner was killed before it could write one and the
run is lost; a result on disk, though, does not mean the lock is free yet.

### Running unbound

Main sessions merge tasks into the primary worktree while an unbound run lasts, and since the run
reads, and the worker harness audits, only its checkout, such a merge can neither change what the
run reads nor make a worker's audit fail. The run is still recorded in the worktree it started in,
in `.concorde/unbound/<run-id>/`, a trace of its own, while everything else it reads comes from the
commit checked out, like every other input of the run. The runtime paths its definition names and
that Git ignores, such as `.venv` and `node_modules`, are linked from that worktree into the
checkout, so the checks a review runs there find them; Method's definitions name the
[worker configuration](../glossary.json#concept.worker-configuration)'s runtime paths, as committed
in the checkout. Each submodule that worktree has checked out is checked out in the checkout too,
when its repository holds the commit the checkout records and Git can check it out; one that cannot
be stays empty, as in a fresh clone, with `submodule-absent` evidence naming why
([Unbound checkout](runner.md#unbound-checkout)). However the run ends, the runner removes the
checkout before it writes the result.

### Following a long run

While a run lives, its run progress file names what runs, in which workspace and step, with the
runner's process identifier, and every worker run its steps launch records the run's identity, so
an observer, such as a workflow step or the run state of a task, follows a run and its worker
without asking the runner. Whether the runner still lives is told by its run lock, which the runner
locks from before its first run progress file until after its result and removes as it exits, and
that the operating system releases however the runner ends: a run without a result whose run lock
nobody holds ended without writing one. No observer decides it by the recorded process identifier,
which is only meaningful in the PID namespace the runner ran in: a runner started in a sandboxed
shell may record 2, a number that names an unrelated, living process on the host.

### What other parts may ask of Execution

Execution offers two [optional integrations](../glossary.json#concept.optional-integration) to parts
that do not depend on it, through its [part registration](../glossary.json#concept.part-registration):

- **The runs of a workspace**, for whoever prepared it, in Concorde Coordination: the runs of a
  workspace with their state, from its workspace folder and the lobby, as running, ended or lost by
  their run locks; stopping the runs that still run, lobby included, as a task's close does; and
  waiting for one run to end without polling. Without the execution part a workspace has no runs,
  and Coordination says so.
- **An idle check**, for Distribution: whether any run of the project still holds its run lock,
  naming each, so that an install or an update never replaces the code a runner is running.

## How it is built

### Why a binding file

A run needs five facts about its workspace: which Modules it works on, which branch it may commit
on, which commit its changes are measured from, the goal a worker is briefed with, and where its
traces and locks go. Asking every caller to pass them on every command line would make each command
long and easy to get wrong, and would let two runs in the same workspace disagree on its base.
Asking the task store for them would tie Execution to tasks. The Kernel's binding, written once when
the workspace is prepared, gives every run the same facts from where it already is, and confines the
knowledge of tasks to whoever writes the file; [the Kernel](../kernel/module.md#the-workspace)
explains what the binding holds and what it leaves to the records.

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

### Why definitions bring the Specs and the workers

The runner runs the steps a definition gives it and nothing more. Admitting Modules against a
registry, computing a grant and launching a worker under it are what particular definitions need,
and putting them in the runner would make Execution depend on the Spec tooling and the worker
harness, so that no project could run its own definitions without installing both. Leaving them to
the definitions keeps the runner the same for every run, while Method, which depends on all three,
gives Concorde's Operations their Spec-derived grants.

### Why an unbound run works in a checkout

The primary worktree is where main sessions merge delivered tasks, and several may do so while an
unbound review of it is still running. A run that read the primary worktree directly would see the
Specs and the code it reads change under its workers, and the worker harness's audit, which compares
`HEAD` and the index before and after each round, would report the merge as the worker's own write.
Locking the primary worktree against merges for a review's whole life would stall every other
session, and tolerating changes would make the audit meaningless. A checkout of one commit gives the
run a fixed input that no other session touches, and naming that commit in the result tells the
caller exactly what was examined. The checkout is Git's own linked worktree (`git worktree add
--detach`), which shares the repository's objects, so it costs no clone and needs no copying code;
it lives in the primary worktree's `.claude/worktrees/`, which Git ignores, beside the task
worktrees, because that is the one placement where the worker harness lets a worker run and knows
every Git administrative path to hide from it, and the runner removes it through Git again. What a
commit never holds, the environments Git ignores and the checkouts of submodules, comes from the
worktree the run started in: the environments linked, since the run only reads them, and each
submodule checked out from its own repository at the commit the checkout records.

### The runner and run store

<a id="realization.execution.runner"></a>

The **Runner and run store** realization binds the binding reader, the run store, the unbound
checkout, the run context and definitions that steps work with and the runner itself, with their
tests; the runner finds an execution command by name in the catalog of
[Commands](commands/module.md). Its run context today also holds the [standard worker sequence](../glossary.json#concept.standard-worker-sequence)'s
launch of a worker and the computation of the grant, which are Method's
([Method](../method/module.md#the-standard-worker-sequence)) and leave this package when a later
code task moves them into Method's package `src/concorde/method/`. The `concorde` command belongs to [Distribution](../distribution/module.md),
which hands `run`, the execution commands and `workflow` to the parts that register them.

```d2
execution: Execution {
  runner: Runner and run store {
    "src/concorde/execution/__init__.py"
    "src/concorde/execution/binding.py"
    "src/concorde/execution/checkout.py"
    "src/concorde/execution/context.py"
    "src/concorde/execution/runner.py"
    "src/concorde/execution/runs.py"
    "tests/concorde/execution/"
  }
  result: Run result
  store: Run store
  checkout: Unbound checkout
  runner -> checkout: works in for each unbound run
  runner -> result: writes
  store -> result: keeps
}
```

## The children

<a id="contains-operations"></a>

**Operations** is the Operation framework: it holds the
[Operation catalog](../glossary.json#concept.operation-catalog), assembled from the Operation
definitions the installed parts register, and hands the runner each definition, which the runner
looks up by name: its steps, its arguments, the ids of the workers it may launch, whether it may run
unbound and its output contract. The runner relies on that definition alone: it parses the arguments
with its own, refuses unbound a definition that does not allow it, runs the steps and checks an `ok`
output against the contract, replacing a result that breaks it by a `failed` one.

<a id="contains-commands"></a>

**Commands** is the execution-command framework: it holds the catalog of the execution commands the
installed parts register, such as Method's `task-validation`, `delivery` and `scaffold`. Its catalog
hands the runner each command's definition as Operations' does, a definition that cannot be loaded
being a command-line error that starts no run, and the runner runs its steps like an Operation's; a
definition that diagnoses the workspace's Specs itself, as `task-validation`'s does, runs its steps
even when those Specs do not load.

<a id="contains-checks"></a>

**Check execution** runs the project's
[configured checks](../glossary.json#concept.configured-check) in a read-only boundary and returns
each result with its log. The steps of Operations and execution commands, and the round validations
they give the worker harness, call it in-process; it starts no run and no worker. When checks cannot
run, it gives its caller its own error link, made by `service_error` of
[the check service](checks/service.md), which a step keeps unchanged as a cause under the run's link
rather than translating it as it translates Spec tooling's errors ([Errors](runner.md#errors)).

## What Execution relies on

<a id="uses-kernel"></a>

**The Kernel** defines the [workspace binding](../glossary.json#concept.workspace-binding) the
runner reads, by its [binding contract](../kernel/contracts.md#contract.kernel.workspace-binding),
and the [workspace lock](../glossary.json#concept.workspace-lock) each bound run holds. Execution
relies on the binding naming the workspace folder and the `.concorde` of its locks, and refuses a
binding that breaks the contract or names another root, rather than trusting it; it relies on every
other taker of the workspace lock, such as a task's merge or close, writing its holder line, so that
a waiting run can name it.

<a id="uses-tracing"></a>

**Tracing** gives every run its trace node's shape and place and every lock its file: the runner
writes the run's node at its start and its end through Tracing's library, takes the run lock and the
workspace lock under `locks/`, registers the unbound runs and the lobby as trace roots, and reports
its errors in the error contract. Execution relies on the
[node contract](../kernel/tracing/contracts.md#contract.tracing.node), the
[layout](../kernel/tracing/contracts.md#layout) and the [locks](../kernel/tracing/contracts.md#locks),
and records nothing that Tracing's node contract refuses.

The runner, its run store and its children rely on no Module of the upper half and on no part but
the kernel, and nothing in Execution reads or writes the task store. The task level of Coordination
uses Execution where it is installed: it writes the binding and reads the run store and the delivery
commits, as its own Spec explains. Workflows' Claude Code workflows start each step through the
`workflow_step` tool that Workflows registers with the
[project MCP server](../glossary.json#concept.project-mcp-server), so that the step's run is started
by a process outside the session's sandboxed Bash and outlives it; the runner itself, and every run
started from a command line, needs nothing of it.
