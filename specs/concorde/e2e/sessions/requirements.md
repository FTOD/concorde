# Headless sessions requirements

The Module-wide obligations of [Headless sessions](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.headless-sessions.conditions-in-tool — Testing conditions are told by the tool

Every round of a [headless session](../../glossary.json#concept.headless-session) SHALL be started
with its client's [headless note](../../glossary.json#concept.headless-note) appended to its system
prompt.

### req.headless-sessions.tools-granted — A Claude Code round is granted its tools

Every Claude Code round of a headless session SHALL be started with its tools granted on the
command line.

### req.headless-sessions.guidance-untouched — The headless note stays out of the guidance

The tool SHALL NOT add any part of a headless note to the
[main-session guidance](../../glossary.json#concept.main-session-guidance), which stays what users
get.

### req.headless-sessions.wake — A run left behind wakes the session

When a round other than the session's last ends with a run of an
[Operation](../../glossary.json#concept.operation) or
[execution command](../../glossary.json#concept.execution-command) of the session still running, or
stopped by the round's end, the driver SHALL resume the same session with a
[wake message](../../glossary.json#concept.wake-message) naming it once every such run has finished
or its runner has gone.

The wait is bounded by [its own requirement](#req.headless-sessions.wait-bounded).

### req.headless-sessions.wake-once — A run wakes the session once

The driver SHALL name each run in at most one wake message of a session, so a session is never
woken twice for one run.

### req.headless-sessions.rounds-bounded — A session has a bounded number of rounds

The driver SHALL start no more rounds of a session than the session was allowed.

### req.headless-sessions.wait-bounded — Waiting for a run is bounded

When a run a round left behind is still running after the wait limit, the driver SHALL fail the
session with `wait_exceeded`, naming that run's
[run progress file](../../glossary.json#concept.run-progress-file).

### req.headless-sessions.logs-kept — Every round is kept

The driver SHALL keep each round's output and standard error and the session's record in the
session directory, including for a session that ends with a failed round.
