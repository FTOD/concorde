# Task sessions

## Purpose

Task sessions is how the main agent delegates the task level of the work: when it splits work into
several tasks it starts a task session per task, a session of its own agent program working inside
that task's worktree while the main agent stays in the primary worktree. Task sessions starts,
confines and follows those sessions: on Claude Code a background session, on pi a sequence of
headless rounds on one session file, each ending with a report the task record confirms. The main
agent relies on it to run tasks in parallel under a boundary that keeps each session's writes
inside its task. It does not decide how work is split, never merges or closes a task, and does not
tell a session how to work in a task; that method is the main agent's own, given by the
[Main session](../main-session/module.md) guidance, and the session follows it at a smaller scale.
Its boundary guards against mistakes, not a malicious session.

## Terminology

| Term | Definition |
| --- | --- |
| Session round | One headless run of a pi task session, from its prompt (the task at the start, or the main agent's answer) to its session report, a failure or a stop; a pi task session is a sequence of rounds on one pi session file. |
| Session report | The structured report with which a pi task session ends a session round: delivered with the delivery commit, or escalated with the escalations it recorded, plus its summary, decisions and open points. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../../vocabulary.md#concept.concorde.task-session) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Task](../../tasks/module.md#concept.tasks.task) | |
| [Task record](../../tasks/module.md#concept.tasks.task-record) | |
| [Decision log](../../tasks/module.md#concept.tasks.decision-log) | |
| [Session boundary](../../harness/module.md#concept.harness.session-boundary) | |
| [Worker backend](../workers/module.md#concept.workers.backend) | |

## Usage

The task level of the work is normally played by the main agent itself: it enters the task
worktree, works there and leaves after delivery. Only when it wants several tasks to run at once
does it delegate: from the primary worktree it starts a
[task session](../../vocabulary.md#concept.concorde.task-session) per task. A task session runs on
the main session's own agent program, read from the environment as Workers reads the default
[worker backend](../workers/module.md#concept.workers.backend) (`CONCORDE_CLIENT`, `CLAUDECODE=1`,
pi's session variables); a command started from neither is refused with `client_unknown`, naming
each variable it looked at. It never runs on the other program: a task session does the main
agent's own task-level work at a smaller scale, so it keeps the main agent's program and
configuration.

```text
concorde task session severity --main concorde-7d      # start one
concorde task session severity --answer "<answer>"     # pi: start the next round
concorde task session severity --stop                  # pi: stop the running round
```

The command belongs to the `concorde task` family, which [Tasks](../../tasks/module.md) runs: its
command line checks that it runs in the primary worktree, reads the main session's program and
checks the options, and Task sessions does the rest. What Task sessions writes for a session goes
under `.concorde/tasks/<task>.session/` of the primary worktree, next to the task record, and the
started session and each round are recorded in the
[task record](../../tasks/module.md#concept.tasks.task-record) through Tasks.

**In Claude Code**, Task sessions writes the session's
[session boundary](../../harness/module.md#concept.harness.session-boundary) — a settings file and
the Harness's task-session write hook with the task's paths embedded — under
`.concorde/tasks/severity.session/`, starts `claude --bg` in the task worktree
with the task-session guidance and the task's goal, Modules, decision log and the main agent's
session name as its first prompt, and appends the started session to the record. `--main` is
required. `--dry-run` writes the boundary and prints the command without starting anything. A task
that is closed or failed, a missing worktree, or a Claude Code that does not report a started
background session is refused (`task_closed`, `missing_worktree`, `session_failed`) with Claude
Code's output in the detail. `--answer` and `--stop` are refused (`invalid_input`): a Claude Code
task session receives the main agent's answers through SendMessage and is stopped with
`claude stop`.

<a id="concept.task-session.round"></a><a id="concept.task-session.report"></a>

**In pi**, which has neither background sessions nor messages between sessions, a task session is
a sequence of **session rounds** on one pi session file. Task sessions writes the boundary under
`.concorde/tasks/severity.session/` — the Harness's task-session extension as `boundary.ts` with the
task's paths embedded, beside the path decisions it imports — and starts a detached supervisor
process that runs one round: `pi -p --mode json --approve` in the task worktree with the
developer's own pi configuration (packages, extensions, settings, credentials and context files,
and the task worktree's project resources, which `--approve` trusts for that run), the boundary
loaded with `-e`, the session file under `pi/` of that directory, and `--model` when given. The
first round's prompt is the task-session guidance for pi followed by the task's goal, Modules and
decision log; `--main`, when given, is only recorded. A round ends when the session calls
`concorde_report` with its **session report** ([contract](contracts.md#contract.task-session.report)),
when pi exits without one, or when `--stop` ends it: the supervisor sends the round's pi process
group SIGTERM, so pi ends its session and sandbox-runtime removes its sockets and bridge, and
SIGKILL to what is left of the group 3 seconds later. Meanwhile the supervisor keeps the round's
progress file `status.json` in that directory current — the round, its phase and the session's
latest tool call — and writes pi's event stream and standard error beside it. It then records the
round's outcome in the task record:

| Outcome | When |
| --- | --- |
| `delivered` | the report says delivered and names a delivery commit the task record holds |
| `escalated` | the report says escalated and names escalations the task record holds with the level `task-session` |
| `failed` | pi exited without a report, or the report names a commit or an escalation the record does not hold; the round's `error` is a link naming pi's exit code, stop reason and error message, the logs, and each mismatch |
| `stopped` | `--stop` ended the round |

The main agent answers an escalation, or asks for more after a delivery, with `--answer`: Task
sessions starts the next round on the same session file, so the session continues with its whole
context and the answer as its prompt. `--answer` is refused while a round runs (`session_busy`) or
when the task has no pi session (`no_session`), and `--stop` when no round runs (`session_idle`). A
start while a round runs is refused with `session_busy`; after the last round ended, a start begins
a new session. `--dry-run` writes the boundary and prints the command without starting anything. A
task that is closed or failed, a missing worktree, a missing program (`pi`, and on Linux `bwrap`
and `socat`) or sandbox-runtime package, or a supervisor that does not start is refused
(`task_closed`, `missing_worktree`, `session_failed`), naming everything that is missing, and
leaves the record unchanged.

A task session escalates what it may not decide with `concorde task escalate --by task-session`,
which Tasks records as a link of level `task-session` on top of the failed runs' chains; the main
agent adds its own link above it when the developer must decide. Exact commands and error codes
are in the [contracts](contracts.md), the obligations in the [requirements](requirements.md) and
the behaviour in the [scenarios](scenarios.md).

## Design

A task session is not a level of its own but the task level delegated. The main agent and a task
session work a task the same way, and the differences all follow from the delegation: a task
session has a write boundary while the main agent has none, it escalates to the main agent while
the main agent escalates to the developer, it has a start, rounds and a stop, and it never merges.
Keeping its program and configuration the main agent's is what makes it the same work: an isolated
configuration, such as a worker gets, would give it other tools and instructions than the main
agent that would otherwise do the task.

### Its place in the five levels

A task session plays level 2 of Concorde's [five levels](../../module.md#the-five-levels), the task
level, in place of the main agent. Only the main agent at level 1 calls this Module, with
`concorde task session` from the primary worktree; the call arrives through Tasks, whose command
line checks the task and the main session's program before handing it here. Task sessions then
starts one agent session in the task worktree, and that session, not this Module, does the task's
work: following its guidance, it changes Specs and code, starts workflows (level 3) and runs
Operations (level 4) inside its task, and never reaches a worker except through an Operation. Its
results go up to level 1 only, never to the developer: a Claude Code session reports to the main
agent with SendMessage, and a pi session ends each round with a session report that this Module
checks against the task record and records there, where the main session's run view finds it. What
the session may not decide it escalates with `concorde task escalate --by task-session`, a link of
level `task-session` on top of the failed runs' chains, for the main agent to decide or to pass on
with its own link.

How a pi task session travels over time, from the main agent's start to its answer:

```d2 illustrative
shape: sequence_diagram
main: Main agent (level 1)
tasks: Tasks
starter: Session starter
session: pi task session (level 2)
main -> tasks: concorde task session <task>
tasks -> starter: start, after Tasks' checks
starter -> starter: write the session boundary
starter -> session: round 1: guidance, goal, Modules, decision log
session -> session: work the task: workflows, Operations, delivery
session -> starter: concorde_report {style.stroke-dash: 3}
starter -> tasks: check the report, record the outcome
starter -> main: outcome, shown by the run view {style.stroke-dash: 3}
main -> tasks: concorde task session <task> --answer
tasks -> starter: next round on the same session file
```

### The session boundary

The session boundary guards against mistakes, not a malicious session. In Claude Code it costs
only generated settings (see the [Harness](../../harness/module.md#concept.harness.session-boundary)
for what they hold). Nobody answers permission prompts in a background session, so it runs in
Claude Code's `auto` mode: a classifier approves or refuses each action instead of asking, an
extra check inside the hook and sandbox, which stay the boundary. `bypassPermissions` would skip
that check, and Claude Code starts a background session in it only after the developer accepted a
disclaimer once. A model without `auto` mode would fall back to asking and stall, so `--model` must
name one that has it. Reads stay open, because the session needs the whole project's context, and
so does the network: a command that did not foresee a host fails, sometimes only partly, as when a
package manager falls back to its cache or Git cannot fetch an object of a partial clone, and
keeping the network closed would guard against exfiltration, which is outside what this boundary is
for. Claude Code's sandbox keeps the repository's `.git/config` and Git's hooks read-only inside
the writable Git directory, since writing them could run code outside the sandbox; a session
commits but cannot register a submodule, so the main agent prepares that before starting it.

A pi task session's boundary is loaded on top of the developer's pi configuration. It intercepts
the tools rather than replacing them, so the developer's own extensions keep theirs; tools other
extensions add, such as MCP tools or a formatter that writes files, are outside this boundary, as
MCP tools are outside the Claude Code session's write hook. pi has no counterpart of Claude Code's
`auto` classifier, so the extension and the sandbox are the whole boundary, which is enough for
what it guards against. A sandbox makes only existing paths writable, so Task sessions creates the
writable directories that do not exist yet, such as a first run's `.concorde/runs/`, before a
session starts, in Claude Code as in pi. Concorde's main-session extension, which the task worktree
may load as a project resource, stays inactive when `CONCORDE_TASK_SESSION` is set, so a task
session neither starts background runs nor watches the project's runs as a main session does.

### Rounds instead of messages

Rounds stand in for messages because pi sessions share no channel and a headless `pi -p` ends when
its agent stops: the session reports once per round through a tool whose arguments follow a
contract, and the main agent's answer starts the next round with `--session-id` on the same session
file. The report is checked against the task record rather than trusted, so a delivery or an
escalation the record does not hold makes the round `failed`. The supervisor is detached from the
command that started it, so closing the main session never ends a round, and a main session that
starts again finds the running rounds from their progress files.

### Inside

```d2
tasksession: Task sessions {
  starter: Session starter {
    "session.py"
    "pi_session.py"
  }
  round: Session round
  report: Session report
  starter -> round: runs and records
  round -> report: ends with
}
```

<a id="realization.task-session.starter"></a>

The **session starter** holds the Claude Code start (`session.py`), which assembles the session's
writable paths and settings and starts `claude --bg`, and the pi task session's rounds and
supervisor (`pi_session.py`), which assembles the pi boundary's policy, runs each round and records
its outcome. The boundary files themselves, the task-session write hook and the pi boundary
extension with its path decisions, are the [Harness](../../harness/module.md)'s. The tests
(`test_session.py`, `test_pi_session.py` and the fake pi session `fake_pi_session.py` under
`tests/concorde/tasks/`) run on real Git repositories with a fake `claude` and a fake `pi`; the pi
path decisions also run under Node.

### Around it

A start touches one piece of each provider: the session starter reads the program the way Workers
does, writes the Harness's boundary, prompts the session with the Main session's guidance and
records in the Tasks record, against which each session report is checked.

```d2
starter: Session starter
report: Session report
guidance: Main session / Main-session guidance
boundary: Harness / Session boundary
backend: Workers / Worker backend
record: Tasks / Task record
starter -> guidance: prompts with
starter -> boundary: writes
starter -> backend: reads the program as
starter -> record: records rounds in
report -> record: is checked against
```

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../tasks/module.md#concept.tasks.task) a session works in — its
worktree, [record](../../tasks/module.md#concept.tasks.task-record) and
[decision log](../../tasks/module.md#concept.tasks.decision-log) — and the `concorde task` command
that dispatches `session` here after checking that it runs in the primary worktree. Task session
records a started session and each round's start and end only through Tasks' record updates, and
relies on the record holding every delivery and escalation, which is what it checks a session
report against. Tasks refusing an update refuses the start or ends the round `failed` with Tasks'
link as its cause.

<a id="uses-harness"></a>

The **Harness** writes the [session boundary](../../harness/module.md#concept.harness.session-boundary):
the task-session write hook for Claude Code and the pi boundary extension with its path decisions,
from the writable paths Task sessions assembles. Task sessions relies on it confining the session's
file tools and shell to those paths and leaving reads and the network open; it never widens the
paths it hands over. The boundary is written before the session starts, and `--dry-run` writes it
without starting anything, so no session runs without its boundary.

<a id="uses-workers"></a>

**Workers** tells how the main session's program is read from the environment
([worker backend](../workers/module.md#concept.workers.backend)) and where the sandbox-runtime
package is installed, which a pi task session needs as a worker does. Task sessions reads the
program the same way so that a task session and a worker started from the same main session agree;
unlike a worker, a task session never takes a program from the worker model configuration, and a
command from neither program is refused with `client_unknown`.

<a id="uses-main-session"></a>

**Main session** provides the
[guidance](../main-session/module.md#concept.main-session.guidance) a task session starts with: the
rendered task-session guidance for Claude Code or pi, which carries the same rules for working
inside a task that the main agent follows. A missing rendered guidance refuses the start with
`session_failed`.

Two Modules call this one, both from level 1's side: the Main session's guidance and pi run view
start, answer and follow task sessions, and Tasks dispatches `concorde task session` here after its
own checks. Neither relies on anything but the recorded outcome of each start and round.
