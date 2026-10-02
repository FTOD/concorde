# Tasks

## Purpose

Tasks manages the workspace of the task level: it gives every unit of work the
[main agent](../../glossary.json#concept.main-agent) starts its own place, a Git branch, a worktree
checked out on it and bound as an [Execution](../../execution/module.md) workspace, a
[task record](../../glossary.json#concept.task-record) and a
[decision log](../../glossary.json#concept.decision-log), kept with the task's
[trace](../../glossary.json#concept.trace) in one folder of its own that moves to the
[history](../../glossary.json#concept.history) when the task ends. The main agent, and the task
session it delegates every task to, rely on it to run pieces of work side by side without their
changes mixing, to know each task's state, and to keep the reasons behind choices made without the
developer. Tasks binds each task worktree when it opens the task and learns what happened in it only
from what Execution recorded, the workspace's runs and its delivery commits; nothing below the task
level reads or writes a task record. When the main agent merges a delivered task, Tasks does the
merge into the primary branch under a lock, so several main sessions never merge at once, and undoes
it if the checks that follow fail; it records the merge in the task until the checks decided, so a
merge interrupted halfway stops every task command that would build on it until it is resumed or
aborted. When a task ends, merged or not, Tasks commits its decision log to the primary branch, so
the reasons behind its choices travel with the code after the local records are gone. A task may name
the [Issues](../../glossary.json#concept.issue) it resolves, which its merge closes once the fix is on
the primary branch.

Tasks is independent of the sessions that work in its tasks: it does not start or follow them,
which [Task sessions](../task-session/module.md) does, and it does not decide how work is split,
which tasks run in parallel or when a task is merged. It never runs an
[Operation](../../glossary.json#concept.operation) or an
[execution command](../../glossary.json#concept.execution-command), never commits on a task branch,
and never interprets the decision log, which it only copies into Git.

## Core concepts

<a id="concept.task"></a>

A **[task](../../glossary.json#concept.task)** is one unit of the main agent's work, which it opens
for each piece of work it wants isolated: a branch `concorde/<task-id>`, a worktree checked out on
it and bound as the [workspace](../../glossary.json#concept.workspace) named after the task, and a
folder of its own in the primary worktree. Parallelism exists only between tasks: none share a
worktree, and Execution's [workspace lock](../../glossary.json#concept.workspace-lock) lets each
workspace run one thing at a time. A task's goal and Modules are those named at open and never
change; a run that names further Modules with `--modules` records them in its own
[run result](../../glossary.json#concept.run-result).

<a id="concept.task-record"></a>

Everything about a current task lives in its folder `.concorde/tasks/<task-id>/` of the primary
worktree: its record `task.json`, its trace node `trace.json`, its decision log `decisions.md`, the
boundary configuration of its task session under `runtime/`, the nodes of its task sessions under
`sessions/` and of its merge attempts under `merges/`, and the workspace folder `workspace/` that
Execution fills. **The [task record](../../glossary.json#concept.task-record)** holds only what the
task commands need to act on the task: identity, goal, Modules, branch, worktree path, base commit,
the [main agent](../../glossary.json#concept.main-agent)'s session its task sessions report to now
with the ones it named before, the reports task sessions made to it with its answers,
stored state, the merge in progress and, once the task ended, how it ended
([exact fields](contracts.md#contract.tasks.record)). Its history is in its trace instead: the
task's node records when it was opened, every change of its stored state, every escalation and how
it ended; each task session is a node below it, and so is each merge attempt with its checks
([exact content](contracts.md#task-trace)). Neither keeps runs, deliveries or workflow: those are
recorded by Execution, and a copy could disagree with them after a crash or a run nobody announced.

<a id="concept.decision-log"></a>

**The [decision log](../../glossary.json#concept.decision-log)** lives at
`.concorde/tasks/<task-id>/decisions.md`. Tasks creates it with a heading and the goal at open, then
only appends escalations, reports and their answers, and how the task ended; the main agent appends
the task's brief before it starts the task's task session, and that session, working on the task,
appends directly: every uncertainty it decided
alone, with options and reason, every non-`ok` run result and what it did about it, and the
decisions and problems of a workflow's report, which Workflows saves beside its own record and never
writes here. `concorde task open` prints the log's path beside the new record, and `concorde task
merge` warns when the log still holds only its heading and goal, since a task worked without writing
it has lost the record of every decision taken alone. The main agent reads the log when it reports
to the developer at the end of the task. When the task ends, the log is committed to the primary
branch as `.concorde/decisions/<history key>.md` ([below](#decision-log-in-git)), the one record of
a task that Git keeps. The log is free Markdown, since its readers are the main agent and the
developer; Tasks gives it only a fixed place and lifetime.

<a id="concept.merge-lock"></a>

**The [merge lock](../../glossary.json#concept.merge-lock)** of the primary worktree keeps merges
from interleaving in the one primary checkout. It is a `flock` held by the command's own process,
so no session has to release it or announce that it is done: the kernel releases it when the
process ends, even when it is killed, and a waiting command wakes as soon as it is free. A command
that gives up waiting fails with `merge_busy`, naming the holder's command, task, process, start
time and Claude Code session, which the holder writes into the lock file while it holds it. The
command may also have been handed both locks by the process that started it, as the
[project MCP server](../../glossary.json#concept.project-mcp-server) hands them to the merge it
starts: it then holds them from its start without waiting, exactly as long as it runs.
`concorde task open` and `concorde task close` take the same lock, so a task is never based on, or
closed against, a merge that may still be undone; `close` takes the task's workspace lock before
it, as `merge` does, waiting up to its own `--wait` and then refusing with `workspace_busy` while a
run of the task could still write the worktree it removes.

A task's **state** is partly stored and partly derived. Only merging and closing a task change its
stored state; whether an open task is still open, active or delivered is derived each time the task
is listed or shown from what Execution recorded and from Git ([Task state](#task-state)).

## Overview

### What a task is made of

The task store writes the record, creates the decision log and commits a copy of it, and holds the
merge lock while it merges, opens or closes a task. Record, log and state fit together this way:

```d2
tasks: Tasks {
  store: Task store {
    "src/concorde/tasks/cli.py"
    "src/concorde/tasks/store.py"
    "src/concorde/tasks/merge.py"
  }
  record: Task record
  log: Decision log
  task: Task
  lock: Merge lock
  store -> record: writes
  store -> log: creates, commits a copy of
  store -> lock: holds while merging, opening or closing
  record -> task: describes
  log -> task: explains the choices of
}
```

### Task state

The record says `open` from the open until the task ends, then `closed` or `failed`, and
**merging** while `concorde task merge` has put, or is about to put, a merge of the task into the
primary branch that its checks have not decided yet. Whether an open task is still **open**,
**active** or **delivered** is derived each time the task is listed or shown:

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

A task is **delivered** when its branch head is a delivery commit of its workspace that verifies,
having exactly one parent as every commit Delivery creates has, and its worktree is clean;
**active** when its workspace has a run in the [run store](../../glossary.json#concept.run-store),
running or finished, or its branch moved past the base commit, or its worktree has uncommitted
changes; and **open** before any of these. A run that changes nothing, such as a review after
delivery, leaves a delivered task delivered; a change after the delivery commit, committed or not,
makes it active until the next delivery. A new path Git cannot version, neither a file, a symbolic
link nor a directory, such as one a sandbox hides behind a `/dev/null` mount, is no change of the
worktree, as Delivery leaves it out of what it commits; a change inside a submodule is one, since
removing the worktree would lose it. A head that carries the subject of a delivery commit but does
not verify leaves the task active: `task show` lists it among the deliveries with its mismatches,
and it is never merged ([Merging](#merging)). A task ends in one of two states, closed or failed,
and the record keeps the outcome ([Ending a task](#ending-a-task)).

### Around it

Tasks writes one thing into Execution, the binding, and reads the rest from what Execution and
Delivery recorded:

```d2
store: Task store
binding: Execution / Workspace binding
runstore: Execution / Run store
lock: Execution / Workspace lock
commits: Delivery / Delivery commit
store -> binding: writes when a task opens
store -> runstore: reads the workspace's runs from
store -> lock: holds while merging or closing, shows the holder of
store -> commits: reads from the task branch and verifies
```

## Opening a task

The main agent opens a task for each piece of work it wants isolated, e.g. "let
[Issue reports](../../glossary.json#concept.issue-report) carry a severity" bound to
`module.issues`, from the primary worktree:

```text
concorde task open severity --goal "let Issue reports carry a severity" --modules module.issues
```

Tasks checks the identity is new and every named [Module](../../glossary.json#concept.module) exists
in the [registry](../../glossary.json#concept.registry), creates branch `concorde/severity` from the
primary worktree's commit (or `--base <ref>`), adds a worktree at `.claude/worktrees/severity`
inside the primary worktree, the only place a task worktree may be, creates the task's folder
`.concorde/tasks/severity/` in the primary worktree, binds the worktree as a workspace, writes the
record, the task's [trace node](../../glossary.json#concept.trace-node) and the log, and prints the
record. The [worker configuration](../../glossary.json#concept.worker-configuration) is tracked by
Git, so the task carries the one of its base commit: its workers keep the models chosen then,
whatever the primary branch chooses later, and a change the task makes to its own copy merges with
the task. The worktree path must be ignored by Git in the primary worktree, or the open is refused
with `worktree_not_ignored`; the installer adds `.claude/worktrees/` to `.gitignore`.

**The binding.** Binding the worktree is what makes it a place where Execution can work. Tasks
writes its [workspace binding](../../glossary.json#concept.workspace-binding),
`.concorde/workspace.json` at the worktree's root, as the
[binding contract](../../execution/contracts.md#contract.execution.workspace-binding) defines:

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
the task identity. Its workspace folder is `workspace/` inside the task's own folder, so every run
of the task, started directly or by a workflow, lands in the task's
[trace](../../glossary.json#concept.trace), below the task's own node, and survives the worktree;
its locks lie under the primary worktree's `.concorde/locks/`. Execution never learns that the
folder belongs to a task. From then on the task's work happens inside that worktree with the
worktree's own `concorde`: every Operation, execution command and workflow started there reads the
binding and works on this task's goal, Modules, branch and base without naming the task. Tasks
writes the binding once and never again; closing removes it with the worktree. A binding the file
system refuses ends the open with `binding_failed`, naming the worktree and branch left behind and
how to remove them, and records no task.

**Resolving Issues.** A task that fixes recorded problems names them: `--resolves <id>,<id>` on
`task open`, or later `concorde task resolve <task> <id>...`, which the project MCP server presents as
`task_resolve`, adds them to the record's `resolves`. Each must be an open Issue of the project,
read from the primary worktree, or the command is refused with `invalid_issue`, naming each that is
not; an ended task resolves nothing more (`task_closed`). Naming an Issue changes neither it nor the
work: the task still fixes it by ordinary work, and only its merge closes it, as
[Merging](#merging) says.

## Listing and showing tasks

`concorde task list` prints the records of the current tasks and of the tasks in the history with
their derived state, optionally filtered by `--state`, one or more derived states separated by
commas, and by `--main`, the main agent's session a record names; given both, it lists the tasks
that satisfy both. `concorde task show <task-id>` prints what the task level needs to know about one
task in one value: the record with its derived state, the
workspace's [runs](../../glossary.json#concept.run) read from its workspace folder, those started
directly and those of its workflow's steps (each with its kind, name, Modules and status, `running`
while its runner lives and `lost` when the runner died without a result), its
[delivery commits](../../glossary.json#concept.delivery-commit) read from the task branch, its task
sessions, each with the main session it was started for, and its escalations read from its trace,
who holds its workspace lock now, and the paths of the decision log and of the task's folder. A
closed task is shown from the history the same way. `concorde trace show <task-id>` shows the whole trace
with its timing and cost.

The record's Modules are not kept in step with the task worktree's registry: a Module the task
branch removes or renames stays in the record and in the binding, and Execution leaves each bound
Module the worktree does not register out of a run, with evidence saying so. Tasks reads a registry
only to open a task.

## Escalating

When it cannot handle an error itself, the session working on a task escalates with
`concorde task escalate`, naming the runs of the task's workspace, saved refusals or earlier
escalations it cannot handle and stating its own
[error chain](../../glossary.json#concept.error-chain) link: code, what needs deciding, why not
alone, what it tried, options and recommendation. A task session escalates with
`--by task-session` to the main agent; the main agent's own link, the default, escalates to the
developer and may name a task session's escalation as a cause with `--escalation <n>`. Tasks reads
each named run's error from its run result, refusing a run of another workspace or an unbound one
with `unknown_run`, puts those errors unchanged under that link as its causes, appends the resulting
chain to the escalations of the task's trace node, numbered from 1, and to the decision log
(rendered and as JSON), and prints it, so the reader gets one chain from the question down to where
the error started. A session that names no error, because what needs deciding is no failure but a
decision it may not keep alone, such as one a run that ended `ok` took without the developer,
escalates its own link with no causes as the whole chain.

## Reports and the main agent's session

A task session tells the main agent what it has to say, its delivery or the escalations it needs
answered, with a Claude Code message to the main agent's session, and that message is only as good
as the name it is sent to. A Claude Code session's name does not survive a restart or a resume of
the session, so a name frozen when the task session started may no longer reach anyone: its report
would be lost, and nothing would wake the main agent to look for it. So Tasks keeps the report and
the name, and the message is only the wake-up.

**The main agent's session.** The record's `main` names the main agent's session the task's task
sessions report to now. `concorde task session --main` sets it when it records a session, and the
main agent changes it with one command once its own session name changed:

```text
concorde task rebind severity --main concorde-8e
```

The record keeps every name it had, so a later reader sees whom each report was sent to.
`concorde task list --main concorde-7d --state open,active,delivered,merging` lists the tasks not
ended whose record still names the former session: those the main agent rebinds, since an ended
task has no task session left to report.

**Reports.** Before every message to the main agent, the task session records it:

```text
concorde task report severity --text "Delivered at 4be1c2d; decisions in the decision log." --escalation 2
```

Tasks appends the report to the task record, numbered from 1, with the escalations it carries and
the main agent's session the record names at that moment, appends it to the decision log, and
prints it with that session, the one the task session then messages. A message that reaches nobody
loses nothing: `concorde task show` lists every report, and the task session waits for a rebind
with `concorde task wait severity --rebound concorde-7d`, which returns the new name once the main
agent has rebound the task. The main agent answers with a message too, and records its answer:

```text
concorde task answer severity --report 1 --text "Merging it now."
```

which marks those reports answered in the record and appends the answer to the decision log. A
report without an answer is unanswered, which is what a main agent that lost its messages reads
first. Nobody answers a report once its task has ended, so the end answers the reports still
unanswered itself: the merge or close that ends the task gives each of them, in the write that
ends it, an answer saying how the task ended, recorded as given by that `merge` or `close` rather
than by the main agent, and its closing entry in the decision log names them with that answer. A
delivery report the main agent acted on by merging is thus answered by the merge, and no ended
task leaves a report looking pending. The reports live in the record rather than the trace because whether each is answered is
state the task commands act on, like the name they were sent to. None of these touches Git, so
none of them is refused for an unfinished merge: a task session reports a `merge_incomplete`
refusal it met with `report`, and a main agent may rebind its tasks before it finishes the merge.

## Ending a task

A task ends in one of two states, and the record keeps the outcome:

- **closed** means the task was ended on purpose because it reached its goal. Merging is the usual
  way: the main agent merges a delivered task, unasked, with `concorde task merge`
  ([Merging](#merging)), which closes it with outcome `merged`.
  `concorde task close <task-id> --merged` closes a task merged some other way, and is accepted
  only when the latest delivery commit of the workspace is the branch's head and verifies, that
  head is in the primary branch, and the worktree is clean. Merging is not the only way to reach a
  goal: a task that tried something out, investigated a question or only needed `understand`
  closes with `--completed --note "<what it achieved>"`, outcome `completed`.
- **failed** means the task did not reach its goal. `--failed --reason "<why>"` records the reason,
  and when an error caused the failure, the error chains too: `--run <run-id>` takes the error of a
  run of the task's workspace and `--error-file` a saved one, each unchanged. A failure no error
  caused, such as a wrong direction, is declared with `--no-error`; one of the two is required, so
  whether an error caused the failure is never left unsaid.

Closing without a merge refuses uncommitted changes unless `--force`. Closing answers every report
still unanswered ([Reports](#reports-and-the-main-agents-session)), appends the outcome, the note,
any error chains and those answered reports to the decision log, commits the log ([below](#decision-log-in-git)),
removes the worktree, and with it the workspace binding, and moves the task's whole folder to the
history, `.concorde/history/<task-id>/`, keeping the branch; no run of the task's workspace can
start there any more, and a closed or failed task stays so whatever happens afterwards. A task
closes only once it has really ended: the close holds the task's workspace lock, so no run of it is
running and none can start, while it moves the folder, and a close with `--completed` or `--failed`
first stops the task's task sessions and the runs of the workspace that still run, those waiting in
Execution's [lobby](../../execution/runner.md#the-lobby) for its lock included, then waits for the
lock. A run that waits for the lock meanwhile writes nothing into the task's folder: it waits in the
lobby, outside it, and when it takes the lock after the close, Execution refuses it with
`workspace_retired`, since the close removed the worktree with its binding and, while still holding
the lock, the lock file, so its result stays in the lobby and the history stays as the close left
it. A [workflow step](../../glossary.json#concept.workflow-step) of the workspace writes its records under the task's workflow lock, which the
close, and the close that ends a merge, takes last, after the workspace and merge locks, and holds
from before it removes the worktree until it has removed that lock's file: a step that holds it
first finishes its writes, which move with the folder, and one that waits for it is refused with
`workspace_retired` and writes nothing. Since a step never waits for another lock while holding the
workflow lock, the close waits for it only briefly. Just before the folder moves,
[Task sessions](../task-session/module.md#ending-claude-sessions) copies each Claude Code task
session's transcript into the session's node and finishes the node with the session's status, end
and usage from Claude Code's records, and once the task is closed it removes those sessions
from Claude's session list; what it could not keep or remove is named in the close's `warnings`,
and never fails the close. The history is never changed afterwards;
[Tracing](../../tracing/module.md)'s retention removes its conversation records after a while and
may remove it whole. A task name used again after its branch was deleted gets a new history key,
free both in the history and among the committed decision logs, so no closed task replaces another.

<a id="decision-log-in-git"></a>

**The decision log in Git.** Every task that ends leaves its decision log on the primary branch at
`.concorde/decisions/<history key>.md`, as the log stands once its closing is appended, the same
bytes as the log the history keeps. A task merged with `concorde task merge` carries it in its
merge commit ([Merging](#merging)), already with the closing `## Closed: merged, <time>` that its
close appends once the checks pass, dated when the merge began. A task closed any other way, with
`--completed`, `--failed` or `--merged` after a merge made by hand, gets a commit of that file
alone on the primary branch, with the subject `concorde: keep the decision log of <task-id>` and the
trailer `Concorde-Task: <task-id>`, made after the closing was appended and under the merge lock the
close holds; other changes of the primary worktree, staged or not, stay as they were and are not
committed. A close whose primary branch already holds the log exactly as it ended commits nothing,
as after a merge; one whose log changed after the merge commit, such as by an entry the main agent
added before `--resume`, gets that commit of the file alone, replacing the merge commit's copy. When
Git refuses that commit, such as on a detached `HEAD` or during an unfinished merge in the primary
worktree, the close refuses with `decision_log_uncommitted`, after the record was closed and the log
appended, and leaves the folder current: the same close run again commits the log and finishes.
The log in Git is a copy: the task's folder keeps its own, and nothing reads the copy back. A
worktree with checked-out submodules, such as the vendored references, is removed too, with its
submodules' checkouts and the repositories Git keeps for them under the worktree's own
administrative directory; a change inside a submodule is refused as any other uncommitted change,
whatever the submodule's `ignore` setting, unless `--force`. The close never deinitializes the
submodules: their registration lives in the repository's configuration, which every worktree
shares, and ending one task leaves it for the others.

## Merging

Several main sessions may work in one project, each delegating its tasks to task sessions that
work in the tasks' worktrees, and each merging from the primary worktree. Two merges at once would interleave in the one primary
checkout, so the main agent merges with one command:

```text
concorde task merge severity
```

Tasks first takes the task's [workspace lock](../../glossary.json#concept.workspace-lock), so
no run of the task commits on its branch or changes its worktree while it is merged, and then the
[merge lock](../../glossary.json#concept.merge-lock) of the primary worktree, and holds both
to the end. It waits for them inside its own process, up to `--wait` seconds in all (default
300): a `delivery` of the task that is still finishing is waited for rather than refused, and a
run still holding the workspace lock after that time refuses the merge with `workspace_busy`,
naming the run. It refuses, before touching anything, a task that could not be closed as merged
apart from not being merged yet (`not_merged`, `delivery_unverified`, `dirty_worktree`), reading the
task's delivery commits from Git, a primary worktree with uncommitted or untracked paths or a
detached `HEAD` (`primary_dirty`), once it has put back there what Issue writes left
([below](#nothing-changed-outside-the-task)), and anything changed outside the task's worktree
([below](#nothing-changed-outside-the-task)). The branch head those checks accepted, the task's latest delivery
commit, is the commit it merges: it records the task as **merging**, with the primary branch's
commit before the merge, that checked commit, the history key the task will close under and the
checks it will run, and only then runs `git merge --no-ff --no-commit <checked commit>` there, never
`git merge` of the branch name, which could take a commit nobody checked. It then adds the task's
decision log, followed by the closing its close will append, as
`.concorde/decisions/<history key>.md` and commits the merge with the trailer
`Concorde-Task: <task-id>`, so the merge commit is always a real merge, even where the primary
branch could fast-forward: its second parent is the delivery commit and it carries the log that
explains it. A Git refusal of that commit aborts the merge, removes the log's copy and refuses with
`git_failed`. A conflict is aborted and refused with `merge_conflict`, naming the paths: the
conflict is resolved in the task worktree by merging the primary branch into the task branch,
validating and delivering again, never in the primary worktree. After the merge, Tasks records the
merge commit and runs the checks in the primary worktree: `concorde spec-validation` of the merged
checkout by default, or exactly the `--check` commands given, such as a project that must build
first. A failed check, or checks that leave uncommitted paths, returns the primary branch with
`git reset --keep` to the commit it had and refuses with `check_failed`, naming the check, its exit
status, its log in the merge attempt's node, and any paths the checks created, which the reset
leaves in the primary worktree. Every merge attempt, whether it merged, conflicted, failed a check
or was undone, is a node `merges/<n>/` of the task's trace, each check a node below it with its
`output.log`. When everything passed, Tasks closes the task as merged, then, still holding the merge lock, closes
each Issue the task resolves that is still open as `resolved`, with the note that the task fixed it
and the merge commit and task as evidence, each closure a commit of its own on the primary branch
after the merge; it prints the record with the Issues it closed (`resolved`), the commits before and
after, each check, how long it waited and its warnings, such as a decision log nobody wrote in or an
Issue it could not close. An Issue it cannot close, because it was closed meanwhile or the Issue
store refused, is a warning carrying the Issues error chain, never a refusal: the merge and the
close stand, and the main agent disposes that Issue itself. Even a merge that cannot reach the
Issues at all warns with `issues_unavailable` and still ends the task's sessions and prints its
result. The merge's process imports Concorde's own modules from a snapshot of their sources taken
when it starts, so a task that changes Concorde itself never leaves the steps after its merge
running a mix of the old and the merged code; its checks, processes of their own, run the merged
code. A merge thus ends with the task closed on a checked merge commit or delivered again
on the commit the primary branch had; after a conflict or a failed check the task is delivered
again.

<a id="nothing-changed-outside-the-task"></a>

**The merge audits what lies outside the task's worktree.** A
[task session](../../glossary.json#concept.task-session) changes nothing outside its task worktree,
and since its shell runs under no sandbox
([Task sessions](../task-session/module.md#the-session-boundary)) nothing but its guidance holds it
there. The merge, the gate into the primary branch, therefore looks outside the task's worktree
before it merges, at each place whose state no task working in it accounts for:

- the **primary worktree**, which must be clean: nothing changes there while tasks run but
  Concorde's own records, which are either paths Git does not version — the task folders, locks,
  runs, history and [unbound runs](../../glossary.json#concept.unbound-run), all ignored by the
  `.gitignore` the installer writes — or
  committed by the command that writes them, as an [Issue](../../glossary.json#concept.issue)
  record and a [decision log](../../glossary.json#concept.decision-log) are. An Issue write killed
  between publishing its record and committing it leaves that record behind, so the merge first
  runs the Issues' recovery, holding the merge lock as every Issue write does, which puts back
  such records and nothing else. Uncommitted or untracked paths left after it refuse the merge as
  `primary_dirty`, whose detail also says that a task changes nothing outside its worktree, since
  the paths may be a task's and not the developer's, and names each Issue record whose change the
  recovery left as no Issue write's, to be inspected and reverted, or the recovery's own failure,
  after which `concorde issues recover` puts the records back once its cause is fixed;
- the **worktree of a task that has ended** and outlived it, which the close normally removes. No
  task will ever validate or deliver what is in it, so a change there refuses the merge as
  `changed_outside`, naming each such worktree, its task and its paths;
- the **worktree of a task that has delivered and waits**, its branch head a
  [delivery commit](../../glossary.json#concept.delivery-commit) that verifies. A change there may
  be its own session's, which went on working after delivering, or another task's; the merge warns,
  naming the worktree and the paths, and does not refuse, since refusing would block a task that
  has nothing to do with it.

What the audit judges is bounded by what the filesystem says, since nothing in it records who wrote
a change. The worktree of a task that is still working is not judged at all: its own session
changes it constantly, and what is written there is not lost either, since it becomes that task's
content, which its own validation, delivery and merge judge — its merge refuses an uncommitted
change as `dirty_worktree`. So a change another task writes into a working task's worktree is
caught, by that task rather than by the one that wrote it. Worktrees of no task, such as one a
developer's own session made, are not the project's to judge. And the audit judges working trees
and not commits: the primary branch legitimately moves while a task runs, as other tasks merge,
Issues are recorded and the developer commits, so a commit there is no evidence of a task having
overstepped. Nothing it names is undone blindly: each refusal and warning says what changed, for
the main agent to find out what wrote it.

The flow of one `concorde task merge`, with where each way out leaves the primary branch and the
task; a task left `merging` is finished as the next passage explains:

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
unlogged: "decision_log_failed: task closed as merged, close --merged appends the closing"
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

**An interrupted merge.** A merge whose process ends before its checks decided, killed or crashed,
leaves the task `merging` and perhaps an unchecked merge commit at the head of the primary branch.
The kernel has released the merge lock, so nothing but the record says that the primary branch is
not to be built on. Every task command that changes something therefore looks for a `merging`
task first: while no live process holds the merge lock, `open`, `merge`, `close`, `session` and
`escalate`, in any main session and for any task, refuse with `merge_incomplete`, naming the task,
the commit before the merge, the merge commit, where the primary branch is now and the two ways
out; `task list` and `task show` still answer, showing the task as `merging`. The main agent
finishes the merge with one of:

```text
concorde task merge severity --resume
concorde task merge severity --abort
```

`--resume` reruns the checks the merge recorded on the merge commit, when the primary branch's head
is still that commit, then closes the task as merged or undoes the merge and refuses with
`check_failed` exactly as an uninterrupted merge does; with any other head it refuses with
`not_resumable`. `--abort` aborts a `git merge` left in progress, resets the primary branch to the
commit before the merge when its head is the merge commit, leaving it alone when it already is
that commit, and returns the task to delivered. Both take the merge lock and the workspace lock like
a merge, and both refuse with `merge_diverged`, touching nothing, when the primary worktree is on
another branch or its head is neither of those commits, since Tasks never resets commits it did
not make. A merge that is still running is not interrupted: its process holds the merge lock, so
`open`, `merge` and `close` wait for it and answer `merge_busy`, a `session` or `escalate` of the
task being merged answers `merge_busy` at once, and those of other tasks go ahead. A reset that
Git refuses (`rollback_failed`) and a close that fails after the checks passed also leave the task
`merging`, and their refusals say to `--abort` or to `--resume` once the cause is fixed.

## Waiting for a task, a run or a lock

<a id="waiting"></a>

A session that wants to learn when something it did not start is over asks once and is woken, never
polls:

```text
concorde task wait severity --until delivered
concorde task wait severity --rebound concorde-7d
concorde task wait --run r-20260929T101500-delivery-5f3a
concorde task wait --lock merge
concorde task wait severity --lock workspace
```

`--until` returns once the task's derived state is one of the named states, `--rebound` once the
task's record names a main agent's session other than the one given, `--run` once the run's
runner holds no [run lock](../../glossary.json#concept.run-lock), with how the run ended, and
`--lock` once nobody holds the merge lock or the task's workspace lock, with who held it. Each
answers at once when that is already so and prints one JSON value, and `--timeout` bounds the wait.
A task reaches `delivered`, `merging`, `closed` and `failed` only while its workspace lock is held,
by a delivery run, a merge or a close, so a task wait learns from the kernel of every new holder of
that lock, blocks on the lock until that holder lets it go, and reads the state again; those four
are the states it admits, and a task that ends in another state ends the wait with
`wait_unreachable`. A rebind wait learns from the kernel of every write of the task's record, and
of its folder moving to the history, and reads the record again; a task that ended ends it with
`wait_unreachable`. A lock or run wait blocks on the lock itself, so a holder that dies wakes it
as surely as one that ends. The project MCP server's `register_wait` runs the same waits for a
session it can wake through a channel; this command is their form for background Bash.

## Who runs the commands, and refusals

Only the main agent opens, merges and closes tasks, starts task sessions, rebinds tasks and
answers reports, only from the primary worktree (`not_primary` otherwise); `concorde task session`
is dispatched to [Task sessions](../task-session/module.md) once that check passed, and every session it starts is
recorded here through the record updates the [contracts](contracts.md#record-updates)
list; a [worker](../../glossary.json#concept.worker) cannot run them, having no Git access.
Every refusal names its code (`task_exists`, `unknown_module`, `invalid_transition`, `not_merged`,
...), what was refused and why, and changes nothing apart from the few refusals that say what they
left behind ([requirements](requirements.md#req.tasks.refusal-inert), [contracts](contracts.md)).

## Why it is built this way

Tasks is the workspace of the task level of Concorde's
[levels of work](../../module.md#the-levels-of-work) without being a level itself: the level is
played by the task session to which the main agent delegates each task, while the main agent
manages the tasks and merges them from the primary worktree, and Tasks holds what the task level
works in, the branch, worktree, record and decision log. It never
appears in a call chain itself: the main agent and Task sessions call into it to read or write that
workspace, and it calls none of them back.

### Where a task lives

The task is the isolation unit because Git already isolates branches and worktrees: changes stay in
their own checkout until Delivery commits and the main agent merges, so two tasks can change the
same Module at once, meeting only at merge time where Git reports conflicts; a shared checkout
would instead leak one task's half-finished edits into another's checks.

Task worktrees live under `.claude/worktrees/` of the primary worktree, at
`.claude/worktrees/<task-id>` and nowhere else, because that is where Claude Code keeps a session's
worktrees, a task session is a Claude Code session started in its task worktree, and every worktree
Concorde's workers work in lives there. Git ignores the directory there, so a task's checkout never
appears as files of the primary branch; the Workers' [deny rules](../../glossary.json#concept.deny-rules) still hide the
primary worktree's other files and the other task worktrees from a worker, since those are siblings
of the path to its own worktree.

Task folders live in the primary worktree, not the task worktrees: the main agent works there and
must see every task in one place, including ones whose worktree is gone; and a task worktree is
exactly what workers and Delivery commit, so records kept there would be swept into commits.
`.concorde/tasks/` and `.concorde/history/` are thus local, Git-ignored state: what travels with the
code is the [delivery commit](../../glossary.json#concept.delivery-commit) and, once the task ended,
its decision log, which Tasks commits to the primary branch. Any process finds the primary worktree
through Git's common directory. One folder per task, organized by the task's lifecycle as
[Tracing](../../tracing/module.md) lays it out, means a task's record, log, sessions and runs are
read in one place and ended in one move; the record stays small because the task's history is its
trace, which only grows by new nodes.

### Locks

Several processes may change a task at once, a task session escalating while the main agent closes
the task, so every change of a task's record or trace is made while holding the task's lock,
`locks/tasks/<task-id>.lock`, and every record write is one
[file transaction](../../glossary.json#concept.file-transaction) bound to the digest it replaces: a
change made meanwhile by a process that did not take the lock is detected, Tasks rereads and
reapplies if preconditions still hold, and refuses with `record_conflict` after three attempts. Each
task has its own lock and folder, so tasks never contend. Every lock lies under `.concorde/locks/`,
apart from the folders it protects, since a close must hold the task's workspace lock precisely
while it moves the task's folder.

The merge lock is held by the process doing the merge rather than recorded as an owner that others
wait on and that must wake them: a recorded owner that crashed, was closed or forgot to notify
would leave every waiter stuck, and the sessions that merge share no channel that would reliably
notify each other. A kernel `flock` is released and wakes waiters whatever happens to its holder,
the same way for every kind of session. It only works if the whole critical section runs in one
process, which is why merging, checking, undoing and closing are one command instead of steps the
main agent issues one by one, and why conflicts are resolved in the task worktree: the lock is then
held for the seconds a merge and its checks take, not for however long a resolution takes. Holding
it also for `open` and `close` keeps both from reading a primary branch whose merge might still be
reset, and every write of the project's Issues, which [Issues](../../issues/module.md) commits on the
primary branch, takes it too, so no Issue commit lands between a merge commit and its checks.

The lock alone cannot cover a merge whose process dies: the kernel releases the lock at once, and
the next command would build on a merge commit no check accepted. So the merge writes `merging`
into the record before `git merge` runs, and that stored state, not the lock, is what the other
commands read; together they tell a merge that is still running (the lock is held) from one that
was interrupted (it is not). The recovery is left to the main agent rather than done by the next
command that notices, because checking again and undoing are both legitimate and the next command
may belong to another main session with another task in mind. Merging the checked commit by its
identity, and holding the task's workspace lock while merging or closing, keep the commit merged
the one the checks accepted: a run of the task, such as a delivery started in the task worktree,
cannot move the branch between the checks and the merge or write a worktree being removed.
The workspace lock is taken before the merge lock and waited for without the merge
lock, so that waiting for one task's run never holds up the merges of other tasks; `merge` and
`close` are the only commands that take both, always in that order, so none waits on another in a
cycle. The waits happen inside the command because its callers are agents: a refusal they must
retry would have them poll, paying for every look, where a blocked command costs nothing until
it returns.

### Why the decision log goes to Git

Of everything a task leaves, the decision log is what a later reader of the code needs: the
decisions taken without the developer, the escalations and their answers, the results that were not
`ok` with their error chains, a few kilobytes per task. The rest of a task's folder, above all the
transcripts of its sessions and workers, is large, local and removed by retention. So the log is
committed when the task ends, and nothing else of the folder is.

Tasks commits it, not Delivery, because Delivery is part of Execution and knows no task, while the
log lives in the task's folder of the primary worktree and belongs to the task level. A merged task
carries its log in its merge commit, so that Git itself relates the two: the commit that brings the
delivery into the primary branch, whose second parent is the delivery commit, adds the log that
explains it, and a merge undone by a failed check takes its log with it. That is why a merge always
makes a merge commit. A task that ends without a merge has no such commit, so its log gets one of
its own; every ended task is thus in Git, completed and failed ones too. The log's file is named by
the history key rather than the task's name, and a key is free only when neither the history nor
the committed logs hold it, because a task name can be used again once its branch is deleted, and
retention may by then have removed the earlier task's history folder while its log stays in Git.
The merge records the key it chose in the `merging` record, so that `--resume` closes the task under
the key its merge commit already used.

The copy in Git equals the log as the task ended, closing included, rather than the log as it stood
at the merge, so that the history and Git never disagree once retention removed the one. The closing
is appended only once the checks pass, after the merge commit, yet amending that commit would change
the commit the checks examined, and a commit of the log after every merge would double the commits
a merge makes. So the merge commit's copy carries the closing in advance, dated by the start the
`merging` record keeps, and the close appends that same closing: a merge undone by a failed check
takes the copy with it and leaves the log without a closing, and only a log changed between the
merge commit and the close, which an interrupted merge allows, needs a commit of its own.

### Why the state is derived

If the runs, deliveries and workflows of a task were written into its record, the execution core
would have to know tasks, and every fact would exist twice, in the record and in the run store or
Git. A runner killed between its result and the record update, a delivery commit whose record
update failed, or a run started by hand in the worktree would each leave the two copies
disagreeing, and something would have to recover the record. So the record holds only the facts
the task level alone knows: why the task exists, what it may touch, who escalated or reported what,
which sessions work it, whom they report to and how it ended. Everything about what happened in
the worktree is read where Execution recorded it, each time Tasks needs it: a task is active when its workspace has a run or a
change, delivered when Git shows a delivery commit of its workspace at the branch head with nothing
after it and that commit has exactly one parent, and mergeable only then. The subject is a mark, not
a proof: only the task level and Delivery commit on the branch, and the task level has no reason to
forge the mark, while the one-parent check keeps a merge that happens to carry the subject, such as
one resolving a conflict, from counting. With no second copy there is nothing to recover and nothing
that can disagree.

Deriving costs a scan of the workspace folder, a `git log` of the task branch and a Git read to
verify its head whenever a task is listed or shown, which is small next to what a run costs, and it
holds however a run ended: a run whose runner died is `lost` in the listing, and the kernel has
already released its workspace lock. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

## The task store

<a id="realization.tasks.store"></a>

The **[Task](../../glossary.json#concept.task) store** realization holds the `concorde task`
commands (`cli.py`), the records, the derived state, the binding written at open and the record
updates task sessions call, the reports and the main agent's session (`store.py`), the merge under
the merge lock (`merge.py`), and their tests, run on real Git repositories with delivery commits
and run store entries written the way Execution writes them. It is the only writer of task records,
writing each decision log once, at open, appending only escalations, reports, answers and closings,
and committing a copy of it when the task ends. The
command dispatches `concorde task session` to the code of Task sessions.

## Providers

<a id="uses-execution"></a>

**Execution** works in the task worktree once it is bound. Tasks writes the
[workspace binding](../../glossary.json#concept.workspace-binding) as the
[binding contract](../../execution/contracts.md#contract.execution.workspace-binding) requires, and
relies on Execution only reading it, working on the Modules, branch and base it names, recording
every run of the workspace as a trace node in the workspace folder it names, and holding the
[workspace lock](../../glossary.json#concept.workspace-lock) for every bound run, so that Tasks,
holding the same lock, after waiting for a running run to release it, while it merges or closes the
task, knows no run of it is changing the branch or worktree meanwhile. It reads a run's
[result](../../glossary.json#concept.run-result) for its status, Modules and error chain, and the
run's [run progress file](../../glossary.json#concept.run-progress-file) while it runs, whose
runner liveness tells a `running` run from a `lost` one; it never writes either. A run that is
neither finished nor alive is shown as `lost` rather than trusted as running.

<a id="uses-delivery"></a>

**Delivery** commits a delivered workspace as a
[delivery commit](../../glossary.json#concept.delivery-commit) on the bound
branch, whose subject names the workspace. Tasks relies on that commit being the only record of a
delivery and reads the delivery commits of the task's workspace on the task branch since its base
commit, with Delivery's own reader, to derive `delivered`, to list deliveries in `task show`, and to
decide whether a task may be merged or closed as merged. A task branch with no delivery commit is
refused with `not_merged`. Tasks counts the head as delivered only when it verifies by Delivery's
own check, the one Delivery applies before it reports a delivered head
([req.delivery.recovered-verified](../../execution/commands/delivery/requirements.md#req.delivery.recovered-verified)):
it has exactly one parent. A head that does not verify is refused with `delivery_unverified`,
naming the mismatch, since Delivery did not create it.

<a id="uses-task-session"></a>

**Task sessions** starts [task sessions](../../glossary.json#concept.task-session) when
`concorde task session` hands it a task that passed Tasks' checks. Tasks relies on it recording
sessions only through the record updates, and prints its refusals in the shape of every
`concorde task` refusal. A close relies on it to stop the task's task sessions before a close
without a merge, to keep their transcripts in their nodes and finish those nodes before the folder
moves and to remove them from Claude's session list afterwards, returning a warning, never a
refusal, for what it could not keep or remove.

<a id="uses-tracing"></a>

**Tracing** lays out the task's folder, its history and the locks, and gives the task, each
session, each merge attempt and its checks the shape of a
[trace node](../../glossary.json#concept.trace-node). Tasks writes those nodes through Tracing's
library, takes the task, workspace and merge locks under `.concorde/locks/`, runs Tracing's
retention at the start of every `task open` and `task close`, and reports in the error contract.
It relies on the [layout](../../tracing/contracts.md#layout), the
[locks](../../tracing/contracts.md#locks) and the
[node contract](../../tracing/contracts.md#contract.tracing.node).

<a id="uses-issues"></a>

**Issues** keeps the project's [Issues](../../glossary.json#concept.issue) in the primary worktree.
Tasks relies on its store to read whether each Issue a task names as resolving exists and is open,
and to put back, before a merge judges the primary worktree clean, what Issue writes left
uncommitted there, for a caller that already holds the merge lock; and on its bookkeeping command
to close them after the merge, for such a caller too, answering or refusing with its own error
link, which Tasks passes on in a warning.

<a id="uses-spec"></a>

**Spec core** provides two things Tasks relies on: its registry, so a record never names a Module
that doesn't exist at open; and its
[file transactions](../../glossary.json#concept.file-transaction), so every record write is
complete or absent, bound to the bytes it replaces. Tasks reads the primary worktree's registry to
open a task, since its worktree doesn't exist yet. If the Specs cannot be loaded, the command is
refused and nothing is written.
