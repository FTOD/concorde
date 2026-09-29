# Headless sessions scenarios

Concrete situations that show the [requirements](requirements.md) of
[Headless sessions](module.md).

### scenario.headless-sessions.command — A round is told its conditions and granted its tools

- GIVEN a prompt, and for a later round the session's identity
- WHEN the driver builds the round's command
- THEN it runs `claude -p` with the prompt, the headless note followed by the test procedure as appended system prompt, `stream-json` output and the [main agent](../../glossary.json#concept.main-agent)'s tools granted
- AND those tools include EnterWorktree and ExitWorktree
- AND the test procedure overrides, for this session only, the rule to hand every task to a [task session](../../glossary.json#concept.task-session), and states in order: open the task, enter its worktree with EnterWorktree, work it running Concorde commands in the foreground, validate and deliver, leave with ExitWorktree with action `keep`, merge from the primary worktree, and record in the [decision log](../../glossary.json#concept.decision-log) each decision it would otherwise ask about
- BUT a headless workflow run's command carries the headless note alone
- AND a later round resumes the session by its identity
- AND the environment keeps a background workflow alive

### scenario.headless-sessions.logs — A replayed empty turn is not the round's answer

- GIVEN a round's log with the session's identity, a replayed result without a model turn, tool calls, texts and the round's own result
- WHEN the driver reads the log
- THEN it names the session, every tool call with its target (its command, path or skill) and every text
- AND the round's result is the last one with a model turn

### scenario.headless-sessions.unsettled — Which runs a round left behind

- GIVEN runs of Operations and [execution commands](../../glossary.json#concept.execution-command) started before and since the session began: one running, one whose runner is gone, one cancelled at the round's end, one cancelled long before the round's end, one failed otherwise, runs already reported in an earlier wake message, and a worker's [progress file](../../glossary.json#concept.progress-file)
- WHEN a round ends
- THEN the running run and the run cancelled at the round's end are unsettled
- BUT a run started before the session, a run whose runner is gone, a run that failed otherwise, a run cancelled long before the round ended, a worker's progress file and a run already reported are not

### scenario.headless-sessions.wake — A run left running wakes the session

- GIVEN a session allowed more than one round, whose first round ends while an [Operation](../../glossary.json#concept.operation) run it started is still running
- AND whose second round succeeds and leaves no run behind
- WHEN the run ends
- THEN the driver resumes the same session with a message naming the run, its kind, name and workspace, how it ended and its result file
- AND the session ends idle after the second round, with both rounds, the run it woke for and the final answer and cost in `session.json`

### scenario.headless-sessions.wait-exceeded — A run that outlives the wait fails a kept session

- GIVEN a session whose first round ends while an [Operation](../../glossary.json#concept.operation) run it started is still running
- AND the run is still running when the wait limit is reached
- WHEN the driver stops waiting
- THEN it fails the session with `wait_exceeded`, naming the run's [run progress file](../../glossary.json#concept.run-progress-file) and the session's `session.json`
- AND `session.json` exists, ends `wait_exceeded`, names the same run progress file under `progress` and keeps the first round with its log
- AND the session is not woken for the run

### scenario.headless-sessions.live — A live session's own wake is told from a prompted turn

- GIVEN a live Claude Code session in a project
- WHEN the tool prompts it to start a command in background Bash and end its turn, and the command then ends while the tool sends nothing
- THEN the prompted turn has ended with its `result` and began no turn before it was prompted
- AND the command's end reaches the session as a `task_notification` that begins a turn, a wake the tool did not send
- AND every event is kept with its arrival time in the session's `.jsonl`
