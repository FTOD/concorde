# Concorde Framework

## Purpose

Concorde makes a project's [Specs](glossary.json#concept.spec) the
[harness](glossary.json#concept.agent-harness) of the AI agents that change it. The Specs describe
the architecture and divide the responsibility among [Modules](glossary.json#concept.module); from
that division Concorde computes, for each piece of work, what a
[worker](glossary.json#concept.worker) is given as [context](glossary.json#concept.context) and what
it may read and write, runs the worker inside that [boundary](glossary.json#concept.boundary) and
verifies its result instead of trusting it.

The developer and the [main agent](glossary.json#concept.main-agent) rely on it. Concorde never
chooses the developer's direction or repairs a Spec on its own. The main agent and its task sessions
run on Claude Code for now; each worker runs on Claude Code or on pi.

## Core concepts

Concorde rests on three ideas: a project described as Modules, each with its Spec; three kinds of
agent that work on it, each at its own level; and a context and a boundary computed for every worker
from the Specs. The [glossary](glossary.json), which this Module declares, defines every term of the
project once. This section explains the terms this Module owns; every other Module explains its own,
such as [Operation](glossary.json#concept.operation), [Task](glossary.json#concept.task),
[Grant](glossary.json#concept.grant) or [Issue](glossary.json#concept.issue).

### Modules and Specs

<a id="concept.module"></a><a id="concept.spec"></a>

A **[Module](glossary.json#concept.module)** is one responsibility, such as reviewing code or
publishing documentation. Its **[Spec](glossary.json#concept.spec)** is the set of documents it
owns, written under the Spec Protocol: an entry that explains the Module, optional topics, and
implementation documents with precise requirements, scenarios and contracts. A Module may span
several directories, share files with others, or have no files at all. The Spec, not the code, is
the shared source of truth between the developer and the agents, and the responsibility it assigns
to a Module is also the boundary of every worker bound to that Module.

### The people and agents

<a id="concept.main-agent"></a>

The developer sets the project's direction with the
**[main agent](glossary.json#concept.main-agent)**, the Claude Code session in the primary
worktree. Its project-wide view lets it judge which responsibilities a change affects and which
questions need the developer. It hands every task to a task session, so that it remains free to talk
with the developer and to answer every session; only a small change the developer approved does it
make itself. It alone merges a task into the primary branch.
[Main session](coordination/main-session/module.md) explains its working method and decision
policy.

<a id="concept.task-session"></a>

A **[task session](glossary.json#concept.task-session)** carries one task to delivery inside the
task's own worktree: it may change Specs and code directly or use Operations, then validate and
deliver. That responsibility is broader than a worker's single bounded job. It never asks the
developer in place: it gathers the decisions its task needs and reports them to the main agent
together. [Task sessions](coordination/task-session/module.md) explains its lifecycle.

<a id="concept.worker"></a>

A **[worker](glossary.json#concept.worker)** is a headless AI process that receives a frozen grant
for one job. Its answer is a proposal until the program that launched it verifies it; it cannot
substitute its own judgement for the checks around it. [Workers](execution/workers/module.md)
explains how it is launched, audited and recorded; Workers, plural, names that Execution code, not
the AI process itself. [Agents at both ends, programs
between](#agents-at-both-ends-programs-between) explains why model reasoning and deterministic steps
occupy different levels.

### Context and boundaries

<a id="concept.task-type"></a>

A **[task type](glossary.json#concept.task-type)** fixes access to the
[boundary sets](glossary.json#concept.boundary-set) of the bound Modules. For example, `specify`
grants writes to their Specs and `implement` to their code; `code-to-spec` reads existing code to
describe it in Specs when the code came first. The Protocol defines the complete access table.

<a id="concept.boundary"></a>

A task's **boundary** is the read and write limits its task type assigns to its bound Modules. The
Protocol defines the sets and the task types; how far Concorde enforces the boundary of a worker is
explained by the [Harness](harness/module.md).

<a id="concept.context"></a>

The **context** of one worker is everything it may know. It always has the same five kinds, each
computed from declarations or produced for the task rather than chosen by hand. Some kinds may be
empty for a given task, but never all five:

- <a id="concept.spec-context"></a>The **[Spec context](glossary.json#concept.spec-context)** is
  what the Protocol calls the SpecContext of the bound Modules: the documents they own and the
  documents their `contains`, `uses` and `includes` select, one level deep, and the glossary entries
  of the terms they use. It is read only. A provider's Specs arrive here instead of its code. It
  holds only the project's own documents and terms, never external material.
- <a id="concept.external-context"></a>The
  **[external context](glossary.json#concept.external-context)** is what the Protocol calls the
  ExternalContext of the bound Modules: the documentation and source of external dependencies that
  their `external` inclusions pin, such as a library's reference documentation or a vendored copy of
  its code, checked out at the commit the project's version control records. Only the bound
  Modules' own inclusions count; a Module their relations select brings none. Every task type grants
  it read only, beside the Spec context. It explains how a dependency works and never adds a promise
  the Spec does not state.
- <a id="concept.implementation-context"></a>The
  **[implementation context](glossary.json#concept.implementation-context)** starts from the
  Protocol's ImplementationContext, the names of the files the bound Modules' realizations bind.
  Only when the task type grants it, as for `implement`, `test`, `review-code` and `code-to-spec`,
  does it also carry contents: the whole project's code, the Protocol's ProjectImplementation, which
  also holds every Module's external material, so that a task reading code reads the code it uses;
  it may change at most the bound Modules' ImplementationScope. An `understand` worker sees only the
  names.
- <a id="concept.capability-context"></a>The
  **[capability context](glossary.json#concept.capability-context)** is not a Protocol set. It is
  the list of tools the worker may use, fixed by its Operation and task type, and the contract of the
  result it must return. It tells the model what it can do, never what the project promises.
- <a id="concept.task-context"></a>The **[task context](glossary.json#concept.task-context)** is
  what the Protocol calls task material: the brief with the task and its constraints, the admitted
  artifacts of earlier steps, such as an accepted assessment or the diff to review, and the explicit
  lists of paths the worker may change, read or only know by name. It is produced for the task and
  adds no source; it never replaces a Spec document or a file.

### Evidence and errors

<a id="concept.evidence"></a>

**[Evidence](glossary.json#concept.evidence)** is what a check or an independent review recorded
about specific inputs. When any of those inputs change, the evidence no longer applies; it is never
a permanent property of a Module, and a Spec never stores it. A failure is never reduced to a
status: it travels up as an [error chain](glossary.json#concept.error-chain) that keeps the original
failure and why each receiving level could not handle it, and every level leaves a [trace
node](glossary.json#concept.trace-node) of what it did.

## Overview

Three pictures give the whole framework: the levels every piece of work passes through, the life of
one task across them, and the Modules that carry them.

### The levels of work

Every change to a Concorde project passes down the same five levels, and every result and error
travels back up them. The first two are Coordination's, where agents decide what to work on; the
other three are Execution's, where one bound workspace is worked on.

```d2 illustrative
classes: {
  agent: {style: {fill: "#e8edff"; stroke: "#3b5bdb"; stroke-width: 2; border-radius: 6; font-size: 15}}
  program: {style: {fill: "#f3f4f6"; stroke: "#6b7280"; stroke-width: 2; border-radius: 6; font-size: 15}}
  layer: {style: {fill: transparent; stroke: "#9aa3b2"; stroke-dash: 4; border-radius: 10; font-size: 16; bold: true}}
}
developer: Developer {shape: person}
coordination: "Coordination: project management" {
  class: layer
  main: "1  Main session\nthe main agent, primary worktree,\nthe whole project" {class: agent}
  task: "2  Task level\na task session,\none task worktree" {class: agent}
  main -> task: "opens a task and\ndelegates it"
}
execution: "Execution: the core, in one bound workspace" {
  class: layer
  workflow: "3  Workflow\norders one workspace's runs\nfor a known procedure" {class: program}
  run: "4  Run\nan Operation (with workers)\nor an execution command" {class: program}
  worker: "5  Worker\nheadless AI, one job\nunder a grant" {class: agent}
  workflow -> run: "runs, one at a time"
  run -> worker: launches
}
developer -> coordination.main: "discusses, decides"
coordination.task -> execution.workflow: "starts, in the task worktree"
coordination.task -> execution.run: "or runs directly"
```

| Level | Who or what works there | What it does | Module |
| --- | --- | --- | --- |
| 1. Main session | the main agent, in the primary worktree | discusses the project with the developer, splits work into tasks, merges delivered tasks | [Main session](coordination/main-session/module.md) |
| 2. Task | a task session, in one task worktree | changes Specs and code directly or through runs, keeps the [decision log](glossary.json#concept.decision-log), validates and delivers | [Task sessions](coordination/task-session/module.md), [Tasks](coordination/tasks/module.md) |
| 3. Workflow | a procedure rendered as a Claude Code workflow | orders the workspace's runs for a known procedure and stops where a decision is needed | [Workflows](execution/workflows/module.md) |
| 4. Run | the Execution runner | runs an [Operation](glossary.json#concept.operation), with workers, or an [execution command](glossary.json#concept.execution-command), without, and returns one [run result](glossary.json#concept.run-result) with evidence | [Execution](execution/module.md) |
| 5. Worker | a headless `claude -p` or `pi -p` process | reasons within its grant on one bounded job and returns a [worker result](glossary.json#concept.worker-result) the run checks | [Workers](execution/workers/module.md) |

Calls go only downward, and results and errors come back up; [Agents at both ends, programs
between](#agents-at-both-ends-programs-between) explains why the levels are split this way.

Work that only reads need not open a task. The main agent may start an
[unbound run](glossary.json#concept.unbound-run), such as an `understand`, a `survey` or a Spec
review, directly in the primary worktree: it has no workspace, and its steps and workers work in a
throwaway detached checkout of that worktree's `HEAD`, so it examines what is committed there, never
uncommitted changes, and changes nothing. [Execution](execution/module.md#unbound-runs) explains it.

### The life of a task

Every change of a Spec or of code is a task, and every task takes the same path. The main agent
opens it, which creates a branch and a worktree bound as the task's
[workspace](glossary.json#concept.workspace), records its brief in the
[decision log](glossary.json#concept.decision-log) and starts a task session there. The task session
changes Specs and code, itself or through runs of Execution, each of which returns a run result with
evidence, and may commit each verified step on the task branch. Decisions that are not its own go up
to the main agent together, which decides them or asks the developer, and the answers come back
down. When the work is done, the task session delivers the workspace: `delivery` validates it whole
and, when it is ready, commits what is left in a
[delivery commit](glossary.json#concept.delivery-commit), which alone marks the task delivered, and
the main agent merges the delivered task. A task that follows a known procedure, such as describing
existing code, runs as a [workflow](execution/workflows/module.md) inside the same path.

```d2 illustrative
grid-columns: 3
horizontal-gap: 100
main: "Main agent\nprimary worktree" {
  grid-columns: 1
  vertical-gap: 50
  open: "1. Open a task:\nbranch, worktree,\nworkspace binding"
  brief: "2. Record the brief,\nstart a task session"
  answer: "Decide, or ask\nthe developer"
  gap: "" {style.opacity: 0}
  merge: "6. Merge the task\ninto the primary branch"
}
session: "Task session\ntask worktree" {
  grid-columns: 1
  vertical-gap: 50
  gap1: "" {style.opacity: 0}
  work: "3. Change Specs and code,\ndirectly or through runs"
  gap2: "" {style.opacity: 0}
  deliver: "5. Validate and deliver"
  gap3: "" {style.opacity: 0}
}
execution: "Execution\nthe task's workspace" {
  grid-columns: 1
  vertical-gap: 50
  gap1: "" {style.opacity: 0}
  run: "4. Run an Operation:\ngrant, worker,\naudit, checks"
  gap2: "" {style.opacity: 0}
  commit: "Delivery commit\non the task branch"
  gap3: "" {style.opacity: 0}
}
main.open -> main.brief
main.brief -> session.work: starts
session.work <-> execution.run: "run and\nrun result"
session.work <-> main.answer: "escalations\nand answers"
session.work -> session.deliver
session.deliver -> execution.commit
execution.commit -> main.merge: delivered
```

The commands behind each step, how tasks run in parallel and how a merge is checked are explained
by [Main session](coordination/main-session/module.md), [Tasks](coordination/tasks/module.md) and
[Task sessions](coordination/task-session/module.md); a run's steps by
[Execution](execution/module.md).

### The Modules

The levels are levels of work, not of Modules. [Coordination](coordination/module.md) holds levels 1
and 2 and [Execution](execution/module.md) levels 3 to 5; the Harness and Tracing serve both halves
without being a level, Issues keeps the problems worth remembering, and all of them rely on the Spec
core of [Spec tooling](spec-tooling/module.md) to load and check the Specs. Each arrow is a declared
`uses`, drawn from the child Module that declares it where that shows why the dependency exists: the
Workers of Execution run under the Harness, the Tasks of Coordination keep their traces with
Tracing, and the Main session records Issues.

```d2
coordination: Coordination {
  main: Main session
  tasks: Tasks
}
execution: Execution {
  workers: Workers
}
harness: Harness
tracing: Tracing
issues: Issues
spec_tooling: Spec tooling {
  spec: Spec core
}
coordination -> execution
coordination -> harness
coordination.main -> issues
coordination.tasks -> tracing
execution -> tracing
execution.workers -> harness
execution -> spec_tooling.spec
harness -> spec_tooling.spec
tracing -> spec_tooling.spec
issues -> spec_tooling.spec
```

## How it is built

### Spec first

Because the Spec is the source of truth, every other choice follows from making that safe: what a
worker may read and write is computed from the Specs, a worker's answer is checked by a program
rather than trusted, and a missing promise stops work instead of being inferred from code. A step
needing an unstated promise stops with a [Spec gap](glossary.json#concept.spec-gap) instead; outside
a `specify` run and the [Adoption](execution/operations/adoption/module.md) route, only the
developer, the main agent and a task session within its task's goal change Specs.

Concorde's normal flow is therefore Spec first: a promise is written, then realized. Only a project
whose code came before its Specs is described the other way round, and only through one explicit
route, the Protocol's `code-to-spec` task type, which the
[Adoption](execution/operations/adoption/module.md) Operations use together with the `scaffold`
command that writes what a survey proposed. It writes down the behaviour it reads as it is, never
changes code, and turns every behaviour whose intent the code does not settle into an
[open question](glossary.json#concept.open-question) for the developer rather than a promise. Once
a Module is described, work on it is Spec first again.

### Two halves, one seam

Project management and the execution core change for different reasons. How tasks are opened,
parallelized, delegated and merged follows how the developer wants to work; how a worker is bounded
by the Specs, launched, audited and checked follows the Protocol and is Concorde's core. So they are
two halves with one narrow seam: the upper half reaches the lower one only through a
[workspace binding](glossary.json#concept.workspace-binding), Execution's commands and what
Execution recorded. It writes the binding into each task worktree, runs Execution's commands inside
that worktree and reads what the lower half recorded: its runs in the
[run store](glossary.json#concept.run-store), with their
[run progress files](glossary.json#concept.run-progress-file), and its
[delivery commits](glossary.json#concept.delivery-commit) on the task branch. The lower half reads
the binding and never learns that tasks exist. No record is written by both, so whether a task is
active or delivered is derived each time from what happened, together with the task branch's head
and whether its worktree is clean, never kept as a second copy that could disagree; and the
execution core can serve any workspace someone prepares, not only a task.

```d2 illustrative
coordination: Coordination {
  main: Main session
  task: Task sessions
  tasks: Tasks
}
execution: Execution {
  binding: Workspace binding
  runs: "Runs: Operations and\nexecution commands"
  store: Run store and delivery commits
}
coordination.tasks -> execution.binding: writes
coordination.main -> execution.runs: "starts unbound runs\nin the primary worktree"
coordination.task -> execution.runs: starts in its worktree
execution.runs -> execution.binding: read
execution.runs -> execution.store: record
coordination.tasks -> execution.store: reads
```

### Agents at both ends, programs between

A model is needed in two places, for opposite reasons. At the top, someone must understand the
developer, see the whole project and judge what to do next; the main agent has the global view and
the developer's trust, so Concorde does not restrict it, but it hands every task to a task session
and never works inside a task worktree itself; in the primary worktree it makes only a small change
the developer approved. At the bottom, someone must read and write code and Specs; a worker has one
bounded job, no human to ask, and a boundary derived from the Specs. Keeping the two apart lets a
large change be split into small, checkable steps without the developer supervising each one.

The levels between them are programs on purpose. What happens to a worker's answer decides what the
next level sees, so it must be reproducible and checkable rather than another model's opinion: an
Operation computes the grant, launches and audits the worker, runs the checks and turns the outcome
into a result whose host evidence the task level can trust, and a workflow's order and continuation
rules are declared in its procedure. A worker's answer therefore never reaches the task level
without a program having checked it. The two agents of Coordination exchange their judgments
directly instead: a task session reports its decisions and escalations to the main agent, which
answers them or asks the developer, and no program judges either side; the decision log records them
for the main agent and the developer to read. What a task session changes, itself or through runs,
is checked by programs before it counts: `delivery` delivers the workspace only when it validates
whole, and a merge can run checks on the primary branch once more. An Operation exists only where a
model works: deterministic steps, such as deciding readiness and delivering, are execution commands,
which the same runner records without any worker machinery.

Keeping one session inside one task worktree makes parallel tasks independent: the main agent
delegates each task to a task session whose writes are confined to that task, while retaining the
project-wide view, the conversation with the developer and sole responsibility for merging. The
[error chain](#errors-as-a-chain) preserves failures across that extra session. Where a task's
commands run with the branch's own copy of the Framework, as in Concorde's own source checkout,
their success is self-validation, which is why a merge there runs the build and `spec-validation`
once more on the primary branch; in an installed project a task worktree ordinarily runs the primary
worktree's copy ([Distribution](distribution/module.md)).

Calls go only downward, and a level may be skipped: the task level runs an Operation or a command
directly whenever no workflow fits, and the execution commands use no worker at all. Nothing calls
upward. A worker never touches Git, runs an Operation or starts an agent; a run never starts another
run; a workflow never opens, merges or closes a task; nothing in Execution reads or writes a [task
record](glossary.json#concept.task-record); and only the main agent merges a task into the primary
branch, a task session merging only the primary branch into its own task branch after a conflict. A
run's steps, and the [Workers](execution/workers/module.md) code between a worker's rounds, call
deterministic services such as [Check execution](execution/checks/module.md) in-process; such a call
is not a level of its own, starts no run and returns to the step that made it, so that failing
checks can drive a repair loop inside one Operation.

### Modules that serve both halves

The Harness, Tracing and Spec tooling serve both halves without being a level.

What an agent may know and touch is its harness, and the [Harness](harness/module.md) generates it
for every level from the same code: a worker's from its grant — on Claude Code settings with deny
rules, a [write hook](glossary.json#concept.write-hook) and the Bash sandbox, on pi a
[permission extension](glossary.json#concept.permission-extension) with the same sandbox engine —
and a task session's from its task. It guards against scope drift and mistakes, not a malicious
actor; the Harness explains why these layers were chosen and what they leave out.

Nearly every Module relies on [Spec tooling](spec-tooling/module.md): its Spec core loads and
checks the Specs and computes the grants, and a Module refuses to act on a structure it reports
untrustworthy. Its core uses no other Module, so the Specs can be checked,
served and published without any agent.

Tracing gives every level the place and shape of its trace: each level records its own content,
and [Tracing](tracing/module.md) decides the structure it is kept in. While a task is current, its
record, decision log and traces are one folder, `.concorde/tasks/<task>/`; closing it moves that
folder to the [history](glossary.json#concept.history). A task's whole
[trace](glossary.json#concept.trace), from its sessions down to each worker round with its cost, is
read with `concorde trace show <task>`.

### Errors as a chain

Every run returns a structured result, and a failure carries an
[error chain](glossary.json#concept.error-chain) that climbs the levels: a worker reports its link
to Workers, the Operation adds its own, a workflow keeps each run's chain whole in its result, a
task session escalates to the main agent with its link on top, and the main agent adds its link
above that when the developer must decide. Every `concorde` command refuses in the same shape,
except Spec tooling's deterministic commands, which keep their own error types.
[Tracing](tracing/contracts.md#reading-an-error-chain) explains how to read a chain.

Errors travel as a chain because every level handles some errors and must pass the others up:
Workers resumes a worker for a failing check but not for a Spec gap, a run reruns nothing, and the
main agent decides ordinary questions but not the project's direction, which it logs and escalates
only when the impact is major. Every level therefore keeps the causes it received unchanged and
adds its own reason on top, in the shape of the
[error contract](tracing/contracts.md#contract.tracing.error), so the developer receives the whole
path from the failing check to the question they are asked. The chain is part of what
[Tracing](tracing/module.md#the-error-chain) retains, and it stays in band: each result carries its
chain whole.

### Around the framework

Three Modules face the people who install, test and develop Concorde rather than a project's work:
Distribution installs the [main-session guidance](glossary.json#concept.main-session-guidance), the
workflows and the docsite of [Views](spec-tooling/views/module.md) into a project; Dogfooding runs a
[develop install](glossary.json#concept.develop-install) and reports Concorde's defects as Issues;
and End-to-end testing runs installed Concorde on real codebases.

```d2
distribution: Distribution
dogfooding: Dogfooding
e2e: End-to-end testing
main: Main session
workflows: Workflows
views: Views
issues: Issues
distribution -> main
distribution -> workflows
distribution -> views
dogfooding -> distribution
dogfooding -> main
dogfooding -> issues
e2e -> distribution
e2e -> workflows
```

## The children

The root is the composition of nine child Modules, listed here by the part they play.

<a id="contains-coordination"></a>

**Coordination** is the upper half: the Main session at level 1 and the task level at level 2, where
a task session carries each task the main agent hands it, with each task's workspace from Tasks. It
hands work to Execution only by binding a task worktree and derives each task's state from what
Execution recorded.

<a id="contains-execution"></a>

**Execution** is the lower half, levels 3 to 5 in one bound workspace: Workflows, the runner that
runs Operations and execution commands, the
[Operation catalog](glossary.json#concept.operation-catalog) and its providers, the
command catalog with Validation, Delivery and Scaffold,
Workers and Check execution. It knows no task and records every run in its run store.

<a id="contains-harness"></a>

The **Harness** derives each agent's harness — what it may know, what it may touch and the
environment it runs in — and applies it through Claude Code's or pi's own configuration, the same
code for every level.

<a id="contains-tracing"></a>

**Tracing** decides which information about the work is combined and retained, and in what
structure: the uniform [trace node](glossary.json#concept.trace-node) every level records, nested
from a task down to each worker round, the folder of each task and its
[history](glossary.json#concept.history), the locks kept apart from the records, retention, the
`concorde trace` command that reads them, and the
[error chain](glossary.json#concept.error-chain). Every level produces its own content through it.

<a id="contains-spec-tooling"></a>

**Spec tooling** maintains and serves Specs — loading, checking, computing
[boundary sets](glossary.json#concept.boundary-set) and grants, answering agents over MCP, reviewing
and publishing them. Every other Module relies on it to refuse an untrustworthy structure; its core
uses no other Module.

<a id="contains-issues"></a>

**Issues** keeps durable, branch-local [Issue](glossary.json#concept.issue) records so a problem
worth keeping survives the task that found it; solving one is ordinary work run through Operations.

<a id="contains-distribution"></a>

**Distribution** builds the package, provides the `concorde` CLI and installs Concorde into a
project.

<a id="contains-dogfooding"></a>

**Dogfooding** lets the developer use Concorde on a real project while developing it: a develop
install runs the Concorde of an independent
[Concorde repository](glossary.json#concept.concorde-repository), the project's main agent watches
Concorde and reports its defects as [Issue reports](glossary.json#concept.issue-report), and the
Concorde repository fixes them under its own tasks, which the project then takes with an update. It
never changes Concorde from the project.

<a id="contains-e2e"></a>

**End-to-end testing** is how this project tests Concorde itself on real codebases from SWE-bench
with real agents, headless or through a deterministic driver. It serves the developers of
Concorde only and reaches no user's project.

## Files of the root

The root also binds files that belong to no single child. They keep the repository running rather
than carry the framework's function, so no diagram above draws them:

- <a id="realization.concorde.project-files"></a>**Project files** are what belongs to no single
  responsibility: README, agent instructions, licence, repository configuration, the `.mcp.json`
  that gives this checkout's Claude Code sessions the
  [project MCP server](glossary.json#concept.project-mcp-server) run by the worktree's own
  `scripts/concorde.py`, and the CI workflow that validates this checkout.
- <a id="realization.concorde.user-documents"></a>**User documents** under `docs/` are written for
  the people who use Concorde, starting with the guide to using it. They follow no Spec Protocol
  structure and are never agent context; the docsite publishes them as its
  user documents, the first tab, with
  `docs/README.md` as the site's home page.
- <a id="realization.concorde.development-environment"></a>**Development environment** is this
  checkout's Python project and lock, pytest setup and shared test support, the reference
  initializer, the Claude Code documentation fetcher, the docsite type check, and the tests of that
  environment; see [Development environment](development.md).
- <a id="realization.concorde.development-guidance"></a>**Development guidance** is the
  `concorde-development` skill's source, `prompts/development/skill.md`: how Concorde itself is
  developed in this checkout, which the build renders beside the `concorde` skill and which the
  checkout's agent instructions tell every session to load with it; see
  [Development environment](development.md#agent-instructions).
- <a id="realization.concorde.acceptance-tests"></a>**Acceptance tests** exercise the root's
  cross-Module [scenarios](scenarios.md) through the installer and the `concorde` command.
