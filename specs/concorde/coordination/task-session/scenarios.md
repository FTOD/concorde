# Task sessions scenarios

Concrete situations that show the [requirements](requirements.md) of [Task sessions](module.md).
Commands, the [session report](../../glossary.json#concept.session-report) and error codes are
defined in the [contracts](contracts.md).

## Starting and confining

### scenario.task-session.start — Start a task session

- GIVEN an open task `severity` and a Claude Code [main agent](../../glossary.json#concept.main-agent) whose session is named `concorde-7d`
- WHEN the main agent runs `concorde task session severity --main concorde-7d`
- THEN `.concorde/tasks/severity.session/` holds a settings file and a [write hook](../../glossary.json#concept.write-hook)
- AND `claude --bg` is started in the task worktree with those settings and a first prompt naming the task, its goal and `concorde-7d`
- AND the [task record](../../glossary.json#concept.task-record) lists the started session with its identity and name
- BUT when Claude Code reports no started session, the command fails with `session_failed`, carrying Claude Code's output, and the record is unchanged

### scenario.task-session.claude-no-rounds — A Claude Code session takes no round options

- GIVEN an open task `severity` and a Claude Code main agent
- WHEN the main agent runs `concorde task session severity` with `--answer "<answer>"`, with `--stop` or with `--wait`
- THEN each is refused with `invalid_input`, naming SendMessage as the way a Claude Code task session receives the main agent's answers

### scenario.task-session.program — A task session runs on the main session's program

- GIVEN an open task `severity`
- WHEN `concorde task session severity --main concorde-7d` runs from a Claude Code session, from a pi session whose Concorde extension set `CONCORDE_CLIENT=pi`, and from neither
- THEN the first starts `claude --bg` and the second a pi [session round](../../glossary.json#concept.session-round)
- AND the third is refused with `client_unknown`, naming every variable it looked at, and the record is unchanged

### scenario.task-session.pi-start — Start a pi task session

- GIVEN a pi main session, an open task `severity`, and pi, `bwrap`, `socat` and the sandbox-runtime package installed
- WHEN the main agent runs `concorde task session severity`
- THEN `.concorde/tasks/severity.session/` holds `boundary.ts` with the task worktree and [decision log](../../glossary.json#concept.decision-log) embedded
- AND a detached supervisor runs `pi -p --mode json --approve -e <boundary.ts>` in the task worktree with the developer's pi configuration, `CONCORDE_TASK_SESSION` set and a session file under `pi/`, its prompt the pi [task-session](../../glossary.json#concept.task-session) guidance followed by the task's goal, Modules and decision log
- AND the task record lists the session with the program `pi` and round 1 as `running`, and the round's status file `status.json` names the round
- BUT when pi, on Linux `bwrap` or `socat`, or the sandbox-runtime package is missing, the command fails with `session_failed` naming each missing program, and the record is unchanged

### scenario.task-session.pi-boundary — The pi boundary confines the session's writes

- GIVEN the boundary written for a pi task session
- WHEN it judges a `write` of a file in the task worktree, of the decision log and of a file of the primary worktree, and a `bash` command
- THEN the first two are allowed and the third is blocked with a reason naming the task worktree
- AND the command is rewritten to run in sandbox-runtime, writing only the task worktree, the Git directory, the primary worktree's `.concorde/runs/` and `.concorde/tasks/`, package caches and the session's private temporary directory, with every network host allowed

### scenario.task-session.pi-rounds — The main agent's answer starts the next round

- GIVEN a pi task session whose round 1 ended `escalated`, naming escalation 1, which it recorded with `concorde task escalate --by task-session`
- WHEN the main agent runs `concorde task session severity --answer "<answer>"`
- THEN round 2 runs on the same session file with the answer as its prompt
- AND when it reports `delivered` naming the task's [delivery commit](../../glossary.json#concept.delivery-commit), round 2 is recorded `delivered` with the report

### scenario.task-session.pi-busy — One round runs at a time

- GIVEN a pi task session of the task `severity` with a running round
- WHEN the main agent runs `concorde task session severity --answer "<answer>"` or `concorde task session severity`
- THEN both are refused with `session_busy`, naming the running round and its supervisor process, and no round starts

### scenario.task-session.pi-no-session — An answer or a stop needs a pi session

- GIVEN an open task `severity` for which no pi task session was started
- WHEN the main agent runs `concorde task session severity` with `--answer "<answer>"` or with `--stop`
- THEN it is refused with `no_session`, no round starts and the task record is unchanged

### scenario.task-session.pi-report-verified — A report the record contradicts fails the round

- GIVEN a pi session round whose report says `delivered` with a commit that is no delivery commit of the task's workspace on its branch or that does not verify against its [evidence bundle](../../glossary.json#concept.evidence-bundle), or `escalated` naming an escalation the task record does not have
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_report_unverified` link naming each mismatch, and the round's entry in the task record keeps the report beside that link

### scenario.task-session.pi-report-shape — New reports use one fixed field set

- GIVEN a new pi task-session report with the six fields `status`, `summary`, `commit`, `escalations`, `decisions` and `open`
- WHEN the boundary and supervisor validate the report
- THEN delivered is accepted only with a full delivery commit and an empty escalation array, and escalated only with a null commit and a nonempty unique array of positive escalation numbers
- BUT a `concorde_report` call with an omitted field, empty commit, mixed status fields or malformed value returns an error naming the problem and does not end the round, and a report that reaches the supervisor without following the contract ends the round `failed` with a `session_report_unverified` link

### scenario.task-session.pi-report-v1 — Earlier reports stay as they were recorded

- GIVEN a task record whose pi session holds rounds recorded with version 1 reports, which have only the fields of their status: no `escalations` when delivered, no `commit` when escalated
- WHEN the task record is read or its rounds are settled
- THEN the report is neither validated again nor rewritten, and the record stays unchanged

### scenario.task-session.pi-failed — A round without a report fails with its evidence

- GIVEN a pi session round whose pi exits with status 1 without calling `concorde_report`
- WHEN the supervisor records the round
- THEN the round is `failed` with a `session_no_report` link naming the exit code, pi's stop reason and error message and the paths of the event stream and standard error
- AND the round's status file shows the round finished

### scenario.task-session.pi-stop — Stop a running round

- GIVEN a pi task session with a running round
- WHEN the main agent runs `concorde task session severity --stop`
- THEN the round's pi receives SIGTERM, so it can end its session and clean up, and the round is recorded `stopped`
- AND a pi that ignores SIGTERM is killed with its process group 3 seconds later, and the round is recorded `stopped` as well

### scenario.task-session.pi-stop-idle — Nothing to stop without a running round

- GIVEN a pi task session of the task `severity` whose last round has ended
- WHEN the main agent runs `concorde task session severity --stop`
- THEN it is refused with `session_idle` and the recorded rounds are unchanged

### scenario.task-session.pi-wait — Wait for a round without the run view

- GIVEN a pi task session with a running round
- WHEN the main agent runs `concorde task session severity --wait`
- THEN the command returns once the round has ended, printing the session with the round's recorded outcome
- AND with `--wait 1` it returns after a second, the round still `running`
- BUT `--wait` for a task without a pi session is refused with `no_session`

### scenario.task-session.boundary — The session's boundary confines its writes

- GIVEN the settings written for a task session
- WHEN its write hook judges an Edit of a file in the task worktree, of the decision log and of a file of the primary worktree
- THEN the first two are allowed and the third is denied with a reason naming the task worktree
- AND the sandbox lets Bash write only the task worktree, the Git directory, the primary worktree's `.concorde/runs/` and `.concorde/tasks/` and package caches
- AND the sandbox allows every network host
