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

### req.operations.escalation-when-not-ok — Every problem carries an escalation

An Operation result SHALL carry an escalation exactly when its status is not `ok`.

### req.operations.status-mapping — Host failures are never ok

A run in which the grant could not be computed, a worker could not be launched or timed out, the
write audit found a violation or a configured check still failed after the last resume round SHALL
end with status `failed`.

### req.operations.output-checked — Outputs match their contract

The host SHALL replace a result that fails the result contract, or whose `output` fails the
provider's output contract, by a `failed` result before writing it.

## Runs

### req.operations.task-worktree-specs — Grants come from the task worktree

The host SHALL compute every grant from the Specs of the task's worktree, never from the primary
worktree's.

### req.operations.recorded — Runs are recorded in their task

The host SHALL record every accepted run in the task record as begun before the first provider step
and as finished with the result's status before exiting.

### req.operations.run-records-primary — Results live in the primary worktree

The host SHALL write every result and run directory under `.concorde/runs/` of the primary worktree.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation.

### req.operations.fixed-order — Steps run in their declared order

The runner SHALL execute a provider's steps in their declared order, each at most once, and stop at
the first step that stops the run.

### req.operations.workers-through-harness — Workers are launched only through Workers

The host SHALL launch every worker through Workers with a grant frozen before the launch.
