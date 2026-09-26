# Main session

## Purpose

Main session is the top of Concorde's five levels of work, level 1: the guidance that makes an
ordinary Claude Code or pi session in a project's primary worktree act as Concorde's main agent:
discuss work with the developer, split it into tasks, carry a task out inside its worktree or hand
tasks to task sessions, keep each task's decision log, decide ordinary questions itself while
escalating only major ones, merge delivered tasks, and handle Issues. The method of working inside a
task is part of this guidance, because the task level is the main agent's own work: it follows the
method when it works a task itself, and a task session it delegates the task to starts with the same
method in the guidance it is given. It is advice to a model, not enforcement — Concorde places no
permission limits on the main agent, and nothing here constrains the developer. In pi it adds a run
view, an extension that starts Operations in the background and shows their progress. Distribution
renders and installs this Module's content.

## Terminology

| Term | Definition |
| --- | --- |
| Main-session guidance | The instructions, installed as a project skill for Claude Code and for pi and as a `CLAUDE.md` block, that tell the main agent how to work with Concorde. |
| Run view | The Concorde extension of a pi main session that starts Operations in the background, shows every run and its worker's progress, and wakes the main agent when a run ends. |
| Model picker | The dialog of the pi run view in which the developer chooses, for every worker, an Operation's workers or one worker role, the model and reasoning level of pi workers. |
| Questions without a task | The guidance's rule that Operations which allow it run without a task for a question or review that changes nothing. |
| Escalation policy | The rule by which the main agent decides ordinary questions itself, records and reports them, and asks the developer only for decisions with major impact. |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Task session](../../vocabulary.md#concept.concorde.task-session) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Task](../../tasks/module.md#concept.tasks.task) | |
| [Decision log](../../tasks/module.md#concept.tasks.decision-log) | |
| [Operation](../../operations/module.md#concept.operations.operation) | |
| [Operation result](../../operations/module.md#concept.operations.result) | |
| [Issue](../../issues/module.md#concept.issues.issue) | |
| [Spec MCP server](../../spec-tooling/spec-mcp/module.md#concept.spec-mcp.server) | |

## Usage

<a id="concept.main-session.guidance"></a>

**What the main agent is told.** The installed guidance tells the Claude Code or pi session opened in a
Concorde project's primary worktree that it is the main agent, and gives it a working method:

- **Discuss first.** Agree the direction with the developer before changing anything.
- **Split into tasks.** Turn agreed work into [tasks](../../tasks/module.md#concept.tasks.task),
  opened with `concorde task`. Run tasks in parallel only across worktrees whose Modules and shared
  files do not overlap; run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Work inside the task.** Never change Specs or code in the primary worktree. For a single
  task, enter its worktree (Claude Code's EnterWorktree), change Specs and code there directly or
  by running [Operations](../../operations/module.md#concept.operations.operation) with
  `concorde run <operation> --task <task> …` in background Bash and reading the
  [Operation result](../../operations/module.md#concept.operations.result), and run every `concorde`
  command with the worktree's own copy; leave after delivery. Be inside at most one task at a time.
  The only change made in the primary worktree is trivial housekeeping, such as regenerating the
  registry mirror.
- **Hand split work to task sessions.** For work split into several tasks, start one
  [task session](../../vocabulary.md#concept.concorde.task-session) per task with
  `concorde task session <task>` and stay in the primary worktree while they run. A task session
  runs on the main agent's own program. In Claude Code the command names the main agent's session
  with `--main`, and the session reports back with SendMessage. In pi the main agent uses the
  `concorde_task_session` tool: each [session round](../task-session/module.md#concept.task-session.round)
  ends with a report that wakes the main agent, which starts the next round with the tool's
  `answer`. Either way a task session escalates with its own link on the chain.
- **Keep the decision log.** Record every non-`ok` result and every unsupervised choice, with its
  reason, in the task's [decision log](../../tasks/module.md#concept.tasks.decision-log).
- **Merge delivered work.** From the primary worktree, merge a branch `delivery` committed without
  asking authorization, with `concorde task merge`, never with `git merge`: it holds the
  [merge lock](../../tasks/module.md#concept.tasks.merge-lock) so merges of several main sessions never
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
file](../../operations/module.md#concept.operations.progress-file) and that of the worker it launched
([progress file](../workers/module.md#concept.workers.progress-file), paired by the host's
process identifier), and shows each run as an external job in pi-subagents' FleetView — its task
and Operation, its step, the worker's round and latest tool call, and on its end the result's
status and summary. A `bg_wait` call without an id waits for the running ones (with an id it
matches only subagent runs); runs are filed under the session's file, or its identity when it is
not persisted, the name pi-subagents gives the session. When a run ends the extension sends the
main agent a message with the result's status and summary and the result file: while the main
agent is in a turn the message is steered into that turn after its current tool calls, and
otherwise it starts the next turn. A run that has already finished when `concorde_run` finds it,
such as one refused at once, is answered in the tool's own result instead, and no message
follows. `/concorde` lists the recent runs. The view only launches and observes: the Operation
host runs and records every run, so closing pi never stops or changes one. Without pi-subagents
the tool, the wake and `/concorde` still work.

The view follows pi task sessions the same way. The `concorde_task_session` tool starts a task
session, answers it (`answer`, which starts the next round) or stops its running round (`stop`),
by running `concorde task session` from the primary worktree, and returns at once. The extension
reads each round's progress file under `.concorde/tasks/<task>.session/` and shows the round as an
external job — its task, round and the session's latest tool call — and when the round ends it
wakes the main agent with the outcome recorded in the task record: the report's summary,
decisions and open points, the delivery commit, the numbers of the escalations to read with
`concorde task show`, or the failed round's error chain rendered. A main session that starts
again finds the running rounds from their progress files. In a pi task session itself, where
`CONCORDE_TASK_SESSION` is set, the extension stays inactive.

<a id="concept.main-session.escalation-policy"></a>

**Escalation policy.** A result that is not `ok`, or a refused `concorde` command, carries an
[error chain](../../vocabulary.md#concept.concorde.error-chain); the guidance tells the main agent to
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

**Worker models.** Workers run on the main agent's own program unless the worktree's [worker model
configuration](../workers/module.md#concept.workers.model-configuration) chooses the other
one, and take their model from it. When the developer asks to run workers on the other program, the
main agent edits the configuration's `backend` section by hand, since no Operation changes it, and
shows the result with `configure_workers`. The guidance
tells the main agent to change it only when the developer asks, and to let the developer choose
from what the [`configure_workers`](../../operations/module.md#concept.operations.configure-workers)
Operation lists. In pi the run view's **model picker** does it: the `/concorde-models` command, or
the `concorde_configure_workers` tool the main agent calls on the developer's request, shows the
default and every Operation's workers — one row per worker role for an Operation with several —
with the model and level each runs on (only the workers that run on pi), then the models pi
lists, then the chosen model's levels, and applies each choice with `configure_workers`, removing
an entry when the developer returns it to the more general one; a task identity limits it to that
task's copy. In Claude Code, which lets no extension draw a dialog, the main agent asks with its question tool — scope, model,
level — and applies the answers itself. Without a request naming a task, only the worktree the
command runs in changes, so in the primary worktree only tasks opened later are affected.

<a id="concept.main-session.no-task-operations"></a>

**Questions without a task.** The guidance tells the main agent that `understand`, `survey`,
`spec_review`, `code_review` and `configure_workers` also run [without a
task](../../operations/module.md#concept.operations.no-task), from the primary worktree only, and
change no Spec or code, and that inside a task's worktree it always passes `--task`; it uses them for a question or a review that does not justify a task, such
as understanding a Module before a change is agreed. In pi `concorde_run` takes the task as
optional for them.

**Workflows.** For a task that follows a known procedure the guidance tells the main agent to run
its [workflow](../../workflows/module.md#concept.workflows.workflow) instead of sequencing the
Operations by hand: open the task, then start the workflow from the primary worktree, in Claude Code
as the installed `/concorde-<name>` workflow and in pi through pi-subagents with the installed
script, and stay in the primary worktree while it runs. The main agent asks the developer which
[mode](../../workflows/module.md#concept.workflows.mode) to use unless the developer already said;
interactive suits a developer who is present, no-ask one who wants the result later. When a
workflow ends `awaiting_decision`, the main agent puts every pending decision point to the developer
at once, with its options and recommendation, writes the answers keyed by step key and starts the
same workflow again. It reads the workflow result from the saved file, and treats it like an
Operation result: it records it, reads every problem's chain, and merges a delivered task. The
guidance names the brownfield workflow as the way to describe a project whose code came before its
Specs, right after installation and initialization, and nowhere else.

### Issues

The main agent decides whether a concrete problem deserves an
[Issue](../../issues/module.md#concept.issues.issue), typically when the current task will not fix
it. A worker finding or an Operation error is input to that decision; neither records an Issue
automatically. The guidance tells the main agent to inspect `concorde issues list` and
`show <id>` first, including closed matches, then create or append a report through the
bookkeeping command. It keeps the receipt for follow-up; repeating a creation command would
create another Issue. Inspecting Issues is explicit, with no automatic notification to sessions.

Run every writing command (`report`, `close`, `reopen`) in a task worktree, and pass that task's
identity to `report --task`. If no task exists, open one for the owning Module, or the root Module
when the owner is unknown. `--task` supplies provenance, not routing; the working directory or
explicit root selects the Issue files. The command still accepts reports without a task; this
workflow is a rule of the guidance. Read-only `list`, `show` and `check` may run in either
worktree and describe its local records. The main agent works through the store's command rather
than editing report contents or flipping `status` in a file.

An Issue stays open while a task investigates or fixes it. Solve it by ordinary Operations on its
current owning Module, then `close --reason resolved` on that task's branch with a note and the
fix's evidence before delivery, so the closure merges with the fix. Other closing reasons are
`duplicate` (naming another open Issue) and `not-actionable`; recurrence uses `reopen`, preserving
history. Each disposition needs evidence whose meaning the main agent checks itself. Appending a
report to an open Issue uses the revision from `show`; closing and reopening read their own
current revisions. On `stale_issue`, read the record again before deciding to retry. See the
Issues [lifecycle](../../issues/module.md#lifecycle) for the complete state model.

Before ending a task without merging it, preserve follow-up information for every Issue worth
keeping. Either record it through the command in a subsequent task, keeping its earlier identity
and branch as references in the report, or append a handoff to the current task's decision log:
Issue identity, branch and commit when available, what remains to be done, and durable locations
of the report and evidence. Preserve uncommitted material needed for the handoff before allowing
worktree removal. Tasks keeps the branch and decision log after closing; committed Issue changes
survive there, but the primary branch's list still shows only what has been merged. A log entry
is a handoff, not a published Issue or an automatic transfer.

If Git reports a conflict in an Issue record, resolve it in the task worktree while merging the
primary branch into it. Preserve accepted reports unchanged and document how competing
dispositions are reconciled, retaining their evidence. Do not concatenate incompatible closes or
invent a reopening just to satisfy the state rules. Run `concorde issues check` explicitly on the
resolved records before `validate` and `delivery`; structural Spec validation alone does not run
the store check. If the meaning of a competing decision cannot be settled within the task's
scope, escalate it under the ordinary escalation policy.

### Develop installs

In a [develop install](../../dogfooding/module.md#concept.dogfooding.develop-install), where the
developer also changes the Concorde the project runs, the installed skill and `CLAUDE.md` block end with
[Dogfooding](../../dogfooding/module.md)'s own section: watch Concorde's runs, never change Concorde
from the project, and report Concorde defects to the Concorde repository. Everything above holds
unchanged; a normal install carries no such section.

### Spec queries

The main agent may configure the
[Spec MCP server](../../spec-tooling/spec-mcp/module.md#concept.spec-mcp.server) for its own session,
to ask which Modules exist, what a Module's context is, or what grant a task type gives. The server
answers from the Specs of the worktree it is rooted in — the primary worktree for the main agent —
and workers never receive it.

## Design

The guidance is instructions, not a program, because the main agent's work is judgment. Everything
that must hold regardless of judgment is enforced elsewhere — workers by the Harness, Operations by
their own checks, readiness by `validate` — so an agent that ignores the guidance wastes effort but
cannot widen a worker's boundary.

### Its place in the five levels

The main session is level 1 of Concorde's [five levels](../../module.md#the-five-levels), the top
of the agent layer. Nothing in Concorde calls it: the developer talks to it, and the installed skill
and `CLAUDE.md` block are Concorde's only way to reach a session at all. It calls only downward. At
level 2 it opens a task and either works it itself or delegates it to a task session; from inside a
task, its own or a task session's, workflows (level 3) and Operations (level 4) are started; and it
reaches workers (level 5) only through an Operation, touching Workers otherwise only to watch a run
and to configure worker models. What comes back up is structured: Operation results, workflow
results, and task-session reports and escalations, each failure carrying its
[error chain](../../vocabulary.md#concept.concorde.error-chain). The chain ends here: the main agent
decides what the escalation policy lets it decide, records and reports it, and otherwise adds its
own `main-agent` link and asks the developer, the chain's last receiver.

What the main agent calls, down the levels. Workers appear only under Operations, because an
Operation is the only way the main agent reaches one:

```d2
mainsession: Main session
tasks: Tasks
tasksession: Task sessions
workflows: Workflows
operations: Operations
workers: Workers
mainsession -> tasks
mainsession -> tasksession
mainsession -> workflows
mainsession -> operations
tasksession -> tasks
workflows -> operations
operations -> workers
```

The main agent never changes the primary worktree's Specs or code: its view there is the whole
project, so nothing would bound or evidence a change made directly, and the primary worktree must
stay clean to merge. Inside a task worktree a direct change is bounded by the task and evidenced by
`validate` and `delivery`, so the main agent and task sessions may change Specs and code there
themselves. Every `concorde` command for a task runs with the worktree's own copy, because only the
branch's copy knows the Specs, Protocol and checks the task changes. A session is inside one task
at a time, which is why split work goes to task sessions; a task session's writes are confined to
its task by the session boundary [Task sessions](../task-session/module.md) writes from the Harness,
while the main agent stays unrestricted and alone merges; merging needs no authorization because
`delivery` only commits what `validate` found ready, and a merge is ordinary, revertible Git. The
escalation policy balances the same way: deciding ordinary questions keeps work moving, recording
and reporting them keeps them reviewable, and reserving major-impact ones protects decisions only
the developer may make.

<a id="uses-tasks"></a>

**Tasks** provides the [task](../../tasks/module.md#concept.tasks.task) — its branch, worktree and
record — and the [decision log](../../tasks/module.md#concept.tasks.decision-log): the workspace of
level 2, the same whether the main agent works the task itself or through a task session. Each
task's own worktree is what keeps parallel tasks from mixing changes; opening, merging, closing
tasks and writing the log are the main agent's responsibility, whether it works the task itself or
through a task session. The guidance relies on `concorde task merge` holding the merge lock and
undoing a merge whose checks fail, and tells the main agent to retry a `merge_busy`, to resolve a
conflict in the task worktree, and to treat a failed check as new work rather than discard a change.

<a id="uses-task-session"></a>

**Task sessions** starts the task sessions the main agent delegates tasks to and, in pi, runs and
records their [session rounds](../task-session/module.md#concept.task-session.round), whose
progress files and recorded outcomes the run view reads. It applies whenever the main agent wants
several tasks to run at once. The guidance relies on a task session never merging or closing its
task and on every round ending with an outcome the task record confirms. A task session's report or
escalation is its result travelling up to level 1: the main agent answers an escalation, or asks
for more, with the next round's answer, reads a failed round's error chain like any other, and
merges a delivered task itself.

<a id="uses-workflows"></a>

**Workflows** provides the [workflows](../../workflows/module.md#concept.workflows.workflow) the main
agent starts in a task, their modes and the [workflow
result](../../workflows/module.md#concept.workflows.result) it reads when one ends. The guidance
relies on a workflow never opening, merging or closing a task and on its result keeping every
Operation's chain whole, so that a workflow's end is handled like an Operation's: an
`awaiting_decision` result makes the main agent put every pending decision point to the developer
at once and start the same workflow again with the answers.

<a id="uses-operations"></a>

**Operations** provides the [Operation](../../operations/module.md#concept.operations.operation)
catalog and `concorde run`, including the Operations that run [without a
task](../../operations/module.md#concept.operations.no-task) and
[`configure_workers`](../../operations/module.md#concept.operations.configure-workers). Each
Operation returns an [Operation result](../../operations/module.md#concept.operations.result) the
main agent can read without inspecting the worker, and none starts the next one: that choice is the
main agent's. The main agent records every non-`ok` result in the decision log and reads its chain
in full before deciding or escalating. The run view also relies on each running Operation keeping
its [progress file](../../operations/module.md#concept.operations.progress-file) current.

### Beside the levels

Two providers serve the main agent without being a level below it.

<a id="uses-issues"></a>

**Issues** provides durable [Issue](../../issues/module.md#concept.issues.issue) records and the
bookkeeping command for [reports](../../issues/interface.md#contract.issues.report) and
[receipts](../../issues/interface.md#contract.issues.receipt). The guidance relies on
[status](../../issues/module.md#concept.issues.status) following dispositions and
[revisions](../../issues/module.md#concept.issues.revision) detecting concurrent writes. It tells
the main agent to inspect before recording, make every Issue write in a task, preserve unmerged
observations for follow-up, and merge closure with the fix. The command records these decisions;
the main agent remains responsible for their evidence and for resolving conflicting decisions.

<a id="uses-spec-mcp"></a>

The **Spec MCP server**, a child of Spec tooling, answers read-only queries about Modules, context
and grants from the worktree it is rooted in. The main agent configures it for its own session only
when it wants to ask such questions; workers never receive it. Since a server rooted in the primary
worktree knows only the primary branch's Specs, the guidance tells the main agent that a question
about a task's Specs needs a server, or a `concorde` command, rooted in that task's worktree.

### Inside

How this Module is built: the guidance on one side, and the pi extension on the other.

```d2
mainsession: Main session {
  sources: Guidance sources {
    "prompts/main-session/"
  }
  guidance: Main-session guidance
  policy: Escalation policy
  view: pi run view {
    "pi_extension.ts"
    "pi_runs.ts"
  }
  picker: pi model picker {
    "pi_models.ts"
  }
  sources -> guidance: authors
  guidance -> policy: includes
  view -> picker: draws the dialogs of
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** live under `prompts/main-session/` (`skill.md`, installed as the project
skill `.claude/skills/concorde/SKILL.md`; `claude-md.md`, installed into the project's `CLAUDE.md`;
`task-session.md` and `task-session-pi.md`, the first prompts `concorde task session` gives a
Claude Code and a pi task session, which share `common/task-session.md`; and
`common/in-task.md`, the rules for working inside a task that the skill and the task-session
guidance share) and are rendered by Distribution's build into `generated/main-session/`. Their
tests, under `tests/concorde/main_session/`, check that the rendered guidance states every rule the
[scenarios](scenarios.md) describe; what the main agent then does is judgment no deterministic test
observes. The skill is also installed for pi as `.pi/skills/concorde/SKILL.md`.

<a id="realization.main-session.pi-run-view"></a>

The **pi run view** is `src/concorde/main_session/pi_extension.ts`, installed as
`.pi/extensions/concorde/index.ts`, with the pure reading of progress files in `pi_runs.ts` beside
it. It also sets `CONCORDE_CLIENT=pi` for every command the session starts, so the host runs pi
workers and pi task sessions for it. `pi_runs.ts` also reads the progress files of task-session
rounds. The tests run `pi_runs.ts` under Node against progress files; the extension itself needs a
pi session and is exercised in one.

<a id="realization.main-session.pi-model-picker"></a>

The **pi model picker**'s dialogs live in the extension; the pure part, turning the output of a
`configure_workers` run into the rows it offers and a chosen row into a `configure_workers` command
line, is `pi_models.ts`, installed beside it. Tests run it under Node; the dialogs themselves were
exercised by driving a pi RPC session.

The pi extension is the only part of this Module that is code meeting other Modules directly. It
observes what they record and starts their commands, and the records it reads stay theirs:

```d2
view: pi run view
picker: pi model picker
round: Task sessions / Session round
wprogress: Workers / Progress file
oprogress: Operations / Operation progress file
configure: Operations / configure_workers
view -> round: follows
view -> wprogress: reads
view -> oprogress: reads
picker -> configure: applies choices with
```

<a id="uses-workers"></a>

**Workers** keeps each worker run's [progress
file](../workers/module.md#concept.workers.progress-file). The run view relies on it
recording the phase, round and latest tool call, and the host process that launched the worker,
and on it being an observation only: the run record, not the progress file, is the evidence, so the
view shows but never judges a run from it. Workers also owns the [worker model
configuration](../workers/module.md#concept.workers.model-configuration); the model picker
and the guidance change its model choices only through the `configure_workers` Operation, which
lists the candidates and validates every choice, so neither writes them itself. Its `backend`
section is the exception: no Operation changes it, so the main agent edits it by hand on the
developer's request and `configure_workers` validates the result.

### Who relies on it

Three Modules consume what this one authors. [Distribution](../../distribution/module.md) renders
the guidance sources and installs the rendered guidance and the pi extension into a project;
[Dogfooding](../../dogfooding/module.md) appends its own section to the guidance in a develop
install and changes nothing else; and [Task sessions](../task-session/module.md) gives a task
session the rendered task-session guidance as its first prompt, so a delegated task follows the
same method the main agent follows when it works the task itself.
