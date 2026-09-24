# Tasks

## Purpose

Tasks gives every unit of work the main agent starts its own place: a Git branch, a worktree
checked out on it, a task record and a decision log. The main agent relies on it to run several
pieces of work side by side without their changes mixing, to know at any time which tasks exist
and what state each is in, and to keep the reasons behind the choices it made without the
developer. The Operation host relies on it to find a task's worktree and to record every Operation
run and delivery against the task. Tasks keeps these records in the primary worktree only. It does
not decide how work is split or which tasks run in parallel, never runs an Operation, never
commits or merges, and never interprets the decision log; the main agent does all of that.

## Terminology

| Term | Definition |
| --- | --- |
| Task | One unit of work of the main agent, made of a branch, a worktree checked out on it, a task record and a decision log. |
| Task record | The JSON file in the primary worktree that holds a task's identity, goal, Modules, branch, worktree path, base commit, state, Operation runs, deliveries and the error chains escalated to the developer. |
| Decision log | The Markdown file next to a task record in which the main agent writes the choices it made without the developer, and to which its escalations are appended. |
| Task state | The stage of a task's life: open, active, delivered, merged or abandoned. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [File transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |

A task is the whole; the task record and the decision log are its two files, and the task state is
one field of the record. Learn Task first.

## Usage

<a id="concept.tasks.task"></a>

The main agent opens a **task** for each piece of work it wants isolated, for example "let Issue
reports carry a severity" bound to `module.issues`. It runs the command in the primary worktree:

```text
concorde task open severity --goal "let Issue reports carry a severity" --modules module.issues
```

Tasks checks that the identity is new and that every named Module exists in the
[registry](../spec-tooling/spec/module.md#concept.spec.registry), creates the branch
`concorde/severity` from the primary worktree's current commit (or from `--base <ref>`), adds a
worktree for it next to the primary checkout, by default at `<parent>/<primary>.tasks/severity`
(or at `--path <dir>`), writes the task record and the decision log, and prints the record. From
then on the main agent names the task in every Operation it runs, `concorde run implement --task
severity`, and the Operation host works in that worktree. Parallelism exists only between tasks:
two tasks never share a worktree, and one task runs at most one Operation at a time.

<a id="concept.tasks.task-record"></a>

The **task record** lives at `.concorde/tasks/<task-id>.json` in the primary worktree. It holds the
task's identity, goal, Modules, branch, absolute worktree path, base commit and state, one entry
per Operation run with its status, and one entry per delivery with its commit and evidence bundle.
`concorde task list` prints the records, optionally filtered by `--state`, and `concorde task show
<task-id>` prints one record with the path of its decision log. The exact fields are in the
[task record contract](contracts.md#contract.tasks.record).

The Operation host updates the record through Tasks while it runs: when a run starts, when it
finishes and when Delivery commits. An Operation run may name further Modules with `--modules`;
Tasks adds them to the record's Modules, so the record always lists every Module the task touched.
A second run for a task whose earlier run is still going is refused with `task_busy`. A run left
`running` by a host process that no longer exists is marked `interrupted` when the next run
starts.

<a id="concept.tasks.decision-log"></a>

The **decision log** lives at `.concorde/tasks/<task-id>.decisions.md`. Tasks creates it with a
heading and the goal when the task opens and otherwise only appends escalations to it. The main
agent appends to it directly: every design uncertainty it decided on its own, with the options and
the reason, and every Operation result that was not `ok` and what it did about it. It is the place
the main agent reads from when it reports to the developer at the end of the task.

When the main agent cannot handle an error itself and asks the developer, it escalates with
`concorde task escalate`: it names the runs, or the saved refusals of other commands, whose errors
it cannot handle, and states its own link of the
[error chain](../vocabulary.md#concept.concorde.error-chain): a code, the detail of what it needs
decided, the reason it may not decide it itself, what it tried, the options and its
recommendation. Tasks puts those errors unchanged under that link as its causes, appends the chain
to the task record's escalations and to the decision log, rendered for a human and as JSON, and
prints it, so the developer reads one chain from the main agent's question down to where the error
started.

<a id="concept.tasks.task-state"></a>

A task's **task state** moves forward only:

```d2 illustrative
start: "" {shape: circle; width: 16; height: 16; style.fill: black}
open
active
delivered
merged
abandoned
start -> open: task open
open -> active: first Operation run
active -> delivered: delivery commit
delivered -> active: a writing Operation starts
delivered -> merged: task close --merged
open -> abandoned: task close --abandoned
active -> abandoned: task close --abandoned
delivered -> abandoned: task close --abandoned
```

A task is **open** until its first Operation run starts, then **active**. Delivery makes it
**delivered**; if the main agent later starts an Operation that may write, such as another
`implement` after a code review, it returns to active and needs another delivery. The main agent
merges the task branch into the primary branch itself, with Git and without asking the developer,
and then runs `concorde task close <task-id> --merged`, which Tasks accepts only when the latest
delivery commit is the head of the task branch, that head is contained in the primary branch, and
the worktree has no uncommitted change. `concorde task close <task-id> --abandoned` ends a task that
will not be merged; it refuses a worktree with uncommitted changes unless `--force` is given.
Closing removes the worktree and keeps the branch, the task record and the decision log. Merged and
abandoned tasks accept no further Operation run.

Only the main agent opens and closes tasks, and only from the primary worktree: the commands refuse
to run in a linked worktree (`not_primary`). A [worker](../vocabulary.md#concept.concorde.worker)
cannot run them at all, because it has no access to Git. Every refusal is an error link that names
its code, such as `task_exists`, `unknown_module`, `invalid_transition` or `not_merged`, what
exactly was refused with the concerned task, Module, path or Git output, and why Tasks cannot handle
it; a refusal changes nothing. The command outputs and error codes are in the
[contracts](contracts.md).

## Design

The task is the unit of isolation because Git already isolates branches and worktrees well: each
task's changes stay in its own checkout until Delivery commits them and the main agent merges them,
so two tasks can change the same Module at the same time and meet only at merge time, where Git
reports any conflict. A shared checkout would instead let one task's half-finished edits leak into
another's checks and audits.

The records live in the primary worktree, not in the task worktrees, for two reasons. The main agent
works in the primary and must see every task in one place, including tasks whose worktree was
already removed. And a task worktree is exactly what workers and Delivery change and commit, so
records kept there would be swept into delivery commits and merges. The `.concorde/tasks/`
directory is therefore local state of the primary checkout, ignored by Git like the run records in
`.concorde/runs/`; the evidence that travels with the code is the evidence bundle Delivery commits.
Any process working for a task, including an Operation host started from a task worktree, finds the
primary worktree through Git's common directory.

Several Operation hosts of different tasks may update records at the same time, and the main agent
may read them meanwhile. Every write is therefore one
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) bound to the
digest of the bytes it replaces, so a concurrent change is detected instead of lost: Tasks rereads
the record, reapplies the update if its preconditions still hold, and refuses with
`record_conflict` after three attempts. Each task has its own record file, so tasks never contend
with each other.

States only move forward, apart from delivered returning to active, and closing is checked against
Git rather than trusted: a task is merged only when Git shows its delivered head inside the primary
branch. This keeps the record honest even though the merge itself is done by the main agent outside
Tasks. The decision log is free Markdown because its reader is the main agent and the developer;
Tasks gives it a fixed place and lifetime and nothing more. The precise obligations are in the
[requirements](requirements.md) and shown in the [scenarios](scenarios.md).

<a id="realization.tasks.store"></a>

The **Task store** realization holds the `concorde task` commands (`src/concorde/tasks/cli.py`),
the task records and the updates the Operation host calls (`src/concorde/tasks/store.py`), and
their tests, which run on real Git repositories.

## Relationships

```d2
store: Task store
record: Task record
log: Decision log
task: Task
state: Task state
tasks: Tasks
spec: Spec core
store -> record: writes
store -> log: creates
record -> task: describes
record -> state: holds
log -> task: explains the choices of
tasks -> spec
```

The Task store is the only writer of task records, and it writes each decision log only once, when
the task opens. A record describes exactly one task and holds its current state; the decision log
explains the choices made during that task. Operations, Validation and Delivery read and update
records through the Task store; they rely on Tasks and Tasks relies on none of them.

<a id="uses-spec"></a>

**Spec core** provides two things Tasks relies on. Its registry answers whether the Modules named
when a task opens or when a run adds Modules exist, so a record never names an unknown Module. Its
[file transactions](../spec-tooling/spec/module.md#concept.spec.file-transaction) make every record
write complete or absent and bound to the bytes it replaces. Tasks reads the registry of the primary
worktree when it opens a task, because the task worktree does not exist yet; later Module checks use
the task worktree's registry. If the Specs cannot be loaded, the command is refused and nothing is
written.
