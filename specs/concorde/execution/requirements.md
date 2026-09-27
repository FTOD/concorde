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

Every `concorde run` or [execution command](../glossary.json#concept.execution-command) whose
command line names a known [Operation](../glossary.json#concept.operation) or command SHALL write
and print exactly one run result, including when the run is refused, fails or is cancelled.

### req.execution.claims-apart — Worker claims stay the worker's

The runner and every step SHALL NOT place any statement taken from a
[worker result](../glossary.json#concept.worker-result) in the result's `summary` or
`host_evidence`.

### req.execution.error-when-not-ok — Every problem carries its error chain

A run result SHALL carry an error exactly when its status is not `ok`, whose top link is the run's
own, with the errors of the worker runs, checks or components the run called as its causes.

### req.execution.reasons — The run says why it cannot handle the error

The run's own link SHALL give the reason the run cannot handle the error as its definition's
[Spec](../glossary.json#concept.spec) or [How a run is executed](runner.md#errors) assigns it, and a
detail that names the workspace, the Modules, the run, the paths and the messages concerned.

### req.execution.output-checked — Outputs match their contract

The runner SHALL replace a result that fails the run result contract, or whose `output` fails the
definition's output contract, by a `failed` result before writing it.

## Runs

### req.execution.workspace-lock — One run per workspace

The runner SHALL hold the [workspace lock](../glossary.json#concept.workspace-lock) of a bound run
from before its first step until after its result is written, refusing with `workspace_busy` a run
of a workspace whose lock another process holds.

### req.execution.unbound-read-only — An unbound run changes no Spec or code

An [unbound run](../glossary.json#concept.unbound-run) SHALL be admitted only for a definition that
allows unbound runs and never launch a worker whose grant would keep a writable path.

### req.execution.records-directory — Runs are recorded where the binding says

The runner SHALL write every [run directory](../glossary.json#concept.run-directory) and result
under `runs/` of the binding's records directory, or of the worktree's own `.concorde` for an
unbound run.

### req.execution.inputs-same-workspace — Inputs come from the same workspace

The runner SHALL admit as `--input` only an `ok` run whose workspace is the run's own workspace, or
none for an unbound run.

### req.execution.detached-same-run — A detached run is an ordinary run

A run started with `--detach` SHALL check, record and report exactly as the same run started without it.

### req.execution.detached-announced — A detached run is announced once it exists

A command started with `--detach` SHALL print the run identity and result path only once the run's [progress file](../glossary.json#concept.progress-file) exists.

### req.execution.fixed-order — Steps run in their declared order

The runner SHALL execute a definition's steps in their declared order, each at most once, and stop
at the first step that stops the run.

### req.execution.no-chaining — Runs do not start runs

No step SHALL start another run.

A [workflow](workflows/module.md) sequences runs from outside them, through the same command lines;
calling a service such as Check execution or resuming a worker is not starting a run.
