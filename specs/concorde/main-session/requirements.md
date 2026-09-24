# Main session requirements

What the [main-session guidance](module.md) must tell the main agent. They are obligations on the
content of the guidance; whether a model follows it is not something a deterministic check can
establish. The [scenarios](scenarios.md) show the intended behaviour.

## Working method

### req.main-session.tasks-own-changes — Changes run in tasks

The guidance SHALL tell the main agent to make every change of Spec meaning or code behaviour
through Operations run in a task worktree, never by editing the project itself.

Trivial housekeeping that changes neither, such as regenerating the registry mirror, is the only
exception.

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
asking the developer for authorization.

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
