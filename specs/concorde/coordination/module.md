# Coordination

## Purpose

Coordination is the upper of Concorde's two halves: project management and task-level parallelism.
It is where the developer and the main agent decide what to work on, split it into tasks, give each
task its own branch and worktree, run several tasks at once through task sessions, keep the reasons
behind decisions taken without the developer, escalate what matters and merge what was delivered.
The developer and the main agent rely on it; it binds no files of its own, and its three children
do the work: the Main session, Tasks and Task sessions.

Coordination does not do the bounded work itself. Inside a task's worktree the changes are made
directly by whoever works the task, or through [Execution](../execution/module.md), the lower half,
which knows nothing of tasks: Coordination hands it a workspace by writing that worktree's
workspace binding, and learns what happened there only from what Execution recorded. It decides
direction, splitting and merging, never how a worker is bounded, launched or checked.

## Terminology

This entry defines no terms of its own. It relies on the words the root defines for the people and
agents, and on the words of the Modules it points to.

| Term | Definition |
| --- | --- |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../vocabulary.md#concept.concorde.task-session) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Agent harness](../harness/module.md#concept.harness.harness) | |
| [Task](tasks/module.md#concept.tasks.task) | |
| [Workspace binding](../execution/module.md#concept.execution.workspace-binding) | |
| [Run store](../execution/module.md#concept.execution.run-store) | |

## Usage

The developer works with the main agent in the primary worktree. For each piece of work the main
agent opens a task, which Tasks makes into a branch, a worktree bound as a workspace, a record and
a decision log. It then either works the task itself, inside that worktree, or, when it wants
several tasks to run at once, starts a task session for each. Whoever works a task changes Specs and
code there, directly or through runs of Execution, validates and delivers it. The main agent then
merges the delivered task from the primary worktree and reports to the developer.

The task level is stable, but who plays it is not:

| | Main agent in a task | Task session |
| --- | --- | --- |
| Write boundary | none: Concorde does not restrict the main agent | its task worktree and decision log, plus what its commits, runs and escalations write |
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
```

The upper half talks to the lower half in exactly three ways. Tasks writes the
[workspace binding](../execution/module.md#concept.execution.workspace-binding) of each task
worktree when it opens the task, naming the workspace after the task. Whoever works the task runs
Execution's commands inside that worktree, never naming the task. And Tasks reads back what
Execution recorded: the task's runs in the [run store](../execution/module.md#concept.execution.run-store)
and its delivery commits on the task branch, from which it derives whether a task is active or
delivered. No record is written by both halves, so neither can leave the other with a state that
disagrees with what happened.

<a id="uses-execution"></a>

**Execution** gets the bounded work done in a bound workspace and records it. Coordination relies
on it working only on the workspace the binding names, never writing the binding, recording every
run under the binding's records directory by the workspace's name, and committing a delivery only
as a delivery commit on the bound branch. It relies on nothing inside Execution beyond those
records and the commands' results.

### What the task level relies on

Every level of Coordination gets its harness from one place and the task level its workspace from
another.

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

The **Harness** generates the [agent harness](../harness/module.md#concept.harness.harness) of a
task session from its task: the session boundary that confines its writes to its task worktree,
its decision log, and what its commits, runs and escalations write: the Git directory, the run
store and the task records. The main session's harness is its installed guidance
alone, since Concorde places no permission limits on the main agent. A task session that cannot get
its harness does not start.

An extra level of messaging is one more place for an error to be lost, so the loss is prevented
structurally: a task session escalates with its own link on top of the chains it received, and the
main agent adds its link on top of that before the developer sees it.

### The children

<a id="contains-main-session"></a>

The **Main session** is the level where the developer and the main agent work on the whole
project: the guidance that makes a Claude Code or pi session in the primary worktree the main
agent, including the method of working inside a task that the main agent and its task sessions
share, and pi's run view. It starts task sessions when it delegates the task level.

<a id="contains-tasks"></a>

**Tasks** manages the task level's workspace: each task's branch, its worktree and the binding that
makes it a workspace, its record and its decision log, the derived state of each task, and the
merge of a delivered task into the primary branch under a lock.

<a id="contains-task-session"></a>

**Task sessions** is the task level delegated: it starts a task session in a task worktree on the
main agent's own program, confines its writes with the session boundary, and in pi runs and records
its rounds.
