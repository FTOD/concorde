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

### scenario.tasks.not-primary — Refuse to open, close or start sessions from a linked worktree

- GIVEN a shell whose working directory is inside a task worktree
- WHEN `concorde task open`, `concorde task close` or `concorde task session` is run there
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
- AND the record's state is `merged` with the primary branch's head recorded
- AND the branch, the record and the decision log remain

### scenario.tasks.close-not-merged — Refuse to close an unmerged task as merged

- GIVEN a task that is not delivered, or whose delivered head is not contained in the primary branch, or whose branch moved past its latest delivery commit
- WHEN the main agent closes it with `--merged`
- THEN the command fails with `not_merged`
- AND the worktree and the record are unchanged

### scenario.tasks.abandon — Abandon a task

- GIVEN an active task whose worktree has uncommitted changes
- WHEN the main agent closes it with `--abandoned` and without `--force`
- THEN the command fails with `dirty_worktree` and nothing changes
- BUT with `--force` the worktree is removed, the state is `abandoned` and the branch is kept

### scenario.tasks.closed-inert — A closed task accepts no run

- GIVEN a merged or abandoned task
- WHEN the host begins a run for it
- THEN the update fails with `task_closed`

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

- GIVEN an open task `severity` and the main agent's session named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity.session/` holds a settings file and a write hook
- AND `claude --bg` is started in the task worktree with those settings and a first prompt naming the task, its goal and `concorde-7d`
- AND the task record lists the started session with its identity and name
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying Claude Code's output, and the record is unchanged

### scenario.tasks.session-boundary — The session's boundary confines its writes

- GIVEN the settings written for a task session
- WHEN its write hook judges an Edit of a file in the task worktree, of the decision log and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the sandbox lets Bash write only the task worktree, the Git directory, `.concorde/runs/`, `.concorde/tasks/` and package caches
