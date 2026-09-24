# Main session requirements

What the [main-session guidance](module.md) must tell the main agent. They are obligations on the
content of the guidance; whether a model follows it is not something a deterministic check can
establish. The [scenarios](scenarios.md) show the intended behaviour.

## Working method

### req.main-session.tasks-own-changes — Changes run in tasks

The guidance SHALL tell the main agent to make every change of Spec meaning or code behaviour in a
task, from inside the task worktree, directly or through Operations, and never in the primary
worktree.

Trivial housekeeping that changes neither, such as regenerating the registry mirror after a merge,
is the only exception.

### req.main-session.worktree-own-concorde — A task runs its worktree's Concorde

The guidance SHALL tell whoever works on a task to run every `concorde` command for it from the
task worktree with that worktree's own copy, never the primary worktree's.

### req.main-session.one-task-at-a-time — One task per session at a time

The guidance SHALL tell the main agent to enter a task worktree to carry out a single task, to be
inside at most one task at a time, and to leave it after delivery.

### req.main-session.task-sessions — Split work goes to task sessions

The guidance SHALL tell the main agent to start a task session per task, with
`concorde task session`, for work split into several tasks, and to stay in the primary worktree
while any runs.

### req.main-session.task-session-guidance — A task session is told its role

The task-session guidance SHALL tell a task session to work only inside its task, to decide
ordinary questions within the task's goal and Modules, to escalate the rest to the main agent with
its own link on top of the error chain, to report to the main agent when it has delivered or cannot
go further, and never to merge or close the task.

### req.main-session.parallel-by-worktree — Parallelism only between worktrees

The guidance SHALL tell the main agent to run tasks in parallel only in separate worktrees and only
when their Modules and shared files do not overlap.

### req.main-session.background-operations — Operations run in background

The guidance SHALL tell the main agent to run each Operation with `concorde run … --task` in
background Bash and to act on its Operation result.

### req.main-session.decision-log — Decisions are recorded

The guidance SHALL tell the main agent to record every result that is not `ok` and every decision
made without the developer in the task's decision log.

### req.main-session.merge-without-authorization — Delivered tasks are merged

The guidance SHALL tell the main agent to merge a task branch that `delivery` committed without
asking the developer for authorization, from the primary worktree, with `concorde task merge`
rather than `git merge`, so that the merge holds the merge lock and validates the primary branch
after merging.

## Worker models

### req.main-session.developer-chooses-models — The developer chooses worker models

The guidance SHALL tell the main agent to change the models workers use only when the developer asks, to let the developer choose among the candidates `concorde workers models` lists (in pi through the model picker, in Claude Code through its question tool), and to change an existing task's configuration only when the developer asks for that task.

## Escalation

### req.main-session.escalation-policy — Only major decisions reach the developer

The guidance SHALL state the escalation policy: decide ordinary questions, record and report them,
and ask the developer before acting only on decisions with major impact.

### req.main-session.read-chain — The whole error chain is read

The guidance SHALL tell the main agent to read the whole error chain of a result that is not `ok` before deciding.

### req.main-session.extend-chain — An escalation extends the chain

The guidance SHALL tell the main agent to escalate an error it cannot handle with `concorde task escalate`, adding its own link on top of the chain instead of summarizing it.

## Issues

### req.main-session.issues-by-operations — Issues are solved by ordinary work

The guidance SHALL tell the main agent to solve an Issue by running ordinary Operations on the
Issue's Module in a task and to close the Issue on that task's branch.
