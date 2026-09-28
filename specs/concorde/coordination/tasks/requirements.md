# Tasks requirements

The Module-wide obligations of [Tasks](module.md). Exact fields, commands and error codes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Records

### req.tasks.primary-records — Records live in the primary worktree

Tasks SHALL keep every [task record](../../glossary.json#concept.task-record) and
[decision log](../../glossary.json#concept.decision-log) under `.concorde/tasks/` of the primary
worktree and nowhere else.

### req.tasks.store-writes — Only the Task store writes records

Every change to a task record SHALL be made by the [Task](../../glossary.json#concept.task) store.

### req.tasks.record-transactions — Each record write is one bound transaction

Every change to a task record SHALL be one
[file transaction](../../glossary.json#concept.file-transaction) bound to the digest of the record
bytes it replaces.

A concurrent change is detected by the digest, never overwritten; after three conflicting attempts
the update is refused with `record_conflict`.

### req.tasks.records-kept — Records outlive their task

Tasks SHALL NOT delete a task record or a decision log, including when the task is closed.

### req.tasks.decision-log-untouched — The decision log belongs to the main agent

Tasks SHALL NOT change a decision log after creating it except by appending a requested escalation or the entry recording how the task ended.

Workflow reports and the session's own decisions are written into the log by the session working
on the task, never by Tasks.

### req.tasks.registered-modules — Records name only registered Modules

Tasks SHALL refuse to open a task that names a [Module](../../glossary.json#concept.module) absent
from the primary worktree's registry.

A record's Modules never change after the open; the Modules a run worked on are in its
[run result](../../glossary.json#concept.run-result).

### req.tasks.no-copies — Tasks keeps no copy of what Execution records

Tasks SHALL NOT store a task's runs, deliveries or workflow in its record.

What happened in a task's workspace is read where Execution recorded it, each time it is needed,
so no second copy can disagree with it.

### req.tasks.no-foreign-writes — Tasks writes nothing Execution records

Tasks SHALL NOT write the [run store](../../glossary.json#concept.run-store), a
[workflow record](../../glossary.json#concept.workflow-record) or a
[delivery commit](../../glossary.json#concept.delivery-commit).

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

### req.tasks.binding — Every task worktree is a bound workspace

Opening a task SHALL write the task record only after writing the new worktree's
[workspace binding](../../glossary.json#concept.workspace-binding), which names the task identity as
the workspace.

The binding satisfies the
[binding contract](../../execution/contracts.md#contract.execution.workspace-binding), names the
primary worktree's `.concorde` as the records directory and is never rewritten by Tasks afterwards;
closing removes it with the worktree.

### req.tasks.transitions — Only closing changes the stored state

Tasks SHALL store a task's state as `open` from the open until the task is closed, and then only
as `closed`, when merged or completed, or `failed`.

### req.tasks.derived-state — Active and delivered are derived

Tasks SHALL derive whether a task that is not closed or failed is `open`, `active` or `delivered`
from its workspace's runs in the run store, its branch and its worktree each time the task is
listed or shown.

It is `delivered` when the branch head is a delivery commit of the task's workspace and the worktree
is clean, `active` when the workspace has a run, the branch moved past its base commit or the
worktree has uncommitted changes, and `open` otherwise.

### req.tasks.failure-explained — A failed task says why

Closing a task as failed SHALL record a reason and either the
[error chains](../../glossary.json#concept.error-chain) that caused the failure, unchanged, or an
explicit declaration that no error caused it.

### req.tasks.closed-inert — A closed task stays closed

Tasks SHALL keep a closed or failed task in that state whatever its workspace records afterwards.

Closing removes the worktree and with it the workspace binding, so no run of the task's workspace
can start there; one task runs one thing at a time by Execution's
[workspace lock](../../glossary.json#concept.workspace-lock), not by the record.

### req.tasks.closed-no-session — A closed task gets no task session

Tasks SHALL refuse with `task_closed` to start or record a
[task session](../../glossary.json#concept.task-session) for a closed or failed task.

### req.tasks.merge-verified — Merged means contained in the primary branch

Closing a task as merged SHALL succeed only when the task branch holds a delivery commit of the
task's workspace since its base, the latest one is the head of the branch, that head is contained
in the primary branch and the worktree has no uncommitted change.

### req.tasks.no-silent-discard — Uncommitted work is never discarded silently

Closing a task SHALL NOT remove a worktree that has uncommitted changes unless the task is closed
without a merge, as completed or failed, with `--force`.

### req.tasks.refusal-inert — A refusal changes nothing

A refused task command or record update SHALL leave every record, branch and worktree unchanged.

The exceptions are refusals that say so themselves: `config_copy_failed` and `binding_failed`,
where `concorde task open` leaves the worktree and branch it had added, naming them and how to
remove them; and three `concorde task merge` refusals: `rollback_failed`, where Git would not
restore the primary branch; a `check_failed` whose checks created paths, which the reset leaves in
the primary worktree and the refusal names; and a close that failed after the merge and its checks
succeeded, which leaves the checked merge in place.

## Merging

### req.tasks.merge-serialized — One merge into the primary at a time

Tasks SHALL hold the [merge lock](../../glossary.json#concept.merge-lock) of the primary worktree
for the whole of every `concorde task merge`, `open` and `close`, so no two of them overlap and none
sees a merge that may still be rolled back.

### req.tasks.merge-lock-released — The lock ends with its process

The merge lock SHALL be released when the process holding it ends, whether it finished, failed or
was killed, without any action by another session.

### req.tasks.merge-busy-named — A waiter learns who holds the lock

A merge, open or close that gives up waiting SHALL name the holder's command, task, process and
start time.

### req.tasks.merge-all-or-nothing — A merge is checked or undone

A `concorde task merge` that has run `git merge` SHALL end with the primary branch either at the
merge commit, all its checks passed and the task closed as merged, or at the commit it started from
with the task still delivered, apart from a `rollback_failed` or a failed close that it reports.

A merge refused before `git merge` is governed by
[req.tasks.merge-clean-primary](#req.tasks.merge-clean-primary) and
[req.tasks.refusal-inert](#req.tasks.refusal-inert).

### req.tasks.empty-log-warned — A merge warns of an unwritten decision log

`concorde task merge` SHALL list, in its output's `warnings`, the task's decision log with its path when the log is missing or holds nothing beyond the heading and goal that `open` wrote, without refusing or undoing the merge for it.

Tasks cannot tell whether a task needed any decision, so an empty log is a reminder to whoever
merges, not a failure: the [main agent](../../glossary.json#concept.main-agent) appends what it
decided alone before it reports the task.

### req.tasks.merge-clean-primary — A merge starts from a clean primary

`concorde task merge` SHALL refuse, before merging, a primary worktree with a detached `HEAD` or any
uncommitted or untracked path, and a task that `close --merged` would refuse for any reason other
than containment.

### req.tasks.refusal-detail — A refusal is an error link

Every refusal of a `concorde task` command SHALL print an error link that names what was refused, with the task, Module, path, run or Git output concerned, and why Tasks cannot handle it.

### req.tasks.escalation-kept — Escalations keep their whole chain

An escalation SHALL record the escalated errors unchanged as the causes of the escalating session's link, in the task record and the decision log.

