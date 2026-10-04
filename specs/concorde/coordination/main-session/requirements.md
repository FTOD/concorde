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
`delivery`, as the task worktree's own `concorde` command, from the task worktree, never as the
primary worktree's.

That command reads the task worktree's
[workspace binding](../../glossary.json#concept.workspace-binding), Specs,
[Protocol copy](../../glossary.json#concept.protocol-copy) and checks, which only the task branch
holds. Which Framework code it runs is
[Distribution](../../distribution/module.md)'s: in an installed project it ordinarily runs the
installed Framework shared with the primary worktree, unless the task reinstalled Concorde in its
worktree, and in Concorde's own source checkout the task branch's code. The commands that manage
tasks are the exception: [Tasks](../tasks/module.md) opens, merges and
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

### req.main-session.task-brief — The task brief is recorded before the task session starts

The guidance SHALL tell the main agent to record a task's
[task brief](../../glossary.json#concept.task-brief) in the task's
[decision log](../../glossary.json#concept.decision-log) before starting its task session.

The task brief holds the developer's decisions the task carries out, the workflow and its
[mode](../../glossary.json#concept.workflow-mode) when one applies, and what the main agent leaves
for the session to decide. It is not a worker's [brief](../../glossary.json#concept.brief), which
an Operation generates for each worker it launches.

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

The task-session guidance SHALL tell a task session to start in background Bash each
[Operation](../../glossary.json#concept.operation) and
[execution command](../../glossary.json#concept.execution-command) it starts itself, never with
`--detach`.

It starts them inside the task worktree
([A task runs its worktree's Concorde](#req.main-session.worktree-own-concorde)) without naming the
task: the task worktree's [workspace binding](../../glossary.json#concept.workspace-binding) tells
the run which task's goal, Modules, branch and base it works on, and one workspace runs one thing
at a time. The background call lives as long as the run it started. A
[workflow step](../../glossary.json#concept.workflow-step) is not such a run: its
[step agents](../../glossary.json#concept.step-agent) start it through the `workflow_step` tool the
workflow part registers with the server
([Workflows](../../workflows/requirements.md#req.workflows.steps-through-server)), which runs it as a
process of the server and waits for it there.

### req.main-session.task-session-quiet-before-validation — A task session stops its background commands before validating

The task-session guidance SHALL tell a task session to let every run of its workspace finish and to
stop every other background command it started, confirming each ended, before it validates and
delivers: before `task-validation` or `delivery` where the method part is installed, and before
`task deliver` otherwise.

A run that still runs holds the [workspace lock](../../glossary.json#concept.workspace-lock), which
refuses both commands, and `delivery` commits every uncommitted change, so a command still writing
in the task worktree would decide what the [delivery commit](../../glossary.json#concept.delivery-commit)
holds. A polling loop, which the guidance forbids anyway
([Waiting never polls](#req.main-session.no-polling)), may never end by itself.

### req.main-session.act-on-run-result — Every run result is acted on

The guidance SHALL tell the main agent to act on the
[run result](../../glossary.json#concept.run-result) of every run it starts.

### req.main-session.decision-log — The main agent records its decisions

The guidance SHALL tell the main agent to record every decision it made for a task without the
developer, with its reason, in the task's [decision log](../../glossary.json#concept.decision-log).

The main agent starts none of a task's runs; the task session records their results
([A task session records its decisions and failed runs](#req.main-session.task-session-decision-log)),
and `concorde task answer` appends the main agent's answers to its reports. An [unbound run](../../glossary.json#concept.unbound-run) belongs to no task and so to no decision
log; [A failed unbound run reaches the developer whole](#req.main-session.unbound-failure) says
what becomes of its result.

### req.main-session.workflow-report-logged — A workflow result reaches the decision log

The task-session guidance SHALL tell a task session to copy the decisions and problems of a
[workflow result](../../glossary.json#concept.workflow-result) into the task's decision log.

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
mode in its task brief for the task session to start inside the task worktree.

### req.main-session.workflow-mode — The developer chooses the workflow mode

The guidance SHALL tell the main agent to ask the developer which
[workflow mode](../../glossary.json#concept.workflow-mode) to use unless the developer already said.

### req.main-session.workflow-restart — A paused workflow starts again with every answer

The task-session guidance SHALL tell a task session to start a workflow that ended
`awaiting_decision` again, once the main agent answered, with every answer given so far.

A step that finished and is neither answered nor retried returns its recorded run; the answered
step runs again and supersedes itself and every step recorded after it, which run anew, as
[Workflows](../../workflows/module.md) states for its
[step keys](../../glossary.json#concept.step-key).

### req.main-session.merge-without-authorization — Delivered tasks are merged

The guidance SHALL tell the main agent to merge, without asking the developer for authorization, a
task branch that `delivery` committed, using `concorde task merge` from the primary worktree rather
than `git merge`.

[Tasks](../tasks/module.md) holds the [merge lock](../../glossary.json#concept.merge-lock) during
the merge, runs `concorde spec-validation` of the merged checkout, or exactly the `--check`
commands given, followed by `concorde spec-validation` while a `concorde update` is not validated
yet, and undoes a merge whose checks fail.

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
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)),
and the main agent merges the task once more. Merging the task into the primary branch stays the
main agent's.

### req.main-session.update-merge — An update reaches the open tasks through their sessions

The guidance SHALL tell the main agent, when a `concorde update` asks to merge the primary branch
into each open task, to have the session of each task it lists merge the primary branch into its
task branch.

An update that installs a new Protocol copy lists the open tasks, whose worktrees still carry the
previous copy ([Distribution](../../distribution/module.md)). The main agent answers each listed
task's session, starting one again if it has ended, and the session then validates again and, when
it had delivered, delivers again
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)).
Merging the task into the primary branch and rebasing stay forbidden to the session.

### req.main-session.task-session-primary-merge — A task session merges the primary branch when asked

The task-session guidance SHALL tell a task session to merge the primary branch into its task
branch when the main agent asks for it after a `merge_conflict` or after a `concorde update`.

The session then resolves the conflicts within the task's goal, verifies and commits the merge and
validates and delivers again, with `task-validation` and `delivery` where the method part is
installed and with `task deliver` otherwise; a task not delivered yet goes on with its work after
validating and delivers when it is done. It is the only merge a task session makes.

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

The end of a run SHALL wake, without any session asking for it, no main session other than its
owner, the session whose background Bash started it.

So a run a main session starts wakes that main session alone; a run a task session starts belongs
to that task session and wakes no main session unasked; a run started by a command run by hand
wakes nobody unasked. What a task session reports reaches only the
main session its task record names when it reports. This guarantee covers the wakes nobody asked for. A session that
registers a wait with the project MCP server's `register_wait`, for a run, a lock or a task it may
not own, asks for its own wake explicitly, and the server admits that registration as its
[contracts](contracts.md#registering-a-wait) document; it wakes only the session that registered
it ([A wait only notifies](#req.main-session.project-mcp-wait-notifies)).

### req.main-session.owner-recorded-by-coordination — Ownership is kept on the main session's side

The guidance and the project MCP server SHALL never take a run's owner from its
[run progress file](../../glossary.json#concept.run-progress-file) or
[run result](../../glossary.json#concept.run-result).

A run's owner is the session whose background Bash started it; the main session a task session
reports to is the `main` its [task record](../../glossary.json#concept.task-record) names.
[Execution](../../execution/module.md), which knows nothing of sessions, defines both records, and
its [run result contract](../../execution/contracts.md#contract.execution.run-result) holds no
owner.

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
only its [brief](../../glossary.json#concept.brief), as the [Harness](../../worker-harness/harness/module.md)
describes.

## The project MCP server

### req.main-session.project-mcp-presentation — Queries and short writes answer as their commands

Each tool Coordination registers with the [project MCP server](../../glossary.json#concept.project-mcp-server) whose row of its [contracts](contracts.md#tools) names a `concorde` command SHALL answer and refuse exactly as
that command does when it waits for no lock, from the
[task records](../../glossary.json#concept.task-record), traces and locks of the primary worktree
read afresh for that call, adding no other rule of its own.

Those tools are the queries `task_list`, `task_show` and `trace_show` and the short writes
`task_open`, `task_escalate`, `task_rebind`, `task_report`, `task_answer`, `task_close` and
`task_resolve`; the Issue tools answer as the Issues command does by the issues part's own
[interface](../../issues/interface.md#mcp-tools). The primary worktree is that of
the repository the server was started in, whichever worktree of the project it was started from.

### req.main-session.project-mcp-record-queries — The other queries present records read-only

The queries `run_result` and `locks` SHALL answer with the result and refuse with the codes their [contracts](contracts.md#tools) define, from the records and locks of the
primary worktree read afresh for that call, changing nothing.

No `concorde` command answers them in that shape: they read a run's saved result,
[run lock](../../glossary.json#concept.run-lock) and
[run progress file](../../glossary.json#concept.run-progress-file), where the execution part is
installed, and the holder lines of the merge lock and the workspace locks.

### req.main-session.project-mcp-merge-start — `task_merge` starts the command's merge

`task_merge` SHALL, once it holds both locks, start the same `concorde task merge` the command line
runs, with the task and the `checks`, `resume` or `abort` it was given.

### req.main-session.project-mcp-merge-answer — `task_merge` answers at once with the start

`task_merge` SHALL answer, once it started the merge, at once with the start its
[contracts](contracts.md#starting-a-merge) define instead of the merge's result.

The merge's own result and refusals are the command's, delivered later: in a `merge_ended` channel
event, or in the output file once the returned `concorde task wait <task> --merge` returns. Before
the start, the call is refused only by its arguments, by a busy lock
([The server never waits for a lock](#req.main-session.project-mcp-no-wait)) or by a failed start.

### req.main-session.project-mcp-merge-output — A merge's output stays with its attempt

`task_merge` SHALL direct the standard output and error of the merge it starts into the folder of
the merge's attempt node in the task's trace, and without a channel return
`concorde task wait <task> --merge` as the command to wait with.

The merge may outlive the server, and the close that ends it removes the task's workspace lock
before the merge has written its answer. The attempt's folder moves with the task to the history
and is found from the task by `task_show` and `trace_show` whatever became of the server, and the
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

It takes those locks without waiting, and a refused call releases every lock it had taken. A task's
record lock is no such lock: every change of a task record holds it for that one update only, so a
short write such as `task_report`, `task_answer`, `task_rebind` or `task_escalate` waits for it as
the command does, briefly, at worst while a close asks Claude Code about the task's sessions, rather
than being refused for contention that ends within moments.

### req.main-session.project-mcp-handover — A granted lock belongs to the work

When `task_merge` has both locks, the server SHALL hand them to the merge process it starts, so
that they are released exactly when that process ends, however it ends, and never by the server or
its session ending.

The call's process takes both locks, answers, and becomes `concorde task merge` in a session of its
own, keeping both locked descriptors; the server itself never holds them.

### req.main-session.project-mcp-wait-notifies — A wait only notifies

`register_wait` SHALL NOT take, keep or hand over any lock for the session it wakes.

It answers at once when what it waits for already happened, and otherwise, with a channel, wakes its
session with one channel event when it happens or ends another way, watching by blocking on the
lock or on the operating system's notice of its changes, never by polling.

### req.main-session.project-mcp-wait-ends — A wait ends with its server

The process that watches a registered wait SHALL end when the server ends, however the server
ends.

A wait wakes only the session whose server registered it, so once that server is gone nobody is
left to wake, and a wait for something that never happens would otherwise block forever.

### req.main-session.project-mcp-fallback — Without a channel the server says so

When the server does not know its session to listen to it as a channel, `task_merge`, and
`register_wait` for something that has not happened yet, SHALL say so and return the
`concorde task wait` command that returns when the same thing happens, for background Bash.

A `register_wait` for something that already happened answers at once with that answer, channel or
not ([`register_wait` answers with its registration](#req.main-session.project-mcp-wait-answer)).

For `task_merge` that is `concorde task wait <task> --merge`, the merge-end wait, which returns
once the merge has written its whole answer, not the wait for the task's
[workspace lock](../../glossary.json#concept.workspace-lock), which the close that ends the merge
removes before then ([A merge's output stays with its attempt](#req.main-session.project-mcp-merge-output)).

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

The operating system's lock is the same whichever path takes it, and everything the server does not present
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

### req.main-session.spec-tooling-errors — A Spec tooling error is translated before it is escalated

The guidance SHALL tell the main agent and task sessions to translate the error record of a refused
Spec tooling command into a `component` link of the
[error chain](../../glossary.json#concept.error-chain), keeping the record's causes as nested
links, before they escalate it.

Spec tooling's commands, such as `spec-validation`, `registry`, `grant` and `build`, and the Spec
MCP server refuse with Spec tooling's own
[error record](../../spec-tooling/spec/errors.md#contract.spec.error), not with a link, and
`concorde task escalate` refuses a file holding such a record with `invalid_error`;
[Tracing](../../kernel/tracing/contracts.md#where-links-appear) has a Module that receives one and cannot
handle it translate it.

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

### req.main-session.task-session-decision-log — A task session records its decisions and failed runs

The task-session guidance SHALL tell a task session to record in its task's
[decision log](../../glossary.json#concept.decision-log) every result that is not `ok` of the runs
it starts and every decision it made without the developer, with its reason.

The task session starts the task's runs and decides its ordinary questions
([A task session decides ordinary questions](#req.main-session.task-session-decides)), so most of
what the log keeps is seen by it alone.

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

A realization binds only files that exist, and a worker writes only bound files and new files
inside bound directories, so no worker creates such a file. A new Spec document is not such a file:
[Specification](../../method/specification/module.md#new-and-deleted-documents)
creates each document a `specify` worker proposes, empty and registered in its Module's `owns`, and
refuses a proposed path that already exists, so a session that created it first would make the
proposal fail.

### req.main-session.task-session-binds-new-files — A task session binds the files it created

The task-session guidance SHALL tell a task session to add each implementation file it created for
a worker to the `entries` of the right realization of its
[Module](../../glossary.json#concept.module) before it launches the worker that fills it.

It checks the binding with [Spec core](../../spec-tooling/spec/module.md)'s
`concorde spec-validation` and commits the file and the binding together.

### req.main-session.task-session-plan-review — A plan review is optional

The task-session guidance SHALL present `plan_review` as optional.

Nothing requires it before `task-validation` or `delivery`; a session runs it when its task brief
asks for it or a change deserves a second reading. The session writes the plan itself and keeps it
where `delivery` does not commit it: the run keeps its own copy of the plan it reviewed.

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

Such a finding is a disagreement the session cannot settle within its task; a maintained finding
whose renewed reasoning the session now accepts it answers with `--accept` and revises the plan,
like any other. The session states the answer it receives in its next run.

### req.main-session.task-session-workflow — A task session runs workflows in its task brief's mode

The task-session guidance SHALL tell a task session to run a
[workflow](../../glossary.json#concept.workflow) in the
[mode](../../glossary.json#concept.workflow-mode) its task brief names, interactive when it names
none.

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
([Decisions go up together](#req.main-session.batched-decisions)), the main agent answers them all
at once ([The session is answered once](#req.main-session.answer-once)), and the session starts the
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

The name is read from the task record at each report rather than from the first prompt, since a
Claude Code session's name does not survive a restart or a resume of the session.

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

The number is the one `concorde task report` gave the report and `concorde task answer` recorded the
answer under, so a session can tell an answer it already acted on.

### req.main-session.task-session-answer-once — An answer already acted on changes nothing

The task-session guidance SHALL tell a task session to treat an answer to a report it already acted
on, matched by the report's number, as nothing to do.

A main agent that reconciles after a restart sends recorded answers again
([A recorded answer is sent again after a restart](#req.main-session.reconcile-resend-answer)),
since it cannot tell whether one was sent.

### req.main-session.reconcile-after-restart — A main agent whose name changed lists its tasks first

The guidance SHALL tell the main agent, when ListAgents reports for its session a name other than
the one it gave its tasks, to list before anything else the tasks not ended whose record names its
former name.

An ended task cannot be rebound and has no report left unanswered, since its end answered them,
so listing it would only look like work pending.

### req.main-session.reconcile-rebind — Each listed task is rebound

The guidance SHALL tell the main agent to rebind each task it listed after its name changed to its
current name with `concorde task rebind`, before anything else.

A task session whose message was lost waits for that rebind, and its report is in the task record
already, so the rebind wakes it.

### req.main-session.reconcile-unanswered — The listed tasks' unanswered reports are read

The guidance SHALL tell the main agent to read the unanswered reports of each task it listed after
its name changed before anything else.

They tell the main agent what it missed while its name did not reach it.

### req.main-session.reconcile-resend-answer — A recorded answer is sent again after a restart

The guidance SHALL tell the main agent to send again, to the task session of each task it listed
after its name changed whose last report has an answer, the latest answer recorded, naming the
reports it answers.

The restart may have come after `concorde task answer` recorded the answer and before SendMessage
sent it, and the session would then wait for an answer that the task record shows as given; a
session that already received it changes nothing
([An answer already acted on changes nothing](#req.main-session.task-session-answer-once)).

### req.main-session.task-session-never-merges — A task session never merges or closes its task

The task-session guidance SHALL tell a task session never to merge its task into the primary
branch or close its task.

Merging the primary branch into its task branch when the main agent asks for it after a
`merge_conflict` or a `concorde update` is the one merge it makes
([A task session merges the primary branch when asked](#req.main-session.task-session-primary-merge)).

### req.main-session.task-session-keeps-branch — A task session keeps its task branch

The task-session guidance SHALL tell a task session never to rebase or switch branches.

The task worktree stays checked out on the task branch that `task open` created.

## Issues

### req.main-session.issues-recording — A session inspects before it records

The guidance SHALL tell the main agent and task sessions to read, before recording a problem, the
open Issues of the Module concerned, and its closed ones when the problem may have been fixed
before, through `issue_list`'s filters rather than the whole project's list.

The whole project's list outgrows a tool result.

### req.main-session.issues-append — A tracked problem is appended to its Issue

The guidance SHALL tell the main agent and task sessions to append a report to the
[Issue](../../glossary.json#concept.issue) that already tracks a problem instead of creating
another.

Repeating a creation creates another Issue. Every report carries a complete description, impact,
basis and evidence, its tier and its severity, so that an Issue escalated by its identity alone can
be acted on.

### req.main-session.issues-through-server — Sessions manage Issues through the project MCP server

The guidance SHALL tell the main agent and task sessions to read and write Issues through the
project MCP server's Issue tools.

The tools record the session that called them, which the `concorde issues` command cannot know; the
command answers the same way and stays the path for the main agent, for a task session's shell and
for the runs a session starts.

### req.main-session.issues-tiers — A task session fixes the Issues its tier lets it

The guidance SHALL tell a task session that it may fix an `obvious-fix` or a `preferred-fix` Issue
itself.

The tier decides who fixes an Issue. A review Operation only reports; fixing is later work of a
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

The severity says how much a problem matters, never who fixes it, which stays the tier's.

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

The guidance names a whole-Module check after a large change, code written before its Specs or by an
earlier version, and a project just adopted.

### req.main-session.issues-close-with-merge — A fixed Issue closes with its task's merge

The guidance SHALL tell the main agent to name the Issues a task fixes in the task, so that the
task's merge closes them.

Starting, fixing or delivering a task changes no Issue; a task that ends without merging closes
none.

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

The decision log and the escalation belong to a task, and an Issue tool or command needs none, so a
failure met without a task has no record to carry it; the main agent opens a task only when the
failure leads to work.

### req.main-session.issues-recovery — The guidance knows how Issue records are put back

The guidance SHALL tell the main agent that a record a `recovery_failed` refusal left uncommitted is
put back by `concorde issues recover` once the cause the refusal names is fixed; that an Issue record
whose change no Issue write made, which `uncommitted_change` or a merge's `primary_dirty` names, is
inspected and reverted, never committed by hand; and that a merge puts back by itself what a killed
Issue write left; and tell task sessions to leave both refusals to the main agent.

Recovery is the Issue system's own repair of its records in the primary worktree; a session that
commits or discards such a record by hand may record what no write made, or lose what one did.
