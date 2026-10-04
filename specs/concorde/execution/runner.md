# How a run is executed

This document gives the exact behaviour of the [Execution runner](../glossary.json#concept.execution-runner).
It covers these details:

- the command lines
- the [workspace binding](../glossary.json#concept.workspace-binding) the runner reads
- what the runner does from the parse to the finish
- the [run progress file](../glossary.json#concept.run-progress-file)
- how refusals and failures become a result

The Operation or execution command a command line names is the run's definition. The definition
gives the runner these things
([What a definition gives the runner](#what-a-definition-gives-the-runner)):

- its steps
- its arguments
- whether it may run unbound
- its admission of the Modules
- its runtime-path resolver
- its output contract

The envelope is the [run result contract](contracts.md#contract.execution.run-result).
The binding is the [workspace binding contract](../kernel/contracts.md#contract.kernel.workspace-binding).
Method's [Operations](../glossary.json#concept.operation) add the
[standard worker sequence](../glossary.json#concept.standard-worker-sequence) in their steps.
That sequence is Method's ([How an Operation runs its workers](../method/workers.md)).

## Command lines

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [--trace-at <folder>] [operation arguments]
concorde <command>       [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [--trace-at <folder>] [command arguments]
```

`<operation>` is a name from the [Operation catalog](../glossary.json#concept.operation-catalog).
`<command>` is one of the [execution commands](../glossary.json#concept.execution-command) the
installed parts register. Concorde Method registers these commands:

- `task-validation`
- `delivery`
- `scaffold`

When `concorde run` names an execution command, it is a command-line error that names the command
to use instead.

The run works on the worktree the command starts in. This is the Git worktree containing the
current directory or, for an [unbound run](../glossary.json#concept.unbound-run), its
[unbound checkout](#unbound-checkout). A directory outside every Git worktree is a command-line
error.

`--modules` names the Modules the run works on. Without `--modules`, the defaults are these:

- A bound run works on the binding's Modules.
- An [unbound run](../glossary.json#concept.unbound-run) works on none.

For the runner, a
[Module](../glossary.json#concept.module) is a name. A definition that reads the Specs admits the
Modules itself ([admission](#runner)). It leaves out the binding's Modules the workspace no longer
registers. It refuses a named Module the worktree does not register.

Each `--input` names a run whose result is `ok`. For a bound run, the input run's workspace is this
run's workspace. For an unbound run, the input run has no workspace. Once its saved result
satisfies the current [run result contract](contracts.md#contract.execution.run-result), its saved
`output` is admitted, with its name, as material of the run. Any other run is refused with
`input_not_admissible`. This includes a result an older Concorde wrote under another version of
the contract.

For a bound run, `--wait <seconds>` (default 0) is how long it waits for a busy workspace's lock
before refusal with `workspace_busy`. A negative value is a command-line error. An unbound run
takes no lock and ignores it. A run waits in the [lobby](#the-lobby), never in its workspace
folder.

`--trace-at <folder>` places the run's [trace node](../glossary.json#concept.trace-node) in that
folder instead of `runs/<run-id>/` of the workspace folder. It is how a
[workflow step](../glossary.json#concept.workflow-step) nests the run it starts inside its own
node. The folder must lie inside the binding's workspace folder and hold no `trace.json` yet.
Otherwise, and for an unbound run, it is a command-line error.

The definition defines Operation and command arguments. The runner parses them with the rest.
An unknown argument is a command-line error.

Without `--detach`, standard output receives exactly the
[run result](../glossary.json#concept.run-result) as one JSON value. With `--detach`, it receives
the announcement described in [Detached runs](#detached-runs). Diagnostics go to standard error.

The exit statuses have these meanings:

- Exit status 0 means the result's status is `ok`.
- Exit status 1 means `blocked` or `failed`, or that the run could not be recorded or its result
  not saved, whatever the work did
  ([When records cannot be written](#when-records-cannot-be-written)).
- Exit status 2 means the command line was malformed or named no known Operation or command.
  In this case, no run is created and no result is written.

## Workspace binding

The runner reads `.concorde/workspace.json` at the root of the worktree it starts in.

When the file is absent, the run is **unbound**. The unbound run has these properties:

- Its trace node is `.concorde/unbound/<run-id>/` of that worktree.
- Its run lock lies under that worktree's `.concorde/locks/`.
- Its workspace is null.
- It takes no workspace lock.

Only when its definition allows unbound runs is the run admitted. Otherwise, the runner refuses
it with `binding_required`. An admitted unbound run works in its
[unbound checkout](#unbound-checkout).

When the file is present, it must satisfy the binding contract and name as `root` the worktree it
lies in. Otherwise, the runner refuses the run with one of these codes:

- `binding_unreadable`
- `binding_invalid`
- `binding_misplaced`

The runner records that refused run as an unbound run of the worktree would be.

Once a bound run holds the workspace lock, its trace node lies in the binding's workspace folder
`traces`. Until then, its trace node lies in the [lobby](#the-lobby) of the binding's `concorde`.
Its locks lie under `locks/` of the binding's `concorde`. Its run context gives every step these
workspace details:

- the name
- the goal
- the Modules
- the branch
- the base commit

When a binding's workspace folder does not exist, the runner refuses the binding with
`binding_invalid`.

Once it holds the workspace lock, the runner reads the binding again. Unless it reads the same
binding as at the parse and the lock it holds is still the workspace's, it refuses the run with
`workspace_retired`.

Whoever retires a workspace, as closing a task does, removes its binding. Still holding the
workspace lock, whoever retires the workspace removes its lock file. A run that waited for that
lock meanwhile therefore takes a file that is no longer there. The runner never takes the lock
file that replaced the one it waited for.

The runner never writes the binding.

## Run identity and trace node

The runner creates the run identity `r-<YYYYMMDD>T<HHMMSS>-<name>-<8 hex digits>` from these values:

- the UTC start time
- the definition's name with `-` written as `_`
- random digits

The runner also creates the run's [trace node](../glossary.json#concept.trace-node) in one of these
places:

- `runs/<run-id>/` of the workspace folder
- the folder `--trace-at` names
- `.concorde/unbound/<run-id>/` for an unbound run

A bound run's node starts in the [lobby](#the-lobby). When the run enters its workspace, the node
moves to its place in the workspace folder. The folder holds these files and nodes:

- `trace.json`, the run's node as [Tracing](../kernel/tracing/contracts.md#contract.tracing.node)
  defines it with the [run trace](contracts.md#contract.execution.run-trace) as content
- `result.json`, the run result exactly as printed
- the run progress file `status.json`
- the nodes of the checks the run ran under `checks/`
- the nodes of the worker runs it launched under `workers/`, each with its
  [run record](../glossary.json#concept.run-record)
- for a [detached run](../glossary.json#concept.detached-run), the runner's output `host.out`

The result lists the worker runs' identities. It names the run's own node as `trace` evidence.

<a id="the-lobby"></a>

**The lobby.** Before it holds the workspace lock, a bound run writes nothing into its workspace
folder, because whoever retires the workspace, as closing a task does, holds that lock while it moves the
folder. Until then, the run's node lies in the lobby, `lobby/<run-id>/` of the binding's `concorde`.
The lobby is next to its run lock and outside every workspace folder. The lobby holds these files:

- its first `trace.json`
- its run progress file while it waits for the lock
- for a [detached run](../glossary.json#concept.detached-run), `host.out`

Once the run holds the lock and the binding passed the second reading, the run **enters** its
workspace. The runner renames the lobby folder to the run's node folder in the workspace folder.
When `runs/` is missing, the runner creates it. Every file the runner wrote moves with the folder,
the runner's open output included. On another file system, the runner copies the folder and
removes the lobby's folder. The runner writes its own output on in the copy. When the runner
cannot move a node, it refuses the run with `run_store_unwritable`. The run stays in the lobby.

A run refused or cancelled before it entered its workspace never enters it. This applies to
refusal or cancellation in any of these rows:

- the binding check
- the lock
- the second reading of the binding

The run's node, with its result, stays in the lobby. Every reader that looks the run up by its
identity finds it there. [Tracing](../kernel/tracing/module.md)'s retention removes it there as it
removes an unbound run. A run with a broken binding is recorded as an unbound run instead, as the
[workspace binding](#workspace-binding) section says.

When it has taken the run lock, the runner writes `trace.json` before any other file of the run.
The runner writes it with status `running` and the metadata it knows then. After `result.json`,
the runner writes `trace.json` again with these details:

- the run's end
- its status (`ok`, `blocked` or `failed`) and outcome (the status, or `cancelled`)
- its duration
- its error
- its metadata
- its inputs as `input` references
- the digests of its files
- its steps with their timings

The metadata hold these values:

- the workspace
- the Modules
- the Operation or command
- the base commit of a bound run and the `HEAD` it started on, or the commit an unbound run examined
- the Concorde commit
- the Protocol version the project binds

## What a definition gives the runner

A definition is plain data and functions the runner calls in its own process. The runner relies
on nothing else of it. The catalogs of [Operations](operations/module.md) and
[Commands](commands/module.md) hand the definition over by name. The other things a definition
declares are for the catalogs and the definition's own steps. These include the ids of its workers
and the Module that provides it.

**Its arguments.** Before parsing, the parse calls a function with the run's command-line parser.
The function adds the definition's own arguments beside the common options. The runner parses
them with the rest. An unknown or malformed argument is a command-line error that starts no run.

**Whether it may run unbound.** The binding is required or optional. When a definition requires a
binding, the runner refuses it unbound in the lock row with `binding_required`. When the binding
is optional, the definition runs unbound in its [unbound checkout](#unbound-checkout). Its steps
learn from the run context that the run may only read.

**Its runtime-path resolver.** This is optional, for a definition that may run unbound. After the
unbound checkout and its submodules exist, the runner calls the resolver once in the lock row
with the checkout's root. The resolver returns relative paths. The runner links them as
[Unbound checkout](#unbound-checkout) step 3 says. Without a resolver, nothing is linked. The
runner reads no configuration of its own to find the paths.

**Its admission of the Modules.** This is optional. After the inputs are admitted, the runner calls
admission once in the admission row with the run context. The context's Modules are then
`--modules` or else the binding's, as names. Admission returns nothing. It may narrow the run
context's Modules and add evidence to it. Method's admissions leave out a Module the workspace
removed with `removed-module` evidence. Admission may instead refuse the run by raising the
refusal the run context's library defines. The refusal holds these details:

- a code
- a message
- the actor that refused
- a reason
- an explanation
- options

The runner turns that refusal into the run's `refused` link, with the reason, explanation and
options the refusal gives. Below that link, the runner puts the refusal as a `component` link of
its actor ([Errors](#errors)). No step runs. Without an admission, the runner takes the Modules as
they are.

**Its steps.** These are an ordered list of functions. Each function receives the run context and
returns "continue" or "stop", as the [Runner](#runner) section says. When a step raises an
exception or returns anything else, the result becomes `failed` with `host-error` evidence.

**Its output contract.** This is an optional JSON Schema the output of an `ok` result must satisfy.
The runner checks it in the composition. When a result's output breaks the contract, the runner
replaces the result by a `failed` one with `invalid-output` evidence and the `invalid_result` link.
Without an output contract, any output passes.

The runner calls an admission or a resolver outside every step. Except for an admission's refusal
or the runner's own refusals of the checkout, what either raises ends the run as a step's exception
does. The result is `failed` with `host-error` evidence and the `host_error` link. The link's cause
names the definition's admission or resolver and keeps the traceback. No step runs. The runner
removes the checkout it made first.

## Runner

The diagram shows the runner's activity with the hand-off of a [detached run](#detached-runs).
The detached run's command does the parsing. The command then starts the runner with the run
identity it announces. Signals follow these rules:

- From the binding check to the execution, a signal at any point goes straight to the composition,
  like a refusal.
- While the parse creates the first records, a signal cancels the run as the binding check begins.
- After the execution, the runner holds a signal until it exits.

Thus nothing cuts the composition or the finish short:

```d2 illustrative
direction: down
exit2: "exit 2: the reason on standard error, no result, no trace node"
launcher: "Detaching command" {
  check: "check the command line; read the binding; create the run identity and its lobby or unbound folder"
  wait: "wait up to 60 s for the run progress file, in the lobby or the run's node"
  announce: "print the announcement, exit 0"
  kill: "kill the runner; still no progress file: remove the run's folder, print detach_failed, exit 1"
  unstarted: "folder or host.out not created: run_unrecorded; runner not started: remove the folder, detach_failed; exit 1"
  check -> unstarted
  check -> wait
  wait -> announce: progress file written
  wait -> kill: runner ended or 60 s passed without one
  kill -> announce: progress file written meanwhile
}
runner: "Execution runner" {
  parse: "parse: command line, definition, binding, node folder; run lock, trace.json, run progress file (in the lobby when bound), or exit 1 unrecorded"
  binding: "binding check"
  lock: "lock: workspace lock, second reading of the binding and entering the workspace (bound), or unbound checkout"
  admission: "admission: Modules, registry, inputs"
  execution: "execution: the definition's steps in order"
  composition: "composition: remove the checkout; compose and check the result"
  finish: "finish: publish result.json, mark finished, write trace.json, release the locks, print, exit"
  parse -> binding -> lock -> admission -> execution -> composition -> finish
  binding -> composition: refused
  lock -> composition: refused
  admission -> composition: refused
  execution -> composition: a step stops or raises
}
runner.parse -> exit2: malformed, unknown or outside Git
launcher.check -> exit2: malformed, unknown or outside Git
launcher.check -> runner.parse: start in a new session with the run identity and directory
```

The runner does what the rows below say, in their order. This document cites each row by its
name. The number gives only the order, so that no row is confused with a step of the definition.

| # | Name | What the runner does | Stops the run when |
| --- | --- | --- | --- |
| 1 | parse | Parse the command line, look up the definition and read the workspace binding, which selects the trace node's place and the locks directory (the worktree's own `.concorde` when the binding is absent or cannot be trusted); only then create the run identity and the run's folder, in the [lobby](#the-lobby) for a bound run, take its [run lock](#run-progress-file), write its first `trace.json` and its run progress file | malformed command line, unknown Operation or command, a directory outside Git, a `--trace-at` folder outside the workspace folder or already holding a node (exit 2, the reason on standard error, no result, no folder); a first record that cannot be created ([When records cannot be written](#when-records-cannot-be-written): exit 1, no result) |
| 2 | binding check | Refuse a binding that could not be read, breaks the binding contract or names another root | an unreadable, invalid or misplaced binding (`failed`) |
| 3 | lock | For a bound run, take the [workspace lock](../glossary.json#concept.workspace-lock), waiting for it up to `--wait` seconds (none by default), refuse the run unless the lock file it holds is still the lock's and the binding read again is the one the parse read, then enter the workspace, moving the run's node from the lobby into the workspace folder; for an unbound run, refuse a definition that needs a binding, then create the [unbound checkout](#unbound-checkout) and work in it from here on | `workspace_busy`, `workspace_retired`, `run_store_unwritable`, `binding_required`, `checkout_unavailable` (`failed`) |
| 4 | admission | Admit the inputs, then run the definition's own admission of its Modules: a definition that reads the [Specs](../glossary.json#concept.spec) leaves out, with `removed-module` evidence, each binding Module the workspace no longer registers and checks the named Modules against the workspace's registry, unless it diagnoses the Specs itself; a definition that reads no Spec takes the Modules as they are | `input_not_admissible`, and from the definition's admission `modules_removed`, `unknown_module`, `specs_unloadable` (`failed`) |
| 5 | execution | Execute the definition's steps in order | a step stops the run with a status |
| 6 | composition | Remove an unbound run's checkout, then compose the run result from the step outcomes, as [Composing the result](#composing-the-result) says, and check it against the run result contract and, for an `ok` result, the definition's output contract | the result or output is invalid (`failed`, `invalid-output` evidence) |
| 7 | finish | Publish `result.json` atomically, mark the run progress file finished, write the final `trace.json`, publish `result.json` again with its `trace-write` evidence when the operating system refused that write, release the workspace lock, remove and release the run lock, print the result and exit | a result that cannot be published or a final `trace.json` that breaks the node contract ([When records cannot be written](#when-records-cannot-be-written): the result printed, exit 1, the run lost) |

Each of the definition's steps returns either "continue" or "stop". A "continue" carries any
output and evidence the step produced. A "stop" carries these details:

- a status
- a summary
- evidence
- unless the status is `ok`, the run's error link

Steps of one run share the run context. The context holds these things:

- the workspace binding
- the worktree the run works in
- for an unbound run, also the worktree it started in and the commit it examines
- the run's node folder
- the Modules
- the admitted inputs
- the output so far
- a state the definition owns
- the run record of the latest worker launch

The runner never skips, repeats or reorders steps. Any repetition, such as
[resume rounds](../glossary.json#concept.resume-round), happens inside one step.

When a step raises an exception, the result becomes `failed` with `host-error` evidence. The
evidence names these details:

- the step
- the error type
- the message

The cause of the result's error is a `component` link. The link holds these details:

- the exception's type
- its message
- its command output
- where it was raised
- the path of the full traceback in the run's node folder

From the binding check to the execution, an exception the runner itself raises outside every step,
other than a refusal, ends the run the same way. The cause's actor is
`Execution runner (<command line>)`. Between steps, a failed write of the run's trace node never
changes the run, like that of a later run progress file.

On `SIGINT` or `SIGTERM`, the runner stops its running step. The step ends every worker process it
started through the worker harness. The runner finishes with a `failed` result with `cancelled`
evidence naming the signal. The runner handles both signals from the parse to its exit. While
the first records are created, the runner holds an arriving signal. As soon as the binding check
begins, that signal cancels the run, no step running. Once the execution ended, an arriving signal
changes nothing while the checkout is removed or the result composed and written. The run
finishes as composed.

The run's `cancelled` link names every worker run the run's steps started. The link's evidence of
kind `worker-run` points at each worker run's node, with its
[progress file](../glossary.json#concept.progress-file). `worker_runs` lists those worker runs.
When a worker run starts, the step tells the run context that worker run's identity, as the worker
harness tells it. The step does not wait until the worker run returns to tell the run context.

The composition and the finish run whatever happened before them. A refusal in any of these rows
still writes and prints a result:

- the binding check
- the lock
- the admission

The result has the refusal code as `refused` evidence. Its error's cause is the refusal of the
workspace binding, the unbound checkout or the [run store](../glossary.json#concept.run-store),
with its message. Such messages include these details:

- Git's output for a checkout it refused
- the holder of a busy workspace's lock
- what retired a workspace
- the registered Modules for an unknown one

While the lock is still held, the runner writes the result. A run admitted to the workspace after
this one therefore always finds its result written. The converse does not hold. Until the runner
ends, whoever reads the result may still find the lock held. A caller that wants to start the
next run therefore waits for the lock to be free, not for the result.

Whenever the status is not `ok`, the runner also writes the
[error chain](../glossary.json#concept.error-chain), rendered as indented text, to standard error.

The runner publishes `result.json` atomically. It writes the whole result under another name in
the run's folder and renames it into place. An observer that reads it without holding any lock
therefore finds no result or the complete one, never part of it. A workflow step or the task level
is such an observer. The run progress file and `trace.json` are replaced the same way.

### Composing the result

The steps build the run's output in the run context. Every later step finds it there as the output
so far. A step may set the output so far itself. When a "continue" carries output, it replaces the
output so far with that output whole. When a "continue" carries none, it keeps the output so far.
The runner never merges two outputs. The evidence of every outcome is appended to the runner's
own, in the order the steps ran. The result is then composed from what the steps left.

When a step stopped the run, the result takes these details, whatever the status:

- that step's status
- that step's summary
- that step's error
- the output so far as its output

When every step continued, the result is `ok`, with the output so far as its output. The result
takes the runner's own summary, `<name> finished for <Modules>.`. When the run has no Modules,
the summary is `<name> finished.`. A definition whose summary must say more ends with a step that
stops the run with `ok` and that summary. The reviews and `task-validation` do this.

When a step stopped the run with a status other than `ok` but no error, the result's error is the
runner's `missing_error` link ([Errors](#errors)).

When a result or an `ok` output breaks its contract, the result becomes `failed` with output null
and the runner's `invalid_result` link. When the earlier error is a well-formed link, that error
becomes the cause. A result whose error is not the run's own link breaks the contract. That link
has level `operation` for an Operation and `command` for an execution command. The replacement
keeps only what satisfies the contract of what the steps left. The replacement leaves out these
items:

- each host evidence item that breaks the contract, counted in its `invalid-output` evidence
- a `worker` that is no object
- each Module or worker run that is no name

Before the replacement is written, the runner checks it against the contract again.

### When records cannot be written

A run's records are what every observer knows it by. The runner therefore treats a failure to
write them apart from a failure of the run's own work, in exactly two ways. Only these cases allow
an accepted command line to write no result
([req.execution.one-result](requirements.md#req.execution.one-result)):

- the two record-write cases below
- a `detach_failed` launch
- a runner killed by a signal it cannot handle

When a detaching command cannot create the run's folder or the runner's output `host.out`, it
treats the failure as the first case. It starts no runner ([Detached runs](#detached-runs)).

**Before any step.** The runner refuses the run before any step runs when any of these conditions
holds:

- The parse cannot create the run's folder.
- The parse cannot take the run lock.
- The parse cannot write the first run progress file.
- The first `trace.json` breaks the node contract.

The runner writes no result and nothing on standard output. It writes its `run_unrecorded` link
to standard error. That link's cause is the `Execution (run store)` link with the operating
system's or Tracing's refusal. If it took the run lock, the runner releases it. The runner exits
with status 1. A folder it created may stay behind, holding no result and no lock anybody holds.

**After the composition.** When publishing `result.json` fails or the final `trace.json` breaks the
node contract, the runner writes nothing more. It still prints the result it composed on standard
output. The runner writes its `result_unsaved` link to standard error. The link's causes are the
`Execution (run store)` link of the failed write and, when the result has its own error, that
error. The runner releases both locks. Whatever the result's status, the runner exits with status
1. The run counts as lost.

Without a published `result.json`, every observer finds the run lost, as a run whose runner was
killed. There is no result and a run lock nobody holds. When only the final `trace.json` failed,
the published result stands for whoever reads it. The run's trace node still reads as lost:
its status is `running`, with nobody holding its run lock. The run's work may be done. Before
running it again, whoever started the run learns from the printed result what it did. A failed
write of a later run progress file never changes the run.

When the operating system refuses a write of `trace.json`, that refusal is neither case. This
applies at these times:

- at the run's start
- while a step runs
- at the run's end

Tracing is best-effort for the run, never silent
([req.execution.trace-write-reported](requirements.md#req.execution.trace-write-reported)). The run
goes on as if the write succeeded. Its result names each refused write as `trace-write` evidence,
by the run identity. The evidence holds these details:

- the node's file
- the moment
- the error

The final write follows the result. When the operating system refuses that write, the runner
publishes the result again with that evidence added, before it releases the locks. The runner
prints that result. The trace node then still says what it said before. When every earlier write
succeeded, its status is `running`. Once nobody holds the run lock, that status reads as lost.

## Unbound checkout

An admitted [unbound run](../glossary.json#concept.unbound-run) works in its
[unbound checkout](../glossary.json#concept.unbound-checkout), never in the worktree it started in.
That starting worktree is here called its origin. The runner follows these steps:

1. The runner resolves the origin's `HEAD` to a commit. It creates the checkout
  `.claude/worktrees/unbound-<run-id>` of the repository's primary worktree, the first worktree
  `git worktree list` names. The runner uses `git worktree add --detach` of that commit from the
  origin's repository, with none of the repository's Git hooks run. A worker runs only in a
  worktree directly inside `.claude/worktrees/` of its primary worktree. The checkout lies there
  because that is where the worker harness lets a worker run
  ([Workers](../worker-harness/workers/launch.md#placement)). A run identity always holds an
  upper-case `T`, which no task name may hold. The checkout therefore never takes a task worktree's
  place. Before creating anything, the runner asks Git whether the primary worktree ignores that
  path. The checkout therefore never appears there as untracked files. Only Git's administrative
  files of the repository and the checkout's own directory change. No other file of the origin or
  of the primary worktree changes, and not their index.
2. Each submodule the commit records receives the same checkout treatment when both conditions
  hold: the origin checked it out, and its repository holds the recorded commit. The runner uses
  `git worktree add --detach` of that commit from the submodule's repository. When the origin's
  checkout is sparse, the runner uses the origin's sparse-checkout patterns. It uses each pattern
  as Git lists it, spaces included, read back in the origin's own mode, cone or not. `submodule`
  evidence names each submodule so checked out. When the origin did not check out a submodule or Git cannot check
  it out or populate it, the submodule stays empty, as in a fresh clone. `submodule-absent` evidence
  names why. Before any step runs, the runner removes a checkout Git began and could not finish.
  `checkout-not-removed` evidence names whatever of it could not be removed.
3. When the definition has a runtime-path resolver, the runner calls it with the checkout's root
  and links what it returns. The runner itself reads no configuration. For Method's Operations,
  the resolver returns the checked-out
  [worker configuration](../glossary.json#concept.worker-configuration)'s `runtime` (default
  `.venv` and `node_modules`). When that file is invalid, the resolver returns nothing. Each
  relative runtime path so named that exists in the origin and that Git ignores receives a
  symbolic link in the checkout to the origin's path. The runner records `environment` evidence.
  Inside the checkout, the runner creates the directories leading to the path that the checkout
  lacks. The run's checks and workers only read the path, the checks inside their read-only
  boundary. When Git does not ignore a runtime path, the runner does not link it, with
  `environment-not-linked` evidence, since the commit holds it. With the same evidence, the runner
  also does not link a path the checkout already holds or one whose directories lead out of the
  checkout. Such directories can lead through an earlier link. When the origin lacks a runtime
  path, the runner passes it over.
4. From here on, the run context's worktree is the checkout. The steps work there, and with them
  whatever they read. In Method's Operations, this includes the Specs, the grant, the workers and
  the worker harness's audit. The worker configuration committed in the checkout chooses the
  workers' backends, models and limits. The run context keeps the origin and the commit. The
  origin's `.concorde` keeps the run's trace node and run lock. The result names the commit as
  `commit`. The run's error link names it as `… (unbound, <origin> at <commit>)`. `checkout`
  evidence names the commit and the checkout's path.
5. Before composing the result, however the steps ended, the runner removes the links, the
  submodule checkouts and the checkout with `git worktree remove --force`. This includes a refusal,
  a raised error or a cancellation. The runner then removes whatever is left of the checkout's
  directory, never the `.claude/worktrees/` that holds it. When Git refuses a removal, the runner
  does it directly, deleting the directory and pruning Git's worktree list. The runner reports
  that removal with `checkout-not-removed` evidence. The evidence says whether the directory is
  gone, or what is left of it, and whether the prune succeeded. Whatever is left is removed later
  with `git worktree remove --force <path>` and `git worktree prune`, which the evidence names.
  None of it ever changes the result's status. When a runner is killed outside its control, by
  `SIGKILL`, it leaves the checkout and its worktree entry behind. `git worktree remove --force`
  of that path removes them.

When any of these conditions holds, the runner refuses the run with `checkout_unavailable`:

- The origin's `HEAD` names no commit.
- The repository has no primary worktree.
- The primary worktree's Git does not ignore the checkout's path.
- The path is taken.
- Git refuses the checkout.

The refusal occurs in the lock row, where an unbound run creates its checkout. Its cause is the
`Execution (unbound checkout)` link with Git's output. Nothing is left behind. The runner never
falls back to working in the origin.

## Detached runs

With `--detach`, the command follows these steps:

1. The command checks the command line. A malformed command line starts nothing, with exit status
  2.
2. The command reads the workspace binding to select the node folder as the parse does.
3. The command chooses the run identity.
4. The command creates the run's folder, in the [lobby](#the-lobby) for a bound run and its unbound
  node otherwise.
5. The command starts the runner as a process of its own, in a new session, handing it the
  identity. The runner therefore records in that folder and writes its output to `host.out`
  there.

That process is the host's `concorde` command run again with the same command line. Before it
looks the definition up, the process loads the definitions the installed parts register, as the
first command did. The command then waits until the run progress file exists. Until the run
enters its workspace, that file is in the lobby. Once the run enters its workspace, the file is
in its node there. The command prints
`{run_id, kind, name, host_pid, trace, progress, result, lobby}` with exit status 0. The announcement
fields give these locations:

- `trace` is the run's node folder in the workspace folder, or its unbound node.
- `progress` and `result` are its `status.json` and `result.json`, where they lie once the run
  entered its workspace.
- `lobby` is the run's lobby folder, null for an unbound run. A run refused before it entered its
  workspace keeps its progress file and result there.

When the command cannot create the run's folder or open the runner's output `host.out` there, it
starts no runner. It reports `run_unrecorded` with exit status 1. It reports this as a foreground
run whose first records cannot be created does
([When records cannot be written](#when-records-cannot-be-written)). When the runner process cannot
be started, the command removes the run's folder. It reports `detach_failed` with the same fields,
`host_pid` null, and exit status 1.

An existing run progress file always wins. Once it exists, the run is announced, even when the
runner already ended by then. The run exists, and its result tells how it ended. When the run has
no result, its lost state tells how it ended. Only when no run progress file appeared by either
limit does the command kill the runner with its process group and look once more. The limits are
the runner's end or the announcement wait running out, 60 seconds from its start. A progress file
written meanwhile still announces the run. Otherwise, the command reports `detach_failed`.

Before any step, the runner writes its first run progress file, or runs none
([When records cannot be written](#when-records-cannot-be-written)). Therefore, when no progress
file appeared, no step ran. The command removes the run's folder, in the lobby or unbound, and a
run lock file the runner left. Nothing of the run therefore remains. The command prints the same
fields with an `error` link `detach_failed` and exit status 1. That link names how the runner
ended and the end of its output. An unannounced runner thus never starts its run later. Running
the command again starts a new run with nothing to repeat.

The new session frees the runner from the command, not from the PID namespace the command runs
in. When a namespace ends, a runner detached inside it is killed with it. Such a namespace can
be that of a sandboxed Bash call
([A detached run lives only as long as the PID namespace it started in](module.md#detached-namespace)).

## Run progress file

Before it writes anything in the run's folder, apart from `host.out` of a detached run, the runner
takes the [run lock](../glossary.json#concept.run-lock). This is an exclusive `flock` on the file
`locks/runs/<run-id>.lock` of the `.concorde` that holds its locks. The runner creates that file.
It holds the lock until after all these records are written:

- the result
- the finished progress file
- the final `trace.json`

The runner holds the lock through a descriptor the processes it starts do not inherit. A worker
or check that outlives the runner therefore never keeps its run alive. As it exits, the runner
removes the file, still holding it. When a runner is killed with `SIGKILL`, its file stays but is
not held. An observer tells a running run from a dead one by the file's existence and by trying
the lock for an instant. The observer tries it shared and without waiting (`runner_alive`).
Whichever PID namespace holds it, the operating system's lock table `/proc/locks` shows the same
for the file's inode. A run without `result.json` whose lock nobody holds is `lost`.

The runner writes `status.json` atomically in the run's folder. Until the run enters its
workspace, that folder is in the lobby. The runner writes the file at these times:

- when the folder is created
- while it waits for the workspace lock
- once it holds the workspace lock
- before each step
- when the result is written

The file holds these fields:

| Field | Content |
| --- | --- |
| `kind` | `operation` or `command` |
| `run_id`, `name`, `workspace`, `worktree`, `modules` | the run's identity, definition, workspace (null when unbound), the worktree it works in (an unbound run's checkout once it exists) and Modules |
| `commit` | the commit an unbound run examines once its checkout exists; null otherwise |
| `phase` | `running`, then `finished` once `result.json` is written |
| `step` | the step running now, `workspace-lock` while the run waits for the workspace lock, or null |
| `waiting_for` | while this run waits for the workspace lock, its holder as the holder line [Tracing](../kernel/tracing/contracts.md#locks) keeps in the lock file describes it: a run's runner, such as `implement run <run-id>`, or another taker such as a task's merge or close, with its process, start time and, when its holder line names them, its session and task; null otherwise |
| `status`, `summary` | null while running; the result's status and summary once finished |
| `host_pid` | the runner's process identifier in its own PID namespace, for display and for the process that started it; never a sign that the run still runs |
| `started_at`, `updated_at` | UTC times |

Except for the first, a failed write never changes the run. Without the first write, the run runs
no step ([When records cannot be written](#when-records-cannot-be-written)).

## Errors

When a run does not end `ok`, the result's `error` is the run's own link of the
[error chain](../kernel/tracing/contracts.md#contract.tracing.error). Its level is `operation` for
an Operation and `command` for an execution command. The actor names the run and its workspace
in one of these forms:

- `Operation <name> <run-id> (workspace <workspace>)`
- `Command <name> <run-id> (workspace <workspace>)`
- for an unbound run, `… (unbound, <origin> at <commit>)`

Here `<origin>` is the worktree the run started in, never its checkout. When the run was refused
before its checkout existed, the actor omits ` at <commit>`. The link also holds these details:

- a code
- a detail naming the paths and the messages concerned and ending with the Modules the run works
  on, `(Modules: <id>, …)` or `(Modules: none)`
- the reason the run cannot handle the error
- the options it offers with a recommendation
- as causes, the errors it received, unchanged

A step that stops the run builds that link itself. The runner builds it as follows.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Refusal before the steps began | `refused` | `decision` for `workspace_busy`; `scope` for `binding_required`; `environment` for `binding_unreadable`, `workspace_retired`, `run_store_unwritable` and `checkout_unavailable`; for a refusal of the definition's admission, the reason it gives, such as `scope` for Method's `specs_unloadable`; `input` otherwise | the `component` link of `Execution (workspace binding)` for a binding refusal and `workspace_retired`, `Execution (unbound checkout)` for `checkout_unavailable`, the admission's own component, such as `Method (Module admission)`, for a refusal of the definition's admission, or `Execution (run store)` otherwise, with the refusal's code and message |
| A step raised, or the runner raised outside every step | `host_error` | `capability` | the exception's `component` link |
| Cancelled | `cancelled` | `environment` | none |
| Invalid result or output | `invalid_result` | `capability` | the error the run had, if any |
| A step stopped without an error | `missing_error` | `capability` | none |

The two failures to write the run's records are no result's error
([When records cannot be written](#when-records-cannot-be-written)). The runner writes their
`component` link to standard error. Its actor is `Execution runner (<command line>)`, its code is
`run_unrecorded` or `result_unsaved`, and its reason is `environment`.

A step keeps the link of whatever it called unchanged as a cause under the run's own link. This
includes the actor, code and reason. Check execution gives its failures as its own link.
`service_error` of [the check service](checks/service.md#check-executions-error-as-a-link) makes
that link. Its actor is `Check execution`, with the reason its code maps to. The
[Issues](../issues/interface.md) store gives each refusal its own link, of the actor
`Issues (concorde issues)`. When a component reports without a link, that report is the concern
of the definition whose step calls it. Method's steps, for one, turn Spec tooling's own error
record into a link as
[How an Operation runs its workers](../method/workers.md#errors-of-the-worker-sequence) says.
