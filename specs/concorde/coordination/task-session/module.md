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
merge it makes is the primary branch into its task branch when the main agent asks for it after a
merge conflict or a `concorde update`, a change inside its own worktree and branch. It runs on the main agent's own program and
configuration, because it does the main agent's own task-level work at a smaller scale: an isolated
configuration, such as a worker gets, would give it other tools and instructions than the main
agent's.

Its **[session boundary](../../glossary.json#concept.session-boundary)**, a term of the Harness, is
the settings and write hook that keep its own file-writing tools inside its task. That is its one
restriction: everything else of the session, its shell included, is as open as the main agent's.

## Overview

### A task session's life

The task level of the work is always delegated: the main agent never works inside a task worktree
but, from the primary worktree, starts a [task session](../../glossary.json#concept.task-session)
for every task, even a single one, after recording the
[task brief](../../glossary.json#concept.task-brief) in its
[decision log](../../glossary.json#concept.decision-log). How a task session travels over time,
from the main agent's start to the end of its task:

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
with its first prompt and records it in the task's [trace](../../glossary.json#concept.trace),
naming the main agent's session in the [task record](../../glossary.json#concept.task-record). The
session then works the task following its guidance and reports to the main agent: it records its
delivery, or every decision it needs, with `concorde task report`, and then wakes the main agent
with SendMessage to the session the record names at that moment; the main agent answers together
the same way. When the main agent merges or closes the task, Tasks' close has Task sessions stop
the task's sessions if the task ends without a merge, keep their transcripts and remove them from
Claude's session list.

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

Task sessions writes the session's [session boundary](../../glossary.json#concept.session-boundary)
— a settings file and the Harness's task-session [write
hook](../../glossary.json#concept.write-hook) with the task's paths embedded — under
`.concorde/tasks/severity/runtime/`, with an MCP configuration `mcp.json` there that gives the
session the [project MCP server](../../glossary.json#concept.project-mcp-server), starts `claude
--bg` in the task worktree with that configuration and the task-session guidance and the task's
goal, Modules, decision log and the main agent's session name as its first prompt, and records the
started session as a node `sessions/<id>/` of the task's trace, named by the short id `claude --bg`
reported, with status `unknown` until its task ends, since Concorde does not see a Claude Code
session end, and has Tasks name the `--main` session as the task's main in its record. The first
prompt gives that name too, but only as the main agent's session when the task session started: a
Claude Code session's name does not survive a restart or resume of that session, so the task session
takes the name to message from the record each time it reports, which the main agent rebinds with
`concorde task rebind` once its name changed
([Tasks](../tasks/module.md#reports-and-the-main-agents-session)). It also asks Claude Code for the
session's full session id, the name of its transcript, with `claude agents --json --all`, whose
entry of that short id gives it as `sessionId`, and records it in the node; when Claude Code does
not tell it then, the node records none and the task's end asks again. `--main` is required: a start
without it is refused with `invalid_input`. `--dry-run` writes the boundary and prints the command
without starting anything. A task that is closed or failed, a missing worktree, or a Claude Code
that does not report a started background session is refused (`task_closed`, `missing_worktree`,
`session_failed`) with Claude Code's output in the detail. The session receives the main agent's
answers through SendMessage and sends its reports the same way once `concorde task report` recorded
them; `claude stop` stops it.

The server is passed explicitly, as the running Python with the running package, so a task session
has it whatever the project's `.mcp.json` holds and whoever approved it. It comes without a channel,
and its configuration says so
(`CONCORDE_CHANNEL=0`): Claude Code does not wake a background session with channel events. A
probe on 2026-09-29 (Claude Code 2.1.284) started a `claude --bg` session with
`--dangerously-load-development-channels server:concorde`; the server loaded and registered a wait
on a held [merge lock](../../glossary.json#concept.merge-lock), and when the lock was released the
idle session was never woken. So `register_wait` answers a task session with the `concorde task
wait` command, which it runs in background Bash and is woken by when it returns. The server runs as
every MCP server does, as a process of the session beside its tools, and its tools may change any
task's record: the developer accepted that a task session can reach the task management tools, which
are no boundary, so the guidance, not the boundary, keeps a task session from merging or closing its
task. Its `workflow_step` starts the runs of the session's workflows from there
([below](#workflow-runs-through-the-server)).

<a id="project-mcp-approvals"></a>

Nobody answers Claude Code's dialog "New MCP server found in this project" in a background session
either: a `claude --bg` session in a trusted project shows it for each server of the project's
`.mcp.json` that nobody approved and waits on it for ever, even for the entry `concorde` that
`--mcp-config` passes as well (seen with Claude Code 2.1.285 on 2026-10-01). So the session's
settings answer it beforehand, server by server, from what Claude Code itself would read:

- The servers are those of every `.mcp.json` Claude Code loads for a session in the task worktree:
  that of each folder from the task worktree up to the filesystem root, the primary worktree's
  included when the task worktree lies inside it. A file that is missing, unreadable or without an
  `mcpServers` object names no server, since Claude Code loads none from it and so asks about none;
  the session starts all the same.
- The entry `concorde` is disabled (`disabledMcpjsonServers`): the `--mcp-config` server replaces
  it, and with both Claude Code loads only the latter, so nothing is lost.
- Every other server is enabled (`enabledMcpjsonServers`) when the primary worktree approved it,
  and disabled otherwise, as the dialog's "Continue without using this MCP server" would. Claude
  Code 2.1.285 judges a server rejected when any settings source lists it in
  `disabledMcpjsonServers`, and otherwise approved when any lists it in `enabledMcpjsonServers` or
  sets `enableAllProjectMcpServers`, comparing names with every character but letters, digits, `_`
  and `-` read as `_`. Task sessions judges the same way over every source that records such an
  approval for the primary worktree or the task worktree: the user's settings, both worktrees'
  `.claude/settings.json` and `.claude/settings.local.json`, the managed settings with their
  drop-ins, and the primary worktree's entry in Claude Code's global configuration, whose
  approvals Claude Code moves into the local settings when it next starts there. A source that is
  missing or unreadable approves nothing.

The dialog records its answer in the local settings of the folder it was shown in; these settings
only reach the session through `--settings`, so they change no approval anywhere else.

## The session boundary

A task session is restricted in one thing: it changes nothing outside its task worktree. Its file
tools are held to that by the [write hook](../../glossary.json#concept.write-hook), which lets Edit
and Write change the task worktree and the task's decision log and denies every other path, an
[Issue](../../glossary.json#concept.issue) record among them; the session writes Issues through the
Issue command or the project MCP server's Issue tools, as the runs it starts do. Nothing else of
the session is restricted. Its commands run under no operating-system sandbox, with every path,
process, socket, home-state file and network host open to them, so the session prepares its own
worktree — dependencies, submodules, build outputs — probes the machine it runs on, and starts the
runs of its task as the main agent starts its own.

The session boundary guards against mistakes, not a malicious session, and a task session is the
main agent's own role at a smaller scale: the main agent works under no boundary at all. The
developer decided the shell's sandbox away after it had cost fourteen problems in one week, of
which only four were answered by changing a rule and the rest by a workaround that moved work to
the main agent or into the project MCP server: a PID namespace per Bash call that killed every
[detached run](../../glossary.json#concept.detached-run), a network namespace reached only through a proxy, Unix sockets blocked by seccomp
(which broke the nested sandbox of every pi worker a session started), protected paths such as
`.git/config` that no setting could open, placeholder files the host saw, and only paths existing
at the start made writable. What keeps the shell inside the task now is the task-session
[guidance](../../glossary.json#concept.main-session-guidance), Claude Code's `auto` mode and, at
the end, the audit `concorde task merge` runs over what lies outside the task worktree
([Tasks](../tasks/module.md#nothing-changed-outside-the-task)): the merge is refused when the
primary worktree, or the worktree of a task that ended, holds changes nobody accounts for, and the
task's own merge refuses an uncommitted change in its worktree, so what another session wrote there
is caught too.

Nobody answers permission prompts in a background session, so it runs in Claude Code's `auto` mode:
a classifier approves or refuses each action instead of asking, which is the only check between the
guidance and the session's shell. `bypassPermissions` would skip that check, and Claude Code starts
a background session in it only after the developer accepted a disclaimer once. A model without
`auto` mode would fall back to asking and stall, so `--model` must name one that has it. Reads are
open because the session needs the whole project's context. Tools that MCP servers add are outside
the write hook, which guards Edit and Write only, and so are the server's own writes: the
[project MCP server](../../glossary.json#concept.project-mcp-server) can change any task's record
and take any lock, which the developer accepted, since it is a management tool and the guidance,
not the boundary, says what a task session does with it.

A run of the session's own, started with `concorde run`, `task-validation` or `delivery` in
background Bash, lives as long as that background call. So the guidance has the session let its runs
finish and stop every other background command before `task-validation` and `delivery`: a run that
still runs holds the [workspace lock](../../glossary.json#concept.workspace-lock), which refuses
both, and `delivery` commits every uncommitted change, so a command still writing in the worktree
would decide what the [delivery commit](../../glossary.json#concept.delivery-commit) holds.

<a id="workflow-runs-through-the-server"></a>

**A task session's workflow runs start from the project MCP server.** The
[step agents](../../glossary.json#concept.step-agent) of the session's
[workflows](../../glossary.json#concept.workflow) start and await every step through that server's
`workflow_step`, which runs the task worktree's own `concorde workflow step` as a process of the
server ([Workflows](../../execution/workflows/module.md#steps-in-claude-code)). A
[workflow step](../../glossary.json#concept.workflow-step) may outlast many relays, and a run
started there depends on neither a relaying agent's turn nor a background command Claude Code ends
after two hours or when the session is stopped. What bounds those runs is Concorde's own, as it
bounds the main agent's: the runner works only on the bound workspace of the session's own task
worktree, with its trace and locks, and commits, for `delivery`, only on the task branch; each
worker keeps its [grant](../../glossary.json#concept.grant) and its own boundary; each
[configured check](../../glossary.json#concept.configured-check) runs in the
[read-only check boundary](../../glossary.json#concept.read-only-check-boundary). This path rests on
the task-session guidance, as `task_merge` and `task_escalate` of the same server do: the guidance
has a task session start its workflows as the installed workflows and use the server's tools only as
they are meant for.

## When the task ends

<a id="ending-claude-sessions"></a>

Tasks' close hands its task sessions, every one the task's trace lists, to Task sessions at three
points:

- A close without a merge (`--completed` or `--failed`) first runs `claude stop <id>` for each, so
  no session goes on working in the worktree the close removes or starts another run there; a
  session already ended or no longer known to Claude Code (`No job matching`) counts as stopped.
  When a stop cannot be confirmed, the close is refused with `session_stop_failed` before it
  changed the task, naming the session, Claude Code's answer and the command to stop it by hand.
- Every close, a merge's included, finishes each session's trace node just before the task's
  folder moves to the history. It asks Claude Code once, with `claude agents --json --all`, for
  every session it still lists, and takes from the session's entry its full session id, when the
  node does not record it yet, its working directory and its state. It opens the transcript by
  that exact id: `projects/<the working directory, every character that is no letter or digit as
  ->/<session id>.jsonl` of Claude Code's configuration folder (`$CLAUDE_CONFIG_DIR`, by default
  `~/.claude`), or else the file of that name in any project folder; a session whose id Claude
  Code does not tell, or whose transcript is in neither place, is named in a warning that says
  what was asked and where it looked. The transcript becomes `transcript.jsonl`, an artifact of
  the node, and the folder Claude Code keeps beside it, with subagent transcripts and long tool
  results, becomes `transcript/`. From these records the node receives what the session consumed
  and when it ended ([below](#finishing-a-session-node)). The history thus keeps each session's
  conversation and its figures, and is never written after the move.
- Once the task is closed, `claude rm <id>` removes each session whose transcript was kept from
  Claude's session list. It kills a session that still runs and deletes Claude Code's own state of
  the job, and it removes a worktree only when Claude Code created it for the session, never the
  task worktree a task session is started in. The removal is best effort: a failing `claude rm`, or
  a transcript that could not be kept, whose session is then left in the list so nothing of it is
  lost, never fails the close, and the close's `warnings` name the session, the whole reason and
  the command that removes it by hand.

### Finishing a session node

A task session's node is written when the session starts, and Concorde sees nothing of the session
until its task ends; its figures then come from Claude Code's own records, as
[Tracing](../../tracing/requirements.md#req.tracing.reported-usage) requires, and are written into
the node because retention later removes the transcript:

- **usage**: the tokens read, written, and read from and written to the prompt cache, summed over
  the `assistant` records of the transcript and of the subagent transcripts beside it, counting
  each API message, by its `message.id`, once, since one message may span several records; the
  turns are those messages; the duration runs from the earliest time the transcript's records carry
  to the latest. The cost
  is the `totalCostUSD` of the transcript's last `cost-state` record, Claude Code's own account,
  when one is there and no `assistant` record follows it, and null otherwise: a background
  session's transcript often has none, and Concorde computes no price.
- **end**: the latest time the transcript's records carry, when a transcript was kept.
- **status**: from the session's state in `claude agents --json --all`, `ok` for `done`, a session
  waiting for its next message, `failed` for `failed`, and `unknown` for any other state or when
  Claude Code no longer lists the session; the state itself is the node's outcome.
- **content**: the full session id, Claude Code's state, the tokens and messages of each model,
  and the `modelUsage` of that `cost-state` record, per model with its cost, when there is one.

A session whose transcript was not kept still receives its session id and status when Claude Code
tells them; its usage stays null. Claude Code judges a session's state by whether its process
lives, so a state read while a session still works says nothing about how it ended. So Concorde
takes the state only at the close, when the task has ended.

## Escalating

A task session escalates what it may not decide with `concorde task escalate --by task-session`,
which Tasks records as a link of level `task-session` on top of the failed runs' chains; the main
agent adds its own link above it when the developer must decide. A task never asks the developer
in place: the session gathers every decision it needs, records each as an escalation and reports
them together, in one report that `concorde task report` records with the escalations it carries
and one SendMessage, and the main agent answers them together. When that message reaches no
session, because the main agent's session was restarted under another name, the report stays
recorded and the session waits in background Bash with `concorde task wait <task> --rebound <name>`
until the main agent has rebound the task, then sends it again to the new name. Exact commands and
error codes are in the [contracts](contracts.md), the obligations in the
[requirements](requirements.md) and the behaviour in the [scenarios](scenarios.md).

## What the started session relies on

These three collaborations are the started session's, which follows its guidance; Task sessions
itself starts no workflow or run and owes them nothing.

<a id="uses-workflows"></a>

**Workflows** is level 3, which a task session may start for its task when the work follows a known
procedure. The session starts a [workflow](../../glossary.json#concept.workflow) for its own task
only, in the [mode](../../glossary.json#concept.workflow-mode) its task brief names, interactive when it
names none. An interactive workflow ends at its first
[decision point](../../glossary.json#concept.decision-point) not yet settled, and since nobody
answers the session in place, it escalates every pending point of that step at once, with the
workflow result as the cause, and starts the workflow again with the main agent's answers; a no-ask
workflow decides those points itself and reports every decision at the end. Its workflow's steps
start through the project MCP server
([The session boundary](#workflow-runs-through-the-server)). The session relies on
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
never starts a worker or another agent itself. It prepares each worker's environment instead: a
realization binds only files that exist and a worker writes only bound files and new files inside
bound directories, so the session itself creates any other new file the work needs, with the least
content its format needs to be valid, and binds it to its Module before it starts the run that
fills it
([req.main-session.task-session-prepares-workers](../main-session/requirements.md#req.main-session.task-session-prepares-workers)).

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

The **session starter** (`session.py`) assembles the session's settings around the write hook and
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

The **Harness** provides the source of the
[session boundary](../../glossary.json#concept.session-boundary): the task-session write hook, which
Task sessions writes into place with the task's worktree and decision log embedded. Task sessions
relies on it holding Edit and Write to those two and leaving everything else of the session open; it
never widens the paths it hands over, and adds no restriction of its own around the hook. The
boundary is written before the session starts, and `--dry-run` writes it without starting anything,
so no session runs without its boundary.

<a id="uses-issues"></a>

**Issues** keeps the project's [Issues](../../glossary.json#concept.issue) in the primary worktree's
`.concorde/issues/`, each write holding the [merge lock](../../glossary.json#concept.merge-lock) and
committing its record alone on the primary branch. Task sessions relies on an Issue record lying
outside every task worktree, so that the write hook refuses one and a task session reaches Issues
only through the Issue command or the Issue tools, as the runs it starts do.

<a id="uses-workers"></a>

**Workers** launches the [workers](../../glossary.json#concept.worker) of the Operations a task
session starts. Task sessions relies on each worker's
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
and, when it closes a task, has its task sessions ended here. A task session records its start, its
reports, and its transcript and figures once its task ends: the main agent learns what it did from
its report, recorded in the task record and delivered by SendMessage, and finds one that ended
without a report with `claude agents` and `claude logs` while its task is open.
