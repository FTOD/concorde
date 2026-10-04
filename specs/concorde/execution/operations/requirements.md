# Operations requirements

This document states the Module-wide obligations of [Operations](module.md). Whatever a run's
definition, the [Execution requirements](../requirements.md) state what every run promises. The
[scenarios](scenarios.md) rely in particular on:

- [req.execution.claims-apart](../requirements.md#req.execution.claims-apart).
- [req.execution.error-when-not-ok](../requirements.md#req.execution.error-when-not-ok).
- [req.execution.reasons](../requirements.md#req.execution.reasons).
- [req.execution.error-detail](../requirements.md#req.execution.error-detail).

[How an Operation runs its workers](../../method/workers.md) describes how Method's
[Operations](../../glossary.json#concept.operation) run their workers. The scenarios show the
obligations at work.

## Definitions

### req.operations.workers-through-workers — Workers are launched only through the worker harness

Every Operation's steps SHALL launch every worker through the worker harness.

Whatever part provides the Operation, these statements therefore hold for every worker:

- It runs under the boundary the harness applies.
- It is audited.
- It leaves its [run record](../../glossary.json#concept.run-record).

### req.operations.grant-frozen — A worker's grant is frozen before its launch

Before asking the worker harness to launch the worker, every worker-backed step SHALL freeze the
grant of its worker.

### req.operations.status-mapping — Worker failures are never ok

When any of these conditions holds, a run SHALL end with status `failed`:

- The grant could not be computed.
- A worker could not be launched or timed out.
- The [write audit](../../glossary.json#concept.write-audit) found a violation.
- After the last [resume round](../../glossary.json#concept.resume-round), the round validation
  still reported a failure it designates to fail the run, such as a
  [configured check](../../glossary.json#concept.configured-check) still failing.

When round validation still reports something else to repair after the last round, the providing
Operation states the run's final status by its own contract. For example, when structural errors
remain, Adoption's `code_to_spec` ends `blocked`
([req.adoption.errors-left-block](../../method/adoption/requirements.md#req.adoption.errors-left-block)).

### req.operations.model-work-only — Every Operation has model work

Every Operation in the catalog SHALL do both of these:

- declare at least one [worker id](../../glossary.json#concept.worker-id)
- ask the worker harness to launch at least one AI worker on a run whose worker step settles the
  worker's grant, backend and model

When a run is refused before that worker step, it launches no worker. For example, when a run's
[worker configuration](../../glossary.json#concept.worker-configuration) cannot be read, the run is
refused before that worker step. Method's
[standard worker sequence](../../method/workers.md#standard-worker-sequence) shows this.

A job that needs no model is an [execution command](../../glossary.json#concept.execution-command)
of its own [Module](../../glossary.json#concept.module) instead.

### req.operations.unique-names — An Operation name has one definition

When two installed parts register an Operation of the same name, the catalog SHALL refuse to load,
naming both.

### req.operations.no-chaining — Operations do not start Operations

An Operation SHALL NOT start another Operation or an execution command.

Calling a service such as Check execution or resuming a worker is not starting a run.
