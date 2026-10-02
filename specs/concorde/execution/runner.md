# How a run is executed

The exact behaviour of the [Execution runner](../glossary.json#concept.execution-runner): the
command lines, the [workspace binding](../glossary.json#concept.workspace-binding) it reads, what
the runner does from the parse to the finish, the [run progress file](../glossary.json#concept.run-progress-file) and how refusals
and failures become a result. The Operation or execution command a command line names is the run's
definition: its steps, its arguments, whether it may run unbound and its output contract. The
envelope is the [run result contract](contracts.md#contract.execution.run-result) and the binding
the [workspace binding contract](contracts.md#contract.execution.workspace-binding). What an
[Operation](../glossary.json#concept.operation) adds, its worker sequence, is in
[How an Operation runs its workers](../method/workers.md).

## Command lines

```text
concorde run <operation> [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [--trace-at <folder>] [operation arguments]
concorde <command>       [--modules <id>[,<id>…]] [--input <run-id>]… [--detach] [--wait <seconds>] [--trace-at <folder>] [command arguments]
```

- `<operation>` is a name from the [Operation catalog](../glossary.json#concept.operation-catalog);
  `<command>` is one of the [execution commands](../glossary.json#concept.execution-command)
  `task-validation`, `delivery` and `scaffold`. `concorde run` naming an execution command is a
  command-line error that names the command to use instead.
- The run works on the worktree the command starts in: the Git worktree containing the current
  directory, or for an [unbound run](../glossary.json#concept.unbound-run) its
  [unbound checkout](#unbound-checkout). A directory outside every Git worktree is a command-line
  error.
- `--modules` names the Modules the run works on. Without it a bound run works on the binding's
  Modules that the workspace still registers, and an
  [unbound run](../glossary.json#concept.unbound-run) on none. Every named
  [Module](../glossary.json#concept.module) must be registered in the worktree.
- Each `--input` names a run whose result is `ok` and whose workspace is this run's workspace, or,
  for an unbound run, a run without a workspace; its saved `output` is admitted, with its name, as
  material of the run. Any other run is refused with `input_not_admissible`.
- `--wait <seconds>` (default 0) is how long a bound run waits for a busy workspace's lock before
  it is refused with `workspace_busy`; a negative value is a command-line error. An unbound run
  takes no lock and ignores it. A run waits in the [lobby](#the-lobby), never in its workspace
  folder.
- `--trace-at <folder>` places the run's [trace node](../glossary.json#concept.trace-node) in that
  folder instead of `runs/<run-id>/` of the workspace folder. It is how a
  [workflow step](../glossary.json#concept.workflow-step) nests the run it starts inside its own
  node. The folder must lie inside the binding's workspace folder and hold no `trace.json` yet;
  otherwise, and for an unbound run, it is a command-line error.
- Operation and command arguments are defined by the definition and parsed with the rest; an
  unknown argument is a command-line error.
- Without `--detach`, standard output receives exactly the
  [run result](../glossary.json#concept.run-result) as one JSON value; with it, the announcement
  described in [Detached runs](#detached-runs). Diagnostics go to standard error.
- Exit status 0 means the result's status is `ok`, 1 means `blocked` or `failed`, and 2 means the
  command line was malformed or named no known Operation or command, in which case no run is
  created and no result is written.

## Workspace binding

The runner reads `.concorde/workspace.json` at the root of the worktree it starts in:

- When the file is absent, the run is **unbound**: its trace node is `.concorde/unbound/<run-id>/`
  of that worktree and its run lock lies under that worktree's `.concorde/locks/`, its workspace is
  null, it takes no workspace lock, and it is admitted only when its definition allows unbound runs;
  otherwise it is refused with `binding_required`. An admitted unbound run works in its
  [unbound checkout](#unbound-checkout).
- When the file is present, it must satisfy the binding contract and name as `root` the worktree
  it lies in; otherwise the run is refused with `binding_unreadable`, `binding_invalid` or
  `binding_misplaced`, and it is recorded as an unbound run of the worktree would be.
- A bound run's trace node lies in the binding's workspace folder `traces` once the run holds the
  workspace lock, and in the [lobby](#the-lobby) of the binding's `concorde` until then; its locks
  lie under `locks/` of the binding's `concorde`, and its run context gives every step the
  workspace's name, goal, Modules, branch and base commit. A binding whose workspace folder does
  not exist is refused with `binding_invalid`.
- Once it holds the workspace lock, the runner reads the binding again and refuses the run with
  `workspace_retired` unless it reads the same binding as at the parse, and unless the lock it
  holds is still the workspace's: whoever retires a workspace, as closing a task does, removes
  its binding and, still holding the workspace lock, its lock file, so a run that waited for that
  lock meanwhile takes a file that is no longer there. The runner never takes the lock file that
  replaced the one it waited for.

The runner never writes the binding.

## Run identity and trace node

The runner creates the run identity `r-<YYYYMMDD>T<HHMMSS>-<name>-<8 hex digits>` from the UTC start
time, the definition's name with `-` written as `_`, and random digits, and the run's
[trace node](../glossary.json#concept.trace-node): `runs/<run-id>/` of the workspace folder, the
folder `--trace-at` names, or `.concorde/unbound/<run-id>/` for an unbound run. A bound run's node
starts in the [lobby](#the-lobby) and moves to its place in the workspace folder when the run
enters its workspace. The folder holds
`trace.json`, the run's node as [Tracing](../kernel/tracing/contracts.md#contract.tracing.node) defines it
with the [run trace](contracts.md#contract.execution.run-trace) as content; `result.json`, the run
result exactly as printed; the run progress file `status.json`; the nodes of the checks the run ran
under `checks/`; the nodes of the worker runs it launched under `workers/`, each with its
[run record](../glossary.json#concept.run-record); and for a
[detached run](../glossary.json#concept.detached-run) the runner's output `host.out`. The result
lists the worker runs' identities and names the run's own node as `trace` evidence.

<a id="the-lobby"></a>

**The lobby.** A bound run writes nothing into its workspace folder before it holds the workspace
lock, since whoever retires the workspace, as closing a task does, holds that lock while it moves
the folder. Until then its node lies in the lobby, `lobby/<run-id>/` of the binding's `concorde`,
next to its run lock and outside every workspace folder: its first `trace.json`, its run progress
file while it waits for the lock and, for a [detached run](../glossary.json#concept.detached-run),
`host.out`. Once the run holds the lock and the binding passed the second reading, the run
**enters** its workspace: the runner renames the lobby folder to the run's node folder in the
workspace folder, creating `runs/` when it is missing, so every file it wrote, the runner's open
output included, moves with it. On another file system it copies the folder, removes the lobby's
and writes its own output on in the copy. A node it cannot move refuses the run with
`run_store_unwritable`, and the run stays in the lobby. A run refused or cancelled before it entered
its workspace, in the binding check, the lock or the second reading of the binding, never enters
it: its node, with its result, stays in the lobby, where every reader that looks a run up by its
identity finds it, and where [Tracing](../kernel/tracing/module.md)'s retention removes it as it removes an
unbound run. A run with a broken binding is recorded as an unbound run instead, as the
[workspace binding](#workspace-binding) section says.

The runner writes `trace.json` when it has taken the run lock, before any other file of the run,
with status `running` and the metadata it knows then, and again after `result.json`, with the run's
end, its status (`ok`, `blocked` or `failed`) and outcome (the status, or `cancelled`), its duration,
error, metadata, inputs as `input` references, the digests of its files, and the steps with their
timings. Its metadata are the workspace, the Modules, the Operation or command, the base commit of a
bound run and the `HEAD` it started on, or the commit an unbound run examined, the Concorde commit
and the Protocol version the project binds.

## Runner

The runner's activity, with the hand-off of a [detached run](#detached-runs), whose command does
the parsing and then starts the runner with the run identity it announces. A signal at any point
from the binding check to the execution, like a refusal, goes straight to the composition:

```d2 illustrative
direction: down
exit2: "exit 2: the reason on standard error, no result, no trace node"
launcher: "Detaching command" {
  check: "check the command line; read the binding; create the run identity and its lobby or unbound folder"
  wait: "wait up to 60 s for the run progress file, in the lobby or the run's node"
  announce: "print the announcement, exit 0"
  kill: "kill the runner; still no progress file: remove the run's folder, print detach_failed, exit 1"
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
name; the number gives only the order, so that no row is confused with a step of the definition.

| # | Name | What the runner does | Stops the run when |
| --- | --- | --- | --- |
| 1 | parse | Parse the command line, look up the definition and read the workspace binding, which selects the trace node's place and the locks directory (the worktree's own `.concorde` when the binding is absent or cannot be trusted); only then create the run identity and the run's folder, in the [lobby](#the-lobby) for a bound run, take its [run lock](#run-progress-file), write its first `trace.json` and its run progress file | malformed command line, unknown Operation or command, a directory outside Git, a `--trace-at` folder outside the workspace folder or already holding a node (exit 2, the reason on standard error, no result, no folder); a first record that cannot be created ([When records cannot be written](#when-records-cannot-be-written): exit 1, no result) |
| 2 | binding check | Refuse a binding that could not be read, breaks the binding contract or names another root | an unreadable, invalid or misplaced binding (`failed`) |
| 3 | lock | For a bound run, take the [workspace lock](../glossary.json#concept.workspace-lock), waiting for it up to `--wait` seconds (none by default), refuse the run unless the lock file it holds is still the lock's and the binding read again is the one the parse read, then enter the workspace, moving the run's node from the lobby into the workspace folder; for an unbound run, refuse a definition that needs a binding, then create the [unbound checkout](#unbound-checkout) and work in it from here on | `workspace_busy`, `workspace_retired`, `run_store_unwritable`, `binding_required`, `checkout_unavailable` (`failed`) |
| 4 | admission | Admit the run: settle the Modules, leaving out with `removed-module` evidence each binding Module the workspace no longer registers; check the named Modules against the workspace's registry unless the definition diagnoses the Specs itself; admit the inputs | `modules_removed`, `unknown_module`, `specs_unloadable`, `input_not_admissible` (`failed`) |
| 5 | execution | Execute the definition's steps in order | a step stops the run with a status |
| 6 | composition | Remove an unbound run's checkout, then compose the run result from the step outcomes, as [Composing the result](#composing-the-result) says, and check it against the run result contract and, for an `ok` result, the definition's output contract | the result or output is invalid (`failed`, `invalid-output` evidence) |
| 7 | finish | Publish `result.json` atomically, mark the run progress file finished, write the final `trace.json`, release the workspace lock, remove and release the run lock, print the result and exit | a final write that fails ([When records cannot be written](#when-records-cannot-be-written): the result printed, exit 1, the run lost) |

- Each of the definition's steps returns either "continue", with any output and evidence it
  produced, or "stop", with a status, a summary, evidence and, unless the status is `ok`, the
  run's error link. Steps of one run share the run context: the workspace binding, the
  worktree the run works in, for an unbound run also the worktree it started in and the commit it
  examines, the run's node folder, the Modules, the admitted inputs, the output so far, a state the
  definition owns, and the run record of the latest worker launch. The runner never skips, repeats
  or reorders steps; any repetition, such as [resume rounds](../glossary.json#concept.resume-round),
  happens inside one step.
- An exception raised by a step becomes a `failed` result with `host-error` evidence naming the
  step, the error type and message; the cause of its error is a `component` link with the
  exception's type, message and command output, where it was raised and the path of the full
  traceback in the run's node folder.
- On `SIGINT` or `SIGTERM` the runner stops its running step, ends every worker process the run
  started through Workers and finishes with a `failed` result with `cancelled` evidence naming the
  signal. Its `cancelled` link names every worker run the run started, with evidence of kind
  `worker-run` pointing at each worker run's node, with its
  [progress file](../glossary.json#concept.progress-file), and `worker_runs` lists them: the
  runner learns each worker run's identity when the worker run starts, not when it returns.
- The composition and the finish run whatever happened before them. A refusal in the binding
  check, the lock or the admission still writes and prints a result, with the refusal code as
  `refused` evidence and an error whose cause is the refusal of the workspace binding, the
  unbound checkout or the [run store](../glossary.json#concept.run-store) with its message, such as Git's output for a checkout it
  refused, the holder of a busy workspace's lock, what retired a workspace or the
  registered Modules for an unknown one.
- The result is written while the lock is still held, so a run admitted to the workspace after
  this one always finds its result written. The converse does not hold: whoever reads the result
  may still find the lock held until the runner has ended, so a caller that wants to start the
  next run waits for the lock to be free, not for the result.
- Whenever the status is not `ok`, the runner also writes the
  [error chain](../glossary.json#concept.error-chain), rendered as indented text, to standard error.
- The runner publishes `result.json` atomically: it writes the whole result under another name in
  the run's folder and renames it into place, so an observer that reads it without holding any
  lock, as a workflow step or the task level does, finds no result or the complete one, never part
  of it. The run progress file and `trace.json` are replaced the same way.

### Composing the result

The steps build the run's output in the run context, where every later step finds it as the output
so far. A step may set the output so far itself, and a "continue" that carries output replaces the
output so far with it whole, while one that carries none keeps it; the runner never merges two
outputs. The evidence of every outcome is appended to the runner's own, in the order the steps ran.
The result is then composed from what the steps left:

- When a step stopped the run, the result takes that step's status, summary and error, and the
  output so far as its output, whatever the status.
- When every step continued, the result is `ok`, with the output so far as its output and the
  runner's own summary, `<name> finished for <Modules>.`, or `<name> finished.` when the run has no
  Modules. A definition whose summary must say more ends with a step that stops the run with `ok`
  and that summary, as the reviews and `task-validation` do.
- A step that stopped the run with a status other than `ok` but no error leaves the runner's
  `missing_error` link as the result's error ([Errors](#errors)).
- A result or an `ok` output that breaks its contract becomes `failed` with output null and the
  runner's `invalid_result` link, its earlier error as the cause.

### When records cannot be written

A run's records are what every observer knows it by, so the runner treats a failure to write them
apart from a failure of the run's own work, and in exactly two ways. These are the only cases, with
a `detach_failed` launch and a runner killed by a signal it cannot handle, in which an accepted
command line writes no result
([req.execution.one-result](requirements.md#req.execution.one-result)).

- **Before any step.** When the parse cannot create the run's folder, take its run lock, write its
  first `trace.json` or write its first run progress file, the run is refused before any step
  runs: the runner writes no result and nothing on standard output, writes its `run_unrecorded`
  link to standard error, whose cause is the `Execution (run store)` link with the operating
  system's or Tracing's refusal, releases the run lock if it took it and exits with status 1. A
  folder it created may stay behind, holding no result and no lock anybody holds.
- **After the composition.** When publishing `result.json` or writing the final `trace.json` fails,
  the runner writes nothing more, still prints the result it composed on standard output, writes
  its `result_unsaved` link to standard error, whose causes are the `Execution (run store)` link of
  the failed write and the result's own error when it has one, releases both locks and exits with
  status 1, whatever the result's status. The run counts as lost. Without a published
  `result.json`, every observer finds it lost, as a run whose runner was killed: no result and a
  run lock nobody holds. When only the final `trace.json` failed, the published result stands for
  whoever reads it, while the run's trace node, still `running` with nobody holding its run lock,
  reads as lost. Its work may have been done: whoever started the run learns from the printed
  result what it did before running it again. A failed write of a later run progress file never
  changes the run.

## Unbound checkout

An admitted [unbound run](../glossary.json#concept.unbound-run) works in its
[unbound checkout](../glossary.json#concept.unbound-checkout), never in the worktree it started in,
here called its origin:

1. The runner resolves the origin's `HEAD` to a commit and creates the checkout
   `.claude/worktrees/unbound-<run-id>` of the repository's primary worktree, the first worktree
   `git worktree list` names, with `git worktree add --detach` of that commit from the origin's
   repository, with none of the repository's Git hooks run. It lies there because a worker runs
   only in a worktree directly inside `.claude/worktrees/` of its primary worktree
   ([Workers](../worker-harness/workers/launch.md#placement)). A run identity always holds an upper-case `T`, which
   no task name may hold, so the checkout never takes a task worktree's place. Before creating
   anything the runner asks Git whether the primary worktree ignores that path, so that the
   checkout never appears there as untracked files. Only Git's administrative files of the
   repository and the checkout's own directory change; no other file of the origin or of the
   primary worktree, and not their index.
2. Each submodule the commit records that the origin has checked out, and whose repository holds
   the recorded commit, is checked out in the checkout the same way, `git worktree add --detach` of
   that commit from the submodule's repository, with the origin's sparse-checkout patterns when
   the origin's checkout is sparse; `submodule` evidence names each. A submodule the origin has not
   checked out, or that Git cannot check out, stays empty, as in a fresh clone, with
   `submodule-absent` evidence naming why.
3. Each relative path of the checked-out worker configuration's `runtime` (default `.venv` and
   `node_modules`) that exists in the origin and that Git ignores is linked into the
   checkout as a symbolic link to the origin's, with `environment` evidence; the run's checks and
   workers only read it, the checks inside their read-only boundary. A runtime path Git does not
   ignore is not linked, with `environment-not-linked` evidence, since the commit holds it.
4. From here on the run context's worktree is the checkout: the Specs, the grant, the workers,
   Workers' audit and the steps all work there, and the
   [worker configuration](../glossary.json#concept.worker-configuration) committed in the checkout
   chooses the workers' backends, models and limits. The run context keeps the origin, whose
   `.concorde` keeps the run's trace node and run lock, and the commit, which the result names as `commit` and the run's
   error link as `… (unbound, <origin> at <commit>)`. `checkout` evidence names the commit and the
   checkout's path.
5. Before the result is composed, however the steps ended, including a refusal, a raised error or
   a cancellation, the runner removes the links, the submodule checkouts and the checkout with
   `git worktree remove --force`, then whatever is left of the checkout's directory, never the
   `.claude/worktrees/` that holds it. A removal Git refuses is done directly, deleting the
   directory and pruning Git's worktree list, and reported with `checkout-not-removed` evidence; it
   never changes the result's status. A runner killed outside its control, by `SIGKILL`, leaves the
   checkout and its worktree entry behind, which `git worktree remove --force` of that path
   removes.

When the origin's `HEAD` names no commit, the repository has no primary worktree, the primary
worktree's Git does not ignore the checkout's path, the path is taken, or Git refuses the checkout,
the run is refused in the
lock row, where an unbound run creates its checkout, with `checkout_unavailable`, whose cause is
the `Execution (unbound checkout)` link with Git's output, and nothing is left behind; the runner
never falls back to working in the origin.

## Detached runs

With `--detach` the command checks the command line (a malformed one starts nothing, with exit
status 2), reads the workspace binding to select the node folder as the parse does, chooses the
run identity, creates the run's folder, in the [lobby](#the-lobby) for a bound run and its unbound
node otherwise, and starts the runner as a process of its own, in a new session, handing it the
identity, so that the runner records in that folder and writes its output to `host.out` there. It
then waits until the run progress file exists, in the lobby or, once the run entered its
workspace, in its node there, and prints `{run_id, kind, name, host_pid, trace, progress, result,
lobby}` with exit status 0: `trace` is the run's node folder in the workspace folder, or its
unbound node, `progress` and `result` its `status.json` and `result.json`, where they lie once the
run entered its workspace, and `lobby` the run's lobby folder, null for an unbound run, where a run
refused before it entered its workspace keeps its progress file and result.

An existing run progress file always wins: once it exists the run is announced, even when the
runner has already ended by then, since the run exists and its result, or its lost state when it
has none, tells how it ended. Only when no run progress file appeared, by the time the runner ended
or the announcement wait, 60 seconds from its start, ran out, does the command kill the runner with
its process group and look once more: a progress file written meanwhile still announces the run.
Otherwise the command reports `detach_failed`. The runner writes its first run progress file
before any step, or runs none ([When records cannot be written](#when-records-cannot-be-written)),
so no step ran; the command removes the run's folder, in the lobby or unbound, and a run lock file
the runner left, so that nothing of the run remains, and prints the same fields with an `error`
link `detach_failed` naming how the runner ended and the end of its output, with exit status 1. An
unannounced runner thus never starts its run later, and running the command again starts a new
run with nothing to repeat. The new session frees the runner from the command, not from the PID
namespace the command runs in: a runner detached inside a namespace that ends, such as that of a
sandboxed Bash call, is killed with it
([A detached run lives only as long as the PID namespace it started in](module.md#detached-namespace)).

## Run progress file

Before it writes anything in the run's folder, apart from `host.out` of a detached run, the
runner takes the [run lock](../glossary.json#concept.run-lock): an exclusive `flock` on the file
`locks/runs/<run-id>.lock` of the `.concorde` that holds its locks, which it creates, held until
after the result, the finished progress file and the final `trace.json` are written, through a
descriptor the processes it starts do not inherit, so a worker or check that outlives the runner
never keeps its run alive. The runner removes the file, still holding it, as it exits; the file of a
runner killed with `SIGKILL` stays but is not held. An observer tells a running run from a dead one
by the file's existence and by trying the lock for an instant, shared and without waiting
(`runner_alive`); the kernel's lock table `/proc/locks` shows the same for the file's inode,
whichever PID namespace holds it. A run without `result.json` whose lock nobody holds is `lost`.

The runner writes `status.json` in the run's folder, in the lobby until the run enters its
workspace, atomically when the folder is created, while it waits for the workspace lock, once it
holds it, before each step and when the result is written:

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

A failed write never changes the run, except the first, without which the run runs no step
([When records cannot be written](#when-records-cannot-be-written)).

## Errors

When a run does not end `ok`, the result's `error` is the run's own link of the
[error chain](../kernel/tracing/contracts.md#contract.tracing.error): the level `operation` for an Operation and
`command` for an execution command, the actor `Operation <name> <run-id> (workspace <workspace>)`,
`Command <name> <run-id> (workspace <workspace>)` or, unbound, `… (unbound, <origin> at <commit>)`,
where `<origin>` is the worktree the run started in, never its checkout, without ` at <commit>`
when the run was refused before its checkout existed, a code, a
detail naming the workspace, the Modules, the run, the paths and the messages concerned, the reason
the run cannot handle the error, the options it offers with a recommendation, and as causes the
errors it received, unchanged. A step that stops the run builds that link itself; the runner builds
it as follows.

| Error | Code | Reason | Causes |
| --- | --- | --- | --- |
| Refusal before the steps began | `refused` | `decision` for `workspace_busy`; `scope` for `binding_required` and `specs_unloadable`; `environment` for `binding_unreadable`, `workspace_retired`, `run_store_unwritable` and `checkout_unavailable`; `input` otherwise | the `component` link of `Execution (workspace binding)` for a binding refusal and `workspace_retired`, `Execution (unbound checkout)` for `checkout_unavailable`, or `Execution (run store)` otherwise, with the refusal's code and message |
| A step raised | `host_error` | `capability` | the exception's `component` link |
| Cancelled | `cancelled` | `environment` | none |
| Invalid result or output | `invalid_result` | `capability` | the error the run had, if any |
| A step stopped without an error | `missing_error` | `capability` | none |

The two failures to write the run's records
([When records cannot be written](#when-records-cannot-be-written)) are no result's error: the runner writes their `component` link, of the actor
`Execution runner (<command line>)`, to standard error, `run_unrecorded` or `result_unsaved`, with
the reason `environment`.

Spec tooling reports with [its own error record](../spec-tooling/spec/errors.md), never with a link.
When a Spec tooling error causes a run's error, the step translates it into a `component` link of
the actor `Spec core`: the record's message and location become the detail, its reason becomes the
explanation of why Spec core could not handle it (reason `input`, or `environment` for a
`system_error`), its remediation becomes the option and recommendation, and each of its causes
becomes a nested link the same way.

Two Modules whose errors are subclasses of the Spec tooling error type make their links
themselves, and a step never translates their errors: Check execution gives its failures as its own
link, made by `service_error` of [the check service](checks/service.md#check-executions-error-as-a-link),
of the actor `Check execution` and with the reason its code maps to, and the
[Issues](../issues/interface.md) store gives each refusal its own link, of the actor
`Issues (concorde issues)`. The step keeps that link unchanged as a cause under the run's own
link, actor, code and reason included.
