# Tasks requirements

The Module-wide obligations of [Tasks](module.md). Exact fields, commands and error codes are in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations at work.

## Records

### req.tasks.primary-records — Each task has one folder in the primary worktree

Tasks SHALL keep every task's [task record](../../glossary.json#concept.task-record),
[decision log](../../glossary.json#concept.decision-log) and trace in these locations and nowhere
else:

- For every current task, the task's folder `.concorde/tasks/<task-id>/` of the primary worktree.
- For a closed task, its folder in the [history](../../glossary.json#concept.history),
  `.concorde/history/<history key>/`.

### req.tasks.store-writes — Only the Task store writes records

The [Task](../../glossary.json#concept.task) store SHALL make every change to a task record.

### req.tasks.record-transactions — Each record write is one bound transaction

Every change to a task record SHALL be one
[file transaction](../../glossary.json#concept.file-transaction) bound to the digest of the record
bytes it replaces.

A change made before the transaction's digest check is detected. The update is applied again to what
is there. After three conflicting attempts, the update is refused with `record_conflict`. During the
transaction, the task's lock excludes a change, not the digest. Every writer of the record holds
that lock.

### req.tasks.records-kept — Records outlive their task

Tasks SHALL NOT delete a task record or a decision log, including when the task is closed.

### req.tasks.decision-log-committed — An ended task's decision log is in Git

When a task ends, Tasks SHALL commit its decision log on the primary branch at
`.concorde/decisions/<history key>.md` exactly as the log stands once its closing is appended, as
follows:

- `concorde task merge` commits the log in the merge commit it makes, with the closing its close
  then appends.
- When the primary branch does not already hold the log so, a close commits the log in a commit of
  that file alone.

The copy in Git is what outlives [Tracing](../../kernel/tracing/module.md)'s retention. The task's
folder keeps its own log, which the copy never replaces.

### req.tasks.log-commit-alone — Committing a log commits nothing else

A close that commits a decision log SHALL act as follows:

- It leaves every other change of the primary worktree, staged or not, as it was.
- When Git refuses that commit, it refuses with `decision_log_uncommitted`, commits nothing and
  leaves the task's folder current.

The same close run again commits the log and finishes the close.

### req.tasks.decision-log-untouched — The decision log belongs to the main agent

After creating a decision log, Tasks SHALL NOT change it except by appending these entries:

- A requested escalation.
- A requested report.
- A requested answer.
- The entry recording how the task ended.

The session working on the task writes workflow reports and its own decisions into the log, never
Tasks.

### req.tasks.registered-modules — Records name only registered Modules

Where the spec part is installed, Tasks SHALL refuse to open a task that names a
[Module](../../glossary.json#concept.module) absent from the primary worktree's registry.

Where it is not, the Modules are plain labels that nothing checks. A record's Modules never change
after the open. The Modules a run worked on are in its
[run result](../../glossary.json#concept.run-result).

### req.tasks.no-copies — Tasks keeps no copy of what the workspace records

Tasks SHALL NOT store any of the following in a task's record:

- The task's runs.
- The task's deliveries.
- The task's workflow.

Each time it is needed, what happened in a task's workspace is read where it was recorded, so no
second copy can disagree with it.

### req.tasks.no-foreign-writes — Tasks writes nothing the workspace's runs record

Tasks SHALL NOT write any of the following, apart from the exceptions listed below:

- The [run store](../../glossary.json#concept.run-store).
- A [workflow record](../../glossary.json#concept.workflow-record).
- A [delivery commit](../../glossary.json#concept.delivery-commit).

The exceptions are:

- Holding a task's [workspace lock](../../glossary.json#concept.workspace-lock).
- When the task is closed, moving the task's whole folder, workspace folder included, to the
  history.
- Where the method part is not installed, the delivery commit of `task deliver`.

The lock file lives under `.concorde/locks/workspaces/`. While Tasks merges or closes the task, its
holder is named there. Nothing else in the lock file is written.

## Lifecycle

### req.tasks.primary-only — Tasks open, close, merge and start sessions only from the primary

Outside the primary worktree, the following commands SHALL refuse to run:

- `concorde task open`
- `concorde task close`
- `concorde task merge`
- `concorde task session`
- `concorde task rebind`
- `concorde task answer`

### req.tasks.worktree-ignored — A worktree inside the primary is ignored there

Unless Git ignores its worktree path in the primary worktree, Tasks SHALL refuse to open a task.

### req.tasks.one-worktree — One branch and one worktree per task

Opening a task SHALL create exactly one new branch and one new worktree as follows:

- The new branch is `concorde/<task-id>`.
- The new worktree is checked out on that branch.
- The new worktree is at `.claude/worktrees/<task-id>` of the primary worktree and nowhere else,
  where every worktree workers work in lives.

When any of the following is already taken, opening refuses, so no two tasks ever share a branch or
a worktree:

- The identity.
- The branch.
- The worktree path.

### req.tasks.binding — Every task worktree is a bound workspace

Opening a task SHALL write the task record only after writing the new worktree's
[workspace binding](../../glossary.json#concept.workspace-binding), which names the task identity as
the workspace.

The binding satisfies the
[binding contract](../../kernel/contracts.md#contract.kernel.workspace-binding). The binding names:

- The task folder's `workspace/` as its workspace folder.
- The primary worktree's `.concorde` for its locks.

Tasks never rewrites the binding afterwards. Closing removes the binding with the worktree.

### req.tasks.transitions — Only merging and closing change the stored state

Tasks SHALL store a task's state according to these cases:

- From the open until the task is closed, the state is `open`, except during the undecided merge
  described below.
- After the task is closed, the state is only `closed`, when merged or completed, or `failed`.
- While `concorde task merge` has a merge of the task that its checks have not decided, the state is
  `merging`.

When its merge is undone or aborted, a `merging` task returns to `open`. Only when every check of
its merge passed does the task become `closed`. Exactly while the state is `merging`, the record's
`merging` field is set.

### req.tasks.derived-state — Active and delivered are derived

Each time a task that is not closed or failed is listed or shown, Tasks SHALL derive whether it is
`open`, `active` or `delivered` from these sources:

- Where the execution part is installed, its workspace's runs in its workspace folder.
- Its branch.
- Its worktree.

A `merging` task is shown as `merging`. Otherwise, the task's derived state follows these cases:

- When the branch head is a delivery commit of the task's workspace that verifies and the worktree
  is clean, the task is `delivered`.
- Otherwise, the task is `active` when any of these conditions applies:
  - The workspace has a run.
  - The branch moved past its base commit.
  - The worktree has uncommitted changes.
- Otherwise, the task is `open`.

As for Delivery, a new path Git cannot version is no uncommitted change. One example is a path a
sandbox hides behind a `/dev/null` mount.

### req.tasks.delivery-verified — Only a delivery commit that verifies counts

Tasks SHALL count a task as delivered, and merge it or close it as merged, only under this
condition:

- Its branch head is a [delivery commit](../../glossary.json#concept.delivery-commit) of its
  workspace that verifies by the Kernel's [convention](../../kernel/contracts.md#delivery-commit):
  it has exactly one parent, whichever part made it.

When a head does not verify, these results apply:

- The head is shown `active`.
- `task show` lists the mismatch with that delivery.
- `merge` and `close --merged` refuse the head with `delivery_unverified`, naming the mismatch.

[scenario.tasks.delivery-unverified](scenarios.md#scenario.tasks.delivery-unverified) shows these
results.

### req.tasks.failure-explained — A failed task says why

Closing a task as failed SHALL record a reason and either the
[error chains](../../glossary.json#concept.error-chain) that caused the failure, unchanged, or an
explicit declaration that no error caused it.

### req.tasks.closed-inert — A closed task stays closed

Tasks SHALL keep a closed or failed task in that state whatever its workspace records afterwards.

Closing removes the worktree and with it the workspace binding. Closing also moves the task's
folder, whose workspace folder the binding named, to the history, so no run of the task's workspace
can start. One task does one thing at a time by the Kernel's
[workspace lock](../../glossary.json#concept.workspace-lock), not by the record.

### req.tasks.close-when-ended — A task moves to the history only once it has ended

Tasks SHALL move a closed task's folder to the history only under these conditions:

- Tasks holds the task's workspace lock and its workflow lock.
- For a close without a merge, Tasks first stopped every task session of the task.
- For a close without a merge, Tasks first stopped every run of the workspace still running or
  waiting for its lock.
- Tasks first removed the worktree with its binding.

Still holding both locks, the close then removes the workspace lock file and the workflow lock file.

A run of the task therefore never writes into a folder that has moved:

- While the close holds the lock, no run runs.
- A run waiting for the lock writes only in the execution part's lobby.
- Once the waiting run takes the removed lock file or finds the binding gone, the run is refused
  with `workspace_retired`.
- After the close, no run starts, since its binding is gone or names a folder that no longer exists.

Nor does a workflow step of the workspace write into a folder that has moved. A step holding the
workflow lock finishes its writes before the folder moves. A step waiting for the workflow lock is
refused with `workspace_retired` in the same way.

### req.tasks.workflow-lock-last — A close takes the workflow lock last

In `close` and the close that ends `merge`, Tasks SHALL take a task's workflow lock only while
holding its workspace lock and the merge lock already, and wait as long as it takes.

A [workflow step](../../glossary.json#concept.workflow-step) holds that lock only for writes that
wait for no other lock, so the wait is short. For that reason, no two processes ever wait for each
other's locks.

### req.tasks.history-unique — No closed task replaces another

Tasks SHALL move a closed task's folder to a history folder that no other task used, under a
history key for which the primary worktree holds no decision log `.concorde/decisions/<key>.md`.

### req.tasks.closed-no-session — A closed task gets no task session

For a closed or failed task, Tasks SHALL refuse with `task_closed` to start or record a
[task session](../../glossary.json#concept.task-session).

Recording a session checks the task's state again inside the record update that writes the session's
node. Thus, a close stored after the start's own check still refuses the recording.

### req.tasks.merge-verified — Merged means contained in the primary branch

Closing a task as merged SHALL succeed only when all these conditions hold:

- The task branch holds a delivery commit of the task's workspace since its base.
- The latest delivery commit is the head of the branch and verifies.
- That head is contained in the primary branch.
- The worktree has no uncommitted change.

### req.tasks.no-silent-discard — Uncommitted work is never discarded silently

Unless the task is closed without a merge, as completed or failed, with `--force`, closing a task
SHALL NOT remove a worktree that has uncommitted changes.

### req.tasks.shared-config-kept — Ending a task leaves the shared Git configuration

Closing or merging a task SHALL NOT change the repository's configuration that every worktree
shares, `.git/config` of the primary worktree.

The task's worktree is removed with its submodules' checkouts and their repositories. The submodules
stay registered for the primary worktree and every other task worktree.

### req.tasks.refusal-inert — A refusal changes nothing

A refused task command or record update SHALL leave every record, branch and worktree unchanged.

The exceptions are refusals that say so themselves:

- With `binding_failed`, `concorde task open` leaves the worktree and branch it had added. The
  refusal names them and how to remove them.
- With `record_unwritable`, `concorde task open` removes the worktree, branch and task folder it had
  added before refusing. The refusal names any of them it could not remove and how to remove them.
- The three `concorde task merge` refusals are:
  - With `rollback_failed`, Git would not restore the primary branch, and the task stays `merging`.
  - With `check_failed` whose checks created paths, the reset leaves those paths in the primary
    worktree, and the refusal names them.
  - When a close fails after the merge and its checks succeeded, the refusal leaves the checked
    merge in place and the task `merging`.

When `concorde task merge` refuses after its [Issue recovery](#req.tasks.merge-clean-primary), it
leaves the Issue records that recovery put back as recovery put them back. That recovery changes
nothing any Issue read shows.

`concorde task close` and `concorde task escalate` are not atomic either. Each changes the following
in steps that cannot be one transaction:

- Git.
- The task record.
- The decision log.

After a step, their refusals leave that step done and say so:

- A close's `worktree_failed` leaves the worktree as `git worktree remove` left it. The refusal says
  so.
- After removing the worktree, a close refused while writing the record (`record_conflict`,
  `record_unwritable`) leaves the task in its state without its worktree. The refusal says so.
- A close's `decision_log_failed` leaves the task closed or failed in its record without its closing
  in the decision log.
- A `record_unwritable` of a close's [trace node](../../glossary.json#concept.trace-node) leaves the
  task closed or failed in its record with its closing logged and its trace node not ended.
- A close's `decision_log_uncommitted` leaves the task closed or failed in its record, with its
  closing in the decision log. Its folder stays current, since the log is not yet in Git.
- An escalation's `decision_log_failed` leaves the escalation in the task's trace and not in the
  decision log. The refusal gives the following:
  - The escalation's number.
  - The rendered chain.
  - A statement that escalating again would record it twice.
  - A request for the chain to be appended by hand.

Each refusal of a close says which rerun finishes the close once the cause is fixed:

- Running the same close again.
- For a close run by a merge whose task stays `merging`, `concorde task merge <task-id>
--resume`.
- For a close whose record the merge's close already stored closed, `concorde task close
<task-id> --merged`.

The rerun skips a worktree that is gone. For a task already closed with that outcome, the same close
does the following and changes nothing else:

- Appends the closing its decision log lacks.
- Ends the trace node that has not ended.
- Commits the log the primary branch lacks.

### req.tasks.close-ends-merge-attempt — A close that finishes a merge ends its attempt

A `concorde task close <task-id> --merged` SHALL end the task's latest merge attempt node that still
says it runs, with the following status and outcome:

- When its merge commit was made, `ok` with the merge's outcome, `merged` or `contained`.
- Otherwise, `failed` with the outcome `interrupted`.

The close holds the merge lock, so no merge of the task still runs. For an attempt whose own close
failed after its merge commit, `close --merged` finishes that close. The attempt would otherwise
stay `running` in the task's history for ever. A write of that node the operating system refuses is
a warning of the close.

## Merging

### req.tasks.merge-exact-commit — A merge merges the commit it checked

Even when the primary branch could fast-forward, `concorde task merge` SHALL merge the task branch's
head that its checks before the merge accepted, in a merge commit with these properties:

- The merge uses the head's commit identity, never the branch by name.
- The merge commit's second parent is that head.
- The merge commit's trailer `Concorde-Task` names the task.
- The merge commit adds the task's decision log.

A commit added to the task branch after those checks is therefore never merged unchecked. Closing
the task as merged then refuses with `not_merged`, since the branch's head is no longer its latest
delivery commit.

When the primary branch already contains the checked head, as after a merge made by hand, there is
nothing to merge. No merge commit is made. The merge does the following:

- Runs its checks on the primary branch's head as it is.
- Records that head as its `after`.
- Answers `contained` true.
- Ends its attempt's node with the outcome `contained`.
- Closes the task as merged, which commits the decision log alone.

### req.tasks.merge-workspace-locked — No run of a task changes it while it is merged or closed

`concorde task merge` and `concorde task close` SHALL hold the task's
[workspace lock](../../glossary.json#concept.workspace-lock), wait up to `--wait` seconds and refuse
with `workspace_busy` under these terms:

- The commands take the workspace lock before the merge lock and hold it to the end.
- The commands wait for the workspace lock inside the command.
- When a run still holds the workspace lock after that wait, the commands refuse, naming the lock's
  holder and changing nothing.

Neither holds the merge lock while it waits for the workspace lock.

### req.tasks.merge-serialized — One merge into the primary at a time

Tasks SHALL hold the [merge lock](../../glossary.json#concept.merge-lock) of the primary worktree
for the whole of every command listed below, so none overlap or see a merge that may still be rolled
back:

- `concorde task merge`.
- `open`.
- `close`.

### req.tasks.merge-lock-released — The lock ends with its process

When the process holding the merge lock ends in any of these ways, the merge lock SHALL be released
without any action by another session:

- The process finishes.
- The process fails.
- The process is killed.

### req.tasks.merge-busy-named — A waiter learns who holds the lock

When a merge, open or close gives up waiting, it SHALL name the following about the holder:

- The holder's command.
- The holder's task.
- The holder's process.
- The holder's start time.
- When the holder's environment names one, the Claude Code session the holder works for.

### req.tasks.merge-handed-locks — A merge may be handed its locks

When a merge starts with the following locks already held on inherited descriptors and named in its
environment, the merge SHALL hold them from its start without waiting until it ends:

- The task's merge attempt lock.
- The workspace lock.
- The merge lock.

### req.tasks.merge-attempt-lock — A merge's end is its attempt lock's release

`concorde task merge` SHALL hold the task's merge attempt lock from before it waits for its other
locks until it has written its whole answer, and remove it then.

The close that ends a merge removes the task's workspace lock before the merge closes the task's
Issues and writes its answer. Thus, the workspace lock's release never says that the merge ended. A
merge that dies leaves a file nobody holds, which is free. When another merge holds a task's attempt
lock, a merge of that task waits for it as for its other locks, within the same `--wait`. The
waiting merge then refuses with `merge_busy`.

### req.tasks.merge-output-kept — A merge keeps the server's output with its attempt

When its environment names the task's next attempt folder made for it in `CONCORDE_MERGE_ATTEMPT`, a
merge SHALL record its attempt's node there, also when refused before it began.

The [project MCP server](../../glossary.json#concept.project-mcp-server) makes that folder. The
server directs the merge's standard output and error to its `output.json` and `messages.log`. This
keeps the merge's whole answer and its messages with its attempt's node. They move with the task to
the [history](../../glossary.json#concept.history), where the merge finishes writing them
([Tracing](../../kernel/tracing/module.md)). An attempt refused before it began records the primary
worktree's branch and commit as it found them.

### req.tasks.wait-without-polling — A wait is woken, never polls

`concorde task wait` SHALL return under any condition below, learning of each change from the
operating system and blocking on the lock itself rather than reading the records repeatedly:

- The task reaches one of the named states.
- The task's record names a main agent's session other than the one named.
- The run's runner holds no [run lock](../../glossary.json#concept.run-lock).
- Nobody holds the lock.
- No merge of the task holds its merge attempt lock.

When any condition is already true, it answers at once.

### req.tasks.wait-bounded — A wait says why it ended without its answer

Without changing anything, a wait SHALL end with the applicable result below:

- When the task ended in a state the wait does not name, or ended at all while the wait waits for a
  rebind, the result is `wait_unreachable`.
- The result is `wait_timeout` when its `--timeout` passes first.

A task wait admits only these states:

- `delivered`
- `closed`
- `failed`

A task reaches these states while its workspace lock is held and keeps them once the lock is
released. A task wait refuses `merging` with `invalid_input`. The refusal explains that a merge
holds the lock for as long as the task is `merging`, so no wait sees that state. The refusal names
`--merge`, which waits for the merge itself.

### req.tasks.merge-all-or-nothing — A merge is checked or undone

A `concorde task merge` that ran `git merge` SHALL end with one of these outcomes:

- The primary branch is at the merge commit, all its checks passed and the task is closed as merged.
- The primary branch is at the commit it started from, with the task delivered again.
- Otherwise, the task is left `merging`.

The merge leaves the task `merging` only when it cannot reach either end itself for one of these
reasons:

- Its process was interrupted.
- Git refused the reset.
- The close failed.

Then `--resume` or `--abort` brings the merge to one of the two ends.

A merge refused before `git merge` is governed by
[req.tasks.merge-clean-primary](#req.tasks.merge-clean-primary) and
[req.tasks.refusal-inert](#req.tasks.refusal-inert).

### req.tasks.merge-update-validated — An unvalidated update is validated by every merge

While the primary worktree holds the mark of a `concorde update` not validated since, and where the
spec part is installed, `concorde task merge` SHALL validate the merged result as follows:

- The merge runs `concorde spec-validation` after the `--check` commands it was given, unless they
  include it.

[Distribution](../../distribution/module.md) promises that nothing merges before an update is
validated. Otherwise, the checks a merge is given replace the default, so they could leave that
validation out. A merge that validates clears the mark as any passing validation does. Thus, the
merge of a task that repairs what the update found still lifts the barrier.

### req.tasks.merge-default-check — A merge without checks runs the Spec validation where it can

`concorde task merge`, given no `--check`, SHALL handle checks on the merged result as follows:

- Where the spec part is installed, the merge runs `concorde spec-validation`.
- Otherwise, the merge runs no check and says so in its answer.

### req.tasks.merging-recorded — A merge is recorded before it touches the primary branch

`concorde task merge` SHALL store the task as `merging` with these details before it runs
`git merge`, and record the merge commit once it has made it:

- The primary branch's name and commit before the merge.
- The checked commit.
- The history key the task will close under.
- The checks the merge will run.

### req.tasks.merge-incomplete-refused — Nothing builds on an unchecked merge

While a task is stored as `merging` and no live process holds the merge lock, these commands SHALL
refuse for every task, changing nothing, with the result and details below:

- `concorde task open`
- `merge`
- `close`
- `session`
- `escalate`

The refusal uses `merge_incomplete` and names:

- The merging task.
- The commit before its merge.
- Its merge commit.
- The primary branch's head.
- The `--resume` and `--abort` recovery.

The exceptions are `merge --resume` and `merge --abort` of the merging task itself. These commands
are never refused:

- `list` and `show`, which read.
- `rebind`
- `report`
- `answer`

The latter three change no Git state. While the merge's process still holds the lock, these commands
wait for it as for any holder:

- `open`
- `merge`
- `close`

While that process still holds the lock, a `session` or `escalate` of the merging task refuses with
`merge_busy`.

### req.tasks.merge-recovery — An interrupted merge is resumed or aborted

Only on the main agent's request, Tasks SHALL finish an interrupted merge through these recovery
commands:

- When the primary branch's head is still the interrupted merge's commit, `concorde task merge
<task-id> --resume` reruns the checks that merge recorded. It then closes the task as merged or
  undoes the merge exactly as an uninterrupted merge does. Otherwise, it refuses with
  `not_resumable`.
- `concorde task merge <task-id> --abort` resets the primary branch to the commit before the merge
  when its head is the merge commit. Either way, the command returns the task to delivered.

Under either of these conditions, both commands refuse with `merge_diverged`, touching nothing:

- The primary worktree is on another branch.
- Its head is neither the commit before the merge nor the merge commit.

When a Git merge in progress there is not the task's, `--abort` also refuses with the same error,
touching nothing. Before aborting anything, the command checks for either difference:

- The Git merge merges another commit than the checked one.
- The Git merge merges into another head than the commit before the merge.

Both commands refuse with `not_merging` for a task that is not `merging`.

### req.tasks.empty-log-warned — A merge warns of an unwritten decision log

Under either condition below, `concorde task merge` SHALL list the task's decision log with its path
in its output's `warnings`, without refusing or undoing the merge for it:

- The log is missing.
- The log holds nothing beyond the heading and goal that `open` wrote.

Tasks cannot tell whether a task needed any decision, so an empty log is a reminder to whoever
merges, not a failure. The [main agent](../../glossary.json#concept.main-agent) appends what it
decided alone before it reports the task.

### req.tasks.resolves-open-issues — A task resolves only open Issues

Tasks SHALL record in a task's `resolves` only open [Issues](../../glossary.json#concept.issue) of
the project, named at `open` or with `resolve` while the task has not ended.

Where the issues part is not installed, `--resolves` and `resolve` are refused with `part_missing`,
naming the part, and a task resolves nothing.

### req.tasks.merge-closes-resolved — A merge closes the Issues its task resolves

Once its checks pass and while it holds the merge lock, `concorde task merge` SHALL act on the
task's Issues as follows:

- The merge closes as `resolved`, with the merge commit as evidence, each Issue of the task's
  `resolves` that is still open.
- The merge reports each Issue it could not close as a warning, never as a refusal of the merge.

A failure of the Issues, whatever it is, never keeps the merge from ending the task's sessions and
printing its result.

The fix is on the primary branch only once the merge stands, so an Issue closes with its merge and
never earlier. A task that ends without merging closes none. Where the issues part is not installed,
no task resolves an Issue and a merge closes none.

### req.tasks.merge-own-sources — A merge runs the Concorde it started with

Even when the merge changes Concorde's code in the primary worktree, `concorde task merge` SHALL run
every step after the merge that it runs in its own process on the Concorde code its process started
with.

These steps include closing the task and its sessions.

A merge of a task that changed Concorde itself changes the files of the running Concorde under its
own process. A module it first needs after the merge would otherwise be the merged version, mixed
with the modules it loaded before. Its checks are processes of their own and run the merged code. So
does the Issues bookkeeping command that closes the task's Issues. Coordination reaches that command
only as a process of the primary worktree's `concorde`, since the parts are independent.

### req.tasks.merge-clean-primary — A merge starts from a clean primary

Before merging, `concorde task merge` SHALL refuse either of these:

- A primary worktree with a detached `HEAD` or any uncommitted or untracked path.
- A task that `close --merged` would refuse for any reason other than containment.

A new path Git cannot version is no untracked path here, by the same rule as a task worktree's
changes. An example is a sandbox's `/dev/null` mount of `.bashrc`. Since the paths may be a task's
and not the developer's, the refusal says both of these:

- A task changes nothing outside its worktree.
- A merge starts from a clean primary worktree.

Where the issues part is installed, the merge uses the Issues' own recovery before it judges the
primary worktree, holding the merge lock. The merge puts back what Issue writes published there and
never committed, as the next Issue write would. The refusal names what that recovery could not put
back or left as no Issue write's.

### req.tasks.merge-nothing-outside — A merge refuses what changed outside every task's reach

Before merging, `concorde task merge` SHALL act on an uncommitted or untracked path outside the
task's own worktree as follows:

- In the worktree of a task that has ended, it refuses the path, naming each such worktree with its
  task and its paths.
- In the worktree of another task that has delivered and waits, it warns without refusing.

A task changes nothing outside its own worktree. Its session's shell is held to that by its guidance
alone ([req.task-session.no-sandbox](../task-session/requirements.md#req.task-session.no-sandbox)),
so the merge audits it as far as the filesystem allows. The filesystem records nothing about who
wrote a change. No task will validate or deliver what is in the worktree of a task that ended, so
the merge refuses that content. A change in the worktree of a task that delivered and waits may be
that task's own session's. The merge therefore warns, since refusing would block a task that has
nothing to do with the change. The merge does not judge the worktree of a task still working: its
own session changes it. What is written there becomes that task's content, which its own delivery
and merge judge, refusing an uncommitted change as `dirty_worktree`. Worktrees of no task are not
the project's to judge. The audit judges working trees and not commits, since the primary branch
legitimately moves while a task runs.

### req.tasks.refusal-detail — A refusal is an error link

Every refusal of a `concorde task` command SHALL print an error link naming what was refused, with
whichever details below are concerned, and why Tasks cannot handle it:

- The task.
- The Module.
- The path.
- The run.
- The Git output.

### req.tasks.escalation-kept — Escalations keep their whole chain

An escalation SHALL record the escalating session's link in the task's trace node and the decision
log with causes as follows:

- When the escalation names errors, the link's causes are the escalated errors unchanged.
- When the escalation names no error, the escalation records that link alone, with no causes.

## Delivering without Method

### req.tasks.deliver-without-method — Tasks delivers only where Method does not

Wherever the method part is installed, `concorde task deliver` SHALL refuse with
`delivery_by_method`, naming `concorde delivery`.

Method's `delivery` validates the whole workspace before it commits. Where that validation was
available, skipping it would let a task be merged that Method would have refused.

### req.tasks.deliver-checked — A delivery follows its checks

`concorde task deliver` SHALL make a [delivery commit](../../glossary.json#concept.delivery-commit)
only after every `--check` command it was given passed in the task's worktree.

At the first check that fails, the command refuses with `check_failed`, commits nothing and names:

- The check.
- Its exit status.
- Its log.

The command runs only in the task's own worktree, holding the task's
[workspace lock](../../glossary.json#concept.workspace-lock). The command judges nothing but its
checks.

### req.tasks.deliver-convention — The delivery commit follows the Kernel's convention

`concorde task deliver` SHALL handle delivery according to these cases:

- With a clean worktree, when the head already is a delivery commit of the workspace that verifies,
  the command reports that head as delivered without committing.
- Otherwise, the command commits every change of the task's worktree that Git does not ignore as one
  commit with these properties:

  - The subject is `concorde: deliver <task-id>`.
  - The body is the task's goal.
  - The only parent is the task branch's head.

The commit follows the Kernel's [convention](../../kernel/contracts.md#delivery-commit), so Tasks
derives `delivered` from it as from any delivery commit.

## Reports and the main agent's session

### req.tasks.main-named — The record names the main agent's session to report to

Tasks SHALL keep each task record's information about the
[main agent](../../glossary.json#concept.main-agent)'s sessions as follows:

- The record names the main agent's session its task sessions report to.
- Only recording a task session started with `--main` or `concorde task rebind` changes the session
  the record names for reports.
- The record keeps every session named for the task before, in order.

A Claude Code session's name does not survive a restart or resume of the session. For that reason,
the name a task session was started with may no longer reach anyone. The record holds the name that
does. Once its own name changed, the main agent changes the name in the record.

### req.tasks.report-recorded — A report is recorded before it is sent

Before printing the session to message, `concorde task report` SHALL append these to the task record
and decision log:

- The task session's report.
- The escalations the report carries.
- The main agent's session the record names at that moment, which the command prints as the one to
  message.

The message is then only the wake-up: a message that reaches nobody loses nothing, since
`concorde task show` lists every report.

### req.tasks.report-answered — An answer marks a report answered, once

`concorde task answer` SHALL handle each named report of the task record as follows:

- When the report has an answer, the command refuses with `already_answered` and never replaces the
  answer.
- Otherwise, the command records the main agent's answer on the report and appends the answer to the
  decision log.

A report without an answer is unanswered. A main agent that lost its messages reads unanswered
reports first.

### req.tasks.end-settles-reports — A task's end answers its unanswered reports

When `concorde task merge` or `concorde task close` ends a task, Tasks SHALL answer every still
unanswered report of its record as follows:

- Tasks records the answer in the write that ends the task.
- That merge or close answers the report, not the main agent.
- The answer says how the task ended.
- The closing entry of the decision log names that answer with those reports.

Once its task ends, nobody may answer a report. For that reason, a report left unanswered then would
look pending forever to a main agent reading the task after a restart.

### req.tasks.list-filters-combine — Listing filters combine

`concorde task list` SHALL list only the tasks that satisfy every filter it is given: a derived
state among those `--state` names, and the main agent's session `--main` names.

A main agent whose session name changed lists with both the tasks it must rebind, those not ended
that still name its former name.

### req.tasks.old-records-read — A record written before its main is read with one

Tasks SHALL read older task records according to these cases:

- A task record of `schema_version` 2 predates the record naming the main agent's sessions and
  holding reports. Tasks reads it as follows:

  - The record names the sessions its task sessions' nodes name.
  - The latest session is its main.
  - The record holds no reports.
- A record of `schema_version` 3 predates an answer saying who gave it. Tasks reads it as holding
  answers the main agent gave.
- A record of `schema_version` 4 or earlier predates a task naming the Issues it resolves. Tasks
  reads it as resolving none.

Tasks open across the change keep working. Their next change writes the current version. Their
trace is unchanged, so a task worktree that still runs an earlier Concorde escalates there as
before.
