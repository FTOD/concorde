# Headless sessions scenarios

Concrete situations that show the [requirements](requirements.md) of
[Headless sessions](module.md).

### scenario.headless-sessions.command — A round is told its conditions and granted its tools

- GIVEN a prompt, and for a later round the session's identity
- WHEN the driver builds the round's command
- THEN it runs `claude -p` with the prompt, the [headless note](../../glossary.json#concept.headless-note) as appended system prompt, `stream-json` output and the [main agent](../../glossary.json#concept.main-agent)'s tools granted
- AND a later round resumes the session by its identity
- AND the environment keeps a background workflow alive

### scenario.headless-sessions.logs — A replayed empty turn is not the round's answer

- GIVEN a round's log with the session's identity, a replayed result without a model turn, tool calls, texts and the round's own result
- WHEN the driver reads the log
- THEN it names the session, every tool call with its target (its command, path or skill) and every text
- AND the round's result is the last one with a model turn

### scenario.headless-sessions.unsettled — Which runs a round left behind

- GIVEN runs of Operations and [execution commands](../../glossary.json#concept.execution-command) started before and since the session began: one running, one whose runner is gone, one cancelled at the round's end, one cancelled long before the round's end, one failed otherwise, runs already reported in an earlier [wake message](../../glossary.json#concept.wake-message), and a worker's [progress file](../../glossary.json#concept.progress-file)
- WHEN a round ends
- THEN the running run and the run cancelled at the round's end are unsettled
- BUT a run started before the session, a run whose runner is gone, a run that failed otherwise, a run cancelled long before the round ended, a worker's progress file and a run already reported are not

### scenario.headless-sessions.pi — A pi session continues one session file and is woken alike

- GIVEN a project installed for pi and a prompt
- WHEN the developer starts a [headless session](../../glossary.json#concept.headless-session) with `--client pi`
- THEN every round runs `pi -p --mode json --approve` with pi's headless note, the session directory and the same session identity, the prompt on standard input
- AND a round that leaves a run running is followed, once the run ends, by a round of the same session whose prompt names the run and its result
- AND the record names the client, adds up the rounds' costs and shows each round's tool calls and turns

### scenario.headless-sessions.wake — A run left running wakes the session

- GIVEN a session allowed more than one round, whose first round ends while an [Operation](../../glossary.json#concept.operation) run it started is still running
- AND whose second round succeeds and leaves no run behind
- WHEN the run ends
- THEN the driver resumes the same session with a message naming the run, its kind, name and workspace, how it ended and its result file
- AND the session ends idle after the second round, with both rounds, the run it woke for and the final answer and cost in `session.json`

### scenario.headless-sessions.unknown-client — Another client is refused

- GIVEN a project and a prompt
- WHEN the driver is asked to start a headless session on a client other than Claude Code or pi
- THEN it refuses with `unknown_client`

### scenario.headless-sessions.wait-exceeded — A run that outlives the wait fails a kept session

- GIVEN a session whose first round ends while an [Operation](../../glossary.json#concept.operation) run it started is still running
- AND the run is still running when the wait limit is reached
- WHEN the driver stops waiting
- THEN it fails the session with `wait_exceeded`, naming the run's [run progress file](../../glossary.json#concept.run-progress-file) and the session's `session.json`
- AND `session.json` exists, ends `wait_exceeded`, names the same run progress file under `progress` and keeps the first round with its log
- AND the session is not woken for the run
