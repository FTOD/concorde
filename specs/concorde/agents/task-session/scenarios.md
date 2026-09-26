# Task session scenarios

Concrete situations that show the [requirements](requirements.md) of [Task session](module.md).
Commands, the session report and error codes are defined in the [contracts](contracts.md).

## Starting and confining

### scenario.task-session.start — Start a task session

- GIVEN an open task `severity` and a Claude Code main agent whose session is named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity.session/` holds a settings file and a write hook
- AND `claude --bg` is started in the task worktree with those settings and a first prompt naming the task, its goal and `concorde-7d`
- AND the task record lists the started session with its identity and name
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying Claude Code's output, and the record is unchanged
- AND `--answer` or `--stop` for a Claude Code session is refused with `invalid_input`

### scenario.task-session.program — A task session runs on the main session's program

- GIVEN an open task `severity`
- WHEN `concorde task session severity` runs from a Claude Code session, from a pi session whose Concorde extension set `CONCORDE_CLIENT=pi`, and from neither
- THEN the first starts `claude --bg` and the second a pi session round
- AND the third is refused with `client_unknown`, naming every variable it looked at, and the record is unchanged

### scenario.task-session.pi-start — Start a pi task session

- GIVEN a pi main session, an open task `severity`, and pi, `bwrap`, `socat` and the sandbox-runtime package installed
- WHEN the main agent runs `concorde task session severity`
- THEN `.concorde/tasks/severity.session/` holds `boundary.ts` with the task worktree and decision log embedded
- AND a detached supervisor runs `pi -p --mode json --approve -e <boundary.ts>` in the task worktree with the developer's pi configuration, `CONCORDE_TASK_SESSION` set and a session file under `pi/`, its prompt the pi task-session guidance followed by the task's goal, Modules and decision log
- AND the task record lists the session with the program `pi` and round 1 as `running`, and the progress file names the round
- BUT when pi or the sandbox-runtime package is missing, the command fails with `session_failed` naming each missing program, and the record is unchanged

### scenario.task-session.pi-boundary — The pi boundary confines the session's writes

- GIVEN the boundary written for a pi task session
- WHEN it judges a `write` of a file in the task worktree, of the decision log and of a file of the primary worktree, and a `bash` command
- THEN the first two are allowed and the third is blocked with a reason naming the task worktree
- AND the command is rewritten to run in sandbox-runtime, writing only the task worktree, the Git directory, `.concorde/runs/`, `.concorde/tasks/` and package caches, with every network host allowed

### scenario.task-session.pi-rounds — The main agent's answer starts the next round

- GIVEN a pi task session whose round 1 ended `escalated`, naming escalation 1, which it recorded with `concorde task escalate --by task-session`
- WHEN the main agent runs `concorde task session severity --answer "<answer>"`
- THEN round 2 runs on the same session file with the answer as its prompt
- AND when it reports `delivered` naming the task's delivery commit, round 2 is recorded `delivered` with the report
- BUT `--answer` while a round runs is refused with `session_busy`, and for a task with no pi session with `no_session`

### scenario.task-session.pi-report-verified — A report the record contradicts fails the round

- GIVEN a pi session round whose report says `delivered` with a commit the task has not delivered, or `escalated` naming an escalation the task does not have
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_report_unverified` link naming each mismatch, and the report is kept beside it

### scenario.task-session.pi-failed — A round without a report fails with its evidence

- GIVEN a pi session round whose pi exits with status 1 without calling `concorde_report`
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_no_report` link naming the exit code, pi's stop reason and error message and the paths of the event stream and standard error
- AND the progress file shows the round finished

### scenario.task-session.pi-stop — Stop a running round

- GIVEN a pi task session with a running round
- WHEN the main agent runs `concorde task session severity --stop`
- THEN the round's pi receives SIGTERM, so it can end its session and clean up, and the round is recorded `stopped`
- AND a pi that ignores SIGTERM is killed with its process group 3 seconds later, and the round is recorded `stopped` as well
- BUT `--stop` when no round runs is refused with `session_idle`

### scenario.task-session.boundary — The session's boundary confines its writes

- GIVEN the settings written for a task session
- WHEN its write hook judges an Edit of a file in the task worktree, of the decision log and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the sandbox lets Bash write only the task worktree, the Git directory, `.concorde/runs/`, `.concorde/tasks/` and package caches
- AND the sandbox allows every network host
