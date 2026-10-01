# Execution requirements

The Module-wide obligations of [Execution](module.md). The runner is in
[How a run is executed](runner.md), the binding and the
[run result](../glossary.json#concept.run-result) in the [contracts](contracts.md); the
[scenarios](scenarios.md) show the obligations at work.

## The seam with the upper half

### req.execution.binding-read-only — The binding is only read

No part of Execution SHALL write, change or remove a
[workspace binding](../glossary.json#concept.workspace-binding).

### req.execution.no-task-knowledge — Execution knows no task

No part of Execution SHALL read or write a [task record](../glossary.json#concept.task-record), a
[decision log](../glossary.json#concept.decision-log) or any other state of the task store, so that
everything a run knows about its workspace comes from the workspace binding of the worktree it
starts in.

### req.execution.binding-trusted — Only a sound binding binds

The runner SHALL refuse a run, before any step, whose worktree holds a binding that cannot be read,
breaks the binding contract or names a root other than that worktree.

## Results

### req.execution.one-result — Every accepted command line ends with one result

Every `concorde run` or [execution command](../glossary.json#concept.execution-command) started in
a Git worktree whose whole command line is accepted and names a known
[Operation](../glossary.json#concept.operation) or command SHALL write exactly one run result,
including when the run is refused, fails or is cancelled by `SIGINT` or `SIGTERM`, unless it was
started with `--detach` and reported `detach_failed`, or its runner was killed by a signal it cannot
handle, such as `SIGKILL`, before writing the result.

A malformed command line, including one with an unknown argument, or one started outside every Git
worktree starts no run and writes no result (exit status 2), and a detached runner that ends or is
killed before it announced its run (`detach_failed`) leaves no run, as
[How a run is executed](runner.md) describes. A runner killed outside its control after that leaves
a run without a result whose [run lock](../glossary.json#concept.run-lock) nobody holds: a lost run,
which every observer tells by that lock ([Run progress file](runner.md#run-progress-file)).

### req.execution.result-printed — A foreground run prints its result

A command started without `--detach` SHALL print on standard output exactly the run result it
wrote.

### req.execution.claims-apart — Worker claims stay the worker's

The runner and every step SHALL NOT place any statement taken from a
[worker result](../glossary.json#concept.worker-result) in the result's `summary` or
`host_evidence`.

### req.execution.error-when-not-ok — Every problem carries its error chain

A run result SHALL carry an error exactly when its status is not `ok`, whose top link is the run's
own, with the errors of the worker runs, checks or components the run called as its causes.

### req.execution.reasons — The run says why it cannot handle the error

The run's own link SHALL give the reason the run cannot handle the error as its definition's
[Spec](../glossary.json#concept.spec) or [How a run is executed](runner.md#errors) assigns it.

### req.execution.error-detail — The run's link names what is concerned

The run's own link SHALL give a detail that names the workspace, the Modules, the run, the paths
and the messages concerned.

### req.execution.output-checked — Outputs match their contract

The runner SHALL replace a result that fails the run result contract, or an `ok` result whose
`output` fails the definition's output contract, by a `failed` result before writing it.

## Runs

### req.execution.workspace-lock — One run per workspace

The runner SHALL hold the [workspace lock](../glossary.json#concept.workspace-lock) of a bound run
from before its first step until after its result is written.

### req.execution.workspace-busy — A busy workspace refuses a run

The runner SHALL refuse with `workspace_busy` a run of a workspace whose lock another process
holds, at once or, with `--wait <seconds>`, once the lock is still held after that many seconds.

### req.execution.workspace-wait — A waiting run waits in its own process

With `--wait <seconds>`, the runner SHALL wait for a busy workspace's lock inside its own process.

While it waits, its [run progress file](../glossary.json#concept.run-progress-file) names the step
`workspace-lock` and, in `waiting_for`, the run holding the lock.

### req.execution.workspace-wait-continues — A waiting run goes on once the lock is free

With `--wait <seconds>`, the runner SHALL take a busy workspace's lock as soon as it is free within
that time and go on with the run from its admission, as for a run that found the workspace free.

### req.execution.unbound-read-only — Only a definition that allows it runs unbound

An [unbound run](../glossary.json#concept.unbound-run) SHALL be admitted only for a definition that
allows unbound runs.

### req.execution.no-writing-worker — An unbound run launches no writing worker

An unbound run SHALL NOT launch a worker whose grant would keep a writable path.

### req.execution.unbound-checkout — An unbound run works in a checkout of HEAD

The runner SHALL run every step of an admitted unbound run, and every worker it launches, in an
[unbound checkout](../glossary.json#concept.unbound-checkout) of the commit at `HEAD` of the
worktree the run started in.

### req.execution.unbound-origin-untouched — An unbound run leaves its worktree as it was

An unbound run SHALL NOT change any file of the worktree it started in outside that worktree's
`.concorde/unbound/` and `.concorde/locks/` and, while the run lasts, its unbound checkout in the
primary worktree's `.claude/worktrees/`, nor that worktree's index.

### req.execution.checkout-removed — The checkout does not outlive the run

The runner SHALL remove an unbound run's checkout, whatever ended its steps, before it writes the
run's result.

### req.execution.commit-named — The result names the commit examined

The result of an unbound run whose checkout was created SHALL name as `commit` the commit that
checkout held.

### req.execution.trace-node — Every run is a trace node where the binding says

The runner SHALL record every run as a [trace node](../glossary.json#concept.trace-node) in the
binding's workspace folder, or in `.concorde/unbound/` of the worktree it started in for an unbound
run or a run whose binding it refused, writing its `trace.json` before its first step and again
after its result.

The node lies in `runs/<run-id>/` of the workspace folder, or in the folder `--trace-at` names inside
it, and every file of the run, its result, run progress file, checks and worker runs, lies in it. A
bound run's node lies in the [lobby](runner.md#the-lobby) until the run enters its workspace, and
stays there when the run never does.

### req.execution.lobby — Nothing enters a workspace folder before its lock

The runner SHALL NOT create or write any file or folder in a bound run's workspace folder before
the run holds the [workspace lock](../glossary.json#concept.workspace-lock) and the binding read
again matches the binding read at the parse.

Until then, and for good when the run is refused or cancelled before, the run's node lies in
`lobby/<run-id>/` of the binding's `.concorde`, so whoever retires a workspace while holding its
lock, as closing a task does, never moves a folder some run is writing.

### req.execution.workspace-retired — A run never works in a retired workspace

Once it holds the workspace lock, the runner SHALL refuse with `workspace_retired` a run whose lock
file was removed or replaced while it waited, or whose worktree's binding is now absent,
untrusted or different from the binding it read at the parse.

### req.execution.locks-apart — A run's locks lie under the locks directory

The runner SHALL take a run's [run lock](../glossary.json#concept.run-lock) and
[workspace lock](../glossary.json#concept.workspace-lock) as files under `locks/` of the binding's
`.concorde`, or of the `.concorde` of the worktree an unbound run started in, never inside a trace.

### req.execution.inputs-same-workspace — Inputs come from the same workspace

The runner SHALL admit as `--input` only an `ok` run whose workspace is the run's own workspace,
which for an unbound run is a run whose `workspace` is null.

### req.execution.detached-same-run — A detached run is an ordinary run

A run started with `--detach` SHALL check, record and report exactly as the same run started without it.

### req.execution.detached-announced — A detached run is announced once it exists

A command started with `--detach` SHALL announce the run, printing its run identity, its node and
result path in its workspace folder and its lobby folder with exit status 0, only once the run's
[run progress file](../glossary.json#concept.run-progress-file) exists, in the lobby or in its node.

When the runner ends or stays silent until the announcement wait runs out, the command reports
`detach_failed` instead, as [How a run is executed](runner.md#detached-runs) describes.

### req.execution.fixed-order — Steps run in their declared order

The runner SHALL execute each of a definition's steps at most once, in their declared order, up to
and including the first step that stops the run.

### req.execution.no-chaining — Runs do not start runs

No step SHALL start another run.

A [workflow](workflows/module.md) sequences runs from outside them, through the same command lines;
calling a service such as Check execution or resuming a worker is not starting a run.
