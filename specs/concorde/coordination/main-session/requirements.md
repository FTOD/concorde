# Main session requirements

What the [main-session guidance](module.md) must tell the
[main agent](../../glossary.json#concept.main-agent) and
[task sessions](../../glossary.json#concept.task-session), and what the pi
[run view](../../glossary.json#concept.run-view) and
[model picker](../../glossary.json#concept.model-picker) must do. Most are obligations on the
content of the guidance: a deterministic check establishes what the rendered guidance says, while
whether a model follows it is not something such a check can establish. The requirements on the pi
extension and on what a session holds in its context are obligations on runtime behaviour, checked
against the extension and the session's context rather than against the guidance's text. The
[scenarios](scenarios.md) show the intended behaviour.

## Working method

### req.main-session.tasks-own-changes — Changes run in tasks

The guidance SHALL tell the main agent to make every change of
[Spec](../../glossary.json#concept.spec) meaning or code behaviour in a task, from inside the task
worktree, directly or through runs of Operations and
[execution commands](../../glossary.json#concept.execution-command), and never in the primary
worktree.

Trivial housekeeping that changes neither, such as regenerating the registry mirror after a merge,
is the only exception.

### req.main-session.worktree-own-concorde — A task runs its worktree's Concorde

The guidance SHALL tell whoever works on a task to run every `concorde` command that works on the
task's workspace, such as `spec-validation`, `build`, `run <operation>`, `task-validation` and
`delivery`, from the task worktree with that worktree's own copy, never the primary worktree's.

The commands that manage tasks are the exception: [Tasks](../tasks/module.md) opens, merges and
closes tasks and starts task sessions only from the primary worktree, and refuses those commands
elsewhere with `not_primary`.

### req.main-session.one-task-at-a-time — One task per session at a time

The guidance SHALL tell the main agent to be inside at most one task at a time.

### req.main-session.single-task-in-worktree — A single task is worked in its worktree

The guidance SHALL tell the main agent to carry out a single task it works itself inside that
task's worktree.

In Claude Code the main agent enters the worktree. pi cannot move a session into another worktree,
so there the main agent addresses the task worktree explicitly: it runs the task's commands with
that worktree as working directory and changes files under its path.

### req.main-session.leave-after-delivery — The main agent leaves a delivered task

In Claude Code, the guidance SHALL tell the main agent to leave a task worktree it entered once the
task is delivered.

### req.main-session.task-sessions — Split work goes to task sessions

The guidance SHALL tell the main agent to start a
[task session](../../glossary.json#concept.task-session) per task, with `concorde task session`, for
work split into several tasks.

In pi the main agent starts it with the `concorde_task_session` tool, which runs that command from
the primary worktree.

### req.main-session.dispatched-named — Dispatched tasks are named to the developer

The guidance SHALL tell the main agent to show the developer the name and a one-line goal of every
[task](../../glossary.json#concept.task) it dispatched to a task session, and to use those names
when it reports on them.

With several task sessions running, the names are what the developer follows, asks about or stops a
task by.

### req.main-session.stay-in-primary — The main agent stays in the primary worktree

The guidance SHALL tell the main agent to stay in the primary worktree while any task session runs.

### req.main-session.parallel-by-worktree — Parallelism only between worktrees

The guidance SHALL tell the main agent to run tasks in parallel only in separate worktrees and only
when their Modules and shared files do not overlap.

### req.main-session.background-operations — Runs start in the background inside the task

The guidance SHALL tell the main agent to start each
[Operation](../../glossary.json#concept.operation) and execution command of a task inside the task
worktree, without naming the task, in the background (background Bash in Claude Code, the
`concorde_run` tool in pi).

The task worktree's [workspace binding](../../glossary.json#concept.workspace-binding) tells the run
which task's goal, Modules, branch and base it works on, and one workspace runs one thing at a time.

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

The guidance SHALL tell the main agent to copy the decisions and problems of a workflow's report
into the task's decision log.

Workflows never writes them into the log, and in no-ask mode they were taken without the
developer.

### req.main-session.no-task-questions — Questions need no task

The guidance SHALL tell the main agent which Operations run unbound, in a worktree without a
workspace binding, that such a run examines a checkout of that worktree's `HEAD` whose commit its
result names, and that it changes no Spec or code.

Every change still runs in a task ([Changes run in tasks](#req.main-session.tasks-own-changes)).

### req.main-session.workflows — Preset tasks run their workflow

The guidance SHALL tell the main agent to run a task that follows a known procedure through its
[workflow](../../glossary.json#concept.workflow), started inside the task worktree.

### req.main-session.workflow-mode — The developer chooses the workflow mode

The guidance SHALL tell the main agent to ask the developer which
[workflow mode](../../glossary.json#concept.workflow-mode) to use unless the developer already said.

### req.main-session.workflow-pause — A paused workflow is answered and started again

The guidance SHALL tell the main agent to answer a workflow that ends `awaiting_decision` by
putting every pending [decision point](../../glossary.json#concept.decision-point) to the developer
and starting the same workflow again with every answer given so far.

### req.main-session.merge-without-authorization — Delivered tasks are merged

The guidance SHALL tell the main agent to merge, without asking the developer for authorization, a
task branch that `delivery` committed, using `concorde task merge` from the primary worktree rather
than `git merge`.

[Tasks](../tasks/module.md) holds the [merge lock](../../glossary.json#concept.merge-lock) during
the merge, runs `concorde spec-validation` of the merged checkout, or exactly the `--check`
commands given, and undoes a merge whose checks fail.

### req.main-session.merge-interrupted — An interrupted merge is finished first

The guidance SHALL tell the main agent, when a `concorde task` command is refused with
`merge_incomplete`, to finish the named task's merge before anything else, with `concorde task
merge <task> --resume`, or `--abort` when the merge commit is not the primary branch's head, and to
bring a `merge_diverged` refusal to the developer.

The task-session guidance tells a task session whose escalation is refused with `merge_incomplete`
or `merge_busy` to send that refusal to the main agent instead.

### req.main-session.no-polling — Waiting never polls

The guidance SHALL tell the main agent and every task session never to wait for a run, a lock, a
task session or a merge by polling, and give each wait a way that costs no model turns while it
lasts: being woken by a background run, the run view or a SendMessage, or one command that blocks
until it is done (`--wait` of a run, of `concorde task session` and of `concorde task merge`).

### req.main-session.project-terms — Sessions use the project's terms exactly

The guidance SHALL tell the main agent and every task session to use each project term exactly as
its glossary entry defines it.

## The pi extension and session context

### req.main-session.pi-run-follow — pi follows every run, wherever it started

In pi, the run view SHALL follow every run of the project that is running when the session starts
or starts afterwards, whoever started it: the `concorde_run` tool, a command run with bash, or
another session.

It finds them in the primary worktree's [run store](../../glossary.json#concept.run-store), where
every task worktree's binding records its runs; a run that started and ended between two looks is
followed too, and a run that had ended before the session started is not.

### req.main-session.pi-owned-work — Only its own runs are a pi session's background work

In pi, the run view SHALL report to pi-subagents as the session's background work only the
unfinished runs and task-session rounds the session started with its `concorde_run` and
`concorde_task_session` tools.

The runs and rounds it only follows, started with bash or by another session, are still shown and
reported, but neither `bg_wait` nor the drain of a `pi -p` session before it exits waits for them.

### req.main-session.pi-run-wake — pi reports every run's end once

In pi, the run view SHALL give the main agent the result of every run it follows once, when the run
ends.

A run that has already finished when `concorde_run` finds it is answered in the tool's own result;
every other run wakes the main agent with a message. Either way a result that carries an
[error chain](../../glossary.json#concept.error-chain) is given with the whole chain.

### req.main-session.pi-task-session-view — pi shows every running task-session round

In pi, the run view SHALL show every running task-session round.

### req.main-session.pi-task-session-wake — pi wakes the main agent on every round

In pi, the run view SHALL wake the main agent with each task-session round's recorded outcome when
the round ends.

### req.main-session.terms-in-context — Sessions start with the glossary

The main agent's session and every task session, in Claude Code or pi, in a worktree whose declared
glossary can be read SHALL each hold every entry of that glossary in its context from its first
prompt.

A worktree whose project declares no glossary, or whose declared glossary cannot be read, starts
its sessions without terms and without an error; Spec validation reports a declared glossary it
cannot read. A [worker](../../glossary.json#concept.worker) is not such a session: its context is
only its brief, as the [Harness](../../harness/module.md) describes.

## Worker models

### req.main-session.developer-chooses-models — The developer chooses worker models

The guidance SHALL tell the main agent to change worker models only when the developer asks.

### req.main-session.model-change-method — AI-driven model changes edit the configuration

The guidance SHALL tell the main agent to make an AI-driven change of worker models by editing the
configuration's JSON directly and then validating it read-only, the shared terminal draft editor
being for the developer's own choices.

### req.main-session.task-models-on-request — A task's models change only on request

The guidance SHALL tell the main agent to change an existing task's
[worker model configuration](../../glossary.json#concept.worker-model-configuration) only when the
developer asks for that task.

### req.main-session.pi-picker-terminal — The picker restores pi's terminal

In pi, the model picker SHALL restore pi's terminal whenever Workers' editor ends, whether after
Save, a cancellation or a launch failure.

## Escalation

### req.main-session.escalation-policy — Only major decisions reach the developer

The guidance SHALL state the [escalation policy](../../glossary.json#concept.escalation-policy):
decide ordinary questions itself, record and report them, and ask the developer before acting
only on decisions with major impact.

Recording those decisions is the obligation of
[Decisions are recorded](#req.main-session.decision-log).

### req.main-session.read-chain — The whole error chain is read

The guidance SHALL tell the main agent to read the whole error chain of a result that is not `ok`
before deciding.

### req.main-session.extend-chain — An escalation extends the chain

The guidance SHALL tell the main agent to escalate an error of a task's runs it cannot handle with
`concorde task escalate`, adding its own link on top of the chain instead of summarizing it.

### req.main-session.unbound-failure — A failed unbound run reaches the developer whole

The guidance SHALL tell the main agent to show the developer the whole rendered
[error chain](../../glossary.json#concept.error-chain) of an unbound run that is not `ok` and, when
the failure leads to work, to open a task for it and escalate there with `concorde task escalate`
naming the run's result file, `.concorde/runs/<run-id>/result.json`, with `--error-file`.

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

A Claude Code task session sends the escalation with SendMessage; a pi task session names the
escalation's number in its round's report.

### req.main-session.task-session-no-ask — A task session runs workflows without asking

The task-session guidance SHALL tell a task session to run a
[workflow](../../glossary.json#concept.workflow) only in no-ask
[mode](../../glossary.json#concept.workflow-mode), to give the decisions of the workflow's report in
its own report, and to escalate to the main agent what needs the developer.

Nobody answers a task session at a [decision point](../../glossary.json#concept.decision-point), so
an interactive workflow would stop there with no one to settle it. A
[workflow result](../../glossary.json#concept.workflow-result) that is not `ok` is escalated with the report as `--error-file`; a decision of major impact the workflow took,
which carries no error, is named in the session's report for the main agent to put to the
developer.

### req.main-session.task-session-reports — A task session reports its end

The task-session guidance SHALL tell a task session to report to the main agent when it has
delivered the task or cannot go further.

### req.main-session.task-session-never-merges — A task session never merges or closes

The task-session guidance SHALL tell a task session never to merge or close its task.

## Issues

### req.main-session.issues-recording — The main agent decides what to record

The guidance SHALL tell the main agent to inspect existing Issues before deciding whether a
worker finding, Operation error or its own observation calls for a new report.

Workers and Operations do not create Issues automatically. Inspection includes closed Issues;
appending to an open match or reopening a closed one preserves its identity, while repeating a
creation command creates another [Issue](../../glossary.json#concept.issue).

### req.main-session.issues-worktree — Issue writes belong to a task

The guidance SHALL tell the main agent to run every Issue writing command in a task worktree,
passing the task identity on `report`.

This applies to creation, append, closure and reopening; read-only inspection may use either
worktree. Only `report` has a `--task` argument. It supplies provenance and does not select the
worktree; this is a workflow obligation, not additional CLI admission logic.

### req.main-session.issues-by-operations — Issues are solved by ordinary work

The guidance SHALL tell the main agent to solve an Issue by running ordinary Operations on the
Issue's [Module](../../glossary.json#concept.module) in a task.

### req.main-session.issues-close-with-fix — An Issue closes with its fix

The guidance SHALL tell the main agent to close a solved Issue on the branch of the task that fixed
it.

### req.main-session.issues-unmerged — Unmerged observations retain a handoff

The guidance SHALL tell the main agent to preserve the report, evidence locations and follow-up
for each Issue worth keeping before ending a task without merging it, through a subsequent task
or a handoff in the task's decision log.

Tasks retains a closed task's branch and log; unmerged committed records remain there, while
forced worktree removal can discard uncommitted material. A log handoff does not publish an Issue
on the primary branch.

### req.main-session.issues-conflicts — Issue conflicts are reconciled

The guidance SHALL tell the main agent to reconcile conflicting Issue records in the task
worktree, preserving accepted reports and documenting the disposition decision.

Competing closes cannot simply be concatenated or made to alternate with fictitious reopenings.

### req.main-session.issues-store-check — Reconciled Issue records are checked

The guidance SHALL tell the main agent to run `concorde issues check` on reconciled Issue records
before validation and delivery.

The store check establishes record consistency, not the truth of a closure's evidence.
