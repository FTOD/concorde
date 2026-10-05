# Tasks

## Purpose

Tasks manages the workspace of the task level. Every unit of work the
[main agent](../../glossary.json#concept.main-agent) starts receives its own place from Tasks:

- A Git branch.
- A worktree checked out on that branch and bound as a
  [workspace](../../glossary.json#concept.workspace).
- A [task record](../../glossary.json#concept.task-record).
- A [decision log](../../glossary.json#concept.decision-log).

Tasks keeps the record and log with the task's [trace](../../glossary.json#concept.trace) in one
folder of its own. When the task ends, that folder moves to the
[history](../../glossary.json#concept.history). The main agent and the task session it delegates
every task to rely on Tasks for these purposes:

- To run pieces of work side by side without their changes mixing.
- To know each task's state.
- To keep the reasons behind choices made without the developer.

When Tasks opens a task, it binds the task worktree. Tasks learns what happened in the worktree only
from what was recorded there. Where the execution part is installed, this includes the workspace's
runs. It also includes the worktree's
[delivery commits](../../glossary.json#concept.delivery-commit). Nothing below the task level reads
or writes a task record. When the main agent merges a delivered task, Tasks merges it into the
primary branch under a lock, so several main sessions never merge at once. If the checks that follow
fail, Tasks undoes the merge. Until the checks decide, Tasks records the merge in the task. Thus, a
merge interrupted halfway stops every task command that would build on it until the merge is resumed
or aborted. When a task ends, merged or not, Tasks commits its decision log to the primary branch.
Thus, the reasons behind the task's choices travel with the code after the local records are gone.
Where the issues part is installed, a task may name the [Issues](../../glossary.json#concept.issue)
it resolves. Once the fix is on the primary branch, the task's merge closes those Issues. Where the
method part is not installed, Tasks also delivers a task itself, with `concorde task deliver`.

Tasks needs only the [Kernel](../../kernel/module.md). Its contracts are:

- The workspace binding.
- The workspace and merge locks.
- The delivery commit.
- File transactions.
- Tracing's trace nodes.

These are [optional integrations](../../glossary.json#concept.optional-integration):

- Runs.
- Issues.
- The registry.
- Method's delivery.

Each integration is described where it applies. Where its part is not installed, the integration is
absent.

Tasks is independent of the sessions that work in its tasks. Tasks does not start or follow them,
which [Task sessions](../task-session/module.md) does. Tasks does not decide:

- How work is split.
- Which tasks run in parallel.
- When a task is merged.

Tasks never runs an [Operation](../../glossary.json#concept.operation) or an
[execution command](../../glossary.json#concept.execution-command). Where the method part is not
installed, Tasks commits on a task branch only for the delivery commit of `task deliver`. Otherwise,
Tasks never commits on a task branch. Tasks never interprets the decision log. It only copies the
log into Git.

## Core concepts

<a id="concept.task"></a>

A **[task](../../glossary.json#concept.task)** is one unit of the main agent's work. For each piece
of work it wants isolated, the main agent opens a task with:

- A branch `concorde/<task-id>`.
- A worktree checked out on that branch and bound as the
  [workspace](../../glossary.json#concept.workspace) named after the task.
- A folder of its own in the primary worktree.

When the task ends, the folder moves to the [history](../../glossary.json#concept.history).

Parallelism exists only between tasks. No tasks share a worktree. The Kernel's
[workspace lock](../../glossary.json#concept.workspace-lock) lets each workspace do one thing at a
time. A task's goal and Modules are those named at open and never change. When a run names further
Modules with `--modules`, it records them in its own
[run result](../../glossary.json#concept.run-result).

<a id="concept.task-record"></a>

Everything about a current task lives in its folder `.concorde/tasks/<task-id>/` of the primary
worktree:

- Its record `task.json`.
- Its trace node `trace.json`.
- Its decision log `decisions.md`.
- The boundary configuration of its task session under `runtime/`.
- The nodes of its task sessions under `sessions/` and of its merge attempts under `merges/`.
- The workspace folder `workspace/` that the runs of its workspace fill.

**The [task record](../../glossary.json#concept.task-record)** holds only what the task commands
need to act on the task:

- Identity.
- Goal.
- Modules.
- Branch.
- Worktree path.
- Base commit.
- The [main agent](../../glossary.json#concept.main-agent)'s session its task sessions report to
  now, with the ones it named before.
- The reports task sessions made to it with its answers.
- Stored state.
- The merge in progress.
- Once the task ended, how it ended.

([exact fields](contracts.md#contract.tasks.record))

The task's history is in its trace instead. The task's node records:

- When the task was opened.
- Every change of its stored state.
- Every escalation.
- How the task ended.

Each task session is a node below the task's node. Each merge attempt with its checks is also a node
below it ([exact content](contracts.md#task-trace)). Neither the task record nor its trace keeps
these:

- Runs.
- Deliveries.
- Workflow.

Those are recorded where they happen, in the workspace folder and on the task branch. After a crash
or a run nobody announced, a copy could disagree with those records.

<a id="concept.decision-log"></a>

**The [decision log](../../glossary.json#concept.decision-log)** lives at
`.concorde/tasks/<task-id>/decisions.md`. At open, Tasks creates the log with a heading and the
goal. Tasks then only appends:

- Escalations.
- Reports and their answers.
- How the task ended.

Before the main agent starts the task's task session, it appends the task's brief. That session,
working on the task, appends these directly:

- Every uncertainty it decided alone, with options and reason.
- Every non-`ok` run result and what it did about it.
- The decisions and problems of a workflow's report.

Workflows saves the workflow's report beside its own record and never writes here.
`concorde task open` prints the log's path beside the new record. When the log still holds only its
heading and goal, `concorde task merge` warns, since a task worked without writing the log has lost
the record of every decision taken alone. The main agent reads the log when it reports to the
developer at the end of the task. When the task ends, the log is committed to the primary branch as
`.concorde/decisions/<history key>.md` ([below](#decision-log-in-git)). The log is the one record of
a task that Git keeps. The log is free Markdown, since its readers are the main agent and the
developer. Tasks gives it only a fixed place and lifetime.

<a id="concept.history"></a>

**The [history](../../glossary.json#concept.history)** is where a task's folder goes when the task
ends. While a task is current, everything about it lives in `.concorde/tasks/<task-id>/`. This
includes its state and its traces alike. Closing the task, merged or not, moves that whole folder to
`.concorde/history/<history key>/`. There, the folder stays as it was when the task ended, except
for `runtime/`, the configuration of its task sessions' boundary. That configuration is no trace.
Once the folder moves, the close removes the configuration. Nothing in the history is ever changed,
except the merge that closed the task finishing the answer it writes into its attempt's node. The
history may be copied out. The organising axis is the task's lifecycle, not a split between state
and traces. A reader never joins these from several stores:

- A task's record.
- Its decision log.
- Its sessions.
- Its runs.

Removing or exporting a task is one folder. Tasks registers the current task folders and the history
with [Tracing](../../kernel/tracing/module.md) as two of its trace roots. Thus,
`concorde trace show` finds a task's nodes in either. Tasks also gives the history its retention.
From each history folder of a task closed more than 30 days ago, Tracing's prune removes its
**conversation records**. These are the transcripts of its task sessions and worker runs. They make
up most of the folder's size. They are read mostly while the task is fresh. When the project
configures a longer period in its
[Tracing configuration](../../kernel/tracing/contracts.md#contract.tracing.configuration), Tracing's
prune removes each history folder of a task closed longer ago than that, whole. Nothing of a current
task is removed. What a task decided outlives retention: when the task ends, its decision log is
committed to Git ([below](#decision-log-in-git)). When a task name is used again after its branch
was deleted, it gets a new history key. The key is free both in the history and among the committed
decision logs, so no closed task replaces another.

These task commands take the Kernel's [merge lock](../../glossary.json#concept.merge-lock) of the
primary worktree:

- Opening a task.
- Merging a task.
- Closing a task.

These commands wait for the lock inside the command, up to `--wait`. When the lock is still held
after `--wait`, the command refuses with `merge_busy`, naming its holder. A merge started by the
[project MCP server](../../glossary.json#concept.project-mcp-server) is handed its locks. That merge
holds the locks from its start without waiting, exactly as long as it runs.

A merge also holds the task's **merge attempt lock**, `locks/attempts/<task>.lock`. The merge holds
this lock from before it waits for its other locks until it prints its whole answer. The merge then
removes the lock. While the merge still closes the task's Issues and writes its answer, the close
that ends the merge removes the task's workspace lock. Thus, only the attempt lock tells that a
merge of the task has really ended. `concorde task wait <task> --merge` waits for that lock. A merge
the server started finds the folder of its attempt's node, `merges/<n>/`, already made and named in
its environment. Its standard output and error go to `output.json` and `messages.log` there. Even
when the merge is refused before it began, it records its attempt in that folder. Thus, the whole
answer of every merge the server started is kept with the task. The answer moves with the task to
the [history](../../glossary.json#concept.history), where the merge finishes writing it.
`concorde task open` and `concorde task close` take the same lock. Thus, a task is never based on,
or closed against, a merge that may still be undone. `close` takes the task's workspace lock before
that lock, as `merge` does. The close waits up to its own `--wait`. While a run of the task could
still write the worktree the close removes, the close then refuses with `workspace_busy`.

A task's **state** is partly stored and partly derived. Only merging and closing a task change its
stored state. Each time an open task is listed or shown, whether it is still open, active or
delivered is derived from what the workspace recorded and from Git ([Task state](#task-state)).

## Overview

### What a task is made of

The task store writes the record. It creates the decision log. It commits a copy of the decision
log. While the store performs any of these actions, it holds the merge lock:

- It merges a task.
- It opens a task.
- It closes a task.

The record, the log and the state fit together this way:

```d2
tasks: Tasks {
  store: Task store {
    "src/concorde/coordination/tasks/cli.py"
    "src/concorde/coordination/tasks/store.py"
    "src/concorde/coordination/tasks/merge.py"
  }
  record: Task record
  log: Decision log
  task: Task
  store -> record: writes
  store -> log: creates, commits a copy of
  record -> task: describes
  log -> task: explains the choices of
}
lock: Kernel / Merge lock
tasks.store -> lock: holds while merging, opening or closing
```

### Task state

From the open until the task ends, the record says `open`. After the task ends, the record says
`closed` or `failed`. In the following situation, the record says **merging**:

- `concorde task merge` has put, or is about to put, a merge of the task into the primary branch.
- Its checks have not decided that merge yet.

Each time an open task is listed or shown, whether it is still **open**, **active** or **delivered**
is derived:

```d2 illustrative
start: "" {shape: circle; width: 16; height: 16; style.fill: black}
open
active
delivered
closed
failed
merging
start -> open: task open
open -> active: a run, a commit or a change in the workspace
active -> delivered: head is a delivery commit that verifies, worktree clean
delivered -> active: a change or a commit after it
delivered -> merging: task merge
merging -> closed: every check passed
merging -> delivered: conflict, failed check, or --abort
delivered -> closed: task close --merged
open -> closed: task close --completed
active -> closed: task close --completed
delivered -> closed: task close --completed
open -> failed: task close --failed
active -> failed: task close --failed
delivered -> failed: task close --failed
```

When both conditions hold, a task is **delivered**:

- Its branch head is a delivery commit of its workspace that verifies, having exactly one parent as
  the Kernel's [convention](../../kernel/contracts.md#delivery-commit) requires.
- Its worktree is clean.

Otherwise, when any of these conditions holds, a task is **active**:

- Where the execution part is installed, its workspace has a running or finished run in the
  [run store](../../glossary.json#concept.run-store).
- Its branch moved past the base commit.
- Its worktree has uncommitted changes.

Before any of these conditions holds, the task is **open**. A run that changes nothing, such as a
review after delivery, leaves a delivered task delivered. A change after the delivery commit,
committed or not, makes the task active until the next delivery.

A new path Git cannot version is no change of the worktree, as Delivery leaves it out of what it
commits. Such a path is none of these:

- A file.
- A symbolic link.
- A directory.

An example is a path a sandbox hides behind a `/dev/null` mount. A change inside a submodule is a
change of the worktree, since removing the worktree would lose it.

When a head carries the subject of a delivery commit but does not verify, it leaves the task active.
`task show` lists that head among the deliveries with its mismatches. That head is never merged
([Merging](#merging)). A task ends in one of two states, closed or failed. The record keeps the
outcome ([Ending a task](#ending-a-task)).

### Around it

Tasks writes one thing for the lower half, the binding. It reads the rest from what was recorded
there, the runs where the execution part is installed and the delivery commits:

```d2
store: Task store
binding: Kernel / Workspace binding
runstore: Execution / Run store
lock: Kernel / Workspace lock
commits: Kernel / Delivery commit
store -> binding: writes when a task opens
store -> runstore: reads the workspace's runs from
store -> lock: holds while merging or closing, shows the holder of
store -> commits: reads from the task branch and verifies
```

## Opening a task

From the primary worktree, the main agent opens a task for each piece of work it wants isolated. For
example, it opens "let [Issue reports](../../glossary.json#concept.issue-report) carry a severity"
bound to `module.issues`:

```text
concorde task open severity --goal "let Issue reports carry a severity" --modules module.issues
```

Tasks checks that the identity is new. Where the spec part is installed, Tasks checks that every
named [Module](../../glossary.json#concept.module) exists in the
[registry](../../glossary.json#concept.registry). Without the spec part, the Modules are plain
labels, written into the record and the binding. Only their form is checked: that of a Module
identity, which the binding requires.

Tasks then performs these steps:

- It creates branch `concorde/severity` from the primary worktree's commit (or `--base <ref>`).
- It adds a worktree at `.claude/worktrees/severity` inside the primary worktree, the only place a
  task worktree may be.
- It creates the task's folder `.concorde/tasks/severity/` in the primary worktree.
- It binds the worktree as a workspace.
- It writes the record.
- It writes the task's [trace node](../../glossary.json#concept.trace-node).
- It writes the log.
- It prints the record.

Git tracks the [worker configuration](../../glossary.json#concept.worker-configuration), so the task
carries the one of its base commit. Whatever the primary branch chooses later, the task's workers
keep the models chosen then. A change the task makes to its own copy merges with the task. The
worktree path must be ignored by Git in the primary worktree. Otherwise, the open is refused with
`worktree_not_ignored`. The installer adds `.claude/worktrees/` to `.gitignore`.

**The binding.** Binding the worktree is what makes it a place where the parts that work in a
workspace can work. Tasks
writes its [workspace binding](../../glossary.json#concept.workspace-binding),
`.concorde/workspace.json` at the worktree's root, as the
[binding contract](../../kernel/contracts.md#contract.kernel.workspace-binding) defines:

```json
{
  "schema_version": 2,
  "workspace": "severity",
  "root": "/home/dev/shop/.claude/worktrees/severity",
  "branch": "concorde/severity",
  "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
  "goal": "let Issue reports carry a severity",
  "modules": ["module.issues"],
  "traces": "/home/dev/shop/.concorde/tasks/severity/workspace",
  "concorde": "/home/dev/shop/.concorde"
}
```

The workspace is named after the task, so its workspace lock and its delivery commits are found by
the task identity. Its workspace folder is `workspace/` inside the task's own folder. Therefore,
every run of the task, started directly or by a workflow, lands in the task's
[trace](../../glossary.json#concept.trace), below the task's own node, and survives the worktree.
Its locks lie under the primary worktree's `.concorde/locks/`. Nothing that works in the workspace
learns that the folder belongs to a task. From then on, the task's work happens inside that worktree
with the worktree's own `concorde`. Every item started there reads the binding and works without
naming the task:

- Every Operation.
- Every execution command.
- Every workflow.

Each works on this task's:

- Goal.
- Modules.
- Branch.
- Base.

Tasks writes the binding once and never again. Closing removes the binding with the worktree. If the
file system refuses the binding, the open ends with `binding_failed` and records no task. The error
names the worktree and branch left behind and how to remove them.

**Resolving Issues.** Where the issues part is installed, a task that fixes recorded problems names
them. The task names them with `--resolves <id>,<id>` on `task open`, or later with
`concorde task resolve <task> <id>...`. The project MCP server presents the latter command as
`task_resolve`. Either command adds them to the record's `resolves`. Each must be an open Issue of
the project, read from the primary worktree. If any is not, the command is refused with
`invalid_issue`, naming each that is not. An ended task resolves nothing more (`task_closed`).
Naming an Issue changes neither it nor the work. The task still fixes the Issue by ordinary work.
Only its merge closes the Issue, as [Merging](#merging) says. Where the issues part is not
installed, `--resolves` and `task resolve` are refused with `part_missing`, naming the issues part.

## Listing and showing tasks

`concorde task list` prints the records of the current tasks and of the tasks in the history with
their derived state. The list is optionally filtered by `--state`: one or more derived states
separated by commas. It is also optionally filtered by `--main`: the main agent's session a record
names. Given both filters, the command lists the tasks that satisfy both.

`concorde task show <task-id>` prints what the task level needs to know about one task in one value:

- The record with its derived state.
- The workspace's [runs](../../glossary.json#concept.run), read from its workspace folder: those
  started directly and those of its workflow's steps.

For each run, the value gives these details:

- Its kind.
- Its name.
- Its Modules.
- Its status. While its runner lives, the status is `running`. When the runner died without a
  result, the status is `lost`.

The value also gives:

- Its [delivery commits](../../glossary.json#concept.delivery-commit), read from the task branch.
- Its task sessions, each with the main session it was started for.
- Its escalations, read from its trace.
- Who holds its workspace lock now.
- The paths of the decision log and of the task's folder.

A closed task is shown from the history the same way. `concorde trace show <task-id>` shows the
whole trace with its timing and cost.

The record's Modules are not kept in step with the task worktree's registry. When the task branch
removes or renames a Module, that Module stays in the record and in the binding. When a run's
definition checks its Modules against the worktree's registry, the run leaves out of it each bound
Module the worktree does not register, with evidence saying so. Tasks reads a registry only to open
a task, and only where the spec part is installed.

## Escalating

When it cannot handle an error itself, the session working on a task escalates with
`concorde task escalate`. The session names what it cannot handle:

- Runs of the task's workspace.
- Saved refusals.
- Earlier escalations.

The session states its own [error chain](../../glossary.json#concept.error-chain) link with:

- The code.
- What needs deciding.
- Why it cannot decide alone.
- What it tried.
- The options.
- The recommendation.

A task session escalates with `--by task-session` to the main agent. The main agent's own link, the
default, escalates to the developer. That link may name a task session's escalation as a cause with
`--escalation <n>`.

Tasks reads each named run's error from its run result. For a run of another workspace or an unbound
run, Tasks refuses with `unknown_run`. Tasks puts those errors unchanged under the session's link as
its causes. Tasks appends the resulting chain to the escalations of the task's trace node, numbered
from 1. Tasks also appends the chain to the decision log, rendered and as JSON. Tasks prints the
chain so the reader gets one chain from the question down to where the error started.

When what needs deciding is no failure but a decision the session may not keep alone, the session
names no error. It escalates its own link with no causes as the whole chain. One example is a
decision that a run that ended `ok` took without the developer.

## Reports and the main agent's session

A task session tells the main agent what it has to say with a Claude Code message to the main
agent's session. This is its delivery or the escalations it needs answered. That message is only as
good as the name it is sent to. A Claude Code session's name does not survive a restart or a resume
of the session. Because of this, a name frozen when the task session started may no longer reach
anyone. Its report would be lost, and nothing would wake the main agent to look for it. So Tasks
keeps the report and the name. The message is only the wake-up.

**The main agent's session.** The record's `main` names the main agent's session the task's task
sessions report to now. When `concorde task session --main` records a session, it sets that name.
Once its own session name changes, the main agent changes the recorded name with one command:

```text
concorde task rebind severity --main concorde-8e
```

The record keeps every name it had, so a later reader sees whom each report was sent to.
`concorde task list --main concorde-7d --state open,active,delivered,merging` lists the tasks not
ended whose record still names the former session. The main agent rebinds those tasks, since an
ended task has no task session left to report.

**Reports.** Before every message to the main agent, the task session records it:

```text
concorde task report severity --text "Delivered at 4be1c2d; decisions in the decision log." --escalation 2
```

Tasks appends the report to the task record, numbered from 1. The appended report includes the
escalations it carries and the main agent's session the record names at that moment.

Tasks appends the report to the decision log. Tasks prints the report with that session, the one the
task session then messages. A message that reaches nobody loses nothing: `concorde task show` lists
every report. The task session waits for a rebind with
`concorde task wait severity --rebound concorde-7d`. Once the main agent rebinds the task, that
command returns the new name. The main agent answers with a message too. It records its answer:

```text
concorde task answer severity --report 1 --text "Merging it now."
```

That command marks those reports answered in the record. It appends the answer to the decision log.
A report without an answer is unanswered. A main agent that lost its messages reads those reports
first. Once a task ends, nobody answers its reports, so the end answers the reports still unanswered
itself. The merge or close that ends the task gives each still unanswered report an answer in the
write that ends the task. The answer says how the task ended. The record attributes the answer to
that `merge` or `close` rather than to the main agent. The closing entry in the decision log names
those reports with that answer. Thus, the merge answers a delivery report the main agent acted on by
merging. No ended task leaves a report looking pending.

The reports live in the record rather than the trace because whether each is answered is state
the task commands act on. The name they were sent to is also such state. None of these touches
Git, so none of them is refused for an unfinished merge. A task session reports a
`merge_incomplete` refusal it met with `report`. A main agent may rebind its tasks before it
finishes the merge.

## Ending a task

A task ends in one of two states, and the record keeps the outcome:

- **closed** means the task was ended on purpose because it reached its goal. Merging is the usual
  way. The main agent merges a delivered task, unasked, with `concorde task merge`
  ([Merging](#merging)), which closes it with outcome `merged`.
  `concorde task close <task-id> --merged` closes a task merged some other way. It is accepted only
  when all these conditions hold:

  - The latest delivery commit of the workspace is the branch's head and verifies.
  - That head is in the primary branch.
  - The worktree is clean.

  Merging is not the only way to reach a goal. A task can close after it reached its goal through
  any of these activities:

  - It tried something out.
  - It investigated a question.
  - It only needed `understand`.

  Such a task closes with `--completed --note "<what it achieved>"`, outcome `completed`.
- **failed** means the task did not reach its goal. `--failed --reason "<why>"` records the reason.
  When an error caused the failure, it records the error chains too. `--run <run-id>` takes the
  error of a run of the task's workspace. `--error-file` takes a saved error. Each error stays
  unchanged. A failure no error caused, such as a wrong direction, is declared with `--no-error`.
  Either an error or that declaration is required, so whether an error caused the failure is never
  left unsaid.

Unless `--force` is given, closing without a merge refuses uncommitted changes. Closing does the
following:

- It answers every report still unanswered ([Reports](#reports-and-the-main-agents-session)).
- It appends the outcome, the note, any error chains and those answered reports to the decision log.
- It commits the log ([below](#decision-log-in-git)).
- It removes the worktree, and with it the workspace binding.
- It moves the task's whole folder to the history, `.concorde/history/<task-id>/`, keeping the
  branch.

No run of the task's workspace can start there any more. A closed or failed task stays so whatever
happens afterwards. A task closes only once it has really ended. While it moves the folder, the
close holds the task's workspace lock, so no run of the task is running and none can start. Before
waiting for the lock, a close with `--completed` or `--failed` first stops the task's task sessions.
Where the execution part is installed, that close also first stops the runs of the workspace that
still run. These include runs waiting in Execution's [lobby](../../execution/runner.md#the-lobby)
for its lock.

A run that waits for the lock meanwhile writes nothing into the task's folder. The run waits in the
lobby, outside the folder. When the run takes the lock after the close, Execution refuses the run
with `workspace_retired`, since the close removed the worktree with its binding and, while still
holding the lock, the lock file. The run's result therefore stays in the lobby, and the history
stays as the close left it.

A [workflow step](../../glossary.json#concept.workflow-step) of the workspace writes its records
under the task's workflow lock. The close, including the close that ends a merge, takes that lock
last, after the workspace and merge locks. The close holds the workflow lock from before it removes
the worktree until it has removed that lock's file. A step that holds the workflow lock first
finishes its writes, which move with the folder. A step that waits for the workflow lock is refused
with `workspace_retired` and writes nothing. Since a step never waits for another lock while holding
the workflow lock, the close waits for it only briefly.

Just before the folder moves, [Task sessions](../task-session/module.md#ending-claude-sessions)
copies each Claude Code task session's transcript into the session's node. Task sessions also
finishes the node with these values from Claude Code's records:

- The session's status.
- The session's end.
- The session's usage.

Once the task is closed, Task sessions removes those sessions from Claude's session list. The
close's `warnings` name what Task sessions could not keep or remove. This never fails the close. The
[history](../../glossary.json#concept.history) is never changed afterwards. Its retention removes
its conversation records after a while and may remove it whole.

<a id="decision-log-in-git"></a>

**The decision log in Git.** Every task that ends leaves its decision log on the primary branch at
`.concorde/decisions/<history key>.md`. The copy is the log as it stands once its closing is
appended, with the same bytes as the log the history keeps. A task merged with `concorde task merge`
carries the log in its merge commit ([Merging](#merging)). The log already contains the closing
`## Closed: merged, <time>` that the close appends once the checks pass, dated when the merge began.

A task closed any other way gets a commit of that file alone on the primary branch. This applies
when the task closes with any of these options:

- `--completed`.
- `--failed`.
- `--merged` after a merge made by hand.

The commit has the subject `concorde: keep the decision log of <task-id>` and the trailer
`Concorde-Task: <task-id>`. The close makes the commit after it appends the closing and under the
merge lock it holds. Other changes of the primary worktree, staged or not, stay as they were and are
not committed. When the primary branch already holds the log exactly as it ended, as after a merge,
the close commits nothing. When the log changed after the merge commit, the close gets that commit
of the file alone, replacing the merge commit's copy. An example is an entry the main agent added
before `--resume`.

On a detached `HEAD` or during an unfinished merge in the primary worktree, for example, Git refuses
that commit. When Git refuses that commit, the close refuses with `decision_log_uncommitted`, after
the record was closed and the log appended. The close leaves the folder current. The same close run
again commits the log and finishes. The log in Git is a copy: the task's folder keeps its own, and
nothing reads the copy back.

A worktree with checked-out submodules, such as the vendored references, is removed too. Removal
includes its submodules' checkouts and the repositories Git keeps for them under the worktree's own
administrative directory. Whatever the submodule's `ignore` setting, unless `--force` is given, a
change inside a submodule is refused as any other uncommitted change. The close never deinitializes
the submodules. Their registration lives in the repository's configuration, which every worktree
shares, and ending one task leaves that registration for the others.

## Delivering without Method

Where the method part is installed, a task session delivers its task with Method's `delivery`. The
delivery command validates the whole workspace before it makes the
[delivery commit](../../glossary.json#concept.delivery-commit). Where the method part is not
installed, Tasks delivers the task itself, from the task worktree:

```text
concorde task deliver severity --check "npm test" --check "npm run lint"
```

`task deliver` runs in the task's worktree, the one its binding names, and only there
(`not_task_worktree` elsewhere). It takes the task's
[workspace lock](../../glossary.json#concept.workspace-lock), waiting up to `--wait` seconds
(`workspace_busy` after). It refuses an ended task (`task_closed`) or a worktree whose head is not
on the task branch (`wrong_branch`). It runs each `--check` command in the worktree in order. At the
first check that fails, it refuses with `check_failed`, naming these details:

- The check.
- Its exit status.
- Its log.

With no check given, it runs none. When every check passes, it stages every change of the worktree
that Git does not ignore. It commits those changes with the subject `concorde: deliver <task-id>`
and the task's goal as body, by the Kernel's
[delivery commit convention](../../kernel/contracts.md#delivery-commit). Even when nothing is left
to commit, it commits as the mark of the delivery. When the head is already a delivery commit of the
workspace that verifies and the worktree is clean, it reports that head as delivered and commits
nothing. Its node is a `deliveries/<n>/` node of the task's trace, with each check a node below it.
The node references the commit it made or found. The task is then **delivered** like any other, and
the main agent merges it as usual.

`task deliver` judges nothing but its checks. The command does not judge any of these:

- [Spec](../../glossary.json#concept.spec) structure.
- Any [configured check](../../glossary.json#concept.configured-check).
- Scenario coverage.

These judgments are Method's. So the command exists only where the method part is not installed.
Wherever the method part is installed, `task deliver` refuses with `delivery_by_method`, naming
`concorde delivery`, so that a workspace Method could validate is never delivered without that
validation.

## Merging

Several main sessions may work in one project. Each delegates its tasks to task sessions that work
in the tasks' worktrees. Each merges from the primary worktree. Two merges at once would interleave
in the one primary checkout, so the main agent merges with one command:

```text
concorde task merge severity
```

Tasks first takes the task's [workspace lock](../../glossary.json#concept.workspace-lock). This
prevents any run of the task from committing on its branch or changing its worktree while Tasks
merges it. Tasks then takes the [merge lock](../../glossary.json#concept.merge-lock) of the primary
worktree. Tasks holds both locks to the end. Tasks waits for them inside its own process, up to
`--wait` seconds in all (default 300). If a `delivery` of the task is still finishing, Tasks waits
rather than refusing. If a run still holds the workspace lock after that time, Tasks refuses the
merge with `workspace_busy`, naming the run.

Before touching anything, Tasks refuses these cases:

- A task that could not be closed as merged apart from not being merged yet. Tasks reads the task's
  delivery commits from Git. The refusal codes are:

  - `not_merged`
  - `delivery_unverified`
  - `dirty_worktree`
- A primary worktree in any of these states (`primary_dirty`):

  - With uncommitted paths.
  - With untracked paths.
  - With a detached `HEAD`.

  Where the issues part is installed, Tasks first puts back there what Issue writes left
  ([below](#nothing-changed-outside-the-task)).
- Anything changed outside the task's worktree ([below](#nothing-changed-outside-the-task)).

Tasks merges the branch head those checks accepted, the task's latest delivery commit. Before
merging, Tasks records the task as **merging**, with:

- The primary branch's commit before the merge.
- The checked commit.
- The history key the task will close under.
- The checks Tasks will run.

Only then does Tasks run `git merge --no-ff --no-commit <checked commit>` there. Tasks never runs
`git merge` of the branch name, which could take a commit nobody checked. Tasks then adds the task's
decision log, followed by the closing its close will append, as
`.concorde/decisions/<history key>.md`. Tasks commits the merge with the trailer
`Concorde-Task: <task-id>`. The merge commit is therefore always a real merge, even where the
primary branch could fast-forward. Its second parent is the delivery commit. The merge commit
carries the log that explains it.

If Git refuses that commit, Tasks aborts the merge. On that refusal, Tasks also removes the log's
copy and refuses with `git_failed`. If a conflict occurs, Tasks aborts it and refuses with
`merge_conflict`, naming the paths. The conflict is resolved in the task worktree through these
steps:

- Merging the primary branch into the task branch.
- Validating again.
- Delivering again.

The conflict is never resolved in the primary worktree.

After the merge, Tasks records the merge commit. Tasks then runs the checks in the primary worktree.
Tasks runs exactly the `--check` commands given, such as a project that must build first. If no
commands are given and the spec part is installed, Tasks runs `concorde spec-validation` of the
merged checkout. If the spec part is not installed and no check is given, the merge runs no check.
Its answer says so. While a `concorde update` is not validated yet, and where the spec part is
installed, the merge also runs `concorde spec-validation` after the given checks. This ensures that
no checks let a merge pass that update's barrier.

If a check fails or checks leave uncommitted paths, Tasks returns the primary branch with
`git reset --keep` to the commit it had. In either case, Tasks refuses with `check_failed`, naming:

- The check.
- Its exit status.
- Its log in the merge attempt's node.
- Any paths the checks created, which the reset leaves in the primary worktree.

Every merge attempt is a node `merges/<n>/` of the task's trace, whether the attempt:

- Merged.
- Conflicted.
- Failed a check.
- Was undone.

Each check is a node below the attempt with its `output.log`.

When everything passed, Tasks closes the task as merged. After that close, where the issues part is
installed, Tasks closes each Issue the task resolves that is still open as `resolved`. Tasks still
holds the merge lock during these Issue closures. The closure's note says that the task fixed the
Issue. The closure uses the merge commit and task as evidence. Each closure is a commit of its own
on the primary branch after the merge. Tasks prints the record with:

- The Issues it closed (`resolved`).
- The commits before and after.
- Each check.
- How long Tasks waited.
- Its warnings, such as a decision log nobody wrote in or an Issue Tasks could not close.

If an Issue was closed meanwhile or the Issue store refused, Tasks cannot close it. This produces a
warning carrying the Issues error chain, never a refusal. The merge and the close stand, and the
main agent disposes that Issue itself. Even when a merge cannot reach the Issues at all, it warns
with `issues_unavailable`. The merge still ends the task's sessions and prints its result.

The merge's process imports Concorde's own modules from a snapshot of their sources taken when it
starts. Therefore, when a task changes Concorde itself, the steps after its merge never run a mix of
the old and the merged code. The merge's checks are processes of their own and run the merged code.
A merge thus ends with the task closed on a checked merge commit or delivered again on the commit
the primary branch had. After a conflict or a failed check, the task is delivered again.

<a id="nothing-changed-outside-the-task"></a>

**The merge audits what lies outside the task's worktree.** A
[task session](../../glossary.json#concept.task-session) changes nothing outside its task worktree.
Since its shell runs under no sandbox
([Task sessions](../task-session/module.md#the-session-boundary)), nothing but its guidance holds
the task session there. The merge is the gate into the primary branch. Therefore, before merging, it
looks outside the task's worktree at each place whose state no task working in it accounts for:

- The **primary worktree**, which must be clean. While tasks run, nothing changes there but
  Concorde's own records. These records are either paths Git does not version or records committed
  by the command that writes them. The unversioned paths are all ignored by the `.gitignore` the
  installer writes. They comprise:

  - The task folders.
  - Locks.
  - Runs.
  - History.
  - The [unbound runs](../../glossary.json#concept.unbound-run).

  An [Issue](../../glossary.json#concept.issue) record and a
  [decision log](../../glossary.json#concept.decision-log) are committed by the command that writes
  them. An Issue write killed between publishing its record and committing it leaves that record
  behind. Therefore, where the issues part is installed, the merge first runs the Issues' recovery.
  The merge holds the merge lock as every Issue write does. The recovery puts back such records and
  nothing else. If uncommitted or untracked paths remain after recovery, Tasks refuses the merge as
  `primary_dirty`. Its detail also says that a task changes nothing outside its worktree, since the
  paths may be a task's and not the developer's. The detail names each Issue record whose change the
  recovery left as no Issue write's, to be inspected and reverted. Alternatively, the detail names
  the recovery's own failure. Once the cause of that failure is fixed, `concorde issues recover`
  puts the records back.
- The **worktree of a task that has ended** and outlived it, which the close normally removes. No
  task will ever validate or deliver what is in it. Therefore, a change there refuses the merge as
  `changed_outside`, naming:

  - Each such worktree.
  - Its task.
  - Its paths.
- The **worktree of a task that has delivered and waits**, whose branch head is a
  [delivery commit](../../glossary.json#concept.delivery-commit) that verifies. A change there may
  be its own session's, which went on working after delivering, or another task's. The merge warns,
  naming the worktree and the paths. The merge does not refuse, since refusing would block a task
  that has nothing to do with the change.

Since nothing in the filesystem records who wrote a change, what the audit judges is bounded by what
the filesystem says. The worktree of a task that is still working is not judged at all, because its
own session changes it constantly. Nor is what is written there lost, since it becomes that task's
content. The content is judged by the task's own:

- Validation.
- Delivery.
- Merge.

Its merge refuses an uncommitted change as `dirty_worktree`. Thus, when another task writes a change
into a working task's worktree, the working task catches the change rather than the task that wrote
it.

Worktrees of no task, such as one a developer's own session made, are not the project's to judge.
The audit judges working trees and not commits. The primary branch legitimately moves while a task
runs, as:

- Other tasks merge.
- Issues are recorded.
- The developer commits.

Therefore, a commit there is no evidence of a task having overstepped. Nothing the audit names is
undone blindly. Each refusal and warning says what changed, for the main agent to find out what
wrote it.

The diagram shows the flow of one `concorde task merge` and where each way out leaves the primary
branch and the task. A task left `merging` is finished as the next passage explains:

```d2 illustrative
direction: down
locks: "Take the workspace lock, then the merge lock"
preflight: "Check the task, the primary worktree and what lies outside the task worktree"
record: "Record the task merging"
merge: "git merge the checked commit, add the decision log, commit"
checks: "Run the checks on the merge commit"
reset: "git reset --keep to the commit before"
close: "Close the task as merged"
busy: "workspace_busy or merge_busy: nothing changed"
refused: "A refusal such as not_merged, delivery_unverified, dirty_worktree, primary_dirty, changed_outside or merge_incomplete: nothing changed"
conflict: "merge_conflict: merge aborted, primary branch at its commit, task delivered"
failed: "check_failed: primary branch at its commit, task delivered, left paths named"
merged: "Task closed as merged on the checked merge commit"
unlogged: "decision_log_failed or record_unwritable after the record: task closed as merged, close --merged finishes"
unchecked: "Task left merging: task commands refused with merge_incomplete"
aborted: "Primary branch at the commit before, task delivered"
locks -> preflight: both held
locks -> busy: still held after --wait
preflight -> record: accepted
preflight -> refused
record -> merge
merge -> checks: merged
merge -> conflict: conflict
checks -> close: every check passed
checks -> reset: a check failed or left paths
reset -> failed
close -> merged
checks -> unchecked: the process ended
reset -> unchecked: rollback_failed
close -> unchecked: the record could not be closed
close -> unlogged: the decision log refused the closing
unchecked -> checks: "--resume, head still the merge commit"
unchecked -> aborted: --abort
```

**An interrupted merge.** If a merge's process ends before its checks decided, killed or crashed, it
leaves the task `merging`. The process may also leave an unchecked merge commit at the head of the
primary branch. The operating system releases the merge lock, so nothing but the record says that
the primary branch is not to be built on. Every task command that changes something therefore looks
for a `merging` task first. While no live process holds the merge lock, these commands, in any main
session and for any task, refuse with `merge_incomplete`:

- `open`
- `merge`
- `close`
- `session`
- `escalate`

The refusal names:

- The task.
- The commit before the merge.
- The merge commit.
- Where the primary branch is now.
- The two ways out.

`task list` and `task show` still answer, showing the task as `merging`. The main agent finishes the
merge with one of:

```text
concorde task merge severity --resume
concorde task merge severity --abort
```

When the primary branch's head is still the merge commit, `--resume` reruns the checks the merge
recorded on that commit. It then closes the task as merged or undoes the merge and refuses with
`check_failed` exactly as an uninterrupted merge does. With any other head, it refuses with
`not_resumable`. `--abort` aborts a `git merge` left in progress. When the primary branch's head is
the merge commit, it resets the branch to the commit before the merge. When the head already is that
commit before the merge, it leaves the branch alone. It returns the task to delivered. Both take the
merge lock and the workspace lock like a merge. When the primary worktree is on another branch or
its head is neither of those commits, both refuse with `merge_diverged`, touching nothing, since
Tasks never resets commits it did not make.

A merge that is still running is not interrupted. Since its process holds the merge lock, these
commands wait for it and answer `merge_busy`:

- `open`
- `merge`
- `close`

A `session` or `escalate` of the task being merged answers `merge_busy` at once. Those commands
for other tasks go ahead. A reset that Git refuses (`rollback_failed`) also leaves the task
`merging`. So does a close that fails after the checks passed. Their refusals say to `--abort`
or to `--resume` once the cause is fixed.

## Waiting for a task, a run or a lock

<a id="waiting"></a>

When a session wants to learn when something it did not start is over, the session asks once and is
woken. The session never polls:

```text
concorde task wait severity --until delivered
concorde task wait severity --rebound concorde-7d
concorde task wait --run r-20260929T101500-delivery-5f3a
concorde task wait --lock merge
concorde task wait severity --lock workspace
concorde task wait severity --merge
```

The options return at these points:

- `--until` returns once the task's derived state is one of the named states.
- `--rebound` returns once the task's record names a main agent's session other than the one given.
- `--run` returns once the run's runner holds no [run lock](../../glossary.json#concept.run-lock),
  with how the run ended.
- `--lock` returns once nobody holds the merge lock or the task's workspace lock, with who held it.
- `--merge` returns once no merge of the task runs, with its latest attempt's node and output files.

`--run` needs the execution part. Where that part is not installed, the wait is refused with
`part_missing` naming it. When the return condition already holds, each wait answers at once. Each
wait prints one JSON value. `--timeout` bounds the wait.

A task reaches these states only while its workspace lock is held, by a delivery run, a merge or a
close:

- `delivered`
- `closed`
- `failed`

The task keeps those states once the lock is released. For this reason, a task wait learns from the
operating system of every new holder of that lock. The wait blocks on the lock until that holder
lets it go, then reads the state again. Those three are the states the wait admits. When a task ends
in another state, the wait ends with `wait_unreachable`.

`merging` is not among them. A merge holds the lock from storing that state until it closes the task
or returns the task to delivered. For this reason, no wait would ever see that state. A wait for it
is refused, pointing to `--merge`.

A rebind wait learns from the operating system of every write of the task's record and of its folder
moving to the history. The wait reads the record again. When a task ended, the rebind wait ends with
`wait_unreachable`. A lock, run or merge wait blocks on the lock itself. For this reason, a holder
that dies wakes the wait as surely as one that ends.

For a session it can wake through a channel, the project MCP server's `register_wait` runs the same
waits. This command is their form for background Bash.

## Who runs the commands, and refusals

Only the main agent performs these actions, only from the primary worktree (`not_primary`
otherwise):

- Opens tasks.
- Merges tasks.
- Closes tasks.
- Starts task sessions.
- Rebinds tasks.
- Answers reports.

Once that check passed, `concorde task session` is dispatched to
[Task sessions](../task-session/module.md). Every session it starts is recorded here through the
record updates the [contracts](contracts.md#record-updates) list. Having no Git access, a
[worker](../../glossary.json#concept.worker) cannot run them.

Every refusal names its code, such as `task_exists`, `unknown_module`, `invalid_transition` or
`not_merged`. Every refusal states what was refused and why.

Apart from the few refusals that say what they left behind, every refusal changes nothing
([requirements](requirements.md#req.tasks.refusal-inert), [contracts](contracts.md)).

## Why it is built this way

Tasks is the workspace of the task level of Concorde's
[levels of work](../../module.md#the-levels-of-work) without being a level itself. The task session
to which the main agent delegates each task plays that level. The main agent manages the tasks and
merges them from the primary worktree. Tasks holds what the task level works in:

- The branch.
- The worktree.
- The record.
- The decision log.

Tasks itself never appears in a call chain. The main agent and Task sessions call into Tasks to read
or write that workspace. Tasks calls none of them back.

### Where a task lives

The task is the isolation unit because Git already isolates branches and worktrees. Changes stay in
their own checkout until Delivery commits and the main agent merges. For this reason, two tasks can
change the same Module at once. The tasks meet only at merge time, where Git reports conflicts. A
shared checkout would instead leak one task's half-finished edits into another's checks.

Task worktrees live under `.claude/worktrees/` of the primary worktree, at
`.claude/worktrees/<task-id>` and nowhere else, for these reasons:

- Claude Code keeps a session's worktrees there.
- A task session is a Claude Code session started in its task worktree.
- Every worktree Concorde's workers work in lives there.

Git ignores the directory there, so a task's checkout never appears as files of the primary branch.
The Workers' [deny rules](../../glossary.json#concept.deny-rules) still hide the primary worktree's
other files and the other task worktrees from a worker. This is because those are siblings of the
path to the worker's own worktree.

Task folders live in the primary worktree, not the task worktrees. The main agent works there and
must see every task in one place, including ones whose worktree is gone. A task worktree is exactly
what workers and Delivery commit, so records kept there would be swept into commits.

For these reasons, `.concorde/tasks/` and `.concorde/history/` are local, Git-ignored state. What
travels with the code is the [delivery commit](../../glossary.json#concept.delivery-commit) and,
once the task ended, its decision log. Tasks commits that log to the primary branch. Any process
finds the primary worktree through Git's common directory.

There is one folder per task, organized by the task's lifecycle as the
[history](../../glossary.json#concept.history) explains. The folder has the shape
[Tracing](../../kernel/tracing/module.md) gives every trace node. This organization means these
items are read in one place and ended in one move:

- The task's record.
- The task's log.
- The task's sessions.
- The task's runs.

The record stays small because the task's history is its trace, which only grows by new nodes.

### Locks

Several processes may change a task at once, such as a task session escalating while the main agent
closes the task. For this reason, every change of a task's record or trace is made while holding the
task's lock, `locks/tasks/<task-id>.lock`. Every record write is one
[file transaction](../../glossary.json#concept.file-transaction) bound to the digest it replaces.
When a change precedes the transaction's digest check, the check detects the change. Tasks then
rereads the record and reapplies the change if the preconditions still hold. After three attempts,
Tasks refuses with `record_conflict`.

A change between that check and the write is not detected, as the Kernel's
[file transactions](../../kernel/contracts.md#file-transactions) leave it to their callers to
exclude. The task's lock excludes that change because every writer of the record holds the lock.
Each task has its own lock and folder, so tasks never contend. Every lock lies under
`.concorde/locks/`, apart from the folders it protects. This is because a close must hold the task's
workspace lock precisely while it moves the task's folder.

The process doing the merge holds the merge lock. The merge lock has no recorded owner for others to
wait on and who must wake them. A recorded owner would leave every waiter stuck in these cases:

- The owner crashed.
- The owner was closed.
- The owner forgot to notify.

The sessions that merge also share no channel that would reliably notify each other. Whatever
happens to its holder, an operating-system `flock` is released and wakes waiters, the same way for
every kind of session. It only works if the whole critical section runs in one process. For this
reason, one command performs these actions instead of steps the main agent issues one by one:

- Merging.
- Checking.
- Undoing.
- Closing.

This is also why conflicts are resolved in the task worktree. The lock is then held for the seconds
a merge and its checks take, not for however long a resolution takes. Holding the lock also for
`open` and `close` keeps both from reading a primary branch whose merge might still be reset. Every
write of the project's Issues, which [Issues](../../issues/module.md) commits on the primary branch,
takes the lock too. For this reason, no Issue commit lands between a merge commit and its checks.

The lock alone cannot cover a merge whose process dies. The operating system releases the lock at
once, and the next command would build on a merge commit no check accepted. For this reason, the
merge writes `merging` into the record before `git merge` runs. The other commands read that stored
state, not the lock. Together, the state and lock distinguish a merge that still runs from one that
was interrupted. The lock is held for the former, not the latter.

The recovery is left to the main agent rather than done by the next command that notices, for these
reasons:

- Checking again and undoing are both legitimate.
- The next command may belong to another main session with another task in mind.

Merging the checked commit by its identity and holding the task's workspace lock while merging or
closing keep the commit merged the one the checks accepted. A run of the task, such as a delivery
started in the task worktree, cannot move the branch between the checks and the merge. The run also
cannot write a worktree being removed.

The workspace lock is taken before the merge lock and waited for without the merge lock. This
ensures that waiting for one task's run never holds up the merges of other tasks. `merge` and
`close` are the only commands that take both, always in that order, so none waits on another in a
cycle. The waits happen inside the command because its callers are agents. A refusal they must
retry would have them poll, paying for every look. A blocked command costs nothing until it
returns.

### Why the decision log goes to Git

Of everything a task leaves, the decision log is what a later reader of the code needs. The log
holds a few kilobytes per task:

- The decisions taken without the developer.
- The escalations and their answers.
- The results that were not `ok` with their error chains.

The rest of a task's folder, above all the transcripts of its sessions and workers, is large and
local. Retention removes it. So when the task ends, the log is committed, and nothing else of the
folder is.

Tasks commits the log, not Delivery, for these reasons:

- Delivery works in the workspace and knows no task.
- The log lives in the task's folder of the primary worktree.
- The log belongs to the task level.

A merged task carries its log in its merge commit, so that Git itself relates the two. The commit
that brings the delivery into the primary branch adds the log that explains the delivery. That
commit's second parent is the delivery commit. When a failed check undoes a merge, the merge takes
its log with it. That is why a merge always makes a merge commit. A task that ends without a merge
has no such commit, so its log gets one of its own. Every ended task is thus in Git, completed and
failed ones too.

The log's file is named by the history key rather than the task's name for these reasons:

- Once its branch is deleted, a task name can be used again.
- By then, retention may have removed the earlier task's history folder while its log stays in Git.

For those same reasons, a key is free only when neither the history nor the committed logs hold it.
The merge records the key it chose in the `merging` record, so that `--resume` closes the task under
the key its merge commit already used.

The copy in Git equals the log as the task ended, closing included, rather than the log as it stood
at the merge. This keeps the history and Git from disagreeing once retention removes the history.
Only once the checks pass, after the merge commit, is the closing appended. Yet amending that commit
would change the commit the checks examined. A commit of the log after every merge would double the
commits a merge makes. So the merge commit's copy carries the closing in advance. The closing is
dated by the start the `merging` record keeps. The close appends that same closing. When a failed
check undoes a merge, the merge takes the copy with it and leaves the log without a closing. Only a
log changed between the merge commit and the close needs a commit of its own. An interrupted merge
allows such a change.

### Why the state is derived

If a task's record held the following, the execution core would have to know tasks:

- The task's runs.
- The task's deliveries.
- The task's workflows.

Under that condition, every fact would exist twice, in the record and in the run store or Git. Each
of these cases would leave the two copies disagreeing, and something would have to recover the
record:

- A runner killed between its result and the record update.
- A delivery commit whose record update failed.
- A run started by hand in the worktree.

So the record holds only the facts the task level alone knows:

- Why the task exists.
- What it may touch.
- Who escalated or reported what.
- Which sessions work it.
- Whom they report to.
- How it ended.

Each time Tasks needs facts about what happened in the worktree, Tasks reads them where they were
recorded. When its workspace has a run or a change, a task is active. A task is delivered when all
these conditions hold:

- Git shows a delivery commit of the task's workspace at the branch head.
- Nothing follows that commit.
- That commit has exactly one parent.

Only then is the task mergeable. The subject is a mark, not a proof. Only the task level and the
delivering command commit on the branch. The task level has no reason to forge the mark. The
one-parent check keeps a merge that happens to carry the subject, such as one resolving a conflict,
from counting. With no second copy, there is nothing to recover and nothing that can disagree.

Whenever a task is listed or shown, deriving costs these reads:

- A scan of the workspace folder.
- A `git log` of the task branch.
- A Git read to verify the branch head.

This cost is small next to what a run costs. Deriving holds however a run ended. When a run's runner
died, the run is `lost` in the listing, and the operating system already released its workspace
lock. See the [requirements](requirements.md) and [scenarios](scenarios.md).

## The task store

<a id="realization.tasks.store"></a>

The **[Task](../../glossary.json#concept.task) store** realization holds:

- The `concorde task` commands (`cli.py`).
- The following (`store.py`):
  - The records.
  - The derived state.
  - The binding written at open.
  - The record updates task sessions call.
  - The reports.
  - The main agent's session.
- The merge under the merge lock (`merge.py`).
- `task deliver` (`deliver.py`).
- The checks both the merge and delivery run (`checks.py`).
- The waits (`wait.py`).
- The reach into the parts Tasks does not depend on, through their commands and formats (`parts.py`,
  and `runs.py` for Execution's runs).
- Their tests.

The tests run on real Git repositories with delivery commits and run store entries written the way
Execution writes them. The tests also run with projects whose own `concorde` lacks some parts. The
realization is the only writer of task records. At open, the realization writes each decision log
once. The realization appends only these entries:

- Escalations.
- Reports.
- Answers.
- Closings.

When the task ends, the realization commits a copy of the decision log. The command dispatches
`concorde task session` to the code of Task sessions.

## Providers

<a id="uses-kernel"></a>

The **Kernel** gives Tasks every contract it cannot do without. Tasks writes the
[workspace binding](../../glossary.json#concept.workspace-binding) as the
[binding contract](../../kernel/contracts.md#contract.kernel.workspace-binding) requires. Tasks
relies on whatever works in the workspace doing the following:

- Only reading the binding.
- Working on what the binding names:

  - The Modules.
  - The branch.
  - The base.
- Recording its runs in the workspace folder the binding names.
- Holding the [workspace lock](../../glossary.json#concept.workspace-lock) for every run.

Tasks holds the same lock during each of these actions:

- Merging the task.
- Closing the task.
- Delivering the task.

This lets Tasks know nothing of the workspace is changing the branch or worktree meanwhile. Tasks
recognizes the task's deliveries by the
[delivery commit](../../glossary.json#concept.delivery-commit) convention. These are the commits of
the task's workspace on the task branch since its base commit, whatever part made them. Tasks
recognizes them for these purposes:

- To derive `delivered`.
- To list deliveries in `task show`.
- To decide whether a task may be merged or closed as merged.

A task branch with no delivery commit is refused with `not_merged`. A head that does not verify,
having another number of parents than one, is refused with `delivery_unverified`, naming the
mismatch. Tasks takes the [merge lock](../../glossary.json#concept.merge-lock), the lock every Issue
write takes too, for these actions:

- Opening.
- Merging.
- Closing.

Tasks writes every record as a [file transaction](../../glossary.json#concept.file-transaction),
complete or absent and bound to the bytes it replaces.

<a id="uses-tracing"></a>

**Tracing**, the Kernel's child, gives the shape of a
[trace node](../../glossary.json#concept.trace-node) to each of the following:

- The task.
- Each session.
- Each merge attempt.
- Each delivery.
- Their checks.

Tracing also gives Tasks the locks under `.concorde/locks/` and the error contract. Tasks writes
those nodes through Tracing's library. Tasks registers the current task folders and the
[history](../../glossary.json#concept.history) as trace roots with the history's retention. At the
start of every `task open` and `task close`, Tasks runs Tracing's retention. Tasks reports in the
error contract. Tasks relies on:

- The [layout](../../kernel/tracing/contracts.md#layout).
- The [locks](../../kernel/tracing/contracts.md#locks).
- The [node contract](../../kernel/tracing/contracts.md#contract.tracing.node).

<a id="uses-task-session"></a>

When `concorde task session` hands it a task that passed Tasks' checks, **Task sessions** starts
[task sessions](../../glossary.json#concept.task-session). Tasks relies on Task sessions recording
sessions only through the record updates. Tasks prints Task sessions' refusals in the shape of every
`concorde task` refusal. A close relies on Task sessions to do the following:

- Before a close without a merge, stop the task's task sessions.
- Before the folder moves, keep their transcripts in their nodes.
- Before the folder moves, finish those nodes.
- Afterwards, remove them from Claude's session list.

For what Task sessions could not keep or remove, Task sessions returns a warning, never a refusal.

<a id="uses-distribution"></a>

**Distribution**, present in every installation, installs and updates Concorde in the project. After
an update, Distribution marks Concorde unvalidated until a validation passes. Tasks relies on that
mark, `.concorde/update.json` of the primary worktree, to tell that a merge must also run
`concorde spec-validation` where the spec part is installed. Whatever checks the merge was given,
this applies so that nothing merges before an update is validated. Tasks also keeps the coordination
part's [part registration](../../glossary.json#concept.part-registration),
`src/concorde/coordination/registration.json`, from which Distribution installs the part. Tasks
relies on the registration meeting Distribution's
[registration contract](../../distribution/contracts.md#contract.distribution.part-registration).

<a id="uses-execution"></a>

**Execution** is an [optional integration](../../glossary.json#concept.optional-integration). Where
the execution part is installed, Tasks reads a run's
[result](../../glossary.json#concept.run-result) for:

- Its status.
- Its Modules.
- Its error chain.

While the run runs, Tasks reads the run's
[run progress file](../../glossary.json#concept.run-progress-file) and
[run lock](../../glossary.json#concept.run-lock). The runner's liveness tells a `running` run from a
`lost` one. Tasks never writes either. Tasks reads the runs of a task's workspace in the
[run store](../../glossary.json#concept.run-store) of its workspace folder and in the lobby for
these purposes:

- To derive `active`.
- To list them in `task show`.
- To stop them when a task closes.
- To wait for one.

A run that is neither finished nor alive is shown as `lost` rather than trusted as running. Where
the part is not installed, no run exists:

- The workspace folder holds none.
- A task is never active through a run.
- A close stops none.
- `task wait --run` is refused with `part_missing`.

<a id="uses-delivery"></a>

**Delivery**, Method's, is an optional integration. Where the method part is installed, Delivery
makes the delivery commits of a task's workspace after validating it whole. Tasks relies on Delivery
verifying a delivered head before Delivery reports one, as Tasks itself does
([req.delivery.recovered-verified](../../method/delivery/requirements.md#req.delivery.recovered-verified)).
Tasks also relies on Delivery's presence to refuse `task deliver`. Tasks learns of that presence
from whether the task worktree's own `concorde` offers `delivery`
([how](contracts.md#parts-not-depended-on)). Where the method part is not installed, Tasks delivers
with `task deliver`.

<a id="uses-issues"></a>

**Issues** is an optional integration. Where the issues part is installed, Issues keeps the
project's [Issues](../../glossary.json#concept.issue) in the primary worktree. Tasks relies on
Issues' bookkeeping command, `concorde issues`, for these actions:

- Show whether each Issue a task names as resolving exists and is open.
- Before a merge judges the primary worktree clean, put back what Issue writes left uncommitted
  there.
- Close those Issues after the merge.

The last two actions serve a caller that holds the merge lock and hands it on to the command. Each
action answers or refuses with its own error link, which Tasks passes on in a warning. Where the
issues part is not installed, the command's refusal of `issues` tells this
([how](contracts.md#parts-not-depended-on)). In that case:

- A task names no Issue (`part_missing`).
- A merge closes none.
- A merge has no Issue records to put back.

<a id="uses-spec"></a>

**Spec core** is an optional integration. The existence of its registry mirror
`.concorde/specs.json` tells whether the spec part is installed. Where the spec part is installed,
Tasks reads the primary worktree's registry through that mirror's format to open a task, since
its worktree does not exist yet. Thus a record never names a Module that does not exist at open.
If the mirror cannot be read, the open is refused (`specs_unloadable`) and nothing is written. A
merge also runs Spec core's `concorde spec-validation` as the default check and after an
unvalidated update. Where the spec part is not installed, a task's Modules are plain labels, still
in the form of a Module identity, which the workspace binding requires. In that case, a merge
runs only the checks it is given.
