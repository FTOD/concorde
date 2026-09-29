# Tasks requirements

The Module-wide obligations of [Tasks](module.md). Exact fields, commands and error codes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Records

### req.tasks.primary-records — Each task has one folder in the primary worktree

Tasks SHALL keep every current task's [task record](../../glossary.json#concept.task-record),
[decision log](../../glossary.json#concept.decision-log) and trace in the task's folder
`.concorde/tasks/<task-id>/` of the primary worktree, and those of a closed task in its folder in
the [history](../../glossary.json#concept.history), `.concorde/history/<history key>/`, and nowhere
else.

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

### req.tasks.decision-log-committed — An ended task's decision log is in Git

When a task ends, Tasks SHALL commit its decision log on the primary branch at
`.concorde/decisions/<history key>.md`: `concorde task merge` in the merge commit it makes, and any
other close, once its closing is appended, in a commit of that file alone, unless the primary
branch already holds that file.

The copy in Git is what outlives [Tracing](../../tracing/module.md)'s retention; the task's folder
keeps its own log, which the copy never replaces.

### req.tasks.log-commit-alone — Committing a log commits nothing else

A close that commits a decision log SHALL leave every other change of the primary worktree, staged
or not, as it was, and refuse with `decision_log_uncommitted`, committing nothing and leaving the
task's folder current, when Git refuses that commit.

The same close run again commits the log and finishes the close.

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
[delivery commit](../../glossary.json#concept.delivery-commit), apart from holding a task's
[workspace lock](../../glossary.json#concept.workspace-lock) through Execution's own lock and moving
the task's whole folder, workspace folder included, to the history when the task is closed.

The lock file lives under `.concorde/locks/workspaces/`, and its holder is named there while Tasks
merges or closes the task, and nothing else in it is written.

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
task folder's `workspace/` as its workspace folder and the primary worktree's `.concorde` for its
locks, and is never rewritten by Tasks afterwards; closing removes it with the worktree.

### req.tasks.transitions — Only merging and closing change the stored state

Tasks SHALL store a task's state as `open` from the open until the task is closed, and then only
as `closed`, when merged or completed, or `failed`, except while `concorde task merge` has a merge
of the task that its checks have not decided, when it stores `merging`.

A `merging` task returns to `open` when its merge is undone or aborted, and becomes `closed` only
when every check of its merge passed. The record's `merging` field is set exactly while the state
is `merging`.

### req.tasks.derived-state — Active and delivered are derived

Tasks SHALL derive whether a task that is not closed or failed is `open`, `active` or `delivered`
from its workspace's runs in its workspace folder, its branch and its worktree each time the task is
listed or shown.

A `merging` task is shown as `merging`. Otherwise it is `delivered` when the branch head is a
delivery commit of the task's workspace that verifies and the worktree is clean, `active` when the workspace has a run, the branch moved past its base commit or the
worktree has uncommitted changes, and `open` otherwise. A new path Git cannot version, such as a
path a sandbox hides behind a `/dev/null` mount, is no uncommitted change, as for Delivery.

### req.tasks.delivery-verified — Only a delivery commit that verifies counts

Tasks SHALL count a task as delivered, and merge it or close it as merged, only when its branch
head is a [delivery commit](../../glossary.json#concept.delivery-commit) of its workspace that
verifies by Delivery's own check: it has exactly one parent.

A head that does not verify is shown `active`, `task show` lists the mismatch with that delivery,
and `merge` and `close --merged` refuse it with `delivery_unverified`, naming the mismatch, as
[scenario.tasks.delivery-unverified](scenarios.md#scenario.tasks.delivery-unverified) shows.

### req.tasks.failure-explained — A failed task says why

Closing a task as failed SHALL record a reason and either the
[error chains](../../glossary.json#concept.error-chain) that caused the failure, unchanged, or an
explicit declaration that no error caused it.

### req.tasks.closed-inert — A closed task stays closed

Tasks SHALL keep a closed or failed task in that state whatever its workspace records afterwards.

Closing removes the worktree and with it the workspace binding, and moves the task's folder, whose
workspace folder the binding named, to the history, so no run of the task's workspace can start;
one task runs one thing at a time by Execution's
[workspace lock](../../glossary.json#concept.workspace-lock), not by the record.

### req.tasks.close-when-ended — A task moves to the history only once it has ended

Tasks SHALL move a closed task's folder to the history only while it holds the task's workspace
lock, after it stopped, for a close without a merge, every task session of the task and every run
of the workspace still running.

A run of the task therefore never writes into a folder that has moved: none runs while the close
holds the lock, and none starts after it, since its binding names a folder that no longer exists.

### req.tasks.history-unique — No closed task replaces another

Tasks SHALL move a closed task's folder to a history folder that no other task used, under a
history key for which the primary worktree holds no decision log `.concorde/decisions/<key>.md`.

### req.tasks.closed-no-session — A closed task gets no task session

Tasks SHALL refuse with `task_closed` to start or record a
[task session](../../glossary.json#concept.task-session) for a closed or failed task.

Recording a session checks the task's state again inside the record update that writes the
session's node, so a close stored after the start's own check still refuses it.

### req.tasks.merge-verified — Merged means contained in the primary branch

Closing a task as merged SHALL succeed only when the task branch holds a delivery commit of the
task's workspace since its base, the latest one is the head of the branch and verifies, that head
is contained in the primary branch and the worktree has no uncommitted change.

### req.tasks.no-silent-discard — Uncommitted work is never discarded silently

Closing a task SHALL NOT remove a worktree that has uncommitted changes unless the task is closed
without a merge, as completed or failed, with `--force`.

### req.tasks.refusal-inert — A refusal changes nothing

A refused task command or record update SHALL leave every record, branch and worktree unchanged.

The exceptions are refusals that say so themselves: `binding_failed`, where `concorde task open`
leaves the worktree and branch it had added, naming them and how to remove them; and three `concorde task merge` refusals: `rollback_failed`, where Git would not
restore the primary branch and the task stays `merging`; a `check_failed` whose checks created
paths, which the reset leaves in the primary worktree and the refusal names; and a close that
failed after the merge and its checks succeeded, which leaves the checked merge in place and the
task `merging`.

`concorde task close` and `concorde task escalate` are not atomic either: each changes Git, the
task record and the decision log in steps that cannot be one transaction. Their refusals after a
step leave that step done, and say so:

- a close's `worktree_failed` may leave the worktree's submodules deinitialized, which the refusal
  says with how to restore them;
- a close refused while writing the record (`record_conflict`, `record_unwritable`) after it
  removed the worktree leaves the task in its state without its worktree, which the refusal says;
- a close's `decision_log_failed` leaves the task closed or failed in its record without its
  closing in the decision log;
- a close's `decision_log_uncommitted` leaves the task closed or failed in its record, with its
  closing in the decision log, and its folder current, since the log is not yet in Git;
- an escalation's `decision_log_failed` leaves the escalation in the task's trace and not in the
  decision log; the refusal names its number, carries the rendered chain, says that escalating
  again would record it twice and asks for the chain to be appended by hand.

Each refusal of a close says that running the same close again finishes it once the cause is
fixed, or, for a close run by a merge whose task stays `merging`, `concorde task merge <task-id>
--resume`: the rerun skips a worktree that is gone, and the same close of a task already closed
with that outcome appends the closing its decision log lacks, commits the log the primary branch
lacks and changes nothing else.

## Merging

### req.tasks.merge-exact-commit — A merge merges the commit it checked

`concorde task merge` SHALL merge, by its commit identity, the task branch's head that its checks
before the merge accepted, never the branch by name, in a merge commit whose second parent is that
head, whose trailer `Concorde-Task` names the task and which adds the task's decision log, even when
the primary branch could fast-forward.

A commit added to the task branch after those checks is therefore never merged unchecked; closing
the task as merged then refuses with `not_merged`, since the branch's head is no longer its latest
delivery commit.

### req.tasks.merge-workspace-locked — No run of a task changes it while it is merged or closed

`concorde task merge` and `concorde task close` SHALL hold the task's
[workspace lock](../../glossary.json#concept.workspace-lock), taken before the merge lock and held
to the end, waiting for it inside the command up to `--wait` seconds, and refuse with
`workspace_busy`, naming the lock's holder and changing nothing, when a run still holds it then.

Neither holds the merge lock while it waits for the workspace lock.

### req.tasks.merge-serialized — One merge into the primary at a time

Tasks SHALL hold the [merge lock](../../glossary.json#concept.merge-lock) of the primary worktree
for the whole of every `concorde task merge`, `open` and `close`, so no two of them overlap and none
sees a merge that may still be rolled back.

### req.tasks.merge-lock-released — The lock ends with its process

The merge lock SHALL be released when the process holding it ends, whether it finished, failed or
was killed, without any action by another session.

### req.tasks.merge-busy-named — A waiter learns who holds the lock

A merge, open or close that gives up waiting SHALL name the holder's command, task, process and
start time, and the Claude Code session the holder works for when its environment names one.

### req.tasks.merge-handed-locks — A merge may be handed its locks

A merge started with the task's workspace lock and the merge lock already held on descriptors it
inherited, and named in its environment, SHALL hold them from its start without waiting until it
ends.

### req.tasks.wait-without-polling — A wait is woken, never polls

`concorde task wait` SHALL return when the task reaches one of the named states, the run's runner
holds no [run lock](../../glossary.json#concept.run-lock), or nobody holds the lock, learning of each
change from the kernel and blocking on the lock itself rather than reading the records repeatedly.

It answers at once when that is already so.

### req.tasks.wait-bounded — A wait says why it ended without its answer

A wait SHALL end with `wait_unreachable` when the task ended in a state it does not name, and with
`wait_timeout` when its `--timeout` passes first, changing nothing.

A task wait admits only `delivered`, `merging`, `closed` and `failed`, the states a task reaches
while its workspace lock is held.

### req.tasks.merge-all-or-nothing — A merge is checked or undone

A `concorde task merge` that has run `git merge` SHALL end with the primary branch either at the
merge commit, all its checks passed and the task closed as merged, or at the commit it started from
with the task delivered again, or else with the task left `merging`.

It leaves the task `merging` only when it cannot reach either end itself, because its process was
interrupted, Git refused the reset or the close failed; `--resume` or `--abort` then brings it to one
of the two.

A merge refused before `git merge` is governed by
[req.tasks.merge-clean-primary](#req.tasks.merge-clean-primary) and
[req.tasks.refusal-inert](#req.tasks.refusal-inert).

### req.tasks.merging-recorded — A merge is recorded before it touches the primary branch

`concorde task merge` SHALL store the task as `merging`, with the primary branch's name and commit
before the merge, the checked commit, the history key the task will close under and the checks it
will run, before it runs `git merge`, and record the merge commit once it has made it.

### req.tasks.merge-incomplete-refused — Nothing builds on an unchecked merge

While a task is stored as `merging` and no live process holds the merge lock, `concorde task open`,
`merge`, `close`, `session` and `escalate` SHALL refuse with `merge_incomplete`, for every task and
changing nothing, naming the merging task, the commit before its merge, its merge commit, the
primary branch's head and the `--resume` and `--abort` recovery.

The exceptions are `merge --resume` and `merge --abort` of the merging task itself; `list` and
`show` read and are never refused. While the merge's
process still holds the lock, `open`, `merge` and `close` wait for it as for any holder and a
`session` or `escalate` of the merging task refuses with `merge_busy`.

### req.tasks.merge-recovery — An interrupted merge is resumed or aborted

Tasks SHALL finish an interrupted merge only on the main agent's request: `concorde task merge
<task-id> --resume` reruns, when the primary branch's head is still the interrupted merge's commit,
the checks that merge recorded and then closes the task as merged or undoes the merge exactly as an
uninterrupted merge does, and otherwise refuses with `not_resumable`; `concorde task merge
<task-id> --abort` resets the primary branch to the commit before the merge when its head is the
merge commit, and returns the task to delivered.

Both refuse with `merge_diverged`, touching nothing, when the primary worktree is on another branch
or its head is neither the commit before the merge nor the merge commit, and with `not_merging` for
a task that is not `merging`.

### req.tasks.empty-log-warned — A merge warns of an unwritten decision log

`concorde task merge` SHALL list, in its output's `warnings`, the task's decision log with its path when the log is missing or holds nothing beyond the heading and goal that `open` wrote, without refusing or undoing the merge for it.

Tasks cannot tell whether a task needed any decision, so an empty log is a reminder to whoever
merges, not a failure: the [main agent](../../glossary.json#concept.main-agent) appends what it
decided alone before it reports the task.

### req.tasks.merge-clean-primary — A merge starts from a clean primary

`concorde task merge` SHALL refuse, before merging, a primary worktree with a detached `HEAD` or any
uncommitted or untracked path, and a task that `close --merged` would refuse for any reason other
than containment.

A new path Git cannot version, such as a sandbox's `/dev/null` mount of `.bashrc`, is no untracked
path here, by the same rule as a task worktree's changes.

### req.tasks.refusal-detail — A refusal is an error link

Every refusal of a `concorde task` command SHALL print an error link that names what was refused, with the task, Module, path, run or Git output concerned, and why Tasks cannot handle it.

### req.tasks.escalation-kept — Escalations keep their whole chain

An escalation SHALL record the escalated errors unchanged as the causes of the escalating session's link, in the task record and the decision log, and an escalation that names no error that link alone, with no causes.

