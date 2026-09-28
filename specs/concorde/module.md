# Concorde Framework

## Purpose

Concorde makes a project's [Specs](glossary.json#concept.spec) the
[harness](glossary.json#concept.agent-harness) of the AI agents that change it. The Specs describe
the architecture and divide the responsibility among [Modules](glossary.json#concept.module); from
that division Concorde computes, for each piece of work, what a
[worker](glossary.json#concept.worker) is given as [context](glossary.json#concept.context) and what
it may read and write, runs the worker inside that [boundary](glossary.json#concept.boundary) and
verifies its result instead of trusting it.

The developer and the [main agent](glossary.json#concept.main-agent) rely on it. Its work is
organized in two halves. The upper half, [Coordination](coordination/module.md), is project
management and task-level parallelism: the main session, in which the main agent works with the
developer on the whole project, and the task level, where each task gets its own branch and worktree
and is worked by the main agent itself or by a task session it delegates the task to. The lower
half, [Execution](execution/module.md), is the execution core: in one bound workspace, workflows
order runs for a known procedure; Operations complete bounded jobs with AI workers under
Spec-derived grants and return checked results;
[execution commands](glossary.json#concept.execution-command) such as `task-validation` and
`delivery` do the deterministic work; workers act at the bottom. The upper half hands a task to the
lower half only through the task worktree's workspace binding and learns what happened only from
what the lower half recorded. Spec tooling checks, serves and publishes the Specs on its own.
Concorde never chooses the developer's direction or repairs a [Spec](glossary.json#concept.spec) on
its own. The main agent and the workers run on Claude Code or on pi.

## Usage

Every term of the project is defined once in the [glossary](glossary.json), which this Module
declares, and linked where a document uses it. The [shared vocabulary](vocabulary.md) explains the
words every Module shares, such as the four kinds of context and the task types.

### The levels of work

Every piece of work on a Concorde project passes down the same levels, and every result and error
travels back up them. The first two are Coordination's, the rest Execution's:

| Level | Half | Who or what works there | Where | What it does | Module |
| --- | --- | --- | --- | --- | --- |
| 1. Main session | Coordination | the main agent, an interactive Claude Code or pi session | the primary worktree | discusses the project with the developer, splits work into tasks, merges delivered tasks, decides ordinary questions and escalates major ones | [Main session](coordination/main-session/module.md) |
| 2. Task | Coordination | the main agent inside the task, or a task session it delegated the task to | one task worktree | changes Specs and code directly or through runs of Execution, keeps the [decision log](glossary.json#concept.decision-log), validates and delivers | [Task sessions](coordination/task-session/module.md), with the workspace from [Tasks](coordination/tasks/module.md) |
| 3. Workflow | Execution | a procedure rendered for Claude Code and pi | one bound workspace | orders the workspace's runs for a known procedure and stops where the developer must decide | [Workflows](execution/workflows/module.md) |
| 4. Run | Execution | the Execution runner, running an [Operation](glossary.json#concept.operation) or an execution command | one bound workspace | completes one bounded job and returns one [run result](glossary.json#concept.run-result) with evidence: an Operation with AI workers, an execution command without | [Execution](execution/module.md), [Operations](execution/operations/module.md), [Commands](execution/commands/module.md) |
| 5. Worker | Execution | a headless `claude -p` or `pi -p` process | a run over the workspace | reasons within its grant on one bounded job and returns a [worker result](glossary.json#concept.worker-result) the run checks | [Workers](execution/workers/module.md) |

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
  task: "2  Task level\nthe main agent or a task session,\none task worktree" {class: agent}
  main -> task: "opens a task, enters it\nor delegates it"
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

Calls go only downward, and a level may be skipped: the task level runs an Operation or a command
directly whenever no workflow fits, and the execution commands use no worker at all. Nothing calls
upward. A worker never touches Git, runs an Operation or starts an agent; a run never starts another
run; a workflow never opens, merges or closes a task; nothing in Execution reads or writes a
[task record](glossary.json#concept.task-record); and only the main agent merges. A run's steps, and
the [Workers](execution/workers/module.md) code between a worker's rounds, call deterministic
services such as [Check execution](execution/checks/module.md) in-process; such a call is not a
level of its own, starts no run and returns to the step that made it, so that failing checks can
drive a repair loop inside one Operation.

The levels are levels of work, not of Modules. [Coordination](coordination/module.md) groups the
sessions and the task workspace; [Execution](execution/module.md) groups everything that works in a
bound workspace; and two Modules serve both halves without being a level, described under
[Design](#design).

### A normal path

The installer places the [Protocol copy](glossary.json#concept.protocol-copy) under
`.concorde/protocol/`, the `concorde` command and the
[main-session guidance](glossary.json#concept.main-session-guidance), but never writes the Specs;
initialization proposes and applies an honest first Spec. The developer then works with the main
agent in the primary worktree. For each piece of work it opens a task (a branch and a worktree under
`.claude/worktrees/`, which `concorde task open` binds as the task's workspace), enters that
worktree and works there with the worktree's own `concorde`: changing Specs and code directly,
running Operations with `concorde run <operation>` (`understand`, `specify`, `implement`/`test`,
`spec_review`/`code_review`), then the execution commands `concorde task-validation` and
`concorde delivery`, until `delivery` commits the result and its evidence on the task branch. None
of these names the task: each reads the worktree's binding. The main agent then returns to the
primary worktree and merges. For work split into several tasks, it starts a
[task session](glossary.json#concept.task-session) per task with `concorde task session`, which does
the same inside its task and reports back, so several tasks run at once. Before any change, a
read-only Operation such as `understand` or a review may also run in the primary worktree itself, as
an [unbound run](glossary.json#concept.unbound-run) that reads that worktree as it stands and
changes nothing.

The normal path moves from opening a task to work in its bound workspace, then back to the main
agent for merge. Operations, validation and delivery run through Execution in the task worktree;
only the main agent merges in the primary worktree.

```d2 illustrative
grid-rows: 1
primary: "Primary worktree\nMain agent" {
  grid-columns: 1
  vertical-gap: 152
  open: "Open task\nbranch + bound worktree"
  merge: "Merge delivered task"
}
task: "Task worktree\nMain agent or task session" {
  grid-columns: 1
  work: "Change Specs and code\ndirectly or through Operations"
  validate: "task-validation\ncheck readiness"
  deliver: "delivery\ncommit result + evidence"
  work -> validate -> deliver
}
primary.open -> task.work: enter or delegate
task.deliver -> primary.merge: delivered
```

Some tasks follow a known procedure. A [workflow](execution/workflows/module.md) records that
procedure: the main agent opens a task as usual and starts the workflow inside its worktree, which
orders the workspace's runs one at a time and returns one
[workflow result](glossary.json#concept.workflow-result). In **interactive** mode it ends at each
point that needs the developer's decision, so the main agent can ask right away and start it again
with the answers; in **no-ask** mode it follows its declared continuation rules and reports every
decision and problem at the end. The first workflow is `brownfield`: after installation and
initialization of a project whose code came before any Spec, it surveys the code, scaffolds child
Modules, describes each [Module](glossary.json#concept.module)'s code with `code_to_spec`, reviews
and validates the result and delivers it.

| Command | Use it to | Provided by |
| --- | --- | --- |
| `concorde spec-validation` | check the structure of the Specs | [Spec core](spec-tooling/spec/module.md) |
| `concorde grant` | compute a [task type](glossary.json#concept.task-type)'s grant for some Modules | [Spec core](spec-tooling/spec/module.md) |
| `concorde spec-mcp` | let an agent query Modules, context and grants over MCP | [Spec MCP server](spec-tooling/spec-mcp/module.md) |
| `concorde task` | open, list, show and close tasks, start task sessions, escalate, merge | [Tasks](coordination/tasks/module.md) |
| `concorde run` | run one Operation in the workspace of the current worktree | [Execution](execution/module.md) with [Operations](execution/operations/module.md) |
| `concorde task-validation`, `concorde delivery`, `concorde scaffold` | decide readiness, deliver, create surveyed Modules, in the current workspace | [Commands](execution/commands/module.md), with [Validation](execution/commands/validation/module.md), [Delivery](execution/commands/delivery/module.md) and [Scaffold](execution/commands/scaffold/module.md) |
| `concorde workflow` | run the steps of a workflow in the current workspace and report its result | [Workflows](execution/workflows/module.md) |
| `concorde configure-workers` | list and change the [worker model configuration](glossary.json#concept.worker-model-configuration) of the current worktree | [Workers](execution/workers/module.md) |

### Errors

Every run returns a structured result; a failure carries an
[error chain](glossary.json#concept.error-chain): the run's own detailed link saying why it cannot
handle the error, with each error it received nested as a cause with its own reason, and every
`concorde` command refuses in the same shape, except Spec tooling's deterministic commands, which
report with Spec tooling's own error record. The chain climbs the levels: a worker reports its link
to Workers, the Operation adds its own, a workflow keeps each run's chain whole in its result, a
task session escalates to the main agent with its link on top, and the main agent adds its link
above that when the developer must decide. The main agent reads the chain, decides what it can, logs
the decision, escalates only a major-impact one, and adds its own link rather than summarizing. A
step needing an unstated promise stops with a [Spec gap](glossary.json#concept.spec-gap) instead of
inferring it from code; outside a `specify` run and the
[Adoption](execution/operations/adoption/module.md) route (`code_to_spec` and the `scaffold` command
that writes what a survey proposed), only the developer, the main agent and a task session within its
task's goal change Specs.

## Design

The Spec, not the code, is the shared source of truth between the developer and the agents, and
the responsibility it assigns to each Module is also the boundary of every worker bound to that
Module. Every other choice follows from making that safe: what a worker may read and write is
computed from the Specs, a worker's answer is checked by a program rather than trusted, and a
missing promise stops work instead of being inferred from code.

Concorde's normal flow is therefore Spec first: a promise is written, then realized. Only a project
whose code came before its Specs is described the other way round, and only through one explicit
route, the Protocol's `code-to-spec` task type, which the
[Adoption](execution/operations/adoption/module.md) Operations use. It writes down the behaviour it
reads as it is, never changes code, and turns every behaviour whose intent the code does not settle
into an [open question](glossary.json#concept.open-question) for the developer rather than a
promise. Once a Module is described, work on it is Spec first again.

### Two halves, one seam

Project management and the execution core change for different reasons. How tasks are opened,
parallelized, delegated and merged follows how the developer wants to work; how a worker is bounded
by the Specs, launched, audited and checked follows the Protocol and is Concorde's core. So they are
two halves with one narrow seam. The upper half writes a
[workspace binding](glossary.json#concept.workspace-binding) into each task worktree and reads what
the lower half recorded: its runs in the [run store](glossary.json#concept.run-store) and its
[delivery commits](glossary.json#concept.delivery-commit) on the task branch. The lower half reads
the binding and never learns that tasks exist. No record is written by both, so whether a task is
active or delivered is derived each time from what happened, never kept as a second copy that could
disagree; and the execution core can serve any workspace someone prepares, not only a task.

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
coordination.main -> execution.runs: starts in the task worktree
coordination.task -> execution.runs: starts in its worktree
execution.runs -> execution.binding: read
execution.runs -> execution.store: record
coordination.tasks -> execution.store: reads
```

### Agents at both ends, programs between

A model is needed in two places, for opposite reasons. At the top, someone must understand the
developer, see the whole project and judge what to do next; the main agent has the global view and
the developer's trust, so Concorde does not restrict it, but it changes the project only inside a
task worktree. At the bottom, someone must read and write code and Specs; a worker has one bounded
job, no human to ask, and a boundary derived from the Specs. Keeping the two apart lets a large
change be split into small, checkable steps without the developer supervising each one.

The levels between them are programs on purpose. What happens to a worker's answer decides what
the next level sees, so it must be reproducible and checkable rather than another model's opinion:
an Operation computes the grant, launches and audits the worker, runs the checks and turns the
outcome into a trustworthy result, and a workflow's order and continuation rules are declared in
its procedure. A judgment therefore never passes from one model to another without a program having
checked it, and the levels that can be wrong in a model's way stay at the two ends, where the grant
and the developer bound them. An Operation exists only where a model works: deterministic steps,
such as deciding readiness and delivering, are execution commands, which the same runner records
without any worker machinery.

The task level between the main session and the programs is stable, but who plays it is not: the
main agent works a task itself unless it wants several tasks to run at once, and then delegates
each to a task session, since a session is inside one task worktree at a time and runs that
worktree's own `concorde`. An extra level of messaging is one more place for an error to be lost,
so the loss is prevented structurally: a task session escalates with
`concorde task escalate --by task-session`, which records its link with the failed runs' chains
unchanged as causes, and the main agent adds its own link on top. A task session's writes are
confined to its task, while the main agent stays unrestricted and alone merges. Where a task's
commands run with the branch's own copy of the Framework, as in Concorde's own source checkout,
their success is self-validation, which is why a merge there runs the build and `spec-validation`
once more on the primary branch; in an installed project a task worktree ordinarily runs the
primary worktree's copy ([Distribution](distribution/module.md)).

One task through the Modules; each arrow is declared by the calling Module's own `uses`:

```d2 illustrative
shape: sequence_diagram
m: Main agent
t: Tasks
r: Execution runner
s: Spec core
w: Worker
c: Check execution
m -> t: open a task (branch, worktree, workspace binding)
m -> r: concorde run implement (in the task worktree)
r -> s: grant for the task type and Modules
r -> w: launch with settings, brief and grant
w -> r: worker result {style.stroke-dash: 3}
r -> r: audit writes against the grant
r -> c: run configured checks
r -> m: run result with evidence {style.stroke-dash: 3}
m -> r: concorde task-validation, then concorde delivery
m -> t: merge the task branch (delivered: read from the delivery commit)
```

### Modules that serve both halves

Two Modules serve both halves without being a level: the Harness, drawn below, and Spec tooling,
which is not drawn because nearly every Module relies on it. Every agent gets its harness from one
Harness:

```d2 illustrative
coordination: Coordination
execution: Execution
harness: Harness
coordination -> harness
execution -> harness
```

What an agent may know and touch is its harness, and the [Harness](harness/module.md) generates it
for every level from the same code: a worker's from its grant — on Claude Code settings with deny
rules, a [write hook](glossary.json#concept.write-hook) and the Bash sandbox, on pi a
[permission extension](glossary.json#concept.permission-extension) with the same sandbox engine —
and a task session's from its task. It guards against scope drift and mistakes, not a malicious
actor; the Harness explains why these layers were chosen and what they leave out.

Nearly every Module relies on [Spec tooling](spec-tooling/module.md): its Spec core loads and checks the Specs and computes the grants, and a Module refuses to act on a
structure it reports untrustworthy. Its core uses no other Module, so the Specs can be checked,
served and published without any agent.

### Around the framework

Three Modules face the people who install, test and develop Concorde rather than a project's work:
Distribution installs the main-session guidance, the workflows and the docsite of
[Views](spec-tooling/views/module.md) into a project;
Dogfooding runs a [develop install](glossary.json#concept.develop-install) and reports Concorde's
defects as Issues; and End-to-end testing runs installed Concorde on real codebases.

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

### Errors as a chain

Errors travel as a chain because every level handles some errors and must pass the others up:
Workers resumes a worker for a failing check but not for a Spec gap, a run reruns nothing, and the
main agent decides ordinary questions but not the project's direction. An error passed up as a bare
code or a one-line summary loses exactly what the next level needs to decide, and an error each
level re-describes in its own words drifts from what happened. So a level that cannot handle an
error adds one link and keeps the rest: its detailed account, the specific reason it cannot handle
the error, taken from a small fixed set such as a missing permission, a decision reserved to a
higher level or used-up rounds, the options it sees, and the errors it received as causes,
unchanged. The chain is structured data with one [contract](contracts.md#contract.concorde.error),
checked by the runner against its schema and extended by the main agent with a command rather than
paraphrased, so the developer receives the whole path from the failing check up to the question they
are asked.

<a id="realization.concorde.error-chain"></a>

**Error chain code** builds and renders the links of an
[error chain](glossary.json#concept.error-chain) in the shape of the Framework's
[error contract](contracts.md#contract.concorde.error): the schema, the reasons a level cannot
handle an error, helpers turning an exception or finding into a link, and the human rendering.
Workers and Check execution report their failures with it, and so do the Execution runner, Tasks,
Task sessions and the Issues command, so every level's link has the same shape whoever wrote it. The
root binds it because the contract is the root's and every Module promises it. Spec tooling keeps
its own error types and does not use it.

### The children

The root is the composition of eight child Modules, listed here by the part they play.

<a id="contains-coordination"></a>

**Coordination** is the upper half: the Main session at level 1 and the task level at level 2,
played by the main agent or delegated through Task sessions, with each task's workspace from Tasks.
It hands work to Execution only by binding a task worktree and derives each task's state from what
Execution recorded.

<a id="contains-execution"></a>

**Execution** is the lower half, levels 3 to 5 in one bound workspace: Workflows, the runner that
runs Operations and execution commands, the
[Operation catalog](glossary.json#concept.operation-catalog) and its providers, the
[command catalog](glossary.json#concept.command-catalog) with Validation, Delivery and Scaffold,
Workers and Check execution. It knows no task and records every run in its run store.

<a id="contains-harness"></a>

The **Harness** derives each agent's harness — what it may know, what it may touch and the
environment it runs in — and applies it through Claude Code's or pi's own configuration, the same
code for every level.

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

### Files of the root

The root also binds files that belong to no single child. They keep the repository running rather
than carry the framework's function, so no diagram above draws them:

- <a id="realization.concorde.project-files"></a>**Project files** are what belongs to no single
  responsibility: README, agent instructions, licence, repository configuration and the CI workflow
  that validates this checkout.
- <a id="realization.concorde.user-documents"></a>**User documents** under `docs/` are written for
  the people who use Concorde, starting with the guide to using it. They follow no Spec Protocol
  structure and are never agent context; the docsite publishes them as its
  [user documents](glossary.json#concept.user-documents), the first tab, with
  `docs/README.md` as the site's home page.
- <a id="realization.concorde.development-environment"></a>**Development environment** is this
  checkout's Python project and lock, pytest setup and shared test support, the reference
  initializer, the Claude Code documentation fetcher, the docsite type check, and the tests of that
  environment; see [Development environment](development.md).
- <a id="realization.concorde.acceptance-tests"></a>**Acceptance tests** exercise the root's
  cross-Module [scenarios](scenarios.md) through the installer and the `concorde` command.
