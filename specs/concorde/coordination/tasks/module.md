# Tasks

## Purpose

Tasks manages the workspace of the task level: it gives every unit of work the main agent starts
its own place, a Git branch, a worktree checked out on it and bound as an
[Execution](../../execution/module.md) workspace, a task record and a decision log. Whoever works
the task relies on it the same way, the main agent that enters the worktree itself or a task
session it delegated the task to: to run pieces of work side by side without their changes mixing,
to know each task's state, and to keep the reasons behind choices made without the developer. Tasks
binds each task worktree when it opens the task and learns what happened in it only from what
Execution recorded, the workspace's runs and its delivery commits; nothing below the task level
reads or writes a task record. When the main agent merges a delivered task, Tasks does the merge
into the primary branch under a lock, so several main sessions never merge at once, and undoes it
if the checks that follow fail. Tasks is independent of the sessions that work in its tasks: it
does not start or follow them, which [Task sessions](../task-session/module.md) does, and it does
not decide how work is split, which tasks run in parallel or when a task is merged. It never runs
an Operation or a recorded command, never commits on a task branch, and never interprets the
decision log.

## Terminology

| Term | Definition |
| --- | --- |
| Task | One unit of work of the main agent, made of a branch, a worktree checked out on it and bound as the workspace named after the task, a task record and a decision log. |
| Task record | The JSON file in the primary worktree that holds a task's identity, goal, Modules, branch, worktree path, base commit, stored state, escalated error chains, started task sessions and, once it ended, how it ended. |
| Decision log | The Markdown file next to a task record in which the session working on the task writes the choices it made without the developer, and to which escalations are appended. |
| Task state | The stage of a task's life, open, active, delivered, then closed when the task reached its goal (merged or completed) or failed when it did not, of which only open, closed and failed are stored and active and delivered are derived from what Execution recorded. |
| Merge lock | The lock of the primary worktree that one process at a time holds while it merges a task into the primary branch, opens a task or closes one; the kernel releases it when that process ends. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../../vocabulary.md#concept.concorde.task-session) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Workspace](../../execution/module.md#concept.execution.workspace) | |
| [Workspace binding](../../execution/module.md#concept.execution.workspace-binding) | |
| [Run](../../execution/module.md#concept.execution.run) | |
| [Run result](../../execution/module.md#concept.execution.run-result) | |
| [Run store](../../execution/module.md#concept.execution.run-store) | |
| [Workspace lock](../../execution/module.md#concept.execution.workspace-lock) | |
| [Delivery commit](../../execution/delivery/module.md#concept.delivery.delivery-commit) | |
| [File transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Registry](../../spec-tooling/spec/module.md#concept.spec.registry) | |

A task is Coordination's word and a workspace Execution's: every task worktree is a workspace named
after its task, but Execution never learns that it is one.

## Usage

<a id="concept.tasks.task"></a>

**Opening a task.** The main agent opens a **task** for each piece of work it wants isolated, e.g.
"let Issue reports carry a severity" bound to `module.issues`, from the primary worktree:

```text
concorde task open severity --goal "let Issue reports carry a severity" --modules module.issues
```

Tasks checks the identity is new and every named Module exists in the
[registry](../../spec-tooling/spec/module.md#concept.spec.registry), creates branch
`concorde/severity` from the primary worktree's commit (or `--base <ref>`), adds a worktree at
`.claude/worktrees/severity` inside the primary worktree by default (or `--path <dir>`), copies the
primary worktree's [worker model
configuration](../../execution/workers/module.md#concept.workers.model-configuration) into it when
there is one, binds the worktree as a workspace, writes the record and log, and prints the record.
Git ignores that configuration, so the copy is the task's own: the task's workers keep the models
chosen when it opened, whatever the primary worktree chooses later, until `concorde
configure-workers` runs in the task worktree. A worktree path inside the primary worktree must be
ignored by Git there, or the open is refused with `worktree_not_ignored`; the installer adds
`.claude/worktrees/` to `.gitignore`.

**The binding.** Binding the worktree is what makes it a place where Execution can work. Tasks
writes its [workspace binding](../../execution/module.md#concept.execution.workspace-binding),
`.concorde/workspace.json` at the worktree's root, as the
[binding contract](../../execution/contracts.md#contract.execution.workspace-binding) defines:

```json
{
  "schema_version": 1,
  "workspace": "severity",
  "root": "/home/dev/shop/.claude/worktrees/severity",
  "branch": "concorde/severity",
  "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
  "goal": "let Issue reports carry a severity",
  "modules": ["module.issues"],
  "records": "/home/dev/shop/.concorde"
}
```

The workspace is named after the task, so its runs, its workspace lock and its delivery commits are
found by the task identity. The records directory is the primary worktree's `.concorde`, so the
runs of every task land in one [run store](../../execution/module.md#concept.execution.run-store)
beside the task records, and survive the worktree. From then on the task's work happens inside that
worktree with the worktree's own `concorde`: every Operation, recorded command and workflow started
there reads the binding and works on this task's goal, Modules, branch and base without naming the
task. Tasks writes the binding once and never again; closing removes it with the worktree. A copy
of the configuration or a binding the file system refuses ends the open with `config_copy_failed`
or `binding_failed`, naming the worktree and branch left behind and how to remove them, and records
no task. Parallelism exists only between tasks: none share a worktree, and Execution's
[workspace lock](../../execution/module.md#concept.execution.workspace-lock) lets each workspace run
one thing at a time.

<a id="concept.tasks.task-record"></a>

**The record.** The **task record** lives at `.concorde/tasks/<task-id>.json`: identity, goal,
Modules, branch, worktree path, base commit, stored state, escalations, started task sessions and,
once the task ended, how it ended ([exact fields](contracts.md#contract.tasks.record)). It keeps no
runs, deliveries or workflow: those are recorded by Execution, and a copy in the record could
disagree with them after a crash or a run nobody announced. Its goal and Modules are those named at
open and never change; a run that names further Modules with `--modules` records them in its own
[run result](../../execution/module.md#concept.execution.run-result).

`concorde task list` prints the records with their derived state, optionally filtered by
`--state`. `concorde task show <task-id>` prints what the task level needs to know about one task
in one value: the record with its derived state, the workspace's
[runs](../../execution/module.md#concept.execution.run) read from the run store (each with its kind,
name, Modules and status, `running` while its runner lives and `lost` when the runner died without
a result), its [delivery commits](../../execution/delivery/module.md#concept.delivery.delivery-commit)
read from the task branch, who holds its workspace lock now, and the path of the decision log.

Since every Module was registered when the task opened, one the task worktree no longer registers
is exactly one the task branch removed or renamed; Tasks tells the current Modules from the removed
ones by reading the task worktree's registry each time it is asked.

<a id="concept.tasks.decision-log"></a>

**The decision log** lives at `.concorde/tasks/<task-id>.decisions.md`. Tasks creates it with a
heading and the goal at open, then only appends escalations and how the task ended; the session
working on the task, the main agent or the task's task session, appends directly: every uncertainty
it decided alone, with options and reason, every non-`ok` run result and what it did about it, and
the decisions and problems of a workflow's report, which Workflows saves beside its own record and
never writes here. The main agent reads the log when it reports to the developer at the end of the
task.

When it cannot handle an error itself, the session escalates with `concorde task escalate`, naming
the runs of the task's workspace, saved refusals or earlier escalations it cannot handle and
stating its own [error chain](../../vocabulary.md#concept.concorde.error-chain) link: code, what
needs deciding, why not alone, what it tried, options and recommendation. A task session escalates
with `--by task-session` to the main agent; the main agent's own link, the default, escalates to the
developer and may name a task session's escalation as a cause with `--escalation <n>`. Tasks reads
each named run's error from its run result, refusing a run of another workspace or an unbound one
with `unknown_run`, puts those errors unchanged under that link as its causes, appends the resulting
chain to the record's escalations and to the decision log (rendered and as JSON), and prints it, so
the reader gets one chain from the question down to where the error started.

<a id="concept.tasks.task-state"></a>

**Task state.** Only closing a task changes its stored state: the record says `open` from the open
until the task ends, then `closed` or `failed`. Whether an open task is still **open**, **active**
or **delivered** is derived each time the task is listed or shown:

```d2 illustrative
start: "" {shape: circle; width: 16; height: 16; style.fill: black}
open
active
delivered
closed
failed
start -> open: task open
open -> active: a run, a commit or a change in the workspace
active -> delivered: head is a delivery commit, worktree clean
delivered -> active: a change or a commit after it
delivered -> closed: task merge, or task close --merged
open -> closed: task close --completed
active -> closed: task close --completed
delivered -> closed: task close --completed
open -> failed: task close --failed
active -> failed: task close --failed
delivered -> failed: task close --failed
```

A task is **delivered** when its branch head is a delivery commit of its workspace and its worktree
is clean; **active** when its workspace has a run in the run store, running or finished, or its
branch moved past the base commit, or its worktree has uncommitted changes; and **open** before any
of these. A run that changes nothing, such as a review after delivery, leaves a delivered task
delivered; a change after the delivery commit, committed or not, makes it active until the next
delivery. A task ends in one of two states, and the record keeps the outcome:

- **closed** means the task was ended on purpose because it reached its goal. Merging is the usual
  way: the main agent merges a delivered task, unasked, with `concorde task merge` (below), which
  closes it with outcome `merged`. `concorde task close <task-id> --merged` closes a task merged
  some other way, and is accepted only when the latest delivery commit of the workspace is the
  branch's head, that head is in the primary branch, and the worktree is clean. Merging is not the
  only way to reach a goal: a task that tried something out, investigated a question or only needed
  `understand` closes with `--completed --note "<what it achieved>"`, outcome `completed`.
- **failed** means the task did not reach its goal. `--failed --reason "<why>"` records the reason,
  and when an error caused the failure, the error chains too: `--run <run-id>` takes the error of a
  run of the task's workspace and `--error-file` a saved one, each unchanged. A failure no error
  caused, such as a wrong direction, is declared with `--no-error`; one of the two is required, so
  whether an error caused the failure is never left unsaid.

Closing without a merge refuses uncommitted changes unless `--force`. Closing appends the outcome,
the note and any error chains to the decision log and removes the worktree, and with it the
workspace binding, keeping the branch, record and log; no run of the task's workspace can start
there any more, and a closed or failed task stays so whatever its workspace records afterwards. A
worktree with checked-out submodules, such as the vendored references, is removed too: its
submodules are deinitialized first, which refuses a submodule with local changes unless `--force`,
and only then is the worktree removed.

<a id="concept.tasks.merge-lock"></a>

**Merging.** Several main sessions may work in one project, each entering a task worktree of its
own and returning to the primary worktree to merge. Two merges at once would interleave in the one
primary checkout, so the main agent merges with one command:

```text
concorde task merge severity
```

Tasks takes the **merge lock** of the primary worktree, waiting for it up to `--wait` seconds
(default 300), and holds it to the end. It refuses, before touching anything, a task that could
not be closed as merged apart from not being merged yet (`not_merged`, `dirty_worktree`), reading
the task's delivery commits from Git, and a primary worktree with uncommitted or untracked paths or
a detached `HEAD` (`primary_dirty`). It then runs `git merge` there. A conflict is aborted and
refused with `merge_conflict`, naming the paths: the conflict is resolved in the task worktree by
merging the primary branch into the task branch, validating and delivering again, never in the
primary worktree. After the merge, Tasks runs the checks in the primary worktree: `concorde
spec-validation` of the merged checkout by default, or exactly the `--check` commands given, such
as a project that must build first. A failed check, or checks that leave uncommitted paths, returns
the primary branch with `git reset --keep` to the commit it had and refuses with `check_failed`,
naming the check, its exit status and its log, `.concorde/tasks/<task-id>.merge.log`. When
everything passed, Tasks closes the task as merged and prints the record with the commits before
and after, each check and how long it waited.

The lock is a `flock` held by the command's own process, so no session has to release it or
announce that it is done: the kernel releases it when the process ends, even when it is killed, and
a waiting command wakes as soon as it is free. A command that gives up waiting fails with
`merge_busy`, naming the holder's command, task, process and start time, which the holder writes
into the lock file while it holds it. `concorde task open` and `concorde task close` take the same
lock, so a task is never based on, or closed against, a merge that may still be undone.

Only the main agent opens, merges and closes tasks and starts task sessions, only from the primary
worktree (`not_primary` otherwise); `concorde task session` is dispatched to
[Task sessions](../task-session/module.md) once that check passed, and every session and round it
starts is recorded here through the record updates the [contracts](contracts.md#record-updates)
list; a [worker](../../vocabulary.md#concept.concorde.worker) cannot run them, having no Git access.
Every refusal names its code (`task_exists`, `unknown_module`, `invalid_transition`, `not_merged`,
...), what was refused and why, and changes nothing ([contracts](contracts.md)).

## Design

Tasks is the workspace of the task level of Concorde's [levels of work](../../module.md#the-levels-of-work)
without being a level itself: the level is played by the main agent or by a task session it
delegates to, and Tasks holds what either of them works in, the branch, worktree, record and
decision log, the same way whichever plays it. It never appears in a call chain itself: the main
agent and Task sessions call into it to read or write that workspace, and it calls none of them
back.

### Inside

The task is the isolation unit because Git already isolates branches and worktrees: changes stay in
their own checkout until Delivery commits and the main agent merges, so two tasks can change the
same Module at once, meeting only at merge time where Git reports conflicts; a shared checkout
would instead leak one task's half-finished edits into another's checks.

Task worktrees live under `.claude/worktrees/` of the primary worktree because that is where
Claude Code can switch a session into an existing worktree and back, which is how the main agent
works inside one task at a time. Git ignores the directory there, so a task's checkout never
appears as files of the primary branch; the Workers' deny rules still hide the primary worktree's
other files and the other task worktrees from a worker, since those are siblings of the path to
its own worktree.

Records live in the primary worktree, not the task worktrees: the main agent works there and must
see every task in one place, including ones whose worktree is gone; and a task worktree is exactly
what workers and Delivery commit, so records kept there would be swept into commits.
`.concorde/tasks/` is thus local, Git-ignored state, like the run store: the evidence bundle
Delivery commits is what travels with the code. Any process finds the primary worktree through
Git's common directory.

Several processes may write a record at once, a task session recording a round while the main agent
escalates, so every write is one
[file transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) bound to the
digest it replaces: a concurrent change is detected, Tasks rereads and reapplies if preconditions
still hold, and refuses with `record_conflict` after three attempts. Each task has its own record
file, so tasks never contend.

The merge lock is held by the process doing the merge rather than recorded as an owner that others
wait on and that must wake them: a recorded owner that crashed, was closed or forgot to notify
would leave every waiter stuck, and Claude Code and pi sessions share no messaging channel to
notify each other. A kernel `flock` is released and wakes waiters whatever happens to its holder,
the same way for every kind of session. It only works if the whole critical section runs in one
process, which is why merging, checking, undoing and closing are one command instead of steps the
main agent issues one by one, and why conflicts are resolved in the task worktree: the lock is then
held for the seconds a merge and its checks take, not for however long a resolution takes. Holding
it also for `open` and `close` keeps both from reading a primary branch whose merge might still be
reset. The decision log is free Markdown, since its readers are the main agent and the developer;
Tasks gives it only a fixed place and lifetime. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

<a id="realization.tasks.store"></a>

The **Task store** realization holds the `concorde task` commands (`cli.py`), the records, the
derived state, the binding written at open and the record updates task sessions call (`store.py`),
the merge under the merge lock (`merge.py`), and their tests, run on real Git repositories with
delivery commits and run store entries written the way Execution writes them. It is the only
writer of task records, writing each decision log once, at open, and appending only escalations and
closings. The command dispatches `concorde task session` to the code of Task sessions.

Record, log and state fit together this way:

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
  state: Task state
  lock: Merge lock
  store -> record: writes
  store -> log: creates
  store -> lock: holds while merging, opening or closing
  record -> task: describes
  record -> state: holds
  log -> task: explains the choices of
}
```

### Why the state is derived

If the runs, deliveries and workflows of a task were written into its record, the execution core
would have to know tasks, and every fact would exist twice, in the record and in the run store or
Git. A runner killed between its result and the record update, a delivery commit whose record
update failed, or a run started by hand in the worktree would each leave the two copies
disagreeing, and something would have to recover the record. So the record holds only the facts
the task level alone knows: why the task exists, what it may touch, who escalated what, which
sessions work it and how it ended. Everything about what happened in the worktree is read where
Execution recorded it, each time Tasks needs it: a task is active when its workspace has a run or a
change, delivered when Git shows a delivery commit of its workspace at the branch head with nothing
after it, and mergeable only then. With no second copy there is nothing to recover and nothing that
can disagree.

Deriving costs a scan of the run store and a `git log` of the task branch whenever a task is listed
or shown, which is small next to what a run costs, and it holds however a run ended: a run whose
runner died is `lost` in the listing, and the kernel has already released its workspace lock.

### Around it

```d2
store: Task store
binding: Execution / Workspace binding
runstore: Execution / Run store
lock: Execution / Workspace lock
commits: Delivery / Delivery commit
store -> binding: writes when a task opens
store -> runstore: reads the workspace's runs from
store -> lock: shows the holder of
store -> commits: reads from the task branch
```

<a id="uses-execution"></a>

**Execution** works in the task worktree once it is bound. Tasks writes the
[workspace binding](../../execution/module.md#concept.execution.workspace-binding) as the
[binding contract](../../execution/contracts.md#contract.execution.workspace-binding) requires, and
relies on Execution only reading it, working on the Modules, branch and base it names, recording
every run of the workspace in the [run store](../../execution/module.md#concept.execution.run-store)
of the records directory it names, under the workspace's name, and holding the
[workspace lock](../../execution/module.md#concept.execution.workspace-lock) for every bound run. It
reads a run's [result](../../execution/module.md#concept.execution.run-result) for its status,
Modules and error chain, and the run's progress file while it runs; it never writes either. A run
that is neither finished nor alive is shown as `lost` rather than trusted as running.

<a id="uses-delivery"></a>

**Delivery** commits a delivered workspace as a
[delivery commit](../../execution/delivery/module.md#concept.delivery.delivery-commit) on the bound
branch, whose subject and trailers name the workspace, its evidence bundle and the run that decided
its readiness. Tasks relies on that commit being the only record of a delivery and reads the
delivery commits of the task's workspace on the task branch since its base commit, with Delivery's
own reader, to derive `delivered`, to list deliveries in `task show`, and to decide whether a task
may be merged or closed as merged. A task branch with no delivery commit is refused with
`not_merged`.

- <a id="uses-workers"></a>**Workers** names the file of the [worker model
  configuration](../../execution/workers/module.md#concept.workers.model-configuration), which Tasks
  copies into a new task worktree. Tasks relies on it being one untracked file per worktree; it
  never reads or changes its content.
- <a id="uses-task-session"></a>**Task sessions** starts, answers and stops
  [task sessions](../../vocabulary.md#concept.concorde.task-session) when `concorde task session`
  hands it a task that passed Tasks' checks. Tasks relies on it recording sessions and
  [rounds](../task-session/module.md#concept.task-session.round) only through the record updates,
  and prints its refusals in the shape of every `concorde task` refusal.
- <a id="uses-spec"></a>**Spec core** provides two things Tasks relies on: its registry, so a
  record never names a Module that doesn't exist at open; and its
  [file transactions](../../spec-tooling/spec/module.md#concept.spec.file-transaction), so every
  record write is complete or absent, bound to the bytes it replaces. Tasks reads the primary
  worktree's registry to open a task (its worktree doesn't exist yet) and the task worktree's to
  tell current Modules from removed ones. If the Specs cannot be loaded, the command is refused and
  nothing is written.
