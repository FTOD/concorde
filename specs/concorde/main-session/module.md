# Main session

## Purpose

Main session is the guidance that makes an ordinary Claude Code session in a project's primary
worktree act as Concorde's main agent: discuss work with the developer, split it into tasks, run
Operations and read their results, keep each task's decision log, decide ordinary questions itself
while escalating only major ones, merge delivered tasks, and handle Issues. It is advice to a
model, not enforcement — Concorde places no permission limits on the main agent, and nothing here
constrains the developer. Distribution renders and installs this Module's content.

## Terminology

| Term | Definition |
| --- | --- |
| Main-session guidance | The Claude Code instructions, installed as a project skill and a `CLAUDE.md` block, that tell the main agent how to work with Concorde. |
| Escalation policy | The rule by which the main agent decides ordinary questions itself, records and reports them, and asks the developer only for decisions with major impact. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
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

**What the main agent is told.** The installed guidance tells the Claude Code session opened in a
Concorde project's primary worktree that it is the main agent, and gives it a working method:

- **Discuss first.** Agree the direction with the developer before changing anything.
- **Split into tasks.** Turn agreed work into [tasks](../tasks/module.md#concept.tasks.task),
  opened with `concorde task`. Run tasks in parallel only across worktrees whose Modules and shared
  files do not overlap; run the rest one after another
  ([requirements](requirements.md#req.main-session.parallel-by-worktree)).
- **Run Operations, do not edit.** Change Specs or code only by running
  [Operations](../operations/module.md#concept.operations.operation) with
  `concorde run <operation> --task <task> …` in background Bash, then read the
  [Operation result](../operations/module.md#concept.operations.result), except for trivial
  housekeeping that changes no Spec meaning and no code behaviour, such as regenerating the
  registry mirror or resolving a mechanical merge conflict in it.
- **Keep the decision log.** Record every non-`ok` result and every unsupervised choice, with its
  reason, in the task's [decision log](../tasks/module.md#concept.tasks.decision-log).
- **Merge delivered work.** Merge a branch `delivery` committed without asking authorization, and
  record the merge; handle a later conflict or failed check as new work, never by discarding
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

The main agent never edits the project itself: its view is the whole project, so nothing would
bound, audit or evidence a change made directly. Tasks and Operations keep every change bounded and
recorded, and keep the primary worktree clean to merge; merging needs no authorization because
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
}
```

<a id="realization.main-session.guidance"></a>

The **guidance sources** live under `prompts/main-session/` (`skill.md`, installed as the project
skill `.claude/skills/concorde/SKILL.md`; `claude-md.md`, installed into the project's `CLAUDE.md`)
and are rendered by Distribution's build into `generated/main-session/`. Their tests, under
`tests/concorde/main_session/`, check that the rendered guidance states every rule the
[scenarios](scenarios.md) describe; what the main agent then does is judgment no deterministic test
observes.

## Relationships

```d2
mainsession: Main session
operations: Operations
tasks: Tasks
issues: Issues
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
