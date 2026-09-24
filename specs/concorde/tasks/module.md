# Tasks

## Purpose

Tasks gives every unit of work the main agent starts its own place: a Git branch, a worktree
checked out on it, a task record and a decision log. The main agent relies on it to run pieces of
work side by side without their changes mixing, to know each task's state, and to keep the reasons
behind choices it made without the developer. The Operation host relies on it to find a task's
worktree and record every run and delivery against it, kept in the primary worktree only. On the
main agent's request it also starts a task session in a task worktree, with a boundary confining
that session's writes to its task. When the main agent merges a delivered task, Tasks does the
merge into the primary branch under a lock, so several main sessions never merge at once, and
undoes it if the checks that follow fail. Tasks does not decide how work is split, which tasks run
in parallel or when a task is merged, never runs an Operation, never commits on a task branch, and
never interprets the decision log; the main agent and its task sessions do all of that.

## Terminology

| Term | Definition |
| --- | --- |
| Task | One unit of work of the main agent, made of a branch, a worktree checked out on it, a task record and a decision log. |
| Task record | The JSON file in the primary worktree that holds a task's identity, goal, Modules, branch, worktree path, base commit, state, Operation runs, deliveries, escalated error chains and started task sessions. |
| Decision log | The Markdown file next to a task record in which the session working on the task writes the choices it made without the developer, and to which escalations are appended. |
| Task state | The stage of a task's life: open, active, delivered, then closed when the task reached its goal (merged or completed) or failed when it did not. |
| Merge lock | The lock of the primary worktree that one process at a time holds while it merges a task into the primary branch, opens a task or closes one; the kernel releases it when that process ends. |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../vocabulary.md#concept.concorde.task-session) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [File transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |

## Usage

<a id="concept.tasks.task"></a>

The main agent opens a **task** for each piece of work it wants isolated, e.g. "let Issue reports
carry a severity" bound to `module.issues`, from the primary worktree:

```text
concorde task open severity --goal "let Issue reports carry a severity" --modules module.issues
```

Tasks checks the identity is new and every named Module exists in the
[registry](../spec-tooling/spec/module.md#concept.spec.registry), creates branch
`concorde/severity` from the primary worktree's commit (or `--base <ref>`), adds a worktree at
`.claude/worktrees/severity` inside the primary worktree by default (or `--path <dir>`), copies the
primary worktree's [worker model
configuration](../harness/workers/module.md#concept.workers.model-configuration) into it when there
is one, writes the record and log, and prints it. Git ignores that configuration, so the copy is
the task's own: the task's workers keep the models chosen when it opened, whatever the primary
worktree chooses later, until a command names the task. A copy the file system refuses ends the
open with `config_copy_failed`, naming the worktree and branch left behind and how to remove them. A worktree path inside the primary worktree must be ignored by Git
there, or the open is refused with `worktree_not_ignored`; the installer adds
`.claude/worktrees/` to `.gitignore`. From then on the task's work happens inside that worktree,
with the worktree's own `concorde`, and the host of every Operation run for the task works there.
Parallelism exists only between tasks: none share a worktree, and each runs at most one Operation
at a time.

<a id="concept.tasks.task-record"></a>

The **task record** lives at `.concorde/tasks/<task-id>.json`: identity, goal, Modules, branch,
worktree path, base commit, state, and one entry per run and delivery
([exact fields](contracts.md#contract.tasks.record)). `concorde task list` prints the records
(optionally by `--state`); `concorde task show <task-id>` adds the decision log's path.

The Operation host updates the record through Tasks as a run starts, finishes, and Delivery
commits, adding any `--modules` a run names, so it always lists every Module touched. A second run
while one is going is refused with `task_busy`; one left `running` by a dead host process is marked
`interrupted` at the next run.

<a id="concept.tasks.decision-log"></a>

The **decision log** lives at `.concorde/tasks/<task-id>.decisions.md`. Tasks creates it with a
heading and the goal at open, then only appends escalations; the session working on the task — the
main agent, or the task's task session — appends directly: every uncertainty it decided alone, with
options and reason, and every non-`ok` Operation result and what it did about it. The main agent
reads the log when it reports to the developer at the end of the task.

When it cannot handle an error itself, the session escalates with `concorde task escalate`, naming
the runs, saved refusals or earlier escalations it cannot handle and stating its own
[error chain](../vocabulary.md#concept.concorde.error-chain) link — code, what needs deciding, why
not alone, what it tried, options and recommendation. A task session escalates with
`--by task-session` to the main agent; the main agent's own link, the default, escalates to the
developer and may name a task session's escalation as a cause with `--escalation <n>`. Tasks puts
those errors unchanged under that link as its causes, appends the resulting chain to the record's
escalations and to the decision log (rendered and as JSON), and prints it, so the reader gets one
chain from the question down to where the error started.

<a id="concept.tasks.task-session-start"></a>

For work split into several tasks, the main agent starts a
[task session](../vocabulary.md#concept.concorde.task-session) per task from the primary worktree:

```text
concorde task session severity --main concorde-7d
```

Tasks writes the session's boundary under `.concorde/tasks/severity.session/` — a settings file
and a write hook — starts `claude --bg` in the task worktree with the task-session guidance and
the task's goal, Modules, decision log and the main agent's session name as its first prompt, and
appends the started session to the record. `--dry-run` writes the boundary and prints the command
without starting anything. A task that is closed or failed, a missing worktree, or a Claude Code
that does not report a started background session is refused (`task_closed`, `missing_worktree`,
`session_failed`) with Claude Code's output in the detail.

<a id="concept.tasks.task-state"></a>

A task's **task state** moves forward only:

```d2 illustrative
start: "" {shape: circle; width: 16; height: 16; style.fill: black}
open
active
delivered
closed
failed
start -> open: task open
open -> active: first Operation run
active -> delivered: delivery commit
delivered -> active: a writing Operation starts
delivered -> closed: task merge, or task close --merged
open -> closed: task close --completed
active -> closed: task close --completed
delivered -> closed: task close --completed
open -> failed: task close --failed
active -> failed: task close --failed
delivered -> failed: task close --failed
```

A task is **open**, then **active** at its first Operation run. Delivery makes it **delivered**; a
later writing Operation, such as another `implement` after a code review, returns it to active for
another delivery. A task ends in one of two states, and the record keeps the outcome:

- **closed** means the task was ended on purpose because it reached its goal. Merging is the usual
  way: the main agent merges a delivered task, unasked, with `concorde task merge` (below), which
  closes it with outcome `merged`. `concorde task close <task-id> --merged` closes a task merged
  some other way, and is accepted only when the latest delivery commit is the branch's head, that
  head is in the primary branch, and the worktree is clean. Merging is not the only way to reach a
  goal: a task that tried something out, investigated a question or only needed `understand`
  closes with `--completed --note "<what it achieved>"`, outcome `completed`.
- **failed** means the task did not reach its goal. `--failed --reason "<why>"` records the reason,
  and when an error caused the failure, the error chains too: `--run <run-id>` takes a run's error
  and `--error-file` a saved one, each unchanged. A failure no error caused, such as a wrong
  direction, is declared with `--no-error`; one of the two is required, so whether an error caused
  the failure is never left unsaid.

Closing without a merge refuses uncommitted changes unless `--force`. Closing appends the outcome,
the note and any error chains to the decision log and removes the worktree, keeping the branch,
record and log; closed and failed tasks accept no further run. A worktree with checked-out
submodules, such as the vendored references, is removed too: its submodules are deinitialized
first, which refuses a submodule with local changes unless `--force`, and only then is the worktree
removed.

<a id="concept.tasks.merge-lock"></a>

Several main sessions may work in one project, each entering a task worktree of its own and
returning to the primary worktree to merge. Two merges at once would interleave in the one
primary checkout, so the main agent merges with one command:

```text
concorde task merge severity
```

Tasks takes the **merge lock** of the primary worktree, waiting for it up to `--wait` seconds
(default 300), and holds it to the end. It refuses, before touching anything, a task that could
not be closed as merged apart from not being merged yet (`not_merged`, `dirty_worktree`) and a
primary worktree with uncommitted or untracked paths or a detached `HEAD` (`primary_dirty`). It
then runs `git merge` there. A conflict is aborted and refused with `merge_conflict`, naming the
paths: the conflict is resolved in the task worktree by merging the primary branch into the task
branch, validating and delivering again, never in the primary worktree. After the merge, Tasks
runs the checks in the primary worktree: `concorde validate` of the merged checkout by default, or
exactly the `--check` commands given, such as a project that must build first. A failed check, or
checks that leave uncommitted paths, returns the primary branch with `git reset --keep` to the
commit it had and refuses with `check_failed`, naming the check, its exit status and its log,
`.concorde/tasks/<task-id>.merge.log`. When everything passed, Tasks closes the task as merged
and prints the record with the commits before and after, each check and how long it waited.

The lock is a `flock` held by the command's own process, so no session has to release it or
announce that it is done: the kernel releases it when the process ends, even when it is killed, and
a waiting command wakes as soon as it is free. A command that gives up waiting fails with
`merge_busy`, naming the holder's command, task, process and start time, which the holder writes
into the lock file while it holds it. `concorde task open` and `concorde task close` take the same
lock, so a task is never based on, or closed against, a merge that may still be undone.

Only the main agent opens, merges and closes tasks and starts task sessions, only from the primary
worktree (`not_primary` otherwise); a [worker](../vocabulary.md#concept.concorde.worker) cannot run
them, having no Git access. Every refusal names its code (`task_exists`, `unknown_module`, `invalid_transition`,
`not_merged`, ...), what was refused and why, and changes nothing ([contracts](contracts.md)).

Record, log and state fit together this way:

```d2
store: Task store
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
```

## Design

The task is the isolation unit because Git already isolates branches and worktrees: changes stay in
their own checkout until Delivery commits and the main agent merges, so two tasks can change the
same Module at once, meeting only at merge time where Git reports conflicts — a shared checkout
would instead leak one task's half-finished edits into another's checks.

Task worktrees live under `.claude/worktrees/` of the primary worktree because that is where
Claude Code can switch a session into an existing worktree and back, which is how the main agent
works inside one task at a time. Git ignores the directory there, so a task's checkout never
appears as files of the primary branch; the Workers' deny rules still hide the primary worktree's
other files and the other task worktrees from a worker, since those are siblings of the path to
its own worktree.

A task session's boundary guards against mistakes, not a malicious session, and costs only
generated settings: its Edit and Write tools pass through a hook that allows only the task
worktree and its decision log, and its Bash runs in Claude Code's sandbox writing only the task
worktree, the repository's Git directory (for commits on the task branch), `.concorde/runs/` and
`.concorde/tasks/` (for Operation runs and records) and package caches. Nobody answers permission
prompts in a background session, so it runs in Claude Code's `auto` mode: a classifier approves or
refuses each action instead of asking, an extra check inside the hook and sandbox, which stay the
boundary. `bypassPermissions` would skip that check, and Claude Code starts a background session
in it only after the developer accepted a disclaimer once. A model without `auto` mode would fall
back to asking and stall, so `--model` must name one that has it. Reads stay open, because the
session needs the whole project's context, and so does the network: the settings allow every host
(`allowedDomains` is `*`). Claude Code's sandbox otherwise admits only the hosts a command names,
and a command that did not foresee one fails, sometimes only partly, as when a package manager
falls back to its cache or Git cannot fetch an object of a partial clone. Keeping the network
closed would guard against exfiltration, which is outside what this boundary is for. Claude Code's
sandbox also keeps the repository's `.git/config` and Git's hooks read-only inside the writable Git
directory, since writing them could run code outside the sandbox; a session commits but cannot
register a submodule, so the main agent prepares that before starting it.

Records live in the primary worktree, not the task worktrees: the main agent works there and must
see every task in one place, including ones whose worktree is gone; and a task worktree is exactly
what workers and Delivery commit, so records kept there would be swept into commits.
`.concorde/tasks/` is thus local, Git-ignored state, like `.concorde/runs/` — the evidence bundle
Delivery commits is what travels with the code. Any process finds the primary worktree through
Git's common directory.

Several Operation hosts may update records at once while the main agent reads, so every write is one
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) bound to the
digest it replaces: a concurrent change is detected, Tasks rereads and reapplies if preconditions
still hold, and refuses with `record_conflict` after three attempts. Each task has its own record
file, so tasks never contend.

States only move forward, apart from delivered returning to active, and closing is checked against
Git, not trusted — merged only when Git shows the delivered head inside the primary branch — which
keeps the record honest when a task was merged outside `concorde task merge`.

The merge lock is held by the process doing the merge rather than recorded as an owner that others
wait on and that must wake them: a recorded owner that crashed, was closed or forgot to notify
would leave every waiter stuck, and Claude Code and pi sessions share no messaging channel to
notify each other. A kernel `flock` is released and wakes waiters whatever happens to its holder,
the same way for every kind of session. It only works if the whole critical section runs in one
process, which is why merging, checking, undoing and closing are one command instead of steps the
main agent issues one by one, and why conflicts are resolved in the task worktree: the lock is then
held for the seconds a merge and its checks take, not for however long a resolution takes. Holding
it also for `open` and `close` keeps both from reading a primary branch whose merge might still be
reset. The decision log is free Markdown,
since its readers are the main agent and the developer; Tasks gives it only a fixed place and
lifetime. See the [requirements](requirements.md) and [scenarios](scenarios.md).

Tasks is built as one realization:

```d2
tasks: Tasks {
  store: Task store {
    "src/concorde/tasks/"
    "tests/concorde/tasks/"
  }
}
```

<a id="realization.tasks.store"></a>

The **Task store** realization holds the `concorde task` commands (`cli.py`), the record updates
the Operation host calls (`store.py`), the task-session start with its settings and write hook
(`session.py`, `session_hook.py`), and their tests, run on real Git repositories. It is the
only writer of task records, writing each decision log once, at open; Operations, Validation and
Delivery read and update records through it, relying on Tasks while it relies on none of them.

## Relationships

```d2
tasks: Tasks
spec: Spec core
workers: Workers
tasks -> spec
tasks -> workers
```

- <a id="uses-workers"></a>**Workers** names the file of the [worker model
  configuration](../harness/workers/module.md#concept.workers.model-configuration), which Tasks
  copies into a new task worktree. Tasks relies on it being one untracked file per worktree; it
  never reads or changes its content.
- <a id="uses-spec"></a>**Spec core** provides two things Tasks relies on: its registry, so a
  record never names a Module that doesn't exist at open or when a run adds one; and its
  [file transactions](../spec-tooling/spec/module.md#concept.spec.file-transaction), so every
  record write is complete or absent, bound to the bytes it replaces. Tasks reads the primary
  worktree's registry to open a task (its worktree doesn't exist yet) and the task worktree's for
  later Module checks. If the Specs cannot be loaded, the command is refused and nothing is
  written.
