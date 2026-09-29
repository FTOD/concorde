# Headless sessions

## Purpose

Headless sessions drives a real Claude Code main session in a
[test project](../../glossary.json#concept.test-project) without a person, so that End-to-end
testing can watch what a [main agent](../../glossary.json#concept.main-agent) actually does with
Concorde. It starts the session, grants it its tools, tells it the conditions of running headless,
wakes it when a run it left behind ends, keeps every round's log and reads the logs back. It also
keeps a main session running as a live session, whose wakes are its own program's. It exists
for the people developing Concorde and changes nothing a user gets: every difference between a
[headless session](../../glossary.json#concept.headless-session) and an interactive one is handled
here, never in the [main-session guidance](../../glossary.json#concept.main-session-guidance).

## Core concepts

<a id="concept.headless-session"></a>

**[Headless session](../../glossary.json#concept.headless-session) and its rounds.** A headless
session is one main session run without a person, in one or more **rounds**: each round is one
`claude -p` process, the first given the developer's prompt and each later one continuing the same
session. A headless session is always a Claude Code session, since Concorde's main agent and task
sessions run on Claude Code only for now; the [workers](../../glossary.json#concept.worker) its
runs launch may still run on pi, as the project's
[worker configuration](../../glossary.json#concept.worker-configuration) chooses.

**The headless note and the test procedure.** A headless session differs from the developer's
interactive one only because of how it is run: `claude -p` ends its process, and every background
command with it, when the turn ends, and no notification reaches it afterwards. The tool tells the
session so in the **headless note** appended to its system prompt, and a headless main session also
receives the **test procedure**, which lets it carry each task out itself because a task session's
report would find no receiver. Both are described under
[What the session is told](#what-the-session-is-told).

**Unsettled runs and the wake.** The one thing an interactive session has and a headless one lacks
is being woken when a run ends. When a round ends, the runs it left running, or that the turn's end
stopped, are its **unsettled** runs; the tool waits for them and resumes the same session with a
**wake message** naming how each ended. A round with no unsettled run leaves the session **idle**,
and it ends.

**Live session.** A [live session](#live-sessions) keeps one main session's process running
instead of running it in rounds, so that what wakes it is its own program rather than the tool.

## Overview

One round and its wake, with every way the session ends. The session ends `idle`, `exited` when a
round's process fails (with its standard error kept), `no_session` when the first round names no
session, `rounds_exhausted` after the allowed rounds
([requirements](requirements.md#req.headless-sessions.rounds-bounded)), or `wait_exceeded` when a
run is still running after the wait limit.

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

The developer, or another part of End-to-end testing, runs

```text
python3 scripts/e2e/e2e.py session start <project> --prompt "<what the developer asks>" [--rounds 4]
python3 scripts/e2e/e2e.py session show <session directory>
```

`session start` keeps the session under `<project>/.concorde/runs/e2e/sessions/<time>/`: one
`round-<n>.jsonl` with the round's `stream-json` output and one `round-<n>.err` per round, and
`session.json` with the session identity, the prompt, each round's exit status, result, number of
tool calls and the runs it woke for, how the session ended and its final answer and cost. It
prints `session.json`. `session show` adds every round's tool calls and texts, read from the logs,
each tool call with its target: its command, its path or its skill. At most 4 rounds are allowed
unless `--rounds` says otherwise.

A headless workflow run of End-to-end testing, `run --via claude`, is a headless session of one
workflow prompt, kept under `.concorde/runs/e2e/<task>-claude/`, in which the session works as the
task's [task session](../../glossary.json#concept.task-session), and a [dogfood
scenario](../../glossary.json#concept.dogfood-scenario) runs its prompt as one, kept under its
scenario directory's `sessions/<time>/`, which the scenario runner passes in place of the default.

### What the session is told

A round is started with the main agent's tools granted on the command line (Bash, Read, Write,
Edit, Glob, Grep, Skill, TodoWrite, EnterWorktree and ExitWorktree, or a workflow's own list), since
an untrusted project's allow rules are ignored, with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, which
keeps a background workflow alive, and with the headless note appended to its system prompt: nobody
answers questions, a command left in the background is stopped when the turn ends and nothing wakes
the session, so Concorde commands run in the foreground, a run still running at the end of a round
is followed by a wake-up, and a task session's report would find no receiver
([requirements](requirements.md#req.headless-sessions.conditions-in-tool),
[tools granted](requirements.md#req.headless-sessions.tools-granted)). What the turn's end stops is
Claude Code's own background command; a Concorde run it was running then ends with the error code
`cancelled` and the session is woken for it as a run stopped by that end, while a
[detached run](../../glossary.json#concept.detached-run) outlives the round and wakes the session
when it ends (see [Waking the session](#waking-the-session)).

**The test-only exception.** The main agent hands every task to a task session and never works
inside a task worktree, but a headless main session cannot: a task session sends the main agent its
outcome with SendMessage, and the process of a `claude -p` round ends with its turn, long before
that message is sent, so it has no receiver. A headless main session exists only in the tests, so
Headless sessions gives it a procedure of its own instead of bending the main-session guidance: the
test procedure, appended after the headless note to every round of a headless main session. It says
that, for that test session only, it overrides the guidance's rule to hand every task to a task
session, and that the session carries each task out itself:

1. open the task from the primary worktree;
2. enter the task worktree with EnterWorktree;
3. work the task there with that worktree's own `concorde`, running every Concorde command in the
   foreground;
4. validate and deliver it with `concorde task-validation` and `concorde delivery`;
5. leave the worktree with ExitWorktree with action `keep`, so its worktree and branch stay;
6. merge the task from the primary worktree with `concorde task merge`.

Since nobody answers, it also tells the session to decide what it would otherwise ask the
developer or escalate, and to record each such decision in the task's
[decision log](../../glossary.json#concept.decision-log) with its reason and the options it
weighed. EnterWorktree and ExitWorktree are granted for it
([requirements](requirements.md#req.headless-sessions.claude-works-tasks)). The exception holds
for headless main sessions only: a headless workflow run works as a task session in the first
place and gets the note alone.

### Waking the session

When a round ends, the tool looks at the [runs](../../glossary.json#concept.run) of
[Operations](../../glossary.json#concept.operation) and
[execution commands](../../glossary.json#concept.execution-command) started since the session began
that it has not reported yet ([requirements](requirements.md#req.headless-sessions.wake-once)), in
the [run store](../../glossary.json#concept.run-store) of the session's project: the workspace
folders of the current tasks and `.concorde/unbound/` of the `.concorde` its
[workspace binding](../../glossary.json#concept.workspace-binding) names when the session runs in a
task worktree, otherwise of the worktree's own. Every run started there since the session began
counts as the session's, including the runs of the tasks it opened, whose workspace folders lie
in the same `.concorde`; a run another session started in the same project meanwhile would be
taken for this one's too.

A run whose [run progress file](../../glossary.json#concept.run-progress-file) is not finished and
whose runner lives is still running; a run whose result has the error code `cancelled` and was
written within 30 seconds of the round's end was stopped by that end. These runs are the round's
unsettled ones. If there are none, the session is idle and ends. Otherwise the tool waits until
every running run has finished or its runner has gone, then, when a round is left, resumes the same
session with a wake message. It names each run, its kind, name and workspace, how it ended and its
result file, saying of a stopped run that the turn's end stopped it and of a run whose runner went
without writing a result that it ended without one
([requirements](requirements.md#req.headless-sessions.wake)).

The wait lasts at most an hour: a run still running then fails the session with `wait_exceeded`
([requirements](requirements.md#req.headless-sessions.wait-bounded)). Before the failure goes up,
the tool writes `session.json` with the rounds so far, the end `wait_exceeded` and, under
`progress`, the path of that run's run progress file; the failure names the same file and the
session's `session.json`, so the kept session shows what outlived the wait.

### Live sessions

<a id="live-sessions"></a>

A round's process ends with its turn, so the tool stands in for every wake. A live session instead
keeps one main session's process running and feeds it prompts on standard input, so that what
wakes it is its own program: `claude -p --input-format stream-json --output-format stream-json
--verbose`, granted Bash and Read, which begins a turn of its own with a `task_notification` when
one of its background commands ends. It gets a short note appended to its system prompt: every
prompt is a step of a test, to be done exactly and answered briefly. Every event the process prints
is kept, with the time it arrived, as one line of `<name>.jsonl`, and its standard error as
`<name>.err`, under the directory the caller names. From these the tool tells when a prompted turn
ended (the `result` event), when a turn began (the `system` `init` event), which notifications
arrived and what a tool call printed. A turn that began, or a notification that arrived, while the
caller sent no prompt is a **wake**
([requirements](requirements.md#req.headless-sessions.live-own-wake)). Closing standard input ends
the session; what is left of it after 30 seconds is killed. The [owners
case](../module.md#owners-case) of End-to-end testing runs several live sessions at once.

### Reading the logs

A resumed round first replays the stopped background command as a turn of its own with no model
turn; its `result` event is not the round's answer. The round's result is the last `result` event
with a model turn, whose cost is the session's total so far.

## Why it is built this way

**Testing conditions stay in the tool.** Writing "run in the foreground" into the main-session
guidance would change what every user's main agent does to suit a test. The headless note is
appended by the tool instead, and the wake loop reproduces being woken when a run ends, so that what
is tested is the main agent's own judgment under the guidance users get.

**Why the main session works its tasks itself.** A task session sends its outcome with SendMessage
to the session name the main agent gave `--main`, and nothing in Concorde's files tells the tool
that it has sent it; with the round's process gone, that message is lost. Running the headless main
session as a background session, or reading the task session's report from its transcript, would
change how the driver runs Claude Code; the exception keeps `claude -p` rounds and gives up only
testing delegation, which a headless main session does not exercise. What it does test differs
from what a user's main agent does there: it works the task itself, as a task session would.

**Resuming, not restarting.** A wake resumes the same session, so the main agent keeps its whole
context, its decision log entries and its plan, exactly as an interactive session does when a
notification arrives. Each run is reported once; a session that keeps leaving runs behind is
bounded by the number of rounds, and a run that never ends by the wait limit, which fails with the
run's run progress file named.

**Files, not the model's words.** Whether a round left a run behind is read from Concorde's own
progress and result files, never from what the session said, because the session's text is the
thing under test. The 30-second window that separates a run the turn's end stopped from one the
session cancelled itself is a heuristic of the testing condition; a session that cancels a run in
its very last seconds is woken for it too, which only costs a round.

## Files

<a id="realization.headless-sessions.driver"></a>

The **session driver** is `scripts/e2e/sessions.py`: the command of a round, the environment, the
wake loop, the log reading and `session.json`. The `session` commands of `scripts/e2e/e2e.py`
call it. `scripts/e2e/live.py` holds the live sessions.

<a id="realization.headless-sessions.tests"></a>

The **session driver tests**, `tests/concorde/e2e/test_sessions.py`, check the command, the log
reading, which runs are unsettled and, with a stand-in for `claude -p`, a whole session that is
woken once, verifying the [requirements](requirements.md) and [scenarios](scenarios.md). The live
sessions are tested with the owners case, in `tests/concorde/e2e/test_owners.py`.

## Around it

<a id="uses-execution"></a>

**Execution** provides the run progress file and the [run
result](../../glossary.json#concept.run-result) of every run a session starts, and the run store
that holds them. The driver relies on the run progress file naming the run's kind, name, workspace,
phase and start time, on the [run lock](../../glossary.json#concept.run-lock) telling whether its
runner still lives, on the result carrying the status, summary and error code, and on a workspace
binding naming the `.concorde` of its runs, to decide which runs are unsettled and to write the wake
message; it never changes any of them.

Claude Code is external: the driver relies on `claude -p` with `--resume`,
`--append-system-prompt`, `--allowedTools` and `stream-json` output, whose events carry the
session identity, and a live session on `--input-format stream-json` besides.
