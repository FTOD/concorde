# Tracing

## Purpose

Tracing decides which information about Concorde's work is combined and retained, and in what
structure, so that the work can be analysed later: what ran, where, on which model, for how long, at
what cost and with what outcome, from a whole task down to one round of one worker. It owns that
structure, the uniform record every level of work leaves, the metadata by which records are compared,
where records are kept while a task is current and after it ended, how long they are kept, the locks
that are kept apart from them, the command that reads them, and the
[error chain](../../glossary.json#concept.error-chain) through which a failure travels up the levels.

Tracing does not produce the information. Each [Module](../../glossary.json#concept.module) that does work, Tasks, [Task sessions](../../glossary.json#concept.task-session),
Workflows, Execution, Workers and Check execution, still decides and writes the content of its own
records; Tracing gives each of them the place and the shape. It keeps no state a command acts on:
a [task record](../../glossary.json#concept.task-record) or a lock is not a trace, and the
[decision log](../../glossary.json#concept.decision-log) Tasks commits to Git when a task ends is the
task's own record, which stays with the code whatever retention removes.
Spec tooling reports with its own error record and never uses the error chain.

## Core concepts

### Traces and trace nodes

<a id="concept.trace"></a><a id="concept.trace-node"></a>

Every level of work in Concorde leaves one
**[trace node](../../glossary.json#concept.trace-node)**: a folder holding a `trace.json` record in one
uniform shape, the files that level keeps next to it and the folders of the nodes below it. A task
is a node, and so is each of its task sessions, each merge attempt, the workflow of its workspace
and each of its steps, each run of an [Operation](../../glossary.json#concept.operation) or
[execution command](../../glossary.json#concept.execution-command), each
[configured check](../../glossary.json#concept.configured-check) a run or a merge ran, each worker run
and each of its rounds. The tree of nodes below one task, or below one
[unbound run](../../glossary.json#concept.unbound-run), is a **[trace](../../glossary.json#concept.trace)**.

### The history

<a id="concept.history"></a>

Everything about one task, its state and its traces alike, lives in one
folder, `.concorde/tasks/<task>/`, while the task is current. When the task is closed, merged or not,
its whole folder is moved to the **[history](../../glossary.json#concept.history)**,
`.concorde/history/<task>/`, where it stays as it was when the task ended: nothing in the history is
ever changed, apart from the merge that closed the task finishing the answer it writes into its
attempt's node, and retention only removes a history folder whole or, sooner, its conversation
records; it may be copied out. An unbound run, which belongs to no task, is
kept in `.concorde/unbound/<run>/` of the worktree it started in. A run of a task's workspace that
does not hold the workspace's lock yet lies in the lobby, `.concorde/lobby/<run>/`, outside the
task's folder, so that a close moving that folder while it holds the lock never races it; it moves
into the workspace folder once it holds the lock, and stays in the lobby when it is refused before.
The [layout](contracts.md#layout) gives every path.

### The error chain

<a id="concept.error-chain"></a>

An **[error chain](../../glossary.json#concept.error-chain)** preserves both the original
failure and why each receiving level could not handle it: each level that cannot handle an error it
received adds its own detailed link, with its reason, on top of the unchanged links below. Every
result that is not `ok` carries its error chain whole, as the
[error contract](contracts.md#contract.tracing.error) defines: its receiver decides from the chain
alone and never has to open a trace to learn what failed. The chain may name trace nodes as entry
points for a deeper analysis, never in place of what it says. How to read a chain, and where each
level writes its link, is in [Reading an error chain](contracts.md#reading-an-error-chain).

## Overview

### The shape of a trace

```d2 illustrative
task: "task\n.concorde/tasks/retry/" {
  sessions: "session"
  merges: "merge → check"
  workspace: "workspace/ (Execution below)" {
    workflow: "workflow → step → run"
    runs: "run" {
      check: check
      worker: "worker run → round → check"
    }
  }
}
```

A level above another holds it: a node's children lie in folders inside its own folder, placed there
by the parent, which gives the child its location before the child starts, so no node is ever
recorded without its parent. Nodes at the same level may refer to each other instead: a run names
the earlier runs it admitted as inputs, a delivery run the [delivery commit](../../glossary.json#concept.delivery-commit) it created. The runs a
[workflow step](../../glossary.json#concept.workflow-step) starts lie inside that step; the runs a task session or the [main agent](../../glossary.json#concept.main-agent) starts directly
lie in the workspace beside the workflow.

A trace crosses Concorde's two halves in one direction only. The task's node holds its workspace's
folder, so an analysis walks from a task down to everything that ran for it; nothing below the
workspace records the task, since Execution knows no task, and nothing walks back up. The
[workspace binding](../../glossary.json#concept.workspace-binding) is what gives Execution the folder
it writes into.

### Where records live over a task's life

A task's folder is current while the task is and moves whole to the history when the task is
closed; there only retention removes anything, first its conversation records and then, when the
project configures it, the whole folder. An unbound run is kept beside the tasks and removed sooner.
The decision log leaves with the task into Git, so it outlives every retention period, and the locks
lie apart from all these folders ([Locks are not records](#locks-are-not-records)).

```d2 illustrative
direction: right
open: "task open" {shape: oval}
current: "Current task\n.concorde/tasks/<task>/\nrecord, decision log, trace"
history: "History\n.concorde/history/<task>/\nnever changed"
slim: "History folder without\nits conversation records"
removed: "Removed" {shape: oval}
git: "Git, with the code\n.concorde/decisions/"
unbound: "Unbound run\n.concorde/unbound/<run>/"
lobby: "Run refused before it held\nits workspace's lock\n.concorde/lobby/<run>/"
open -> current
current -> history: "task close,\nmerged or not"
current -> git: "task close: Tasks commits\nthe decision log" {style.stroke-dash: 3}
history -> slim: "closed more than\n30 days ago (default)"
slim -> removed: "closed longer ago than\nthe project configures,\nif it does"
unbound -> removed: "ended more than\n7 days ago (default)"
lobby -> removed: "ended more than\n7 days ago (default)"
```

### Tracing and its producers

Every producer writes its nodes and takes its locks through the tracing library and reports its
failures with the error chain code; the trace command reads and prunes through the same library.

```d2 illustrative
tracing: Tracing {
  library: Tracing library
  command: Trace command
  errors: Error chain code
  command -> library: reads and prunes through
}
producers: "Tasks, Task sessions, Workflows,\nExecution, Workers, Check execution" {shape: page}
producers -> tracing.library: write their nodes and take their locks through
producers -> tracing.errors: report with
```

## Using traces

### What a node records

Every `trace.json` holds the same fields, defined by the
[trace node contract](contracts.md#contract.tracing.node):

- its identity and kind, when it started and ended, and its status: `running`, `ok`, `blocked`,
  `failed` or, for a node whose end its producer never observes, `unknown`, with the producer's own
  finer outcome, such as `merged` for a task or `timed_out` for a check;
- its own **usage**: tokens in, out and through the cache, cost, turns and duration, of the node
  itself, never of its children, so a sum over a subtree counts every token once;
- its error link when it did not end `ok`;
- **metadata**: the workspace, the Modules, the Operation or command, the [task type](../../glossary.json#concept.task-type), the [worker id](../../glossary.json#concept.worker-id),
  backend, model and reasoning level, the commit, the [context identity](../../glossary.json#concept.context-identity), the grant and brief digests,
  the Concorde commit and the Protocol version, whichever the level has, taken only from what
  Concorde observed itself and never from a worker's claim, so that nodes of one kind can be
  selected and compared by them;
- **artifacts**: the files it keeps in its folder, such as a transcript, a log or a run result, each
  by its path relative to the folder and its digest, so a transcript is referenced, never copied;
- **references** to nodes at the same level and to commits, which tell a commit the node created
  (`commit`) from one an earlier node created and this node only found (`found_commit`), such as a
  delivery that finds its work already delivered;
- and the producer's own **content**, a [typed value](../../glossary.json#concept.typed-value) whose
  type the producer registers, such as a run's steps with their timings or a worker round's audit.

The figures of a node's usage come from what the agent program itself reported or recorded, never
from a computation of Concorde's own: a worker round's from the result its agent process returned,
a task session's from Claude Code's records of the session, read when its task ends. Concorde keeps
no price table, so a cost the program did not report stays null. A task session's node is the one
whose end Concorde does not see happen: Task sessions finishes it when the task ends, from the
session's transcript and Claude Code's own account of the session, writing the figures into the
node, since retention later removes the transcript they came from.

A producer writes its node when the node starts and rewrites it when it ends, so a node that is
still running, or whose process died, is already there. A node never refers to a file or another node by an absolute
path: it names its files relative to its own folder and other nodes by their identity, since a
task's folder moves when the task ends.

### Reading a trace

`concorde trace` reads traces and never changes one:

```text
concorde trace show [<node>] [--depth <n>] [--format json|tree]
concorde trace list [--history] [--unbound]
concorde trace prune [--dry-run]
```

`show` takes a task name, a run identity, a worker run identity or a node's folder, and prints the
node with its subtree: each node's status, times and own usage, and the usage rolled up over its
subtree, so the cost of a whole task, of one of its workflows or of one run is read in one place. It
finds a node among the current tasks, the [history](../../glossary.json#concept.history), the
unbound runs and the lobby of the worktree it runs in and of the primary worktree. A node that says it is still
running although the process that writes it has ended is shown `lost`. `list` lists the current
tasks, and with its options the history and the unbound runs, with their status and rolled-up usage.
A result's error chain names the node that reported it, as evidence of kind `trace` whose reference
is the run or worker run identity, so a reader goes from an error to its trace with `show`.

For a task `retry` whose session ran `implement` and then `delivery`,
`concorde trace show retry --format tree` prints the task, its session, the two runs under its
workspace, the `implement` run's worker run with its rounds and checks, and the total cost of the
task, with the cost of each run beside it.

### Locks are not records

Every lock Concorde takes lies under `.concorde/locks/`, never inside a
trace or a task folder, and its file holds only who holds it now:

| Lock | Taken by | Kept |
| --- | --- | --- |
| [merge lock](../../glossary.json#concept.merge-lock) `merge.lock` | a task merge, open or close, and an [Issue](../../glossary.json#concept.issue) write | always |
| task lock `tasks/<task>.lock` | a change of the task's record | until the task is closed |
| [workspace lock](../../glossary.json#concept.workspace-lock) `workspaces/<workspace>.lock` | a run of the workspace, a merge or close of its task | until the task is closed |
| workflow lock `workflows/<workspace>.lock` | a workflow step or report of the workspace, a close of its task, also the close that ends its merge | until the task is closed |
| [run lock](../../glossary.json#concept.run-lock) `runs/<run>.lock` | the run's runner only | removed by the runner as it exits |

A lock file's holder line names the holder, its process and since when it holds the lock, and,
when they are known, the Claude Code session it works for and the task, so that whoever is refused
learns who to wait for. A lock can be handed on: its holder passes the locked descriptor to a
process it starts, or to the program it replaces itself with, which inherits it. That is how the
process a [project MCP server](../../glossary.json#concept.project-mcp-server) runs for one
`task_merge` call, having taken both locks and answered, gives them to the `concorde task merge`
it replaces itself with, so that the locks belong to the work: the long-lived server takes no lock
at all. A wait for a lock's
release blocks on the lock itself, so the kernel wakes it when the holder ends or dies
([contracts](contracts.md#locks)).

### Retention

Traces are removed only at defined points, never by a process running in the
background: `concorde trace prune`, and the start of every `task open` and `task close`, remove
each unbound run and each run of the lobby that ended more than 7 days ago; from each history folder of a task closed more
than 30 days ago, its **conversation records**, the transcripts of its task sessions and worker
runs, which make up most of the history's size and are read mostly while
the task is fresh; and, when the project configures it, each history folder of a task closed longer
ago than that, whole. By default the rest of the history is kept. A project changes the three
periods in its tracked [Tracing configuration](contracts.md#contract.tracing.configuration),
`.concorde/tracing.json`. A node still running is never removed, and nothing of a current task is.
What a task decided outlives this retention: Tasks commits each ended task's
[decision log](../../glossary.json#concept.decision-log) to Git, where it travels with the code.

## How it is built

### Why Tracing combines the records

Two needs meet in Tracing. Every level already had to leave some record, because the level above
decides from it; and a developer who wants to know why a task was expensive, slow or failed needs
all those records together, in one shape, below the task. Before this Module each level kept its own
record in its own shape, flat and side by side: runs and worker runs as siblings in one store, the
[workflow record](../../glossary.json#concept.workflow-record) elsewhere, a task's history inside its record, and nothing added up. Tracing is the
capability of combining those records; the levels still own what they record.

### Nested by the parent, referenced among peers

A tree whose nesting is the folder layout cannot lose a child: a node is created inside its parent's
folder, at the location the parent chose before starting it, so there is no orphan to reattach and no
parent identity a child could get wrong. Nodes of the same level are not nested, because neither
contains the other; a run that admitted another run's output refers to it by identity.

The link between the halves goes downward only because
[Execution knows no task](../../execution/requirements.md#req.execution.no-task-knowledge). The task
places its workspace's folder inside its own, and the binding tells Execution to write there; so a
task's trace reaches every run of its workspace without Execution ever learning that a task exists,
and the same Execution serves a workspace someone else prepared, with a folder that preparer chose.
The link is at the workspace, not at each task session, since a workspace is what Execution knows.

### One record, structured for analysis

Analysis compares like with like: the cost of every `implement` worker on one model, the duration
of every `delivery`, the checks that failed most. That needs every level to answer the same
questions in the same fields, which is why `trace.json` is uniform and why its metadata is a closed
set of dimensions rather than free text. The producer's own content stays its own, as a typed value
it registers, so a level can record what only it knows without widening the uniform part. A derived
index for faster queries is allowed but is never the source of truth; the nodes are.

A node records only its own usage because the levels nest: a run's cost is the sum of its worker
rounds' costs, and a run that also recorded that sum would count it twice in every total above it.
Metadata records only what Concorde observed, since a worker's statement about itself is a claim,
kept in the content where the producer puts it.

Large and growing content, a transcript or a log, stays a file of the node's folder
named by path and digest; copying it into the record would make every record as large as its
largest file and make the uniform part slow to read. Writing the record at the start and again at
the end costs one more write per node and means a crashed process still leaves a node that says when
it started and what it was doing.

A node refers to its files and to other nodes without absolute paths because a task's folder moves
when the task ends, and because a history copied to another machine must still read. What a node
keeps as it was reported is different: a [run result](../../glossary.json#concept.run-result) and the
error link it carries are what their receiver acts on at once, so their evidence names absolute
paths the receiver can open. The node keeps them unchanged, the result as a file of its folder named
relatively, and never follows those paths to find its own files or its children.

### One folder per task, by its lifecycle

The organising axis is the task's lifecycle, not a split between state and traces: while the task
is current everything about it is in one folder, and closing it moves that one folder to the
history. A reader never has to join a task's record, its [decision log](../../glossary.json#concept.decision-log), its sessions and its runs
from four stores, and removing or exporting a task is one folder. State that commands act on, the
[task record](../../glossary.json#concept.task-record), still lives in that folder beside the task's
trace node, but it is not a trace: it holds only what the commands need, and the history of the task
is in its trace.

Locks are the exception, and deliberately. A lock is not a record of anything; it exists so that one
process at a time does something, and it must outlive the folders it protects from moving: a close
takes the workspace lock precisely to move the task's folder. Keeping every lock in one place with
nothing else also lets a reader tell a live run from a dead one without searching the traces, and
lets a folder move or be removed without a held lock moving with it.

A worker's runtime inputs are not traces either. Its generated configuration, the copies of the
credentials it needs, its home, temporary and working directories exist only while it runs, in a
private directory outside the records that is removed when it ends; what analysis needs, the grant,
the brief and the transcript, is kept in its node. Credentials are therefore never retained.

### Why errors travel as a chain

<a id="realization.tracing.error-chain"></a>

The [error chain](../../glossary.json#concept.error-chain) is part of tracing because it is the path a
failure takes up the levels, retained with each level's reason for passing it on. It stays in band:
each level adds its link on top of the unchanged links below and hands the whole chain to the level
above in its result or record, so every receiver decides from what it received, even when the
traces are gone. Summarizing an error loses what the next level needs to decide, and re-describing
it at every level lets the account drift; keeping the received causes unchanged preserves the
account while each level explains its own inability to proceed. The
[error contract](contracts.md#contract.tracing.error) makes this checkable: the runner checks the
chain against its schema, and the main agent extends it through a command, so the developer receives
the whole path from the failing check to the question they are asked.

**Error chain code** builds and renders the links in the shape of the error contract: the schema,
the reasons a level cannot handle an error, helpers turning an exception or finding into a link, and
the human rendering. Workers, Check execution, the Execution runner, Workflows, Tasks, Task sessions
and the Issues command report with it, so every level's link has the same shape whoever wrote it.
Spec tooling keeps its own error types and does not use it; a Module that receives a Spec tooling
error translates it into a link.

### The parts

<a id="realization.tracing.library"></a>

The **tracing library** gives every producer the same means: the layout's paths, writing a node at
its start and its end atomically with its artifacts' digests, checking a node against the node
contract and its content against the type its producer registered, the locks under
`.concorde/locks/` with handing a held lock on to a process and waiting for a lock's release or its
next holder without polling, walking a tree and rolling usage up, finding a node by identity, telling a run
lost by its run lock, and removing what retention allows. It never decides what a producer records.

<a id="realization.tracing.command"></a>

The **trace command** is `concorde trace`: `show`, `list` and `prune` over the library. It is the
one command of this Module and, like every command, is named after its owner.

<a id="realization.tracing.tests"></a>

The **Tracing tests** exercise the library and the command on traces they build, and the error
chain code.

### What Tracing relies on

<a id="uses-spec"></a>

**Spec core** registers and checks [typed values](../../glossary.json#concept.typed-value): a node's
content is a typed value whose type its producer registered there, and the library refuses to write
content that fails its type rather than record it in a shape nobody declared. Tracing relies on no
Module that produces traces; they rely on it.
