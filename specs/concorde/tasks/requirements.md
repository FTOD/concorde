# Tasks requirements

The Module-wide obligations of [Tasks](module.md). Exact fields, commands and error codes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Records

### req.tasks.primary-records — Records live in the primary worktree

Tasks SHALL keep every task record and decision log under `.concorde/tasks/` of the primary
worktree and nowhere else.

### req.tasks.store-writes — Only the Task store writes records

Every change to a task record SHALL be made by the Task store as one file transaction bound to the
digest of the record bytes it replaces.

A concurrent change is detected by the digest, never overwritten; after three conflicting attempts
the update is refused with `record_conflict`.

### req.tasks.records-kept — Records outlive their task

Tasks SHALL NOT delete a task record or a decision log, including when the task is closed.

### req.tasks.decision-log-untouched — The decision log belongs to the main agent

Tasks SHALL NOT change a decision log after creating it except by appending an escalation the main agent requested.

### req.tasks.registered-modules — Records name only registered Modules

Tasks SHALL refuse to open a task or begin a run that names a Module absent from the registry it
checks.

## Lifecycle

### req.tasks.primary-only — Tasks open, close and start sessions only from the primary

The `concorde task open`, `concorde task close` and `concorde task session` commands SHALL refuse
to run outside the primary worktree.

### req.tasks.worktree-ignored — A worktree inside the primary is ignored there

Tasks SHALL refuse to open a task whose worktree path lies inside the primary worktree unless Git
ignores that path in the primary worktree.

### req.tasks.one-worktree — One branch and one worktree per task

Opening a task SHALL create exactly one new branch `concorde/<task-id>` and one new worktree
checked out on it.

Opening refuses when the identity, the branch or the worktree path is already taken, so no two
tasks ever share a branch or a worktree.

### req.tasks.transitions — States move only along allowed transitions

Tasks SHALL change a task's state only along open to active, active to delivered, delivered to
active for a writing run, delivered to merged, and open, active or delivered to abandoned.

### req.tasks.one-run — One running Operation per task

Tasks SHALL refuse to begin a run for a task that has a running run whose host process is alive.

### req.tasks.closed-inert — Closed tasks accept no runs

Tasks SHALL refuse to begin a run for a task in state merged or abandoned.

### req.tasks.merge-verified — Merged means contained in the primary branch

Closing a task as merged SHALL succeed only when the task is delivered, its latest delivery commit
is the head of the task branch, that head is contained in the primary branch and the worktree has
no uncommitted change.

### req.tasks.no-silent-discard — Uncommitted work is never discarded silently

Closing a task SHALL NOT remove a worktree that has uncommitted changes unless the task is abandoned
with `--force`.

### req.tasks.refusal-inert — A refusal changes nothing

A refused task command or record update SHALL leave every record, branch and worktree unchanged.

### req.tasks.refusal-detail — A refusal is an error link

Every refusal of a `concorde task` command SHALL print an error link that names what was refused, with the task, Module, path, run or Git output concerned, and why Tasks cannot handle it.

### req.tasks.escalation-kept — Escalations keep their whole chain

An escalation SHALL record the escalated errors unchanged as the causes of the escalating session's link, in the task record and the decision log.

## Task sessions

### req.tasks.session-boundary — A task session writes only its task

The settings Tasks writes for a task session SHALL let the session's Edit and Write tools change
only the task worktree and its decision log, and its Bash commands write only the task worktree,
the repository's Git directory, `.concorde/runs/`, `.concorde/tasks/` and the user's package
caches.

### req.tasks.session-recorded — A started session is recorded

Tasks SHALL append a task session to the task record only after Claude Code reported it started.

A session Claude Code did not report as started leaves the record unchanged.
