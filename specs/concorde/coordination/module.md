# Coordination

## Purpose

Coordination is the upper of Concorde's two halves: project management and task-level parallelism.
It is where the developer and the [main agent](../glossary.json#concept.main-agent) decide what to
work on, split it into [tasks](../glossary.json#concept.task), give each task its own branch and
worktree, run several tasks at once
through [task sessions](../glossary.json#concept.task-session), keep the reasons behind decisions
taken without the developer, escalate what matters and merge what was delivered. The developer and
the main agent rely on it; it binds no files of its own, and its three children do the work: the
Main session, Tasks and Task sessions.

Coordination does not do the bounded work itself. Inside a task's worktree the changes are made
directly by whoever works the task, or through [Execution](../execution/module.md), the lower half,
which knows nothing of tasks: Coordination hands it a workspace by writing that worktree's
[workspace binding](../glossary.json#concept.workspace-binding), and learns what happened there
only from what Execution recorded. It decides direction, splitting and merging, never how a
[worker](../glossary.json#concept.worker) is bounded, launched or checked.

## Usage

The developer works with the main agent in the primary worktree. For each piece of work the main
agent opens a task, which Tasks makes into a branch, a worktree bound as a workspace, a
[task record](../glossary.json#concept.task-record) and a
[decision log](../glossary.json#concept.decision-log). It then either works the task itself, inside
that worktree, or, when it wants several tasks to run at once, starts a task session for each; only
tasks whose Modules and shared files do not overlap run at once, and the rest run one after
another. Whoever works a task changes [Specs](../glossary.json#concept.spec) and code there,
directly or through [runs](../glossary.json#concept.run) of Execution, validates and delivers it.
The main agent then merges the delivered task from the primary worktree and reports to the
developer.

```d2 illustrative
direction: right
primary: Primary worktree, main agent {
  open: Open the task
  merge: Merge the delivered task
  report: Report to the developer
}
task: Task worktree, main agent or task session {
  work: Change Specs and code, directly or through runs
  validate: Validate
  deliver: Deliver
  work -> validate -> deliver
}
primary.open -> task.work: enter it, or start a task session
task.deliver -> primary.merge: leave it, or the task session reports
primary.merge -> primary.report
```

Work does not always go that way. A result that is not `ok` is read with its whole [error
chain](../glossary.json#concept.error-chain), then repaired within the task or escalated with a link
of its own: a task session escalates to the main agent, which decides ordinary questions itself
under the escalation policy and asks the developer
only for decisions with major impact. A merge refused for a conflict is resolved in the task
worktree by merging the primary branch into the task branch and delivering again, a merge whose
checks fail is undone and the failure handled as new work, and a task that reached its goal without
a merge, or will not reach it, is closed as completed or failed instead. The [Main
session](main-session/module.md) and [Tasks](tasks/module.md) give the details.

The task level, level 2 of Concorde's [levels of work](../module.md#the-levels-of-work) below the
main session's level 1, is stable, but who plays it is not:

| | Main agent in a task | Task session |
| --- | --- | --- |
| Write boundary | none: Concorde does not restrict the main agent | for its own file tools and shell: its task worktree and decision log, plus what its commits, runs and escalations write and package caches |
| Escalates to | the developer | the main agent |
| Lifecycle | enters and leaves the worktree | started, answered and stopped by the main agent |
| Merges | yes, from the primary worktree | never |

## Design

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
[merge lock](../glossary.json#concept.merge-lock), which one process holds at a time. Only a
delegated task session gets a write boundary, which keeps its mistakes inside its task while it
runs beside others; Concorde places no permission limits on the main agent.

### The seam with Execution

```d2 illustrative
coordination: Coordination {
  tasks: Tasks
  main: Main session
  session: Task sessions
}
execution: Execution {
  binding: Workspace binding
  store: Run store
  commits: Delivery commits
}
coordination.tasks -> execution.binding: writes when a task opens
coordination.main -> execution: runs in the task worktree
coordination.session -> execution: runs in its task worktree
coordination.tasks -> execution.store: reads a task's runs
coordination.tasks -> execution.commits: reads whether a task is delivered
coordination.main -> execution.store: follows runs in pi
```

The upper half talks to the lower half only through the binding, Execution's commands and what
Execution recorded. Tasks writes the
[workspace binding](../glossary.json#concept.workspace-binding) of each task worktree when it opens
the task, naming the workspace after the task. Whoever works the task runs Execution's commands
inside that worktree, never naming the task. Tasks reads back the task's runs in the
[run store](../glossary.json#concept.run-store) and its
[delivery commits](../glossary.json#concept.delivery-commit) on the task branch, and derives whether
a task is active or delivered from them together with its branch head and whether its worktree is
clean. The Main session's pi [run view](../glossary.json#concept.run-view) follows every run through
its [run progress file](../glossary.json#concept.run-progress-file) in the run store and the
[progress file](../glossary.json#concept.progress-file) of the worker it launched. No record is
written by both halves, so neither can leave the other with a state that disagrees with what
happened.

The main agent may also start an [Operation](../glossary.json#concept.operation) that allows it as
an [unbound run](../glossary.json#concept.unbound-run) in the primary worktree, for a question or a
review that changes nothing; such a run has no workspace and belongs to no task.

<a id="uses-execution"></a>

**Execution** gets the bounded work done in a bound workspace and records it. Coordination relies
on it working only on the workspace the binding names, never writing the binding, recording every
run of a bound workspace under the binding's records directory by the workspace's name, and
committing a delivery only as a delivery commit on the bound branch. It relies on nothing inside
Execution beyond those records and the commands' results. A run whose runner ended without a result
is taken as lost rather than trusted as running, and a run of another workspace named to Tasks is
refused with `unknown_run`; [Tasks](tasks/module.md) gives the details.

### What the task level relies on

A task session gets its harness from the Harness, the main session gets only the guidance
Distribution installs, and the task level gets its workspace from Tasks.

```d2
coordination: Coordination {
  main: Main session
  task: Task sessions
  tasks: Tasks
  main -> task
  main -> tasks
  task -> tasks
}
harness: Harness
coordination.task -> harness
```

<a id="uses-harness"></a>

The **Harness** generates the [agent harness](../glossary.json#concept.agent-harness) of a task
session from its task: the [session boundary](../glossary.json#concept.session-boundary), which
confines what the session's own file tools and shell write to its task worktree, its decision log,
what its commits, runs and escalations write (the Git directory, the run store and the task
records), the user's package caches and, in pi, a private temporary directory. Tools that other
extensions or MCP servers add are outside it, and it guards against mistakes, not a malicious
session; the [Harness](../harness/module.md) states its exact paths and limits. The main session's
harness is its installed guidance alone, since Concorde places no permission limits on the main
agent. A task session that cannot get its harness does not start.

### Escalations

An extra level of messaging is one more place for an error to be lost, so the loss is prevented
structurally: a task session escalates with `concorde task escalate --by task-session`, which Tasks
records as the session's own link on top of the chains it received, unchanged. The main agent
decides the escalation itself when the escalation policy lets it, and otherwise adds its own link
on top before the developer sees it.

### The children

<a id="contains-main-session"></a>

The **Main session** is the level where the developer and the main agent work on the whole project:
the guidance that makes a Claude Code or pi session in the primary worktree the main agent,
including the method of working inside a task that the main agent and its task sessions share, and
pi's run view. It asks Task sessions to start a task session when it delegates the task level.

<a id="contains-tasks"></a>

**Tasks** manages the task level's workspace: each task's branch, its worktree and the binding that
makes it a workspace, its record and its decision log, the derived state of each task, and the
merge of a delivered task into the primary branch under a lock.

<a id="contains-task-session"></a>

**Task sessions** is the task level delegated: it starts a task session in a task worktree on the
main agent's own program, confines its writes with the session boundary, and in pi runs and records
its rounds.
