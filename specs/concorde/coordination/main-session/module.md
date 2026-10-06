# Main session

## Purpose

Main session is the top of Concorde's levels of work, level 1. Its guidance makes an ordinary Claude
Code session in a project's primary worktree act as Concorde's
[main agent](../../glossary.json#concept.main-agent):

- Discuss work with the developer.
- Split work into [tasks](../../glossary.json#concept.task).
- Hand every task to a [task session](../../glossary.json#concept.task-session) and answer it.
- Keep each task's [decision log](../../glossary.json#concept.decision-log).
- Decide ordinary questions itself while escalating only major ones.
- Merge delivered tasks.
- Handle [Issues](../../glossary.json#concept.issue).

The method of working inside a task is part of this guidance too, as the task-session guidance. The
task level is the main agent's own work, which it always delegates. A task session starts with that
method in the guidance it is given. The guidance is advice to a model, not enforcement. Concorde
places no permission limits on the main agent. Nothing here constrains the developer.

For now the guidance serves Claude Code only. The main agent is a Claude Code session. Since a task
session runs on the main agent's own program, every task session is a Claude Code session too. But
the [workers](../../glossary.json#concept.worker) of their runs may run on pi. Distribution renders
and installs this [Module](../../glossary.json#concept.module)'s content. That content is composed
with the guidance the other installed [parts](../../glossary.json#concept.part) contribute
([Guidance by part](#guidance-by-part)). Beside the guidance the Module provides Coordination's
tools on the [project MCP server](../../glossary.json#concept.project-mcp-server). This server is
Distribution's host of the tools every installed part registers. Coordination's tools are a thin MCP
presentation of the task and lock commands through which a Claude Code session does the following:

- Queries and changes tasks.
- Takes a lock without waiting.
- Is woken when something it waits for happens.

## Core concepts

<a id="concept.main-session-guidance"></a>

The **[main-session guidance](../../glossary.json#concept.main-session-guidance)** is what Concorde
tells the main agent. Concorde installs it as the project skill and as a block of the project's
`CLAUDE.md`. It tells the Claude Code session opened in a Concorde project's primary worktree that
it is the main agent. It also gives that session a [working method](#the-working-method). Its
task-session part is the first prompt of every task session. Because the main agent's work is
judgment, the guidance is instructions, not a program. The project MCP server beside the guidance is
a program. It only presents commands and adds no rule beyond taking locks without waiting.
Everything that must hold regardless of judgment is enforced elsewhere:

- The worker harness enforces workers.
- Operations' own checks enforce Operations.
- `task-validation` and `delivery` enforce readiness.

Thus, an agent that ignores the guidance wastes effort but cannot widen a worker's boundary.

<a id="guidance-by-part"></a>

**Guidance by part.** At install, the guidance a main agent reads is composed from the installed
parts' sections. Each part contributes the sections about its own commands and tools. A part that is
not installed contributes nothing, so the guidance never tells an agent to use what the project
lacks. This Module's section comes first in each of the three compositions:

- The project skill.
- The task-session prompt.
- The `CLAUDE.md` block.

The other installed parts' sections of that kind follow in the order of Distribution's parts table,
as [Distribution](../../distribution/module.md#guidance-composition) composes them. This Module owns
Coordination's sections, the frame every other section fits in:

- The working method.
- The escalation policy.
- The task brief.
- Reports and the decision log.
- Tasks, task sessions and their merges.
- Coordination's tools.
- The method of working inside a task.

Each other part keeps its sections in `prompts/guidance/<part directory>/`, bound by its top Module.
Each section says what happens where a part it mentions is not installed. Coordination's own
sections say, for instance, how a task session delivers. Where the method part is installed, the
task session delivers with Method's `delivery`. Otherwise, the task session delivers with
`concorde task deliver`. Those sections also say that, only where the spec part is installed, a
merge runs `concorde spec-validation`. The sections that describe another part's commands are that
part's contribution, described here as the main agent reads them:

| Section | Contributed by | Present only where |
| --- | --- | --- |
| [The working method](#the-working-method), [Escalation policy](#escalation-policy), reports, merging, task sessions, Coordination's tools; in the task-session prompt, working inside the task, deciding and escalating, merging the primary branch and reporting | coordination | the coordination part is installed, without which there is no main agent and no task session |
| Project terms, Spec queries, `spec-validation`, `grant`, `registry --write` and translating Spec tooling's errors ([Spec queries](#spec-queries)); the glossary import of the `CLAUDE.md` block | spec | the spec part is installed |
| `concorde trace show` and reading an error chain | kernel | the kernel part is installed |
| [Worker models](#worker-models) | worker harness | the worker harness part is installed |
| Runs, their results and unbound runs ([Questions without a task](#questions-without-a-task)) | execution | the execution part is installed |
| [Workflows](#workflows), `workflow_report` and `workflow_step` | workflow | the workflow part is installed |
| [Issues](#issues) | issues | the issues part is installed |
| Method's Operations and their order, preparing the workers' environment, `plan_review`, `task-validation` and `delivery`, reviews and the brownfield workflow | method | the method part is installed; otherwise the task session delivers with `concorde task deliver` |
| What `concorde` is, `part_missing` and `concorde update` | distribution | always, since Distribution is installed with any part |
| [Develop installs](#develop-installs) | Dogfooding | a develop install, appended after every part's section |

What each section tells the main agent is described here once.

<a id="concept.task-brief"></a>

The **[task brief](../../glossary.json#concept.task-brief)** is how the main agent hands a task to
its session. Before it starts the task session, the main agent records these items in the task's
[decision log](../../glossary.json#concept.decision-log):

- The developer's decisions the task carries out.
- When a workflow applies, the workflow and its [mode](../../glossary.json#concept.workflow-mode).
- Anything the goal leaves out.
- What the main agent leaves for the session to decide.

Before it changes anything, the session reads the task brief. The main agent writes the task brief
for a task session, unlike a worker's [brief](../../glossary.json#concept.brief). An Operation
generates that brief from the worker's grant for each worker it launches.

<a id="coordination-tools"></a>

**Coordination's tools** are what this Module registers, for the coordination part, with the
[project MCP server](../../glossary.json#concept.project-mcp-server). This is the project's one
stdio MCP server that [Distribution](../../distribution/module.md) hosts and composes from what
every installed part registers. Each Claude Code session that loads it runs its own server process.
A fresh process of the Concorde the primary worktree's `concorde` runs at that moment answers each
call. Thus, a merge or a `concorde update` during a session changes the code that answers its next
call. That host behaviour is Distribution's. Coordination's tools are a presentation. The
`concorde task` commands stay the source of truth. Every answer and refusal of a query or short
write is the command's own. The tools' one rule of their own is that they never wait for a lock.
Thus, `task_merge` answers at once with the merge it started, and `register_wait` with the wait it
registered. The merge's result and the wait's answer arrive later. Among the tools are two queries
over other parts' records:

- `trace_show` over Tracing's traces.
- Where the execution part is installed, `run_result` over a run's result.

The other parts register their own tools beside them:

- The issues part registers the Issue tools.
- The workflow part registers `workflow_step` and `workflow_report`.

A tool of a part that is not installed is simply absent. The tools and how they wake a session are
explained [below](#the-project-mcp-server).

<a id="owners"></a>

**Owners.** The main agent starts each run of its own, an unbound Operation, in background Bash.
When the command ends, Claude Code wakes the main agent. A task session does the same with the runs
of its task. Several main sessions may work on one project at the same time. Without anyone asking,
the end of a run wakes only its **owner**. A run never has more than one owner. A session that wants
to hear of work it does not own asks for its own wake explicitly. It does this by registering a wait
with the [project MCP server](../../glossary.json#concept.project-mcp-server). That wake reaches
only the session that registered it:

| Work | Owner | How the owner is woken |
| --- | --- | --- |
| A run a main session starts, in background Bash | that session | Claude Code's own notification when the command ends |
| What a task session reports | the main session its task record names when it reports | the task session's SendMessage, once `concorde task report` recorded the report |
| A run a task session starts in its worktree | that task session, no main session | Claude Code's own notification in the task session; its main session hears of it in the task session's report |
| A run started by a command run by hand | no main session | nobody is woken |
| A wait registered with, or a merge started through, the [project MCP server](../../glossary.json#concept.project-mcp-server) | the session whose server it is | a channel event of that server, or, without a channel, the session's own background Bash running the equivalent `concorde task wait` |

Execution knows nothing of main sessions. It never records an owner. A run's owner is the session
whose background Bash started it. A task session reports to the main session named by the `main` in
its task's [task record](../../glossary.json#concept.task-record). First, this is the `--main` its
task session was started with. Then it is the name the main agent rebound the task to. Since nothing
unasked is pushed into a main session, a main session that does not own a run is never woken by that
run unasked. That main session asks with `concorde task show <task>`, which lists:

- The task workspace's runs with their status.
- The task's sessions with the main session each reports to.

Alternatively, that main session registers a wait for the run's end
([requirements](requirements.md#req.main-session.single-owner)).

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

The main agent carries out these steps:

- It agrees the change with the developer.
- It opens a task and records its task brief.
- It hands the task to a task session.

The task session carries out these steps:

- It runs the Operations and execution commands in the task worktree.
- It reads each [run result](../../glossary.json#concept.run-result).
- It delivers.

The main agent merges the delivered task. It reports what it decided on the developer's behalf,
here the back-off.

### What the main agent reaches

The main session is level 1 of Concorde's [levels of work](../../module.md#the-levels-of-work), the
top of Coordination. Nothing in Concorde calls it. The developer talks to it. The installed skill
and `CLAUDE.md` block are Concorde's only way to reach a session at all. It calls only downward. At
level 2, the main session opens a task and delegates it to a task session. From inside the task, the
task session starts workflows (level 3) in the task worktree. It also starts runs (level 4),
Operations and execution commands, in the task worktree. The main agent itself starts only unbound
runs, in the primary worktree. It reaches workers (level 5) only through an Operation. Otherwise,
the main agent touches Workers only to edit the worker configuration.

What comes back up is structured:

- Run results.
- Workflow results.
- Task-session reports and escalations.

Each failure carries its [error chain](../../glossary.json#concept.error-chain). The chain ends
here. The main agent decides what the escalation policy lets it decide. It records and reports that
decision. Otherwise, the main agent adds its own `main-agent` link. It then asks the developer, the
chain's last receiver.

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
- **Split into tasks.** Turn agreed work into [tasks](../../glossary.json#concept.task), opened with
  `concorde task`. Only across worktrees whose Modules and shared files do not overlap, run tasks in
  parallel. Run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Hand every task to a task session.** Never work inside a task worktree. Even for a single task,
  start one [task session](../../glossary.json#concept.task-session) per task with
  `concorde task session <task>`. Stay in the primary worktree, where the main agent does the
  following:

  - Discusses.
  - Opens and closes tasks.
  - Starts and answers task sessions.
  - Runs [unbound](../../glossary.json#concept.unbound-run) Operations.
  - Merges.
  - Reports.
  - Inspects Issues.
  - Changes the worker configuration.

  Before starting the session, record the task's
  [task brief](../../glossary.json#concept.task-brief) in its decision log. The session reads the
  task brief first. A task session is a background Claude Code session, on the main agent's own
  program. The command names the main agent's session with `--main`. The task session reports back
  with SendMessage. The main agent answers the task session the same way. Ending the task, by its
  merge or its close, stops its task sessions and removes them from Claude's session list. Ending
  the task keeps their transcripts in the task's [trace](../../glossary.json#concept.trace), so the
  main agent never removes the task sessions itself. The task session changes Specs and code in the
  task worktree directly or by running the following:

  - [Operations](../../glossary.json#concept.operation) with `concorde run <operation> …`.
  - The [execution commands](../../glossary.json#concept.execution-command)
    `concorde task-validation` and `concorde delivery`.

  The task session reads each [run result](../../glossary.json#concept.run-result). From the task
  worktree, the task session runs every `concorde` command that works on the task's workspace as
  that worktree's own command
  ([requirements](requirements.md#req.main-session.worktree-own-concorde)). The following commands
  run from the primary worktree:

  - Commands that open tasks.
  - Commands that merge tasks.
  - Commands that close tasks.
  - Commands that start task sessions.

  None of the commands that work on the task's workspace names the task. The task worktree's
  [workspace binding](../../glossary.json#concept.workspace-binding), which `concorde task open`
  wrote, tells every run what it works on:

  - The goal.
  - The Modules.
  - The branch.
  - The base.

  One workspace runs one of those Operations or execution commands at a time (`workspace_busy`
  otherwise). A task session starts them in background Bash, which wakes it when they end (see
  [Task sessions](../task-session/module.md)).
- **Make only approved small changes in the primary worktree.** Only after both of the following may
  the main agent make a very small change directly in the primary worktree
  ([requirements](requirements.md#req.main-session.small-change)):

  - The main agent states what it would change and why the change is small.
  - The developer approves that specific change.

  Examples of very small changes are:

  - A typo.
  - A one-line fix.
  - A wording correction.

  Besides that change, the primary worktree sees only the following
  ([requirements](requirements.md#req.main-session.tasks-own-changes)):

  - Housekeeping that regenerates derived files, such as the registry mirror.
  - The commit of the worker configuration alone.

- **Ask the developer from the main session only.** A task never asks the developer in place. A task
  session gathers every decision it needs and escalates them together to the main agent. The main
  agent decides those its authority covers. The main agent puts the rest to the developer at once.
  The main agent answers the session once with every answer
  ([requirements](requirements.md#req.main-session.batched-decisions)).
- **Have a plan reviewed when it deserves it.** The task-session guidance presents `plan_review` as
  optional. Nothing requires this Operation before `task-validation` or `delivery`. When the task
  session chooses or its task brief asks for it, the task session runs the Operation. The session
  writes the plan itself, possibly starting from an `understand` plan. The session leads the
  discussion over several runs. The session answers every finding of an iteration, accepting it and
  revising the plan or rejecting it with its reason. The session runs `plan_review` again with the
  following:

  - The previous run as `--input`.
  - The answers as `--accept` and `--reject`.

  The session repeats these runs until the verdict is `accepted`. If the reviewer maintains a
  finding after the session rejects it, and the session still rejects it, the finding is a
  disagreement. The session does not iterate on that disagreement again. The session escalates the
  disagreement to the main agent, stating the answer in its next run
  ([requirements](requirements.md#req.main-session.task-session-plan-review)).
- **Keep the decision log.** Each session records in the task's
  [decision log](../../glossary.json#concept.decision-log) what it did without the developer, with
  its reason. The task session starts the task's runs and decides its ordinary questions. The task
  session records every non-`ok` result of the runs it starts and every choice it made. These
  records include the decisions and problems of a
  [workflow result](../../glossary.json#concept.workflow-result), which nothing else writes there
  ([requirements](requirements.md#req.main-session.task-session-decision-log)). The main agent
  records every choice it made for the task
  ([requirements](requirements.md#req.main-session.decision-log)). `concorde task answer` appends
  the main agent's answers to the session's reports. When the task ends, the log is committed to the
  primary branch and so outlives the local history.
- **Merge delivered work.** From the primary worktree, merge a task branch that `delivery`
  committed, without asking the developer's authorization. Use `concorde task merge`, never
  `git merge`. The merge command holds the [merge lock](../../glossary.json#concept.merge-lock) so
  merges of several main sessions never interleave. The command runs `concorde spec-validation` on
  the primary branch, or exactly the `--check` commands given. After those commands, the command
  runs `concorde spec-validation` while a `concorde update` is not validated yet. The command undoes
  a merge whose checks fail. The command closes the task. Retry a `merge_busy`. Once the task's run
  ends, retry a `workspace_busy`. Have the task's session resolve a conflict by merging the primary
  branch into its task branch and delivering again. After a `concorde update` that installs a new
  Protocol copy, have the session of each open task merge the primary branch the same way and
  validate again. These are the only merges a task session makes. Handle a failed check as new work,
  never by discarding someone's change. Before anything else, finish a merge that a
  `merge_incomplete` refusal names with `concorde task merge <task> --resume`. When the merge commit
  is no longer the primary branch's head, use `--abort` instead. Leave a `merge_diverged` primary
  branch to the developer. Act on every warning of `task merge` and `task close`. Each warning names
  one of the following:

  - A decision log nobody wrote in.
  - A Claude Code task session whose transcript the close could not keep or that it could not
    remove, with the command that removes it by hand.

  On a close's `decision_log_uncommitted`, fix what Git refused in the primary worktree and run the
  same close again.
- **Keep reports reachable.** A Claude Code session's name does not survive a restart or a resume of
  the session, so the name a task session starts with may no longer reach the main agent. The
  task-session guidance therefore has a task session record every report with `concorde task report`
  before it sends the report. The task session sends the report to the main agent's session the
  command prints from the task record at that moment. When SendMessage reaches no session of that
  name, the task session waits in background Bash with `concorde task wait <task> --rebound <name>`.
  The task session sends the same report again to the name that command returns
  ([requirements](requirements.md#req.main-session.task-session-report-recorded)). The main agent
  records its answer with `concorde task answer` before it sends the answer. When ListAgents reports
  for its own session a name other than the one it gave its tasks, the main agent reconciles before
  anything else. This can happen after a resume. The main agent reconciles as follows
  ([requirements](requirements.md#req.main-session.reconcile-after-restart)):

  - Lists the tasks not ended whose record names its former name with
    `concorde task list --main <former> --state open,active,delivered,merging`.
  - Rebinds each to its current name with `concorde task rebind`.
  - Reads their unanswered reports, those `concorde task show` lists with no answer.

  Since the restart may come between `concorde task answer` and SendMessage, an answer the main
  agent records may never have been sent. For each such task whose last report has an answer, the
  main agent also sends the latest recorded answer again to the task's session, naming the reports
  it answers by number. Every answer names those reports. An answer to a report the task session
  already acted on gives the task session nothing to do
  ([requirements](requirements.md#req.main-session.reconcile-resend-answer)). An ended task needs
  none of this. An ended task has no task session left. Its merge or close answers every report
  still unanswered when the task ends.
- **Report.** Close each piece of work with a short summary for the developer:

  - What was merged.
  - What was decided on the developer's behalf.
  - What is still open.

- **Use the project's terms.** Every session of the project starts with all the terms of its
  worktree's glossary. The Concorde block of `CLAUDE.md` imports the glossary file. In main and task
  sessions alike, Claude Code loads that file at launch. The guidance tells the main agent and every
  task session to use each term exactly as defined in the following:

  - Exchanges with the developer.
  - Task goals.
  - Decision logs.
  - Escalations.
  - Commit messages.
  - Specs.

  The guidance tells those sessions never to coin a synonym. It also tells them to raise a missing
  or no longer fitting definition instead of working around it, changing the glossary through a
  task.
  A SessionStart hook could not carry the terms: Claude Code cuts a hook's output at 10,000
  characters, while a project's glossary is usually longer.

## Escalation policy

A result that is not `ok`, or a refused `concorde` command, carries an
[error chain](../../glossary.json#concept.error-chain). The guidance tells the main agent to read it
in full, since the chain gives these explanations:

- The origin says what went wrong.
- Each link says why that level could not handle it.

Spec tooling is the exception. Its commands include:

- `spec-validation`
- `registry`
- `grant`
- `build`

These commands and the Spec MCP server refuse with Spec tooling's own
[error record](../../spec-tooling/spec/errors.md#contract.spec.error). The record contains:

- A code
- A message
- Why it is an error
- Where
- How to fix it
- Its causes

The record is no link of the chain, so `concorde task escalate` refuses a file holding one with
`invalid_error`. When a Module receives such an error and cannot handle it,
[Tracing](../../kernel/tracing/contracts.md#where-links-appear) requires translation of the record.
The guidance tells the main agent and task sessions to translate it into a `component` link of actor
`Spec tooling (concorde <command>)`. The link's detail keeps the record's:

- Message
- Reason
- Location
- Remediation

The link's causes are the record's causes translated the same way. The guidance tells the main agent
and task sessions to save that link in a file and escalate with it as `--error-file`
([requirements](requirements.md#req.main-session.spec-tooling-errors)).

The main agent decides ordinary design uncertainty itself:

- Naming
- Internal structure
- Task order
- A clarified re-run
- Splitting a task

The main agent records and reports the choice. Among the questions the work raises, the main agent
asks the developer first only for a decision with major impact:

- Changing what a Module promises to its users or the project's direction
- Contradicting an earlier developer decision
- Discarding work or data
- Doing something an ordinary revert cannot undo
- Touching security or credentials
- Needing more resources than the developer set

When in doubt, the main agent records its reasoning and asks. The choices and approvals the sections
of this guidance reserve to the developer stay the developer's besides:

- A workflow's mode
- The models of a missing worker configuration
- A small change in the primary worktree

A task never asks the developer in place. A task session escalates every decision it needs together.
The main agent answers them together, asking the developer at once about all those it may not
decide. An escalation is never a summary. `concorde task escalate` adds its own link, with the
reason it may not decide, on top of the chain. The command records the chain in the task and prints
it rendered for the developer. A decision of major impact that no error carries is escalated as that
link alone.

The decision log and the escalation both belong to a task, so they cover the runs of a task. An
[unbound run](../../glossary.json#concept.unbound-run) belongs to none. When an unbound run is not
`ok`, the guidance tells the main agent to show the developer its whole chain as rendered on the
command's standard error. When the failure of an unbound run that is not `ok` leads to work, the
guidance tells the main agent to open a task for that work. For that failure, the guidance tells the
main agent to escalate there with the run's result file,
`--error-file .concorde/unbound/<run-id>/result.json`, since `--run` names only runs of the task's
own workspace ([requirements](requirements.md#req.main-session.unbound-failure)).

## Worker models

Every [worker](../../glossary.json#concept.worker) runs only on what the worktree's
[worker configuration](../../glossary.json#concept.worker-configuration), the tracked
`.concorde/workers.json`, enables and chooses per
[worker id](../../glossary.json#concept.worker-id). A worker never runs on the developer's own pi or
Claude Code settings. Unless the file chooses Claude Code for the worker, the worker runs on pi,
although the main agent runs on Claude Code. No worker runs without the file, which the installer
does not write. When the project has none, the guidance tells the main agent to ask the developer
which models workers may use and which is the default. The main agent then writes the file with its
required enabled models and a default model. Before any Operation runs, the main agent commits the
file alone on the primary branch
([requirements](requirements.md#req.main-session.worker-configuration-first)). The guidance
describes:

- The enabled models, each named by a project model name that depends on no installation and each
  with an optional level of its own
- The refusals of a model that is not enabled and of a worker without a model
- Which level a worker takes

The guidance describes the developer's untracked [model map](../../glossary.json#concept.model-map),
which gives each project model name its local id on pi or Claude Code. The guidance describes the
map's refusals:

- A missing map
- An unreadable map
- A model the map does not map for the worker's program

Since the map belongs to the developer's machine, the guidance tells the main agent to change it
only when the developer asks or agrees. When the file gains a model, the guidance tells the main
agent to tell the developer the entry the map needs
([requirements](requirements.md#req.main-session.model-map-developers)). The guidance tells the main
agent to change the file only when the developer asks, by editing the JSON directly and preserving
unrelated entries. When changing the file, the main agent adds every model it names to the enabled
models. There is no editor. The main agent chooses Claude Code for a worker by setting that entry's
`backend` to `claude`. The chosen program must be installed when a worker launches, not when the
file is edited.

A change meant for future tasks is committed alone directly on the primary branch, never while a
merge is unfinished. This is one of the changes the main agent may make in the primary worktree
outside a task ([requirements](requirements.md#req.main-session.tasks-own-changes)). A task may
change its own copy, which reaches the primary branch when the task merges
([requirements](requirements.md#req.main-session.model-change-commit)). The separate
`scripts/available_models.py --backend pi|claude [--json]` supplies optional suggestions without Git
or inference API calls. The suggestions include the project model names the map already gives each
candidate and the map's pi ids pi no longer lists. Discovery does not gate custom/offline
configuration or impose an extra question flow when the developer already chose a model.

## Questions without a task

The guidance tells the main agent that these also run
[unbound](../../glossary.json#concept.unbound-run):

- `understand`
- `survey`
- `spec_panel`
- `code_review` (a change review with `--base`, a Module review without)

They run in a worktree without a workspace binding such as the primary worktree, on the Modules
`--modules` names. Such a run works on an
[unbound checkout](../../glossary.json#concept.unbound-checkout) of that worktree's `HEAD`, with
these consequences:

- A task merged there meanwhile does not disturb the run.
- Uncommitted changes are not examined.

Its result has `workspace` null and names the examined commit as `commit`. An `--input` of such a
run must be unbound too. These runs change no [Spec](../../glossary.json#concept.spec) or code,
since an unbound run launches only reading workers. The main agent uses them for a question or a
review that does not justify a task, such as understanding a Module before a change is agreed.

## Workflows

For a task that follows a known procedure, the guidance tells the main agent to have its
[workflow](../../glossary.json#concept.workflow) run instead of sequencing the runs by hand. The
main agent opens the task and names these in its task brief:

- The workflow
- Its Module
- Its [mode](../../glossary.json#concept.workflow-mode)

The task session starts the workflow inside the task worktree, since like every run the workflow:

- Works on the workspace of the worktree it starts in
- Never names the task

The task session runs the installed `/concorde-<name>` workflow. Unless the developer already said,
the main agent asks the developer which mode to use. Interactive suits a developer who wants the
decision points settled before the workflow goes on, by the main agent or by the developer. No-ask
suits a developer who wants the result later. A task session runs the workflow in the mode its task
brief names. When the task brief names none, the task session runs the workflow in interactive mode
([requirements](requirements.md#req.main-session.task-session-workflow)).

When the workflow ends `awaiting_decision`, the session escalates every pending
[decision point](../../glossary.json#concept.decision-point) at once, with the
[workflow result](../../glossary.json#concept.workflow-result) as `--error-file`. The workflow
result's chain names each point with its options and recommendation. The main agent decides those
its authority covers. The main agent puts the rest to the developer at once and answers the session
with every answer. The session starts the same workflow again with its `answers` keyed by each
step's base key. The base key is its [step key](../../glossary.json#concept.step-key) without a
restart label or answer digest. Each key holds every answer given for that step so far, not only the
newest ([Workflows](../../workflows/module.md) defines the arguments).

The session reads the workflow result from the file Workflows saves in the workflow's node beside
the workspace's [workflow record](../../glossary.json#concept.workflow-record), in the task's
workspace folder. The session treats the workflow result like a run result. The session copies the
result's decisions and problems into the task's decision log for these reasons:

- Workflows keeps its record apart from the task.
- In no-ask mode, those are decisions taken without the developer.

The session gives the decisions in its own report. The session escalates a result that is not `ok`
with the saved workflow result as `--error-file`. The session escalates a decision of major impact
with its own link alone. The main agent reads every problem's chain and merges a delivered task.

The guidance names the [brownfield workflow](../../glossary.json#concept.brownfield-workflow) as
the way to describe a project whose code came before its Specs, right after installation and
initialization, and nowhere else. The workflow runs in a task opened for the root Module, or for
a created Module to split further.

## Issues

[Issues](../../glossary.json#concept.issue) are project-level: the primary worktree keeps them.
Every session and run sees the same records at once. The guidance tells the main agent and task
sessions to manage them through the [project MCP server](#the-project-mcp-server)'s Issue tools:

- `issue_list`
- `issue_show`
- `issue_report`
- `issue_close`
- `issue_reopen`
- `issue_check`

These tools answer as `concorde issues` does. They record the session that called them, which the
command cannot know. The command answers the same way. It stays the path for a task session's shell
and for the runs a session starts.

**Recording.** When a session meets a concrete problem it will not fix now, the session decides
whether the problem deserves an Issue. A worker finding or an Operation error is input to that
decision. A review Operation may report the problems it finds itself. Before recording, the session
reads the Issues of the Module concerned, rather than the whole project's list, which outgrows a
tool result. The session uses `issue_list` filtered by that `module` and by `status`. It reads the
open Issues. When the problem may have been fixed before, it reads the closed Issues too. For a
possible match, it uses `issue_show`. At the revision `issue_show` printed, the session appends a
report to the Issue that already tracks the problem, rather than create another. When the
observation calls a closed match's closure into question, the session reopens that match.

Every report carries these complete details:

- Description
- Impact
- Basis
- Evidence

Every report also carries a **tier** that says who may handle the problem
([Issues' tiers](../../issues/module.md#tiers)):

- `suggestion`
- `obvious-fix`
- `preferred-fix`
- `decision-needed`

Every report carries a **[severity](../../glossary.json#concept.issue-severity)** that says how much
it matters ([Issues' severities](../../issues/module.md#severities)):

- `critical`
- `high`
- `medium`
- `low`

The guidance explains each severity in a few words. Recording never stops the reporter. Recording
schedules nothing.

**Tiers decide who fixes.** Reporting and fixing are separate. A review Operation only reports.
Fixing is later work of a task. A task session working a task may fix an `obvious-fix` Issue itself.
It may fix a `preferred-fix` Issue too, reporting the fix it chose to the main agent. It never
settles a `decision-needed` Issue. It escalates that Issue, naming the Issue by its identity, for
the main agent to decide or put to the developer. A `suggestion` blocks nothing. The main agent
decides which Issues a task takes up. It starts from the most severe ones that `issue_list` sorted
by `severity` lists first among the open Issues. The main agent names those Issues in the task, with
`concorde task open --resolves` or `task_resolve`, so the task's merge closes them as `resolved`
with the merge commit as evidence.

None of these actions changes an Issue:

- Starting a task
- Fixing a task
- Delivering a task

When an Issue is closed for another reason, or fixed without such a task, it is closed with
`issue_close`. The closure uses `duplicate` naming another open Issue or `not-actionable`. It
includes a note and evidence whose meaning the closer answers for. A recurrence uses `issue_reopen`,
preserving history. On `stale_issue`, read the record again before deciding to retry.

**After a review.** These review Operations report every finding as an Issue with the severity and
tier their reviewer or chair gave it:

- `spec_panel`
- `code_review`

Their result names:

- Each finding's Issue
- The earlier Issues that still stand
- The Issues the review found resolved

The guidance tells the task session to handle these Issues like any other Issue of its task, by
their tier. It tells the task session to handle them in later `specify` or `implement` work, never
in the review. For a `code_review` finding that challenges the Spec, usually `decision-needed`, the
guidance tells the task session to escalate rather than change the promise itself. The guidance also
tells the task session to close each Issue the review found resolved. When the task fixed the Issue,
the task session closes it through its task with `task resolve`. Otherwise, the task session closes
it with `issue_close` as `resolved`, naming the review's run as evidence.

**A Module review.** Besides judging a task's change, `code_review --scope module` judges each named
Module's whole code against all of its Specs. It uses one reviewer per Module
([Code review](../../method/code-review/module.md#two-scopes)). The guidance names this review and
when to use it for a whole-Module check:

- After a large change
- On code written before its Specs or by an earlier version
- On a project just adopted

Unbound, in the primary worktree, the review needs only `--modules`.

**The Issue system's own failures.** A refusal of the Issue tools or command that is a failure of
the Issue system itself is never recorded as an Issue. Examples are:

- A busy merge lock
- An unfinished merge
- A failed commit

When a session meets such a failure for a task, it carries the error chain in the task's decision
log and escalation, as it would any other failure. A run carries the error chain in its result. An
Issue tool or command needs no task. A failure the main agent meets for no task has no decision log
or escalation to carry it. For that reason, the guidance tells the main agent to show the developer
its whole chain at once, as it does an [unbound run](../../glossary.json#concept.unbound-run)'s
([requirements](requirements.md#req.main-session.issues-failure-no-task)). The guidance tells the
main agent to open a task only when the failure leads to work. A busy merge lock is waited for
(`register_wait`) and the write asked again.

Two of these failures concern a record in the primary worktree, which the main agent alone puts
right. After `recovery_failed`, a record a write published stays uncommitted until the cause is
fixed and `concorde issues recover` puts it back. That command has no tool. After
`uncommitted_change`, the record holds a change no Issue write made. The main agent inspects and
reverts that change, never committing it by hand. A task's merge first puts back what a killed Issue
write left. The merge's `primary_dirty` names any record that recovery left the same way.

## Develop installs

In a [develop install](../../glossary.json#concept.develop-install), the developer also changes the
Concorde the project runs. In that install, the installed skill and `CLAUDE.md` block end with
[Dogfooding](../../dogfooding/module.md)'s own section:

- Watch Concorde's runs.
- Never change Concorde from the project.
- Report [Concorde defects](../../glossary.json#concept.concorde-defect) to the
  [Concorde repository](../../glossary.json#concept.concorde-repository).

Everything above holds unchanged. A normal install carries no such section.

## The project MCP server

The [project MCP server](../../glossary.json#concept.project-mcp-server) presents the tools of the
installed parts. Coordination's tools are listed with the others' for the reader. The exact tools
and events Coordination registers are in the [contracts](contracts.md).

<a id="current-code"></a>

**Current code.** The server answers every call with a fresh process of the primary worktree's
current Concorde. In its own long-lived process, the server keeps only what must live as long as its
session:

- The MCP session.
- The channel.
- The wait and merge processes it watches
  ([Distribution](../../distribution/contracts.md#waits-and-long-work)).

For Coordination's tools, the wait `register_wait` registers is that `concorde`'s
`concorde task wait`. The wait runs as a process the server watches. The merge `task_merge` starts
is the very process the call ran in. After taking both locks and answering, that process replaces
itself with `concorde task merge`.

- **Queries**:

  - `task_list`.
  - `task_show`.
  - `trace_show`: one node, down to a `depth`, so a large trace need not be read whole.
  - `run_result`, present where the execution part is installed.
  - `locks`, which says who holds the merge lock and each task's
    [workspace lock](../../glossary.json#concept.workspace-lock).
  - Beside them, the workflow part's `workflow_report`.
- **Short writes** with structured arguments:

  - `task_open`.
  - `task_escalate`, whose error chain link is typed arguments rather than a command line to quote.
  - `task_report`.
  - `task_answer`.
  - `task_rebind`.
  - `task_resolve`.
  - `task_close` without a merge.
- **Issues**: where the issues part is installed, it registers these tools:

  - `issue_list`, filtered by:

    - `status`.
    - `module`.
    - `tier`.
    - `severity`.

    It is sorted by severity as `concorde issues list` is.
  - `issue_show`.
  - `issue_check`.

  These tools read the project's [Issues](../../glossary.json#concept.issue). These tools write
  them:

  - `issue_report`.
  - `issue_close`.
  - `issue_reopen`.

  All six tools work as `concorde issues` does, without waiting for the merge lock an Issue write
  takes. While another process holds that lock, each write is refused at once with `merge_busy`.
  Each write tool's description also says that the write first puts back what a killed Issue write
  left. The description says how its `recovery_failed` and `uncommitted_change` refusals are put
  right. Recovery itself is `concorde issues recover`'s alone. A report is checked against the
  session's worktree, where its evidence lies. The report is recorded as the session's:

  - `task-session` with its task in a task worktree bound as a workspace.
  - `main-agent` otherwise.
- **Long work**: `task_merge` never waits for a lock. It takes the task's workspace lock and the
  [merge lock](../../glossary.json#concept.merge-lock) at once or is refused at once. The refusal
  uses `workspace_busy` or `merge_busy` and names who holds the busy lock:

  - The holder's command.
  - The holder's process.
  - The holder's start time.
  - The holder's Claude Code session.
  - The holder's task.

  The call's process takes the locks. When it gets both, it becomes `concorde task merge`, a process
  of its own session, keeping both locks. The `flock` belongs to the open file description, which
  survives the change of program. The server never holds either lock. Therefore, the lock belongs to
  the session's work, never to the server. The lock is released when the merge ends, however it
  ends, even when the session and its server end first. The call returns at once with the merge it
  started, not the merge's result. A channel event or the returned wait command delivers the result
  later.
- **[Workflow steps](../../glossary.json#concept.workflow-step)**: where the workflow part is
  installed, it registers `workflow_step`. The [step agents](../../glossary.json#concept.step-agent)
  of a [workflow](../../glossary.json#concept.workflow) call it, one call per relay. This makes a
  step's run a process of the server rather than of the relaying agent's turn
  ([Workflows](../../workflows/module.md#steps-through-the-server)). The tool's exact shape is
  [Workflows'](../../workflows/contracts.md).
- **Waiting**: `register_wait` asks to be woken in these cases:

  - A task becomes one of these:

    - `delivered`.
    - `closed`.
    - `failed`.

    The tool never waits for `merging`, which lasts only while the merge holds the task's workspace
    lock.
  - A task is rebound to a main agent's session other than a named one.
  - A run ends.
  - A lock is released.

  The server watches by running the matching `concorde task wait`, which waits without polling. The
  command blocks on the lock itself or on the operating system's notice of each new holder. When the
  awaited event happens, the server wakes its session with a [Claude Code channel](#channels) event
  with that command's answer. The wait process ends with the server. The wait only notifies. It
  never takes a lock for the session it wakes. That session asks again and may be refused again.

The diagram below shows a merge through the server, from a refusal to the merge's end, with who
holds the locks at each stage. The call's process takes the locks and keeps them as it becomes the
merge, until the merge ends. The server and the woken session never hold the locks.

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
  merge -> merge: "take the three locks,\nmake the attempt's folder"
  merge -> server: "started, with the attempt's\noutput files"
  server -> session: "started, with the attempt's\noutput files and how the\nsession is woken"
  merge -> merge: "become concorde task merge,\nkeeping the locks, writing\ninto the attempt's folder"
  merge -> merge: "merge, run the checks,\nclose the task"
}
ended: "The merge ends" {
  merge -> server: "exits once its answer is\nwritten, and the operating\nsystem releases the locks"
  server -> session: "a merge_ended event, or, without a\nchannel, the background concorde\ntask wait --merge returns"
}
```

Using the server is recommended, not enforced. The operating system's `flock` stays the only lock.
The CLI and the runs of task sessions take the same locks directly, so both paths see each other's
holders. Whenever the main agent would otherwise wait, the server is the better path:

- `task_merge` instead of a `task merge --wait` that blocks a background command for minutes.
- `register_wait` instead of watching a task.

Where the workflow part is installed, the Claude Code workflow adapter always takes the server path
for workflow steps, since a step may outlast many relays. The CLI remains the way for everything
else:

- `task session`.
- The runs a task session starts itself in background Bash.
- The Issues it writes from its shell.
- Anything the server does not present.

<a id="channels"></a>

**Channels.** Claude Code delivers a server's `notifications/claude/channel` only to an interactive
session started with that server as a channel. Channels are a research preview of Claude Code. When
the session starts, a self-built server needs
`--dangerously-load-development-channels server:concorde`, which Claude Code confirms once. Channels
also need Anthropic authentication (claude.ai or a Console key) and an organization that has not
disabled them (`channelsEnabled`). The guidance tells the developer to start the main agent's
session in the primary worktree with
`claude --dangerously-load-development-channels server:concorde`.

A background session is never woken by channels. A probe on 2026-09-29 (Claude Code 2.1.284) started
a `claude --bg` session with that flag. Its server loaded and registered a wait. When the lock it
waited for was released, the session stayed idle. `claude -p` registers no channel at all. So task
sessions, which are background sessions, get the server without a channel
([Task sessions](../task-session/module.md)).

A server cannot learn from Claude Code whether it is a channel. So the server reads that from the
command line of the interactive `claude` above it, one whose standard input is a terminal. When the
server has no channel, these tools return blocking commands to run in background Bash:

- `register_wait` says so and returns the equivalent blocking `concorde task wait` command.
- `task_merge` returns the `concorde task wait <task> --merge` that returns when the merge has ended
  and written its whole answer.

Background Bash wakes the session when the command ends. The merge's answer never lies in the
server. The answer goes to `output.json` of the merge attempt's node in the task's trace. When a
session loses any of these, it finds the merge's answer from the task:

- The server.
- The start's answer.
- The event.

The session uses `task_show` and `trace_show`, also once the close moved the task to the history. An
organization that disabled channels drops the events silently. The guidance tells the agent to use
the background Bash form then.

**Task sessions** receive the server too, with the same tools of the same installed parts. A task
session may query its task or register a wait. Since the task session has no channel,
`register_wait` answers it with the `concorde task wait` command for its background Bash. Its
workflows' step agents start their steps through `workflow_step`. The developer does not consider a
task session's reach to other tasks' management a problem, so there is no split by role. The
guidance still tells a task session never to merge or close its task.
[Workers](../../glossary.json#concept.worker) never receive the server: they launch with an empty
MCP configuration.

## Spec queries

Where the spec part is installed, the main agent may configure the Spec MCP server for its own
session to ask:

- Which Modules exist.
- What a Module's context is.
- What grant a [task type](../../glossary.json#concept.task-type) gives.

The server answers from the Specs of the worktree it is rooted in: the primary worktree for the
main agent. Workers never receive the server.

## Why it is built this way

The main agent never changes the primary worktree's Specs or code beyond a small change the
developer approved. Its view there is the whole project, so nothing would bound or evidence a change
made directly. The primary worktree must also stay clean to merge. Where a task would cost more than
the change, the developer's approval of the specific change stands in for that evidence. Inside a
task worktree, a direct change is bounded by the task and evidenced by `task-validation` and
`delivery`, so task sessions may change Specs and code there themselves.

Only the task branch holds the materials the task changes:

- The Specs.
- The [Protocol copy](../../glossary.json#concept.protocol-copy).
- The checks.

Only that worktree's binding names the task's workspace. For these reasons, every `concorde` command
that works on a task's workspace is the task worktree's own command, run from that worktree. Which
Framework code the command runs is [Distribution](../../distribution/module.md)'s concern, not the
guidance's. Unless the task reinstalled Concorde there, a task worktree's command in an installed
project ordinarily runs the installed Framework shared with the primary worktree. In Concorde's own
source checkout, the command runs the task branch's code.

The main agent hands every task, even a single one, to a task session for these reasons:

- The main agent stays free to talk with the developer while tasks run.
- The main agent stays free to answer every session while tasks run.
- Every task runs under a boundary.

A task session's writes are confined to its task by the
[session boundary](../../glossary.json#concept.session-boundary), which
[Task sessions](../task-session/module.md) writes for it. The main agent stays unrestricted and
alone merges. Merging needs no authorization for these reasons:

- A [delivery commit](../../glossary.json#concept.delivery-commit) is made only after its delivering
  command's checks, which are `delivery`'s readiness where the method part is installed.
- A merge is ordinary, revertible Git.

The escalation policy balances the same way:

- Deciding ordinary questions keeps work moving.
- Recording and reporting them keeps them reviewable.
- Reserving major-impact ones protects decisions only the developer may make.

Gathering a task's decisions into one escalation, and the developer's answers into one reply,
keeps the developer's attention in one place, the main session. This gathering asks for the
developer's attention once per escalation rather than once per question.

## Down the levels

These are the providers the main agent reaches down the levels of work. Coordination depends on the
[Kernel](../../kernel/module.md) alone. Thus, every provider below that belongs to another part is
an [optional integration](../../glossary.json#concept.optional-integration). Only where that part is
installed are the guidance section and the tools that need it present, since each part contributes
its own ([Guidance by part](#guidance-by-part)). The main agent never reaches for a part the project
lacks.

<a id="uses-kernel"></a>

The **Kernel** gives the main agent's commands the
[merge lock](../../glossary.json#concept.merge-lock). Every change of the primary branch on
Concorde's behalf takes this lock. The guidance relies on one lock for merges and Issue writes
alike, so it tells the main agent to retry a `merge_busy` rather than work around it. The Kernel
also gives the commands the [workspace binding](../../glossary.json#concept.workspace-binding). The
binding names a task worktree's workspace to every run started there, so no command the guidance
names takes the task.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../glossary.json#concept.task) with:

- Its branch.
- Its worktree bound as a workspace.
- Its record.

Tasks also provides the [decision log](../../glossary.json#concept.decision-log). The task is the
workspace of level 2, which a task session works. `concorde task show` lists the following, read
from what the workspace recorded:

- The task's runs.
- Its deliveries.
- Its task sessions.
- The holder of its [workspace lock](../../glossary.json#concept.workspace-lock).

Thus, the main agent learns a task's progress from one command, with the task sessions' reports and
their answers. The guidance relies on the following:

- The record names the main agent's session a task session reports to, which `concorde task rebind`
  changes.
- `concorde task report` records a report before it is sent.
- `concorde task answer` marks the report answered.
- `concorde task wait --rebound` returns the new name without polling.

Each task's own worktree keeps parallel tasks from mixing changes. The main agent is responsible
for:

- Opening tasks.
- Merging tasks.
- Closing tasks.

The main agent and the task's session alike write the log. The guidance relies on
`concorde task merge` holding the merge lock and undoing a merge whose checks fail. It tells the
main agent to:

- Retry a `merge_busy`.
- Have the task's session resolve a conflict in the task worktree.
- Treat a failed check as new work rather than discard a change.

After an interrupted merge, the guidance also relies on Tasks refusing the following:

- `open`.
- `merge`.
- `close`.
- `session`.
- `escalate`.

Tasks refuses these with `merge_incomplete`, except for the merging task's `merge --resume` and
`merge --abort`. Meanwhile, `list` and `show` stay available to inspect the interrupted merge. The
guidance tells the main agent to finish that merge first with `--resume` or `--abort` rather than
work around the refusal. Checking the merge again is the default, since the recorded checks decide
as they would have. Only a primary branch changed by hand after the merge goes to the developer. A
task session has no authority to finish a merge, so its guidance sends such a refusal to the main
agent.

The project MCP server presents Tasks' commands unchanged. When each command waits for no lock, the
server answers and refuses as that command does. The results are the
[task records](../tasks/contracts.md#contract.tasks.record) and the other results of
[Tasks' commands](../tasks/contracts.md#commands). The server starts `concorde task merge` with the
two locks it took. It runs the waits of `concorde task wait`, which Tasks provides for background
Bash too.

<a id="uses-task-session"></a>

**Task sessions** starts the background Claude Code task sessions the main agent delegates tasks to.
It ends the task sessions with their task. It applies to every task. The guidance relies on a task
session never merging its task into the primary branch or closing it. It also relies on the task
session reporting only to the main session its task record names. `--main` sets that main session,
and the main agent rebinds it. A task session's report or escalation is its result travelling up to
level 1. The main agent answers the escalations, all at once, or asks for more, with SendMessage.
The main agent reads every error chain the result carries like any other. The main agent merges a
delivered task itself.

<a id="uses-workflows"></a>

Where the workflow part is installed, **Workflows** provides:

- The [workflows](../../glossary.json#concept.workflow) the main agent names in a task brief.
- Their modes.
- The [workflow result](../../glossary.json#concept.workflow-result) read when a workflow ends.

The guidance relies on a workflow never doing any of the following:

- Opening a task.
- Merging a task.
- Closing a task.

It also relies on the workflow's result keeping every run's chain whole, so that a workflow's end is
handled like a run's. An `awaiting_decision` result makes the task session escalate every pending
decision point at once. Before the session starts the same workflow again with the answers, the main
agent answers all those decision points. Workflows never writes the decision log, so the guidance
makes the task session copy a report's decisions and problems there. Without the workflow part, the
guidance has no workflow section, and the task session sequences its runs itself.

<a id="uses-execution"></a>

Where the execution part is installed, **Execution** runs the work a task session starts in its task
worktree:

- `concorde run` for an Operation.
- The [execution commands](../../glossary.json#concept.execution-command) the installed parts
  register.

Examples of those execution commands are Method's:

- `concorde task-validation`.
- `concorde delivery`.
- `concorde scaffold`.

Each Operation run and execution command in the task worktree reads the worktree's
[workspace binding](../../glossary.json#concept.workspace-binding). Execution also runs the
Operations that run [unbound](../../glossary.json#concept.unbound-run) in the primary worktree. Each
run returns a [run result](../../glossary.json#concept.run-result) in the shape of Execution's
[run result contract](../../execution/contracts.md#contract.execution.run-result). The session that
started the run can read its result without inspecting a worker. No run starts the next one. That
choice belongs to the session that started the run. The task session records every non-`ok` result
of the runs it starts in the decision log. Before deciding or escalating, the task session reads
that result's chain in full.

The project MCP server's `run_result` presents a run's saved result unchanged. While the run has no
result, the tool presents its [run progress file](../../glossary.json#concept.run-progress-file)
unchanged. The server reads the run's [run lock](../../glossary.json#concept.run-lock) to tell
whether the run still runs. The server waits for the run lock's release to learn that the run ended.
The server also reads the workspace lock Execution's runs hold. Execution records no owner in a
run's records, so the guidance and the server never take a run's owner from them
([requirements](requirements.md#req.main-session.owner-recorded-by-coordination)). Without the
execution part, no run exists. Without that part, the task session changes Specs and code itself and
delivers with `concorde task deliver`.

<a id="uses-operations"></a>

**Operations** provides the [Operation](../../glossary.json#concept.operation) catalog of the
installed parts:

- Which Operations exist.
- What each takes.
- Which may run unbound.

The guidance names them, and the task session chooses which to run for a task's next step. What an
Operation takes and returns belongs to its provider. Concorde's own providers belong to the method
part. Where that part is installed, the guidance relies on four of them directly. Otherwise, the
guidance's method section is absent.

<a id="uses-understanding"></a>

**Understanding** provides `understand` and `plan_review`. The task-session guidance relies on
`plan_review`'s iterations. When a run receives the previous run as `--input`, it must answer every
finding of that previous run once, with `--accept` or `--reject`. Its reviewer answers those
answers. Its verdict follows the findings that stand
([plan review](../../method/understanding/contracts.md#contract.understanding.plan-review)). The
guidance also relies on an `understand` plan naming in `new_files` the files a change needs that do
not exist yet. The task session creates and binds those files before the run that fills them.

<a id="uses-specification"></a>

**Specification** provides `specify`. The task-session guidance relies on it creating each new Spec
document a `specify` worker proposes, empty and registered in its Module's `owns`. The guidance also
relies on Specification refusing a proposed path that already exists
([New and deleted documents](../../method/specification/module.md#new-and-deleted-documents)). These
behaviours ensure that a task session prepares implementation files for workers and never a Spec
document.

<a id="uses-spec-review"></a>

**Spec review** provides `spec_panel`. Where the issues part is installed, the guidance relies on
it reporting every finding that stands as an Issue of the Module it concerns. The guidance relies on
it closing none. It also relies on it naming the following in its result
([result](../../method/spec-review/panel.md#contract.spec-review.panel-payload)):

- Each finding's Issue.
- The earlier Issues that still stand.
- Those it found resolved.

The result has a [review verdict](../../glossary.json#concept.review-verdict) derived from the
Issues that stand.

<a id="uses-code-review"></a>

**Code review** provides `code_review`. It judges a task's change since its base. With
`--scope module`, it instead judges each named Module's whole code against all its Specs. Where the
issues part is installed, the guidance relies on it reporting every finding as an Issue, including a
`spec-challenge` finding. The guidance relies on it closing none. As Spec review does, the guidance
also relies on it naming the earlier Issues that stand and those it found resolved
([Code review](../../method/code-review/module.md#two-scopes)).

<a id="uses-commands"></a>

**Commands** provides the catalog of
[execution commands](../../glossary.json#concept.execution-command) the installed parts register. In
Concorde, these are the method part's deterministic runs:

- `task-validation`.
- `delivery`.
- `scaffold`.

A task session starts these by name in its task worktree. The guidance names them apart from the
Operations, since they launch no worker and a caller starts them without `run`.

<a id="uses-workers"></a>

Where the worker harness part is installed, **Workers** owns the
[worker configuration](../../glossary.json#concept.worker-configuration). The guidance tells the
main agent to edit it directly. The guidance relies on Workers validating the whole file when a
worker launches. It also relies on Workers reporting a malformed file with `config_invalid`. The
separate discovery helper supplies suggestions without proving API access or gating edits.

<a id="uses-tracing"></a>

**Tracing**, the Kernel's child, records the whole history of a task as its
[trace](../../glossary.json#concept.trace). This is a tree of
[trace nodes](../../glossary.json#concept.trace-node) from the task's sessions down to each worker
round. For that history with its cost, the guidance points the main agent to
`concorde trace show <task>`. For one run, the guidance points the main agent to
`concorde trace show <run-id>`. Coordination presents this on the project MCP server as
`trace_show`. Coordination's tools also rely on Tracing's locks:

- Their holder lines name the holder's session and task, which is how a refusal says who holds a
  lock.
- A held lock can be handed to a process that inherits its descriptor.
- A wait for a release blocks on the lock itself.

Tracing's [locks](../../kernel/tracing/contracts.md#locks) state these properties. Every refusal
Coordination's tools return is a link of Tracing's
[error chain](../../glossary.json#concept.error-chain), in the shape of its
[error contract](../../kernel/tracing/contracts.md#contract.tracing.error). `trace_show` answers
as Tracing's [trace view](../../kernel/tracing/contracts.md#contract.tracing.view).

## Beside the levels

Four providers serve the main agent without being a level below it.

<a id="uses-distribution"></a>

**Distribution** is present in every installation. It renders and installs the guidance composed
from the sections of the installed parts. Distribution hosts the
[project MCP server](../../glossary.json#concept.project-mcp-server) on which Coordination registers
its tools through its [part registration](../../glossary.json#concept.part-registration). The
guidance relies on the composed guidance holding exactly the sections of the installed parts.
Coordination's tools rely on the host running each call in a fresh process of the primary worktree's
current Concorde. The tools also rely on the host handing a lock a call took to the process that
does the work.

<a id="uses-issues"></a>

Where the issues part is installed, **Issues** provides durable, project-level
[Issue](../../glossary.json#concept.issue) records. It also provides the bookkeeping command for
[reports](../../issues/interface.md#contract.issues.report) and
[receipts](../../issues/interface.md#contract.issues.receipt). The issues part registers the
command's actions with the project MCP server as its Issue tools, unchanged. The guidance relies on
these properties:

- Status follows dispositions.
- Issue [revisions](../../glossary.json#concept.issue-revision) detect concurrent writes.
- Every report carries its tier and severity.

The guidance tells sessions to do the following:

- Inspect before recording.
- Fix by tier, starting from the most severe Issues.
- Have a task's merge close the Issues it resolves.
- Never report a failure of the Issue system as an Issue.

The command records these decisions. Whoever disposes an Issue remains responsible for the evidence.

<a id="uses-spec"></a>

Where the spec part is installed, **Spec core** provides the commands that check and regenerate the
Specs a session works on:

- `concorde spec-validation` reports every
  [structural check](../../glossary.json#concept.structural-check) finding of a worktree's Specs.
- After a Module's `module` block changed, `concorde registry --write` regenerates the
  [registry](../../glossary.json#concept.registry) mirror. This is the housekeeping the main agent
  may do in the primary worktree.

Before a session commits a realization entry it added, the task-session guidance tells the session
to check that entry with `spec-validation`. The guidance relies on these commands, like every
command of Spec tooling, refusing with Spec tooling's own
[error record](../../spec-tooling/spec/errors.md#contract.spec.error). Before a session escalates
that record, the session translates it into a link of the chain
([Escalation policy](#escalation-policy)).

<a id="uses-spec-mcp"></a>

The **Spec MCP server** is a child of Spec tooling installed with the spec part. From the worktree
it is rooted in, the server answers read-only queries about:

- Modules.
- Context.
- Grants.

Only when the main agent wants to ask such questions does it configure the server for its own
session. Workers never receive it. A server rooted in the primary worktree knows only the primary
branch's Specs. For this reason, the guidance tells the main agent that a question about a task's
Specs needs a server, or a `concorde` command, rooted in that task's worktree.

## Inside

This section describes how this Module is built:

- The guidance sources.
- What the build renders from them.
- The project MCP server.

```d2
mainsession: Main session {
  sources: Guidance sources {
    "prompts/main-session/"
  }
  guidance: Main-session guidance
  server: Task tools {
    "src/concorde/coordination/tasks/tools.py"
  }
  sources -> guidance: authors
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** of Coordination's sections live under `prompts/main-session/`:

- `skill.md` opens the project skill `.claude/skills/concorde/SKILL.md`.
- `claude-md.md` opens the block of the project's `CLAUDE.md`.
- `task-session.md` opens the first prompt `concorde task session` gives a task session.

The coordination part's registration registers these sources under `guidance`. Distribution's build
renders them into `generated/main-session/`. Their tests live under `tests/concorde/main_session/`.
The tests check that the guidance composed of every part states every rule the
[scenarios](scenarios.md) describe, whichever part's section says it. What the main agent then does
is judgment no deterministic test observes.

<a id="realization.main-session.project-mcp"></a>

The **task tools** in `src/concorde/coordination/tasks/tools.py` are the coordination part's tools
of the project MCP server. Its [part registration](../../glossary.json#concept.part-registration)
names them:

- The task tools.
- `task_merge`.
- `locks`.
- `register_wait`.
- `trace_show`.
- Where the execution part is installed, `run_result`.

Each tool maps to Tasks' and Tracing's records. Each has its definition and the sentence it adds to
the server's instructions. Distribution's
[host](../../distribution/module.md#realization.distribution.project-mcp) calls them with each call
in a fresh process of the current Concorde. `task_merge` takes the merge's locks and leaves the host
the command it becomes. Their tests live under `tests/concorde/project_mcp/`. The tests talk to the
server over a real stdio connection and watch:

- Real locks.
- Real merges.
- Real channel events.

## Who relies on it

Three Modules consume what this one authors:

- [Distribution](../../distribution/module.md) renders the guidance sources. It composes them
  with the other installed parts' sections and installs the rendered guidance into a project.
- In a develop install, [Dogfooding](../../dogfooding/module.md) appends its own section to the
  guidance. It changes nothing else.
- [Task sessions](../task-session/module.md) gives a task session the task-session guidance
  composed of the installed parts as its first prompt, so every task follows the method this
  Module sets.
