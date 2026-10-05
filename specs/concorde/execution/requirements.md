# Execution requirements

The Module-wide obligations of [Execution](module.md). The runner is in
[How a run is executed](runner.md). The binding and the
[run result](../glossary.json#concept.run-result) are in the [contracts](contracts.md).
The [scenarios](scenarios.md) show the obligations at work.

## The seam with the upper half

### req.execution.binding-read-only — The binding is only read

No part of Execution SHALL write, change or remove a
[workspace binding](../glossary.json#concept.workspace-binding).

### req.execution.no-task-knowledge — Execution knows no task

No part of Execution SHALL read or write any of this state, so that everything a run knows about its workspace comes from the workspace binding of the worktree it starts in:

- a [task record](../glossary.json#concept.task-record)
- a [decision log](../glossary.json#concept.decision-log)
- any other state of the task store

### req.execution.reads-no-spec — Execution reads no Spec

No part of Execution SHALL read a [Spec](../glossary.json#concept.spec).

So the runner treats the [Modules](../glossary.json#concept.module) a run names as names, and a
definition that reads the Specs admits them itself, as Method's do. Execution installs and runs
with the kernel part alone.

### req.execution.computes-no-grant — Execution computes no grant

No part of Execution SHALL compute a [grant](../glossary.json#concept.grant).

A definition whose steps launch workers computes their grants itself, as Method's
[standard worker sequence](../glossary.json#concept.standard-worker-sequence) does.

### req.execution.launches-no-worker — Execution launches no worker

No part of Execution SHALL launch a [worker](../glossary.json#concept.worker) itself.

A run's definition's steps do whatever the run needs of a worker, through the parts they depend
on. The runner only tells the run context which worker runs those steps started.

### req.execution.binding-trusted — Only a sound binding binds

When a run's worktree holds a binding with any of these faults, the runner SHALL refuse the run
before any step:

- The binding cannot be read.
- The binding breaks the binding contract.
- The binding names a root other than that worktree.

## Results

### req.execution.one-result — Every accepted command line ends with one result

Every `concorde run` or [execution command](../glossary.json#concept.execution-command) started in
a Git worktree, whose whole command line is accepted and names a known
[Operation](../glossary.json#concept.operation) or command, SHALL write exactly one run result,
also when the run is refused, fails or is cancelled by `SIGINT` or `SIGTERM`, except when any of
these conditions holds:

- It was started with `--detach` and reported `detach_failed`.
- Its first records could not be created (`run_unrecorded`).
- A final write of its records failed (`result_unsaved`).
- Its runner was killed by a signal it cannot handle, such as `SIGKILL`, before writing the result.

A malformed command line, including one with an unknown argument, starts no run and writes no
result (exit status 2). A command line started outside every Git worktree also starts no run and
writes no result (exit status 2). A detached runner that ends or is killed before it announced its
run (`detach_failed`) leaves no run, as [How a run is executed](runner.md) describes. A run whose
first records could not be created runs no step. A run whose result could not be saved, or whose
final `trace.json` broke the node contract, still prints its result and counts as lost. Both runs
end with exit status 1
([When records cannot be written](runner.md#when-records-cannot-be-written)).

A runner killed outside its control after its announcement leaves a run without a result. Nobody
holds that run's [run lock](../glossary.json#concept.run-lock). This is a lost run, which every
observer tells by that lock ([Run progress file](runner.md#run-progress-file)).

### req.execution.unrecorded-runs-nothing — A run that cannot be recorded runs no step

When any of these conditions holds, the runner SHALL run no step of the run:

- The runner could not create the run's folder.
- The runner could not create the run's run lock.
- The runner could not create the run's first
  [run progress file](../glossary.json#concept.run-progress-file).
- The run's first `trace.json` breaks the node contract.

The runner exits instead with status 1 and its `run_unrecorded` link on standard error, as
[When records cannot be written](runner.md#when-records-cannot-be-written) describes.

### req.execution.unsaved-printed — A result that cannot be saved is still printed

When publishing a run's result fails, or its final `trace.json` breaks the node contract, the
runner SHALL print the result it composed on standard output.

The run then counts as lost. The runner takes these actions, as
[When records cannot be written](runner.md#when-records-cannot-be-written) describes:

- writes its `result_unsaved` link to standard error
- releases the run's locks
- exits with status 1

### req.execution.result-atomic — A result is published whole

The runner SHALL publish a run's `result.json` so that a reader finds either no result or the
complete result, never part of one.

### req.execution.result-printed — A foreground run prints its result

Unless the run could not be recorded
([req.execution.unrecorded-runs-nothing](#req.execution.unrecorded-runs-nothing)), a command
started without `--detach` SHALL print on standard output exactly the run result it composed.

That is the result the command wrote. When the command could not save the result, it is the result
the command composed ([req.execution.unsaved-printed](#req.execution.unsaved-printed)).

### req.execution.claims-apart — Worker claims stay the worker's

The runner and every step SHALL NOT place any statement taken from a
[worker result](../glossary.json#concept.worker-result) in the result's `summary` or
`host_evidence`.

### req.execution.error-when-not-ok — Every problem carries its error chain

A run result SHALL carry an error exactly when its status is not `ok`.

### req.execution.error-chain — The run's own link is on top of what it received

The top link of a run result's error SHALL be the run's own link, with the errors of the worker
runs, checks or components the run called as its causes.

### req.execution.reasons — The run says why it cannot handle the error

The run's own link SHALL give the reason the run cannot handle the error as its definition's
[Spec](../glossary.json#concept.spec) or [How a run is executed](runner.md#errors) assigns it.

### req.execution.error-detail — The run's link names what is concerned

The run's own link SHALL name all of these:

- in its actor, the run and its workspace or, for an unbound run, the worktree it started in and
  the commit it examined
- in a detail, the paths and the messages concerned
- in that detail, the Modules the run works on

### req.execution.output-checked — Outputs match their contract

The runner SHALL replace a result that fails the run result contract, or an `ok` result whose
`output` fails the definition's output contract, by a `failed` result that satisfies the run
result contract before writing it.

Of what the steps left, the replacement keeps only what satisfies the contract, as
[Composing the result](runner.md#composing-the-result) says. A result fails the contract when its
error is not the run's own link of the level `operation` or `command` its definition's kind gives.

## Runs

### req.execution.workspace-lock — One run per workspace

The runner SHALL hold the [workspace lock](../glossary.json#concept.workspace-lock) of a bound run
from before its admission until after its result is written.

### req.execution.workspace-busy — A busy workspace refuses a run

When another process holds a workspace's lock, the runner SHALL refuse its run with
`workspace_busy` at once or, with `--wait <seconds>`, once the lock is still held after that many
seconds.

### req.execution.workspace-wait — A waiting run waits in its own process

With `--wait <seconds>`, the runner SHALL wait for a busy workspace's lock inside its own process.

### req.execution.waiting-progress — A waiting run names the lock's holder

While a run waits for its workspace's lock, its
[run progress file](../glossary.json#concept.run-progress-file) SHALL name both of these:

- the step `workspace-lock`
- in `waiting_for`, the lock's holder as its holder line describes it, whether that holder is a run
  or another taker of the lock, such as a task's merge or close

### req.execution.workspace-wait-continues — A waiting run goes on once the lock is free

With `--wait <seconds>`, the runner SHALL take a busy workspace's lock as soon as it is free within
that time and go on with the run from its admission, as for a run that found the workspace free.

### req.execution.unbound-read-only — Only a definition that allows it runs unbound

An [unbound run](../glossary.json#concept.unbound-run) SHALL be admitted only for a definition that
allows unbound runs.

### req.execution.no-writing-worker — An unbound run launches no writing worker

No step of an unbound run SHALL launch a worker whose grant would keep a writable path.

Through its run context, the runner tells every step of an unbound run that the run may only read.
A definition whose steps launch workers, as Method's do, gives them reading grants only.

### req.execution.unbound-checkout — An unbound run works in a checkout of HEAD

The runner SHALL run every step of an admitted unbound run, and so every worker its steps launch,
in an [unbound checkout](../glossary.json#concept.unbound-checkout) of the commit at `HEAD` of the
worktree the run started in.

### req.execution.unbound-origin-untouched — An unbound run leaves its worktree as it was

Except for the [Issues](../glossary.json#concept.issue) it publishes through the Issues store,
an unbound run SHALL NOT change its starting worktree's index or any file of that worktree outside
these locations:

- that worktree's `.concorde/unbound/`
- that worktree's `.concorde/locks/`
- while the run lasts, its unbound checkout in the primary worktree's `.claude/worktrees/`

The requirement protects the worktree's content and index. Two changes lie outside it. As the
runner creates and removes the checkout as a linked worktree, Git's administrative files change,
as [Unbound checkout](runner.md#unbound-checkout) says. They belong to the repository, not to the
worktree's content. A review may publish Issues, only through the [Issues](../issues/module.md)
store. While the store holds the [merge lock](../glossary.json#concept.merge-lock), it commits each
Issue on the primary branch as a commit of its own. Nothing else of the run writes there. The
checkout the run examines stays as it was. Its Specs and its code stay as they were.

### req.execution.checkout-removed — The checkout does not outlive the run

Whatever ended an unbound run's steps, the runner SHALL remove the run's checkout before it writes the run's result, and name in that result whatever of the checkout it could not remove.

When Git refuses to remove something, the runner removes it directly. The runner names what that
leaves with `checkout-not-removed` evidence, as [Unbound checkout](runner.md#unbound-checkout)
step 5 says.

### req.execution.commit-named — The result names the commit examined

When an unbound run's checkout was created, its result SHALL name as `commit` the commit that
checkout held.

### req.execution.trace-node — Every run is a trace node where the binding says

The runner SHALL record every run as a [trace node](../glossary.json#concept.trace-node) in the
location that applies:

- once the run entered its workspace, in the binding's workspace folder
- when the run never entered its workspace, in the lobby of the binding's `.concorde`
- for an unbound run or a run whose binding the runner refused, in `.concorde/unbound/` of the
  worktree the run started in

The node lies in `runs/<run-id>/` of the workspace folder, or in the folder `--trace-at` names inside
it. A bound run's node lies in the [lobby](runner.md#the-lobby) until the run enters its workspace,
and stays there when the run never does.

### req.execution.trace-started — A run's node says it runs before its first step

The runner SHALL write a run's `trace.json`, with the status `running`, before the run's first step.

### req.execution.trace-ended — A run's node holds its end after its result

After writing a run's result, the runner SHALL write its `trace.json` again with the fields
[Run identity and trace node](runner.md#run-identity-and-trace-node) lists:

- the run's end
- the run's status
- the run's outcome

### req.execution.trace-write-reported — A refused trace write is in the result

For every write of a run's `trace.json` that the operating system refused, the runner SHALL report
`trace-write` evidence in the run's result without changing any of the following for it:

- the run's status
- the run's steps
- the run's exit status

Tracing is best-effort for the run, never silent
([req.tracing.written-at-start](../kernel/tracing/requirements.md#req.tracing.written-at-start)).
The result names each refused write with these details:

- the node's file
- the moment (start, update or end)
- the error

A refused final write follows the result. Afterwards, the runner adds the refused write to the
published result, so that the result as published and printed names it.

### req.execution.files-in-node — Every file of a run lies in its node

The runner SHALL keep every file of a run in the run's node folder, including:

- its result
- its run progress file
- the nodes of its checks
- the nodes of its worker runs
- for a [detached run](../glossary.json#concept.detached-run), its runner's output

### req.execution.lobby — Nothing enters a workspace folder before its lock

Before a bound run holds the [workspace lock](../glossary.json#concept.workspace-lock) and its
reread binding matches the binding read at the parse, the runner SHALL NOT create or write any
file or folder in its workspace folder.

Until then, the run's node lies in `lobby/<run-id>/` of the binding's `.concorde`. When the run is
refused or cancelled before then, its node lies there for good. So whoever retires a workspace
while holding its lock, as closing a task does, never moves a folder some run is writing.

### req.execution.workspace-retired — A run never works in a retired workspace

Once it holds the workspace lock, the runner SHALL refuse a run with `workspace_retired` when any
of these conditions holds:

- The run's lock file was removed or replaced while it waited.
- The run's worktree's binding is now absent.
- The run's worktree's binding is now untrusted.
- The run's worktree's binding is now different from the binding the runner read at the parse.

### req.execution.locks-apart — A run's locks lie under the locks directory

The runner SHALL take a run's [run lock](../glossary.json#concept.run-lock) and
[workspace lock](../glossary.json#concept.workspace-lock) as files under `locks/` of the binding's
`.concorde` or, for an unbound run, its starting worktree's `.concorde`, never inside a trace.

### req.execution.inputs-same-workspace — Inputs come from the same workspace

The runner SHALL admit a run as `--input` only when all these conditions hold:

- The input run is `ok`.
- The input run's workspace is the run's own workspace, which for an unbound run means the input
  run's `workspace` is null.
- The input run's saved result satisfies the current run result contract.

A result an older Concorde wrote under another version of the contract is refused like any other
inadmissible input. No version field or migration exists, since runs are short-lived trace data.

### req.execution.detached-same-run — A detached run is an ordinary run

A run started with `--detach` SHALL check, record and report exactly as the same run started
without it.

### req.execution.detached-announced — A detached run is announced once it exists

Only once the run's [run progress file](../glossary.json#concept.run-progress-file) exists in the
lobby or its node SHALL a command started with `--detach` announce the run with exit status 0 by
printing:

- its run identity
- its node and result path in its workspace folder
- its lobby folder

An existing run progress file wins. Once that file exists, the command announces the run, even
when the runner ended by then. When none exists by the time the runner ends or the announcement
wait runs out, the command reports `detach_failed` instead.
[How a run is executed](runner.md#detached-runs) describes this.

### req.execution.detach-failed-ends-runner — An unannounced runner is ended

A command started with `--detach` SHALL end the runner before it reports `detach_failed`.

So an unannounced runner never starts its run later, and so running the command again starts a new
run with nothing to repeat.

### req.execution.detach-failed-leaves-nothing — An unannounced run leaves nothing behind

A command started with `--detach` that reports `detach_failed` SHALL leave no folder and no run lock
file of the run behind.

### req.execution.fixed-order — Steps run in their declared order

The runner SHALL execute each of a definition's steps at most once, in their declared order, up to
and including the first step that stops the run.

### req.execution.run-lock-held — A run's lock is held exactly while its runner lives

The runner SHALL hold a run's [run lock](../glossary.json#concept.run-lock) from before it writes
the run's first [run progress file](../glossary.json#concept.run-progress-file) until after it
writes all of the following:

- the run's result
- its finished run progress file
- its final `trace.json`

However the runner ends, the operating system releases the lock. So a run is running exactly
while its run lock is held. So a run without a result whose lock nobody holds is lost
([Run progress file](runner.md#run-progress-file)). Whoever prepared a workspace reads its runs
through this lock and the records the [run store](../glossary.json#concept.run-store) keeps. The
run store keeps those records in the workspace folder and the [lobby](runner.md#the-lobby). To
stop a run that still runs, whoever prepared the workspace sends its runner `SIGTERM`. Execution
registers no call for either reading or stopping runs. Where the execution part is installed,
Coordination does both to derive whether a task is active and to stop a task's runs before it
closes the task.

### req.execution.no-chaining — Runs do not start runs

No step SHALL start another run.

A [workflow](../workflows/module.md) sequences runs from outside them, through the same command
lines. Calling a service such as Check execution or resuming a worker is not starting a run.
