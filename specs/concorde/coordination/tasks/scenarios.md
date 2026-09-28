# Tasks scenarios

Concrete situations that show the [requirements](requirements.md) of [Tasks](module.md). Commands,
records and error codes are defined in the [contracts](contracts.md).

## Opening and listing

### scenario.tasks.open — Open a task

- GIVEN a primary worktree whose registry lists `module.issues` and no task named `severity`
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde task open severity --goal "let reports carry a severity" --modules module.issues`
- THEN branch `concorde/severity` exists at the primary worktree's head commit
- AND a worktree checked out on that branch exists at `.claude/worktrees/severity` of the primary worktree
- AND the worktree's `.concorde/workspace.json` binds it as the workspace `severity`, with its real path as root, the branch, the base commit, the goal, `module.issues` and the primary worktree's `.concorde` as records directory, untracked by Git
- AND `.concorde/tasks/severity.json` holds the record in state `open` with that base commit and no runs, deliveries or workflow
- AND `.concorde/tasks/severity.decisions.md` holds the heading and the goal
- AND the command prints the record and the [decision log](../../glossary.json#concept.decision-log)'s absolute path

### scenario.tasks.open-carries-worker-configuration — A new task carries the worker configuration of its base commit

- GIVEN a primary branch whose committed `.concorde/workers.json` chooses a default model
- WHEN the main agent opens a task and then commits another default model on the primary branch
- THEN the task worktree holds the configuration of the task's base commit, with nothing left for Git to report
- AND a change the task commits to its own copy leaves the primary branch's file as it is until the task merges
- AND a task opened after the change carries the new default model

### scenario.tasks.open-taken — Refuse a taken identity

- GIVEN a task `severity` exists in any state, or the branch `concorde/severity` or the worktree path exists
- WHEN the main agent opens a task named `severity`
- THEN the command fails with `task_exists`, `branch_exists` or `path_exists`
- AND no record, branch or worktree is created or changed

### scenario.tasks.open-not-ignored — Refuse a worktree the primary would track

- GIVEN a primary worktree whose `.gitignore` does not ignore `.claude/worktrees/`
- WHEN the main agent opens a task at the default path
- THEN the command fails with `worktree_not_ignored`, naming the path and how to ignore it
- AND no record, branch or worktree is created

### scenario.tasks.open-unknown-module — Refuse an unknown Module

- GIVEN a registry without `module.billing`
- WHEN the main agent opens a task naming `module.billing`
- THEN the command fails with `unknown_module`
- AND nothing is created

### scenario.tasks.not-primary — Refuse to open, close, merge or start sessions from a linked worktree

- GIVEN a shell whose working directory is inside a task worktree
- WHEN `concorde task open`, `concorde task close`, `concorde task merge` or `concorde task session` is run there
- THEN the command fails with `not_primary`
- AND nothing changes

### scenario.tasks.list-show — List and show tasks

- GIVEN an open task `quiet` whose workspace has no run and an open task `severity` whose workspace ran `concorde task-validation`
- WHEN the main agent runs `concorde task list --state active` and `concorde task show severity`
- THEN the list holds exactly the record of `severity`, whose derived state is `active`, while its stored state stays `open`
- AND show prints the record of `severity` with its derived state, the workspace's runs from the [run store](../../glossary.json#concept.run-store) with their kind, name, Modules and status, its [delivery commits](../../glossary.json#concept.delivery-commit), who holds its [workspace lock](../../glossary.json#concept.workspace-lock) (null when nobody does) and the absolute path of its decision log
- AND show of `quiet` prints no runs, no deliveries and no holder

## State and runs

### scenario.tasks.first-run — A run of the task's workspace activates the task

- GIVEN an open task `severity` with no change and no run
- WHEN a run of another workspace and an [unbound run](../../glossary.json#concept.unbound-run) are recorded in the run store
- THEN `severity` is still `open`
- BUT once a run of the workspace `severity` is recorded, running or finished, `concorde task show severity` derives `active` and lists the run
- AND the stored state stays `open`

A commit on the task branch past its base, or an uncommitted change in its worktree, makes the task
`active` the same way.

### scenario.tasks.modules-fixed — A run's extra Modules stay the run's

- GIVEN an open task bound to `module.issues`
- WHEN a run in its worktree names `module.issues` and `module.spec` with `--modules`
- THEN the run's result and its entry in `concorde task show` name both Modules
- BUT the [task record](../../glossary.json#concept.task-record), which nothing below the task level writes, still names only `module.issues`

### scenario.tasks.busy — Show who holds a busy workspace

- GIVEN an open task whose workspace lock a run holds
- WHEN the main agent shows the task
- THEN `busy` names the run holding the lock
- AND a second run started in the task worktree meanwhile is refused by Execution with `workspace_busy`, naming the same holder
- BUT once the holder ends, `busy` is null and the next run starts

### scenario.tasks.interrupted — A run whose runner died shows as lost

- GIVEN a task whose workspace has a run with a [run progress file](../../glossary.json#concept.run-progress-file) and no result, whose runner process no longer exists
- WHEN the main agent shows the task
- THEN the run is listed with the status `lost`
- AND `busy` is null, since the kernel released the dead runner's workspace lock
- AND the task is `active`

### scenario.tasks.concurrent-update — Detect a concurrent change

- GIVEN a record that another process changes between Tasks' read and its write
- WHEN Tasks applies an update
- THEN the write is refused by the [file transaction](../../glossary.json#concept.file-transaction)
- AND Tasks rereads the record and reapplies the update if its preconditions still hold
- BUT after three conflicting attempts the update fails with `record_conflict` and the other process's change stays

### scenario.tasks.delivered-reopened — A change after a delivery makes the task active again

- GIVEN a task whose branch head is its first delivery commit, with a clean worktree
- WHEN the main agent shows it
- THEN it is `delivered`, and its deliveries list that commit with its [evidence bundle](../../glossary.json#concept.evidence-bundle) `.concorde/evidence/<task-id>/1.json`
- AND a later run that changes nothing leaves it `delivered`
- BUT an uncommitted change, or a commit after the delivery commit, makes it `active`
- AND a second delivery commit makes it `delivered` again, with both deliveries listed in order

### scenario.tasks.sandbox-masks — A path a sandbox masks is no change

- GIVEN a task whose branch head is a delivery commit that verifies
- AND a sandbox that hides paths of the task worktree, such as `.bashrc`, behind `/dev/null` mounts, which Git lists as untracked
- WHEN the main agent shows the task inside that sandbox
- THEN it is `delivered`, since a new path Git cannot version is no change of the worktree, as Delivery leaves it out
- BUT a new file beside it makes the task `active`

### scenario.tasks.delivery-unverified — A delivery commit that does not verify is not delivered

- GIVEN a task whose branch head has the subject and trailers of a delivery commit of its workspace
- AND the commit does not add the [evidence bundle](../../glossary.json#concept.evidence-bundle) its `Concorde-Evidence` trailer names, or that bundle's readiness run is not its `Concorde-Readiness` trailer
- WHEN the main agent lists or shows it, merges it, or closes it with `--merged` after merging its branch by hand
- THEN list and show give it as `active`, and show lists that commit among its deliveries with each mismatch
- AND merge and close fail with `delivery_unverified` and the reason `decision`, naming the head, its bundle and each mismatch
- AND the primary branch, the task record and the worktree are unchanged
- AND a later delivery commit that verifies makes the task `delivered` again

## Closing

### scenario.tasks.close-merged — Close a merged task

- GIVEN a delivered task whose latest delivery commit is the head of its branch
- AND the main agent merged that branch into the primary branch
- WHEN the main agent runs `concorde task close <task-id> --merged`
- THEN the worktree is removed
- AND the record's state is `closed` with outcome `merged` and the primary branch's head recorded
- AND the branch, the record and the decision log remain

### scenario.tasks.close-submodules — Close a task whose worktree has submodules

- GIVEN a merged task whose worktree has a checked-out submodule
- WHEN the main agent closes it with `--merged` while the submodule has a local change
- THEN the command fails with `dirty_worktree` and the worktree stays
- BUT once the change is undone, closing removes the worktree and records the task as `closed` with outcome `merged`

### scenario.tasks.close-not-merged — Refuse to close an unmerged task as merged

- GIVEN a task whose branch holds no delivery commit of its workspace, or whose branch moved past its latest delivery commit, or whose delivered head is not contained in the primary branch
- WHEN the main agent closes it with `--merged`
- THEN the command fails with `not_merged`
- AND the worktree and the record are unchanged

### scenario.tasks.close-completed — Close a task that reached its goal without merging

- GIVEN an open task that tried something out, whose worktree has uncommitted changes
- WHEN the main agent closes it with `--completed` and no `--note`
- THEN the command fails with `invalid_input`
- AND with a note but without `--force` it fails with `dirty_worktree` and nothing changes
- BUT with a note and `--force` the worktree is removed, the state is `closed` with outcome `completed` and the note, the branch is kept, and the decision log records the outcome and the note

### scenario.tasks.close-failed — Close a failed task with its reason and error chains

- GIVEN a task whose workspace has an [Operation](../../glossary.json#concept.operation) run that ended with an error the task cannot get past
- WHEN the main agent closes it with `--failed` and a reason but names neither an error source nor `--no-error`, or names both
- THEN the command fails with `invalid_input`
- BUT with the reason and `--run <run-id>` the state is `failed`, the note is the reason and the errors hold the run's [error chain](../../glossary.json#concept.error-chain) unchanged, also appended to the decision log
- AND a task that failed for no error, such as a wrong direction, closes as `failed` with `--no-error` and no errors

### scenario.tasks.close-rerun — Running a close again finishes it

- GIVEN a task whose close removed its worktree and then could not write the record, or wrote the record and then could not append its closing to the decision log
- WHEN the main agent reads the refusal
- THEN it names what the close did and says that running the same close again finishes it
- AND running the same close again closes the task, or appends the missing closing once and leaves the record unchanged
- BUT a close with another outcome of the task already closed fails with `invalid_transition`

### scenario.tasks.closed-inert — A closed task stays closed

- GIVEN a task closed as completed
- WHEN the main agent lists the tasks
- THEN the task's worktree, and with it its [workspace binding](../../glossary.json#concept.workspace-binding), is gone, so no run of its workspace can start there
- AND a run of its workspace recorded anyway leaves the task `closed`
- BUT starting or recording a [task session](../../glossary.json#concept.task-session) for it fails with `task_closed`

### scenario.tasks.round-closed — No round begins in a task closed meanwhile

- GIVEN a pi task session of an open task whose rounds have all ended
- AND the task is closed after the session checked it and before the new round is recorded
- WHEN the round is begun
- THEN the record update reads the record again, finds the task closed and fails with `task_closed`, leaving the session's rounds unchanged
- BUT a round that was running when the task closed still records its outcome

## Merging

### scenario.tasks.merge — Merge a delivered task

- GIVEN a delivered task whose latest delivery commit is the head of its branch and whose worktree is clean
- AND a clean primary worktree on its branch
- WHEN the main agent runs `concorde task merge <task-id>` in the primary worktree
- THEN the task branch is merged into the primary branch
- AND `concorde spec-validation` ran in the primary worktree after the merge and passed, its output in `.concorde/tasks/<task-id>.merge.log`
- AND the task is closed as merged with its worktree removed
- AND the output names the commits before and after the merge, each check with its exit status, and how long the command waited for the lock

### scenario.tasks.merge-empty-log — A merge warns of an unwritten decision log

- GIVEN a delivered task whose decision log holds only the heading and goal `open` wrote
- WHEN the main agent runs `concorde task merge <task-id>` in the primary worktree
- THEN the task is merged and closed as merged
- AND the output's `warnings` names the decision log's path and says that nothing was recorded in it
- BUT a task whose decision log has an entry of its own merges with no warning

### scenario.tasks.merge-checks — Run the named checks instead of the default

- GIVEN a delivered task
- WHEN the main agent runs `concorde task merge <task-id> --check "python3 scripts/concorde.py build" --check "python3 scripts/concorde.py spec-validation"`
- THEN exactly those two commands run, in that order, in the primary worktree after the merge
- AND the default check does not run

### scenario.tasks.merge-waits — A second merge waits for the first

- GIVEN one process holding the [merge lock](../../glossary.json#concept.merge-lock) for task `a`
- WHEN another main session runs `concorde task merge b` and the first process releases the lock within the wait
- THEN the merge of `b` starts only after the release and reports how long it waited
- BUT when the lock stays held for the whole `--wait`, the merge of `b` fails with `merge_busy` naming the holder's command `merge`, task `a`, process and start time, and nothing changes

### scenario.tasks.merge-lock-dies — A dead holder releases the lock

- GIVEN a process that took the merge lock and was killed before finishing
- WHEN a main session runs `concorde task merge`, `open` or `close`
- THEN it takes the lock at once, without waiting for any timeout or any other session

### scenario.tasks.merge-open-close-wait — Opening and closing wait for a merge

- GIVEN a process holding the merge lock
- WHEN a main session runs `concorde task open` or `concorde task close` with the lock held for longer than the wait
- THEN the command fails with `merge_busy` naming the holder
- AND no record, branch or worktree is created or changed

### scenario.tasks.merge-conflict — A conflict is aborted

- GIVEN a delivered task whose branch conflicts with the primary branch
- WHEN the main agent merges it with `concorde task merge`
- THEN the command fails with `merge_conflict` naming the conflicting paths
- AND the primary worktree is clean at the commit it had before, and the task is still delivered with its worktree
- AND the refusal's options say to merge the primary branch into the task branch in the task worktree, validate and deliver again

### scenario.tasks.merge-check-failed — A failed check undoes the merge

- GIVEN a delivered task
- WHEN the main agent merges it with a `--check` that exits with status 1, or with checks that leave an uncommitted path
- THEN the command fails with `check_failed`, naming for a failing check the check, its exit status, the log and the end of its output, and for checks that left paths those paths and the log
- AND the primary branch is back at the commit it had before the merge, clean apart from the paths the checks created, which stay
- AND the task is still delivered with its worktree

### scenario.tasks.merge-refused-early — Refuse a merge that cannot close

- GIVEN a task that is not delivered, or whose branch moved past its latest delivery commit, or whose worktree has uncommitted changes, or a primary worktree with an uncommitted or untracked path or a detached `HEAD`
- WHEN the main agent runs `concorde task merge` for it
- THEN the command fails with `not_merged`, `delivery_unverified`, `dirty_worktree` or `primary_dirty` before merging
- AND the primary branch, the task record and the worktree are unchanged

### scenario.tasks.merge-exact-commit — A merge takes the commit it checked

- GIVEN a delivered task
- AND a commit added to its branch after the merge's checks accepted the branch head
- WHEN `concorde task merge` merges the task
- THEN the primary branch holds the checked delivery commit and not the later commit
- AND closing the task fails with `not_merged`, leaving the task `merging` and saying that `--resume` finishes it once the cause is fixed

### scenario.tasks.merge-waits-for-run — A merge waits for the task's run to end

- GIVEN a delivered task whose [workspace lock](../../glossary.json#concept.workspace-lock) a run that is finishing holds
- WHEN the main agent runs `concorde task merge` for it
- THEN the command waits inside its own process, without holding the merge lock, so other tasks can be merged meanwhile
- AND once the run releases the workspace lock it merges the task, reporting in `waited_seconds` how long it waited

### scenario.tasks.merge-workspace-busy — A running task is neither merged nor closed

- GIVEN a delivered task whose [workspace lock](../../glossary.json#concept.workspace-lock) a run holds
- WHEN the main agent runs `concorde task merge` or `concorde task close --completed` for it and the run outlasts its `--wait`
- THEN the command fails with `workspace_busy`, naming the run holding the lock and how long it waited
- AND the primary branch, the task record and the worktree are unchanged, and the merge lock is free again

### scenario.tasks.merge-interrupted — An interrupted merge stops the commands that would build on it

- GIVEN a `concorde task merge` whose process was killed while its checks ran, leaving the task `merging` and its merge commit at the head of the primary branch
- WHEN any main session runs `concorde task open`, `merge`, `close`, `session` or `escalate`, for that task or another
- THEN the command fails with `merge_incomplete`, naming the task, the commit before the merge, the merge commit and the `--resume` and `--abort` recovery, and changes nothing
- AND `concorde task list` and `concorde task show` still answer, showing the task as `merging` with the commits before and after the merge and the checked commit
- BUT `concorde task session <task-id> --stop` is not refused for it

### scenario.tasks.merge-resume — Resume checks the interrupted merge again

- GIVEN a task left `merging` by an interrupted merge whose merge commit is still the primary branch's head
- WHEN the main agent runs `concorde task merge <task-id> --resume`
- THEN the checks the merge recorded run again on the merge commit
- AND when they pass, the task is closed as merged and the output names the commits before and after
- AND when one fails, the primary branch is reset to the commit before the merge, the task is delivered again and the command fails with `check_failed`
- BUT when the primary branch's head is not the merge commit, the command fails with `not_resumable` and changes nothing; `--check` with `--resume` fails with `invalid_input`, and `--resume` of a task that is not merging fails with `not_merging`

### scenario.tasks.merge-abort — Abort undoes the interrupted merge

- GIVEN a task left `merging` by an interrupted merge
- WHEN the main agent runs `concorde task merge <task-id> --abort`
- THEN the primary branch is back at the commit before the merge, the task is delivered again, and the output names that commit and the merge commit it undid
- AND the task can be merged again, and no command is refused any more
- BUT when the primary branch has moved on past the merge commit, the command fails with `merge_diverged`, naming the commits, and changes nothing

### scenario.tasks.merge-live-busy — A merge still running is busy, not incomplete

- GIVEN a `concorde task merge` of task `a` that is still running and holds the merge lock, with `a` stored as `merging`
- WHEN another main session runs `concorde task open`, or `session` or `escalate` for task `a`
- THEN the command fails with `merge_busy` naming the holder, never with `merge_incomplete`
- BUT a `session` or `escalate` for another task is not refused for the merge

## Escalation

### scenario.tasks.escalate — The main agent adds its link when it escalates

- GIVEN a task whose workspace has an Operation run that ended with an error the main agent cannot decide
- WHEN the main agent runs `concorde task escalate` naming that run with its own code, detail, reason and options
- THEN the printed chain's top link has the level `main-agent` and the run's error, unchanged, as its cause
- AND the chain is appended to the task record's escalations and to the decision log, rendered and as JSON
- BUT an escalation naming a run of another workspace or an unbound run is refused with `unknown_run`, and one naming a run that ended without an error with `nothing_to_escalate`, and neither records anything

### scenario.tasks.escalate-decision — A decision without an error is escalated as a link alone

- GIVEN a task whose no-ask workflow ended `ok` after a worker took a decision of major impact
- WHEN the task session runs `concorde task escalate --by task-session` naming no run, no file and no earlier escalation, with its code, detail, reason `decision`, options and recommendation
- THEN the recorded chain is the task session's link alone, with no causes
- AND it is appended to the task record's escalations and to the decision log like any escalation

### scenario.tasks.session-escalates — A task session escalates to the main agent

- GIVEN a task whose task session met an error it may not decide
- WHEN the task session runs `concorde task escalate --by task-session` naming the failed run
- THEN the recorded link has the level `task-session` and the run's error as its cause
- AND the decision log names the main agent as the receiver
- AND when the main agent then escalates with `--escalation 1`, its `main-agent` link has the task session's link, unchanged, as its cause

### scenario.tasks.escalate-log-failed — An escalation the decision log refused is recorded once

- GIVEN a task whose decision log cannot be appended to
- WHEN the main agent escalates
- THEN the command fails with `decision_log_failed`, naming the escalation's number and carrying the rendered chain
- AND the record holds the escalation once, and the refusal says that escalating again would record it twice

