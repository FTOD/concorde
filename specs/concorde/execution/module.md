# Execution

## Purpose

Given one bound [workspace](../glossary.json#concept.workspace), Execution runs work there and
returns checked results. Execution is the execution [part](../glossary.json#concept.part). It runs
[Operations](../glossary.json#concept.operation), whose steps combine AI workers with host logic.
It also runs [execution commands](../glossary.json#concept.execution-command), which do deterministic
work such as deciding readiness and delivering. Both use the definitions the installed parts
register. Execution provides Check execution, which runs the project's checks for those steps.
Everything in Execution learns what it works on from one place: the
[workspace binding](../glossary.json#concept.workspace-binding) in the worktree it starts in.
Execution records what it did as [trace nodes](../glossary.json#concept.trace-node) in the workspace
folder that binding names, its [run store](../glossary.json#concept.run-store). Whoever prepares a
workspace and reads those records relies on Execution. In Concorde, that is the task level of
[Coordination](../coordination/module.md). Coordination binds each task worktree and derives the
task's state from what Execution recorded. What a run does is its definition's. In Concorde,
[Method](../method/module.md) registers the Operations and commands of Concorde's way of working.
[Workflows](../workflows/module.md) orders runs for a known procedure.

Execution does not know that tasks exist. Execution never does any of these things:

- opens, merges or closes a task
- reads or writes a [task record](../glossary.json#concept.task-record)
- switches branches
- asks the developer anything

Execution does none of these things itself:

- reads a [Spec](../glossary.json#concept.spec)
- computes a grant
- launches a worker

A definition's steps do whatever needs the Specs or a worker, through the parts they depend on.
Execution chooses no next step on its own. Whoever started a run, or the workflow that orders runs,
decides what runs next. Execution depends on the kernel part alone.

## Core concepts

Execution rests on three ideas:

- a run that works on a workspace and ends with one result
- the definitions that say what a run does
- the run store where every run is kept

Execution builds on the Kernel's [workspace](../glossary.json#concept.workspace). It reads the
workspace's [binding](../glossary.json#concept.workspace-binding). Each bound run holds the
[workspace lock](../glossary.json#concept.workspace-lock). Execution also builds on Tracing's
[trace node](../glossary.json#concept.trace-node) and
[error chain](../glossary.json#concept.error-chain).

### Runs and their definitions

<a id="concept.run"></a>

A **run** is one execution of an Operation or of an execution command in one worktree. An
[Operation](../glossary.json#concept.operation) is a definition whose steps launch AI workers. The
[Operation catalog](../glossary.json#concept.operation-catalog) of [Operations](operations/module.md)
lists the ones the installed parts register. An
[execution command](../glossary.json#concept.execution-command) is a definition whose steps are
deterministic and launch no worker. Method provides these examples:

- `task-validation`
- `delivery`
- `scaffold`

The catalog of [Commands](commands/module.md) lists execution commands. Both kinds are **runs**.
The same runner performs these steps for both kinds:

- parses their command line
- resolves the workspace
- takes the workspace lock
- runs their steps
- writes one run result

A workflow, the task level or an observer therefore treats them alike. The Operation or execution
command a run names is the run's **definition**. The definition supplies these things:

- the steps the runner runs
- the arguments they take
- whether the run may be unbound
- the runtime paths an unbound run's checkout links
- the contract its output must satisfy

<a id="concept.execution-runner"></a>

The **Execution runner** is that runner. This deterministic process runs one run, an Operation's or
an execution command's, from its command line to its written result. It launches workers only
through the steps that ask for them. [The life of a run](#the-life-of-a-run) shows its steps.

<a id="concept.run-result"></a>

Every run ends with one **[run result](../glossary.json#concept.run-result)**. The result holds these
items:

- kind (`operation` or `command`)
- name
- workspace
- Modules
- run identity
- status
- summary
- output

When the run did what it promises, `status` is `ok`. When it needs a decision above it, `status` is
`blocked`. Examples include a reported [Spec gap](../glossary.json#concept.spec-gap) or a workspace
that is not ready. When something went wrong, `status` is `failed`. Something went wrong when one of
these happened:

- a refusal
- a write outside the grant
- checks still failing after the last [resume round](../glossary.json#concept.resume-round)
- a Git refusal
- a runner error

A worker-backed run also carries the worker's own
[worker result](../glossary.json#concept.worker-result) unchanged, beside the runner's own evidence.
A caller therefore always tells what the runner observed from what a worker claims. When `status`
is not `ok`, `error` is the run's [error chain](../glossary.json#concept.error-chain). The chain is
the run's own link over the unchanged errors it received. The
[run result contract](contracts.md#contract.execution.run-result) defines the envelope.
[How a run is executed](runner.md) defines how the runner fills it.

For the runner, the [Modules](../glossary.json#concept.module) a run works on are names. They are
the ones `--modules` gives, or else the binding's. When a definition's steps read the Specs, the
definition checks the Modules in its own admission. Method's definitions do this through the Spec
tooling. Such an admission leaves out the binding's Modules the workspace no longer registers. It
refuses a named Module the workspace does not register. A definition that reads no Spec takes the Modules as
labels.

### Unbound runs

<a id="concept.unbound-run"></a>

When a definition allows it, the definition may also run
**[unbound](../glossary.json#concept.unbound-run)**, in a worktree without a binding such as the
primary worktree. In Concorde, these are Method's reading Operations:

- `understand`
- `survey`
- `spec_panel`
- `code_review`

An unbound run has these properties:

- It works with the Modules `--modules` names.
- It records `workspace` null.
- It admits only unbound inputs.
- It takes no workspace lock, having no workspace to lock.
- It takes its run lock like every run.
- It may launch only reading workers, so it changes no Spec or code.

Besides its own record, the one lasting change an unbound run may make is publishing
[Issues](../glossary.json#concept.issue). Where the issues part is installed, a Spec or code review
reports its findings this way. It publishes only through the [Issues](../issues/module.md) store.
The store commits each Issue on the primary branch as a commit of its own under the
[merge lock](../glossary.json#concept.merge-lock). The run never publishes through the checkout it
examines
([req.execution.unbound-origin-untouched](requirements.md#req.execution.unbound-origin-untouched)).
Every other definition is refused unbound with `binding_required`.

<a id="concept.unbound-checkout"></a>

An unbound run never works in the worktree it starts in. The runner checks out that worktree's
`HEAD` detached as `.claude/worktrees/unbound-<run-id>` of the repository's primary worktree. This is
the **[unbound checkout](../glossary.json#concept.unbound-checkout)**, where the run's steps and
workers work. Before it writes the result, the runner removes the checkout. The result names the
commit examined as `commit`. The run examines that commit, never uncommitted changes.
[Running unbound](#running-unbound) says what else the checkout holds.

### Long runs

<a id="concept.detached-run"></a><a id="concept.run-progress-file"></a><a id="concept.run-lock"></a>

With `--detach`, the command starts the runner as a
**[detached run](../glossary.json#concept.detached-run)**, a process of its own that outlives the
command. As soon as the run's **[run progress file](../glossary.json#concept.run-progress-file)**
exists, the command prints the run identity and the path of its result. Everything else about the
run is the same. The run progress file names these things:

- what runs
- in which workspace
- in which step

The **[run lock](../glossary.json#concept.run-lock)**, `locks/runs/<run-id>.lock`, tells whether the
runner still lives. Only the run's runner locks it. The runner locks it before the first run
progress file and holds it until after the result. The runner removes the file as it exits. An
observer in any PID namespace tells by the lock whether the run still runs.
[Following a long run](#following-a-long-run) explains how an observer uses
both.

<a id="detached-namespace"></a>

**A detached run lives only as long as the PID namespace it started in.** The runner is a new
session and process group, which frees it from the command and its terminal. No process leaves
the PID namespace it was started in. When the first process of a PID namespace ends, the
operating system kills every other one in it at once. Claude Code's Bash sandbox runs every call
of a session's Bash tool in a PID namespace of its own, foreground or background. The namespace's
first process is the sandbox's own wrapper around the call's shell. When the call's command ends,
the call's namespace ends. When a sandboxed Bash call returns, a runner detached from it is
therefore killed without a word. The runner leaves a run with no result whose run lock nobody
holds. The same holds for any process that call started. A sandboxed command cannot hand the run
to a process outside either, since the sandbox refuses it even Unix sockets. Whoever needs a run
to outlive a sandboxed call starts it from a process outside the sandbox or keeps the call alive
as long as the run. A [workflow step](../glossary.json#concept.workflow-step) starts it outside
through the [project MCP server](../glossary.json#concept.project-mcp-server)
([Workflows](../workflows/module.md#steps-in-claude-code)). Which callers those are is not
Execution's to say. On the Claude Code backend, a worker's Bash is sandboxed
([req.workers.bash-sandbox](../worker-harness/workers/launch.md#req.workers.bash-sandbox)). A
[main agent](../glossary.json#concept.main-agent)'s own session may be sandboxed. A
[task session](../glossary.json#concept.task-session)'s calls are not sandboxed
([req.task-session.no-sandbox](../coordination/task-session/requirements.md#req.task-session.no-sandbox)).
No namespace of a task session's calls therefore ends with them. A task session starts its runs
in background Bash rather than detached all the same, because Claude Code may end the processes of
a call that returned. Execution itself does not see which namespace it was started in and promises no
more than this.

### The run store

<a id="concept.run-store"></a>

Every run is a [trace node](../glossary.json#concept.trace-node) of
[Tracing](../kernel/tracing/module.md). Its folder holds these things:

- its `trace.json`
- its [run progress file](../glossary.json#concept.run-progress-file)
- its result
- below it, the nodes of the checks it ran and of the worker runs its steps launched

The **run store** is where those folders lie. Runs have these locations:

- A run started directly lies in `runs/<run-id>/` of the workspace folder.
- A run a [workflow step](../glossary.json#concept.workflow-step) started lies inside that step's
  node of [Workflows](../workflows/module.md)' workflow node in the same folder.
- An unbound run lies in `.concorde/unbound/<run-id>/` of the worktree it started in, never in its
  checkout.

Until a bound run holds its workspace's lock, it lies in the lobby. The lobby is
`.concorde/lobby/<run-id>/` of the `.concorde` its binding names. When the run is refused before it
holds the lock, it stays there. A run that has not entered a workspace therefore writes nothing
into that workspace's folder. Git ignores all of them. Execution registers the unbound runs and
the lobby with Tracing as [trace roots](../kernel/tracing/contracts.md#trace-roots). Unless the
project configures otherwise, each is kept 7 days after its run ended. Whoever prepared a workspace
reads its runs in its workspace folder to know what happened in it. The preparer also reads the
runs waiting in the lobby for its lock. Among the registered roots, `concorde trace` finds a run by
its identity. Those roots hold every run of a workspace Concorde's task level prepared. When
another preparer placed a workspace's folder elsewhere, its run is found by the path of its node
folder instead.

## Overview

Three pictures give the whole of Execution:

- the seam through which whoever prepares a workspace reaches it
- the children that carry its runs
- the life of one run

### One narrow seam

The upper half of Concorde decides what to work on and in which workspace. The parts that work in
a workspace do the work. Execution keeps the two apart with one narrow seam. The upper half writes
a file that Execution only reads: the Kernel's binding. Execution writes records that the upper
half only reads: the run store and the
[delivery commits](../glossary.json#concept.delivery-commit) a delivering definition makes. Nothing
in Execution imports or writes the task store. A change of how tasks are managed, parallelized or
merged therefore never reaches the code that runs work. Execution can run in any workspace someone
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
level 4 of Concorde's [levels of work](../module.md#the-levels-of-work), the runs. They are the AI
half and the deterministic half. Check execution is no level. It is a service the runs' steps call
in-process. The definitions themselves come from the installed parts. Method registers Concorde's
Operations and commands. Their worker-backed steps launch their workers through the worker harness.
Workflows is a part of its own above Execution. It starts runs as the steps of a procedure.

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

A run is something the task level or a workflow starts and waits for. Its result is recorded. A
run's step starts a worker or calls a service, which answers only to that step. Deterministic work
that is taken and recorded as a step of its own is therefore an execution command. Deterministic
work that a step calls is a service. [The children](#the-children) explains each child's part.

### The life of a run

The Execution runner runs one run per process. It performs these steps:

- It parses the command line.
- It reads the binding.
- It creates the run's trace node, in the lobby for a bound run.
- It takes its run lock.
- For a bound run, it takes the workspace lock.
- For a bound run, it checks that the workspace was not retired meanwhile and moves the node into
  the workspace folder.
- For an unbound run, it checks out the worktree's `HEAD`.
- It admits the inputs.
- It runs the definition's own admission of its Modules.
- It runs the definition's steps in their declared order until one stops the run.
- For an unbound run, it removes the checkout.
- It composes the run result.
- It checks the result against its contract.
- When the result is `ok`, it checks the result against the definition's output contract.
- While it still holds the lock, it writes the result.

A run that takes the lock after it therefore finds that result written. The runner then writes
its run's trace node again, with the run's end. Seeing the result alone does not tell that the
workspace is free: the runner may still hold the lock. Each of these cases still ends in a written
result with the runner's link on top:

- a refusal before the steps
- a step that raises
- a signal
- an invalid result

The runner's exact behaviour is in [How a run is executed](runner.md).

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

Each of these cases takes the same dashed way:

- a step that raises
- a signal
- an invalid result

The run still ends in a written result with the runner's link on top. For an unbound run, the runner
removes the checkout first.

## Running work

Inside a bound workspace, every run works on that workspace without naming it:

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [operation arguments]
concorde <execution command> [--modules …] [--input …] [--detach] [--wait <s>] [command arguments]
```

These are the usual forms, not the whole syntax. Even where a line above leaves them out, every
run takes these common options:

- `--modules`
- `--input`
- `--detach`
- `--wait`
- `--trace-at`, which a workflow step uses to place its run's node

[Command lines](runner.md#command-lines) gives them in full. Execution's part registration names
`concorde run`. The part that defines an execution command names it in its own registration.
Method's registration names these commands
([Commands](commands/module.md#running-an-execution-command)):

- `concorde task-validation`
- `concorde delivery`
- `concorde scaffold`

`--modules` names the Modules the run works on (default: the binding's). `--input` admits the output
of an earlier `ok` run of the same workspace, such as a plan or a survey.
`concorde workflow step|report …` also works on the bound workspace without naming it. It is not
itself a run: it starts and awaits runs through [Workflows](../workflows/module.md).

For example, a run of Method's `implement` in a task worktree reads a binding with these values:

- workspace `retry`
- Module `module.http`
- base `4be1…`

The run takes the lock of `retry` and runs the definition's steps. The steps do these things:

- admit `module.http` against the worktree's Specs
- compute the implement grant for it
- launch one worker through the [worker harness](../worker-harness/module.md)
- audit and check its change

The runner prints its run result and saves it in the run's trace node,
`<workspace folder>/runs/<run-id>/result.json`. The command has these exit codes:

- For `ok`, it exits 0.
- For `blocked` or `failed`, it exits 1.
- When the run could not be recorded or its result not saved, it also exits 1, whatever the work
  did ([When records cannot be written](runner.md#when-records-cannot-be-written)).
- For a malformed command line, it exits 2 and starts nothing.

### Waiting for a busy workspace

Before it starts its run, a [workflow step](../glossary.json#concept.workflow-step) waits for the
workspace lock to be free. `--wait <seconds>` queues any run instead. The runner waits for the lock
inside its own process. Its run progress file names the lock's holder: a run or, in Concorde, a
task's merge or close. The moment that holder lets go, the run starts. Only when the lock is
still held after that many seconds is the run refused with `workspace_busy`. A caller that wants a
`delivery` after an `implement` thus asks once and never polls the lock. The run waits in the lobby,
outside the workspace folder. Only once it holds the lock and finds the binding it started from
unchanged does the run enter the workspace. A task closed meanwhile removed the binding and,
holding the lock, its lock file. The run is therefore refused with `workspace_retired` in the lobby.
It does not write into the folder the close moved to the history. The lock is a file lock held by
the runner's process. However the run ends, the operating system releases the lock. Before it
releases the lock, the runner writes a run's result. Unless the runner was killed before it could
write one and the run is lost, a run admitted after it finds that result written. A result on disk,
though, does not mean the lock is free yet.

### Running unbound

While an unbound run lasts, main sessions merge tasks into the primary worktree. The run reads,
and the worker harness audits, only its checkout. Such a merge can therefore neither change what
the run reads nor make a worker's audit fail. The run is still recorded in the worktree it started
in, in `.concorde/unbound/<run-id>/`, a trace of its own. Everything else it reads comes from the
commit checked out, like every other input of the run. The runtime paths its definition names and
that Git ignores are linked from that worktree into the checkout. Examples include `.venv` and
`node_modules`. The checks a review runs there therefore find them. Method's definitions name the
[worker configuration](../glossary.json#concept.worker-configuration)'s runtime paths, as committed
in the checkout. Each submodule that worktree checked out is checked out in the checkout too, when
its repository holds the commit the checkout records for it and Git can check it out. A submodule that cannot be
checked out stays empty, as in a fresh clone. The `submodule-absent` evidence names why
([Unbound checkout](runner.md#unbound-checkout)). However the run ends, the runner removes the
checkout before it writes the result.

### Following a long run

While a run lives, its run progress file names these things:

- what runs
- in which workspace
- in which step
- the runner's process identifier

Every worker run its steps launch records the run's identity. An observer therefore follows a run
and its worker without asking the runner. Examples of observers include a workflow step or the run
state of a task. The run lock tells whether the runner still lives. The runner locks it from before
its first run progress file until after its result. As it exits, the runner removes the lock.
However the runner ends, the operating system releases the lock. A run without a result whose run
lock nobody holds ended without writing one. No observer decides whether the runner still lives
by the recorded process identifier. The identifier is only meaningful in the PID namespace the
runner ran in. A runner started in a sandboxed shell may record 2. On the host, that number names
an unrelated, living process.

### What other parts may ask of Execution

Two parts that do not depend on Execution reach it. Each uses an
[optional integration](../glossary.json#concept.optional-integration) of its own.

**The runs of a workspace** serves whoever prepared it, in Concorde Coordination's task level.
This integration works through records rather than a call. Execution promises these things:

- Until the run holds the workspace lock, its node folder lies in the lobby. When the run is
  refused before it holds the lock, the node folder stays there for good. Otherwise, the folder
  lies in the workspace folder ([The run store](#the-run-store)).
- The run has its [run progress file](../glossary.json#concept.run-progress-file) and its result.
- The run has its [run lock](../glossary.json#concept.run-lock), held exactly while its runner
  lives. The runner holds it from before its first run progress file until after its result
  ([req.execution.run-lock-held](requirements.md#req.execution.run-lock-held)).
- When sent `SIGTERM` wherever its run lies, lobby included, the runner ends its running step,
  if one runs. It finishes with a `failed` result with `cancelled` evidence
  ([Runner](runner.md#runner)).

The preparer reads those records itself to tell each run running, ended or lost. It waits on a run
lock to learn that a run ended. It sends `SIGTERM` itself, as a task's close does. Execution
registers no call for any of it. Without the execution part, none of these records exists, so a
workspace has no runs. Coordination says so.

**An idle check** serves Distribution. This is the one integration Execution's
[part registration](../glossary.json#concept.part-registration) names. When asked, it tells whether
any run of the project holds its run lock, naming each. The installer therefore refuses to replace
the code under a run it finds running. The idle check reads the run locks of the primary worktree's
`.concorde`, where every bound run keeps them. It also reads those of the `.concorde` of every other
worktree Git lists, where an unbound run started there keeps them. Every worktree runs the primary
worktree's one Framework copy. The check keeps no run from starting afterwards
([Distribution](../distribution/requirements.md#req.distribution.idle-install)).

## How it is built

### Why a binding file

A run needs five facts about its workspace:

- which Modules it works on
- which branch it may commit on
- which commit its changes are measured from
- the goal a worker is briefed with
- where its traces and locks go

Asking every caller to pass them on every command line would make each command long and easy to
get wrong. It would also let two runs in the same workspace disagree on its base. Asking the task
store for them would tie Execution to tasks. When the workspace is prepared, its preparer writes
the Kernel's binding once. The binding gives every run the same facts from where it already is.
It confines the knowledge of tasks to whoever writes the file.
[The Kernel](../kernel/module.md#the-workspace) explains what the binding holds and what it leaves
to the records.

### Why commands are runs

An Operation exists to combine AI workers with host logic that checks them. These activities need
no model, so they are not Operations:

- deciding readiness
- delivering
- scaffolding

A workflow must be able to take them as steps. Like for any Operation, a caller must be able to do
these things:

- wait for them
- read their evidence
- receive their error chain

Running execution commands with the same runner gives them all of that without the
[Operation catalog](../glossary.json#concept.operation-catalog) or any worker machinery. The only
difference a caller sees is the result's `kind` and the error link's level, `command` instead of
`operation`. Being a run also tells an execution command from a deterministic service such as
[Check execution](checks/module.md). A run's step calls a service, which answers it. An execution
command is itself the run, with these things:

- a workspace
- a lock
- a recorded result

### Why definitions bring the Specs and the workers

The runner runs the steps a definition gives it and nothing more. Particular definitions need
these activities:

- admitting Modules against a registry
- computing a grant
- launching a worker under that grant

Putting them in the runner would make Execution depend on the Spec tooling and the worker harness.
No project could then run its own definitions without installing both. Leaving them to the
definitions keeps the runner the same for every run. Method depends on all three and gives
Concorde's Operations their Spec-derived grants.

### Why an unbound run works in a checkout

The primary worktree is where main sessions merge delivered tasks. While an unbound review of it
still runs, several main sessions may merge tasks. A run that read the primary worktree directly
would see the Specs and the code it reads change under its workers. The worker harness's audit
compares `HEAD` and the index before and after each round. The audit would report the merge as the
worker's own write. Locking the primary worktree against merges for a review's whole life would
stall every other session. Tolerating changes would make the audit meaningless. A checkout of one
commit gives the run a fixed input that no other session touches. Naming that commit in the result
tells the caller exactly what was examined. The checkout is Git's own linked worktree
(`git worktree add
--detach`), which shares the repository's objects. It costs no clone and needs no copying code.
The checkout lives in the primary worktree's `.claude/worktrees/`, beside the task worktrees. Git
ignores that directory. The execution part's registration contributes that ignore rule as
Coordination's does. The checkout lies there because this is the one placement where the worker
harness lets a worker run and knows every Git administrative path to hide from it. The runner removes the checkout through Git again.
What a commit never holds comes from the worktree the run started in. These are the environments
Git ignores and the checkouts of submodules. Since the run only reads the environments, they are
linked. Each submodule is checked out from its own repository at the commit the checkout records.

### The runner and run store

<a id="realization.execution.runner"></a>

The **Runner and run store** realization binds these things, with their tests:

- the run store
- the unbound checkout
- the run context and definitions that steps work with
- the runner itself

The runner finds an execution command by name in the catalog of [Commands](commands/module.md).
It launches no worker and computes no grant. The
[standard worker sequence](../glossary.json#concept.standard-worker-sequence) is Method's
([Method](../method/module.md#the-standard-worker-sequence)). Method's steps record each worker run
on the run context. An unbound run's checkout links what the definition's runtime-path resolver
returns. The `concorde` command belongs to [Distribution](../distribution/module.md). Distribution
hands these commands to the parts that register them:

- `run`
- the execution commands
- `workflow`

```d2
execution: Execution {
  runner: Runner and run store {
    "src/concorde/execution/__init__.py"
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

### Guidance

<a id="realization.execution.guidance"></a>

The **Execution guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). It is kept in `prompts/guidance/execution/`
and registered under `guidance` in the part's registration. Wherever the part is installed,
[Distribution](../distribution/module.md#guidance-composition) composes these sections after
Coordination's working method:

- the project skill's section `Runs`
- the project skill's section `Read results`
- the project skill's section `Unbound runs`
- the `CLAUDE.md` block's sentence on unbound runs

Where a part it mentions is not installed, each section says what happens.

## The children

<a id="contains-operations"></a>

**Operations** is the Operation framework. It holds the
[Operation catalog](../glossary.json#concept.operation-catalog), assembled from the Operation
definitions the installed parts register. Operations hands the runner each definition, which the
runner looks up by name. The definition gives these things:

- its steps
- its arguments
- the ids of the workers it may launch
- whether it may run unbound
- its output contract

The runner relies on that definition alone. It performs these actions:

- It parses the definition's arguments with its own.
- When a definition does not allow unbound runs, it refuses that definition unbound.
- It runs the steps.
- It checks an `ok` output against the contract.
- When such an output breaks the contract, it replaces that result by a `failed` one.

<a id="contains-commands"></a>

**Commands** is the execution-command framework. It holds the catalog of the execution commands
the installed parts register. Method provides these examples:

- `task-validation`
- `delivery`
- `scaffold`

Commands' catalog hands the runner each command's definition as Operations' does. When a definition
cannot be loaded, this is a command-line error that starts no run. The runner runs a command's
steps like an Operation's. Even when the workspace's Specs do not load, a definition that diagnoses
them itself runs its steps. The definition of `task-validation` diagnoses them itself.

<a id="contains-checks"></a>

**Check execution** runs the project's
[configured checks](../glossary.json#concept.configured-check) in a read-only boundary. It returns
each result with its log. These callers call it in-process:

- the steps of Operations
- the steps of execution commands
- the round validations those steps give the worker harness

Check execution starts no run and no worker. When checks cannot run, it gives its caller its own
error link, made by `service_error` of [the check service](checks/service.md). A step keeps that
link unchanged as a cause under the run's link ([Errors](runner.md#errors)).

## What Execution relies on

<a id="uses-kernel"></a>

**The Kernel** defines the [workspace binding](../glossary.json#concept.workspace-binding) the
runner reads, by its [binding contract](../kernel/contracts.md#contract.kernel.workspace-binding).
It also defines the [workspace lock](../glossary.json#concept.workspace-lock) each bound run holds.
Execution relies on the binding naming the workspace folder and the `.concorde` of its locks.
When a binding breaks the contract or names another root, Execution refuses it rather than trusting
it. Execution relies on every other taker of the workspace lock writing its holder line, so that a
waiting run can name it. Examples include a task's merge or close.

<a id="uses-tracing"></a>

**Tracing** gives every run its trace node's shape and place and every lock its file. The runner
performs these actions:

- Through Tracing's library, it writes the run's node at its start and its end.
- Under `locks/`, it takes the run lock and the workspace lock.
- It registers the unbound runs and the lobby as trace roots.
- It reports its errors in the error contract.

Execution relies on these things:

- the [node contract](../kernel/tracing/contracts.md#contract.tracing.node)
- the [layout](../kernel/tracing/contracts.md#layout)
- the [locks](../kernel/tracing/contracts.md#locks)

Execution records nothing that Tracing's node contract refuses.

<a id="uses-distribution"></a>

**Distribution** is the installation host present in every installation. It installs the execution
part from its [part registration](../glossary.json#concept.part-registration). This is the plain
data its [registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines. The registration gives these things:

- the `run` command and its entry
- the modules it loads, which register the run and check traces' node kinds and the trace roots of
  the unbound runs and the lobby
- the [typed value](../glossary.json#concept.typed-value) types of those traces
- the part's guidance sections
- the ignore rules for `.concorde/unbound/`, `.concorde/lobby/` and `.claude/worktrees/`
- the idle check over the run locks

Execution relies on Distribution performing these actions:

- routing `concorde run` to the runner's entry
- composing its guidance
- asking its idle check before an install or an update

Execution imports nothing of Distribution.

The runner, its run store and its children depend on no Module of the upper half and on no part but
the kernel. They meet Distribution's host promises as every part does. Nothing in Execution reads
or writes the task store. Where Execution is installed, the task level of Coordination uses it.
Coordination writes the binding and reads the run store and the delivery commits, as its own Spec
explains. Workflows' Claude Code workflows start each step through the `workflow_step` tool.
Workflows registers that tool with the
[project MCP server](../glossary.json#concept.project-mcp-server). A process outside the session's
sandboxed Bash therefore starts the step's run, which outlives the sandboxed Bash. The runner
itself, and every run started from a command line, needs nothing of the project MCP server.
