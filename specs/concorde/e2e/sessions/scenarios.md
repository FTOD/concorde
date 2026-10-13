# Headless sessions scenarios

Concrete situations that show the [requirements](requirements.md) of
[Headless sessions](module.md).

### scenario.headless-sessions.command — A round is told its conditions and granted its tools

- GIVEN a prompt, and for a later round the session's identity
- WHEN the driver builds the round's command
- THEN it runs `claude -p` with the prompt, the headless note followed by the test procedure as appended system prompt, `stream-json` output and the [main agent](../../glossary.json#concept.main-agent)'s tools granted
- AND those tools include EnterWorktree and ExitWorktree
- AND the command's own `--settings` turns Claude Code's Bash sandbox off
- AND the test procedure overrides, for this session only, the rule to hand every task to a [task session](../../glossary.json#concept.task-session)
- AND the test procedure states in order: open the task, enter its worktree with EnterWorktree, work it running Concorde commands in the foreground, validate and deliver
- AND it then states: leave with ExitWorktree with action `keep`, merge from the primary worktree, and record in the [decision log](../../glossary.json#concept.decision-log) each decision it would otherwise ask about
- BUT a headless workflow run's command carries the headless note alone, with the sandbox off as well
- AND a later round resumes the session by its identity
- AND the environment keeps a background workflow alive

### scenario.headless-sessions.logs — A replayed empty turn is not the round's answer

- GIVEN a round's log with the session's identity, a replayed result whose `num_turns` is 0, tool calls, texts and the round's own result, whose `num_turns` is 5
- AND a command longer than 500 characters, and texts and a result holding unescaped Unicode line and paragraph separators
- WHEN the driver reads the log
- THEN it names the session, every tool call with its whole target (its command, path or skill) and every text
- AND the round's result is the last one whose `num_turns` is 1 or more
- BUT a round whose log holds only a replayed result has no result

### scenario.headless-sessions.unsettled — Which runs a round left behind

- GIVEN runs of Operations and [execution commands](../../glossary.json#concept.execution-command) started before and since the session began
- AND among them one running, one queued in the lobby behind its busy workspace and one whose runner is gone
- AND one cancelled at the round's end, one cancelled long before the round's end and one failed otherwise
- AND runs already reported in an earlier wake message, and a worker's [progress file](../../glossary.json#concept.progress-file)
- AND in the session's first second, a run started before the session and one started after it
- AND a run started in the next second, whose start time names no fraction of a second
- WHEN a round ends
- THEN the running run, the queued run, the run whose runner is gone and the run cancelled at the round's end are unsettled
- AND the wake message names the run whose runner is gone as ended without a result
- AND the runs started after the session are unsettled, whatever the precision of their start times
- BUT a run started before the session, even within the same second, and a run that failed otherwise are not unsettled
- AND neither are a run cancelled long before the round ended, a worker's progress file and a run already reported

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

### scenario.headless-sessions.moved-run — A run that enters its workspace while listed is found

- GIVEN a run queued in the lobby behind its busy workspace, whose runner lives
- WHEN the driver lists the run store, finds the run in the lobby, and the run then moves into its workspace folder before the driver reads it
- THEN the driver reads the run in its workspace folder and finds it unsettled, once

### scenario.headless-sessions.observation-failed — A run the driver cannot read fails a kept session

- GIVEN a session whose first round ends while the [run store](../../glossary.json#concept.run-store) holds a run whose progress file is no JSON object
- WHEN the driver reads it, and reads it again once
- THEN it fails the session with `observation_failed`, naming that progress file and the session's `session.json`
- AND `session.json` exists, ends `observation_failed`, names the same file under `file` and keeps the first round with its log
- AND a finished run whose result is no JSON object fails the same way, naming its result

### scenario.headless-sessions.binding-invalid — An invalid workspace binding refuses the session

- GIVEN a worktree whose [workspace binding](../../glossary.json#concept.workspace-binding) is no JSON, names no `.concorde`, or names one that is no text
- WHEN `session start` runs in it
- THEN the driver refuses with `binding_invalid`, naming the binding
- AND it starts no round and writes no `session.json`

### scenario.headless-sessions.rounds-exhausted — A session that leaves runs behind every round ends after its rounds

- GIVEN a session allowed two rounds, each of which leaves a new [Operation](../../glossary.json#concept.operation) run running
- WHEN the second round's run ends
- THEN the driver has started exactly two `claude -p` processes, the second resuming the session by its identity
- AND the session ends `rounds_exhausted`
- AND the first round woke for its run, while the second round woke for none and names its run under `left_behind`

### scenario.headless-sessions.failed-round — A failed round ends a kept session

- GIVEN a session whose first round leaves a run running and whose resumed round prints its output and an error and exits with status 3
- WHEN the second round ends
- THEN the session ends `exited`
- AND `session.json` keeps the first round with its result and the run it woke for, and the second round with its exit status and the end of its standard error
- AND both rounds' output and standard error files are kept
- AND the session's final answer is the first round's result
