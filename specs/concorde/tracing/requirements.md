# Tracing requirements

The Module-wide obligations of [Tracing](module.md) and of every [Module](../glossary.json#concept.module) that records a
[trace node](../glossary.json#concept.trace-node). The record, layout, locks and command are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## The record

### req.tracing.node-contract — Every node follows the node contract

Every `trace.json` SHALL satisfy the [trace node contract](contracts.md#contract.tracing.node), with
content of the type the node kinds table names for its kind.

### req.tracing.written-at-start — A node exists from its start

The producer of a trace node SHALL write its `trace.json` before the work the node records begins,
and write it again when that work ends.

A node whose process dies therefore still says what it was and when it started, and the reading
command shows it `lost` when its run lock tells that nobody writes it any more.

### req.tracing.own-usage — A node records only its own consumption

A trace node's `usage` SHALL record only what the node itself consumed, never what the nodes below it
consumed.

The reading command rolls usage up over a subtree, which counts each token once only because no
node repeats its children's.

### req.tracing.observed-metadata — Metadata is observed, not claimed

A trace node's `metadata` SHALL hold only facts the Concorde code that writes the node observed
itself, never a statement taken from a [worker result](../glossary.json#concept.worker-result).

### req.tracing.relative-paths — A trace holds no absolute path

No `trace.json` SHALL contain an absolute path.

A node names its files relative to its own folder and other nodes by their identity, so a task's
trace reads the same after its folder moved to the [history](../glossary.json#concept.history) or to
another machine.

### req.tracing.large-by-reference — Large content is referenced

A trace node SHALL keep a transcript, an event stream or a log as a file of its folder named among
its artifacts, never copied into its `trace.json`.

### req.tracing.no-credentials — Credentials are never retained

No trace, task folder or history folder SHALL contain a credential file or a copy of one.

A worker's credential copies live only in its runtime directory, which is removed when the worker
ends.

## The tree

### req.tracing.nested-by-parent — A child lies inside its parent

The folder of every trace node except a task and an [unbound run](../glossary.json#concept.unbound-run) SHALL lie inside the folder of the
node it belongs to, at the location that node chose before the child started.

### req.tracing.downward-only — Execution's nodes never name a task

No trace node written by a Module of Execution SHALL record a task, a [task session](../glossary.json#concept.task-session), a [decision log](../glossary.json#concept.decision-log) or
any other node of Coordination.

A task's node reaches its workspace's nodes because its folder contains them; nothing below the
workspace names what is above it.

## Keeping and removing

### req.tracing.locks-apart — Locks lie apart from records

Every lock Concorde takes SHALL be a file under `.concorde/locks/` that holds nothing but its current
holder.

### req.tracing.run-lock-removed — A run lock ends with its runner

A runner SHALL remove its [run lock](../glossary.json#concept.run-lock) file as it exits, while it
still holds the lock.

### req.tracing.history-unchanged — The history is not changed

No Concorde command SHALL change a file inside a history folder; a history folder is only removed
whole, by retention.

### req.tracing.retention-explicit — Traces are removed only at defined points

Traces SHALL be removed only by `concorde trace prune` and by the retention step at the start of
`task open` and `task close`, and only nodes that have ended.

No background process removes traces, and a node whose run lock is held, or that has no end, is
never removed.

## Reading

### req.tracing.reader-read-only — Reading changes nothing

`concorde trace show` and `concorde trace list` SHALL NOT write, move or remove any file.

### req.tracing.error-in-band — An error chain stays whole where it is reported

Every result, record and escalation that carries an [error chain](../glossary.json#concept.error-chain)
SHALL carry it whole, never only a reference to a trace node.

A link may name a trace node as evidence of kind `trace`, as an entry point for a deeper analysis;
its receiver still decides from the chain alone.
