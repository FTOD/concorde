# Headless sessions requirements

The Module-wide obligations of [Headless sessions](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.headless-sessions.conditions-in-tool — Testing conditions are told by the tool

The driver SHALL start every round of a
[headless session](../../glossary.json#concept.headless-session) with the headless note appended to
its system prompt.

### req.headless-sessions.tools-granted — A round is granted its tools

The driver SHALL start every round of a headless session with its tools granted on the command
line.

### req.headless-sessions.sandbox-off — A round runs without the Bash sandbox

The driver SHALL start every round of a headless session with Claude Code's Bash sandbox turned
off by the round's own command line, never by a change of the developer's settings files.

A [detached run](../../glossary.json#concept.detached-run) started from a sandboxed Bash call dies
with that call, so it could never outlive the round.

### req.headless-sessions.worktree-tools-granted — A headless main session may enter task worktrees

The driver SHALL grant EnterWorktree and ExitWorktree to every round of a headless [main
agent](../../glossary.json#concept.main-agent).

### req.headless-sessions.claude-works-tasks — A headless main session works its tasks itself

The driver SHALL append to every round of a headless main agent, after its headless note, a test
procedure with these contents:

- It overrides, for that session only, the rule to hand every task to a
  [task session](../../glossary.json#concept.task-session).
- It states that the session opens each task and enters its worktree with EnterWorktree.
- It states that the session works the task running Concorde commands in the foreground, then
  validates and delivers it.
- It states that the session leaves with ExitWorktree keeping the worktree and merges the task from
  the primary worktree.
- It states that the session records in the task's
  [decision log](../../glossary.json#concept.decision-log) each decision it would otherwise ask
  about.

The reason is that a task session's report would have no receiver once the round's process has
ended.

### req.headless-sessions.guidance-untouched — The headless note stays out of the guidance

The tool SHALL NOT add any part of a headless note or of the test procedure to the
[main-session guidance](../../glossary.json#concept.main-session-guidance), which stays what users
get.

### req.headless-sessions.wake — A run left behind wakes the session

When both of these conditions hold, the driver SHALL resume the same session with a wake message
naming each such run, once every such run has finished or its runner has gone:

- A round other than the session's last ends.
- A run of an [Operation](../../glossary.json#concept.operation) or
  [execution command](../../glossary.json#concept.execution-command) of the session is still
  running at that end, was stopped by it, or is unfinished with its runner gone.

The wait is bounded by [its own requirement](#req.headless-sessions.wait-bounded).

### req.headless-sessions.live-own-wake — A live session is woken by its own program

A live session SHALL be woken only by its own program, never by the tool.

Every event it printed is kept with its arrival time so that a wake is distinguished from a turn
the tool prompted.

### req.headless-sessions.wake-once — A run wakes the session once

The driver SHALL name each run in at most one wake message of a session, so a session is never
woken twice for one run.

### req.headless-sessions.rounds-bounded — A session has a bounded number of rounds

The driver SHALL start no more rounds of a session than the session was allowed.

### req.headless-sessions.left-behind-not-woken — The last round's runs are left behind

When the session's last allowed round leaves runs unsettled, the driver SHALL record them as left
behind and never as runs a round woke for.

### req.headless-sessions.wait-bounded — Waiting for a run is bounded

When a run a round left behind still runs after the wait limit, the driver SHALL fail the session
with `wait_exceeded`, naming:

- That run's [run progress file](../../glossary.json#concept.run-progress-file).
- The session's record.

### req.headless-sessions.round-answer — A round's answer has a model turn

The driver SHALL take as a round's result the last `result` event of the round whose `num_turns` is
1 or more.

A round without such an event has no result: a resumed round's replayed turn has `num_turns` 0.

### req.headless-sessions.observation-visible — What the driver cannot observe fails the session

The driver SHALL fail the session with `observation_failed`, naming the file and the session's
record, when one of these still cannot be read as a JSON object when read again once:

- The [run progress file](../../glossary.json#concept.run-progress-file) of a run in the
  [run store](../../glossary.json#concept.run-store).
- The result of a run whose run progress file says it finished.

The same holds for a run progress file that names no start time the driver can read.

### req.headless-sessions.binding-valid — An invalid workspace binding refuses the session

When the session's worktree holds a [workspace
binding](../../glossary.json#concept.workspace-binding) that cannot be read or names no
`.concorde`, the driver SHALL refuse the session with `binding_invalid`, naming the binding, before
it starts the first round.

### req.headless-sessions.logs-kept — Every round is kept

The driver SHALL keep each round's output and standard error and the session's record in the session
directory, also for a session that ends with a failed round or fails with `wait_exceeded` or
`observation_failed`.

The record of such a failure ends with its code and names the file concerned: the run progress
file of the run that outlived the wait, or the file the driver could not read.
