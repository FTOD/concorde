# Operations requirements

The Module-wide obligations of [Operations](module.md). What every run promises, whatever its
definition, is in the [Execution requirements](../requirements.md); how an
[Operation](../../glossary.json#concept.operation) runs its workers is in
[How an Operation runs its workers](workers.md), and the [scenarios](scenarios.md) show the
obligations at work.

## Workers

### req.operations.workspace-specs — Grants come from the workspace

Every worker-backed step SHALL compute the grant of a bound run from the Specs of the workspace the
run works on, never from the primary worktree's, and the grant of an
[unbound run](../../glossary.json#concept.unbound-run) from the Specs of the worktree it runs in.

### req.operations.workers-through-harness — Workers are launched only through Workers

Every Operation SHALL launch every worker through Workers with a grant frozen before the launch.

### req.operations.status-mapping — Worker failures are never ok

A run in which the grant could not be computed, a worker could not be launched or timed out, the
[write audit](../../glossary.json#concept.write-audit) found a violation or a
[configured check](../../glossary.json#concept.configured-check) still failed after the last
[resume round](../../glossary.json#concept.resume-round) SHALL end with status `failed`.

### req.operations.model-work-only — Every Operation launches a worker

Every Operation in the catalog SHALL launch at least one AI worker on a run that reaches its worker
step.

A job that needs no model is an [execution command](../../glossary.json#concept.execution-command)
of its own [Module](../../glossary.json#concept.module) instead.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation or an execution command.

Calling a service such as Check execution or resuming a worker is not starting a run.
