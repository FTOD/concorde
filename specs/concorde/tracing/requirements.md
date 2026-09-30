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

### req.tracing.reported-usage — Usage is what the agent program reported

A trace node's `usage` SHALL hold the figures the agent program reported or recorded for the node's
work, and null for a figure it did not report, never a figure Concorde computed from prices or
estimates of its own.

A task session's node takes them from Claude Code's records of the session when its task ends
([Task sessions](../coordination/task-session/requirements.md#req.task-session.node-finished)), a
worker round's from its agent process's result.

### req.tracing.observed-metadata — Metadata is observed, not claimed

A trace node's `metadata` SHALL hold only facts the Concorde code that writes the node observed
itself, never a statement taken from a [worker result](../glossary.json#concept.worker-result).

### req.tracing.relative-paths — A trace refers to its files and nodes relatively

A trace node SHALL refer to its own files only by paths relative to its folder and to other nodes
only by their identities, never by an absolute path.

An error link or a worker's claim that a node keeps is kept exactly as it was reported, with the
paths it named then; the node's own references never depend on them.

A node names its files relative to its own folder and other nodes by their identity, so a task's
trace reads the same after its folder moved to the [history](../glossary.json#concept.history) or to
another machine.

### req.tracing.created-or-found — A reference tells what the node created from what it found

A [trace node](../glossary.json#concept.trace-node) SHALL reference a commit with the relation
`commit` only when the node itself created it, and one an earlier node created, which it found and
reports, with `found_commit`.

A reader that follows a node's `commit` references therefore finds only the work of that node, and
still reaches the existing work a node reported, as
[scenario.tracing.created-or-found](scenarios.md#scenario.tracing.created-or-found) shows.

### req.tracing.large-by-reference — Large content is referenced

A trace node SHALL keep a transcript, an event stream or a log as a file of its folder named among
its artifacts, never copied into its `trace.json`.

### req.tracing.no-credentials — Credentials are never retained

No trace, task folder or history folder SHALL contain a credential file or a copy of one.

A worker's credential copies live only in its [runtime directory](../glossary.json#concept.runtime-directory), which is removed when the worker
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

### req.tracing.holder-named — A holder line names the session and the task

The holder line of a lock SHALL name, besides the holder, its process and when it took the lock,
the Claude Code session its process works for when its environment names one, and the task when
its taker names it.

### req.tracing.lock-handed-on — A handed lock lives as long as its receiver

A process started with a locked descriptor named in its `CONCORDE_INHERITED_LOCKS` SHALL adopt that
lock without waiting and hold it until it ends.

It passes neither the lock nor the variable on to the processes it starts, so the lock is released
when that process ends.

### req.tracing.history-unchanged — The history is not changed

No Concorde command SHALL change a file inside a history folder; retention only removes a history
folder whole or removes its conversation records.

### req.tracing.conversations-shorter — Conversation records have their own retention

Retention SHALL remove the conversation records of a history folder whose task was closed longer ago
than the configuration's `conversation_days`, 30 by default, and leave every other file of that
folder in place until the folder itself expires.

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
