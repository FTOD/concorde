# Coordination

## Purpose

Coordination is the coordination [part](../glossary.json#concept.part) and the upper of Concorde's
two halves: project management and task-level parallelism. It is where the developer and the
[main agent](../glossary.json#concept.main-agent) decide what to work on. There, they do the
following:

- Split the work into [tasks](../glossary.json#concept.task).
- Give each task its own branch and worktree.
- Have every task worked by a [task session](../glossary.json#concept.task-session), one or several
  at once.
- Keep the reasons behind decisions taken without the developer.
- Escalate what matters.
- Merge what was delivered.

The developer and the main agent rely on Coordination. Coordination binds no files of its own. Its
three children do the work:

- The Main session.
- Tasks.
- Task sessions.

Coordination does not do the bounded work itself. Inside a task's worktree, the task session makes
changes directly or through the runs of the lower half, [Execution](../execution/module.md) with
Method's Operations and commands. Execution knows nothing of tasks. Coordination hands Execution a
workspace by writing that worktree's
[workspace binding](../glossary.json#concept.workspace-binding). Coordination learns what happened
there only from what was recorded. Coordination decides these matters:

- Direction.
- Splitting.
- Merging.

Coordination never decides these aspects of a [worker](../glossary.json#concept.worker):

- How the worker is bounded.
- How the worker is launched.
- How the worker is checked.

The coordination part depends on the [Kernel](../kernel/module.md) alone. These are the Kernel's
contracts:

- The binding Coordination writes.
- The [workspace lock](../glossary.json#concept.workspace-lock) Coordination takes.
- The [merge lock](../glossary.json#concept.merge-lock) Coordination takes.
- The [delivery commits](../glossary.json#concept.delivery-commit) Coordination recognizes.
- The [trace nodes](../glossary.json#concept.trace-node) Coordination records.

Everything else Coordination can use is an
[optional integration](../glossary.json#concept.optional-integration). Each is described where it
applies and summed up in [Optional integrations](#optional-integrations):

- Runs where the execution part is installed.
- Issues where the issues part is installed.
- Spec checks where the spec part is installed.
- Method's validated delivery where the method part is installed, with Coordination's own
  `concorde task deliver` where the method part is not installed.

A project that installs only the kernel and coordination still does the following with tasks:

- Opens them.
- Delegates them.
- Delivers them.
- Merges them.
- Closes them.

## Core concepts

Coordination owns no term of its own. It is built from terms its children and the root define.

A **[task](../glossary.json#concept.task)** is one unit of the main agent's work:

- A branch.
- A worktree bound as a workspace.
- A [task record](../glossary.json#concept.task-record).
- A [decision log](../glossary.json#concept.decision-log).

[Tasks](tasks/module.md) provides all of these.

Except for a small change the developer approved, every change of a
[Spec](../glossary.json#concept.spec)'s meaning or of code's behaviour is a task. The main agent
makes that approved small change in the primary worktree itself
([Changes run in tasks](main-session/requirements.md#req.main-session.tasks-own-changes)). That
requirement also names the housekeeping the primary worktree takes besides. Only tasks whose Modules
and shared files do not overlap run at once. The rest run one after another.

The **[main agent](../glossary.json#concept.main-agent)** and the
**[task session](../glossary.json#concept.task-session)** are the two agents of this half. The task
level is level 2 of Concorde's [levels of work](../module.md#the-levels-of-work), below the main
session's level 1. A task session always plays the task level, never the main agent itself:

| | Main agent | Task session |
| --- | --- | --- |
| Works in | the primary worktree only | its task worktree only |
| Write boundary | none: Concorde does not restrict the main agent | for its file tools (Edit, Write): its task worktree and decision log; its shell is not restricted, kept inside the task by its guidance and checked by the merge's audit of what changed outside the task worktree |
| Asks | the developer, every open decision at once | the main agent, every decision its task needs together |
| Lifecycle | the developer's session | started, answered and stopped by the main agent |
| Merges | a delivered task into the primary branch | only the primary branch into its task branch, when asked after a merge conflict or a `concorde update` |

For now the main agent is a Claude Code session and every task session a background Claude Code
session. For now the workers that the runs of a task launch may run on pi.

The **[workspace binding](../glossary.json#concept.workspace-binding)** is the Kernel's term and the
whole seam between the halves. The file in a task worktree tells every run there what it works on:

- Workspace.
- Goal.
- [Modules](../glossary.json#concept.module).
- Branch.
- Base.

## Overview

### How a task goes

The developer works with the main agent in the primary worktree. For each piece of work, even when
it is the only task, the main agent does the following:

- Opens a task.
- Records the [task brief](../glossary.json#concept.task-brief) in its decision log.
- Starts a task session for it.

The main agent never works inside the task worktree itself. The task session changes Specs and code
there, directly or through [runs](../glossary.json#concept.run) of Execution. The task session
validates and delivers the task. The main agent then merges the delivered task from the primary
worktree and reports to the developer. Only for a small change the developer approved does the main
agent make the change directly in the primary worktree.

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

Work does not always go straight. A result that is not `ok` is read with its whole
[error chain](../glossary.json#concept.error-chain). The result is then repaired within the task or
escalated with a link of its own. A task never asks the developer in place. Its session gathers
every decision it needs and escalates them together to the main agent. Under the escalation policy,
the main agent decides ordinary questions itself. The main agent asks the developer at once about
all decisions with major impact. The main agent answers the session once.

A merge refused for a conflict goes back to the task session. The task session then does the
following:

- Merges the primary branch into its task branch.
- Resolves the conflict.
- Delivers again.

When a `concorde update` brings a new [Protocol copy](../glossary.json#concept.protocol-copy), the
task session also merges the primary branch. When a merge's checks fail, the merge is undone. The
failure is handled as new work. When a task reached its goal without a merge, it is closed as
completed instead. When a task will not reach its goal, it is closed as failed instead. The
[Main session](main-session/module.md) and [Tasks](tasks/module.md) give the details.

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

When Tasks opens a task, it writes the
[workspace binding](../glossary.json#concept.workspace-binding) of the task worktree. It names the
workspace after the task. It places the workspace folder inside the task's own folder, so the task's
[trace](../glossary.json#concept.trace) holds every run of the task. The task session that works the
task runs Execution's commands inside that worktree, never naming the task. Tasks reads back the
task's runs in that part of the [run store](../glossary.json#concept.run-store). Tasks also reads
the task's [delivery commits](../glossary.json#concept.delivery-commit) on the task branch. Tasks
derives whether a task is active or delivered from these:

- The task's runs.
- Its delivery commits.
- Its branch head.
- Whether its worktree is clean.

Without the execution part, there are no runs to read. Only these count:

- The delivery commits.
- The branch head.
- The worktree.

Only by asking Tasks with `concorde task show` does a main session learn how the runs it did not
start stand. A main session is woken only by the runs its own background Bash started and by the
waits it registered with its own [project MCP server](../glossary.json#concept.project-mcp-server).
No record is written by both halves, so neither can leave the other with a state that disagrees with
what happened.

For a question or a review that changes no Spec or code, the main agent may also start an
[Operation](../glossary.json#concept.operation) that allows it as an
[unbound run](../glossary.json#concept.unbound-run) in the primary worktree. Where the issues part
is installed, a review may publish its findings as [Issues](../glossary.json#concept.issue). This is
the review's one lasting change besides its own record
([Execution](../execution/module.md#unbound-runs)). Such a run has no workspace and belongs to no
task.

### The children and what they rely on

A task session gets its harness from Task sessions' own
[session boundary](../glossary.json#concept.session-boundary). The main session gets the
guidance Distribution installs and Tasks' session-start hook, which Distribution adds to the
project's Claude Code settings for Coordination. The task level gets its workspace from Tasks.

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

Coordination and Execution change for different reasons. Project management follows how the
developer wants to work and covers:

- How tasks are opened.
- How many tasks run at once.
- Who works the tasks.
- How tasks are merged.

Concorde's core follows the Protocol and covers how a worker is:

- Bounded by the Specs.
- Launched.
- Audited.
- Checked.

Keeping them apart lets either change without the other. As long as the upper half binds a workspace
the way Execution reads it, the upper half can reorganize tasks and sessions freely. As long as the
lower half reads that binding and records what it did, the lower half can change how runs work.

Tasks that run at once never mix their changes for these reasons:

- Each task has its own branch and worktree.
- Only tasks whose Modules and shared files do not overlap run together.

Merges never interleave, because each is made from the primary worktree under the
[merge lock](../glossary.json#concept.merge-lock), which one process holds at a time. Every task has
a task session that works it. While the task session runs beside others, its
[session boundary](../glossary.json#concept.session-boundary) keeps its file-tool writes inside its
task. Its shell is not restricted
([req.task-session.no-sandbox](task-session/requirements.md#req.task-session.no-sandbox)). When
anything outside the task worktree changed that nobody accounts for, the merge refuses the task.
Concorde places no permission limits on the main agent, which works no task itself.

### Escalations

An extra level of messaging is one more place for an error to be lost, so the loss is prevented
structurally. A task session escalates with `concorde task escalate --by task-session`. Tasks
records the escalation as the session's own link on top of the chains it received, unchanged. When
the escalation policy lets it, the main agent decides the escalation itself. Otherwise, the main
agent adds its own link on top before the developer sees the escalation. Since a task never asks the
developer in place, a session reports every decision its task needs together and the main agent
answers them together. They do this so that the developer is asked once, from the main session,
rather than once per question.

## Providers

<a id="uses-kernel"></a>

The **Kernel** is the one part Coordination depends on. Coordination relies on these guarantees:

- The [binding contract](../kernel/contracts.md#contract.kernel.workspace-binding) is the same file
  every part that works in the workspace reads, so that writing it is the whole hand-over.
- Every run of a workspace holds the [workspace lock](../glossary.json#concept.workspace-lock). A
  merge or close that holds this lock therefore knows no run of the task is changing its worktree.
- Every change of the primary branch on Concorde's behalf takes the
  [merge lock](../glossary.json#concept.merge-lock). This applies to an
  [Issue](../glossary.json#concept.issue) write as much as a merge.
- Whichever part made a [delivery commit](../glossary.json#concept.delivery-commit), the commit is
  recognized by its subject and verified by its single parent.
- Coordination uses Tracing's trace nodes, locks and error chain for every record it keeps.

<a id="uses-execution"></a>

**Execution** is an [optional integration](../glossary.json#concept.optional-integration). Where the
execution part is installed, it gets the bounded work done in a bound workspace and records it.
Coordination relies on Execution doing the following:

- Working only on the workspace the binding names.
- Never writing the binding.
- Recording every run of a bound workspace as a [trace node](../glossary.json#concept.trace-node) in
  the workspace folder the binding names, its [run store](../glossary.json#concept.run-store), or in
  the lobby while the run waits for the lock.

Coordination relies on nothing inside Execution beyond those records and the commands' results. When
a run's runner ended without a result, the run is taken as lost rather than trusted as running. When
a run of another workspace is named to Tasks, the run is refused with `unknown_run`.
[Tasks](tasks/module.md) gives the details. Where the execution part is not installed, no run
exists:

- A task's activity follows from its branch and worktree alone.
- A close has no run to stop.
- `concorde task wait --run` is refused naming the missing part.

## The children

<a id="contains-main-session"></a>

The **Main session** is the level where the developer and the main agent work on the whole project.
Its guidance makes a Claude Code session in the primary worktree the main agent. This guidance
includes the method of working inside a task that Main session gives its task sessions. Main session
asks Task sessions to start a task session for every task.

<a id="contains-tasks"></a>

**Tasks** manages the task level's workspace:

- Each task's branch.
- Each task's worktree and the binding that makes it a workspace.
- Each task's record and decision log.
- The derived state of each task.
- The merge of a delivered task into the primary branch under a lock.

<a id="contains-task-session"></a>

**Task sessions** is the task level delegated. Task sessions does the following:

- Starts a background Claude Code task session in a task worktree.
- Confines the task session's writes with its own session boundary.
- Ends the task session with its task.

## Optional integrations

Each reach of Coordination into a part it does not depend on, where it is described and what
happens without the part:

| Part | What Coordination does with it | Without it |
| --- | --- | --- |
| execution | counts a workspace's runs as the task's activity, stops them and those in the lobby when a task closes, waits for a run, lists [run locks](../glossary.json#concept.run-lock) ([Tasks](tasks/module.md)) | no run exists; a task's activity follows from its branch and worktree alone; waiting for a run is refused naming the part |
| issues | names the Issues a task resolves, closes them when it merges, puts back what a killed Issue write left before the merge audits the primary worktree, gives task sessions the Issue tools ([Tasks](tasks/module.md), [Main session](main-session/module.md)) | `--resolves` is refused naming the part; a merge closes nothing and its audit has no Issue records to put back |
| spec | runs `concorde spec-validation` as a merge's default check, checks a task's Modules against the registry ([Tasks](tasks/module.md)) | a merge runs only the `--check` commands it is given; Modules are plain labels |
| method | a task is validated with `task-validation` and delivered with `delivery`, and the main agent starts Method's reading Operations, such as `understand`, `spec_panel` and `code_review`, as unbound runs ([Task sessions](task-session/module.md), [Main session](main-session/module.md)) | the task session delivers with `concorde task deliver`, which runs the checks it is given and makes the delivery commit ([Tasks](tasks/module.md)) |
| workflow | a task session may run a workflow in its worktree; the workflow part contributes that guidance | no workflow runs; the guidance has no workflow section |
| worker harness | the main agent edits the [worker configuration](../glossary.json#concept.worker-configuration) the worker harness part owns, and the workers of a task session's runs take their backend from it ([Main session](main-session/module.md), [Task sessions](task-session/module.md)) | no worker runs; the guidance has no worker-models section |

Coordination imports the code of none of these parts. It reaches each in these ways:

- Through the part's `concorde` command, JSON in and out.
- Through a file format the part's Spec defines.

Coordination learns the same way whether the part is installed:

- The spec part by its registry mirror `.concorde/specs.json`.
- The others by whether the worktree's own `concorde` offers their commands.
- The runs by Execution's run store existing at all.

When a process holding the merge lock runs a command needing that lock, the process hands the
lock on to that command. [Tasks](tasks/contracts.md#parts-not-depended-on) gives the exact rules.
