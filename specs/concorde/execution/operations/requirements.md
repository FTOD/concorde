# Operations requirements

The Module-wide obligations of [Operations](module.md). What every run promises, whatever its
definition, is in the [Execution requirements](../requirements.md); the [scenarios](scenarios.md)
rely in particular on
[req.execution.claims-apart](../requirements.md#req.execution.claims-apart),
[req.execution.error-when-not-ok](../requirements.md#req.execution.error-when-not-ok),
[req.execution.reasons](../requirements.md#req.execution.reasons) and
[req.execution.error-detail](../requirements.md#req.execution.error-detail). How Method's
[Operations](../../glossary.json#concept.operation) run their workers is in
[How an Operation runs its workers](../../method/workers.md), and the scenarios show the obligations at work.

## Definitions

### req.operations.workers-through-workers — Workers are launched only through the worker harness

Every Operation's steps SHALL launch every worker through the worker harness.

So every worker runs under the boundary the harness applies, is audited and leaves its [run record](../../glossary.json#concept.run-record),
whatever part provides the Operation.

### req.operations.grant-frozen — A worker's grant is frozen before its launch

Every worker-backed step SHALL freeze the grant of its worker before it asks the worker harness to
launch the worker.

### req.operations.status-mapping — Worker failures are never ok

A run in which the grant could not be computed, a worker could not be launched or timed out, the
[write audit](../../glossary.json#concept.write-audit) found a violation or the round validation
still reported something to repair, such as a
[configured check](../../glossary.json#concept.configured-check) still failing, after the last
[resume round](../../glossary.json#concept.resume-round) SHALL end with status `failed`.

### req.operations.model-work-only — Every Operation has model work

Every Operation in the catalog SHALL declare at least one [worker id](../../glossary.json#concept.worker-id) and ask the worker harness to
launch at least one AI worker on a run whose worker step settles the worker's grant, backend and
model.

A run refused before that, such as one whose [worker
configuration](../../glossary.json#concept.worker-configuration) cannot be read, launches no
worker, as Method's [standard worker sequence](../../method/workers.md#standard-worker-sequence)
shows.

A job that needs no model is an [execution command](../../glossary.json#concept.execution-command)
of its own [Module](../../glossary.json#concept.module) instead.

### req.operations.unique-names — An Operation name has one definition

The catalog SHALL refuse to load when two installed parts register an Operation of the same name,
naming both.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation or an execution command.

Calling a service such as Check execution or resuming a worker is not starting a run.
