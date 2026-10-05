# Main session requirements

What the [main-session guidance](module.md) must tell the
[main agent](../../glossary.json#concept.main-agent) and
[task sessions](../../glossary.json#concept.task-session), and what holds for the sessions it
guides. Most are obligations on the content of the guidance. A deterministic check establishes what
the rendered guidance says. Such a check cannot establish whether a model follows it. The
requirements on owners and on what a session holds in its context are obligations on runtime
behaviour. Checks compare that behaviour against what Concorde records and installs rather than
against the guidance's text. The [scenarios](scenarios.md) show the intended behaviour.

## Working method

### req.main-session.tasks-own-changes — Changes run in tasks

The guidance SHALL tell the main agent to make every [Spec](../../glossary.json#concept.spec)
meaning or code behaviour change in a task, never in the primary worktree except an approved
[small change](#req.main-session.small-change).

Besides such a change, only these changes are made in the primary worktree:

- Housekeeping that regenerates derived files, such as the registry mirror after a merge.
- The commit of the worker configuration alone
  ([A model change for future tasks is committed alone](#req.main-session.model-change-commit)).

### req.main-session.small-change — A small change needs the developer's approval

The guidance SHALL tell the main agent that it may make a very small change directly in the primary
worktree only after all these conditions hold:

- The main agent said what it would change.
- The main agent said why the change is small.
- The developer approved that specific change.

Examples are:

- A typo.
- A one-line fix.
- A wording correction.

Without that approval the change runs in a task like any other.

### req.main-session.worktree-own-concorde — A task runs its worktree's Concorde

The task-session guidance SHALL tell a task session to run every `concorde` command that works on the
task's workspace, such as `spec-validation`, `build`, `run <operation>`, `task-validation` and
`delivery`, as the task worktree's own `concorde` command, from the task worktree, never as the
primary worktree's.

That command reads these items of the task worktree, which only the task branch holds:

- The task worktree's [workspace binding](../../glossary.json#concept.workspace-binding).
- Specs.
- The [Protocol copy](../../glossary.json#concept.protocol-copy).
- Checks.

[Distribution](../../distribution/module.md) determines which Framework code the command runs.
Unless the task reinstalled Concorde in its worktree, the command in an installed project ordinarily
runs the installed Framework shared with the primary worktree. In Concorde's own source checkout,
the command runs the task branch's code. The commands that manage tasks are the exception. Only from
the primary worktree, [Tasks](../tasks/module.md) performs these actions:

- Opens tasks.
- Merges tasks.
- Closes tasks.
- Starts task sessions.

Elsewhere, Tasks refuses those commands with `not_primary`.

### req.main-session.every-task-delegated — Every task is worked by a task session

The guidance SHALL tell the main agent to start a
[task session](../../glossary.json#concept.task-session) with `concorde task session` for every
task, even a single one.

### req.main-session.no-work-in-task-worktree — The main agent never works inside a task worktree

The guidance SHALL tell the main agent never to work inside a task worktree itself.

The main agent keeps what needs the whole project or the developer:

- Discussing.
- Opening tasks.
- Merging tasks.
- Closing tasks.
- Starting task sessions.
- Answering task sessions.
- The [unbound runs](../../glossary.json#concept.unbound-run).
- Reporting.
- Issues.
- The worker configuration.

### req.main-session.task-brief — The task brief is recorded before the task session starts

The guidance SHALL tell the main agent to record a task's
[task brief](../../glossary.json#concept.task-brief) in the task's
[decision log](../../glossary.json#concept.decision-log) before starting its task session.

The task brief holds:

- The developer's decisions the task carries out.
- The workflow and its [mode](../../glossary.json#concept.workflow-mode) when one applies.
- What the main agent leaves for the session to decide.

The task brief is not a worker's [brief](../../glossary.json#concept.brief), which an Operation
generates for each worker it launches.

### req.main-session.brief-read-first — A task session reads the decision log first

The task-session guidance SHALL tell a task session to read the task's
[decision log](../../glossary.json#concept.decision-log) before it changes anything.

The log holds the task brief the main agent recorded
([The task brief is recorded before the task session starts](#req.main-session.task-brief)).

### req.main-session.dispatched-named — Dispatched tasks are named to the developer

The guidance SHALL tell the main agent to show the developer the name and a one-line goal of every
[task](../../glossary.json#concept.task) it dispatched to a task session.

With several task sessions running, the names are what the developer follows, asks about or stops a
task by.

### req.main-session.reports-by-name — Reports name the dispatched tasks

The guidance SHALL tell the main agent, whenever it reports on a dispatched task, to name that task
by the name it showed the developer.

### req.main-session.stay-in-primary — The main agent stays in the primary worktree

The guidance SHALL tell the main agent to stay in the primary worktree.

### req.main-session.parallel-by-worktree — Parallelism only between worktrees

The guidance SHALL tell the main agent to run tasks in parallel only in separate worktrees and only
when their Modules and shared files do not overlap.

### req.main-session.background-operations — Runs start in the background

The guidance SHALL tell the main agent to start each unbound run in background Bash.

### req.main-session.task-session-background-runs — A task session starts its runs in the background

The task-session guidance SHALL tell a task session to start in background Bash each
[Operation](../../glossary.json#concept.operation) and
[execution command](../../glossary.json#concept.execution-command) it starts itself, never with
`--detach`.

The task session starts them inside the task worktree
([A task runs its worktree's Concorde](#req.main-session.worktree-own-concorde)) without naming the
task. The task worktree's [workspace binding](../../glossary.json#concept.workspace-binding) tells
the run which task's items it works on:

- Goal.
- Modules.
- Branch.
- Base.

One workspace runs one thing at a time. The background call lives as long as the run it started. A
[workflow step](../../glossary.json#concept.workflow-step) is not such a run. Its
[step agents](../../glossary.json#concept.step-agent) start it through the `workflow_step` tool the
workflow part registers with the server
([Workflows](../../workflows/requirements.md#req.workflows.steps-through-server)). The tool runs the
workflow step as a process of the server and waits for the workflow step there.

### req.main-session.task-session-quiet-before-validation — A task session stops its background commands before validating

The task-session guidance SHALL tell a task session to let every run of its workspace finish and to
stop every other background command it started, confirming each ended, before it validates and
delivers: before `task-validation` or `delivery` where the method part is installed, and before
`task deliver` otherwise.

A run that still runs holds the [workspace lock](../../glossary.json#concept.workspace-lock), which
refuses both commands. Since `delivery` commits every uncommitted change, a command still writing in
the task worktree would decide what the
[delivery commit](../../glossary.json#concept.delivery-commit) holds. A polling loop, which the
guidance forbids anyway ([Waiting never polls](#req.main-session.no-polling)), may never end by
itself.

### req.main-session.task-session-still-during-runs — A task session leaves its worktree alone while a run of it runs

The task-session guidance SHALL tell a task session to leave its task worktree untouched, editing
and committing nothing, from the start of any run of its workspace until that run has ended.

A run's [write audit](../../glossary.json#concept.write-audit) attributes every worktree change to
the run's [workers](../../glossary.json#concept.worker)
([Workers](../../worker-harness/workers/module.md)). Therefore, a change the session makes meanwhile
fails the run as a write of a worker that may only read, or is blamed on its workers. The session's
change thus wastes the run, with its model spend.

### req.main-session.act-on-run-result — Every run result is acted on

The guidance SHALL tell the main agent to act on the
[run result](../../glossary.json#concept.run-result) of every run it starts.

### req.main-session.decision-log — The main agent records its decisions

The guidance SHALL tell the main agent to record every decision it made for a task without the
developer, with its reason, in the task's [decision log](../../glossary.json#concept.decision-log).

The main agent starts none of a task's runs. The task session records their results
([A task session records its decisions and failed runs](#req.main-session.task-session-decision-log)).
The command `concorde task answer` appends the main agent's answers to the task session's reports.
An [unbound run](../../glossary.json#concept.unbound-run) belongs to no task and so to no decision
log. [A failed unbound run reaches the developer whole](#req.main-session.unbound-failure) says what
becomes of its result.

### req.main-session.workflow-report-logged — A workflow result reaches the decision log

The task-session guidance SHALL tell a task session to copy the decisions and problems of a
[workflow result](../../glossary.json#concept.workflow-result) into the task's decision log.

Workflows never writes them into the log. In no-ask mode, they were taken without the developer.

### req.main-session.no-task-questions — Questions need no task

The guidance SHALL tell the main agent which Operations run unbound, in a worktree without a
workspace binding.

Every change still runs in a task ([Changes run in tasks](#req.main-session.tasks-own-changes)).

### req.main-session.unbound-examines-head — An unbound run examines the committed HEAD

The guidance SHALL tell the main agent that an unbound run examines a checkout of its worktree's
`HEAD`, whose commit its result names.

Uncommitted changes of that worktree are not examined.

### req.main-session.unbound-reads-only — An unbound run changes nothing

The guidance SHALL tell the main agent that an unbound run changes no Spec or code.

An unbound run launches only reading workers.

### req.main-session.workflows — Preset tasks run their workflow

The guidance SHALL tell the main agent to have a task that follows a known procedure run through
its [workflow](../../glossary.json#concept.workflow), by naming the workflow, its Module and its
mode in its task brief for the task session to start inside the task worktree.

### req.main-session.workflow-mode — The developer chooses the workflow mode

The guidance SHALL tell the main agent, unless the developer already said, to ask the developer
which [workflow mode](../../glossary.json#concept.workflow-mode) to use.

### req.main-session.workflow-restart — A paused workflow starts again with every answer

The task-session guidance SHALL tell a task session, once the main agent answers, to restart a
workflow that ended `awaiting_decision` with every answer given so far.

A step that finished and is neither answered nor retried returns its recorded run. The answered step
runs again. It supersedes itself and every step recorded after it. Those later steps run anew, as
[Workflows](../../workflows/module.md) states for its
[step keys](../../glossary.json#concept.step-key).

### req.main-session.merge-without-authorization — Delivered tasks are merged

The guidance SHALL tell the main agent to merge a task branch `delivery` committed, without asking
the developer for authorization, using `concorde task merge` from the primary worktree rather than
`git merge`.

[Tasks](../tasks/module.md) holds the [merge lock](../../glossary.json#concept.merge-lock) during
the merge. Tasks runs `concorde spec-validation` of the merged checkout, or exactly the `--check`
commands given. While a `concorde update` is not validated yet, `concorde spec-validation` follows
those commands. When a merge's checks fail, Tasks undoes the merge.

### req.main-session.merge-interrupted — An interrupted merge is finished first

The guidance SHALL tell the main agent, when a `concorde task` command is refused with
`merge_incomplete`, to finish the named task's merge before anything else.

Unless [An unfinished merge that cannot resume is aborted](#req.main-session.merge-abort) applies,
the main agent finishes the merge with `concorde task merge <task> --resume`, which checks the merge
again.

### req.main-session.merge-abort — An unfinished merge that cannot resume is aborted

The guidance SHALL tell the main agent to finish an interrupted merge with
`concorde task merge <task> --abort` when either of these conditions holds:

- The merge commit is no longer the primary branch's head.
- `--resume` answers `not_resumable`.

### req.main-session.merge-diverged — A diverged primary branch goes to the developer

The guidance SHALL tell the main agent to bring a `merge_diverged` refusal to the developer.

The primary branch was changed by hand after the merge. Discarding those commits is the developer's
decision.

### req.main-session.task-session-merge-refusal — A task session passes a merge refusal on

The task-session guidance SHALL tell a task session whose escalation is refused with
`merge_incomplete` or `merge_busy` to send that refusal, unchanged, to the main agent.

A task session has no authority to finish a merge.

### req.main-session.merge-conflict — The task session resolves a merge conflict

The guidance SHALL tell the main agent, when merging a task fails with `merge_conflict`, to have
the task's session merge the primary branch into its task branch.

The session then delivers again
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)).
The main agent merges the task once more. Merging the task into the primary branch stays the main
agent's.

### req.main-session.update-merge — An update reaches the open tasks through their sessions

The guidance SHALL tell the main agent, when a `concorde update` asks to merge the primary branch
into each open task, to have each listed task's session make that merge.

An update that installs a new Protocol copy lists the open tasks
([Distribution](../../distribution/module.md)). Those tasks' worktrees still carry the previous
copy. The main agent answers each listed task's session. If the session ended, the main agent starts
one again. The session then validates again. If the session delivered before, it delivers again
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)).
Merging the task into the primary branch and rebasing stay forbidden to the session.

### req.main-session.task-session-primary-merge — A task session merges the primary branch when asked

The task-session guidance SHALL tell a task session to merge the primary branch into its task
branch when the main agent asks for it after a `merge_conflict` or after a `concorde update`.

The session then resolves the conflicts within the task's goal. The session verifies and commits the
merge. The session validates and delivers again with the applicable commands:

- Where the method part is installed, `task-validation` and `delivery`.
- Otherwise, `task deliver`.

A task not delivered yet goes on with its work after validating. That task delivers when it is done.
This merge is the only merge a task session makes.

### req.main-session.no-polling — Waiting never polls

The guidance SHALL tell the main agent and every task session never to wait by polling for any of
these:

- A run.
- A lock.
- A task session.
- A merge.

### req.main-session.wait-without-turns — Every wait costs no model turns

The guidance SHALL give each wait of the main agent and of a task session a way that costs no model
turns while it lasts.

The ways are:

- Being woken by a background run.
- Being woken by a SendMessage.
- Being woken by a channel event of a wait the session registered.
- One command that blocks until it is done.

The blocking commands are:

- `--wait` of a run and of `concorde task merge`.
- `concorde task wait`.

### req.main-session.project-terms — Sessions use the project's terms exactly

The guidance SHALL tell the main agent and every task session to use each project term exactly as
its glossary entry defines it.

## Owners and session context

### req.main-session.single-owner — Only a run's owner is woken unasked

The end of a run SHALL wake, without any session asking for it, no main session other than its
owner, the session whose background Bash started it.

The consequences for wakes nobody asked for are:

- A run a main session starts wakes that main session alone.
- A run a task session starts belongs to that task session and wakes no main session unasked.
- A run started by a command run by hand wakes nobody unasked.

What a task session reports reaches only the main session its task record names when it reports.
This guarantee covers the wakes nobody asked for. A session that registers a wait with the project
MCP server's `register_wait` asks for its own wake explicitly. The wait can concern any of these,
which the session may not own:

- A run.
- A lock.
- A task.

The server admits that registration as its [contracts](contracts.md#registering-a-wait) document.
The server wakes only the session that registered the wait
([A wait only notifies](#req.main-session.project-mcp-wait-notifies)).

### req.main-session.owner-recorded-by-coordination — Ownership is kept on the main session's side

The guidance and the project MCP server SHALL never take a run's owner from its
[run progress file](../../glossary.json#concept.run-progress-file) or
[run result](../../glossary.json#concept.run-result).

A run's owner is the session whose background Bash started it. The main session a task session
reports to is the `main` its [task record](../../glossary.json#concept.task-record) names.
[Execution](../../execution/module.md) knows nothing of sessions. Execution defines both records.
Its [run result contract](../../execution/contracts.md#contract.execution.run-result) holds no
owner.

### req.main-session.claude-sees-by-query — A main session sees others' work by asking

A main session SHALL learn the state of a task's runs and sessions it does not own only by asking
for it, with nothing unasked pushed into its session.

For the state now, the session asks with `concorde task show <task>`, or the server's `task_show`.
Alternatively, the session registers a wait with `register_wait` to be woken when any of these
happens:

- A run ends.
- A lock is released.
- A task reaches a state.

### req.main-session.terms-in-context — Sessions start with the glossary

In a worktree whose declared glossary can be read, the main agent's session and every task session
SHALL each hold every glossary entry in its context from its first prompt.

The Concorde block of the worktree's `CLAUDE.md` imports the glossary file. Claude Code loads that
file at launch. If a worktree's project declares no glossary, or its declared glossary cannot be
read, the worktree starts its sessions without terms and without an error. Spec validation reports a
declared glossary it cannot read. A [worker](../../glossary.json#concept.worker) is not such a
session. Its context is only its [brief](../../glossary.json#concept.brief), as the
[Harness](../../worker-harness/harness/module.md) describes.

## The project MCP server

### req.main-session.project-mcp-presentation — Queries and short writes answer as their commands

Each tool Coordination registers with the
[project MCP server](../../glossary.json#concept.project-mcp-server) whose
[contracts](contracts.md#tools) row names a `concorde` command SHALL answer and refuse exactly as
that command does when it waits for no lock, from the
[task records](../../glossary.json#concept.task-record), traces and locks of the primary worktree
read afresh for that call, adding no other rule of its own.

Those tools are:

- The query `task_list`.
- The query `task_show`.
- The query `trace_show`.
- The short write `task_open`.
- The short write `task_escalate`.
- The short write `task_rebind`.
- The short write `task_report`.
- The short write `task_answer`.
- The short write `task_close`.
- The short write `task_resolve`.

The Issue tools answer as the Issues command does by the issues part's own
[interface](../../issues/interface.md#mcp-tools). The primary worktree belongs to the repository the
server started in, whichever worktree of the project the server started from.

### req.main-session.project-mcp-record-queries — The other queries present records read-only

The queries `run_result` and `locks` SHALL answer with the result and refuse with the codes their
[contracts](contracts.md#tools) define, from the records and locks of the primary worktree read
afresh for that call, changing nothing.

No `concorde` command answers them in that shape. Where the execution part is installed, the queries
read:

- A run's saved result.
- Its [run lock](../../glossary.json#concept.run-lock).
- Its [run progress file](../../glossary.json#concept.run-progress-file).

The queries also read the holder lines of the merge lock and the workspace locks.

### req.main-session.project-mcp-merge-start — `task_merge` starts the command's merge

Once it holds both locks, `task_merge` SHALL start the same `concorde task merge` the command line
runs, with the task and the `checks`, `resume` or `abort` it was given.

### req.main-session.project-mcp-merge-answer — `task_merge` answers at once with the start

Once it starts the merge, `task_merge` SHALL answer at once with the start its
[contracts](contracts.md#starting-a-merge) define instead of the merge's result.

The merge's own result and refusals are the command's. They arrive later in either form:

- A `merge_ended` channel event.
- The output file, once the returned `concorde task wait <task> --merge` returns.

Before the start, only these refuse the call:

- Its arguments.
- A busy lock ([The server never waits for a lock](#req.main-session.project-mcp-no-wait)).
- A failed start.

### req.main-session.project-mcp-merge-output — A merge's output stays with its attempt

`task_merge` SHALL save the started merge's standard output and error in its attempt node's folder
in the task's trace and, without a channel, return `concorde task wait <task> --merge` as the wait
command.

The merge may outlive the server. The close that ends the merge removes the task's workspace lock
before the merge has written its answer. The attempt's folder moves with the task to the history.
Whatever became of the server, `task_show` and `trace_show` find that folder from the task. The
merge-end wait returns only once that answer is complete
([Tasks](../tasks/requirements.md#req.tasks.merge-attempt-lock)).

### req.main-session.project-mcp-wait-as-command — `register_wait` waits for what the command waits for

`register_wait` SHALL wait for exactly what the matching `concorde task wait` waits for.

### req.main-session.project-mcp-wait-answer — `register_wait` answers with its registration

`register_wait` SHALL answer at once with the registration its
[contracts](contracts.md#registering-a-wait) define.

When what it waits for already happened, its answer carries the value that command would print.

### req.main-session.project-mcp-no-wait — The server never waits for a workspace or merge lock

A tool of the server that needs a [workspace lock](../../glossary.json#concept.workspace-lock) or
the [merge lock](../../glossary.json#concept.merge-lock) SHALL be refused at once, with
`workspace_busy` or `merge_busy`, when another process holds it, naming the lock file and the
holder's command, process, start time, Claude Code session and task as the holder line gives them.

The tool takes those locks without waiting. A
refused call releases every lock it took. A task's record lock is no such lock. Every change of a
task record holds its record lock for that one update only. For that reason, a short write waits for
the record lock as the command does, briefly. At worst, the short write waits while a close asks
Claude Code about the task's sessions. The short write is not refused for contention that ends
within moments. Examples of short writes are:

- `task_report`
- `task_answer`
- `task_rebind`
- `task_escalate`

### req.main-session.project-mcp-handover — A granted lock belongs to the work

When `task_merge` has both locks, the server SHALL hand them to the merge process it starts, so
that they are released exactly when that process ends, however it ends, and never by the server or
its session ending.

The call's process follows this sequence:

- It takes both locks.
- It answers.
- It becomes `concorde task merge` in a session of its own, keeping both locked descriptors.

The server itself never holds them.

### req.main-session.project-mcp-wait-notifies — A wait only notifies

`register_wait` SHALL NOT take, keep or hand over any lock for the session it wakes.

When what it waits for already happened, it answers at once. Otherwise, with a channel, it wakes its
session with one channel event when what it waits for happens or ends another way. In that case, it
watches by blocking on the lock or on the operating system's notice of its changes, never by
polling.

### req.main-session.project-mcp-wait-ends — A wait ends with its server

The process that watches a registered wait SHALL end when the server ends, however the server
ends.

A wait wakes only the session whose server registered it, so once that server is gone nobody is left
to wake. A wait for something that never happens would otherwise block forever.

### req.main-session.project-mcp-fallback — Without a channel the server says so

When the server does not know its session to listen to it as a channel, `task_merge`, and
`register_wait` for something that has not happened yet, SHALL say so and return the
`concorde task wait` command that returns when the same thing happens, for background Bash.

A `register_wait` for something that already happened answers at once with that answer, channel or
not ([`register_wait` answers with its registration](#req.main-session.project-mcp-wait-answer)).

For `task_merge` that is `concorde task wait <task> --merge`, the merge-end wait. That wait returns
once the merge writes its whole answer. It is not the wait for the task's
[workspace lock](../../glossary.json#concept.workspace-lock). The close that ends the merge removes
that lock before the merge writes its whole answer
([A merge's output stays with its attempt](#req.main-session.project-mcp-merge-output)).

### req.main-session.project-mcp-errors — Every refusal is an error link

Every refusal of the server SHALL be an [error chain](../../glossary.json#concept.error-chain)
link: the refusing component's own link unchanged, or the server's own `component` link with its
reason, explanation and options.

### req.main-session.project-mcp-guidance — The guidance says how to start with a channel

The guidance SHALL tell the main agent how to start its session with the server as a channel.

### req.main-session.project-mcp-preview — The guidance says channels may be unavailable

The guidance SHALL tell the main agent that channels are a research preview that may be
unavailable.

### req.main-session.project-mcp-preferred — The guidance prefers the server to waiting commands

The guidance SHALL tell the main agent to prefer `task_merge` and `register_wait` to commands that
wait.

### req.main-session.project-mcp-no-channel — Without a channel the returned command runs in the background

The guidance SHALL tell the main agent to run the `concorde task wait` command that `task_merge` or
`register_wait` returns in background Bash when no channel is available.

### req.main-session.project-mcp-ask-again — A woken session asks for the lock again

The guidance SHALL tell the main agent that a lock is never handed to a session woken for it, which
asks for it again and may be refused again.

### req.main-session.project-mcp-source-of-truth — The commands stay the source of truth

The guidance SHALL tell the main agent that the `concorde` commands stay the source of truth.

The operating system's lock is the same whichever path takes it. Everything the server does not
present stays a command.

## Worker models

### req.main-session.developer-chooses-models — The developer chooses worker models

The guidance SHALL tell the main agent to change worker models only when the developer asks.

### req.main-session.worker-configuration-first — The worker configuration comes before any worker

The guidance SHALL tell the main agent that no worker runs without the tracked
[worker configuration](../../glossary.json#concept.worker-configuration).

The installer does not write it.

### req.main-session.worker-configuration-created — A missing worker configuration is created with the developer

The guidance SHALL tell the main agent, when the project has no worker configuration, to create it
with the enabled models and default model the developer names.

### req.main-session.worker-configuration-committed — A new worker configuration is committed before any Operation

The guidance SHALL tell the main agent to commit a worker configuration it created alone on the
primary branch before any Operation runs.

### req.main-session.model-map-names — Worker models are project model names

The guidance SHALL tell the main agent that the worker configuration names models by project model
names, which the developer's untracked [model map](../../glossary.json#concept.model-map) resolves
to each program's local id.

### req.main-session.model-map-developers — The model map is the developer's

The guidance SHALL tell the main agent to change the developer's
[model map](../../glossary.json#concept.model-map) only when the developer asks or agrees.

The map belongs to the developer's machine. The map is never committed.

### req.main-session.model-change-method — Model changes edit the tracked configuration

The guidance SHALL tell the main agent to change worker models by editing the tracked
[worker configuration](../../glossary.json#concept.worker-configuration) directly.

There is no editor. The edit preserves unrelated entries.

### req.main-session.model-change-commit — A model change for future tasks is committed alone

The guidance SHALL tell the main agent to commit a worker configuration change meant for future
tasks as follows:

- Alone.
- Directly on the primary branch.
- Never while a merge is unfinished.

That commit is one of the changes the main agent may make in the primary worktree outside a task,
as [Changes run in tasks](#req.main-session.tasks-own-changes) lists them.

### req.main-session.task-models-kept — A task's own model change merges with it

The guidance SHALL tell the main agent that a task may change its own worker configuration while it
works and that the change reaches the primary branch when the task merges.

## Escalation

### req.main-session.batched-decisions — Decisions go up together

The task-session guidance SHALL tell a task session to gather every decision its task needs that is
not its own and escalate them together in one report, instead of waiting for an answer in the
middle of its work.

A task never asks the developer in place: the developer is asked only from the main session.

### req.main-session.batched-answers — Answers go back together

The guidance SHALL tell the main agent to put all the decisions a task session escalated together
that its authority does not cover to the developer at once.

### req.main-session.answer-once — The session is answered once

The guidance SHALL tell the main agent to answer a task session's escalations once, with every
answer.

### req.main-session.ordinary-decisions — Ordinary questions are decided

The guidance SHALL tell the main agent to decide ordinary questions itself.

Ordinary questions are those without major impact, such as:

- Naming.
- Internal structure.
- Task order.
- A clarified re-run.
- Splitting a task.

Recording those decisions is the obligation of
[Decisions are recorded](#req.main-session.decision-log).

### req.main-session.report-decisions — Decisions taken for the developer are reported

The guidance SHALL tell the main agent to report to the developer the decisions it took on the
developer's behalf.

Its report closes each piece of work with:

- What was merged.
- What was decided.
- What is still open.

### req.main-session.escalation-policy — Only major decisions reach the developer

The guidance SHALL tell the main agent to ask the developer before acting on a decision with major
impact.

The main agent decides the other questions of the work itself
([Ordinary questions are decided](#req.main-session.ordinary-decisions)). Beyond such decisions, the
developer is still asked for what other requirements name:

- The [workflow mode](#req.main-session.workflow-mode).
- The models of a [missing worker configuration](#req.main-session.worker-configuration-created).
- The approval of a [small change](#req.main-session.small-change).

A decision has major impact when any of these conditions applies:

- It changes what a Module promises or the project's direction.
- It contradicts an earlier developer decision.
- It discards work or data.
- It cannot be undone by an ordinary revert.
- It touches security or credentials.
- It needs more resources than the developer set.

### req.main-session.read-chain — The whole error chain is read

The guidance SHALL tell the main agent to read the whole error chain of a result that is not `ok`
before deciding.

### req.main-session.extend-chain — An escalation extends the chain

The guidance SHALL tell the main agent to escalate an error of a task's runs it cannot handle with
`concorde task escalate`, adding its own link on top of the chain instead of summarizing it.

### req.main-session.spec-tooling-errors — A Spec tooling error is translated before it is escalated

The guidance SHALL tell the main agent and task sessions to translate a refused Spec tooling
command's error record before escalation:

- Into a `component` link of the [error chain](../../glossary.json#concept.error-chain).
- With the record's causes kept as nested links.

Examples of Spec tooling's commands are:

- `spec-validation`
- `registry`
- `grant`
- `build`

Spec tooling's commands and the Spec MCP server refuse with Spec tooling's own
[error record](../../spec-tooling/spec/errors.md#contract.spec.error), not with a link.

When a file holds such a record, `concorde task escalate` refuses it with `invalid_error`. When a
Module receives such a record and cannot handle it,
[Tracing](../../kernel/tracing/contracts.md#where-links-appear) has the Module translate it.

### req.main-session.unbound-failure — A failed unbound run reaches the developer whole

The guidance SHALL tell the main agent to show the developer the whole rendered
[error chain](../../glossary.json#concept.error-chain) of an unbound run that is not `ok`.

An unbound run belongs to no task, so no decision log or escalation records it.

### req.main-session.unbound-failure-task — Work from a failed unbound run carries its chain

The guidance SHALL tell the main agent, when the failure of an unbound run leads to work, to open a
task for that work.

### req.main-session.unbound-failure-escalated — The task escalates with the run's result file

The guidance SHALL tell the main agent to escalate in the task opened for a failed unbound run,
using `concorde task escalate` naming the run's result file,
`.concorde/unbound/<run-id>/result.json`, with `--error-file`.

`--run` names only runs of the task's own [workspace](../../glossary.json#concept.workspace), and an
unbound run has none.

## Task sessions

### req.main-session.task-session-guidance — A task session works only inside its task

The task-session guidance SHALL tell a task session to work only inside its task.

### req.main-session.task-session-decides — A task session decides ordinary questions

The task-session guidance SHALL tell a task session to decide ordinary questions within the task's
goal and Modules itself.

### req.main-session.task-session-decision-log — A task session records its decisions and failed runs

The task-session guidance SHALL tell a task session to record in its task's
[decision log](../../glossary.json#concept.decision-log) the following:

- Every result that is not `ok` of the runs the task session starts.
- Every decision the task session made without the developer, with its reason.

Most of what the log keeps is seen by the task session alone because the task session:

- Starts the task's runs.
- Decides the task's ordinary questions
  ([A task session decides ordinary questions](#req.main-session.task-session-decides)).

### req.main-session.task-session-escalates — A task session escalates the rest

The task-session guidance SHALL tell a task session to escalate every other question to the main
agent with its own link on top of the [error chain](../../glossary.json#concept.error-chain).

A task session records every escalation and then sends them together with SendMessage
([Decisions go up together](#req.main-session.batched-decisions)).

### req.main-session.task-session-prepares-workers — A task session prepares the workers' environment

The task-session guidance SHALL tell a task session to create every new implementation file the
work needs outside the directories its Modules' realizations bind, with the least content its
format needs to be valid, before it launches the [worker](../../glossary.json#concept.worker) that
fills it.

No worker creates such a file because:

- A realization binds only files that exist.
- A worker writes only bound files and new files inside bound directories.

A new Spec document is not such a file.
[Specification](../../method/specification/module.md#new-and-deleted-documents) creates each
document a `specify` worker proposes, empty and registered in its Module's `owns`. When a proposed
path already exists, Specification refuses it. Therefore, a session that created the document first
would make the proposal fail.

### req.main-session.task-session-binds-new-files — A task session binds the files it created

The task-session guidance SHALL tell a task session to add each implementation file it created for a
worker to the `entries` of the right realization of its [Module](../../glossary.json#concept.module)
before launching the worker that fills it.

It checks the binding with [Spec core](../../spec-tooling/spec/module.md)'s
`concorde spec-validation` and commits the file and the binding together.

### req.main-session.task-session-plan-review — A plan review is optional

The task-session guidance SHALL present `plan_review` as optional.

Nothing requires it before `task-validation` or `delivery`. When its task brief asks for it or a
change deserves a second reading, a session runs it. The session writes the plan itself. The session
keeps the plan where `delivery` does not commit it. The run keeps its own copy of the plan it
reviewed.

### req.main-session.task-session-plan-review-iterates — A task session answers every finding until the plan is accepted

The task-session guidance SHALL tell a task session that runs `plan_review` to answer every finding
of one iteration with `--accept` or `--reject` in the next run, with the previous run as `--input`,
until the verdict is `accepted`.

[Understanding](../../method/understanding/module.md) refuses a next run that leaves
a finding of the previous one unanswered.

### req.main-session.task-session-plan-review-disagreement — A continuing disagreement is escalated

The task-session guidance SHALL tell a task session to escalate a finding the reviewer maintains
after the session rejected it, and that the session still rejects, instead of running `plan_review`
again on it.

Such a finding is a disagreement the session cannot settle within its task. When the session now
accepts a maintained finding's renewed reasoning, the session answers with `--accept`. For such an
accepted finding, the session revises the plan, like any other. The session states the answer it
receives in its next run.

### req.main-session.task-session-workflow — A task session runs workflows in its task brief's mode

The task-session guidance SHALL tell a task session to run a
[workflow](../../glossary.json#concept.workflow) in the
[mode](../../glossary.json#concept.workflow-mode) its task brief names, or in interactive mode when
the task brief names none.

### req.main-session.task-session-workflow-decisions — A task session reports a workflow's decisions

The task-session guidance SHALL tell a task session to give the decisions of a
[workflow result](../../glossary.json#concept.workflow-result) in its own report to the main agent.

### req.main-session.task-session-workflow-failure — A task session escalates a failed workflow with its result

The task-session guidance SHALL tell a task session to escalate a
[workflow result](../../glossary.json#concept.workflow-result) that is not `ok` and that it cannot
repair within the task, naming the saved workflow result with `--error-file`.

A workflow that ended `awaiting_decision` is such a result: its chain names each pending
[decision point](../../glossary.json#concept.decision-point) with its options and recommendation.
The session escalates it with the task's other decisions
([Decisions go up together](#req.main-session.batched-decisions)). The main agent answers them all
at once ([The session is answered once](#req.main-session.answer-once)). The session starts the
workflow again
([A paused workflow starts again with every answer](#req.main-session.workflow-restart)).

### req.main-session.task-session-workflow-major — A task session escalates a workflow's major decision alone

The task-session guidance SHALL tell a task session to escalate a decision of major impact that a
no-ask workflow took naming no run or file.

Such a decision carries no error, so the session's own link is the whole chain the main agent puts
to the developer.

### req.main-session.task-session-reports — A task session reports its end

The task-session guidance SHALL tell a task session to report to the main agent when it has
delivered the task or cannot go further.

### req.main-session.task-session-report-recorded — A task session records every report before sending it

The task-session guidance SHALL tell a task session to record every report to the main agent with
`concorde task report` before it messages the main agent.

The recorded report is what the main agent reads when the message was lost.

### req.main-session.task-session-report-addressee — A report goes to the session the task record names

The task-session guidance SHALL tell a task session to message each report to the main agent's
session that `concorde task report` printed for it.

At each report, the name comes from the task record rather than the first prompt because a Claude
Code session's name does not survive a restart or resume.

### req.main-session.task-session-report-resent — A lost report is sent again after the rebind

The task-session guidance SHALL tell a task session whose message reaches no session of the printed
name to wait in background Bash with `concorde task wait <task> --rebound <that name>` and send the
same report to the name it returns.

### req.main-session.answers-recorded — The main agent records its answers

The guidance SHALL tell the main agent to record its answer to a task session's reports with
`concorde task answer` before it sends the answer.

### req.main-session.answers-name-reports — Every answer names the reports it answers

The guidance SHALL tell the main agent to name, in every answer it sends a task session, the numbers
of the reports it answers.

The number is the one `concorde task report` gave the report. The command `concorde task answer`
recorded the answer under that number, so a session can tell an answer it already acted on.

### req.main-session.task-session-answer-once — An answer already acted on changes nothing

The task-session guidance SHALL tell a task session to treat an answer to a report it already acted
on, matched by the report's number, as nothing to do.

A main agent that reconciles after a restart sends recorded answers again
([A recorded answer is sent again after a restart](#req.main-session.reconcile-resend-answer)),
since it cannot tell whether one was sent.

### req.main-session.reconcile-after-restart — A main agent whose name changed lists its tasks first

The guidance SHALL tell the main agent, when ListAgents reports another name for its session than it
gave its tasks, to list before anything else the tasks not ended that still name the former one.

An ended task cannot be rebound. Because the task's end answered its reports, the task has no report
left unanswered. Therefore, listing the task would only look like work pending.

### req.main-session.reconcile-rebind — Each listed task is rebound

The guidance SHALL tell the main agent to rebind each task it listed after its name changed to its
current name with `concorde task rebind`, before anything else.

A task session whose message was lost waits for that rebind. Because its report is already in the
task record, the rebind wakes the task session.

### req.main-session.reconcile-unanswered — The listed tasks' unanswered reports are read

The guidance SHALL tell the main agent to read the unanswered reports of each task it listed after
its name changed before anything else.

They tell the main agent what it missed while its name did not reach it.

### req.main-session.reconcile-resend-answer — A recorded answer is sent again after a restart

The guidance SHALL tell the main agent to resend the latest recorded answer to each listed task's
task session, naming the reports it answers, under these conditions:

- The main agent listed the task after its name changed.
- The task's last report has an answer.

The restart may have come after `concorde task answer` recorded the answer and before SendMessage
sent it. The session would then wait for an answer that the task record shows as given. A session
that already received the answer changes nothing
([An answer already acted on changes nothing](#req.main-session.task-session-answer-once)).

### req.main-session.task-session-never-merges — A task session never merges or closes its task

The task-session guidance SHALL tell a task session never to merge its task into the primary
branch or close its task.

When the main agent asks after `merge_conflict` or `concorde update`, the task session makes its one
merge: the primary branch into its task branch
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)).

### req.main-session.task-session-keeps-branch — A task session keeps its task branch

The task-session guidance SHALL tell a task session never to rebase or switch branches.

The task worktree stays checked out on the task branch that `task open` created.

## Issues

### req.main-session.issues-recording — A session inspects before it records

The guidance SHALL tell the main agent and task sessions to read the concerned Module's following
Issues before recording a problem, through `issue_list`'s filters rather than the whole project's
list:

- Its open Issues.
- Its closed Issues when the problem may have been fixed before.

The whole project's list outgrows a tool result.

### req.main-session.issues-append — A tracked problem is appended to its Issue

The guidance SHALL tell the main agent and task sessions to append a report to the
[Issue](../../glossary.json#concept.issue) that already tracks a problem instead of creating
another.

Repeating a creation creates another Issue. So that an Issue escalated by its identity alone can be
acted on, every report carries:

- A complete description.
- Complete impact.
- Complete basis.
- Complete evidence.
- Its tier.
- Its severity.

### req.main-session.issues-through-server — Sessions manage Issues through the project MCP server

The guidance SHALL tell the main agent and task sessions to read and write Issues through the
project MCP server's Issue tools.

The tools record the session that called them, which the `concorde issues` command cannot know. The
command answers the same way and stays the path for:

- The main agent.
- A task session's shell.
- The runs a session starts.

### req.main-session.issues-tiers — A task session fixes the Issues its tier lets it

The guidance SHALL tell a task session that it may fix an `obvious-fix` or a `preferred-fix` Issue
itself.

The tier decides who fixes an Issue. A review Operation only reports. Fixing is later work of a
task. A `suggestion` blocks nothing.

### req.main-session.issues-preferred-fix-reported — The chosen fix of a `preferred-fix` Issue is reported

The guidance SHALL tell a task session to report to the main agent the fix it chose for each
`preferred-fix` Issue it fixed.

### req.main-session.issues-decision-needed — A `decision-needed` Issue is escalated

The guidance SHALL tell a task session to escalate a `decision-needed` Issue, named by its identity,
instead of settling it.

### req.main-session.issues-severity — Work starts from the most severe Issues

The guidance SHALL tell every session that records an Issue to give each report one of the
[severities](../../glossary.json#concept.issue-severity) `critical`, `high`, `medium` and `low`,
saying what each means, and the main agent to choose which Issues a task takes up from the open
Issues listed by severity, most severe first.

The severity says how much a problem matters, never who fixes it. The tier decides who fixes it.

### req.main-session.review-issues — A review's Issues are handled by their tier

The guidance SHALL tell a task session to handle the Issues a review Operation reports by their tier
in later work of its task.

### req.main-session.review-resolved-closed — An Issue a review found resolved is closed

The guidance SHALL tell a task session to close each Issue a review Operation lists as resolved:
through its task when the task fixed it, and otherwise as `resolved` with the review's run as
evidence.

The review itself never closes one.

### req.main-session.module-code-review — The guidance names the Module review

The guidance SHALL tell the main agent and a task session that `code_review --scope module` judges
each named Module's whole code against all of its Specs, and when to use it.

The guidance names a whole-Module check in these cases:

- After a large change.
- For code written before its Specs or by an earlier version.
- For a project just adopted.

### req.main-session.issues-close-with-merge — A fixed Issue closes with its task's merge

The guidance SHALL tell the main agent to name the Issues a task fixes in the task, so that the
task's merge closes them.

The following task actions change no Issue:

- Starting a task.
- Fixing a task.
- Delivering a task.

A task that ends without merging closes none.

### req.main-session.issues-own-failures — A failure of the Issue system is never an Issue

The guidance SHALL tell the main agent and task sessions never to report a failure of the Issue
system as an Issue.

An Issue system that failed cannot be trusted to record its own failure.

### req.main-session.issues-failure-chain — A task carries an Issue-system failure as its error chain

The guidance SHALL tell a session whose Issue tool or command failed for a task to carry the
failure's [error chain](../../glossary.json#concept.error-chain) in that task's decision log and
escalation.

### req.main-session.issues-failure-no-task — Without a task the developer sees the failure whole

The guidance SHALL tell the main agent to show the developer at once the whole error chain of an
Issue-system failure it met for no task.

The decision log and the escalation belong to a task. An Issue tool or command needs no task, so a
failure met without a task has no record to carry it. The main agent opens a task only when the
failure leads to work.

### req.main-session.issues-recovery — The guidance knows how Issue records are put back

The guidance SHALL tell the main agent that a record a `recovery_failed` refusal left uncommitted is
put back by `concorde issues recover` once the cause the refusal names is fixed, that an Issue
record whose change no Issue write made, which `uncommitted_change` or a merge's `primary_dirty`
names, is inspected and reverted and never committed by hand, and that a merge puts back by itself
what a killed Issue write left, and tell task sessions to leave both refusals to the main agent.

Recovery is the Issue system's own repair of its records in the primary worktree. A session that
commits or discards such a record by hand may record what no write made, or lose what one did.
