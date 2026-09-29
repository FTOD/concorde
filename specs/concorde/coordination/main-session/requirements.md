# Main session requirements

What the [main-session guidance](module.md) must tell the
[main agent](../../glossary.json#concept.main-agent) and
[task sessions](../../glossary.json#concept.task-session), and what holds for the sessions it
guides. Most are obligations on the content of the guidance: a deterministic check establishes what
the rendered guidance says, while whether a model follows it is not something such a check can
establish. The requirements on owners and on what a session holds in its context are obligations
on runtime behaviour, checked against what Concorde records and installs rather than against the
guidance's text. The [scenarios](scenarios.md) show the intended behaviour.

## Working method

### req.main-session.tasks-own-changes — Changes run in tasks

The guidance SHALL tell the main agent to make every change of
[Spec](../../glossary.json#concept.spec) meaning or code behaviour in a task, and never in the
primary worktree except an approved [small change](#req.main-session.small-change).

Besides such a change, only housekeeping that regenerates derived files, such as the registry
mirror after a merge, and the commit of the worker configuration alone
([A model change for future tasks is committed alone](#req.main-session.model-change-commit)) are
made in the primary worktree.

### req.main-session.small-change — A small change needs the developer's approval

The guidance SHALL tell the main agent that it may make a very small change, such as a typo, a
one-line fix or a wording correction, directly in the primary worktree only after it said what it
would change and why the change is small and the developer approved that specific change.

Without that approval the change runs in a task like any other.

### req.main-session.worktree-own-concorde — A task runs its worktree's Concorde

The task-session guidance SHALL tell a task session to run every `concorde` command that works on the
task's workspace, such as `spec-validation`, `build`, `run <operation>`, `task-validation` and
`delivery`, from the task worktree with that worktree's own copy, never the primary worktree's.

The commands that manage tasks are the exception: [Tasks](../tasks/module.md) opens, merges and
closes tasks and starts task sessions only from the primary worktree, and refuses those commands
elsewhere with `not_primary`.

### req.main-session.every-task-delegated — Every task is worked by a task session

The guidance SHALL tell the main agent to start a
[task session](../../glossary.json#concept.task-session) with `concorde task session` for every
task, even a single one.

### req.main-session.no-work-in-task-worktree — The main agent never works inside a task worktree

The guidance SHALL tell the main agent never to work inside a task worktree itself.

The main agent keeps what needs the whole project or the developer:
discussing, opening, merging and closing tasks, starting and answering task sessions,
[unbound runs](../../glossary.json#concept.unbound-run), reporting, Issues and the worker
configuration.

### req.main-session.task-brief — A task's brief is recorded before its session starts

The guidance SHALL tell the main agent to record a task's brief in the task's
[decision log](../../glossary.json#concept.decision-log) before starting its task session.

The brief holds the developer's decisions the task carries out, the workflow and its
[mode](../../glossary.json#concept.workflow-mode) when one applies, and what the main agent leaves
for the session to decide.

### req.main-session.brief-read-first — A task session reads the decision log first

The task-session guidance SHALL tell a task session to read the task's
[decision log](../../glossary.json#concept.decision-log) before it changes anything.

The log holds the brief the main agent recorded
([A task's brief is recorded before its session starts](#req.main-session.task-brief)).

### req.main-session.dispatched-named — Dispatched tasks are named to the developer

The guidance SHALL tell the main agent to show the developer the name and a one-line goal of every
[task](../../glossary.json#concept.task) it dispatched to a task session.

With several task sessions running, the names are what the developer follows, asks about or stops a
task by.

### req.main-session.reports-by-name — Reports name the dispatched tasks

The guidance SHALL tell the main agent to name each dispatched task by the name it showed the
developer whenever it reports on that task.

### req.main-session.stay-in-primary — The main agent stays in the primary worktree

The guidance SHALL tell the main agent to stay in the primary worktree.

### req.main-session.parallel-by-worktree — Parallelism only between worktrees

The guidance SHALL tell the main agent to run tasks in parallel only in separate worktrees and only
when their Modules and shared files do not overlap.

### req.main-session.background-operations — Runs start in the background

The guidance SHALL tell the main agent to start each unbound run in background Bash.

### req.main-session.task-session-background-runs — A task session starts its runs in the background

The task-session guidance SHALL tell a task session to start each
[Operation](../../glossary.json#concept.operation) and
[execution command](../../glossary.json#concept.execution-command) of its task in background Bash.

It starts them inside the task worktree
([A task runs its worktree's Concorde](#req.main-session.worktree-own-concorde)) without naming the
task: the task worktree's [workspace binding](../../glossary.json#concept.workspace-binding) tells
the run which task's goal, Modules, branch and base it works on, and one workspace runs one thing
at a time.

### req.main-session.act-on-run-result — Every run result is acted on

The guidance SHALL tell the main agent to act on the
[run result](../../glossary.json#concept.run-result) of every run it starts.

### req.main-session.decision-log — Decisions are recorded

The guidance SHALL tell the main agent to record every result of a task's runs that is not `ok` and
every decision made without the developer in the task's
[decision log](../../glossary.json#concept.decision-log).

An [unbound run](../../glossary.json#concept.unbound-run) belongs to no task and so to no decision
log; [A failed unbound run reaches the developer whole](#req.main-session.unbound-failure) says
what becomes of its result.

### req.main-session.workflow-report-logged — A workflow's report reaches the decision log

The task-session guidance SHALL tell a task session to copy the decisions and problems of a
workflow's report into the task's decision log.

Workflows never writes them into the log, and in no-ask mode they were taken without the
developer.

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
mode in the task's brief for the task session to start inside the task worktree.

### req.main-session.workflow-mode — The developer chooses the workflow mode

The guidance SHALL tell the main agent to ask the developer which
[workflow mode](../../glossary.json#concept.workflow-mode) to use unless the developer already said.

### req.main-session.workflow-pause — A paused workflow is answered and started again

The guidance SHALL tell the main agent to answer the escalation of a workflow that ended
`awaiting_decision` by settling every pending
[decision point](../../glossary.json#concept.decision-point), itself or through the developer, in
one answer.

### req.main-session.workflow-restart — A paused workflow starts again with every answer

The task-session guidance SHALL tell a task session to start a workflow that ended
`awaiting_decision` again, once the main agent answered, with every answer given so far.

A step that finished and is neither answered nor retried returns its recorded run; the answered
step runs again and supersedes itself and every step recorded after it, which run anew, as
[Workflows](../../execution/workflows/module.md) states for its
[step keys](../../glossary.json#concept.step-key).

### req.main-session.merge-without-authorization — Delivered tasks are merged

The guidance SHALL tell the main agent to merge, without asking the developer for authorization, a
task branch that `delivery` committed, using `concorde task merge` from the primary worktree rather
than `git merge`.

[Tasks](../tasks/module.md) holds the [merge lock](../../glossary.json#concept.merge-lock) during
the merge, runs `concorde spec-validation` of the merged checkout, or exactly the `--check`
commands given, and undoes a merge whose checks fail.

### req.main-session.merge-interrupted — An interrupted merge is finished first

The guidance SHALL tell the main agent, when a `concorde task` command is refused with
`merge_incomplete`, to finish the named task's merge before anything else.

It finishes it with `concorde task merge <task> --resume`, which checks the merge again, unless
[An unfinished merge that cannot resume is aborted](#req.main-session.merge-abort) applies.

### req.main-session.merge-abort — An unfinished merge that cannot resume is aborted

The guidance SHALL tell the main agent to finish an interrupted merge with `concorde task merge
<task> --abort` when the merge commit is no longer the primary branch's head or `--resume` answers
`not_resumable`.

### req.main-session.merge-diverged — A diverged primary branch goes to the developer

The guidance SHALL tell the main agent to bring a `merge_diverged` refusal to the developer.

The primary branch was changed by hand after the merge, and discarding those commits is the
developer's decision.

### req.main-session.task-session-merge-refusal — A task session passes a merge refusal on

The task-session guidance SHALL tell a task session whose escalation is refused with
`merge_incomplete` or `merge_busy` to send that refusal, unchanged, to the main agent.

A task session has no authority to finish a merge.

### req.main-session.merge-conflict — The task session resolves a merge conflict

The guidance SHALL tell the main agent, when merging a task fails with `merge_conflict`, to have
the task's session merge the primary branch into its task branch.

The session then delivers again
([A task session merges the primary branch when asked](#req.main-session.task-session-conflict-merge)),
and the main agent merges the task once more. Merging the task into the primary branch stays the
main agent's.

### req.main-session.task-session-conflict-merge — A task session merges the primary branch when asked

The task-session guidance SHALL tell a task session to merge the primary branch into its task
branch when the main agent asks for it after a `merge_conflict`.

The session then resolves the conflicts within the task's goal, verifies and commits the merge and
runs `task-validation` and `delivery` again. It is the only merge a task session makes.

### req.main-session.no-polling — Waiting never polls

The guidance SHALL tell the main agent and every task session never to wait for a run, a lock, a
task session or a merge by polling.

### req.main-session.wait-without-turns — Every wait costs no model turns

The guidance SHALL give each wait of the main agent and of a task session a way that costs no model
turns while it lasts.

The ways are being woken by a background run, by a SendMessage or by a channel event of a wait the
session registered, and one command that blocks until it is done (`--wait` of a run and of
`concorde task merge`, and `concorde task wait`).

### req.main-session.project-terms — Sessions use the project's terms exactly

The guidance SHALL tell the main agent and every task session to use each project term exactly as
its glossary entry defines it.

## Owners and session context

### req.main-session.single-owner — Only a run's owner is woken unasked

The end of a run SHALL wake, without any session asking for it, at most one main session: its
owner, the main session whose own background Bash started it.

A run a task session starts belongs to that task session and wakes no main session unasked; a run
started by a command run by hand wakes nobody unasked. What a task session reports reaches only the
main session its `--main` names. This guarantee covers the wakes nobody asked for. A session that
registers a wait with the project MCP server's `register_wait`, for a run, a lock or a task it may
not own, asks for its own wake explicitly, and the server admits that registration as its
[contracts](contracts.md#registering-a-wait) document; it wakes only the session that registered
it ([A wait only notifies](#req.main-session.project-mcp-wait-notifies)).

### req.main-session.owner-recorded-by-coordination — Ownership is kept on the main session's side

The owner of a run SHALL never be recorded in a run's
[run progress file](../../glossary.json#concept.run-progress-file) or
[run result](../../glossary.json#concept.run-result).

A run's owner is the session whose background Bash started it; the main session a task session
reports to is the `main` its session's [trace node](../../glossary.json#concept.trace-node)
records.

### req.main-session.claude-sees-by-query — A main session sees others' work by asking

A main session SHALL learn the state of a task's runs and sessions it does not own only by asking
for it; nothing it did not ask for is pushed into its session.

It asks with `concorde task show <task>`, or the server's `task_show`, for the state now, or
registers a wait with `register_wait` to be woken when a run ends, a lock is released or a task
reaches a state.

### req.main-session.terms-in-context — Sessions start with the glossary

The main agent's session and every task session in a worktree whose declared glossary can be read
SHALL each hold every entry of that glossary in its context from its first prompt.

The Concorde block of the worktree's `CLAUDE.md` imports the glossary file, which Claude Code loads
at launch. A worktree whose project declares no glossary, or whose declared glossary cannot be read,
starts its sessions without terms and without an error; Spec validation reports a declared glossary
it cannot read. A [worker](../../glossary.json#concept.worker) is not such a session: its context is
only its brief, as the [Harness](../../harness/module.md) describes.

## The project MCP server

### req.main-session.project-mcp-presentation — Queries and short writes answer as their commands

Each tool of the [project MCP server](../../glossary.json#concept.project-mcp-server) whose row of
its [contracts](contracts.md#tools) names a `concorde` command SHALL answer and refuse exactly as
that command does when it waits for no lock, from the
[task records](../../glossary.json#concept.task-record), traces and locks of the primary worktree
read afresh for that call, adding no other rule of its own.

Those tools are the queries `task_list`, `task_show` and `trace_show` and the short writes
`task_open`, `task_escalate` and `task_close`. The primary worktree is that of
the repository the server was started in, whichever worktree of the project it was started from.

### req.main-session.project-mcp-record-queries — The other queries present records read-only

The queries `run_result`, `workflow_report` and `locks` SHALL answer with the result and refuse
with the codes their [contracts](contracts.md#tools) define, from the records and locks of the
primary worktree read afresh for that call, changing nothing.

No `concorde` command answers them in that shape: they read a run's saved result,
[run lock](../../glossary.json#concept.run-lock) and
[run progress file](../../glossary.json#concept.run-progress-file), a task's saved workflow results, and the holder lines of the merge lock and the
workspace locks.

### req.main-session.project-mcp-merge-start — `task_merge` starts the command's merge

`task_merge` SHALL, once it holds both locks, start the same `concorde task merge` the command line
runs, with the task and the `checks`, `resume` or `abort` it was given.

### req.main-session.project-mcp-merge-answer — `task_merge` answers at once with the start

`task_merge` SHALL answer, once it started the merge, at once with the start its
[contracts](contracts.md#starting-a-merge) define instead of the merge's result.

The merge's own result and refusals are the command's, delivered later: in a `merge_ended` channel
event, or in the output file once the returned `concorde task wait` command returns. Before the
start, the call is refused only by its arguments, by a busy lock
([The server never waits for a lock](#req.main-session.project-mcp-no-wait)) or by a failed start.

### req.main-session.project-mcp-wait-as-command — `register_wait` waits for what the command waits for

`register_wait` SHALL wait for exactly what the matching `concorde task wait` waits for.

### req.main-session.project-mcp-wait-answer — `register_wait` answers with its registration

`register_wait` SHALL answer at once with the registration its
[contracts](contracts.md#registering-a-wait) define.

When what it waits for already happened, its answer carries the value that command would print.

### req.main-session.project-mcp-no-wait — The server never waits for a lock

A tool of the server that needs a lock SHALL be refused at once, with `workspace_busy` or
`merge_busy`, when another process holds it, naming the lock file and the holder's command,
process, start time, Claude Code session and task as the holder line gives them.

It takes a lock without waiting, and a refused call releases every lock it had taken.

### req.main-session.project-mcp-handover — A granted lock belongs to the work

When `task_merge` has both locks, the server SHALL hand them to the merge process it starts, so
that they are released exactly when that process ends, however it ends, and never by the server or
its session ending.

It starts the merge as a process of its own with both locked descriptors inherited, and closes its
own copies before it answers.

### req.main-session.project-mcp-wait-notifies — A wait only notifies

`register_wait` SHALL NOT take, keep or hand over any lock for the session it wakes.

It answers at once when what it waits for already happened, and otherwise, with a channel, wakes its
session with one channel event when it happens or ends another way, watching by blocking on the
lock or on the kernel's notice of its changes, never by polling.

### req.main-session.project-mcp-fallback — Without a channel the server says so

When the server does not know its session to listen to it as a channel, `task_merge`, and
`register_wait` for something that has not happened yet, SHALL say so and return the
`concorde task wait` command that returns when the same thing happens, for background Bash.

A `register_wait` for something that already happened answers at once with that answer, channel or
not ([`register_wait` answers with its registration](#req.main-session.project-mcp-wait-answer)).

For `task_merge` that is the wait for the task's
[workspace lock](../../glossary.json#concept.workspace-lock), which the merge holds until it ends.

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

The kernel's lock is the same whichever path takes it, and everything the server does not present
stays a command.

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

The map belongs to the developer's machine and is never committed.

### req.main-session.model-change-method — Model changes edit the tracked configuration

The guidance SHALL tell the main agent to change worker models by editing the tracked
[worker configuration](../../glossary.json#concept.worker-configuration) directly.

There is no editor; the edit preserves unrelated entries.

### req.main-session.model-change-commit — A model change for future tasks is committed alone

The guidance SHALL tell the main agent to commit a change of the worker configuration meant for
future tasks alone, directly on the primary branch, and never while a merge is unfinished.

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

Ordinary questions are those without major impact, such as naming, internal structure, task order,
a clarified re-run or splitting a task. Recording those decisions is the obligation of
[Decisions are recorded](#req.main-session.decision-log).

### req.main-session.report-decisions — Decisions taken for the developer are reported

The guidance SHALL tell the main agent to report to the developer the decisions it took on the
developer's behalf.

Its report closes each piece of work with what was merged, what was decided and what is still open.

### req.main-session.escalation-policy — Only major decisions reach the developer

The guidance SHALL tell the main agent to ask the developer before acting on a decision with major
impact.

It decides the other questions of the work itself
([Ordinary questions are decided](#req.main-session.ordinary-decisions)). The
developer is still asked, beyond such decisions, for what other requirements name: the
[workflow mode](#req.main-session.workflow-mode), the models of a
[missing worker configuration](#req.main-session.worker-configuration-created) and the approval of
a [small change](#req.main-session.small-change). A decision has major impact when it changes what a Module promises or the project's direction,
contradicts an earlier developer decision, discards work or data, cannot be undone by an ordinary
revert, touches security or credentials or needs more resources than the developer set.

### req.main-session.read-chain — The whole error chain is read

The guidance SHALL tell the main agent to read the whole error chain of a result that is not `ok`
before deciding.

### req.main-session.extend-chain — An escalation extends the chain

The guidance SHALL tell the main agent to escalate an error of a task's runs it cannot handle with
`concorde task escalate`, adding its own link on top of the chain instead of summarizing it.

### req.main-session.unbound-failure — A failed unbound run reaches the developer whole

The guidance SHALL tell the main agent to show the developer the whole rendered
[error chain](../../glossary.json#concept.error-chain) of an unbound run that is not `ok`.

An unbound run belongs to no task, so no decision log or escalation records it.

### req.main-session.unbound-failure-task — Work from a failed unbound run carries its chain

The guidance SHALL tell the main agent, when the failure of an unbound run leads to work, to open a
task for that work.

### req.main-session.unbound-failure-escalated — The task escalates with the run's result file

The guidance SHALL tell the main agent to escalate in the task opened for a failed unbound run with
`concorde task escalate` naming the run's result file, `.concorde/unbound/<run-id>/result.json`,
with `--error-file`.

`--run` names only runs of the task's own [workspace](../../glossary.json#concept.workspace), and an
unbound run has none.

## Task sessions

### req.main-session.task-session-guidance — A task session works only inside its task

The task-session guidance SHALL tell a task session to work only inside its task.

### req.main-session.task-session-decides — A task session decides ordinary questions

The task-session guidance SHALL tell a task session to decide ordinary questions within the task's
goal and Modules itself.

### req.main-session.task-session-escalates — A task session escalates the rest

The task-session guidance SHALL tell a task session to escalate every other question to the main
agent with its own link on top of the [error chain](../../glossary.json#concept.error-chain).

A task session records every escalation and then sends them together with SendMessage
([Decisions go up together](#req.main-session.batched-decisions)).

### req.main-session.task-session-prepares-workers — A task session prepares the workers' environment

The task-session guidance SHALL tell a task session to create every new file the work needs outside
the directories its Modules bind, with the least content its format needs to be valid, before it
launches the [worker](../../glossary.json#concept.worker) that fills it.

A realization binds only files that exist, and a worker writes only bound files and new files
inside bound directories, so no worker and no Operation creates such a file.

### req.main-session.task-session-binds-new-files — A task session binds the files it created

The task-session guidance SHALL tell a task session to add each file it created for a worker to the
`entries` of the right realization of its [Module](../../glossary.json#concept.module) before it
launches the worker that fills it.

It checks the binding with `concorde spec-validation` and commits the file and the binding together.

### req.main-session.task-session-workflow — A task session runs workflows in its brief's mode

The task-session guidance SHALL tell a task session to run a
[workflow](../../glossary.json#concept.workflow) in the
[mode](../../glossary.json#concept.workflow-mode) its brief names, interactive when it names none.

### req.main-session.task-session-workflow-pause — A task session escalates a paused workflow's decision points at once

The task-session guidance SHALL tell a task session to escalate every pending
[decision point](../../glossary.json#concept.decision-point) of a workflow that ended
`awaiting_decision` at once, with the workflow's report as `--error-file`.

The report's chain names each point with its options and recommendation.

### req.main-session.task-session-workflow-decisions — A task session reports a workflow's decisions

The task-session guidance SHALL tell a task session to give the decisions of a workflow's report in
its own report to the main agent.

### req.main-session.task-session-workflow-failure — A task session escalates a failed workflow with its report

The task-session guidance SHALL tell a task session to escalate a
[workflow result](../../glossary.json#concept.workflow-result) that is not `ok` and that it cannot
repair within the task with the workflow's report as `--error-file`.

### req.main-session.task-session-workflow-major — A task session escalates a workflow's major decision alone

The task-session guidance SHALL tell a task session to escalate a decision of major impact that a
no-ask workflow took naming no run or file.

Such a decision carries no error, so the session's own link is the whole chain the main agent puts
to the developer.

### req.main-session.task-session-reports — A task session reports its end

The task-session guidance SHALL tell a task session to report to the main agent when it has
delivered the task or cannot go further.

### req.main-session.task-session-never-merges — A task session never merges or closes its task

The task-session guidance SHALL tell a task session never to merge its task into the primary
branch or close its task.

Merging the primary branch into its task branch when the main agent asks for it after a
`merge_conflict` is the one merge it makes
([The task session resolves a merge conflict](#req.main-session.merge-conflict)).

### req.main-session.task-session-keeps-branch — A task session keeps its task branch

The task-session guidance SHALL tell a task session never to rebase or switch branches.

The task worktree stays checked out on the task branch that `task open` created.

## Issues

### req.main-session.issues-recording — The main agent decides what to record

The guidance SHALL tell the main agent to inspect existing Issues before deciding whether a
worker finding, Operation error or its own observation calls for a new report.

Workers and Operations do not create Issues automatically. Inspection includes closed Issues;
appending to an open match or reopening a closed one preserves its identity, while repeating a
creation command creates another [Issue](../../glossary.json#concept.issue).

### req.main-session.issues-worktree — Issue writes belong to a task

The guidance SHALL tell the main agent to have every Issue writing command run in a task
worktree, by the session working that task, passing the task identity on `report`.

This applies to creation, append, closure and reopening; read-only inspection may use either
worktree. Only `report` has a `--task` argument. It supplies provenance and does not select the
worktree; this is a workflow obligation, not additional CLI admission logic.

### req.main-session.issues-by-operations — Issues are solved by ordinary work

The guidance SHALL tell the main agent to solve an Issue by a task on the Issue's
[Module](../../glossary.json#concept.module) whose session runs ordinary Operations.

### req.main-session.issues-close-with-fix — An Issue closes with its fix

The guidance SHALL tell the main agent to have a solved Issue closed on the branch of the task that
fixed it.

### req.main-session.issues-unmerged — Unmerged observations retain a handoff

The guidance SHALL tell the main agent to preserve the report, evidence locations and follow-up
for each Issue worth keeping before ending a task without merging it, through a subsequent task
or a handoff in the task's decision log.

Tasks retains a closed task's branch and log; unmerged committed records remain there, while
forced worktree removal can discard uncommitted material. A log handoff does not publish an Issue
on the primary branch.

### req.main-session.issues-conflicts — Issue conflicts are reconciled

The guidance SHALL tell the main agent to have the task's session reconcile conflicting Issue
records in the task worktree, preserving accepted reports and documenting the disposition
decision.

Competing closes cannot simply be concatenated or made to alternate with fictitious reopenings.

### req.main-session.issues-store-check — Reconciled Issue records are checked

The guidance SHALL tell the main agent to have `concorde issues check` run on reconciled Issue
records before validation and delivery.

The store check establishes record consistency, not the truth of a closure's evidence.
