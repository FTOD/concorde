# Operations requirements

The Module-wide obligations of [Operations](module.md). The runner and the standard worker sequence
are in [How the host runs an Operation](host.md), the envelope in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Results

### req.operations.one-result — Every accepted command line ends with one result

Every `concorde run` whose command line names a catalog Operation and a task SHALL write and print
exactly one Operation result, including when the run is refused, fails or is cancelled.

### req.operations.claims-apart — Worker claims stay the worker's

The host SHALL NOT place any statement taken from a worker result in the result's `summary` or
`host_evidence`.

### req.operations.error-when-not-ok — Every problem carries its error chain

An Operation result SHALL carry an error exactly when its status is not `ok`, whose top link is the Operation's own, with the errors of the worker run, the checks or the components the host called as its causes.

### req.operations.reasons — The Operation says why it cannot handle the error

The Operation's own link SHALL give the reason the Operation cannot handle the error as [How the host runs an Operation](host.md#errors) assigns it, and a detail that names the task, the Modules, the run, the paths and the messages concerned.

### req.operations.status-mapping — Host failures are never ok

A run in which the grant could not be computed, a worker could not be launched or timed out, the
write audit found a violation or a configured check still failed after the last resume round SHALL
end with status `failed`.

### req.operations.output-checked — Outputs match their contract

The host SHALL replace a result that fails the result contract, or whose `output` fails the
provider's output contract, by a `failed` result before writing it.

## Runs

### req.operations.task-worktree-specs — Grants come from the task worktree

The host SHALL compute every grant of a run of a task from the Specs of the task's worktree, never
from the primary worktree's, and every grant of a run without a task from the Specs of the primary
worktree.

### req.operations.recorded — Runs are recorded in their task

The host SHALL record every accepted run of a task in the task record as begun before the first
provider step and as finished with the result's status before exiting.

### req.operations.no-task-read-only — A run without a task changes no Spec or code

The host SHALL run an Operation without a task only when its catalog entry makes the task optional and the command runs in the primary worktree, and then refuse every `specify` or `implement` worker launch of the run before computing its grant.

### req.operations.run-records-primary — Results live in the primary worktree

The host SHALL write every result and run directory under `.concorde/runs/` of the primary worktree.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation.

A [workflow](../workflows/module.md) sequences Operations from outside them, through `concorde run`;
no provider knows it runs inside one.

### req.operations.detached-same-run — A detached run is an ordinary run

A run started with `--detach` SHALL check, record and report exactly as the same run started without it.

### req.operations.detached-announced — A detached run is announced once it exists

`concorde run --detach` SHALL print the run identity and result path only once the run's progress file exists.

### req.operations.fixed-order — Steps run in their declared order

The runner SHALL execute a provider's steps in their declared order, each at most once, and stop at
the first step that stops the run.

### req.operations.workers-through-harness — Workers are launched only through Workers

The host SHALL launch every worker through Workers with a grant frozen before the launch.
