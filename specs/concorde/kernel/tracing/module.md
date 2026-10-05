# Tracing

## Purpose

Tracing is the [Kernel](../module.md)'s child. It decides which information about Concorde's work
is combined and retained. It decides the structure of that information for later analysis.
The analysis ranges from a whole task down to one round of one worker and covers:

- What ran.
- Where it ran.
- On which model it ran.
- For how long it ran.
- At what cost it ran.
- With what outcome it ran.

Tracing owns:

- That structure.
- The uniform record every level of work leaves.
- The metadata by which records are compared.
- The trace roots under which the parts keep their trees.
- How long each is kept.
- The locks that are kept apart from the records.
- The command that reads the records.
- The [error chain](../../glossary.json#concept.error-chain) through which a failure travels up
  the levels.

Like the rest of the kernel part, it depends on no other part. Every part that records its work
depends on it.

Tracing does not produce the information. Each [Module](../../glossary.json#concept.module) that
does work still decides and writes the content of its own records. In Concorde, these Modules are:

- Tasks.
- [Task sessions](../../glossary.json#concept.task-session).
- Workflows.
- Execution.
- Workers.
- Check execution.

Tracing gives each of them the place and the shape. It knows none of them. A part tells Tracing
which trace roots it keeps and which node kinds it produces. Tracing applies the same rules to all.
It keeps no state a command acts on. A [task record](../../glossary.json#concept.task-record)
or a lock is not a trace. When a task ends, Tasks commits the
[decision log](../../glossary.json#concept.decision-log) to Git. The decision log is the task's
own record. Whatever retention removes, the decision log stays with the code.
Spec tooling reports with its own error record. Spec tooling never uses the error chain.

## Core concepts

### Traces and trace nodes

<a id="concept.trace"></a><a id="concept.trace-node"></a>

Every level of work in Concorde leaves one
**[trace node](../../glossary.json#concept.trace-node)**. A trace node is a folder holding:

- A `trace.json` record in one uniform shape.
- The files that level keeps next to the record.
- The folders of the nodes below it.

The record holds these fields:

- The identity of the node.
- Its kind.
- Its times.
- Its status.
- Its own usage.
- Its error link.
- Its metadata.
- Its artifacts.
- Its references.
- The content of its producer.

Each of the following is a node:

- A task.
- Each of its task sessions.
- Each merge attempt.
- The workflow of its workspace.
- Each of the workflow's steps.
- Each run of an [Operation](../../glossary.json#concept.operation) or
  [execution command](../../glossary.json#concept.execution-command).
- Each [configured check](../../glossary.json#concept.configured-check) a run or a merge ran.
- Each worker run.
- Each of the worker run's rounds.

The tree of nodes below one task, or below one
[unbound run](../../glossary.json#concept.unbound-run), is a **[trace](../../glossary.json#concept.trace)**.
The nodes nest as the work did:

- Below a task lie its task sessions, its merge attempts and its workspace.
- Below the workspace lie its workflow and its runs.
- Below a run lie its checks and its worker runs.
- Below a worker run lie its rounds.

### Trace roots

A tree of nodes starts at a **trace root**. A trace root is a folder under a `.concorde` directory
in which a part keeps the top nodes of its traces. The part that keeps them registers the root
with Tracing, saying:

- Where the root lies.
- Which node kind its top nodes have.
- Whether its folders are still current or closed for good.
- How long its nodes are kept after they ended.

Through those registrations alone, Tracing performs these actions:

- Finds nodes.
- Lists nodes.
- Applies retention.

It therefore never learns what a task or a run is.

In Concorde two parts register roots. Coordination keeps each current task in
`.concorde/tasks/<task>/`. That one folder holds:

- Its record.
- Its decision log.
- Its trace.

When the task is closed, Coordination moves that folder whole to its
[history](../../glossary.json#concept.history), `.concorde/history/<task>/`.
A history folder is closed for good. Except when the closing merge finishes the answer it writes
into its own attempt's node, nothing in a history folder ever changes.
Execution keeps an unbound run in `.concorde/unbound/<run>/` of the worktree it started in.
An unbound run belongs to no workspace. Until a bound run holds its workspace's lock, Execution
keeps it in the lobby, `.concorde/lobby/<run>/`, outside the workspace folder.
This prevents a close that moves the workspace folder while holding the lock from racing the run.
Once the run holds the lock, it moves into the workspace folder. When the run is refused before
it holds the lock, it stays in the lobby. The [layout](contracts.md#layout) gives every path.

### The error chain

<a id="concept.error-chain"></a>

An **[error chain](../../glossary.json#concept.error-chain)** preserves both the original
failure and why each receiving level could not handle it. When a level cannot handle an error it
received, it adds its own detailed link, with its reason, on top of the unchanged links below.
When a result is not `ok`, it carries its error chain whole, as the
[error contract](contracts.md#contract.tracing.error) defines. Its receiver decides from the chain
alone. The receiver never has to open a trace to learn what failed. The chain may name trace nodes
as entry points for a deeper analysis, never in place of what it says. How to read a chain, and where each
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

A level above another holds it. A node's children lie in folders inside its own folder.
The parent places the children there. Before a child starts, the parent gives the child its
location. Therefore, no node is ever recorded without its parent.
Nodes at the same level may refer to each other instead. A run names the earlier runs it admitted
as inputs. A delivery run names the [delivery commit](../../glossary.json#concept.delivery-commit)
it created. The runs a [workflow step](../../glossary.json#concept.workflow-step) starts lie inside
that step. The runs a task session or the [main agent](../../glossary.json#concept.main-agent)
starts directly lie in the workspace beside the workflow.

A trace crosses Concorde's two halves in one direction only. The task's node holds its workspace's
folder. Therefore, an analysis walks from a task down to everything that ran for it.
Since the parts that work in a workspace know no task, nothing below the workspace records the
task. Nothing walks back up. The [workspace binding](../../glossary.json#concept.workspace-binding)
gives those parts the folder they write into. Whoever prepared the workspace chose that folder.

### Where records live

Each registered root keeps its trees for as long as its part says. In Concorde, while a task is
current, its folder is current. When the task is closed, its folder moves whole to the history.
In the history, only retention removes anything. Retention first removes the task's conversation
records. Then, when the project configures it, retention removes the whole folder.
An unbound run, and a run that never left the lobby, is kept beside the tasks and removed sooner.
The decision log leaves with the task into Git. Therefore, it outlives every retention period.
The locks lie apart from all these folders ([Locks are not records](#locks-are-not-records)).

```d2 illustrative
direction: right
coordination: "Roots Coordination registers" {
  open: "task open" {shape: oval}
  current: "Current task\n.concorde/tasks/<task>/\nrecord, decision log, trace"
  history: "History\n.concorde/history/<task>/\nnever changed"
  slim: "History folder without\nits conversation records"
  git: "Git, with the code\n.concorde/decisions/"
  open -> current
  current -> history: "task close,\nmerged or not"
  current -> git: "task close: Tasks commits\nthe decision log" {style.stroke-dash: 3}
  history -> slim: "closed more than\n30 days ago (default)"
}
execution: "Roots Execution registers" {
  unbound: "Unbound run\n.concorde/unbound/<run>/"
  lobby: "Run refused before it held\nits workspace's lock\n.concorde/lobby/<run>/"
}
removed: "Removed" {shape: oval}
coordination.slim -> removed: "closed longer ago than\nthe project configures,\nif it does"
execution.unbound -> removed: "ended more than\n7 days ago (default)"
execution.lobby -> removed: "ended more than\n7 days ago (default)"
```

### Tracing and its producers

Every producer writes its nodes through the tracing library. Every producer takes its locks
through the tracing library. Every producer reports its failures with the error chain code.
The parts that keep roots register them. The trace command reads through the same library.
The trace command prunes through the same library.

```d2 illustrative
tracing: Tracing {
  library: Tracing library
  command: Trace command
  errors: Error chain code
  command -> library: reads and prunes through
}
producers: "Tasks, Task sessions, Workflows,\nExecution, Workers, Check execution" {shape: page}
producers -> tracing.library: "write their nodes, take their locks\nand register their roots through"
producers -> tracing.errors: report with
```

## Using traces

### What a node records

Every `trace.json` holds the same fields, defined by the
[trace node contract](contracts.md#contract.tracing.node):

- Its identity and kind.
- When it started and ended.
- Its status, from these values:
  - `running`.
  - `ok`.
  - `blocked`.
  - `failed`.
  - When its producer never observes the node's end, `unknown`.
  The status is accompanied by the producer's own finer outcome, such as `merged` for a task or
  `timed_out` for a check.
- Its own **usage**, with these figures:
  - Tokens in.
  - Tokens out.
  - Tokens through the cache.
  - Cost.
  - Turns.
  - Duration.
  The usage covers the node itself, never its children.
  Because of this, a sum over a subtree counts every token once.
- When it did not end `ok`, its error link.
- **Metadata**, whichever the level has:
  - The workspace.
  - The Modules.
  - The Operation or command.
  - The [task type](../../glossary.json#concept.task-type).
  - The [worker id](../../glossary.json#concept.worker-id).
  - The backend.
  - The model.
  - The reasoning level.
  - The commit.
  - The [context identity](../../glossary.json#concept.context-identity).
  - The grant and brief digests.
  - The Concorde commit.
  - The Protocol version.
  Metadata comes only from what Concorde observed itself, never from a worker's claim.
  This allows nodes of one kind to be selected and compared by their metadata.
- **Artifacts**: the files it keeps in its folder. Each artifact is referenced by its path relative
  to the folder and its digest. Examples include:
  - A transcript.
  - A log.
  - A run result.
  This means a transcript is referenced, never copied.
- **References** to nodes at the same level and to commits. These distinguish two kinds of commit:
  - A commit the node created (`commit`).
  - A commit an earlier node created and this node only found (`found_commit`).
  An example is a delivery that finds its work already delivered.
- The producer's own **content**, a [typed value](../../glossary.json#concept.typed-value).
  The producer registers its type. Examples include a run's steps with their timings or a worker
  round's audit.

The figures of a node's usage come from what the agent program itself reported or recorded,
never from a computation of Concorde's own. A worker round's figures come from the result its
agent process returned. A task session's figures come from Claude Code's records of the session.
When its task ends, these records are read.
Concorde keeps no price table, so when the program did not report a cost, that cost stays null.
A task session's node is the one whose end Concorde does not see happen.
When the task ends, Task sessions finishes the node from these sources:

- The session's transcript.
- Claude Code's own account of the session.

When the task ends, Task sessions writes the figures into the node as part of finishing it.
The reason is that retention later removes the transcript they came from.

When the node starts, a producer writes its node. When the node ends, the producer rewrites it.
These writes mean that a node that still runs, or whose process died, is already there.
A node never refers to a file or another node by an absolute path.
It names its files relative to its own folder. It names other nodes by their identity.
The reason is that, when the task ends, the task's folder moves.

### Reading a trace

`concorde trace` reads traces. It never changes one:

```text
concorde trace show [<node>] [--depth <n>] [--format json|tree]
concorde trace list [--history] [--unbound] [--format json|tree]
concorde trace prune [--dry-run]
```

`show` takes one of these:

- A task name.
- A run identity.
- A worker run identity.
- A node's folder.

It prints the node with its subtree, including:

- Each node's status.
- Each node's times.
- Each node's own usage.
- The usage rolled up over each node's subtree.

This lets a reader read these costs in one place:

- The cost of a whole task.
- The cost of one of its workflows.
- The cost of one run.

It finds a node among the registered roots of the worktree it runs in and of the primary worktree.
In Concorde, these roots are:

- The current tasks.
- The [history](../../glossary.json#concept.history).
- The unbound runs.
- The lobby.

When its writing process ended but a node says it still runs, `show` shows the node as `lost`.
This applies in both cases:

- The node appears below its run.
- The node is addressed directly.

A worker run is addressed directly by its identity.
`list` lists the current tasks with their status and rolled-up usage.
With its options, it also lists the history and the unbound runs with their status and rolled-up
usage. When a root's part is not installed, the root is simply not searched or listed.
Tracing registers `concorde trace` as a command of the kernel part.
A result's error chain names the node that reported the result as evidence of kind `trace`.
The evidence's reference is the run or worker run identity.
Because of this, a reader goes from an error to its trace with `show`.

For a task `retry` whose session ran `implement` and then `delivery`,
`concorde trace show retry --format tree` prints:

- The task.
- Its session.
- The two runs under its workspace.
- The `implement` run's worker run with its rounds and checks.
- The total cost of the task, with the cost of each run beside it.

### Locks are not records

Every lock Concorde takes lies under `.concorde/locks/`, never inside a trace or a task folder.
Its file holds only who holds it now. Tracing gives every lock its place and its holder line.
The parts that take locks decide which locks exist and who takes each.
These locks include the Kernel's own [merge lock](../../glossary.json#concept.merge-lock) and
[workspace lock](../../glossary.json#concept.workspace-lock):

| Lock | Taken by | Kept |
| --- | --- | --- |
| [merge lock](../../glossary.json#concept.merge-lock) `merge.lock` | a task merge, open or close, and an [Issue](../../glossary.json#concept.issue) write | always |
| task lock `tasks/<task>.lock` | a change of the task's record | until the task is closed |
| [workspace lock](../../glossary.json#concept.workspace-lock) `workspaces/<workspace>.lock` | a run of the workspace, a merge or close of its task | until the task is closed |
| workflow lock `workflows/<workspace>.lock` | a workflow step or report of the workspace, a close of its task, also the close that ends its merge | until the task is closed |
| [run lock](../../glossary.json#concept.run-lock) `runs/<run>.lock` | the run's runner only | removed by the runner as it exits |

A lock file's holder line names:

- The holder.
- Its process.
- Since when it holds the lock.
- When known, the Claude Code session it works for.
- When known, the task.

This lets whoever is refused learn who to wait for. A lock can be handed on.
Its holder passes the locked descriptor to a process it starts or to the program it replaces
itself with. The receiving process or program inherits the descriptor.
That is how the process a [project MCP server](../../glossary.json#concept.project-mcp-server)
runs for one `task_merge` call hands on both locks. That process takes both locks and answers.
It then gives them to the `concorde task merge` it replaces itself with.
This handoff makes the locks belong to the work. The long-lived server takes no lock at all.
A wait for a lock's release blocks on the lock itself.
Because of this, when the holder ends or dies, the operating system wakes the wait
([contracts](contracts.md#locks)).

### Retention

Traces are removed only at defined points, never by a process that runs in the background:

- `concorde trace prune`.
- Whenever a part that registers a root asks for retention.

Coordination asks for retention at the start of every `task open` and `task close`.
Each root is pruned by the periods its part registered. In Concorde, this removes:

- Each unbound run that ended more than 7 days ago.
- Each run of the lobby that ended more than 7 days ago.
- From each history folder of a task closed more than 30 days ago, its **conversation records**.
- When the project configures it, each whole history folder of a task closed longer ago than that.

The conversation records are the transcripts of the task's task sessions and worker runs.
They make up most of the history's size.
While the task is fresh, the conversation records receive most of their reads.
By default the rest of the history is kept. A project changes the three periods in its tracked
[Tracing configuration](contracts.md#contract.tracing.configuration), `.concorde/tracing.json`.
When no installed part registers a root, that root's period is ignored.
A node that still runs is never removed. Nothing of a current folder is removed.
`concorde trace prune` prunes the `.concorde` directories `show` searches.
This means that, when it runs in a linked worktree, that worktree's unbound runs go.
The command prints every path it could not remove with the operating system's error.
Until the rest of such a folder is gone, the folder keeps its `trace.json`.
This lets the next prune find the folder and try again.
What a task decided outlives this retention.
Tasks commits each ended task's [decision log](../../glossary.json#concept.decision-log) to Git.
In Git, the decision log travels with the code.

## How it is built

### Why Tracing combines the records

Two needs meet in Tracing. Every level already had to leave some record, because the level above
decides from it. A developer needs all those records together, in one shape, below the task to
understand these outcomes:

- Why a task was expensive.
- Why a task was slow.
- Why a task failed.

Records each level kept in its own shape, side by side, would add nothing up.
That arrangement would keep:

- Runs and worker runs as siblings in one store.
- The [workflow record](../../glossary.json#concept.workflow-record) elsewhere.
- A task's history inside its record.

Tracing is the capability of combining those records. The levels still own what they record.
Tracing belongs to the kernel part for these reasons:

- Every part that records its work needs the same shape and the same place.
- None of those parts may depend on another to get it.

### Nested by the parent, referenced among peers

A tree whose nesting is the folder layout cannot lose a child. A node is created inside its parent's
folder, at the location the parent chose before starting it. Because of this placement, there is no
orphan to reattach and no parent identity a child could get
wrong. Nodes of the same
level are not nested, because neither contains the other. A run that admitted another run's output
refers to it by identity.

The link between the halves goes downward only because
[Execution knows no task](../../execution/requirements.md#req.execution.no-task-knowledge). The task
places its workspace's folder inside its own. The binding tells the parts that work in the
workspace to write there. Because of this placement and binding, a task's trace reaches every run
of its workspace without any run ever learning that a task exists. The same parts therefore serve
a workspace someone else prepared, with a folder that preparer chose. Since a workspace is what
these parts know, the link is at the workspace, not at each task session.

### One record, structured for analysis

Analysis compares like with like:

- the cost of every `implement` worker on one model
- the duration of every `delivery`
- the checks that failed most

That needs every level to answer the same questions in the same fields. This is why `trace.json`
is uniform. It is also why its metadata is a closed set of dimensions rather than free text.
The producer's own content stays its own, as a typed value it registers. This lets a level record
what only it knows without widening the uniform part. A derived index for faster queries is
allowed but is never the source of truth. The nodes are the source of truth.

A node records only its own usage because the levels nest. A run's cost is the sum of its worker
rounds' costs. If a run also recorded that sum, it would count the cost twice in every total above
it. Since a worker's statement about itself is a claim, metadata records only what Concorde
observed. The claim stays in the content where the producer puts it.

Large and growing content, a transcript or a log, stays a file of the node's folder named by path
and digest. This is because copying it into the record would make every record as large as its
largest file. Copying it would also make the uniform part slow to read. Writing the record at the
start and again at the end costs one more write per node. These writes mean a crashed process
still leaves a node that says when it started and what it was doing.

A node refers to its files and to other nodes without absolute paths for these reasons:

- A task's folder moves when the task ends.
- A history copied to another machine must still read.

What a node keeps as it was reported is different. A [run result](../../glossary.json#concept.run-result)
and the error link it carries are what their receiver acts on at once. Their evidence therefore
names absolute paths the receiver can open. The node keeps the run result and its error link
unchanged. The result stays as a file of the node's folder named relatively. The node never follows
those absolute paths to find its own files or its children.

### One folder per top node, by its lifecycle

The organising axis is the lifecycle of a root's top node, not a split between state and traces.
Coordination registers a task. While the task is current, everything about it is in one folder.
Closing the task moves that one folder to the history. A reader never has to join these parts of a
task from four stores:

- its record
- its [decision log](../../glossary.json#concept.decision-log)
- its sessions
- its runs

Removing or exporting a task involves one folder. State that commands act on, the
[task record](../../glossary.json#concept.task-record), still lives in that folder beside the task's
trace node. The task record is not a trace. It holds only what the commands need. The history of
the task is in its trace.

Locks are the exception, and deliberately. A lock is not a record of anything. It exists so that
one process at a time does something. It must outlive the folders it protects from moving. The
reason is that a close takes the workspace lock precisely to move the task's folder. Keeping every
lock in one place with nothing else also lets a reader tell a live run from a dead one without
searching the traces. It also lets a folder move or be removed without a held lock moving with it.

A worker's runtime inputs are not traces either. Only while the worker runs, these inputs exist
in a private directory outside the records:

- its generated configuration
- the copies of the credentials it needs
- its home directory
- its temporary directory
- its working directory

When the worker ends, the private directory is removed. What analysis needs stays in the worker's
node:

- the grant
- the brief
- the transcript

Credentials are therefore never retained.

### Why errors travel as a chain

<a id="realization.tracing.error-chain"></a>

The [error chain](../../glossary.json#concept.error-chain) is part of tracing because it is the path a
failure takes up the levels. The chain is retained with each level's reason for passing the failure
on. It stays in band. Each level adds its link on top of the unchanged links below. The level hands
the whole chain to the level above in its result or record. Because each level hands on the whole
chain, every receiver decides from what it received, even when the traces are gone. Summarizing an error loses what the next level
needs to decide. Re-describing the error at every level lets the account drift. Keeping the
received causes unchanged preserves the account while each level explains its own inability to
proceed. The [error contract](contracts.md#contract.tracing.error) makes this checkable. The runner
checks the chain against its schema. The main agent extends the chain through a command. Through
these checks and extensions, the developer receives the whole path from the failing check to the
question they are asked.

**Error chain code** builds and renders the links in the shape of the error contract. It includes:

- the schema
- the reasons a level cannot handle an error
- helpers turning an exception or finding into a link
- the human rendering

These producers report with Error chain code:

- Workers
- Check execution
- the Execution runner
- Workflows
- Tasks
- Task sessions
- the Issues command

Because they report with it, every level's link has the same shape whoever wrote it. Spec tooling
keeps its own error types and does not use Error chain code. When a Module receives a Spec tooling
error, the Module translates it into a link.

### Its realizations

<a id="realization.tracing.library"></a>

The **tracing library** gives every producer the same means:

- the layout's paths
- writing a node at its start and its end atomically with its artifacts' digests
- checking a node against the node contract and the registration of its kind
- checking a node's content against the type its producer registered
- the node kinds and trace roots the parts register
- the locks under `.concorde/locks/`
- handing a held lock from that directory on to a process
- waiting for such a lock's release or its next holder without polling
- walking a tree and rolling usage up
- finding a node by identity
- telling a run lost by its run lock
- removing what retention allows

It never decides what a producer records.

<a id="realization.tracing.command"></a>

The **trace command** is `concorde trace`. It provides these operations over the library:

- `show`
- `list`
- `prune`

It is the one command of this Module. The kernel part registers it with Distribution's `concorde`
command. Like every command, it is named after its owner.

<a id="realization.tracing.tests"></a>

The **Tracing tests** exercise the library and the command on traces they build. They also exercise
the error chain code.

### What Tracing relies on

<a id="uses-kernel"></a>

**The Kernel**, its parent, defines [typed values](../../glossary.json#concept.typed-value).
A node's content is a typed value whose type its producer registered. When content fails its type,
the library refuses to write it rather than record it in a shape nobody declared. Tracing relies
on no Module that produces traces. It relies on no part outside the kernel. Those Modules and
parts rely on Tracing.
