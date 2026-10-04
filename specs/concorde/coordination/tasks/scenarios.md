# Tasks scenarios

Concrete situations that show the [requirements](requirements.md) of [Tasks](module.md). Commands,
records and error codes are defined in the [contracts](contracts.md).

## Opening and listing

### scenario.tasks.open — Open a task

- GIVEN a primary worktree whose registry lists `module.issues` and no task named `severity`
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde task open severity --goal "let reports carry a severity" --modules module.issues`
- THEN branch `concorde/severity` exists at the primary worktree's head commit
- AND a worktree checked out on that branch exists at `.claude/worktrees/severity` of the primary worktree
- AND the worktree's `.concorde/workspace.json` binds it as the workspace `severity`, with its real path as root, the branch, the base commit, the goal, `module.issues`, the workspace folder `.concorde/tasks/severity/workspace/` and the primary worktree's `.concorde`, untracked by Git
- AND `.concorde/tasks/severity/task.json` holds the record in state `open` with that base commit and no runs, deliveries or workflow
- AND `.concorde/tasks/severity/trace.json` is the task's [trace node](../../glossary.json#concept.trace-node), `running`, whose transitions begin with `open`
- AND `.concorde/tasks/severity/decisions.md` holds the heading and the goal
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
- WHEN `concorde task open`, `concorde task close`, `concorde task merge`, `concorde task session`, `concorde task rebind` or `concorde task answer` is run there
- THEN the command fails with `not_primary`
- AND nothing changes

### scenario.tasks.list-show — List and show tasks

- GIVEN an open task `quiet` whose workspace has no run and an open task `severity` whose workspace ran `concorde task-validation`
- WHEN the main agent runs `concorde task list --state active` and `concorde task show severity`
- THEN the list holds exactly the record of `severity`, whose derived state is `active`, while its stored state stays `open`
- AND show prints the record of `severity` with its derived state, its main agent's sessions and its reports, the workspace's runs from its workspace folder with their kind, name, Modules and status, its [delivery commits](../../glossary.json#concept.delivery-commit), its sessions, each with the main session it was started for, and its escalations, who holds its [workspace lock](../../glossary.json#concept.workspace-lock) (null when nobody does) and the absolute paths of its decision log and folder
- AND show of `quiet` prints no runs, no deliveries and no holder

## State and runs

### scenario.tasks.first-run — A run of the task's workspace activates the task

- GIVEN an open task `severity` with no change and no run
- WHEN a run of another workspace and an [unbound run](../../glossary.json#concept.unbound-run) are recorded
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
- AND `busy` is null, since the operating system released the dead runner's workspace lock
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
- THEN it is `delivered`, and its deliveries list that commit with no mismatch
- AND a later run that changes nothing leaves it `delivered`
- BUT an uncommitted change, or a commit after the delivery commit, makes it `active`
- AND a second delivery commit makes it `delivered` again, with both deliveries listed in order

### scenario.tasks.sandbox-masks — A path a sandbox masks is no change

- GIVEN a task whose branch head is a delivery commit that verifies
- AND a sandbox that hides paths of the task worktree, such as `.bashrc`, behind `/dev/null` mounts, which Git lists as untracked
- WHEN the main agent shows the task inside that sandbox
- THEN it is `delivered`, since a new path Git cannot version is no change of the worktree, as Delivery leaves it out
- BUT a new file beside it makes the task `active`

### scenario.tasks.merge-sandbox-masks — A path a sandbox masks does not block a merge

- GIVEN a delivered task
- AND a sandbox that hides paths of the primary worktree, such as `.bashrc`, behind `/dev/null` mounts, which Git lists as untracked
- WHEN the main agent merges the task inside that sandbox
- THEN the merge is not refused as `primary_dirty`, since a new path Git cannot version is no change of the primary worktree, and the task is closed as merged

### scenario.tasks.merge-recovers-issue-records — A merge puts back what a killed Issue write left

- GIVEN a delivered task
- AND an Issue record a killed Issue write published and never committed in the primary worktree
- AND an Issue record edited by hand there
- WHEN the main agent merges the task
- THEN the merge puts back the killed write's record, as the next Issue write would, and refuses with `primary_dirty`, naming the edited record and that no Issue write made its change
- AND once the edit is reverted, the merge runs and closes the task as merged

### scenario.tasks.merge-nothing-outside — A merge judges what changed outside the task's worktree

- GIVEN a delivered task `severity`, a task `labels` that has delivered and waits and a task `quiet` that ended and whose worktree outlived it
- AND an uncommitted change in the worktree of `quiet`
- WHEN the main agent merges `severity`
- THEN the merge is refused with `changed_outside` before anything is merged, naming the worktree of `quiet`, the task and the changed paths
- AND once that change is reverted, the merge runs and closes `severity` as merged
- BUT an uncommitted change in the worktree of `labels` only warns, naming the worktree and the paths, since that task's own session may have written it after delivering

### scenario.tasks.delivery-unverified — A delivery commit that does not verify is not delivered

- GIVEN a task whose branch head has the subject of a delivery commit of its workspace
- AND the commit has two parents, as a merge given that subject has
- WHEN the main agent lists or shows it, merges it, or closes it with `--merged` after merging its branch by hand
- THEN list and show give it as `active`, and show lists that commit among its deliveries with the mismatch
- AND merge and close fail with `delivery_unverified` and the reason `decision`, naming the head and the mismatch
- AND the primary branch, the task record and the worktree are unchanged
- AND a later delivery commit that verifies makes the task `delivered` again

## Closing

### scenario.tasks.close-merged — Close a merged task

- GIVEN a delivered task whose latest delivery commit is the head of its branch
- AND the main agent merged that branch into the primary branch
- WHEN the main agent runs `concorde task close <task-id> --merged`
- THEN the worktree is removed
- AND the record's state is `closed` with outcome `merged` and the primary branch's head recorded
- AND the task's whole folder, with the record, the decision log and the trace node ended `ok` with outcome `merged`, is now `.concorde/history/<task-id>/`, and `.concorde/tasks/<task-id>/` no longer exists
- AND the primary branch's head is a commit adding only `.concorde/decisions/<task-id>.md`, the decision log with its closing, with the trailer `Concorde-Task: <task-id>`
- AND the branch remains, and the task's workspace and task locks are gone

### scenario.tasks.close-submodules — Close a task whose worktree has submodules

- GIVEN a merged task whose worktree has a checked-out submodule without local changes
- AND the submodule is registered in the repository's shared configuration
- WHEN the main agent closes it with `--merged`
- THEN the worktree, with the submodule's checkout and the repository Git kept for it, is removed
- AND the repository's shared configuration is unchanged, the submodule still registered
- AND the record's state is `closed` with outcome `merged`

### scenario.tasks.close-submodules-dirty — Refuse to close a task whose submodule has a change

- GIVEN a merged task whose worktree has a checked-out submodule with a local change
- AND the submodule's `ignore` setting is `all` or not set
- WHEN the main agent closes it with `--merged`
- THEN the command fails with `dirty_worktree`
- AND the worktree and the record are unchanged

### scenario.tasks.close-not-merged — Refuse to close an unmerged task as merged

- GIVEN a task whose branch holds no delivery commit of its workspace, or whose branch moved past its latest delivery commit, or whose delivered head is not contained in the primary branch
- WHEN the main agent closes it with `--merged`
- THEN the command fails with `not_merged`
- AND the worktree and the record are unchanged

### scenario.tasks.close-completed — Close a task that reached its goal without merging

- GIVEN an open task that tried something out, whose worktree has uncommitted changes
- WHEN the main agent closes it with `--completed`, a `--note` and `--force`
- THEN the worktree is removed
- AND the state is `closed` with outcome `completed` and the note
- AND the branch is kept, and the decision log records the outcome and the note
- AND the task's folder is in the history

### scenario.tasks.close-commits-log — A close commits the decision log alone

- GIVEN an open task, and a primary worktree with a staged change and an unstaged change of its own
- WHEN the main agent closes the task with `--failed`, a reason and `--no-error`
- THEN the primary branch's head is a new commit, with the subject `concorde: keep the decision log of <task-id>` and the trailer `Concorde-Task: <task-id>`, that adds only `.concorde/decisions/<task-id>.md`, the decision log with its closing
- AND the primary worktree's staged and unstaged changes are still there, uncommitted
- BUT on a detached `HEAD` the close fails with `decision_log_uncommitted`, commits nothing and leaves the task's folder current, and the same close on the branch again commits the log and moves the folder

### scenario.tasks.close-completed-no-note — Refuse to close as completed without a note

- GIVEN an open task
- WHEN the main agent closes it with `--completed` and no `--note`
- THEN the command fails with `invalid_input`
- AND the worktree and the record are unchanged

### scenario.tasks.close-completed-dirty — Refuse to discard uncommitted changes without force

- GIVEN an open task whose worktree has uncommitted changes
- WHEN the main agent closes it with `--completed` and a `--note` but without `--force`
- THEN the command fails with `dirty_worktree`
- AND the worktree, its changes and the record are unchanged

### scenario.tasks.close-failed — Close a failed task with its reason and error chains

- GIVEN a task whose workspace has an [Operation](../../glossary.json#concept.operation) run that ended with an error the task cannot get past
- WHEN the main agent closes it with `--failed`, a reason and `--run <run-id>`
- THEN the state is `failed` and the note is the reason
- AND the errors hold the run's [error chain](../../glossary.json#concept.error-chain) unchanged, also appended to the decision log

### scenario.tasks.close-failed-no-error — Close a task that failed for no error

- GIVEN a task that failed for no error, such as a wrong direction
- WHEN the main agent closes it with `--failed`, a reason and `--no-error`
- THEN the state is `failed`, the note is the reason and the errors are empty

### scenario.tasks.close-failed-invalid — Refuse a failed close without its reason or one error choice

- GIVEN a task whose workspace has an Operation run that ended with an error
- WHEN the main agent closes it with `--failed` but without a reason, or names neither an error source nor `--no-error`, or names both
- THEN the command fails with `invalid_input`
- AND the worktree and the record are unchanged

### scenario.tasks.close-rerun — Running a close again finishes it

- GIVEN a task whose close removed its worktree and then could not write the record, wrote the record and then could not append its closing to the decision log, or appended it and then could not end the task's trace node
- WHEN the main agent reads the refusal
- THEN it names what the close did and says that running the same close again finishes it
- AND running the same close again closes the task, or appends the missing closing once, or ends the trace node, and leaves the record unchanged

### scenario.tasks.close-other-outcome — Refuse to close a closed task again

- GIVEN a task already closed or failed
- WHEN the main agent closes it with another outcome, or with its own outcome once its decision log holds the closing
- THEN the command fails with `invalid_transition`
- AND the record and the decision log are unchanged

### scenario.tasks.closed-inert — A closed task stays closed

- GIVEN a task closed as completed
- WHEN the main agent lists the tasks
- THEN the task's worktree, and with it its [workspace binding](../../glossary.json#concept.workspace-binding), is gone, so no run of its workspace can start there
- AND a run of its workspace recorded anyway leaves the task `closed`
- BUT starting or recording a [task session](../../glossary.json#concept.task-session) for it fails with `task_closed`

## Merging

### scenario.tasks.merge — Merge a delivered task

- GIVEN a delivered task whose latest delivery commit is the head of its branch and whose worktree is clean
- AND a clean primary worktree on its branch
- WHEN the main agent runs `concorde task merge <task-id>` in the primary worktree
- THEN the task branch is merged into the primary branch in a merge commit whose second parent is the delivery commit, even though the primary branch could fast-forward
- AND the merge commit adds the task's decision log as it stood, followed by the closing `## Closed: merged, <time>` with the time the merge began, as `.concorde/decisions/<task-id>.md` and carries the trailer `Concorde-Task: <task-id>`
- AND `concorde spec-validation` ran in the primary worktree after the merge and passed, recorded as the merge attempt's node `merges/1/` of the task with the check's node and its `output.log` below it
- AND the task is closed as merged with its worktree removed, its closing dated with that time
- AND the merge commit is the primary branch's head, its copy of the decision log the same as the log in the history
- AND the output names the commits before and after the merge, each check with its exit status, and how long the command waited for the lock

### scenario.tasks.merge-closes-resolved-issues — A merge closes the Issues its task resolves

- GIVEN open [Issues](../../glossary.json#concept.issue) A, B and C of the project, a task opened with `--resolves A` to which `concorde task resolve` added B and C, and B closed by hand meanwhile
- WHEN the main agent merges the delivered task and its checks pass
- THEN A and C are closed as `resolved` by `main-agent`, with the merge commit and the task as evidence, each in a commit of its own on the primary branch after the merge commit
- AND the merge prints them as `resolved` and names B, with the Issues error chain `closed_issue`, in its warnings
- BUT `open --resolves` or `resolve` naming an Issue that does not exist or is not open is refused with `invalid_issue`

This illustrates [resolving open Issues](requirements.md#req.tasks.resolves-open-issues) and
[closing them with the merge](requirements.md#req.tasks.merge-closes-resolved).

### scenario.tasks.merge-issues-unavailable — A merge whose Issues fail still closes and answers

- GIVEN a delivered task that resolves an open Issue, and a project whose `concorde issues` cannot run to an answer
- WHEN the main agent merges the task and its checks pass
- THEN the task is closed as merged, its sessions are ended and the merge prints its result with no Issue `resolved`
- AND its warnings name the Issue with the error chain `issues_unavailable`, and the Issue stays open for the main agent to close

This illustrates [closing resolved Issues with the merge](requirements.md#req.tasks.merge-closes-resolved).

### scenario.tasks.merge-own-sources — A module first imported after the merge is the one the merge started with

- GIVEN a merge process that has loaded one module of its package and not yet another that imports from it
- WHEN the merge changes both files so that the second needs a name only the new version of the first has
- THEN the second module, imported after the merge, is its source as it was when the merge started, and imports
- AND no bytecode cache is written for it from that source
- BUT a process that did not keep its sources fails that import with `ImportError`, as the merge of a task changing Concorde did before

This illustrates [a merge running the Concorde it started with](requirements.md#req.tasks.merge-own-sources).

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

### scenario.tasks.merge-update-validated — An unvalidated update adds the default check

- GIVEN a delivered task and the primary worktree's mark `.concorde/update.json` of an update not validated since, in a project whose `concorde spec-validation` fails
- WHEN the main agent runs `concorde task merge <task-id>` with one passing `--check`
- THEN the given check runs and then `concorde spec-validation`, recorded among the attempt's checks, which fails, so the merge is undone with `check_failed`, the task is delivered again and the mark stays
- AND once the mark is gone, the same merge runs the given check alone

### scenario.tasks.merge-waits — A second merge waits for the first

- GIVEN one process holding the [merge lock](../../glossary.json#concept.merge-lock) for task `a`
- WHEN another main session runs `concorde task merge b` and the first process releases the lock within the wait
- THEN the merge of `b` starts only after the release and reports how long it waited

### scenario.tasks.merge-busy — A merge refuses a lock held for its whole wait

- GIVEN one process holding the merge lock for task `a`
- WHEN another main session runs `concorde task merge b` and the lock stays held for the whole `--wait`
- THEN the merge of `b` fails with `merge_busy` naming the holder's command `merge`, task `a`, process and start time
- AND the primary branch and the task `b` are unchanged

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
- AND the primary branch is back at the commit it had before the merge, without the decision log the merge commit added, clean apart from the paths the checks created, which stay
- AND the task is still delivered with its worktree
- AND a check stopped after its time limit fails the same way, its log and the refusal keeping what it printed before it was stopped

### scenario.tasks.merge-commit-refused — A refused merge commit is undone

- GIVEN a delivered task, and a commit hook in the primary worktree that rejects every commit
- WHEN the main agent merges it with `concorde task merge`
- THEN the command fails with `git_failed`, naming the decision log's path and the hook's output
- AND the merge was aborted, the log's copy removed, and the primary branch is clean at the commit it had before
- AND the task is still delivered with its worktree, and its merge attempt's node ended `failed`

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

### scenario.tasks.merge-already-contained — A head the primary branch already holds is checked and closed

- GIVEN a delivered task whose delivery commit was merged into the primary branch by hand
- WHEN the main agent merges the task with `concorde task merge`
- THEN no merge commit is made: the checks run on the primary branch's head, which the answer gives as both `before` and `after`, with `contained` true
- AND the task is closed as merged, its attempt's node ending with the outcome `contained`, and its decision log is committed alone on the primary branch

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
- THEN the command fails with `merge_incomplete`, naming the task, the commit before the merge, the merge commit and the `--resume` and `--abort` recovery, and changes nothing, a close stopping none of the task's sessions and runs
- AND `concorde task list` and `concorde task show` still answer, showing the task as `merging` with the commits before and after the merge and the checked commit

### scenario.tasks.merge-resume — Resume checks the interrupted merge again

- GIVEN a task left `merging` by an interrupted merge whose merge commit is still the primary branch's head
- WHEN the main agent runs `concorde task merge <task-id> --resume`
- THEN the checks the merge recorded run again on the merge commit
- AND when they pass, the task is closed as merged and the output names the commits before and after

### scenario.tasks.merge-log-changed — A log changed after the merge commit is committed again

- GIVEN a task left `merging` by an interrupted merge whose merge commit is still the primary branch's head
- AND an entry the main agent appended to its decision log since
- WHEN the main agent runs `concorde task merge <task-id> --resume` and the checks pass
- THEN the task is closed as merged
- AND the primary branch's head is a commit on top of the merge commit, with the subject `concorde: keep the decision log of <task-id>` and the trailer `Concorde-Task: <task-id>`, that changes only `.concorde/decisions/<task-id>.md`, to the log as it ended, with the entry and the closing
- AND the primary worktree is clean

### scenario.tasks.merge-resume-check-failed — A failed check on resume undoes the merge

- GIVEN a task left `merging` by an interrupted merge whose merge commit is still the primary branch's head
- AND a recorded check that now exits with a failure
- WHEN the main agent runs `concorde task merge <task-id> --resume`
- THEN the command fails with `check_failed`
- AND the primary branch is reset to the commit before the merge, clean apart from the paths the checks created, which stay
- AND the task is delivered again

### scenario.tasks.merge-resume-refused — Refuse a resume that cannot check the merge

- GIVEN a task that is not merging, or one left `merging` whose merge commit is not the primary branch's head
- WHEN the main agent runs `concorde task merge <task-id> --resume`, with or without `--check`
- THEN the command fails with `not_merging` for a task that is not merging, with `not_resumable` for a merge commit that is not the head, and with `invalid_input` for `--check` with `--resume`
- AND the primary branch and the task record are unchanged

### scenario.tasks.merge-abort — Abort undoes the interrupted merge

- GIVEN a task left `merging` by an interrupted merge
- WHEN the main agent runs `concorde task merge <task-id> --abort`
- THEN the primary branch is back at the commit before the merge, the task is delivered again, and the output names that commit and the merge commit it undid
- AND the task can be merged again, and no command is refused any more

### scenario.tasks.merge-abort-diverged — Refuse to abort a merge the primary branch moved past

- GIVEN a task left `merging` by an interrupted merge
- AND a commit made on the primary branch on top of the merge commit
- WHEN the main agent runs `concorde task merge <task-id> --abort`
- THEN the command fails with `merge_diverged`, naming the primary branch's head, the commit before the merge and the merge commit
- AND the primary branch and the task, still `merging`, are unchanged
- BUT when the primary branch is back at the commit before the merge with a merge of another commit in progress, made by hand, the command fails with `merge_diverged` naming that commit and leaves that merge in progress

### scenario.tasks.merge-live-busy — A merge still running is busy, not incomplete

- GIVEN a `concorde task merge` of task `a` that is still running and holds the merge lock, with `a` stored as `merging`
- WHEN another main session runs `concorde task open`, or `session` or `escalate` for task `a`
- THEN the command fails with `merge_busy` naming the holder, never with `merge_incomplete`
- BUT a `session` or `escalate` for another task is not refused for the merge

## Delivering without Method

### scenario.tasks.deliver — Deliver a task where the method part is not installed

- GIVEN a project whose own `concorde` does not offer `delivery`, and task `t1` whose worktree holds a change
- WHEN its task session runs `concorde task deliver t1 --check <first> --check <second>` in the task worktree, and both checks pass
- THEN the task branch's head is a new commit holding the change, with the subject `concorde: deliver t1`, the task's goal as body and the earlier head as its only parent, and the worktree is clean
- AND the command prints the record in the derived state `delivered` and each check with its exit status
- AND the task's trace holds the attempt as `deliveries/1/`, of kind `delivery`, `ok` with outcome `delivered` and the commit among its references and metadata, each check a `delivery-check` node below it with its `output.log`
- AND `concorde task merge t1` then merges and closes the task as it does any delivered task

This illustrates [a delivery following its checks](requirements.md#req.tasks.deliver-checked) and
[the Kernel's convention](requirements.md#req.tasks.deliver-convention).

### scenario.tasks.deliver-check-failed — A failed check delivers nothing

- GIVEN a project without the method part and a task whose worktree holds a change
- WHEN `concorde task deliver` runs three checks of which the second exits with status 3
- THEN the command fails with `check_failed`, naming the check, its exit status, the end of its output and its `output.log`
- AND the third check never runs, the branch head is unchanged, the change stays uncommitted and the task stays `active`
- AND the attempt's node ended `failed` with outcome `check_failed`

This illustrates [a delivery following its checks](requirements.md#req.tasks.deliver-checked).

### scenario.tasks.deliver-recovered — A delivered head is reported, not committed again

- GIVEN a project without the method part and a task whose worktree holds no change
- WHEN `concorde task deliver` runs with no check
- THEN it commits a delivery commit all the same, with nothing in it, as the mark of the delivery
- AND run again, it reports that commit with `recovered` true and commits nothing, its node `ok` with outcome `recovered` and the commit as `found_commit`

This illustrates [the Kernel's convention](requirements.md#req.tasks.deliver-convention).

### scenario.tasks.deliver-refused — Deliver only in the task's worktree, without Method

- GIVEN a project whose own `concorde` offers `delivery`
- WHEN a task session runs `concorde task deliver` in its task worktree
- THEN it fails with `delivery_by_method`, naming `concorde delivery`
- AND in a project without the method part it fails with `not_task_worktree` run in the primary worktree, with `workspace_busy` while a run holds the task's workspace lock past `--wait`, and with `wrong_branch` naming the branch when the worktree is on another branch, committing nothing each time
- AND a delivery waiting for the workspace lock while the worktree is switched to another branch fails with `wrong_branch` once it holds the lock, and one waiting while a close retires the task's workspace fails with `task_closed`, taking no lock file again

This illustrates [Tasks delivering only where Method does not](requirements.md#req.tasks.deliver-without-method).

### scenario.tasks.coordination-alone — A project with the kernel and coordination alone

- GIVEN a project whose own `concorde` offers neither `run`, `delivery` nor `issues`, and that has no registry mirror `.concorde/specs.json`
- WHEN the main agent opens a task naming the [Module](../../glossary.json#concept.module) `module.anything`, its session changes the worktree and runs `concorde task deliver`, and the main agent runs `concorde task merge` with no `--check`
- THEN the task opens with that Module as a plain label, shows no run, is `active` and then `delivered`, and the merge closes it as merged without running a check, a warning saying that no check ran because none was given and the spec part is not installed
- AND `open --resolves` and `resolve` fail with `part_missing` naming the issues part, and `wait --run` with `part_missing` naming the execution part, recording nothing
- AND an open naming a Module that is no Module identity, such as `m`, fails with `invalid_input` before any branch or worktree exists
- AND another task closes with `--completed` as in any project

This illustrates [the parts Coordination does without](../module.md#optional-integrations) and
[a task resolving only open Issues](requirements.md#req.tasks.resolves-open-issues).

## Escalation

### scenario.tasks.escalate — The main agent adds its link when it escalates

- GIVEN a task whose workspace has an Operation run that ended with an error the main agent cannot decide
- WHEN the main agent runs `concorde task escalate` naming that run with its own code, detail, reason and options
- THEN the printed chain's top link has the level `main-agent` and the run's error, unchanged, as its cause
- AND the chain is appended to the escalations of the task's trace node, as number 1, and to the decision log, rendered and as JSON

### scenario.tasks.escalate-refused — Refuse to escalate a run that is not the task's or has no error

- GIVEN a task
- WHEN the main agent runs `concorde task escalate` naming a run of another workspace, an unbound run or a run of the task's workspace that ended without an error
- THEN the command fails with `unknown_run` for a run that is not of the task's workspace and with `nothing_to_escalate` for a run without an error
- AND nothing is recorded in the task's trace or the decision log

### scenario.tasks.escalate-decision — A decision without an error is escalated as a link alone

- GIVEN a task whose no-ask workflow ended `ok` after a worker took a decision of major impact
- WHEN the task session runs `concorde task escalate --by task-session` naming no run, no file and no earlier escalation, with its code, detail, reason `decision`, options and recommendation
- THEN the recorded chain is the task session's link alone, with no causes
- AND it is appended to the task's escalations and to the decision log like any escalation

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

## Reports and the main agent's session

### scenario.tasks.report — A report is recorded before the message

- GIVEN a task `severity` whose task session was started with `--main concorde-7d` and has escalated once
- WHEN the task session runs `concorde task report severity --text "<its report>" --escalation 1`
- THEN the task record holds report 1 with its time, `main` `concorde-7d`, the text, escalation 1 and `answer` null, and the decision log holds it under `## Report 1 to the main agent (concorde-7d), <time>`
- AND the command prints the report with `main` `concorde-7d`, the session to message
- AND `concorde task show severity` prints the record with the report among its `reports`
- BUT a report naming an escalation the task does not have is refused with `unknown_escalation`, and a report for a closed task with `task_closed`, recording nothing

### scenario.tasks.rebind — The main agent rebinds its tasks to its new session name

- GIVEN a task `severity` whose record names the main agent's session `concorde-7d`
- WHEN the main agent, whose session is now named `concorde-8e`, runs `concorde task rebind severity --main concorde-8e` in the primary worktree
- THEN the record's `main` is `concorde-8e`, the command prints the former `concorde-7d`, and the record keeps both names in order in `mains`
- AND `concorde task list --main concorde-7d` no longer lists the task, while `--main concorde-8e` does
- AND the task session's next `concorde task report` prints `main` `concorde-8e`
- BUT rebinding a closed task is refused with `task_closed`, and rebinding from a task worktree with `not_primary`

### scenario.tasks.answer — The main agent's answer marks reports answered

- GIVEN a task with two unanswered reports
- WHEN the main agent runs `concorde task answer <task> --report 1 --report 2 --text "<its answer>"`
- THEN both reports hold the answer with its time and `by` `main-agent`, and the decision log holds it under `## Answer to report(s) 1, 2 of the task session, <time>`
- AND answering report 1 again is refused with `already_answered` and a report the task does not have with `unknown_report`, changing nothing

### scenario.tasks.close-settles-reports — Closing a task answers its unanswered reports

- GIVEN a task with an answered report 1 and unanswered reports 2 and 3
- WHEN the main agent closes it with `concorde task close <task> --completed --note "<what it achieved>"`
- THEN reports 2 and 3 hold the answer `by` `close`, dated with the closing, saying that `concorde task close --completed` closed the task with the note, while report 1 keeps the main agent's answer
- AND the decision log's closing entry ends with `The close answered report(s) 2, 3 of the task session, unanswered until then: <the answer>`
- AND a failed close answers them likewise with its reason

### scenario.tasks.merge-settles-reports — Merging a task answers its unanswered reports

- GIVEN a delivered task whose task session's delivery report 1 is unanswered
- WHEN the main agent merges it with `concorde task merge <task>`
- THEN report 1 holds the answer `by` `merge`, dated with the closing, naming the checked delivery commit and the primary branch
- AND the merge commit's copy of the decision log already ends with that answer, so the close commits no further copy
- AND `concorde task answer <task> --report 1` is refused with `task_closed`

### scenario.tasks.list-not-ended — The tasks not ended that name a session are listed

- GIVEN a closed task and an open task whose records both name `concorde-7d`, and an open task naming `concorde-8e`
- WHEN the main agent runs `concorde task list --main concorde-7d --state open,active,delivered,merging`
- THEN only the open task naming `concorde-7d` is listed
- AND `--state` naming a state that does not exist is refused with `invalid_input`

### scenario.tasks.wait-rebound — A task session waits for the main agent to rebind the task

- GIVEN a task whose record names `concorde-7d`, a session that no longer exists
- WHEN the task session runs `concorde task wait <task> --rebound concorde-7d` and the main agent then rebinds the task to `concorde-8e`
- THEN the command returns once the record is written, printing `main` `concorde-8e`
- AND the same wait run again returns at once
- AND a wait on a task that is closed meanwhile ends with `wait_unreachable`

### scenario.tasks.report-merge-incomplete — Reports and rebinds go on while a merge is unfinished

- GIVEN a task stored as `merging` whose merge process died, so `concorde task escalate` is refused with `merge_incomplete`
- WHEN a task session of another task runs `concorde task report` with that refusal and the main agent runs `concorde task rebind` for that task
- THEN both are recorded, since neither touches Git

### scenario.tasks.old-record — A task opened before the main was recorded keeps working

- GIVEN a current task whose record has `schema_version` 2 and no `main`, `mains` or `reports`, with a task session started with `--main concorde-7d`
- WHEN it is shown, reported to and rebound
- THEN it is shown with `main` `concorde-7d`, `mains` from its session and no reports, the report is recorded, and after the rebind the record has the current `schema_version`, 5, and satisfies the record contract
- AND its trace node is unchanged in shape, so an earlier Concorde still writes it
- AND a record of `schema_version` 3 with an answered report is read with that answer `by` `main-agent`

## History

### scenario.tasks.close-stops-runs — A failed task is closed only once its runs stopped

- GIVEN a task whose workspace has a run still running in the background
- WHEN the main agent closes it with `--failed`, a reason and `--no-error`
- THEN the run is stopped with `SIGTERM` and ends with its own result, as a task session of the task would be stopped with `claude stop` ([scenario.task-session.close-stops](../task-session/scenarios.md#scenario.task-session.close-stops))
- AND only then, holding the task's workspace lock, the close moves the task's folder to the history, with the stopped run in its trace

### scenario.tasks.close-retires-waiting-run — A run waiting for the workspace while the task closes

- GIVEN a task whose workspace lock a run holds, and a second run of its workspace started with `--wait 600` in a PID namespace the close cannot see, so the close cannot stop it, waiting for that lock
- WHEN the main agent closes the task with `--failed` and `--wait 600`, and the first run ends
- THEN the close takes the workspace lock, removes the worktree with its binding, moves the task's folder to the history and removes the workspace lock file while still holding it
- AND the waiting run, which wrote only in Execution's lobby, then takes the removed lock file and is refused with `workspace_retired`, its result kept in the lobby and found by its identity
- AND the history holds nothing of the waiting run and is never written afterwards

### scenario.tasks.close-takes-workflow-lock — A close waits for a workflow step's writes

- GIVEN a task whose workflow lock a [workflow step](../../glossary.json#concept.workflow-step) of its workspace holds while it records its step
- WHEN the main agent closes the task with `--completed`
- THEN the close, holding the task's workspace lock and then the merge lock, waits for the workflow lock, and only once the step released it removes the worktree and moves the task's folder to the history, with what the step wrote
- AND it removes the workflow lock file while still holding the lock, so a step that waited for that lock meanwhile is refused with `workspace_retired` and writes nothing

### scenario.tasks.closed-run-refused — A run of a closed task is refused

- GIVEN a closed task whose worktree was left in place by hand with its binding
- WHEN a run is started in that worktree
- THEN it is refused with `binding_invalid`, since the workspace folder its binding names no longer exists, and nothing is written into the history

### scenario.tasks.history-key — A reused name gets its own history folder

- GIVEN a closed task `retry` in the history whose branch was deleted
- WHEN a new task `retry` is opened and closed
- THEN its folder moves to `.concorde/history/retry.2/`, its decision log is committed as `.concorde/decisions/retry.2.md`, and the first task's folder and log are unchanged
- AND after retention removed both history folders, a third task `retry` closes as `retry.3`, since the committed logs still hold `retry` and `retry.2`

## Waiting

### scenario.tasks.wait-task — A task wait returns when the delivery ends

- GIVEN a task whose delivery run holds its workspace lock
- WHEN a session runs `concorde task wait <task> --until delivered` and the run commits its delivery and ends
- THEN the command returns once the lock is released, printing the task and its state `delivered`
- AND the same wait run again returns at once

### scenario.tasks.wait-task-unreachable — A task that ends elsewhere ends the wait

- GIVEN a session waiting for a task to become delivered
- WHEN the task is closed as completed
- THEN the wait ends with `wait_unreachable`, an error link naming the state the task ended in
- AND a wait for a state a task reaches without its workspace lock, such as `active`, is refused with `invalid_input`
- AND so is a wait for `merging`, which lasts only while a merge holds the lock, the refusal naming `--merge`, which waits for the merge itself

### scenario.tasks.wait-lock — A lock wait returns when its holder dies

- GIVEN a process holding the merge lock for task `t9` in Claude Code session `s-1`
- WHEN a session runs `concorde task wait --lock merge` and the holder is killed
- THEN the command returns at once after the kill, saying the lock was released and naming the holder line it waited for, with its session and task

### scenario.tasks.wait-merge — A merge wait returns after the merge, not its workspace lock

- GIVEN a delivered task `t1` whose merge attempt lock a process holds, and whose workspace lock file a close already removed
- WHEN a session runs `concorde task wait t1 --merge` and the holder lets the lock go
- THEN the command returns only then, naming the holder line it waited for, and the lock file is gone
- AND after `concorde task merge t1` merged and closed the task, the same wait answers at once with the attempt's node in the history, `merges/1/`, its status `ok` and outcome `merged`, the node the merge's answer names as its `log`
- BUT `concorde task wait --merge` without a task is refused with `invalid_input`

### scenario.tasks.wait-timeout — A wait that times out says so

- GIVEN a run holding a task's workspace lock
- WHEN a session runs `concorde task wait <task> --lock workspace --timeout 0.3`
- THEN the command fails with `wait_timeout`, reason `environment`, and nothing changed
- AND a wait for a run no reader finds fails with `unknown_run`

