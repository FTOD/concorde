# Task sessions

## Purpose

Task sessions is how the [main agent](../../glossary.json#concept.main-agent) delegates the task
level of the work: it starts a task session for every task, a background session of the main
agent's own program working inside that task's worktree while the main agent stays in the primary
worktree. For now that program is Claude Code, the only one a main agent runs on, while the
[workers](../../glossary.json#concept.worker) of the runs a task session starts may run on pi. Task
sessions starts, confines and ends those sessions. The main agent relies on it to have every task
worked, one or several at once, under a boundary that keeps each session's writes inside its task.
It does not decide how work is split, never merges a task into the primary branch or closes it, and
does not tell a session how to work in a task; that method is the main agent's own, given by the
[Main session](../main-session/module.md) guidance, and the session follows it at a smaller scale.
Its boundary guards against mistakes, not a malicious session.

Task sessions matter to the developer only through the main agent: the developer talks to main
sessions, and a task session is a means of the main agent that has served its purpose once its
task ends. So Task sessions also ends them with their task: a task session still running when a
task is closed without a merge is stopped first, and once a task has ended, each of its task
sessions is removed from Claude's session list, where finished task sessions would otherwise pile
up beside the developer's main sessions, after its transcript has been kept in the task's trace,
which moves to the history with the task.

## Core concepts

A **[task session](../../glossary.json#concept.task-session)**, a term of the root, is not a level
of its own but the task level delegated, and the main agent delegates every task. Keeping the main
agent out of task worktrees keeps it free to talk with the developer and to answer every session
while tasks run, and puts every task under a write boundary, which the main agent itself does not
have. A task session escalates to the main agent while the main agent escalates to the developer, it
has a start and ends with its task, and it never merges its task into the primary branch; the one
merge it makes is the primary branch into its task branch when the main agent answers a merge
conflict, a change inside its own worktree and branch. It runs on the main agent's own program and
configuration, because it does the main agent's own task-level work at a smaller scale: an isolated
configuration, such as a worker gets, would give it other tools and instructions than the main
agent's.

Its **[session boundary](../../glossary.json#concept.session-boundary)**, a term of the Harness, is
the settings and write hook that confine what its own file tools and shell write to its task while
leaving reads and the network open.

## Overview

### A task session's life

The task level of the work is always delegated: the main agent never works inside a task worktree
but, from the primary worktree, starts a [task session](../../glossary.json#concept.task-session)
for every task, even a single one, after recording the task's brief in its
[decision log](../../glossary.json#concept.decision-log). How a task session travels over time, from
the main agent's start to the end of its task:

```d2 illustrative
grid-columns: 4
horizontal-gap: 110
main: "Main agent\nlevel 1, primary worktree" {
  grid-columns: 1
  vertical-gap: 50
  start: "concorde task session\n<task> --main <session>"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  answer: "Read the report,\nanswer every escalation\nat once"
  end: "concorde task merge\nor task close"
}
tasks: Tasks {
  grid-columns: 1
  vertical-gap: 50
  check: "Check the primary\nworktree, the task\nand the options"
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  record: "Record the session\nin the task's trace"
  g3: "" {style.opacity: 0}
  close: "Close the task"
}
starter: "Session starter" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  boundary: "Write the session\nboundary and the\nMCP configuration"
  launch: "claude --bg: guidance,\ngoal, Modules,\ndecision log"
  g2: "" {style.opacity: 0}
  g3: "" {style.opacity: 0}
  stop: "Stop its sessions,\nkeep their transcripts,\nremove them"
}
session: "Task session\nlevel 2, task worktree" {
  grid-columns: 1
  vertical-gap: 50
  g1: "" {style.opacity: 0}
  g2: "" {style.opacity: 0}
  work: "Work the task:\nworkflows, Operations,\ndelivery"
  g3: "" {style.opacity: 0}
  report: "SendMessage: delivered,\nor every escalation"
  g4: "" {style.opacity: 0}
}
main.start -> tasks.check
tasks.check -> starter.boundary: checks passed
starter.boundary -> starter.launch
starter.launch -> session.work: starts
starter.launch -> tasks.record
session.work -> session.report
session.report <-> main.answer: "the report,\nevery answer"
main.answer -> main.end: delivered
main.end -> tasks.close
tasks.close -> starter.stop
```

The main agent starts the session through `concorde task session`, which Tasks checks before it
hands the start here. Task sessions writes the session's boundary, starts it in the task worktree
with its first prompt and records it in the task's [trace](../../glossary.json#concept.trace). The
session then works the task following its guidance and reports to the main agent with SendMessage:
its delivery, or every decision it needs, which the main agent answers together the same way. When
the main agent merges or closes the task, Tasks' close has Task sessions stop the task's sessions if
the task ends without a merge, keep their transcripts and remove them from Claude's session list.

### Its place in the levels of work

A task session plays level 2 of Concorde's [levels of work](../../module.md#the-levels-of-work), the
task level, in place of the main agent. Only the main agent at level 1 calls this
[Module](../../glossary.json#concept.module), with `concorde task session` from the primary
worktree; the call arrives through Tasks, whose command line checks the task and the options before
handing it here. Task sessions then starts one agent session in the task worktree, and that
session, not this Module, does the task's work: following its guidance, it changes Specs and code,
starts workflows (level 3) and runs Operations and
[execution commands](../../glossary.json#concept.execution-command) (level 4) inside its task
worktree, and never reaches a worker except through an Operation. Its results go up to level 1
only, never to the developer: the session reports to the main agent with SendMessage. What the
session may not decide it escalates with `concorde task escalate --by task-session`, a link of level
`task-session` on top of the failed runs' chains, for the main agent to decide or to pass on with
its own link.

```d2 illustrative
main: Main session
module: Task sessions
tasksession: "Task session (agent, level 2)"
workflows: Workflows
runs: "Runs: Operations and execution commands"
workers: Workers
main -> module: starts
module -> tasksession: starts in its task worktree
tasksession -> workflows: starts in its task worktree
tasksession -> runs: starts in its task worktree
workflows -> runs: runs one at a time
runs -> workers: an Operation launches
```

## Starting a session

```text
concorde task session severity --main concorde-7d
```

The command belongs to the `concorde task` family, which [Tasks](../tasks/module.md) runs: its
command line checks that it runs in the primary worktree and checks the options, and Task sessions
does the rest. What Task sessions writes for a session goes into the task's folder of the primary
worktree: the session's boundary configuration under `runtime/`, which the close removes with the
folder, and the session's [trace node](../../glossary.json#concept.trace-node) under
`sessions/<session>/`, written through Tasks' updates so the task's
[trace](../../glossary.json#concept.trace) holds every session.

Task sessions writes the session's
[session boundary](../../glossary.json#concept.session-boundary) — a settings file and the Harness's
task-session [write hook](../../glossary.json#concept.write-hook) with the task's paths embedded —
under `.concorde/tasks/severity/runtime/`, with an MCP configuration `mcp.json` there that gives
the session the [project MCP server](../../glossary.json#concept.project-mcp-server), starts
`claude --bg` in the task worktree with that configuration and the task-session guidance and the
task's goal, Modules, decision log and the main agent's session name as its first prompt, and
records the started session as a node `sessions/<id>/` of the task's trace, with status `unknown`,
since nothing tells Concorde when a Claude Code session ends. `--main` is required: a start without
it is refused with `invalid_input`. `--dry-run` writes the boundary and prints the command without
starting anything. A task that is closed or failed, a missing worktree, or a Claude Code that does
not report a started background session is refused (`task_closed`, `missing_worktree`,
`session_failed`) with Claude Code's output in the detail. The session receives the main agent's
answers and sends its reports through SendMessage; `claude stop` stops it.

The server is passed explicitly because a background session does not load the project-scoped
`.mcp.json` of a folder nobody trusted. It comes without a channel, and its configuration says so
(`CONCORDE_CHANNEL=0`): Claude Code does not wake a background session with channel events. A
probe on 2026-09-29 (Claude Code 2.1.284) started a `claude --bg` session with
`--dangerously-load-development-channels server:concorde`; the server loaded and registered a wait
on a held [merge lock](../../glossary.json#concept.merge-lock), and when the lock was released the
idle session was never woken. So `register_wait` answers a task session with the `concorde task
wait` command, which it runs in background Bash and is woken by when it returns. The server runs as
every MCP server does, outside the Bash sandbox, and its tools may change any task's record: the
developer accepted that a task session can reach the task management tools, which are no boundary,
so the guidance, not the boundary, keeps a task session from merging or closing its task.

## The session boundary

A task session may write only what working its task needs: with its file tools, the task worktree
and the task's decision log; with its shell, also the repository's Git directory, where its commits
on the task branch are written, the task's own folder `.concorde/tasks/<task>/` of the primary
worktree, which holds the workspace folder the task worktree's
[workspace binding](../../glossary.json#concept.workspace-binding) names for every run started
there, including the [workflow record](../../glossary.json#concept.workflow-record), and the task's
record and trace, where `concorde task escalate` records its escalations, the primary worktree's
`.concorde/locks/`, where those runs take the
[workspace lock](../../glossary.json#concept.workspace-lock) and their
[run locks](../../glossary.json#concept.run-lock), and the user's package caches. Reads and the
network stay open. The shell's sandbox reaches the network through a proxy of its own on
`localhost`, named in the proxy variables of the commands it runs, since those commands have a
network namespace holding only a loopback interface; the workers of the Operations a session starts
pass that proxy on ([Workers' proxy rule](../../execution/workers/launch.md#proxy)), so they reach
their model endpoints, one on `localhost` included, as a main session's workers do, while their own
tools keep no network.

The session boundary guards against mistakes, not a malicious session. It costs only generated
settings (see the [Harness](../../glossary.json#concept.session-boundary) for what they hold).
Nobody answers permission prompts in a background session, so it runs in Claude Code's `auto` mode:
a classifier approves or refuses each action instead of asking, an extra check inside the hook and
sandbox, which stay the boundary. `bypassPermissions` would skip that check, and Claude Code starts
a background session in it only after the developer accepted a disclaimer once. A model without
`auto` mode would fall back to asking and stall, so `--model` must name one that has it. Reads stay
open, because the session needs the whole project's context, and so does the network: a command
that did not foresee a host fails, sometimes only partly, as when a package manager falls back to
its cache or Git cannot fetch an object of a partial clone, and keeping the network closed would
guard against exfiltration, which is outside what this boundary is for. Claude Code's sandbox keeps
the repository's `.git/config` and Git's hooks read-only inside the writable Git directory, since
writing them could run code outside the sandbox; a session commits but cannot register a submodule,
so the main agent prepares that before starting it. While a sandboxed background command of a
session lives, its sandbox also keeps placeholder files in the task worktree and holds the
repository's `.git/config.lock`, which blocks the session's own `task-validation` and every other
task's preparation; so the guidance has a task session stop every background command it started
before `task-validation` and `delivery`, and never wait by polling, whose loop may never end.

Tools that MCP servers add are outside the write hook, which guards Edit and Write only. A sandbox
makes only existing paths writable, so Task sessions creates the writable directories that do not
exist yet, such as the task's `.concorde/locks/`, before a session starts.

## When the task ends

<a id="ending-claude-sessions"></a>

Tasks' close hands its task sessions, every one the task's trace lists, to Task sessions at three
points:

- A close without a merge (`--completed` or `--failed`) first runs `claude stop <id>` for each, so
  no session goes on working in the worktree the close removes or starts another run there; a
  session already ended or no longer known to Claude Code (`No job matching`) counts as stopped.
  When a stop cannot be confirmed, the close is refused with `session_stop_failed` before it
  changed the task, naming the session, Claude Code's answer and the command to stop it by hand.
- Every close, a merge's included, copies each session's transcript into the session's trace node
  just before the task's folder moves to the history: Claude Code's
  `projects/<the worktree's path with every character that is no letter or digit as ->/<session
  uuid>.jsonl` of its configuration folder (`$CLAUDE_CONFIG_DIR`, by default `~/.claude`), found as
  the only `<id>*.jsonl` of that project folder, or else of any project folder, becomes
  `transcript.jsonl`, an artifact of the node, and the folder Claude Code keeps beside it, with
  subagent transcripts and long tool results, becomes `transcript/`. The history thus keeps each
  session's conversation, and is never written after the move.
- Once the task is closed, `claude rm <id>` removes each session whose transcript was kept from
  Claude's session list. It kills a session that still runs and deletes Claude Code's own state of
  the job, and it removes a worktree only when Claude Code created it for the session, never the
  task worktree a task session is started in. The removal is best effort: a failing `claude rm`, or
  a transcript that could not be kept, whose session is then left in the list so nothing of it is
  lost, never fails the close, and the close's `warnings` name the session, the whole reason and
  the command that removes it by hand.

## Escalating

A task session escalates what it may not decide with `concorde task escalate --by task-session`,
which Tasks records as a link of level `task-session` on top of the failed runs' chains; the main
agent adds its own link above it when the developer must decide. A task never asks the developer
in place: the session gathers every decision it needs, records each as an escalation and reports
them together, in one SendMessage, and the main agent answers them together. Exact commands and
error codes are in the [contracts](contracts.md), the obligations in the
[requirements](requirements.md) and the behaviour in the [scenarios](scenarios.md).

## What the started session relies on

These three collaborations are the started session's, which follows its guidance; Task sessions
itself starts no workflow or run and owes them nothing.

<a id="uses-workflows"></a>

**Workflows** is level 3, which a task session may start for its task when the work follows a known
procedure. The session starts a [workflow](../../glossary.json#concept.workflow) for its own task
only, in the [mode](../../glossary.json#concept.workflow-mode) its brief names, interactive when it
names none. An interactive workflow ends at its first
[decision point](../../glossary.json#concept.decision-point) not yet settled, and since nobody
answers the session in place, it escalates every pending point of that step at once, with the
workflow result as the cause, and starts the workflow again with the main agent's answers; a no-ask
workflow decides those points itself and reports every decision at the end. The session relies on
the [workflow result](../../glossary.json#concept.workflow-result) listing those decisions and
keeping every step's [error chain](../../glossary.json#concept.error-chain) whole. It copies the
decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log),
gives the decisions in its own report, and escalates to the main agent what needs the developer: a
result that is not `ok` and that it cannot repair within the task, with its own link above the
result's chain, and a decision of major impact a no-ask workflow took, which carries no error, with
its own link alone. The workflow never merges or closes the task, which stays the main agent's.

<a id="uses-execution"></a>

**Execution** is level 4, which a task session runs directly whenever no workflow fits: an
[Operation](../../glossary.json#concept.operation) with `concorde run`, or the execution commands
`concorde task-validation` and `concorde delivery`, always inside its task worktree with the
worktree's own `concorde`. Every run reads the worktree's
[workspace binding](../../glossary.json#concept.workspace-binding), which Tasks wrote when the task
opened, so it works on the task's goal and Modules without naming the task, and holds the workspace
lock, so two runs of one task never overlap. The session relies on each
[run result](../../glossary.json#concept.run-result) separating what the runner verified from what a
worker claimed. A failed result is either repaired within the task, by a changed
[Spec](../../glossary.json#concept.spec) or code and a new run, or escalated with the result's chain
unchanged beneath the session's link. The session reaches a worker only through an Operation and
never starts a worker or another agent itself.

<a id="uses-operations"></a>

**Operations** provides the catalog of the Operations a task session may run in its task, the same
the main agent would run, with the same arguments.

## Inside and around it

```d2
tasksession: Task sessions {
  starter: Session starter {
    "session.py"
  }
}
```

<a id="realization.task-session.starter"></a>

The **session starter** (`session.py`) assembles the session's writable paths and settings and
starts `claude --bg`, and ends a task's task sessions: their stop, the copy of their transcripts and
their removal, which Tasks' close calls. The boundary files themselves, the task-session write hook
among them, are the [Harness](../../harness/module.md)'s. The tests (`test_session.py` under
`tests/concorde/tasks/`) run on real Git repositories with a fake `claude`.

A start touches one piece of each provider: the session starter writes the Harness's boundary,
prompts the session with the Main session's guidance and records the session in the task's trace
through Tasks.

```d2
starter: Session starter
guidance: Main session / Main-session guidance
boundary: Harness / Session boundary
task: Tasks / Task
starter -> guidance: prompts with
starter -> boundary: writes
starter -> task: records sessions in the trace of
```

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../glossary.json#concept.task) a session works in — its
worktree, [record](../../glossary.json#concept.task-record) and
[decision log](../../glossary.json#concept.decision-log) — and the `concorde task` command
that dispatches `session` here after checking that it runs in the primary worktree. Task sessions
records a started session only through Tasks' record updates; Tasks refusing the update refuses
the start.

<a id="uses-harness"></a>

The **Harness** provides the sources of the
[session boundary](../../glossary.json#concept.session-boundary): the task-session write hook,
which Task sessions writes into place with the writable paths it assembles, beside the settings
that carry the Bash sandbox. Task sessions relies on them confining the session's file tools and
shell to those paths and leaving reads and the network open; it never widens the paths it hands
over. The boundary is written before the session starts, and `--dry-run` writes it without starting
anything, so no session runs without its boundary.

<a id="uses-workers"></a>

**Workers** launches the [workers](../../glossary.json#concept.worker) of the Operations a task
session starts. Task sessions relies on it passing the shell sandbox's proxy on to them
([req.workers.proxy-passed](../../execution/workers/launch.md#req.workers.proxy-passed)), so they
reach their model endpoints from inside the session's sandbox, and on each worker's
[worker backend](../../glossary.json#concept.worker-backend) coming from the
[worker configuration](../../glossary.json#concept.worker-configuration), pi unless it chooses
Claude Code, never from the program the task session runs on.

<a id="uses-main-session"></a>

**Main session** provides the
[guidance](../../glossary.json#concept.main-session-guidance) a task session starts with: the
rendered task-session guidance, which carries the same rules for working inside a task that the
main agent follows. A missing rendered guidance refuses the start with `session_failed`. It also
provides the [project MCP server](../../glossary.json#concept.project-mcp-server), which Task
sessions configures for every task session it starts, without a channel (`CONCORDE_CHANNEL=0`).

Two Modules call this one, both from level 1's side: the Main session's guidance has the main
agent start task sessions, and Tasks dispatches `concorde task session` here after its own checks
and, when it closes a task, has its task sessions ended here. A task session records only its
start, and its transcript once its task ends: the main agent learns what it did from its
SendMessage report, and finds one that ended without a message with `claude agents` and
`claude logs` while its task is open.
