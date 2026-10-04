# Headless sessions

## Purpose

Headless sessions drives a real Claude Code main session in a
[test project](../../glossary.json#concept.test-project) without a person. This lets End-to-end
testing watch what a [main agent](../../glossary.json#concept.main-agent) actually does with Concorde.
It performs these actions:

- Starts the session.
- Grants it its tools.
- Tells it the conditions of running headless.
- When a run it left behind ends, wakes the session.
- Keeps every round's log.
- Reads the logs back.

It also keeps a main session running as a live session. Its wakes are its own program's.
It exists for the people developing Concorde. It changes nothing a user gets. Headless sessions
handles every difference between a [headless session](../../glossary.json#concept.headless-session)
and an interactive one. It never changes the
[main-session guidance](../../glossary.json#concept.main-session-guidance).

## Core concepts

<a id="concept.headless-session"></a>

**[Headless session](../../glossary.json#concept.headless-session) and its rounds.** A headless
session is one main session run without a person, in one or more **rounds**. Each round is one
`claude -p` process. The first receives the developer's prompt. Each later round continues the
same session. Since Concorde's main agent and task sessions use only Claude Code for now,
a headless session always uses Claude Code. As the project's
[worker configuration](../../glossary.json#concept.worker-configuration) chooses, the
[workers](../../glossary.json#concept.worker) its runs launch may still run on pi.

**The headless note and the test procedure.** A headless session differs from the developer's
interactive one only because of how it is run. When the turn ends, `claude -p` ends its process.
It also ends every background command with it. No notification reaches it afterwards. The tool tells the
session so in the **headless note** appended to its system prompt. A headless main session also
receives the **test procedure**. This lets it carry each task out itself because a task session's
report would find no receiver. Both are described under
[What the session is told](#what-the-session-is-told).

**Unsettled runs and the wake.** The one thing an interactive session has and a headless one lacks
is being woken when a run ends. When a round ends, these runs are its **unsettled** runs:

- Runs it left running.
- Runs that the turn's end stopped.

The tool waits for them. It resumes the same session with a **wake message**.
The message names how each ended.
When a round has no unsettled run, the session is **idle**. When the session is idle, it ends.

**Live session.** A [live session](#live-sessions) keeps one main session's process running
instead of running it in rounds. This lets its own program wake it instead of the tool.

## Overview

The diagram shows one round and its wake. The session ends in these ways:

- The session ends with `idle`.
- When a round's process fails, the session ends with `exited`. The tool keeps its standard error.
- When the first round names no session, the session ends with `no_session`.
- After the allowed rounds, the session ends with `rounds_exhausted`
  ([requirements](requirements.md#req.headless-sessions.rounds-bounded)).
- When a run still runs after the wait limit, the session ends with `wait_exceeded`.

```d2 illustrative
direction: down
round: "Round n: claude -p"
failed: "Process failed?" {shape: diamond}
named: "Session named?" {shape: diamond}
unsettled: "Unsettled runs?" {shape: diamond}
wait: "Wait until each has ended or its runner has gone"
within: "Within the hour?" {shape: diamond}
remaining: "A round left?" {shape: diamond}
wake: "Resume with the wake message"
exited: "exited" {shape: oval}
no_session: "no_session" {shape: oval}
idle: "idle" {shape: oval}
exceeded: "wait_exceeded, session.json written first" {shape: oval}
exhausted: "rounds_exhausted" {shape: oval}
round -> failed
failed -> exited: yes
failed -> named: no
named -> no_session: no
named -> unsettled: yes
unsettled -> idle: no
unsettled -> wait: yes
wait -> within
within -> exceeded: no
within -> remaining: yes
remaining -> exhausted: no
remaining -> wake: yes
wake -> round: "round n + 1"
```

## Running a session

The developer, or another component of End-to-end testing, runs these commands:

```text
python3 scripts/e2e/e2e.py session start <project> --prompt "<what the developer asks>" [--rounds 4]
python3 scripts/e2e/e2e.py session show <session directory>
```

`session start` keeps the session under `<project>/.concorde/runs/e2e/sessions/<time>/` with these
files:

- One `round-<n>.jsonl` with the round's `stream-json` output per round.
- One `round-<n>.err` per round.
- `session.json`.

The last file contains these details:

- The session identity.
- The prompt.
- Each round's exit status.
- Each round's result.
- Each round's number of tool calls.
- The runs each round woke for.
- How the session ended.
- Its final answer.
- Its cost.

`session start` prints `session.json`. From the logs, `session show` adds every round's tool calls
and texts.
Each tool call includes one of these targets:

- Its command.
- Its path.
- Its skill.

Unless `--rounds` says otherwise, the tool allows at most 4 rounds.

A headless workflow run of End-to-end testing, `run --via claude`, is a headless session of one
workflow prompt. It is kept under `.concorde/runs/e2e/<task>-claude/`. In it, the session works as
the task's [task session](../../glossary.json#concept.task-session). A [dogfood
scenario](../../glossary.json#concept.dogfood-scenario) runs its prompt as one. It is kept under its
scenario directory's `sessions/<time>/`. The scenario runner passes this path in place of the default.

### What the session is told

Since Claude Code ignores an untrusted project's allow rules, a round starts with the main agent's
tools granted on the command line. These are a workflow's own list or the following tools:

- Bash.
- Read.
- Write.
- Edit.
- Glob.
- Grep.
- Skill.
- TodoWrite.
- EnterWorktree.
- ExitWorktree.

The round also starts with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, which keeps a background
workflow alive. The tool appends the headless note to its system prompt. The note states these
conditions:

- Nobody answers questions.
- When the turn ends, a command left in the background is stopped.
- Nothing wakes the session, so Concorde commands run in the foreground.
- When a round ends, a run that still runs is followed by a wake-up.
- A task session's report would find no receiver.

See [requirements](requirements.md#req.headless-sessions.conditions-in-tool) and
[tools granted](requirements.md#req.headless-sessions.tools-granted). The turn's end stops Claude
Code's own background command. A Concorde run that command was still running then ends with the
error code `cancelled`. The session is woken for it as a run stopped by that end. A
[detached run](../../glossary.json#concept.detached-run) outlives the round. When it ends, it wakes
the session (see [Waking the session](#waking-the-session)).

**The test-only exception.** The main agent hands every task to a task session. It never works
inside a task worktree. A headless main session cannot do this because a task session sends the
main agent its outcome with SendMessage. Because a `claude -p` round ends with its turn, the message has no receiver.
The process ends long before the message is sent. A headless main session exists
only in the tests. Headless sessions therefore gives it the test procedure instead of bending
the main-session guidance. This procedure is appended after the headless note to every round of a
headless main session. For that test session only, it overrides the guidance's rule to hand every
task to a task session. It says that the session carries each task out itself:

1. open the task from the primary worktree.
2. enter the task worktree with EnterWorktree.
3. work the task there with that worktree's own `concorde`. Run every Concorde command in the
   foreground.
4. validate and deliver it with `concorde task-validation` and `concorde delivery`.
5. leave the worktree with ExitWorktree with action `keep`, so its worktree and branch stay.
6. merge the task from the primary worktree with `concorde task merge`.

Since nobody answers, it also tells the session to decide what it would otherwise ask the
developer or escalate.

It tells the session to record each such decision in the task's
[decision log](../../glossary.json#concept.decision-log), with its reason and the options it
weighed.

EnterWorktree and ExitWorktree are granted for it
([requirements](requirements.md#req.headless-sessions.claude-works-tasks)). The exception holds
for headless main sessions only. A headless workflow run works as a task session in the first
place and gets the note alone.

### Waking the session

When a round ends, the tool looks at runs started since the session began. These are the
[runs](../../glossary.json#concept.run) of
[Operations](../../glossary.json#concept.operation) and
[execution commands](../../glossary.json#concept.execution-command).
It looks only at runs it did not report yet
([requirements](requirements.md#req.headless-sessions.wake-once)). It looks in the
[run store](../../glossary.json#concept.run-store) of the session's project, in these locations:

- The workspace folders of the current tasks.
- `.concorde/unbound/`.
- The lobby `.concorde/lobby/`, where a bound run waits for its workspace's lock.

When the session runs in a task worktree, these locations belong to the `.concorde` its
[workspace binding](../../glossary.json#concept.workspace-binding) names. Otherwise, they belong
to the worktree's own `.concorde`. Every run started there since the session began counts as the
session's. This includes the runs of the tasks it opened. Their workspace folders lie in the
same `.concorde`. If another session starts a run in the same project meanwhile, the tool also
takes that run for this session.

When a run meets both conditions, it still runs:

- Its [run progress file](../../glossary.json#concept.run-progress-file) is not finished.
- Its runner lives.

When both conditions hold, the round's end stopped the run:

- The run's result has the error code `cancelled`.
- The result was written within 30 seconds of the round's end.

These runs are the round's unsettled ones. With no unsettled runs, the session is idle.
When the session is idle, it ends.
Otherwise, the tool waits until every running run finishes or its runner goes.
When a round is left, it then resumes the same session with a wake message. The message names these details:

- Each run.
- Its kind.
- Its name.
- Its workspace.
- How it ended.
- Its result file.

For a stopped run, it says that the turn's end stopped it. For a run whose runner went without
writing a result, it says that the run ended without one
([requirements](requirements.md#req.headless-sessions.wake)).

The wait lasts at most an hour. If a run still runs then, the tool fails the session with `wait_exceeded`
([requirements](requirements.md#req.headless-sessions.wait-bounded)). Before the failure goes up,
the tool writes `session.json` with these details:

- The rounds so far.
- The end `wait_exceeded`.
- Under `progress`, the path of that run's run progress file.

The failure names the same file and the session's `session.json`.
This lets the kept session show what outlived the wait.

### Live sessions

<a id="live-sessions"></a>

A round's process ends with its turn, so the tool stands in for every wake. A live session instead
keeps one main session's process running. It feeds the process prompts on standard input so that
its own program wakes it.
The program is `claude -p --input-format stream-json --output-format stream-json
--verbose`. The process is granted Bash and Read. When one of its background commands ends, it
begins a turn of its own with a `task_notification`. It gets a short note appended to its system
prompt. The note says that every prompt is a step of a test. Each step is to be done exactly.
Each answer is to be brief. In the directory the caller names, the tool keeps each event
the process prints as one line of `<name>.jsonl`. Each line includes its arrival time.
Its standard error is kept as `<name>.err`.
From these, the tool tells these details:

- When a prompted turn ended, from the `result` event.
- When a turn began, from the `system` `init` event.
- Which notifications arrived.
- What a tool call printed.

While the caller sends no prompt, a turn that begins or a notification that arrives is a **wake**
([requirements](requirements.md#req.headless-sessions.live-own-wake)). Closing standard input ends
the session. After 30 seconds, the tool kills what is left of it. The [owners
case](../module.md#owners-case) of End-to-end testing runs several live sessions at once.

### Reading the logs

A resumed round first replays the stopped background command as a turn of its own with no model
turn. Its `result` event is not the round's answer. The round's result is the last `result` event
with a model turn. Its cost is the session's total so far.

## Why it is built this way

**Testing conditions stay in the tool.** Writing "run in the foreground" into the main-session
guidance would change every user's main agent's behaviour to suit a test. The tool appends the
headless note instead. By reproducing a wake when a run ends, the wake loop lets tests examine
the main agent's own judgment under users' guidance.

**Why the main session works its tasks itself.** A task session sends its outcome with SendMessage
to the session name the main agent gave `--main`. Nothing in Concorde's files tells the tool that
it sent the outcome. With the round's process gone, that message is lost. Running the headless
main session as a background session would change how the driver runs Claude Code. Reading the
task session's report from its transcript would also change how the driver runs Claude Code.
The exception keeps `claude -p` rounds. It gives up only testing delegation, which a headless
main session does not exercise. What it does test differs from what a user's main agent does
there. It works the task itself, as a task session would.

**Resuming, not restarting.** A wake resumes the same session so the main agent keeps these things,
exactly as an interactive session does on a notification:

- Everything the session knows.
- Its decision log entries.
- Its plan.

The tool reports each run once. The number of rounds bounds a session that keeps leaving runs
behind. The wait limit bounds a run that never ends.
When the wait limit expires, the tool fails with the run's run progress file named.

**Files, not the model's words.** Because the session's text is under test, the tool uses
Concorde's own progress and result files to identify runs a round left behind. It never reads this from
what the session said. The 30-second window separates a run the turn's end stopped from one the
session cancelled itself. This window is a heuristic of the testing condition. If a session
cancels a run in its very last seconds, the tool wakes it for that run too. This only costs a round.

## Files

<a id="realization.headless-sessions.driver"></a>

The **session driver** is `scripts/e2e/sessions.py`. It handles these things:

- The command of a round.
- The environment.
- The wake loop.
- The log reading.
- `session.json`.

The `session` commands of `scripts/e2e/e2e.py` call it. `scripts/e2e/live.py` holds the live sessions.

<a id="realization.headless-sessions.tests"></a>

The **session driver tests**, `tests/concorde/e2e/test_sessions.py`, verify the
[requirements](requirements.md) and [scenarios](scenarios.md) by checking these things:

- The command.
- The log reading.
- Which runs are unsettled.
- With a stand-in for `claude -p`, a whole session that is woken once.

The live sessions are tested with the owners case, in `tests/concorde/e2e/test_owners.py`.

## Around it

<a id="uses-execution"></a>

**Execution** provides the run progress file and the [run
result](../../glossary.json#concept.run-result) of every run a session starts. It also provides the
run store that holds them. To decide which runs are unsettled and to write the wake message, the
driver relies on these details:

- The run progress file names these details:
  - The run's kind.
  - Its name.
  - Its workspace.
  - Its phase.
  - Its start time.
- The [run lock](../../glossary.json#concept.run-lock) tells whether its runner still lives.
- The result carries these details:
  - The status.
  - The summary.
  - The error code.
- The workspace binding, which the Kernel defines, names the `.concorde` of its runs.

The driver never changes any of them.

<a id="uses-kernel"></a>

**Kernel** defines the [workspace binding](../../glossary.json#concept.workspace-binding).
The driver relies on its `.concorde` to name where a session's workspace keeps these files:

- Its runs' locks.
- Its [run progress files](../../glossary.json#concept.run-progress-file).

Claude Code is external. The driver relies on `claude -p` with these options and output:

- `--resume`.
- `--append-system-prompt`.
- `--allowedTools`.
- `stream-json` output, whose events carry the session identity.

A live session also relies on `--input-format stream-json`.
