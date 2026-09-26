# Tasks scenarios

Concrete situations that show the [requirements](requirements.md) of [Tasks](module.md). Commands,
records and error codes are defined in the [contracts](contracts.md).

## Opening and listing

### scenario.tasks.open — Open a task

- GIVEN a primary worktree whose registry lists `module.issues` and no task named `severity`
- WHEN the main agent runs `concorde task open severity --goal "let reports carry a severity" --modules module.issues`
- THEN branch `concorde/severity` exists at the primary worktree's head commit
- AND a worktree checked out on that branch exists at `.claude/worktrees/severity` of the primary worktree
- AND `.concorde/tasks/severity.json` holds the record in state `open` with that base commit
- AND `.concorde/tasks/severity.decisions.md` holds the heading and the goal
- AND the command prints the record

### scenario.tasks.open-inherits-worker-models — A new task keeps its own copy of the worker models

- GIVEN a primary worktree whose `.concorde/worker-models.json` chooses a default model
- WHEN the main agent opens a task and then changes the primary worktree's default model
- THEN the task worktree holds the configuration as it was when the task opened, untracked by Git
- AND it changes only through `configure_workers` run with `--task` naming the task
- BUT a task opened from a primary worktree without the file gets none, and its workers use the program's default

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

- GIVEN tasks in several states
- WHEN the main agent runs `concorde task list --state active` and `concorde task show severity`
- THEN the list holds exactly the active tasks' records, oldest first
- AND show prints the record of `severity` with the absolute path of its decision log

## Runs

### scenario.tasks.first-run — The first run activates a task

- GIVEN an open task
- WHEN the Operation host begins a run for it
- THEN the run is appended as `running` with its host process
- AND the task state is `active`

### scenario.tasks.run-adds-modules — A run records extra Modules

- GIVEN an active task bound to `module.issues`
- WHEN the host begins a run naming `module.issues` and `module.spec`
- THEN the record's Modules are `module.issues` and `module.spec`

### scenario.tasks.busy — Refuse a second concurrent run

- GIVEN a task with a running run whose host process is alive
- WHEN the host begins another run for the task
- THEN the update fails with `task_busy`
- AND the record is unchanged

### scenario.tasks.interrupted — Recover from a dead host

- GIVEN a task with a run left `running` by a host process that no longer exists
- WHEN the host begins a new run for the task
- THEN the old run's status becomes `interrupted`
- AND the new run is appended as `running`

### scenario.tasks.concurrent-update — Detect a concurrent change

- GIVEN a record that another process changes between Tasks' read and its write
- WHEN Tasks applies an update
- THEN the write is refused by the file transaction
- AND Tasks rereads the record and reapplies the update if its preconditions still hold
- BUT after three conflicting attempts the update fails with `record_conflict` and the other process's change stays

### scenario.tasks.delivered-reopened — A writing run reopens a delivered task

- GIVEN a delivered task
- WHEN the host begins a run whose Operation may write the worktree
- THEN the task state becomes `active`
- BUT a run that may not write leaves the state `delivered`

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

- GIVEN a task that is not delivered, or whose delivered head is not contained in the primary branch, or whose branch moved past its latest delivery commit
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

- GIVEN a task whose Operation run ended with an error the task cannot get past
- WHEN the main agent closes it with `--failed` and a reason but names neither an error source nor `--no-error`, or names both
- THEN the command fails with `invalid_input`
- BUT with the reason and `--run <run-id>` the state is `failed`, the note is the reason and the errors hold the run's error chain unchanged, also appended to the decision log
- AND a task that failed for no error, such as a wrong direction, closes as `failed` with `--no-error` and no errors

### scenario.tasks.closed-inert — A closed task accepts no run

- GIVEN a closed or failed task
- WHEN the host begins a run for it
- THEN the update fails with `task_closed`

## Merging

### scenario.tasks.merge — Merge a delivered task

- GIVEN a delivered task whose latest delivery commit is the head of its branch and whose worktree is clean
- AND a clean primary worktree on its branch
- WHEN the main agent runs `concorde task merge <task-id>` in the primary worktree
- THEN the task branch is merged into the primary branch
- AND `concorde validate` ran in the primary worktree after the merge and passed, its output in `.concorde/tasks/<task-id>.merge.log`
- AND the task is closed as merged with its worktree removed
- AND the output names the commits before and after the merge, each check with its exit status, and how long the command waited for the lock

### scenario.tasks.merge-checks — Run the named checks instead of the default

- GIVEN a delivered task
- WHEN the main agent runs `concorde task merge <task-id> --check "python3 scripts/concorde.py build" --check "python3 scripts/concorde.py validate"`
- THEN exactly those two commands run, in that order, in the primary worktree after the merge
- AND the default check does not run

### scenario.tasks.merge-waits — A second merge waits for the first

- GIVEN one process holding the merge lock for task `a`
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
- WHEN the main agent merges it with a `--check` that exits with status 1
- THEN the command fails with `check_failed` naming the check, its exit status, the log and the end of its output
- AND the primary branch is back at the commit it had before the merge, clean
- AND the task is still delivered with its worktree

### scenario.tasks.merge-refused-early — Refuse a merge that cannot close

- GIVEN a task that is not delivered, or whose branch moved past its latest delivery commit, or whose worktree has uncommitted changes, or a primary worktree with an uncommitted or untracked path or a detached `HEAD`
- WHEN the main agent runs `concorde task merge` for it
- THEN the command fails with `not_merged`, `dirty_worktree` or `primary_dirty` before merging
- AND the primary branch, the task record and the worktree are unchanged

## Escalation

### scenario.tasks.escalate — The main agent adds its link when it escalates

- GIVEN a task with an Operation run that ended with an error the main agent cannot decide
- WHEN the main agent runs `concorde task escalate` naming that run with its own code, detail, reason and options
- THEN the printed chain's top link has the level `main-agent` and the run's error, unchanged, as its cause
- AND the chain is appended to the task record's escalations and to the decision log, rendered and as JSON
- BUT an escalation that names no run and no file is refused with `nothing_to_escalate` and records nothing

### scenario.tasks.session-escalates — A task session escalates to the main agent

- GIVEN a task whose task session met an error it may not decide
- WHEN the task session runs `concorde task escalate --by task-session` naming the failed run
- THEN the recorded link has the level `task-session` and the run's error as its cause
- AND the decision log names the main agent as the receiver
- AND when the main agent then escalates with `--escalation 1`, its `main-agent` link has the task session's link, unchanged, as its cause

## Task sessions

### scenario.tasks.session-start — Start a task session

- GIVEN an open task `severity` and a Claude Code main agent whose session is named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity.session/` holds a settings file and a write hook
- AND `claude --bg` is started in the task worktree with those settings and a first prompt naming the task, its goal and `concorde-7d`
- AND the task record lists the started session with its identity and name
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying Claude Code's output, and the record is unchanged
- AND `--answer` or `--stop` for a Claude Code session is refused with `invalid_input`

### scenario.tasks.session-program — A task session runs on the main session's program

- GIVEN an open task `severity`
- WHEN `concorde task session severity` runs from a Claude Code session, from a pi session whose Concorde extension set `CONCORDE_CLIENT=pi`, and from neither
- THEN the first starts `claude --bg` and the second a pi session round
- AND the third is refused with `client_unknown`, naming every variable it looked at, and the record is unchanged

### scenario.tasks.pi-session-start — Start a pi task session

- GIVEN a pi main session, an open task `severity`, and pi, `bwrap`, `socat` and the sandbox-runtime package installed
- WHEN the main agent runs `concorde task session severity`
- THEN `.concorde/tasks/severity.session/` holds `boundary.ts` with the task worktree and decision log embedded
- AND a detached supervisor runs `pi -p --mode json --approve -e <boundary.ts>` in the task worktree with the developer's pi configuration, `CONCORDE_TASK_SESSION` set and a session file under `pi/`, its prompt the pi task-session guidance followed by the task's goal, Modules and decision log
- AND the task record lists the session with the program `pi` and round 1 as `running`, and the progress file names the round
- BUT when pi or the sandbox-runtime package is missing, the command fails with `session_failed` naming each missing program, and the record is unchanged

### scenario.tasks.pi-session-boundary — The pi boundary confines the session's writes

- GIVEN the boundary written for a pi task session
- WHEN it judges a `write` of a file in the task worktree, of the decision log and of a file of the primary worktree, and a `bash` command
- THEN the first two are allowed and the third is blocked with a reason naming the task worktree
- AND the command is rewritten to run in sandbox-runtime, writing only the task worktree, the Git directory, `.concorde/runs/`, `.concorde/tasks/` and package caches, with every network host allowed

### scenario.tasks.pi-session-rounds — The main agent's answer starts the next round

- GIVEN a pi task session whose round 1 ended `escalated`, naming escalation 1, which it recorded with `concorde task escalate --by task-session`
- WHEN the main agent runs `concorde task session severity --answer "<answer>"`
- THEN round 2 runs on the same session file with the answer as its prompt
- AND when it reports `delivered` naming the task's delivery commit, round 2 is recorded `delivered` with the report
- BUT `--answer` while a round runs is refused with `session_busy`, and for a task with no pi session with `no_session`

### scenario.tasks.pi-session-report-verified — A report the record contradicts fails the round

- GIVEN a pi session round whose report says `delivered` with a commit the task has not delivered, or `escalated` naming an escalation the task does not have
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_report_unverified` link naming each mismatch, and the report is kept beside it

### scenario.tasks.pi-session-failed — A round without a report fails with its evidence

- GIVEN a pi session round whose pi exits with status 1 without calling `concorde_report`
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_no_report` link naming the exit code, pi's stop reason and error message and the paths of the event stream and standard error
- AND the progress file shows the round finished

### scenario.tasks.pi-session-stop — Stop a running round

- GIVEN a pi task session with a running round
- WHEN the main agent runs `concorde task session severity --stop`
- THEN the round's pi process group ends and the round is recorded `stopped`
- BUT `--stop` when no round runs is refused with `session_idle`

### scenario.tasks.session-boundary — The session's boundary confines its writes

- GIVEN the settings written for a task session
- WHEN its write hook judges an Edit of a file in the task worktree, of the decision log and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the sandbox lets Bash write only the task worktree, the Git directory, `.concorde/runs/`, `.concorde/tasks/` and package caches
- AND the sandbox allows every network host
