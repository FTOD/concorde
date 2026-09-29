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
([Model changes edit the tracked configuration](#req.main-session.model-change-method)) are made
in the primary worktree.

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
task, even a single one, and never to work inside a task worktree itself.

The main agent keeps what needs the whole project or the developer:
discussing, opening, merging and closing tasks, starting and answering task sessions,
[unbound runs](../../glossary.json#concept.unbound-run), reporting, Issues and the worker
configuration.

### req.main-session.task-brief — A task's brief is recorded before its session starts

The guidance SHALL tell the main agent to record a task's brief in the task's
[decision log](../../glossary.json#concept.decision-log) before starting its task session, and the
task session to read the decision log before changing anything.

The brief holds the developer's decisions the task carries out, the workflow and its
[mode](../../glossary.json#concept.workflow-mode) when one applies, and what the main agent leaves
for the session to decide.

### req.main-session.dispatched-named — Dispatched tasks are named to the developer

The guidance SHALL tell the main agent to show the developer the name and a one-line goal of every
[task](../../glossary.json#concept.task) it dispatched to a task session, and to use those names
when it reports on them.

With several task sessions running, the names are what the developer follows, asks about or stops a
task by.

### req.main-session.stay-in-primary — The main agent stays in the primary worktree

The guidance SHALL tell the main agent to stay in the primary worktree.

### req.main-session.parallel-by-worktree — Parallelism only between worktrees

The guidance SHALL tell the main agent to run tasks in parallel only in separate worktrees and only
when their Modules and shared files do not overlap.

### req.main-session.background-operations — Runs start in the background

The guidance SHALL tell the main agent to start each unbound run in background Bash, and a task
session to start each [Operation](../../glossary.json#concept.operation) and
[execution command](../../glossary.json#concept.execution-command) of its task inside the task
worktree, without naming the task, in background Bash.

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

The task-session guidance SHALL tell a task session to copy the decisions and problems of a
workflow's report into the task's decision log.

Workflows never writes them into the log, and in no-ask mode they were taken without the
developer.

### req.main-session.no-task-questions — Questions need no task

The guidance SHALL tell the main agent which Operations run unbound, in a worktree without a
workspace binding, that such a run examines a checkout of that worktree's `HEAD` whose commit its
result names, and that it changes no Spec or code.

Every change still runs in a task ([Changes run in tasks](#req.main-session.tasks-own-changes)).

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
one answer, and the task session to start the same workflow again with every answer given so far.

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

### req.main-session.merge-conflict — The task session resolves a merge conflict

The guidance SHALL tell the main agent, when merging a task fails with `merge_conflict`, to have
the task's session merge the primary branch into its task branch, resolve the conflicts, validate
and deliver again, and the task session to make that merge when the main agent asks for it.

It is the only merge a task session makes; merging the task into the primary branch stays the main
agent's.

### req.main-session.no-polling — Waiting never polls

The guidance SHALL tell the main agent and every task session never to wait for a run, a lock, a
task session or a merge by polling, and give each wait a way that costs no model turns while it
lasts: being woken by a background run or a SendMessage, or one command that blocks until it is
done (`--wait` of a run and of `concorde task merge`).

### req.main-session.project-terms — Sessions use the project's terms exactly

The guidance SHALL tell the main agent and every task session to use each project term exactly as
its glossary entry defines it.

## Owners and session context

### req.main-session.single-owner — Only a run's owner is woken

Every run SHALL wake at most one main session when it ends, its owner: the main session whose own
background Bash started it.

A run a task session starts belongs to that task session and wakes no main session; a run started
by a command run by hand wakes nobody. What a task session reports reaches only the main session
its `--main` names. Every other main session may see the state of the run, never be woken by it.

### req.main-session.owner-recorded-by-coordination — Ownership is kept on the main session's side

The owner of a run SHALL never be recorded in a run's
[run progress file](../../glossary.json#concept.run-progress-file) or
[run result](../../glossary.json#concept.run-result).

A run's owner is the session whose background Bash started it; the main session a task session
reports to is the `main` its session's [trace node](../../glossary.json#concept.trace-node)
records.

### req.main-session.claude-sees-by-query — A main session sees others' work by asking

A main session SHALL see the state of a task's runs and sessions it does not own only by asking
with `concorde task show <task>`; nothing is pushed into its session.

### req.main-session.terms-in-context — Sessions start with the glossary

The main agent's session and every task session in a worktree whose declared glossary can be read
SHALL each hold every entry of that glossary in its context from its first prompt.

The Concorde block of the worktree's `CLAUDE.md` imports the glossary file, which Claude Code loads
at launch. A worktree whose project declares no glossary, or whose declared glossary cannot be read,
starts its sessions without terms and without an error; Spec validation reports a declared glossary
it cannot read. A [worker](../../glossary.json#concept.worker) is not such a session: its context is
only its brief, as the [Harness](../../harness/module.md) describes.

## Worker models

### req.main-session.developer-chooses-models — The developer chooses worker models

The guidance SHALL tell the main agent to change worker models only when the developer asks.

### req.main-session.worker-configuration-first — The worker configuration comes before any worker

The guidance SHALL tell the main agent that no worker runs without the tracked
[worker configuration](../../glossary.json#concept.worker-configuration), and, when the project has
none, to ask the developer for its enabled models and default model and commit the file alone on the
primary branch before any Operation runs.

### req.main-session.model-change-method — Model changes edit the tracked configuration

The guidance SHALL tell the main agent to change worker models by editing the tracked
[worker configuration](../../glossary.json#concept.worker-configuration) directly, and to commit a
change of that file alone directly on the primary branch when it is meant for future tasks.

That commit is the one change the main agent makes directly in the primary worktree; it is never
made while a merge is unfinished.

### req.main-session.task-models-kept — A task's own model change merges with it

The guidance SHALL tell the main agent that a task may change its own worker configuration while it
works and that the change reaches the primary branch when the task merges.

## Escalation

### req.main-session.batched-decisions — Decisions go up together and come back together

The guidance SHALL tell a task session never to wait in the middle of its work for an answer, but
to gather every decision its task needs that is not its own and escalate them together in one
report, and the main agent to answer them together: to decide those its authority covers, to put
all the others to the developer at once and to answer the session once with every answer.

A task never asks the developer in place: the developer is asked only from the main session.

### req.main-session.escalation-policy — Only major decisions reach the developer

The guidance SHALL state the escalation policy:
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
naming the run's result file, `.concorde/unbound/<run-id>/result.json`, with `--error-file`.

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
([Decisions go up together and come back together](#req.main-session.batched-decisions)).

### req.main-session.task-session-workflow — A task session runs workflows in its brief's mode

The task-session guidance SHALL tell a task session to run a
[workflow](../../glossary.json#concept.workflow) in the
[mode](../../glossary.json#concept.workflow-mode) its brief names, interactive when it names none,
to escalate every pending [decision point](../../glossary.json#concept.decision-point) of an
interactive workflow that ended `awaiting_decision` at once, to give the decisions of the workflow's
report in its own report, and to escalate to the main agent what needs the developer.

The workflow's report is the `--error-file` of an escalation of pending decision points, whose
chain names each point, and of a [workflow result](../../glossary.json#concept.workflow-result) that
is not `ok`; a decision of major impact a no-ask workflow took, which carries no error, is escalated
naming no run or file, so that the session's own link is the whole chain the main agent puts to the
developer.

### req.main-session.task-session-reports — A task session reports its end

The task-session guidance SHALL tell a task session to report to the main agent when it has
delivered the task or cannot go further.

### req.main-session.task-session-never-merges — A task session never merges or closes its task

The task-session guidance SHALL tell a task session never to merge its task into the primary
branch, rebase, switch branches or close its task.

Merging the primary branch into its task branch when the main agent asks for it after a
`merge_conflict` is the one merge it makes
([The task session resolves a merge conflict](#req.main-session.merge-conflict)).

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
