# Operations requirements

The Module-wide obligations of [Operations](module.md). What every run promises, whatever its
definition, is in the [Execution requirements](../requirements.md); the [scenarios](scenarios.md)
rely in particular on
[req.execution.claims-apart](../requirements.md#req.execution.claims-apart),
[req.execution.error-when-not-ok](../requirements.md#req.execution.error-when-not-ok),
[req.execution.reasons](../requirements.md#req.execution.reasons) and
[req.execution.error-detail](../requirements.md#req.execution.error-detail). How an
[Operation](../../glossary.json#concept.operation) runs its workers is in
[How an Operation runs its workers](workers.md), and the scenarios show the obligations at work.

## Workers

### req.operations.workspace-specs — Grants come from the workspace

Every worker-backed step SHALL compute the grant of a bound run from the Specs of the workspace the
run works on, never from the primary worktree's, and the grant of an
[unbound run](../../glossary.json#concept.unbound-run) from the Specs of its
[unbound checkout](../../glossary.json#concept.unbound-checkout).

### req.operations.workers-through-workers — Workers are launched only through Workers

Every Operation SHALL launch every worker through Workers.

### req.operations.grant-frozen — A worker's grant is frozen before its launch

Every worker-backed step SHALL freeze the grant of its worker before it asks Workers to launch the
worker.

### req.operations.status-mapping — Worker failures are never ok

A run in which the grant could not be computed, a worker could not be launched or timed out, the
[write audit](../../glossary.json#concept.write-audit) found a violation or a
[configured check](../../glossary.json#concept.configured-check) still failed after the last
[resume round](../../glossary.json#concept.resume-round) SHALL end with status `failed`.

### req.operations.models-placed-first — Every worker is placed before the first launches

Every Operation's run SHALL check every worker its Operation may launch against the
[model map](../../glossary.json#concept.model-map) before it launches its first worker, launching
none when the map cannot place one of them.

### req.operations.model-work-only — Every Operation has model work

Every Operation in the catalog SHALL ask Workers to launch at least one AI worker on a run whose
worker step settles the worker's grant, backend and model.

A run refused before that, such as one whose [worker
configuration](../../glossary.json#concept.worker-configuration) cannot be read, launches no
worker, as [the standard worker sequence](workers.md#standard-worker-sequence) shows.

A job that needs no model is an [execution command](../../glossary.json#concept.execution-command)
of its own [Module](../../glossary.json#concept.module) instead.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation or an execution command.

Calling a service such as Check execution or resuming a worker is not starting a run.
