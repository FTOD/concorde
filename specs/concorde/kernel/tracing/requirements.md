# Tracing requirements

These are the Module-wide obligations of [Tracing](module.md) and of every
[Module](../../glossary.json#concept.module) that records a
[trace node](../../glossary.json#concept.trace-node). The [contracts](contracts.md) describe:

- The record.
- The layout.
- The locks.
- The command.

The [scenarios](scenarios.md) show the obligations at work.

## The record

### req.tracing.node-contract — Every node follows the node contract

Every `trace.json` SHALL satisfy the [trace node contract](contracts.md#contract.tracing.node)
with content of the type the node kinds table names for its kind.

### req.tracing.written-at-start — A node exists from its start

The producer of a trace node SHALL write its `trace.json` before the work the node records begins,
and write it again when that work ends.

Because the producer writes the record before work begins, a node whose process dies still says what it was and when it started.
When the node's run lock tells that nobody writes it any more, the reading command shows the node
as `lost`. Tracing is best-effort for the work, never silent.
When the operating system refuses a write of `trace.json`, the refusal never changes the work the
node records. The producer reports every such failed write in its own result as evidence or a warning.
The evidence or warning names the node's file and the error.

### req.tracing.own-usage — A node records only its own consumption

A trace node's `usage` SHALL record only what the node itself consumed, never what the nodes below
it consumed.

The reading command rolls usage up over a subtree.
This counts each token once only because no node repeats its children's usage.

### req.tracing.reported-usage — Usage is what the agent program reported

A trace node's `usage` SHALL hold the figures the agent program reported or recorded for the node's
work, and null for a figure it did not report, never a figure Concorde computed from prices or
estimates of its own.

When its task ends, a task session's node takes the figures from Claude Code's records of the session
([Task sessions](../../coordination/task-session/requirements.md#req.task-session.node-finished)).
A worker round's node takes the figures from its agent process's result.

### req.tracing.observed-metadata — Metadata is observed, not claimed

A trace node's `metadata` SHALL hold only facts the Concorde code that writes the node observed
itself, never a statement taken from a [worker result](../../glossary.json#concept.worker-result).

### req.tracing.relative-paths — A trace refers to its files and nodes relatively

A trace node SHALL refer to its own files only by paths relative to its folder and to other nodes
only by their identities, never by an absolute path.

When a node keeps an error link or a worker's claim, it keeps it exactly as reported, with the paths it named then.
The node's own references never depend on the retained error link or worker's claim.

A node names its files relative to its own folder.
The node names other nodes by their identity.
Therefore, after its folder moves to the [history](../../glossary.json#concept.history) or another
machine, a task's trace reads the same.

### req.tracing.created-or-found — A reference tells what the node created from what it found

A [trace node](../../glossary.json#concept.trace-node) SHALL reference a commit with the relation
`commit` only when the node itself created it, and one an earlier node created, which it found and
reports, with `found_commit`.

Because these relations distinguish created work from found work, a reader that follows a node's `commit` references finds only the work of that node.
For the same reason, the reader still reaches the existing work a node reported, as
[scenario.tracing.created-or-found](scenarios.md#scenario.tracing.created-or-found) shows.

### req.tracing.large-by-reference — Large content is referenced

A trace node SHALL keep a transcript or a log as a file of its folder named among
its artifacts, never copied into its `trace.json`.

### req.tracing.no-credentials — Credentials are never retained

The following SHALL contain no credential file or copy of one:

- A trace.
- A task folder.
- A history folder.

A worker's credential copies live only in its
[runtime directory](../../glossary.json#concept.runtime-directory).
When the worker ends, the runtime directory is removed.

## The tree

### req.tracing.nested-by-parent — A child lies inside its parent

Except for the following nodes, every trace node's folder SHALL lie inside its parent's folder
at the location its parent chose before the child started:

- A task.
- An [unbound run](../../glossary.json#concept.unbound-run).
- A bound run in the lobby.

Until it holds its workspace's lock, a bound run lies in the lobby, `lobby/<run>/`.
When the bound run never holds the lock, it stays there.
Once it holds the lock, the bound run lies at the location its parent chose.

### req.tracing.downward-only — The nodes of a workspace never name a task

For a trace node written by a Module that works in a
[workspace](../../glossary.json#concept.workspace), the node SHALL record none of the following:

- A task.
- A [task session](../../glossary.json#concept.task-session).
- A [decision log](../../glossary.json#concept.decision-log).
- Any other node of Coordination.

Examples of such trace nodes are those of:

- Execution.
- Workflows.
- Method.
- The worker harness.

A task's node reaches its workspace's nodes because its folder contains them.
Nothing below the workspace names what is above it.

## Keeping and removing

### req.tracing.roots-registered — Only registered roots are searched and pruned

`concorde trace` SHALL do these only for the trace roots the installed parts registered, each by the rules its part registered for it:

- Search them.
- List them.
- Prune them.

For a root whose part is not installed:

- The root is not searched.
- The root is not listed.
- Its retention periods are ignored.

### req.tracing.locks-apart — Locks lie apart from records

Every lock Concorde takes SHALL be a file under `.concorde/locks/` that holds nothing but its current
holder.

### req.tracing.run-lock-removed — A run lock ends with its runner

As it exits, while it still holds the lock, a runner SHALL remove its
[run lock](../../glossary.json#concept.run-lock) file.

### req.tracing.holder-named — A holder line names the session and the task

The holder line of a lock SHALL name:

- The holder.
- The holder's process.
- When the holder took the lock.
- When its environment names one, the Claude Code session its process works for.
- When its taker names it, the task.

### req.tracing.lock-handed-on — A handed lock lives as long as its receiver

When a process starts with a locked descriptor named in its `CONCORDE_INHERITED_LOCKS`, the process
SHALL adopt that lock without waiting and hold it until the process ends.

The process passes neither the lock nor the variable on to the processes it starts.
Therefore, when the process that adopted the lock ends, the lock is released.

### req.tracing.history-unchanged — A closed root is not changed

No Concorde command SHALL change a file inside a folder of a trace root its part registered as closed, such as Coordination's [history](../../glossary.json#concept.history), except that retention only removes such a folder whole or removes its conversation records.

The one exception is the one the registering part names. For the history, this exception is the
merge that closed the task. The reason is that the close moves the task's folder while the merge
still writes its answer. Therefore, before it ends, the merge's process finishes the `output.json`
and `messages.log` of its attempt's node there
([Tasks](../../coordination/tasks/requirements.md#req.tasks.merge-output-kept)).

### req.tracing.conversations-shorter — Conversation records have their own retention

Retention SHALL remove the conversation records of a folder of a closed trace root whose top node ended longer ago than the period its part registered for them, for Coordination's history the configuration's `conversation_days`, 30 by default, and leave every other file of that folder in place until the folder itself expires.

### req.tracing.retention-explicit — Traces are removed only at defined points

Traces SHALL be removed only by `concorde trace prune` and by the retention step a part that registers a trace root runs, such as Coordination's at the start of `task open` and `task close`, and only nodes that have ended.

No background process removes traces. When a node's run lock is held or the node has no end, the
node is never removed.

## Reading

### req.tracing.reader-read-only — Reading changes nothing

`concorde trace show` and `concorde trace list` SHALL NOT perform any of these actions on any file:

- Write.
- Move.
- Remove.

### req.tracing.error-in-band — An error chain stays whole where it is reported

When they carry an [error chain](../../glossary.json#concept.error-chain), the following SHALL carry
it whole, never only a reference to a trace node:

- Every result.
- Every record.
- Every escalation.

A link may name a trace node as evidence of kind `trace`, as an entry point for a deeper analysis.
Its receiver still decides from the chain alone.
