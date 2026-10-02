# Main session

## Purpose

Main session is the top of Concorde's levels of work, level 1: the guidance that makes an ordinary
Claude Code session in a project's primary worktree act as Concorde's
[main agent](../../glossary.json#concept.main-agent): discuss work with the developer, split it into
[tasks](../../glossary.json#concept.task), hand every task to a
[task session](../../glossary.json#concept.task-session) and answer it, keep each task's
[decision log](../../glossary.json#concept.decision-log), decide ordinary questions itself while
escalating only major ones, merge delivered tasks, and handle
[Issues](../../glossary.json#concept.issue). The method of working inside a task is part of this
guidance too, as the task-session guidance: the task level is the main agent's own work, which it
always delegates, and a task session starts with that method in the guidance it is given. It is
advice to a model, not enforcement — Concorde places no permission limits on the main agent, and
nothing here constrains the developer.

For now the guidance serves Claude Code only: the main agent is a Claude Code session, and so is
every task session, since a task session runs on the main agent's own program, while the
[workers](../../glossary.json#concept.worker) of their runs may run on pi. Distribution renders and
installs this [Module](../../glossary.json#concept.module)'s content. Beside the guidance the Module
owns one program, the [project MCP server](../../glossary.json#concept.project-mcp-server): a thin
MCP presentation of the task, trace and lock commands through which a Claude Code session queries
and changes tasks, takes a lock without waiting, and is woken when something it waits for happens.

## Core concepts

<a id="concept.main-session-guidance"></a>

The **[main-session guidance](../../glossary.json#concept.main-session-guidance)** is what Concorde
tells the main agent: installed as the project skill and as a block of the project's `CLAUDE.md`, it
tells the Claude Code session opened in a Concorde project's primary worktree that it is the main
agent, and gives it a [working method](#the-working-method). Its task-session part is the first
prompt of every task session. The guidance is instructions, not a program, because the main agent's
work is judgment; the project MCP server beside it is a program, but one that only presents
commands and adds no rule beyond taking locks without waiting. Everything that must hold regardless
of judgment is enforced elsewhere — workers by the Harness, Operations by their own checks,
readiness by `task-validation` and `delivery` — so an agent that ignores the guidance wastes effort
but cannot widen a worker's boundary.

<a id="concept.task-brief"></a>

The **[task brief](../../glossary.json#concept.task-brief)** is how the main agent hands a task to
its session: before it starts the task session, it records in the task's
[decision log](../../glossary.json#concept.decision-log) the developer's decisions the task carries
out, the workflow and its [mode](../../glossary.json#concept.workflow-mode) when one applies,
anything the goal leaves out and what it leaves for the session to decide, and the session reads it
before it changes anything. It is written by the main agent for a task session, unlike a worker's
[brief](../../glossary.json#concept.brief), which an Operation generates for each worker it launches
from that worker's grant.

<a id="concept.project-mcp-server"></a>

The **[project MCP server](../../glossary.json#concept.project-mcp-server)** is the project's one
stdio MCP server for the main-session side, `concorde project-mcp`, which the installer registers as
`concorde` in the project's `.mcp.json`. Each Claude Code session that loads it runs its own server
process, which lives exactly as long as that session; there is no daemon. Started from any worktree,
it finds the primary worktree through Git's common directory and serves that project's tasks, traces
and locks, read afresh on every call. It answers no call with code of its own: each call runs in a
fresh process of the Concorde that the primary worktree's `concorde` command runs at that moment, so
a merge or a `concorde update` during a session changes the code that answers the session's next
call, and the long-lived process keeps only what must live as long as its session. It is a
presentation: the `concorde` commands stay the source of truth, and every answer and refusal of a
query or short write is the command's own. Its one rule of its own is that it never waits for a
lock, so `task_merge` answers at once with the merge it started, and `register_wait` with the wait
it registered, while the merge's result and the wait's answer arrive later. One tool,
`workflow_step`, works on a workspace rather than on records: it starts and awaits the [workflow
steps](../../glossary.json#concept.workflow-step) of the workspace its session works in, so that
their runs are processes of the server rather than of a relaying agent's turn. Its tools and how it
wakes a session are explained [below](#the-project-mcp-server).

<a id="owners"></a>

**Owners.** The main agent starts each run of its own, an unbound Operation, in background Bash,
and Claude Code wakes it when the command ends; a task session does the same with the runs of its
task. Several main sessions may work on one project at the same time, but the end of a run wakes,
without anyone asking, only its **owner**, and it has never more than one. A session that wants to
hear of work it does not own asks for its own wake explicitly, by registering a wait with the
[project MCP server](../../glossary.json#concept.project-mcp-server); that wake reaches only the
session that registered it:

| Work | Owner | How the owner is woken |
| --- | --- | --- |
| A run a main session starts, in background Bash | that session | Claude Code's own notification when the command ends |
| What a task session reports | the main session its task record names when it reports | the task session's SendMessage, once `concorde task report` recorded the report |
| A run a task session starts in its worktree | that task session, no main session | Claude Code's own notification in the task session; its main session hears of it in the task session's report |
| A run started by a command run by hand | no main session | nobody is woken |
| A wait registered with, or a merge started through, the [project MCP server](../../glossary.json#concept.project-mcp-server) | the session whose server it is | a channel event of that server, or, without a channel, the session's own background Bash running the equivalent `concorde task wait` |

Execution, which knows nothing of main sessions, never records an owner: a run's owner is the
session whose background Bash started it, and the main session a task session reports to is the
`main` that its task's [task record](../../glossary.json#concept.task-record) names, first the
`--main` its session was started with, then the name the main agent rebound the task to. A main
session that does not own a run is never woken by it unasked, since nothing it did not ask for is
pushed into it: it asks with `concorde task show <task>`, which lists the task workspace's runs with
their status and the task's sessions with the main session each reports to, or it registers a wait
for the run's end ([requirements](requirements.md#req.main-session.single-owner)).

## Overview

### A piece of work, end to end

A representative flow, agreeing a payments retry limit, with who works where at each stage:

```d2 illustrative
grid-columns: 3
horizontal-gap: 110
developer: Developer {
  grid-columns: 1
  vertical-gap: 60
  ask: "Ask for a retry limit"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  g4: "" {style.opacity: 0}
  g5: "" {style.opacity: 0}
  read: "Read the report"
}
primary: "Main agent\nprimary worktree" {
  grid-columns: 1
  vertical-gap: 60
  agree: "Agree the limit\nwith the developer"
  open: "Open a task for\nmodule.payments,\nrecord its task brief"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  merge: "Merge the\ndelivered task"
  report: "Report the exponential\nback-off it chose"
}
task: "Task session\ntask worktree" {
  grid-columns: 1
  vertical-gap: 60
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  work: "Run specify,\nimplement, test"
  review: "Run code_review"
  deliver: "Run task-validation,\ndelivery"
  g3: "" {style.opacity: 0}
  g4: "" {style.opacity: 0}
}
developer.ask -> primary.agree
primary.agree -> primary.open
primary.open -> task.work: "start a\ntask session"
task.work -> task.review: "read each\nrun result"
task.review -> task.deliver
task.deliver -> primary.merge: "report the\ndelivery"
primary.merge -> primary.report
primary.report -> developer.read
```

The main agent agrees the change with the developer, opens a task and records its task brief, and
hands the task to a task session, which runs the Operations and execution commands in the task worktree,
reads each [run result](../../glossary.json#concept.run-result) and delivers. The main agent merges
the delivered task and reports what it decided on the developer's behalf, here the back-off.

### What the main agent reaches

The main session is level 1 of Concorde's [levels of work](../../module.md#the-levels-of-work), the
top of Coordination. Nothing in Concorde calls it: the developer talks to it, and the installed
skill and `CLAUDE.md` block are Concorde's only way to reach a session at all. It calls only
downward. At level 2 it opens a task and delegates it to a task session; from inside the task,
the task session starts workflows (level 3) and runs (level 4), Operations and execution
commands, in the task worktree; the main agent itself starts only unbound runs, in the primary
worktree, and it reaches workers (level 5) only through an Operation, touching Workers otherwise
only to edit the worker configuration. What comes back up is structured: run results, workflow
results, and task-session reports and escalations, each failure carrying its
[error chain](../../glossary.json#concept.error-chain). The chain ends here: the main agent
decides what the escalation policy lets it decide, records and reports it, and otherwise adds its
own `main-agent` link and asks the developer, the chain's last receiver.

What the main agent reaches, down the levels. Workers appear only under Operations, because an
Operation is the only way the main agent reaches one:

```d2 illustrative
mainsession: Main session
tasks: Tasks
tasksession: Task sessions
workflows: Workflows
runs: "Runs: Operations and execution commands"
workers: Workers
mainsession -> tasks: opens, merges, closes
mainsession -> tasksession: delegates a task to
mainsession -> runs: starts unbound
tasksession -> tasks: records sessions in
tasksession -> workflows: starts in its task worktree
tasksession -> runs: starts in its task worktree
workflows -> runs: runs one at a time
runs -> workers: an Operation launches
```

## The working method

The installed guidance gives the main agent this working method:

- **Discuss first.** Agree the direction with the developer before changing anything.
- **Split into tasks.** Turn agreed work into [tasks](../../glossary.json#concept.task),
  opened with `concorde task`. Run tasks in parallel only across worktrees whose Modules and shared
  files do not overlap; run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Hand every task to a task session.** Never work inside a task worktree: start one
  [task session](../../glossary.json#concept.task-session) per task with
  `concorde task session <task>`, even for a single task, and stay in the primary worktree, where
  the main agent discusses, opens and closes tasks, starts and answers task sessions, runs
  [unbound](../../glossary.json#concept.unbound-run) Operations, merges, reports, inspects Issues
  and changes the worker configuration. Before starting the session, record the task's
  [task brief](../../glossary.json#concept.task-brief) in its decision log; the session reads it
  first. A task session is a background Claude Code session, on the main agent's own program: the
  command names the main agent's session with `--main`, the task session reports back with
  SendMessage, and the main agent answers it the same way; ending the task, by its merge or its close, stops its task sessions and
  removes them from Claude's session list, keeping their transcripts in the task's
  [trace](../../glossary.json#concept.trace), so the main agent never removes them itself. The task
  session changes Specs and code in the task worktree directly or by running
  [Operations](../../glossary.json#concept.operation) with `concorde run <operation> …` and the
  [execution commands](../../glossary.json#concept.execution-command) `concorde task-validation`
  and `concorde delivery`, reading each [run result](../../glossary.json#concept.run-result), and
  runs every `concorde` command that works on the task's workspace as the task worktree's own
  command, from that worktree
  ([requirements](requirements.md#req.main-session.worktree-own-concorde));
  the commands that open, merge and close tasks and start task sessions run from the primary
  worktree. None of these names the task: the task worktree's
  [workspace binding](../../glossary.json#concept.workspace-binding), which `concorde task open`
  wrote, tells every run which goal, Modules, branch and base it works on, and one workspace runs
  one of them at a time (`workspace_busy` otherwise); a task session starts them in background
  Bash, which wakes it when they end (see [Task sessions](../task-session/module.md)).
- **Make only approved small changes in the primary worktree.** A very small change, such as a
  typo, a one-line fix or a wording correction, may be made by the main agent directly in the
  primary worktree, but only after it said what it would change and why the change is small and the
  developer approved that specific change
  ([requirements](requirements.md#req.main-session.small-change)). Besides it, the primary
  worktree sees only housekeeping that regenerates derived files, such as the registry mirror, and
  the commit of the worker configuration alone
  ([requirements](requirements.md#req.main-session.tasks-own-changes)).
- **Ask the developer from the main session only.** A task never asks the developer in place: a
  task session gathers every decision it needs and escalates them together to the main agent,
  which decides those its authority covers, puts the rest to the developer at once, and answers
  the session once with every answer
  ([requirements](requirements.md#req.main-session.batched-decisions)).
- **Have a plan reviewed when it deserves it.** The task-session guidance presents `plan_review` as
  optional: nothing requires it before `task-validation` or `delivery`, and a task session runs it
  when it chooses or its task brief asks for it. The session writes the plan itself, possibly
  starting from an `understand` plan, and leads the discussion over several runs: it answers every finding
  of an iteration, accepting it and revising the plan or rejecting it with its reason, and runs
  `plan_review` again with the previous run as `--input` and the answers as `--accept` and
  `--reject`, until the verdict is `accepted`. A finding the reviewer maintains after the session
  rejected it, and that the session still rejects, is a disagreement it does not iterate on again
  but escalates to the main agent, stating the answer in its next run
  ([requirements](requirements.md#req.main-session.task-session-plan-review)).
- **Keep the decision log.** Each session records in the task's
  [decision log](../../glossary.json#concept.decision-log) what it did without the developer, with
  its reason. The task session, which starts the task's runs and decides its ordinary questions,
  records every non-`ok` result of the runs it starts and every choice it made, including the
  decisions and problems of a [workflow result](../../glossary.json#concept.workflow-result), which
  nothing else writes there
  ([requirements](requirements.md#req.main-session.task-session-decision-log)); the main agent
  records every choice it made for the task
  ([requirements](requirements.md#req.main-session.decision-log)), and `concorde task answer`
  appends its answers to the session's reports. The log is committed to the primary branch when the
  task ends and so outlives the local history.
- **Merge delivered work.** Merge, without asking the developer's authorization, a task branch
  that `delivery` committed, from the primary worktree with `concorde task merge`, never with
  `git merge`: it holds the [merge lock](../../glossary.json#concept.merge-lock) so merges of
  several main sessions never interleave, runs `concorde spec-validation` on the primary branch, or
  exactly the `--check` commands given, undoes a merge whose checks fail and closes the task.
  Retry a `merge_busy`, and a `workspace_busy` once the task's run ended; have the task's session
  resolve a conflict by merging the primary branch into its task branch and delivering again, and
  after a `concorde update` that installed a new Protocol copy have the session of each open task
  merge the primary branch the same way and validate again, the only merges a task session makes;
  handle a failed check as new work, never by discarding
  someone's change. Finish a merge that a `merge_incomplete` refusal names before anything else,
  with `concorde task merge <task> --resume`, or `--abort` when the merge commit is no longer the
  primary branch's head, and leave a `merge_diverged` primary branch to the developer. Act on every
  warning of `task merge` and `task close`: each names a decision log nobody wrote in, or a Claude
  Code task session whose transcript the close could not keep or that it could not remove, with the
  command that removes it by hand; and on a close's `decision_log_uncommitted`, fix what Git
  refused in the primary worktree and run the same close again.
- **Keep reports reachable.** A Claude Code session's name does not survive a restart or a resume
  of the session, so the name a task session was started with may no longer reach the main agent.
  The task-session guidance therefore has a task session record every report with `concorde task
  report` before it sends it, to the main agent's session the command prints from the task record
  at that moment, and, when SendMessage reaches no session of that name, wait in background Bash
  with `concorde task wait <task> --rebound <name>` and send the same report again to the name it
  returns ([requirements](requirements.md#req.main-session.task-session-report-recorded)). The main
  agent records its answer with `concorde task answer` before it sends it. When ListAgents reports
  for its own session a name other than the one it gave its tasks, such as after a resume, the
  main agent lists the tasks not ended whose record names its former name with `concorde task
  list --main <former> --state open,active,delivered,merging`, rebinds each to its current name
  with `concorde task rebind`, and reads their unanswered reports, those `concorde task show` lists
  with no answer, before anything else
  ([requirements](requirements.md#req.main-session.reconcile-after-restart)). An answer it recorded
  may never have been sent, since the restart may have come between `concorde task answer` and
  SendMessage, so it also sends again, to the session of each such task whose last report has an
  answer, the latest answer recorded, naming the reports it answers by number; every answer names
  them, and a task session treats an answer to a report it already acted on as nothing to do
  ([requirements](requirements.md#req.main-session.reconcile-resend-answer)). An ended task needs
  none of this: it has no task session left, and its merge or close answered every report still
  unanswered when it ended.
- **Report.** Close each piece of work with a short summary for the developer: what was merged,
  what was decided on the developer's behalf, and what is still open.
- **Use the project's terms.** Every session of the project starts with all the terms of its
  worktree's glossary: the Concorde block of `CLAUDE.md` imports the glossary file, which Claude
  Code loads at launch, in main and task sessions alike. The guidance tells the main agent and every
  task session to use each term exactly as defined, with the developer and in task goals, decision
  logs, escalations, commit messages and Specs; never to coin a synonym; and to raise a missing or
  no longer fitting definition instead of working around it, changing the glossary through a task.
  A SessionStart hook could not carry the terms: Claude Code cuts a hook's output at 10,000
  characters, while a project's glossary is usually longer.

## Escalation policy

A result that is not `ok`, or a refused `concorde` command, carries an
[error chain](../../glossary.json#concept.error-chain); the guidance tells the main agent to read it
in full, since the origin says what went wrong and each link says why that level could not handle
it. Spec tooling is the exception: its commands, such as `spec-validation`, `registry`, `grant` and
`build`, and the Spec MCP server refuse with Spec tooling's own
[error record](../../spec-tooling/spec/errors.md#contract.spec.error) — a code, a message, why it is
an error, where, how to fix it and its causes — which is no link of the chain, so that
`concorde task escalate` refuses a file holding one with `invalid_error`. As
[Tracing](../../tracing/contracts.md#where-links-appear) requires of any Module that receives such
an error and cannot handle it, the guidance tells the main agent and task sessions to translate the
record into a `component` link of actor `Spec tooling (concorde <command>)`, its detail keeping the
record's message, reason, location and remediation and its causes being the record's causes
translated the same way, to save that link in a file and to escalate with it as `--error-file`
([requirements](requirements.md#req.main-session.spec-tooling-errors)). The main agent decides ordinary design uncertainty itself — naming, internal structure, task
order, a clarified re-run, splitting a task — and records and reports the choice. Among the
questions the work raises, it asks the developer first only for a decision with major impact:
changing what a Module promises to its users or the project's direction, contradicting an earlier
developer decision, discarding work or data, doing something an ordinary revert cannot undo,
touching security or credentials, or needing more resources than the developer set; in doubt it
records its reasoning and asks. The choices and approvals the sections of this guidance reserve to
the developer — a workflow's mode, the models of a missing worker configuration and a small change
in the primary worktree — stay the developer's besides. A task never asks the
developer in place: a task session escalates every decision it needs together, and the main agent
answers them together, asking the developer at once about all those it may not decide. An
escalation is never a summary: `concorde task escalate` adds its own link, with the reason it may
not decide, on top of the chain, records it in the task and prints it rendered for the developer; a
decision of major impact that no error carries is escalated as that link alone.

The decision log and the escalation both belong to a task, so they cover the runs of a task. An
[unbound run](../../glossary.json#concept.unbound-run) belongs to none: when one is not `ok`, the
guidance tells the main agent to show the developer its whole chain as rendered, on the command's
standard error, and, when the failure leads to work, to open a task for that work and escalate there
with the run's result file, `--error-file .concorde/unbound/<run-id>/result.json`, since `--run`
names only runs of the task's own workspace
([requirements](requirements.md#req.main-session.unbound-failure)).

## Worker models

Every [worker](../../glossary.json#concept.worker) runs only on what the worktree's
[worker configuration](../../glossary.json#concept.worker-configuration), the tracked
`.concorde/workers.json`, enables and chooses per
[worker id](../../glossary.json#concept.worker-id), never on the developer's own pi or Claude Code
settings; it runs on pi, although the main agent runs on Claude Code, unless the file chooses Claude
Code for it. No worker runs without the file, which the installer does not write: the guidance tells
the main agent, when the project has none, to ask the developer which models workers may use and
which is the default, and to write the file with its required enabled models and a default model
and commit it alone on the primary branch before any Operation runs
([requirements](requirements.md#req.main-session.worker-configuration-first)). It describes the
enabled models, each named by a project model name that depends on no installation and each with an
optional level of its own, the refusals of a model that is not enabled and of a worker without a
model, and which level a worker takes. It describes the developer's untracked [model
map](../../glossary.json#concept.model-map), which gives each project model name its local id on pi
or Claude Code, and its refusals of a missing or unreadable map and of a model it does not map for
the worker's program; since the map belongs to the developer's machine, the guidance tells the main
agent to change it only when the developer asks or agrees, and to tell the developer the entry the
map needs when the file gains a model
([requirements](requirements.md#req.main-session.model-map-developers)). The guidance tells the
main agent to change the file only when the developer asks, by editing the JSON directly and
preserving unrelated entries, adding every model it names to the enabled models; there is no
editor. It chooses Claude Code for a worker by setting that entry's `backend` to `claude`; the
chosen program must be installed when a worker launches, not when the file is edited. A change
meant for future tasks is committed alone directly on the primary branch, one of the changes the
main agent may make in the primary worktree outside a task
([requirements](requirements.md#req.main-session.tasks-own-changes)), never while a merge is
unfinished; a task may change its own copy, which reaches the primary branch when the task merges
([requirements](requirements.md#req.main-session.model-change-commit)). The separate
`scripts/available_models.py --backend pi|claude [--json]` supplies optional suggestions without
Git or inference API calls, with the project model names the map already gives each candidate and
the map's pi ids pi no longer lists. Discovery does not gate custom/offline configuration or impose an extra
question flow when the developer already chose a model.

## Questions without a task

The guidance tells the main agent that `understand`, `survey`, `spec_review`, `spec_panel` and
`code_review` (a change review with `--base`, a Module review without) also run [unbound](../../glossary.json#concept.unbound-run), in a
worktree without a workspace binding such as the primary worktree, on the Modules `--modules` names.
Such a run works on an [unbound checkout](../../glossary.json#concept.unbound-checkout) of that
worktree's `HEAD`, so a task merged there meanwhile does not disturb it and uncommitted changes are
not examined; its result has `workspace` null and names the examined commit as `commit`, an
`--input` of such a run must be unbound too, and they change no
[Spec](../../glossary.json#concept.spec) or code, since an unbound run launches only reading
workers. It uses them for a question or a review that does not justify a task, such as understanding
a Module before a change is agreed.

## Workflows

For a task that follows a known procedure the guidance tells the main agent to have its
[workflow](../../glossary.json#concept.workflow) run instead of sequencing the runs by hand: open the
task and name in its task brief the workflow, its Module and its
[mode](../../glossary.json#concept.workflow-mode); the task session starts the workflow inside the
task worktree, since like every run it works on the workspace of the worktree it starts in and
never names the task: it runs the installed `/concorde-<name>` workflow. The main agent asks the
developer which mode to use unless the developer already said; interactive suits a developer who
wants the decision points settled before the workflow goes on, by the main agent or by the
developer, no-ask one who wants the result later. A task session runs the
workflow in the mode its task brief names, and in interactive mode when the task brief names none
([requirements](requirements.md#req.main-session.task-session-workflow)).

When the workflow ends `awaiting_decision`, the session escalates every pending
[decision point](../../glossary.json#concept.decision-point) at once, with the
[workflow result](../../glossary.json#concept.workflow-result) as `--error-file`, whose chain names
each point with its options and recommendation; the main agent decides those its authority covers,
puts the rest to the developer at once and answers the session with every answer, and the session
starts the same workflow again with its `answers` keyed by each step's base key, its
[step key](../../glossary.json#concept.step-key) without a restart label or answer digest, each key
holding every answer given for that step so far, not only the newest
([Workflows](../../execution/workflows/module.md) defines the arguments). The session reads the
workflow result from the file Workflows saves in the workflow's node beside the workspace's
[workflow record](../../glossary.json#concept.workflow-record), in the task's workspace folder, and
treats it like a run result: it copies the result's decisions and problems into the task's decision
log, since Workflows keeps its record apart from the task and in no-ask mode those are decisions
taken without the developer, gives the decisions in its own report and escalates a result that is
not `ok` with the saved workflow result as `--error-file` and a decision of major impact with its
own link alone. The main agent reads every problem's chain and merges a delivered task. The guidance names the
[brownfield workflow](../../glossary.json#concept.brownfield-workflow) as the way to describe a
project whose code came before its Specs, right after installation and initialization, and
nowhere else, in a task opened for the root Module, or for a created Module to split further.

## Issues

[Issues](../../glossary.json#concept.issue) are project-level: the primary worktree keeps them and
every session and run sees the same records at once. The guidance tells the main agent and task
sessions to manage them through the [project MCP server](#the-project-mcp-server)'s Issue tools,
`issue_list`, `issue_show`, `issue_report`, `issue_close`, `issue_reopen` and `issue_check`, which
answer as `concorde issues` does and record the session that called them, which the command cannot
know; the command answers the same way and stays the path for a task session's shell and for the
runs a session starts.

**Recording.** The session that meets a concrete problem it will not fix now decides whether it
deserves an Issue; a worker finding or an Operation error is input to that decision, and a review
Operation may report the problems it finds itself. Before recording, the session reads the Issues of
the Module concerned, `issue_list` filtered by that `module` and by `status`, the open ones and the
closed ones when the problem may have been fixed before, rather than the whole project's list, which
outgrows a tool result, and `issue_show` for a possible match, and appends a report to the Issue
that already tracks the problem, at the revision `issue_show` printed, rather than create another;
it reopens a closed match whose closure the observation calls into question. Every report carries a
complete description, impact, basis and evidence, a **tier** that says who may handle the
problem ([Issues' tiers](../../issues/module.md#tiers)): `suggestion`, `obvious-fix`,
`preferred-fix` or `decision-needed`, and a **[severity](../../glossary.json#concept.issue-severity)**
that says how much it matters ([Issues' severities](../../issues/module.md#severities)): `critical`,
`high`, `medium` or `low`, which the guidance explains in a few words each. Recording never stops
the reporter and schedules nothing.

**Tiers decide who fixes.** Reporting and fixing are separate: a review Operation only reports, and
fixing is later work of a task. A task session working a task may fix an `obvious-fix` Issue
itself, and a `preferred-fix` one too, reporting the fix it chose to the main agent; it never
settles a `decision-needed` Issue, which it escalates, naming the Issue by its identity, for the
main agent to decide or put to the developer. A `suggestion` blocks nothing. The main agent decides
which Issues a task takes up, starting from the most severe ones that `issue_list` sorted by
`severity` lists first among the open Issues, and names them in the task, with `concorde task open --resolves` or
`task_resolve`, so the task's merge closes them as `resolved` with the merge commit as evidence;
starting, fixing or delivering a task changes no Issue. An Issue closed for another reason, or fixed
without such a task, is closed with `issue_close`, `duplicate` naming another open Issue or
`not-actionable`, with a note and evidence whose meaning the closer answers for; recurrence uses
`issue_reopen`, preserving history. On `stale_issue`, read the record again before deciding to
retry.

**After a review.** The review Operations, `spec_review`, `spec_panel` and `code_review`, report
every finding as an Issue with the severity and tier their reviewer or chair gave it, and their result names each
finding's Issue, the earlier Issues that still stand and those the review found resolved. The
guidance tells the task session to handle them like any other Issue of its task, by their tier, in
later `specify` or `implement` work, never in the review, to escalate a `code_review` finding that
challenges the Spec, usually `decision-needed`, rather than change the promise itself, and to close
each Issue the review found resolved: through its task with `task resolve` when the task fixed it,
otherwise with `issue_close` as `resolved`, naming the review's run as evidence.

**A Module review.** Besides judging a task's change, `code_review --scope module` judges each named
Module's whole code against all of its Specs, one reviewer per Module
([Code review](../../execution/operations/code-review/module.md#two-scopes)). The guidance names it
and when to use it: a whole-Module check after a large change, on code written before its Specs or
by an earlier version, or on a project just adopted; unbound, in the primary worktree, it needs only
`--modules`.

**The Issue system's own failures.** A refusal of the Issue tools or command that is a failure of the
Issue system itself, such as a busy merge lock, an unfinished merge or a failed commit, is never
recorded as an Issue: a session that met it for a task carries its error chain in the task's
decision log and escalation, as it would any other failure, and a run carries it in its result. An
Issue tool or command needs no task, and a failure the main agent met for none has no decision log
or escalation to carry it, so the guidance tells the main agent to show the developer its whole
chain at once, as it does an [unbound run](../../glossary.json#concept.unbound-run)'s, and to open
a task only when the failure leads to work
([requirements](requirements.md#req.main-session.issues-failure-no-task)). A busy merge lock is
waited for (`register_wait`) and the write asked again. Two of these failures concern a record in the
primary worktree, which the main agent alone puts right: after `recovery_failed`, a record a write
published stays uncommitted until the cause is fixed and `concorde issues recover`, which has no
tool, puts it back; after `uncommitted_change`, the record holds a change no Issue write made, to be
inspected and reverted, never committed by hand. A task's merge first puts back what a killed Issue
write left, and its `primary_dirty` names any record that recovery left the same way.

## Develop installs

In a [develop install](../../glossary.json#concept.develop-install), where the developer also
changes the Concorde the project runs, the installed skill and `CLAUDE.md` block end with
[Dogfooding](../../dogfooding/module.md)'s own section: watch Concorde's runs, never change Concorde
from the project, and report [Concorde defects](../../glossary.json#concept.concorde-defect) to the
[Concorde repository](../../glossary.json#concept.concorde-repository). Everything above holds
unchanged; a normal install carries no such section.

## The project MCP server

The [project MCP server](../../glossary.json#concept.project-mcp-server) presents these tools; the exact tools and
events are in the [contracts](contracts.md).

<a id="current-code"></a>

**Current code.** The server process lives as long as its Claude Code session, which may be hours,
while Concorde itself changes under it: a task merge in Concorde's own checkout, or
`concorde update` in an installed project. Code loaded once would then keep answering with the
rules and record formats it started with, and refuse the records the new code writes. So the server
runs none of its tools itself. Each call runs `concorde project-mcp --call <tool>` with the
`concorde` of the primary worktree as it is when the call arrives, its `.concorde/bin/concorde` or,
in Concorde's source checkout, its `scripts/concorde.py`, as a process of its own; the call's
arguments and the session's provenance go to it as one JSON object, and its answer or refusal is
the tool's. A waiting tool works the same way: the wait `register_wait` registers is that
`concorde`'s `concorde task wait`, run as a process the server watches, and the merge `task_merge`
starts is the very process the call ran in, which, having taken both locks and answered, replaces
itself with `concorde task merge`. What stays in the server is what needs a process that lives with
its session: the MCP session itself, the channel, and the wait and merge processes it watches. A
call whose process gives no answer is refused with the server's own `call_failed` link, naming the
command and what it printed. Each answer also says which tools the current code has; when they
differ from those the session was given, the server tells its session that its tools changed, and
Claude Code lists them again. Only the server's own session code, its few protocol messages and its
instructions, stays what the session started with until the next session.

- **Queries**: `task_list`, `task_show`, `trace_show` (one node, down to a `depth`, so a large
  trace need not be read whole), `run_result`, `workflow_report` and `locks`, which says who holds
  the merge lock and each task's [workspace lock](../../glossary.json#concept.workspace-lock).
- **Short writes** with structured arguments: `task_open`, `task_escalate`, whose error chain link
  is typed arguments rather than a command line to quote, `task_report`, `task_answer`,
  `task_rebind`, `task_resolve` and `task_close` without a merge.
- **Issues**: `issue_list`, filtered by `status`, `module`, `tier` and `severity` and sorted by
  severity as `concorde issues list` is, `issue_show` and `issue_check` read the project's
  [Issues](../../glossary.json#concept.issue), and `issue_report`, `issue_close` and
  `issue_reopen` write them, each as `concorde issues` does and without waiting for the merge lock
  an Issue write takes, refused at once with `merge_busy` while another process holds it. Each
  write tool's description also says that the write first puts back what a killed Issue write
  left, and how its `recovery_failed` and `uncommitted_change` refusals are put right, recovery
  itself being `concorde issues recover`'s alone. A report
  is checked against the session's worktree, where its evidence lies, and recorded as the session's:
  `task-session` with its task in a task worktree bound as a workspace, `main-agent` otherwise.
- **Long work**: `task_merge`, which never waits for a lock. It takes the task's workspace lock and
  the [merge lock](../../glossary.json#concept.merge-lock) at once or is refused at once, with
  `workspace_busy` or `merge_busy` naming who holds the busy one: the holder's command, process,
  start time, Claude Code session and task. The call's process takes them and, when it gets both,
  becomes `concorde task merge`, a process of its own session, keeping both locks: the `flock`
  belongs to the open file description, which survives the change of program, and the server never
  holds either, so the lock belongs to the session's work, never to the server, and is released
  when the merge ends, however it ends, even when the session and its server end first. It returns
  at once with the merge it started, not the merge's result, which a channel event or the returned
  wait command delivers later.
- **Workflow steps**: `workflow_step`, which the
  [step agents](../../glossary.json#concept.step-agent) of a [workflow](../../glossary.json#concept.workflow) call, one call per relay, with the step
  request as an object. It runs `concorde workflow step --json <request> --wait <wait>`, waiting at
  most 100 seconds, with the `concorde` of the session's worktree, the Git worktree
  `CLAUDE_PROJECT_DIR` or else the server's working directory lies in, which for a task session is
  its task worktree, and answers with the step outcome that command printed. It refuses, with
  `unbound_worktree`, a session whose worktree has no
  [workspace binding](../../glossary.json#concept.workspace-binding), such as the main agent's in
  the primary worktree, since a workflow runs only in a bound workspace. It exists because of where
  the server runs: the step command is a process the server started, so the
  [detached run](../../glossary.json#concept.detached-run) it starts depends on neither the
  relaying agent's turn nor a background command of the session, and lives until its run ends
  ([Workflows](../../execution/workflows/module.md#steps-through-the-server)). The server answers
  these calls, which wait, each on a thread of its own, so the session's other calls are not held up
  meanwhile.
- **Waiting**: `register_wait` asks to be woken when a task becomes `delivered`, `merging`,
  `closed` or `failed`, when a task is rebound to a main agent's session other than a named one,
  when a run ends, or when a lock is released. The server watches by running the matching
  `concorde task wait`, which waits without polling, blocking on the lock itself or on the kernel's
  notice of each new holder, and wakes its session with a [Claude Code channel](#channels) event
  with that command's answer when it happens. The wait process ends with the server. It only
  notifies: it never takes a lock for the session it wakes, which asks again and may be refused
  again.

A merge through the server, from a refusal to the merge's end, with who holds the locks at each
stage: the call's process takes them and keeps them as it becomes the merge, until the merge ends;
the server and the woken session never hold them.

```d2 illustrative
shape: sequence_diagram
session: Claude Code session
server: Project MCP server
merge: "call process, then\nconcorde task merge"
busy: "A lock is held by another process" {
  session -> server: task_merge
  server -> merge: "run the call"
  merge -> server: "workspace_busy or merge_busy,\nnaming the holder"
  server -> session: "the refusal"
  session -> server: register_wait for that lock
  server -> session: "released: a wait_done event, or,\nwithout a channel, the returned\nconcorde task wait in background Bash"
}
granted: "Both locks are free" {
  session -> server: task_merge again
  server -> merge: "run the call"
  merge -> merge: take both locks
  merge -> server: "started, with the output files"
  server -> session: "started, with the output files\nand how the session is woken"
  merge -> merge: "become concorde task merge,\nkeeping both locks"
  merge -> merge: "merge, run the checks,\nclose the task"
}
ended: "The merge ends" {
  merge -> server: "exits, and the kernel\nreleases both locks"
  server -> session: "a merge_ended event, or, without a\nchannel, the background concorde\ntask wait returns"
}
```

Using the server is recommended, not enforced. The kernel's `flock` stays the only lock: the CLI
and the runs of task sessions take the same locks directly, so both paths see each other's
holders. The server is the better path for the main agent whenever it would otherwise wait:
`task_merge` instead of a `task merge --wait` that blocks a background command for minutes, and
`register_wait` instead of watching a task. For workflow steps it is the path the Claude Code
workflow adapter always takes, since a step may outlast many relays. The CLI remains the way for
everything else: `task session`, the runs a task session starts itself in background Bash, the
Issues it writes from its shell, and anything the server does not present.

<a id="channels"></a>

**Channels.** Claude Code delivers a server's `notifications/claude/channel` only to an
interactive session started with that server as a channel. Channels are a research preview of
Claude Code: a self-built server needs `--dangerously-load-development-channels server:concorde`
when the session starts, which Claude Code confirms once, and they need Anthropic authentication
(claude.ai or a Console key) and an organization that has not disabled them (`channelsEnabled`).
The guidance tells the developer to start the main agent's session in the primary worktree with
`claude --dangerously-load-development-channels server:concorde`. A background session is never
woken by them: a probe on 2026-09-29 (Claude Code 2.1.284) started a `claude --bg` session with that
flag, whose server loaded and registered a wait, and the session stayed idle when the lock it waited
for was released; `claude -p` registers no channel at all. So task sessions, which are background
sessions, get the server without a channel ([Task sessions](../task-session/module.md)). A server
cannot learn from Claude Code whether it is a channel, so it reads it from the command line of the
interactive `claude` above it, one whose standard input is a terminal; when it has none,
`register_wait` says so and returns the equivalent blocking `concorde task wait` command, and
`task_merge` returns the `concorde task wait … --lock workspace` that returns when the merge ends,
to run in background Bash, which wakes the session when the command ends. An organization that
disabled channels drops the events silently; the guidance tells the agent to use the background
Bash form then.

**Task sessions** receive the server too, with the same tools: a task session may query its task
or register a wait, which answers it with the `concorde task wait` command for its background Bash
since it has no channel, its workflows' step agents start their steps through `workflow_step`, and
the developer does not consider its reach to other tasks' management a problem, so there is no split
by role. The guidance still tells a task session never to merge or
close its task. [Workers](../../glossary.json#concept.worker) never receive it: they launch with an
empty MCP configuration.

## Spec queries

The main agent may configure the Spec MCP server for its own session, to ask which Modules exist,
what a Module's context is, or what grant a [task type](../../glossary.json#concept.task-type)
gives. The server answers from the Specs of the worktree it is rooted in — the primary worktree for
the main agent — and workers never receive it.

## Why it is built this way

The main agent never changes the primary worktree's Specs or code beyond a small change the
developer approved: its view there is the whole project, so nothing would bound or evidence a
change made directly, and the primary worktree must stay clean to merge; the developer's approval
of the specific change stands in for that evidence where a task would cost more than the change.
Inside a task worktree a direct change is bounded by the task and evidenced by `task-validation`
and `delivery`, so task sessions may change Specs and code there themselves. Every `concorde`
command that works on a task's workspace is the task worktree's own command, run from that
worktree, because only the task branch holds the Specs,
[Protocol copy](../../glossary.json#concept.protocol-copy) and checks the task changes, and only
that worktree's binding names the task's workspace. Which Framework code the command runs
is [Distribution](../../distribution/module.md)'s concern, not the guidance's: in an installed
project a task worktree's command ordinarily runs the installed Framework shared with the primary
worktree, unless the task reinstalled Concorde there, while in Concorde's own source checkout it
runs the task branch's code.

The main agent hands every task, even a single one, to a task session, so that it stays free to
talk with the developer and to answer every session while tasks run, and every task runs under a
boundary; a task session's writes are confined to its task by the
[session boundary](../../glossary.json#concept.session-boundary), which
[Task sessions](../task-session/module.md) obtains from the Harness, while the main agent stays
unrestricted and alone merges; merging needs no authorization because `delivery` only commits what
it found ready, and a merge is ordinary, revertible Git.

The escalation policy balances the same way: deciding ordinary questions keeps work moving,
recording and reporting them keeps them reviewable, and reserving major-impact ones protects
decisions only the developer may make. Gathering a task's decisions into one escalation, and the
developer's answers into one reply, keeps the developer's attention in one place, the main session,
and asks for it once per escalation rather than once per question.

## Down the levels

The providers the main agent reaches down the levels of work.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../glossary.json#concept.task) — its branch, its worktree bound as
a workspace, and its record — and the [decision log](../../glossary.json#concept.decision-log): the
workspace of level 2, which a task session works. `concorde task show` lists the task's runs,
deliveries and task sessions and the holder of its [workspace
lock](../../glossary.json#concept.workspace-lock), read from what Execution recorded, so the main
agent learns a task's progress from one command, with the task sessions' reports and their answers.
The guidance relies on the record naming the main agent's session a task session reports to, which
`concorde task rebind` changes, on `concorde task report` recording a report before it is sent and
`concorde task answer` marking it answered, and on `concorde task wait --rebound` returning the new
name without polling. Each task's own worktree is what keeps parallel tasks from mixing changes;
opening, merging and closing tasks are the main agent's responsibility, and the log is written by
the main agent and the task's session alike. The guidance relies on `concorde task merge` holding
the merge lock and undoing a merge whose checks fail, and tells the main agent to retry a
`merge_busy`, to have the task's session resolve a conflict in the task worktree, and to treat a
failed check as new work rather than discard a change. It also relies on Tasks refusing `open`,
`merge`, `close`, `session` and `escalate` with `merge_incomplete` after a merge was interrupted,
all but the merging task's `merge --resume` and `merge --abort`, while `list` and `show` stay
available to inspect it, and tells the main agent to finish that merge first with `--resume` or
`--abort` rather than to work around the refusal: checking the merge again is the default, since the
recorded checks decide as they would have, and only a primary branch changed by hand after the merge
goes to the developer. A task session has no authority to finish a merge, so its guidance sends such
a refusal to the main agent. The project MCP server presents Tasks' commands unchanged, answering
and refusing as each command does when it waits for no lock, whose results are the [task
records](../tasks/contracts.md#contract.tasks.record) and the other results of [Tasks'
commands](../tasks/contracts.md#commands); it starts `concorde task merge` with the two locks it
took, and runs the waits of `concorde task wait`, which Tasks provides for background Bash too.

<a id="uses-task-session"></a>

**Task sessions** starts the background Claude Code task sessions the main agent delegates tasks to
and ends them with their task. It applies to every task. The guidance relies on a task session never
merging its task into the primary branch or closing it, and on it reporting only to the main session
its task record names, which `--main` sets and the main agent rebinds. A task session's report or
escalation is its result travelling up to level 1: the main agent answers the escalations, all at
once, or asks for more, with SendMessage, reads every error chain it carries like any other, and
merges a delivered task itself.

<a id="uses-workflows"></a>

**Workflows** provides the [workflows](../../glossary.json#concept.workflow) the main agent names
in a task brief, their modes and the
[workflow result](../../glossary.json#concept.workflow-result) read when one ends. The guidance
relies on a workflow never opening, merging or closing a task and on its result keeping every
run's chain whole, so that a workflow's end is handled like a run's: an `awaiting_decision` result
makes the task session escalate every pending decision point at once, and the main agent answers
them all before the session starts the same workflow again with the answers. Workflows never
writes the decision log, so the guidance makes the task session copy a report's decisions and
problems there.

<a id="uses-execution"></a>

**Execution** runs the work a task session starts in its task worktree: `concorde run` for an
Operation and the [execution commands](../../glossary.json#concept.execution-command)
`concorde task-validation`, `concorde delivery` and `concorde scaffold`, each reading the
worktree's [workspace binding](../../glossary.json#concept.workspace-binding), and
the Operations that run [unbound](../../glossary.json#concept.unbound-run) in the
primary worktree. Each run returns a [run result](../../glossary.json#concept.run-result), in the
shape of Execution's [run result contract](../../execution/contracts.md#contract.execution.run-result),
which the session that started it can read without inspecting a worker, and none starts the next
one: that choice is the session's that started it. The task session records every non-`ok` result
of the runs it starts in the decision log, and reads its chain in full before deciding or
escalating. The project MCP server's `run_result` presents a run's saved result, and while the run
has none its [run progress file](../../glossary.json#concept.run-progress-file), unchanged; it
reads the run's [run lock](../../glossary.json#concept.run-lock) to tell whether it still runs and
waits for its release to learn that it ended, and reads the workspace lock Execution's runs hold.
Execution records no owner in a run's records, so the guidance and the server never take a run's
owner from them ([requirements](requirements.md#req.main-session.owner-recorded-by-coordination)).

<a id="uses-operations"></a>

**Operations** provides the [Operation](../../glossary.json#concept.operation)
catalog: which Operations exist, what each takes and which may run unbound. The guidance names
them, and the task session chooses which to run for a task's next step. What an Operation takes
and returns is its provider's, and the guidance relies on four of them directly.

<a id="uses-understanding"></a>

**Understanding** provides `understand` and `plan_review`. The task-session guidance relies on
`plan_review`'s iterations: a run given the previous run as `--input` must answer every finding of
it once, with `--accept` or `--reject`, its reviewer answers those answers, and its verdict follows
the findings that stand ([plan review](../../execution/operations/understanding/contracts.md#contract.understanding.plan-review)).
It relies too on an `understand` plan naming in `new_files` the files a change needs that do not
exist yet, for the task session to create and bind before the run that fills them.

<a id="uses-specification"></a>

**Specification** provides `specify`. The task-session guidance relies on it creating each new
Spec document a `specify` worker proposes, empty and registered in its Module's `owns`, and
refusing a proposed path that already exists
([New and deleted documents](../../execution/operations/specification/module.md#new-and-deleted-documents)),
so that a task session prepares implementation files for workers and never a Spec document.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_review` and `spec_panel`. The guidance relies on each reporting every
finding that stands as an Issue of the Module it concerns, closing none, and naming in its result
each finding's Issue, the earlier Issues that still stand and those it found resolved
([result](../../spec-tooling/spec-review/operation.md#contract.spec-review.payload)), with a
[review verdict](../../glossary.json#concept.review-verdict) derived from the Issues that stand.

<a id="uses-code-review"></a>

**Code review** provides `code_review`, which judges a task's change since its base or, with
`--scope module`, each named Module's whole code against all its Specs. The guidance relies on it
reporting every finding as an Issue, a `spec-challenge` finding among them, closing none, and
naming the earlier Issues that stand and those it found resolved, as Spec review does
([Code review](../../execution/operations/code-review/module.md#two-scopes)).

<a id="uses-commands"></a>

**Commands** provides the catalog of
[execution commands](../../glossary.json#concept.execution-command), the
deterministic runs `task-validation`, `delivery` and `scaffold` that a task session starts by name
in its task worktree. The guidance names them apart from the Operations, since they launch no worker
and a caller starts them without `run`.

<a id="uses-workers"></a>

**Workers** owns the [worker configuration](../../glossary.json#concept.worker-configuration),
which the guidance tells the main agent to edit directly; the guidance relies on Workers validating
the whole file when a worker launches and reporting a malformed one with `config_invalid`. The
separate discovery helper supplies suggestions without proving API access or gating edits.

<a id="uses-tracing"></a>

**Tracing** records the whole history of a task as its [trace](../../glossary.json#concept.trace),
a tree of [trace nodes](../../glossary.json#concept.trace-node) from its sessions down to each
worker round. For that history with its cost, the guidance points the main agent to
`concorde trace show <task>`, and to `concorde trace show <run-id>` for one run, which the
project MCP server presents as `trace_show`. The server also relies on Tracing's locks: their
holder lines name the holder's session and task, which is how a refusal says who holds a lock; a
held lock can be handed to a process that inherits its descriptor; and a wait for a release
blocks on the lock itself, as Tracing's [locks](../../tracing/contracts.md#locks) state. Every
refusal the server returns is a link of Tracing's
[error chain](../../glossary.json#concept.error-chain), in the shape of its
[error contract](../../tracing/contracts.md#contract.tracing.error), and `trace_show` answers as
Tracing's [trace view](../../tracing/contracts.md#contract.tracing.view).

## Beside the levels

Three providers serve the main agent without being a level below it.

<a id="uses-issues"></a>

**Issues** provides durable, project-level [Issue](../../glossary.json#concept.issue) records and
the bookkeeping command for [reports](../../issues/interface.md#contract.issues.report) and
[receipts](../../issues/interface.md#contract.issues.receipt), whose actions the project MCP server
presents as its Issue tools, unchanged. The guidance relies on status following dispositions,
[revisions](../../glossary.json#concept.issue-revision) detecting concurrent writes and every
report carrying its tier and severity. It tells sessions to inspect before recording, to fix by
tier, starting from the most severe Issues, to have a
task's merge close the Issues it resolves and never to report a failure of the Issue system as an
Issue. The command records these decisions; whoever disposes an Issue remains responsible for the
evidence.

<a id="uses-spec"></a>

**Spec core** provides the commands that check and regenerate the Specs a session works on:
`concorde spec-validation`, which reports every [structural check](../../glossary.json#concept.structural-check)
finding of a worktree's Specs, and `concorde registry --write`, which regenerates the
[registry](../../glossary.json#concept.registry) mirror after a Module's `module` block changed,
the housekeeping the main agent may do in the primary worktree. The task-session guidance tells a
session to check with `spec-validation` a realization entry it added before it commits it. The
guidance relies on these commands, like every command of Spec tooling, refusing with Spec tooling's
own [error record](../../spec-tooling/spec/errors.md#contract.spec.error), which a session
translates into a link of the chain before it escalates it ([Escalation policy](#escalation-policy)).

<a id="uses-spec-mcp"></a>

The **Spec MCP server**, a child of Spec tooling, answers read-only queries about Modules, context
and grants from the worktree it is rooted in. The main agent configures it for its own session only
when it wants to ask such questions; workers never receive it. Since a server rooted in the primary
worktree knows only the primary branch's Specs, the guidance tells the main agent that a question
about a task's Specs needs a server, or a `concorde` command, rooted in that task's worktree.

## Inside

How this Module is built: the guidance sources and what the build renders from them, and the
project MCP server.

```d2
mainsession: Main session {
  sources: Guidance sources {
    "prompts/main-session/"
  }
  guidance: Main-session guidance
  server: Server program {
    "src/concorde/project_mcp/"
  }
  sources -> guidance: authors
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** live under `prompts/main-session/` (`skill.md`, installed as the project
skill `.claude/skills/concorde/SKILL.md`; `claude-md.md`, installed into the project's `CLAUDE.md`;
and `task-session.md`, the first prompt `concorde task session` gives a task session) and are
rendered by Distribution's build into `generated/main-session/`. Their tests, under
`tests/concorde/main_session/`, check that the rendered guidance states every rule the
[scenarios](scenarios.md) describe; what the main agent then does is judgment no deterministic test
observes.

<a id="realization.main-session.project-mcp"></a>

The **project MCP server** lives in `src/concorde/project_mcp/`: `server.py` runs the stdio session,
finds the project, decides whether the session listens to it as a channel and sends channel events
from the threads that watch; `calls.py` runs each call in a fresh process of the primary worktree's
current Concorde and watches the wait and merge processes; `tools.py` is what that process runs,
mapping each tool to Tasks, Tracing, Issues and Workflows' records and taking the merge's locks.
Like the Spec MCP server it is a small hand-written JSON-RPC session with no MCP library, since its
wire is the same few messages plus one notification; it keeps its own session code rather than
reusing the Spec MCP server's, which is written for one read-only root with its tools fixed and
sends only from one thread. Its tests, under `tests/concorde/project_mcp/`, talk to it over a real
stdio connection and watch real locks, merges and channel events.

## Who relies on it

Three Modules consume what this one authors. [Distribution](../../distribution/module.md) renders
the guidance sources and installs the rendered guidance into a project;
[Dogfooding](../../dogfooding/module.md) appends its own section to the guidance in a develop
install and changes nothing else; and [Task sessions](../task-session/module.md) gives a task
session the rendered task-session guidance as its first prompt, so every task follows the method
this Module sets.
