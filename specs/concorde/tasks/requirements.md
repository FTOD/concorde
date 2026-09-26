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

Tasks SHALL NOT change a decision log after creating it except by appending a requested escalation, a workflow report or the entry recording how the task ended.

### req.tasks.one-workflow — A task runs at most one workflow

Tasks SHALL refuse to record a workflow step that names a workflow other than the one the task record names.

### req.tasks.registered-modules — Records name only registered Modules

Tasks SHALL refuse to open a task or begin a run that names a Module absent from the registry it
checks.

## Lifecycle

### req.tasks.primary-only — Tasks open, close, merge and start sessions only from the primary

The `concorde task open`, `concorde task close`, `concorde task merge` and `concorde task session`
commands SHALL refuse to run outside the primary worktree.

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
active for a writing run, delivered to closed when merged, and open, active or delivered to closed
when completed without a merge or to failed.

### req.tasks.failure-explained — A failed task says why

Closing a task as failed SHALL record a reason and either the error chains that caused the
failure, unchanged, or an explicit declaration that no error caused it.

### req.tasks.one-run — One running Operation per task

Tasks SHALL refuse to begin a run for a task that has a running run whose host process is alive.

### req.tasks.closed-inert — Closed tasks accept no runs

Tasks SHALL refuse to begin a run for a task in state closed or failed.

### req.tasks.merge-verified — Merged means contained in the primary branch

Closing a task as merged SHALL succeed only when the task is delivered, its latest delivery commit
is the head of the task branch, that head is contained in the primary branch and the worktree has
no uncommitted change.

### req.tasks.no-silent-discard — Uncommitted work is never discarded silently

Closing a task SHALL NOT remove a worktree that has uncommitted changes unless the task is closed
without a merge, as completed or failed, with `--force`.

### req.tasks.refusal-inert — A refusal changes nothing

A refused task command or record update SHALL leave every record, branch and worktree unchanged.

The two exceptions are `concorde task merge` refusals that say so themselves: `rollback_failed`,
where Git would not restore the primary branch, and a close that failed after the merge and its
checks succeeded, which leaves the checked merge in place.

## Merging

### req.tasks.merge-serialized — One merge into the primary at a time

Tasks SHALL hold the merge lock of the primary worktree for the whole of every `concorde task
merge`, `open` and `close`, so no two of them overlap and none sees a merge that may still be
rolled back.

### req.tasks.merge-lock-released — The lock ends with its process

The merge lock SHALL be released when the process holding it ends, whether it finished, failed or
was killed, without any action by another session.

### req.tasks.merge-busy-named — A waiter learns who holds the lock

A merge, open or close that gives up waiting SHALL name the holder's command, task, process and
start time.

### req.tasks.merge-all-or-nothing — A merge is checked or undone

`concorde task merge` SHALL end with the primary branch either at the merge commit, all its checks
passed and the task closed as merged, or at the commit it started from with the task still
delivered, apart from a `rollback_failed` or a failed close that it reports.

### req.tasks.merge-clean-primary — A merge starts from a clean primary

`concorde task merge` SHALL refuse, before merging, a primary worktree with a detached `HEAD` or any
uncommitted or untracked path, and a task that `close --merged` would refuse for any reason other
than containment.

### req.tasks.refusal-detail — A refusal is an error link

Every refusal of a `concorde task` command SHALL print an error link that names what was refused, with the task, Module, path, run or Git output concerned, and why Tasks cannot handle it.

### req.tasks.escalation-kept — Escalations keep their whole chain

An escalation SHALL record the escalated errors unchanged as the causes of the escalating session's link, in the task record and the decision log.

