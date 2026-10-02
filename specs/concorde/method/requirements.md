# Method requirements

These requirements hold for every [Operation](../glossary.json#concept.operation) and [execution command](../glossary.json#concept.execution-command) [Method](module.md) provides; each
child [Module](../glossary.json#concept.module) states the precise behaviour of its own.

## The standard worker sequence

### req.method.workspace-specs — Grants come from the workspace

Every worker-backed step of a Method Operation SHALL compute the grant of a bound run from the Specs of the workspace the run works on, never from the primary worktree's, and the grant of an [unbound run](../glossary.json#concept.unbound-run) from the Specs of its [unbound checkout](../glossary.json#concept.unbound-checkout).

### req.method.models-placed-first — Every worker is placed before the first launches

Every run of a Method Operation SHALL check every worker its Operation may launch against the [worker configuration](../glossary.json#concept.worker-configuration) and the [model map](../glossary.json#concept.model-map) before it launches its first worker, launching none when the configuration names an Operation or [worker id](../glossary.json#concept.worker-id) Method does not register or the map cannot place one of them.

### req.method.grant-as-data — The worker harness receives the grant as data

Every worker-backed step of a Method Operation SHALL hand the worker harness the grant it computed through Spec core, converted into the worker harness's grant input, unchanged in its paths, levels and [context identity](../glossary.json#concept.context-identity).

### req.method.glossary-by-entry — The glossary is audited by entry

When a worker's grant names a writable glossary, Method's round validation SHALL report as a violation every glossary entry a round added, changed or removed whose owner, before or after the round, is not one of the grant's Modules.

The worker harness audits the worktree's files against the grant's `rw` list, which makes the whole
glossary writable or not; which entries of it a worker may change is a question of the Specs, so it
is asked in Method's [round validation](workers.md), which reports such a violation as
`audit_violation` and ends the run without another round.

## Optional integrations

### req.method.issues-optional — Reviews work without the issues part

Every review Operation of Method SHALL derive its verdict and return every finding in its [run result](../glossary.json#concept.run-result) whether or not the issues part is installed, reporting its findings as Issues only where it is installed.

Where it is not, the result says that the findings were not recorded as Issues, as the
[optional integration](../glossary.json#concept.optional-integration) rule of the root requires.
