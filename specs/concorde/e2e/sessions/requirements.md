# Headless sessions requirements

The Module-wide obligations of [Headless sessions](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.headless-sessions.conditions-in-tool — Testing conditions are told by the tool

Every round of a [headless session](../../glossary.json#concept.headless-session) SHALL be started
with the headless note appended to its system prompt.

### req.headless-sessions.tools-granted — A round is granted its tools

Every round of a headless session SHALL be started with its tools granted on the
command line.

### req.headless-sessions.claude-works-tasks — A headless main session works its tasks itself

Every round of a headless [main agent](../../glossary.json#concept.main-agent) SHALL
be granted EnterWorktree and ExitWorktree and carry, after its headless note, the test procedure,
which overrides for that session only the rule to hand every task to a
[task session](../../glossary.json#concept.task-session) and states that the session opens each
task, enters its worktree with EnterWorktree, works it running Concorde commands in the
foreground, validates and delivers it, leaves with ExitWorktree keeping the worktree, merges it
from the primary worktree and records in the task's
[decision log](../../glossary.json#concept.decision-log) each decision it would otherwise
ask about, because a task session's report would have no receiver once the round's process has
ended.

### req.headless-sessions.guidance-untouched — The headless note stays out of the guidance

The tool SHALL NOT add any part of a headless note or of the test procedure to the
[main-session guidance](../../glossary.json#concept.main-session-guidance), which stays what users
get.

### req.headless-sessions.wake — A run left behind wakes the session

When a round other than the session's last ends with a run of an
[Operation](../../glossary.json#concept.operation) or
[execution command](../../glossary.json#concept.execution-command) of the session still running, or
stopped by the round's end, the driver SHALL resume the same session with a
wake message naming it once every such run has finished
or its runner has gone.

The wait is bounded by [its own requirement](#req.headless-sessions.wait-bounded).

### req.headless-sessions.live-own-wake — A live session is woken by its own program

A live session SHALL be woken only by its own program, never by the tool.

Every event it printed is kept with its arrival time, so that a wake is told from a turn the tool
prompted.

### req.headless-sessions.wake-once — A run wakes the session once

The driver SHALL name each run in at most one wake message of a session, so a session is never
woken twice for one run.

### req.headless-sessions.rounds-bounded — A session has a bounded number of rounds

The driver SHALL start no more rounds of a session than the session was allowed.

### req.headless-sessions.wait-bounded — Waiting for a run is bounded

When a run a round left behind is still running after the wait limit, the driver SHALL fail the
session with `wait_exceeded`, naming that run's
[run progress file](../../glossary.json#concept.run-progress-file) and the session's record.

### req.headless-sessions.logs-kept — Every round is kept

The driver SHALL keep each round's output and standard error and the session's record in the
session directory, including for a session that ends with a failed round or fails with
`wait_exceeded`, whose record ends `wait_exceeded` and names the run progress file of the run that
outlived the wait.
