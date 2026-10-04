# Coordination

## Purpose

Coordination is the coordination [part](../glossary.json#concept.part) and the upper of Concorde's
two halves: project management and task-level parallelism.
It is where the developer and the [main agent](../glossary.json#concept.main-agent) decide what to
work on, split it into [tasks](../glossary.json#concept.task), give each task its own branch and
worktree, have every task worked by a [task session](../glossary.json#concept.task-session), one
or several at once, keep the reasons behind decisions taken without the developer, escalate what
matters and merge what was delivered. The developer and the main agent rely on it; it binds no
files of its own, and its three children do the work: the Main session, Tasks and Task sessions.

Coordination does not do the bounded work itself. Inside a task's worktree the changes are made
directly by the task session that works the task, or through the runs of the lower half,
[Execution](../execution/module.md) with Method's Operations and commands, which knows nothing of
tasks: Coordination hands it a workspace by writing that worktree's
[workspace binding](../glossary.json#concept.workspace-binding), and learns what happened there only
from what was recorded. It decides direction, splitting and merging, never how a
[worker](../glossary.json#concept.worker) is bounded, launched or checked.

The coordination part depends on the [Kernel](../kernel/module.md) alone: the binding it writes, the
[workspace lock](../glossary.json#concept.workspace-lock) and
[merge lock](../glossary.json#concept.merge-lock) it takes, the
[delivery commits](../glossary.json#concept.delivery-commit) it recognizes and the
[trace nodes](../glossary.json#concept.trace-node) it records are the Kernel's contracts. Everything
else it can use is an [optional integration](../glossary.json#concept.optional-integration),
described where it applies and summed up in [Optional integrations](#optional-integrations): runs
where the execution part is installed, Issues where the issues part is, Spec checks where the spec
part is, and Method's validated delivery where the method part is, with Coordination's own
`concorde task deliver` where it is not. A project that installs only the kernel and coordination
still opens, delegates, delivers, merges and closes tasks.

## Core concepts

Coordination owns no term of its own; it is built from terms its children and the root define.

A **[task](../glossary.json#concept.task)** is one unit of the main agent's work: a branch, a
worktree bound as a workspace, a [task record](../glossary.json#concept.task-record) and a
[decision log](../glossary.json#concept.decision-log), all provided by [Tasks](tasks/module.md).
Every change of a [Spec](../glossary.json#concept.spec) or of code is a task, and only tasks whose
Modules and shared files do not overlap run at once; the rest run one after another.

The **[main agent](../glossary.json#concept.main-agent)** and the
**[task session](../glossary.json#concept.task-session)** are the two agents of this half. The task
level, level 2 of Concorde's [levels of work](../module.md#the-levels-of-work) below the main
session's level 1, is always played by a task session, never by the main agent itself:

| | Main agent | Task session |
| --- | --- | --- |
| Works in | the primary worktree only | its task worktree only |
| Write boundary | none: Concorde does not restrict the main agent | for its own file tools and shell: its task worktree and decision log, plus what its commits, runs and escalations write and package caches |
| Asks | the developer, every open decision at once | the main agent, every decision its task needs together |
| Lifecycle | the developer's session | started, answered and stopped by the main agent |
| Merges | a delivered task into the primary branch | only the primary branch into its task branch, when asked after a merge conflict or a `concorde update` |

For now the main agent is a Claude Code session and every task session a background Claude Code
session, while the workers that the runs of a task launch may run on pi.

The **[workspace binding](../glossary.json#concept.workspace-binding)** is the Kernel's term and the
whole seam between the halves: the file in a task worktree that tells every run there which
workspace, goal, [Modules](../glossary.json#concept.module), branch and base it works on.

## Overview

### How a task goes

The developer works with the main agent in the primary worktree. For each piece of work the main
agent opens a task, records the [task brief](../glossary.json#concept.task-brief) in its decision log
and starts a task session for it, even when it is the only task, and never works inside the task
worktree itself. The task session
changes Specs and code there, directly or through [runs](../glossary.json#concept.run) of
Execution, validates and delivers it. The main agent then merges the delivered task from the
primary worktree and reports to the developer. Only a small change the developer approved is made
by the main agent directly in the primary worktree.

```d2 illustrative
grid-columns: 4
horizontal-gap: 120
developer: Developer {
  grid-columns: 1
  vertical-gap: 50
  discuss: "Discuss the work"
  decide: "Decide what only\nthe developer may"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  read: "Read the report"
}
main: "Main agent\nprimary worktree" {
  grid-columns: 1
  vertical-gap: 50
  open: "Open a task,\nrecord its task brief,\nstart a task session"
  answer: "Decide ordinary questions,\nanswer every escalation\nat once"
  g1: "" {style.opacity: 0}
  merge: "Merge the delivered task,\nor close it as\ncompleted or failed"
  report: "Report"
}
session: "Task session\ntask worktree" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  work: "Change Specs and code,\ndirectly or through runs"
  deliver: "Validate and deliver"
  resolve: "Merge the primary\nbranch in, resolve,\ndeliver again"
  g2: "" {style.opacity: 0}
}
execution: "Execution\nthe task's workspace" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  run: "Runs: Operations and\nexecution commands"
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  g4: "" {style.opacity: 0}
}
developer.discuss -> main.open
main.open -> session.work: starts
session.work <-> execution.run: "runs and\nrun results"
session.work <-> main.answer: "escalations, together,\nand every answer"
main.answer <-> developer.decide: "major impact"
session.work -> session.deliver
session.deliver -> execution.run: "task-validation,\ndelivery"
session.deliver -> main.merge: delivered
main.merge <-> session.resolve: "merge_conflict,\ndelivered again"
main.merge -> main.report
main.report -> developer.read
```

Work does not always go straight. A result that is not `ok` is read with its whole [error
chain](../glossary.json#concept.error-chain), then repaired within the task or escalated with a link
of its own. A task never asks the developer in place: its session gathers every decision it needs
and escalates them together to the main agent, which decides ordinary questions itself under the
escalation policy, asks the developer at once about all those with major impact and answers the
session once. A merge refused for a conflict goes back to the task session, which merges the
primary branch into its task branch, resolves the conflict and delivers again, as it merges the
primary branch when a `concorde update` brings a new
[Protocol copy](../glossary.json#concept.protocol-copy); a merge whose
checks fail is undone and the failure handled as new work; and a task that reached its goal without
a merge, or will not reach it, is closed as completed or failed instead. The [Main
session](main-session/module.md) and [Tasks](tasks/module.md) give the details.

### The seam with the lower half

The upper half talks to the lower half only through the binding, the lower half's commands and what
it recorded:

```d2 illustrative
coordination: Coordination {
  tasks: Tasks
  main: Main session
  session: Task sessions
}
kernel: Kernel {
  binding: Workspace binding
  commits: Delivery commits
}
execution: "Execution (optional)" {
  store: Run store
}
coordination.tasks -> kernel.binding: writes when a task opens
coordination.main -> execution: runs unbound in the primary worktree
coordination.session -> execution: runs in its task worktree
coordination.tasks -> execution.store: reads a task's runs
coordination.tasks -> kernel.commits: reads whether a task is delivered
```

Tasks writes the [workspace binding](../glossary.json#concept.workspace-binding) of each task
worktree when it opens the task, naming the workspace after the task and placing its workspace
folder inside the task's own folder, so the task's [trace](../glossary.json#concept.trace) holds
every run of it. The task session that works the task runs Execution's commands inside that
worktree, never naming the task. Tasks reads back the task's runs in that part of the
[run store](../glossary.json#concept.run-store) and its
[delivery commits](../glossary.json#concept.delivery-commit) on the task branch, and derives whether
a task is active or delivered from them together with its branch head and whether its worktree is
clean; without the execution part there are no runs to read, and only the delivery commits, the
branch head and the worktree count. A main session learns how the runs it did not start stand only by asking Tasks with
`concorde task show`, and is woken only by the runs its own background Bash started and by the
waits it registered with its own
[project MCP server](../glossary.json#concept.project-mcp-server). No record is written by both
halves, so neither can leave the other with a state that disagrees with what happened.

The main agent may also start an [Operation](../glossary.json#concept.operation) that allows it as
an [unbound run](../glossary.json#concept.unbound-run) in the primary worktree, for a question or a
review that changes nothing; such a run has no workspace and belongs to no task.

### The children and what they rely on

A task session gets its harness from Task sessions' own
[session boundary](../glossary.json#concept.session-boundary), the main session gets only the
guidance Distribution installs, and the task level gets its workspace from Tasks.

```d2
coordination: Coordination {
  main: Main session
  task: Task sessions
  tasks: Tasks
  main -> task
  main -> tasks
  task -> tasks
}
kernel: Kernel
coordination -> kernel
```

## Why it is built this way

Coordination and Execution change for different reasons. How tasks are opened, how many run at
once, who works them and how they are merged is project management and follows how the developer
wants to work; how a worker is bounded by the Specs, launched, audited and checked is Concorde's
core and follows the Protocol. Keeping them apart lets either change without the other: the upper
half can reorganize tasks and sessions freely as long as it binds a workspace the way Execution
reads it, and the lower half can change how runs work as long as it reads that binding and records
what it did.

Tasks that run at once never mix their changes, because each has its own branch and worktree and
only tasks whose Modules and shared files do not overlap run together; merges never interleave,
because each is made from the primary worktree under the
[merge lock](../glossary.json#concept.merge-lock), which one process holds at a time. Every task is
worked by a task session, which gets a write boundary that keeps its mistakes inside its task while
it runs beside others; Concorde places no permission limits on the main agent, which works no task
itself.

### Escalations

An extra level of messaging is one more place for an error to be lost, so the loss is prevented
structurally: a task session escalates with `concorde task escalate --by task-session`, which Tasks
records as the session's own link on top of the chains it received, unchanged. The main agent
decides the escalation itself when the escalation policy lets it, and otherwise adds its own link
on top before the developer sees it. Since a task never asks the developer in place, a session
reports every decision its task needs together, and the main agent answers them together, so that
the developer is asked once, from the main session, rather than once per question.

## Providers

<a id="uses-kernel"></a>

The **Kernel** is the one part Coordination depends on. Coordination relies on the
[binding contract](../kernel/contracts.md#contract.kernel.workspace-binding) being the same file
every part that works in the workspace reads, so that writing it is the whole hand-over; on the
[workspace lock](../glossary.json#concept.workspace-lock) being the lock every run of a workspace
holds, so that a merge or close that holds it knows no run of the task is changing its worktree; on
the [merge lock](../glossary.json#concept.merge-lock) being the lock every change of the primary
branch on Concorde's behalf takes, an [Issue](../glossary.json#concept.issue) write as much as a merge; on a
[delivery commit](../glossary.json#concept.delivery-commit) being recognized by its subject and
verified by its single parent, whichever part made it; and on Tracing's trace nodes, locks and
error chain for every record it keeps.

<a id="uses-execution"></a>

**Execution** is an [optional integration](../glossary.json#concept.optional-integration). Where
the execution part is installed, it gets the bounded work done in a bound workspace and records it.
Coordination relies on it working only on the workspace the binding names, never writing the
binding, and recording every run of a bound workspace as a
[trace node](../glossary.json#concept.trace-node) in the workspace folder the binding names, its
[run store](../glossary.json#concept.run-store), or in the lobby while it waits for the lock. It
relies on nothing inside Execution beyond those records and the commands' results. A run whose
runner ended without a result is taken as lost rather than trusted as running, and a run of another
workspace named to Tasks is refused with `unknown_run`; [Tasks](tasks/module.md) gives the details.
Where the execution part is not installed, no run exists: a task's activity follows from its branch
and worktree alone, a close has no run to stop, and `concorde task wait --run` is refused naming the
missing part.

## The children

<a id="contains-main-session"></a>

The **Main session** is the level where the developer and the main agent work on the whole project:
the guidance that makes a Claude Code session in the primary worktree the main agent, including
the method of working inside a task that it gives its task sessions. It asks Task sessions to start
a task session for every task.

<a id="contains-tasks"></a>

**Tasks** manages the task level's workspace: each task's branch, its worktree and the binding that
makes it a workspace, its record and its decision log, the derived state of each task, and the
merge of a delivered task into the primary branch under a lock.

<a id="contains-task-session"></a>

**Task sessions** is the task level delegated: it starts a background Claude Code task session in a
task worktree, confines its writes with its own session boundary, and ends it with its task.

## Optional integrations

Each reach of Coordination into a part it does not depend on, where it is described and what
happens without the part:

| Part | What Coordination does with it | Without it |
| --- | --- | --- |
| execution | counts a workspace's runs as the task's activity, stops them and those in the lobby when a task closes, waits for a run, lists [run locks](../glossary.json#concept.run-lock) ([Tasks](tasks/module.md)) | no run exists; a task's activity follows from its branch and worktree alone; waiting for a run is refused naming the part |
| issues | names the Issues a task resolves, closes them when it merges, puts back what a killed Issue write left before the merge audits the primary worktree, gives task sessions the Issue tools ([Tasks](tasks/module.md), [Main session](main-session/module.md)) | `--resolves` is refused naming the part; a merge closes nothing and its audit has no Issue records to put back |
| spec | runs `concorde spec-validation` as a merge's default check, checks a task's Modules against the registry ([Tasks](tasks/module.md)) | a merge runs only the `--check` commands it is given; Modules are plain labels |
| method | a task is validated with `task-validation` and delivered with `delivery`, and the main agent starts Method's reading Operations, such as `understand`, `spec_review`, `spec_panel` and `code_review`, as unbound runs ([Task sessions](task-session/module.md), [Main session](main-session/module.md)) | the task session delivers with `concorde task deliver`, which runs the checks it is given and makes the delivery commit ([Tasks](tasks/module.md)) |
| workflow | a task session may run a workflow in its worktree; the workflow part contributes that guidance | no workflow runs; the guidance has no workflow section |
| worker harness | the main agent edits the [worker configuration](../glossary.json#concept.worker-configuration) the worker harness part owns, and the workers of a task session's runs take their backend from it ([Main session](main-session/module.md), [Task sessions](task-session/module.md)) | no worker runs; the guidance has no worker-models section |

Coordination imports the code of none of these parts. It reaches each through its `concorde`
command, JSON in and out, or through a file format its Spec defines, and learns the same way whether
the part is installed: the spec part by its registry mirror `.concorde/specs.json`, the others by
whether the worktree's own `concorde` offers their commands, and the runs by Execution's run store
existing at all. A process holding the merge lock that runs a command needing it hands the lock on
to that command. [Tasks](tasks/contracts.md#parts-not-depended-on) gives the exact rules.
