# Main session

## Purpose

Main session is the guidance that makes an ordinary Claude Code or pi session in a project's
primary worktree act as Concorde's main agent: discuss work with the developer, split it into
tasks, carry a task out inside its worktree or, in Claude Code, hand tasks to task sessions, keep
each task's decision log, decide ordinary questions itself while escalating only major ones, merge
delivered tasks, and handle Issues. It also holds the guidance a task session starts with. It is
advice to a
model, not enforcement — Concorde places no permission limits on the main agent, and nothing here
constrains the developer. In pi it adds a run view, an extension that starts Operations in the
background and shows their progress. Distribution renders and installs this Module's content.

## Terminology

| Term | Definition |
| --- | --- |
| Main-session guidance | The instructions, installed as a project skill for Claude Code and for pi and as a `CLAUDE.md` block, that tell the main agent how to work with Concorde. |
| Run view | The Concorde extension of a pi main session that starts Operations in the background, shows every run and its worker's progress, and wakes the main agent when a run ends. |
| Model picker | The dialog of the pi run view in which the developer chooses, for every worker, an Operation's workers or one worker role, the model and reasoning level of pi workers. |
| Questions without a task | The guidance's rule that Operations which allow it run without a task for a question or review that changes nothing. |
| Escalation policy | The rule by which the main agent decides ordinary questions itself, records and reports them, and asks the developer only for decisions with major impact. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../vocabulary.md#concept.concorde.task-session) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Error chain](../vocabulary.md#concept.concorde.error-chain) | |
| [Task](../tasks/module.md#concept.tasks.task) | |
| [Decision log](../tasks/module.md#concept.tasks.decision-log) | |
| [Operation](../operations/module.md#concept.operations.operation) | |
| [Operation result](../operations/module.md#concept.operations.result) | |
| [Issue](../issues/module.md#concept.issues.issue) | |
| [Spec MCP server](../spec-tooling/spec-mcp/module.md#concept.spec-mcp.server) | |

## Usage

<a id="concept.main-session.guidance"></a>

**What the main agent is told.** The installed guidance tells the Claude Code or pi session opened in a
Concorde project's primary worktree that it is the main agent, and gives it a working method:

- **Discuss first.** Agree the direction with the developer before changing anything.
- **Split into tasks.** Turn agreed work into [tasks](../tasks/module.md#concept.tasks.task),
  opened with `concorde task`. Run tasks in parallel only across worktrees whose Modules and shared
  files do not overlap; run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Work inside the task.** Never change Specs or code in the primary worktree. For a single
  task, enter its worktree (Claude Code's EnterWorktree), change Specs and code there directly or
  by running [Operations](../operations/module.md#concept.operations.operation) with
  `concorde run <operation> --task <task> …` in background Bash and reading the
  [Operation result](../operations/module.md#concept.operations.result), and run every `concorde`
  command with the worktree's own copy; leave after delivery. Be inside at most one task at a time.
  The only change made in the primary worktree is trivial housekeeping, such as regenerating the
  registry mirror.
- **Hand split work to task sessions.** For work split into several tasks, start one
  [task session](../vocabulary.md#concept.concorde.task-session) per task with
  `concorde task session <task> --main <own session name>` and stay in the primary worktree while
  they run; they report back with SendMessage and escalate with their own link on the chain.
- **Keep the decision log.** Record every non-`ok` result and every unsupervised choice, with its
  reason, in the task's [decision log](../tasks/module.md#concept.tasks.decision-log).
- **Merge delivered work.** From the primary worktree, merge a branch `delivery` committed without
  asking authorization, with `concorde task merge`, never with `git merge`: it holds the
  [merge lock](../tasks/module.md#concept.tasks.merge-lock) so merges of several main sessions never
  interleave, validates the primary branch, undoes a merge whose checks fail and closes the task.
  Retry a `merge_busy`; resolve a conflict in the task worktree by merging the primary branch into
  the task branch and delivering again; handle a failed check as new work, never by discarding
  someone's change.
- **Report.** Close each piece of work with a short summary for the developer: what was merged,
  what was decided on the developer's behalf, and what is still open.

A representative flow, agreeing a payments retry limit:

```d2 illustrative
shape: sequence_diagram
developer: Developer
main: Main agent
task: Task worktree (module.payments)
developer -> main: ask for a retry limit
main -> developer: agree the limit
main -> task: open the task
main -> task: run specify, implement, test
main -> task: run code_review, validate, delivery
task -> main: operation results
main -> developer: merge; report the exponential back-off it chose
```

<a id="concept.main-session.run-view"></a>

**The run view in pi.** In Claude Code the main agent runs `concorde run` in background Bash and
is woken when it exits. In pi the installed extension gives the same with more to watch: the
`concorde_run` tool starts `concorde run` as a detached process and returns at once with the run
identity. It starts the task worktree's own `concorde` in that worktree, found through the task
record, since a pi session cannot move into the task worktree itself. The extension follows every running Operation of the project through its [progress
file](../operations/module.md#concept.operations.progress-file) and that of the worker it launched
([progress file](../harness/workers/module.md#concept.workers.progress-file), paired by the host's
process identifier), and shows each run as an external job in pi-subagents' FleetView — its task
and Operation, its step, the worker's round and latest tool call, and on its end the result's
status and summary. A `bg_wait` call without an id waits for the running ones (with an id it
matches only subagent runs); runs are filed under the session's file, or its identity when it is
not persisted, the name pi-subagents gives the session. When a run ends the extension sends the
main agent a message naming the result file, which starts its next turn. `/concorde` lists the
recent runs. The view only launches and observes: the Operation host runs and records every run,
so closing pi never stops or changes one. Without pi-subagents the tool, the wake and `/concorde`
still work.

<a id="concept.main-session.escalation-policy"></a>

**Escalation policy.** A result that is not `ok`, or a refused `concorde` command, carries an
[error chain](../vocabulary.md#concept.concorde.error-chain); the guidance tells the main agent to
read it in full, since the origin says what went wrong and each link says why that level could not
handle it. The main agent decides ordinary design uncertainty itself — naming, internal structure,
task order, a clarified re-run, splitting a task — and records and reports the choice. It asks the
developer first only for a decision with major impact: changing what a Module promises to its
users or the project's direction, contradicting an earlier developer decision, discarding work or
data, doing something an ordinary revert cannot undo, touching security or credentials, or needing
more resources than the developer set; in doubt it records its reasoning and asks. An escalation is
never a summary: `concorde task escalate` adds its own link, with the reason it may not decide, on
top of the chain, records it in the task and prints it rendered for the developer.

<a id="concept.main-session.model-picker"></a>

**Worker models.** Workers run on the main agent's own program and take their model from the
worktree's [worker model
configuration](../harness/workers/module.md#concept.workers.model-configuration). The guidance
tells the main agent to change it only when the developer asks, and to let the developer choose
from what the [`configure_workers`](../operations/module.md#concept.operations.configure-workers)
Operation lists. In pi the run view's **model picker** does it: the `/concorde-models` command, or
the `concorde_configure_workers` tool the main agent calls on the developer's request, shows the
default and every Operation's workers — one row per worker role for an Operation with several —
with the model and level each runs on, then the models pi lists, then the chosen model's levels,
and applies each choice with `configure_workers`, removing an entry when the developer returns it
to the more general one; a task identity limits it to that task's copy. In Claude Code,
which lets no extension draw a dialog, the main agent asks with its question tool — scope, model,
level — and applies the answers itself. Without a request naming a task, only the worktree the
command runs in changes, so in the primary worktree only tasks opened later are affected.

<a id="concept.main-session.no-task-operations"></a>

**Questions without a task.** The guidance tells the main agent that `understand`, `spec_review`,
`code_review` and `configure_workers` also run [without a
task](../operations/module.md#concept.operations.no-task), on the worktree it starts them in, and
change no Spec or code; it uses them for a question or a review that does not justify a task, such
as understanding a Module before a change is agreed. In pi `concorde_run` takes the task as
optional for them.

**Issues.** A problem the current task will not fix is worth an
[Issue](../issues/module.md#concept.issues.issue) so it survives the task. Solving one is ordinary
work: open a task for its Module, run the Operations that fix it, and close the Issue on that
branch so the closure merges with the fix. `concorde issues report|list|show|close|reopen` is the
bookkeeping command.

**Spec queries.** The main agent may configure the
[Spec MCP server](../spec-tooling/spec-mcp/module.md#concept.spec-mcp.server) for its own session,
to ask which Modules exist, what a Module's context is, or what grant a task type gives. The server
answers from the Specs of the worktree it is rooted in — the primary worktree for the main agent —
and workers never receive it.

## Design

The guidance is instructions, not a program, because the main agent's work is judgment. Everything
that must hold regardless of judgment is enforced elsewhere — workers by the Harness, Operations by
their own checks, readiness by `validate` — so an agent that ignores the guidance wastes effort but
cannot widen a worker's boundary.

The main agent never changes the primary worktree's Specs or code: its view there is the whole
project, so nothing would bound or evidence a change made directly, and the primary worktree must
stay clean to merge. Inside a task worktree a direct change is bounded by the task and evidenced by
`validate` and `delivery`, so the main agent and task sessions may change Specs and code there
themselves. Every `concorde` command for a task runs with the worktree's own copy, because only the
branch's copy knows the Specs, Protocol and checks the task changes. A session is inside one task
at a time, which is why split work goes to task sessions; a task session's writes are confined to
its task by the settings [Tasks](../tasks/module.md) generates, while the main agent stays
unrestricted and alone merges; merging needs no authorization because
`delivery` only commits what `validate` found ready, and a merge is ordinary, revertible Git. The
escalation policy balances the same way: deciding ordinary questions keeps work moving, recording
and reporting them keeps them reviewable, and reserving major-impact ones protects decisions only
the developer may make.

How this Module is built:

```d2
mainsession: Main session {
  guidance: Guidance sources {
    "prompts/main-session/"
    "tests/concorde/main_session/"
  }
  view: pi run view {
    "pi_extension.ts"
    "pi_runs.ts"
  }
  picker: pi model picker {
    "pi_models.ts"
  }
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** live under `prompts/main-session/` (`skill.md`, installed as the project
skill `.claude/skills/concorde/SKILL.md`; `claude-md.md`, installed into the project's `CLAUDE.md`;
`task-session.md`, the first prompt `concorde task session` gives a task session; and
`common/in-task.md`, the rules for working inside a task that the skill and the task-session
guidance share) and are rendered by Distribution's build into `generated/main-session/`. Their tests, under
`tests/concorde/main_session/`, check that the rendered guidance states every rule the
[scenarios](scenarios.md) describe; what the main agent then does is judgment no deterministic test
observes. The skill is also installed for pi as `.pi/skills/concorde/SKILL.md`.

<a id="realization.main-session.pi-run-view"></a>

The **pi run view** is `src/concorde/main_session/pi_extension.ts`, installed as
`.pi/extensions/concorde/index.ts`, with the pure reading of progress files in `pi_runs.ts` beside
it. It also sets `CONCORDE_CLIENT=pi` for every command the session starts, so the host runs pi
workers for it. The tests run `pi_runs.ts` under Node against progress files; the extension itself
needs a pi session and is exercised in one.

<a id="realization.main-session.pi-model-picker"></a>

The **pi model picker**'s dialogs live in the extension; the pure part, turning the output of a
`configure_workers` run into the rows it offers and a chosen row into a `configure_workers` command
line, is `pi_models.ts`, installed beside it. Tests run it under Node; the dialogs themselves were
exercised by driving a pi RPC session.

## Relationships

```d2
mainsession: Main session
operations: Operations
tasks: Tasks
issues: Issues
workers: Workers
mainsession -> workers
tooling: Spec tooling {
  mcp: Spec MCP server
}
mainsession -> operations
mainsession -> tasks
mainsession -> issues
mainsession -> tooling.mcp
```

The guidance describes how the main agent uses four providers; the installed skill and `CLAUDE.md`
block are its only way to reach a session.

<a id="uses-operations"></a>

**Operations** provides the [Operation](../operations/module.md#concept.operations.operation)
catalog and `concorde run`. Each Operation returns an
[Operation result](../operations/module.md#concept.operations.result) the main agent can read
without inspecting the worker, and none starts the next one: that choice is the main agent's.

<a id="uses-workers"></a>

**Workers** keeps each worker run's [progress
file](../harness/workers/module.md#concept.workers.progress-file). The run view relies on it
recording the phase, round and latest tool call, and the host process that launched the worker,
and on it being an observation only. Workers also owns the [worker model
configuration](../harness/workers/module.md#concept.workers.model-configuration); the model picker
and the guidance change it only through the `configure_workers` Operation, which lists the
candidates and validates every choice, so neither ever writes the file itself.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../tasks/module.md#concept.tasks.task) — its branch, worktree and
record — and the [decision log](../tasks/module.md#concept.tasks.decision-log). Each task's own
worktree is what keeps parallel tasks from mixing changes; opening, merging, closing tasks and
writing the log are the main agent's responsibility.

<a id="uses-issues"></a>

**Issues** provides the durable [Issue](../issues/module.md#concept.issues.issue) records and their
bookkeeping command. Because Issues are branch-local, the guidance tells the main agent to close
one on the branch that fixes it.

<a id="uses-spec-mcp"></a>

The **Spec MCP server**, a child of Spec tooling, answers read-only queries from the worktree it is
rooted in, so the guidance tells the main agent that a question about a task's Specs needs a
server, or a `concorde` command, rooted in that task's worktree.
