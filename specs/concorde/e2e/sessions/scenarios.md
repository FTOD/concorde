# Headless sessions scenarios

Concrete situations that show the [requirements](requirements.md) of
[Headless sessions](module.md).

### scenario.headless-sessions.command — A round is told its conditions and granted its tools

- GIVEN a prompt, and for a later round the session's identity
- WHEN the driver builds the round's command
- THEN it runs `claude -p` with the prompt, the headless note as appended system prompt, `stream-json` output and the main agent's tools granted
- AND a later round resumes the session by its identity
- AND the environment keeps a background workflow alive

### scenario.headless-sessions.logs — A replayed empty turn is not the round's answer

- GIVEN a round's log with the session's identity, a replayed result without a model turn, tool calls, texts and the round's own result
- WHEN the driver reads the log
- THEN it names the session, every tool call with its target and every text
- AND the round's result is the last one with a model turn

### scenario.headless-sessions.unsettled — Which runs a round left behind

- GIVEN runs started before and since the session began: one running, one whose host is gone, one cancelled at the round's end, one failed otherwise, and a worker's progress file
- WHEN a round ends
- THEN the running run and the run cancelled at the round's end are unsettled
- BUT a run started before the session, a run whose host is gone, a run that failed otherwise, a run cancelled long before the round ended, a worker's progress file and a run already reported are not

### scenario.headless-sessions.wake — A run left running wakes the session

- GIVEN a session whose first round ends while an Operation run it started is still running
- WHEN the run ends
- THEN the driver resumes the same session with a message naming the run, its Operation and task, how it ended and its result file
- AND the session ends idle after the second round, with both rounds, the run it woke for and the final answer and cost in `session.json`
