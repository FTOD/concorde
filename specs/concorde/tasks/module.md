# Tasks

## Purpose

Tasks gives every unit of work the main agent starts its own place: a Git branch, a worktree
checked out on it, a task record and a decision log. The main agent relies on it to run pieces of
work side by side without their changes mixing, to know each task's state, and to keep the reasons
behind choices it made without the developer. The Operation host relies on it to find a task's
worktree and record every run and delivery against it, kept in the primary worktree only. On the
main agent's request it also starts a task session in a task worktree, on the main session's own
agent program, with a boundary confining that session's writes to its task. When the main agent merges a delivered task, Tasks does the
merge into the primary branch under a lock, so several main sessions never merge at once, and
undoes it if the checks that follow fail. Tasks does not decide how work is split, which tasks run
in parallel or when a task is merged, never runs an Operation, never commits on a task branch, and
never interprets the decision log; the main agent and its task sessions do all of that.

## Terminology

| Term | Definition |
| --- | --- |
| Task | One unit of work of the main agent, made of a branch, a worktree checked out on it, a task record and a decision log. |
| Task record | The JSON file in the primary worktree that holds a task's identity, goal, Modules, branch, worktree path, base commit, state, Operation runs, deliveries, escalated error chains, started task sessions and, when a workflow runs in the task, its steps and reports. |
| Decision log | The Markdown file next to a task record in which the session working on the task writes the choices it made without the developer, and to which escalations are appended. |
| Task state | The stage of a task's life: open, active, delivered, then closed when the task reached its goal (merged or completed) or failed when it did not. |
| Session round | One headless run of a pi task session, from its prompt (the task at the start, or the main agent's answer) to its session report, a failure or a stop; a pi task session is a sequence of rounds on one pi session file. |
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

A task may also run a [workflow](../workflows/module.md), which presets the Operations it runs.
Workflows then records in the task record the workflow's name, each step key with its run (or,
for a step that could not start, its error) and whether a later rerun superseded it, and each
report, and appends every report to the decision log. A task runs at most one workflow:
a step naming another is refused with `workflow_conflict`, and a key already recorded for another
Operation with `step_conflict`. Tasks keeps these entries but never interprets them.

<a id="concept.tasks.decision-log"></a>

The **decision log** lives at `.concorde/tasks/<task-id>.decisions.md`. Tasks creates it with a
heading and the goal at open, then only appends escalations and workflow reports; the session working on the task — the
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
[task session](../vocabulary.md#concept.concorde.task-session) per task from the primary worktree.
A task session runs on the main session's own agent program, which Tasks reads from the
environment as Workers reads the default [worker backend](../harness/workers/module.md#concept.workers.backend)
(`CONCORDE_CLIENT`, `CLAUDECODE=1`, pi's session variables); a command started from neither is
refused with `client_unknown`, naming each variable it looked at. It never runs on the other
program: a main agent that does not split its work carries the task out itself, so a task session
is the main agent's own role at a smaller scale and keeps its program and configuration.

```text
concorde task session severity --main concorde-7d      # start one
concorde task session severity --answer "<answer>"     # pi: start the next round
concorde task session severity --stop                  # pi: stop the running round
```

**In Claude Code**, Tasks writes the session's boundary under `.concorde/tasks/severity.session/` —
a settings file and a write hook — starts `claude --bg` in the task worktree with the task-session
guidance and the task's goal, Modules, decision log and the main agent's session name as its first
prompt, and appends the started session to the record. `--main` is required. `--dry-run` writes the
boundary and prints the command without starting anything. A task that is closed or failed, a
missing worktree, or a Claude Code that does not report a started background session is refused
(`task_closed`, `missing_worktree`, `session_failed`) with Claude Code's output in the detail.
`--answer` and `--stop` are refused (`invalid_input`): a Claude Code task session receives the main
agent's answers through SendMessage and is stopped with `claude stop`.

<a id="concept.tasks.session-round"></a>

**In pi**, which has neither background sessions nor messages between sessions, a task session is
a sequence of **session rounds** on one pi session file. Tasks writes the boundary under
`.concorde/tasks/severity.session/` — the task-session extension `boundary.ts` with the task's paths
embedded, beside the path decisions it shares with the Workers' [permission
extension](../harness/workers/module.md#concept.workers.permission-extension) — and starts a
detached supervisor process that runs one round: `pi -p --mode json --approve` in the task worktree
with the developer's own pi configuration (packages, extensions, settings, credentials and context
files, and the task worktree's project resources, which `--approve` trusts for that run), the
boundary loaded with `-e`, the session file under `pi/` of that directory, and `--model` when
given. The first round's prompt is the task-session guidance for pi followed by the task's goal,
Modules and decision log; `--main`, when given, is only recorded. A round ends when the session
calls `concorde_report` with its [session report](contracts.md#contract.tasks.session-report), when
pi exits without one, or when `--stop` ends it. Meanwhile the supervisor keeps the round's
progress file `status.json` in that directory current — the round, its phase and the session's
latest tool call — and writes pi's event stream and standard error beside it. It then records the
round's outcome in the task record:

| Outcome | When |
| --- | --- |
| `delivered` | the report says delivered and names a delivery commit the task record holds |
| `escalated` | the report says escalated and names escalations the task record holds with the level `task-session` |
| `failed` | pi exited without a report, or the report names a commit or an escalation the record does not hold; the round's `error` is a link naming pi's exit code, stop reason and error message, the logs, and each mismatch |
| `stopped` | `--stop` ended the round |

The main agent answers an escalation, or asks for more after a delivery, with `--answer`: Tasks
starts the next round on the same session file, so the session continues with its whole context and
the answer as its prompt. `--answer` is refused while a round runs (`session_busy`) or when the task
has no pi session (`no_session`), and `--stop` when no round runs (`session_idle`). A start while a
round runs is refused with `session_busy`; after the last round ended, a start begins a new session.
`--dry-run` writes the boundary and prints the command without starting anything. A task that is
closed or failed, a missing worktree, a missing program (`pi`, and on Linux `bwrap` and `socat`) or
sandbox-runtime package, or a supervisor that does not start is refused (`task_closed`,
`missing_worktree`, `session_failed`), naming everything that is missing, and leaves the record
unchanged.

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

A task session's boundary guards against mistakes, not a malicious session. In Claude Code it
costs only generated settings: its Edit and Write tools pass through a hook that allows only the task
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

A pi task session keeps the developer's pi configuration because it does the main agent's work at a
smaller scale: an isolated configuration, such as a worker gets, would give it other tools and
instructions than the main agent that would otherwise do the task. Its boundary is loaded on top of
that configuration. The task-session extension intercepts every `write` and `edit` call and blocks
one whose path, resolved as pi resolves it, is neither inside the task worktree nor the decision log,
naming the task worktree; and it rewrites every `bash` command to run inside sandbox-runtime with
the same writable paths and the same open network as the Claude Code session's sandbox. It
intercepts the tools rather than replacing them, so the developer's own extensions keep theirs;
tools other extensions add, such as MCP tools or a formatter that writes files, are outside this
boundary, as MCP tools are outside the Claude Code session's write hook. pi has no counterpart of
Claude Code's `auto` classifier, so the extension and the sandbox are the whole boundary, which is
enough for what it guards against. Concorde's main-session extension, which the task worktree may
load as a project resource, stays inactive when `CONCORDE_TASK_SESSION` is set, so a task session
neither starts background runs nor watches the project's runs as a main session does.

Rounds stand in for messages because pi sessions share no channel and a headless `pi -p` ends when
its agent stops: the session reports once per round through a tool whose arguments follow a
contract, and the main agent's answer starts the next round with `--session-id` on the same session
file. The report is checked against the task record rather than trusted, so a delivery or an
escalation the record does not hold makes the round `failed`. The supervisor is detached from the
command that started it, so closing the main session never ends a round, and a main session that
starts again finds the running rounds from their progress files.

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
(`session.py`, `session_hook.py`), the pi task session's rounds and supervisor (`pi_session.py`)
with its boundary extension and path decisions (`pi_session.ts`, `pi_session_policy.ts`), and their
tests, run on real Git repositories with a fake `pi`; the path decisions also run under Node. It is the
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
  never reads or changes its content. Tasks also takes from Workers how the main session's program
  is read from the environment ([worker backend](../harness/workers/module.md#concept.workers.backend)),
  where the sandbox-runtime package is installed and how pi resolves a tool's path, which the
  [permission extension](../harness/workers/module.md#concept.workers.permission-extension)'s path
  decisions implement and the pi task session's boundary reuses.
- <a id="uses-spec"></a>**Spec core** provides two things Tasks relies on: its registry, so a
  record never names a Module that doesn't exist at open or when a run adds one; and its
  [file transactions](../spec-tooling/spec/module.md#concept.spec.file-transaction), so every
  record write is complete or absent, bound to the bytes it replaces. Tasks reads the primary
  worktree's registry to open a task (its worktree doesn't exist yet) and the task worktree's for
  later Module checks. If the Specs cannot be loaded, the command is refused and nothing is
  written.
