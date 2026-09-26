# Headless sessions

## Purpose

Headless sessions drives a real Claude Code main session in a test project without a person, so
that End-to-end testing can watch what a main agent actually does with Concorde. It starts the
session, grants it its tools, tells it the conditions of running headless, wakes it when an
Operation run it left behind ends, keeps every round's log and reads the logs back. It exists for
the people developing Concorde and changes nothing a user gets: every difference between a
headless session and an interactive one is handled here, never in the main-session guidance.
It drives Claude Code only; a headless pi main session is not supported yet.

## Terminology

| Term | Definition |
| --- | --- |
| Headless session | A `claude -p` main session in a test project, run by the tool in one or more rounds and kept in a session directory. |
| Round | One `claude -p` process of a headless session, the first with the developer's prompt and each later one resuming the same session with a wake message. |
| Headless note | The system prompt the tool appends to every round, telling the session that nobody answers, that background commands stop at the end of its turn, and that it will be woken. |
| Wake message | The message a later round resumes the session with, naming each Operation run the previous round left running or stopped, as the notification an interactive session receives. |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Operation result](../../operations/module.md#concept.operations.result) | |
| [Operation progress file](../../operations/module.md#concept.operations.progress-file) | |

A headless session is made of rounds; the headless note is given to every round, and a wake
message starts every round but the first.

## Usage

<a id="concept.headless-sessions.session"></a><a id="concept.headless-sessions.round"></a>

**Running a session.** The developer, or another part of End-to-end testing, runs

```text
python3 scripts/e2e/e2e.py session start <project> --prompt "<what the developer asks>" [--rounds 4]
python3 scripts/e2e/e2e.py session show <session directory>
```

`session start` keeps the session under `<project>/.concorde/runs/e2e/sessions/<time>/`: one
`round-<n>.jsonl` with the round's `stream-json` output and one `round-<n>.err` per round, and
`session.json` with the session identity, the prompt, each round's exit status, result, number of
tool calls and the runs it woke for, how the session ended and its final answer and cost. It
prints `session.json`. `session show` adds every round's tool calls and texts, read from the logs.
A headless workflow run of End-to-end testing, `run --via claude`, is a headless session of one
workflow prompt, kept under `.concorde/runs/e2e/<task>-claude/`, and a dogfood scenario runs its
prompt as one.

<a id="concept.headless-sessions.note"></a>

**What the session is told.** Every round is started with the main agent's tools granted on the
command line (Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite, EnterWorktree and
ExitWorktree, or a workflow's own list), since an untrusted project's allow rules are ignored, with
the environment variable that keeps a background workflow alive, and with the **headless note**
appended to its system prompt: nobody answers questions, a command left in the background is
stopped when the turn ends and nothing wakes the session, so Concorde commands run in the
foreground, and a run still running at the end of a round is followed by a wake-up
([requirements](requirements.md#req.headless-sessions.conditions-in-tool)).

<a id="concept.headless-sessions.wake"></a>

**Waking the session.** When a round ends, the tool looks at the Operation runs started since the
session began that it has not reported yet
([requirements](requirements.md#req.headless-sessions.wake)). A run whose progress file is not
finished and whose host lives is still running; a run that ended `cancelled` with its result
written within 30 seconds of the round's end was stopped by that end. If there is neither, the
session is **idle** and ends. Otherwise the tool waits until every running run has finished or its
host has gone (at most an hour), then resumes the same session with a **wake message** naming each
run, its Operation and task, how it ended and its result file, saying of a stopped run that the
turn's end stopped it. The session ends `idle`, `exited` when a round's process fails (with its
standard error kept), `no_session` when the first round names no session, or `rounds_exhausted`
after the allowed rounds.

**Reading the logs.** A resumed round first replays the stopped background command as a turn of
its own with no model turn; its `result` event is not the round's answer. The round's result is
the last `result` event with a model turn.

## Design

**Testing conditions stay in the tool.** A headless session differs from the developer's
interactive one only because of how it is run: `claude -p` ends its process, and every background
command with it, when the turn ends, and no notification reaches it afterwards. Writing "run in
the foreground" into the main-session guidance would change what every user's main agent does to
suit a test. The headless note is appended by the tool instead, and the wake loop reproduces the
one thing the interactive session has and the headless one lacks, being woken when a run ends, so
that what is tested is the main agent's own judgment under the guidance users get.

**Resuming, not restarting.** A wake resumes the same session, so the main agent keeps its whole
context, its decision log entries and its plan, exactly as an interactive session does when a
notification arrives. Each run is reported once; a session that keeps leaving runs behind is
bounded by the number of rounds, and a run that never ends by the wait limit, which fails with
the run's progress file named.

**Files, not the model's words.** Whether a round left a run behind is read from Concorde's own
progress and result files, never from what the session said, because the session's text is the
thing under test. The 30-second window that separates a run the turn's end stopped from one the
session cancelled itself is a heuristic of the testing condition; a session that cancels a run in
its very last seconds is woken for it too, which only costs a round.

How Headless sessions is built:

```d2
sessions: Headless sessions {
  driver: Session driver {
    "sessions.py"
  }
}
```

<a id="realization.headless-sessions.driver"></a>

The **session driver** is `scripts/e2e/sessions.py`: the command of a round, the environment, the
wake loop, the log reading and `session.json`. The `session` commands of `scripts/e2e/e2e.py`
call it.

<a id="realization.headless-sessions.tests"></a>

The **session driver tests**, `tests/concorde/e2e/test_sessions.py`, check the command, the log
reading, which runs are unsettled and, with a stand-in for `claude -p`, a whole session that is
woken once, verifying the [requirements](requirements.md) and [scenarios](scenarios.md).

## Relationships

```d2
sessions: Headless sessions
operations: Operations
sessions -> operations
```

<a id="uses-operations"></a>

**Operations** provides the [Operation progress
file](../../operations/module.md#concept.operations.progress-file) and the [Operation
result](../../operations/module.md#concept.operations.result) of every run a session starts. The
driver relies on the progress file naming its Operation, task, phase, host process and start time,
and on the result carrying the status, summary and error code, to decide which runs are unsettled
and to write the wake message; it never changes either.

Claude Code itself is external: the driver relies on `claude -p` with `--resume`,
`--append-system-prompt`, `--allowedTools` and `stream-json` output, whose events carry the
session identity.
