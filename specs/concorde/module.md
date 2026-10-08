# Concorde Framework

## Purpose

Concorde makes a project's [Specs](glossary.json#concept.spec) the
[harness](glossary.json#concept.agent-harness) of the AI agents that change it. The Specs describe
the architecture. They divide the responsibility among [Modules](glossary.json#concept.module).
From that division, Concorde computes what each piece of work gives a
[worker](glossary.json#concept.worker) as [context](glossary.json#concept.context). It also computes
what the worker may read and write. Concorde runs the worker inside that
[boundary](glossary.json#concept.boundary). It verifies the worker's result instead of trusting it.

The developer and the [main agent](glossary.json#concept.main-agent) rely on it. Concorde never
chooses the developer's direction. It never repairs a Spec on its own. The main agent and its task sessions
run on Claude Code for now. Each worker runs on Claude Code or on pi.

Concorde is made of [parts](glossary.json#concept.part) that a project installs alone or in any
combination:

- The Spec tooling without any agent.
- The worker harness under another orchestrator.
- The task management without Concorde's method.
- Everything together.

Each part works without the parts it does not depend on. When a feature needs another part, it is an
[optional integration](glossary.json#concept.optional-integration).
It says plainly what is missing rather than failing.

## Core concepts

Concorde rests on four ideas:

- A project described as Modules, each with its Spec.
- Three kinds of agent that work on it, each at its own level.
- A context and a boundary computed for every worker from the Specs.
- Parts that can be installed apart.

The [glossary](glossary.json) defines every term of the project once.
This Module declares it.
This section explains the terms this Module owns. Every other Module explains its own, such as:

- [Operation](glossary.json#concept.operation).
- [Task](glossary.json#concept.task).
- [Grant](glossary.json#concept.grant).
- [Issue](glossary.json#concept.issue).

### Modules and Specs

<a id="concept.module"></a><a id="concept.spec"></a>

A **[Module](glossary.json#concept.module)** is one responsibility, such as reviewing code or
publishing documentation. Its **[Spec](glossary.json#concept.spec)** is the set of documents it
owns, written under the Spec Protocol:

- An entry that explains the Module.
- Optional topics.
- Implementation documents with these precise details:
  - Requirements.
  - Scenarios.
  - Contracts.

A Module may have any of these arrangements:

- It may span several directories.
- It may share files with others.
- It may have no files at all.

The Spec, not the code, is the shared source of truth between the developer and the agents.
The responsibility it assigns to a Module is also the boundary of every worker bound to that Module.

### The people and agents

<a id="concept.main-agent"></a>

The developer sets the project's direction with the
**[main agent](glossary.json#concept.main-agent)**, the Claude Code session in the primary
worktree. Its project-wide view lets it judge which responsibilities a change affects.
That view also lets it judge which questions need the developer.
It hands every task to a task session so that it remains free for these activities:

- Talking with the developer.
- Answering every session.

Of the changes of Spec meaning or code behaviour,
it makes itself only a small change the developer approved. It alone merges a task into the
primary branch.
[Main session](coordination/main-session/module.md) explains its working method and decision
policy.

<a id="uses-main-session"></a>

Every flow of this Module follows Main session's policy for who settles a question. The main agent
and a task session decide ordinary questions themselves
([req.main-session.ordinary-decisions](coordination/main-session/requirements.md#req.main-session.ordinary-decisions),
[req.main-session.task-session-decides](coordination/main-session/requirements.md#req.main-session.task-session-decides)).
A task session escalates every other question to the main agent
([req.main-session.task-session-escalates](coordination/main-session/requirements.md#req.main-session.task-session-escalates)).
Before acting on a decision of major impact, the main agent asks the developer
([req.main-session.escalation-policy](coordination/main-session/requirements.md#req.main-session.escalation-policy)).
Except for a small change the developer approved, the main agent makes every change of Spec meaning
or code behaviour in a task
([req.main-session.small-change](coordination/main-session/requirements.md#req.main-session.small-change)).
The main agent changes only these in the primary worktree itself
([req.main-session.tasks-own-changes](coordination/main-session/requirements.md#req.main-session.tasks-own-changes)):

- A small change the developer approved.
- Housekeeping that regenerates derived files.
- A commit of the worker configuration alone.

This Module states no decision policy of its own.
When that policy does not let a level settle a question, the question goes up with its error chain.
This continues until it reaches the developer.
Where the coordination part is not installed, Concorde has no main agent or task session.
There, whoever drives the other parts settles every question itself.

<a id="concept.task-session"></a>

A **[task session](glossary.json#concept.task-session)** carries one task to delivery inside the
task's own worktree. It may change Specs and code directly or use Operations. It then validates
and delivers the task. That responsibility is broader than a worker's single bounded job. It never asks the
developer in place. It gathers the decisions its task needs and reports them to the main agent
together. [Task sessions](coordination/task-session/module.md) explains its lifecycle.

<a id="concept.worker"></a>

A **[worker](glossary.json#concept.worker)** is a headless AI process that receives a frozen grant
for one job. Until the program that launched it verifies its answer, that answer is a proposal.
It cannot substitute its own judgement for the checks around it.
[Workers](worker-harness/workers/module.md) explains these aspects:

- How it is launched.
- How it is audited.
- How it is recorded.

Workers, plural, names that code of the worker harness. It does not name the AI process itself.
[Agents at both ends, programs
between](#agents-at-both-ends-programs-between) explains why model reasoning and deterministic steps
occupy different levels.

<a id="concept.agent-harness"></a>

An agent's **[agent harness](glossary.json#concept.agent-harness)** consists of:

- What it may know.
- What it may touch.
- The environment it runs in.

The three agent levels need very different amounts of each.
For each level, a different part applies the agent harness:

| | Main session | Task session | Worker |
| --- | --- | --- | --- |
| Context | the installed [guidance](glossary.json#concept.main-session-guidance) and whatever the developer's own configuration adds | the developer's configuration, the task-session guidance and the task's goal, Modules and decision log | only its [brief](glossary.json#concept.brief): its caller's instructions and the grant's `rw`, `ro` and `names` lists, from which it reads its [Spec context](glossary.json#concept.spec-context), [external context](glossary.json#concept.external-context), [implementation context](glossary.json#concept.implementation-context) and [task context](glossary.json#concept.task-context); its tool set is its [capability context](glossary.json#concept.capability-context) |
| Permission | none | the file tools write only the task worktree and its decision log; the shell and everything else are open, kept inside the task by its guidance, and the merge audits only some working trees outside the task worktree ([Tasks](coordination/tasks/module.md#nothing-changed-outside-the-task)) | the grant: `rw` writable, `ro` readable, `names` named only, everything else hidden; no network, no Git |
| Environment | the developer's | the developer's Claude Code configuration | its own configuration directory, a cleared environment, its own working directory and limits |
| Applied by | Distribution, which installs the guidance | Coordination's [session boundary](glossary.json#concept.session-boundary) | the worker harness's [worker settings](glossary.json#concept.worker-settings) or [permission extension](glossary.json#concept.permission-extension) |

The worker's column is the one computed from the Specs. Method computes its grant through the Spec
tooling. The worker harness applies it. The task session's harness comes from its task.
Since Concorde places no permission limits on the main agent, its agent harness is its guidance alone.

### Context and boundaries

<a id="concept.task-type"></a>

In this section a task is the Protocol's word for one worker's bounded job. It is not a Concorde
[Task](glossary.json#concept.task). A Task is the branch and worktree a task session carries to
delivery. A **[task type](glossary.json#concept.task-type)** is the kind of such a job.
It fixes access to the [boundary sets](glossary.json#concept.boundary-set) of the bound Modules.
Examples are:

- `specify` grants writes to their Specs.
- `implement` grants writes to their code.
- When the code came first, `code-to-spec` reads existing code to describe it in Specs.
- `review-architecture` reads every Module's Specs, and no code, to judge how the Modules divide
  and share the project.

The Protocol defines the complete access table.
Spec core repeats it with [its grants](spec-tooling/spec/contracts.md#grants).

<a id="concept.boundary"></a>

The **boundary** of a worker's job is the read and write limits its task type assigns to its bound
Modules. The Protocol defines the sets and the task types.
The [Harness](worker-harness/harness/module.md) explains how far Concorde enforces a worker's
boundary. A Concorde Task has no task type. Its task session has no such boundary.
The session receives the [session boundary](glossary.json#concept.session-boundary).
This keeps its writes inside its task and leaves the rest of the session open.

<a id="concept.context"></a>

The **context** of one worker is everything it may know. It always has the same five kinds.
Each kind is computed from declarations or produced for the task.
It is not chosen by hand.
For a given task, some kinds may be empty, but never all five:

- <a id="concept.spec-context"></a>The **[Spec context](glossary.json#concept.spec-context)** is
  what the Protocol calls the SpecContext of the bound Modules. It contains:
  - The documents they own.
  - The documents these relations select, one level deep:
    - `contains`.
    - `uses`.
    - `includes`.
  - The glossary entries of the terms they use.

  It is read only. A provider's Specs arrive here instead of its code.
  It holds only the project's own documents and terms, never external material.
  For a `review-architecture` worker only, it also contains the Protocol's ProjectSpecification.
  Since the architecture between Modules shows only when they are read together, this contains:
  - Every Module's documents.
  - The whole glossary.
- <a id="concept.external-context"></a>The
  **[external context](glossary.json#concept.external-context)** is what the Protocol calls the
  ExternalContext of the bound Modules. It contains the documentation and source of external
  dependencies that their `external` inclusions pin. Examples include a library's reference
  documentation or a vendored copy of its code. This material is checked out at the commit the
  project's version control records. Only the bound Modules' own inclusions count.
  A Module their relations select brings none. Every task type grants it read only, beside the
  Spec context. It explains how a dependency works. It never adds a promise the Spec does not state.
- <a id="concept.implementation-context"></a>The
  **[implementation context](glossary.json#concept.implementation-context)** starts from the
  Protocol's ImplementationContext: the names of the files the bound Modules' realizations bind.
  Only when the task type grants it does the implementation context also carry contents.
  These task types grant contents:
  - `implement`.
  - `test`.
  - `review-code`.
  - `code-to-spec`.

  The contents are the whole project's code, the Protocol's ProjectImplementation.
  So that a task reading code reads the code it uses, this also holds
  every Module's external material.
  The worker may change at most the bound Modules' ImplementationScope.
  For an `understand` worker, it carries only the names.
  For a `review-architecture` worker, it carries the names of the whole ProjectImplementation, never
  its contents.
- <a id="concept.capability-context"></a>The
  **[capability context](glossary.json#concept.capability-context)** is not a Protocol set.
  The worker's Operation and task type fix the list of tools it may use.
  It includes two kinds of contract:
  - The contracts those tools reach.
    Each contract says how the tool is called.
    It also says what the tool answers.
  - The contract of the [worker result](glossary.json#concept.worker-result) it must end with.
    This contract says what its answer must hold.

  It tells the model what it can do, never what the project promises.
- <a id="concept.task-context"></a>The **[task context](glossary.json#concept.task-context)** is
  what the Protocol calls task material. It contains:
  - The [brief](glossary.json#concept.brief) with the task and its constraints.
  - The admitted artifacts of earlier steps, such as an accepted assessment or the diff to review.
  - The explicit lists of paths by access:
    - Paths the worker may change.
    - Paths the worker may read.
    - Paths the worker may only know by name.

  It is produced for the task.
  It adds no source.
  It never replaces a Spec document or a file.

### Evidence and errors

<a id="concept.evidence"></a>

**[Evidence](glossary.json#concept.evidence)** is what a check or an independent review recorded
about specific inputs. When any of those inputs change, the evidence no longer applies.
It is never a permanent property of a Module. A Spec never stores it.
A failure is never reduced to a status.
It travels up as an [error chain](glossary.json#concept.error-chain).
The chain keeps the original failure and why each receiving level could not handle it.
Every level leaves a [trace
node](glossary.json#concept.trace-node) of what it did.

### Parts

<a id="concept.part"></a>

A **[part](glossary.json#concept.part)** is what a project installs.
It is one top-level Module of this root with its children, packaged on its own.
It names the parts it depends on.
The installer installs any set of parts with the parts they depend on.
It records which are installed. `concorde update` updates those.
Each part contributes its own:

- `concorde` commands.
- MCP tools.
- Guidance.
- `.concorde/` files.

Where a part is not installed, it contributes nothing.
These are therefore simply absent:

- Its commands.
- Its tools.
- Its guidance.

All parts come from this one repository.
They carry one version number.
Dogfooding and End-to-end testing are Modules of this repository's own development, not parts.

<a id="concept.optional-integration"></a>

A part relies only on the parts it depends on. Where its work can use more, it does so through an
**[optional integration](glossary.json#concept.optional-integration)**.
When the other part is installed, the feature works.
Otherwise, the feature is skipped with a plain statement of what is missing.
Examples are:

- Only where the issues part is installed does a task merge close the Issues the task resolved.
- Only there does a review report its findings as Issues.
  Otherwise, it keeps them in its run result.
- Only where the spec part is installed does the merge run `concorde spec-validation`.
- Without the spec part, a task's Modules and an Issue's Module are plain labels that nothing checks
  against a registry.

The Module that owns such a feature states, where it describes it, what it does in both cases.

## Overview

Four pictures give the whole framework:

- The levels every piece of work passes through.
- The life of one task across them.
- The parts that carry them.
- How the parts depend on each other.

### The levels of work

Work on a Concorde project is organized in five levels.
Every result and error travels back up them.
A piece of work uses only the levels it needs.
For example, a task session changes a file itself or runs an Operation without a workflow.
The first two levels are Coordination's, where agents decide what to work on.
The other three run in one bound workspace, where the work is done.

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
workspace: "In one bound workspace" {
  class: layer
  workflow: "3  Workflow\norders one workspace's runs\nfor a known procedure" {class: program}
  run: "4  Run\nan Operation (with workers)\nor an execution command" {class: program}
  worker: "5  Worker\nheadless AI, one job\nunder a grant" {class: agent}
  workflow -> run: "runs, one at a time"
  run -> worker: launches
}
developer -> coordination.main: "discusses, decides"
coordination.task -> workspace.workflow: "starts, in the task worktree"
coordination.task -> workspace.run: "or runs directly"
```

| Level | Who or what works there | What it does | Part |
| --- | --- | --- | --- |
| 1. Main session | the main agent, in the primary worktree | discusses the project with the developer, splits work into tasks, merges delivered tasks | coordination: [Main session](coordination/main-session/module.md) |
| 2. Task | a task session, in one task worktree | changes Specs and code directly or through runs, keeps the [decision log](glossary.json#concept.decision-log), validates and delivers | coordination: [Task sessions](coordination/task-session/module.md), [Tasks](coordination/tasks/module.md) |
| 3. Workflow | a procedure rendered as a Claude Code workflow | orders the workspace's runs for a known procedure and stops where a decision is needed | workflow: [Workflows](workflows/module.md) |
| 4. Run | the Execution runner | runs an [Operation](glossary.json#concept.operation), with workers, or an [execution command](glossary.json#concept.execution-command), without, and returns one [run result](glossary.json#concept.run-result) with evidence | execution: [Execution](execution/module.md); the concrete Operations and commands are method's: [Method](method/module.md) |
| 5. Worker | a headless `claude -p` or `pi -p` process | reasons within its grant on one bounded job and returns a [worker result](glossary.json#concept.worker-result) the run checks | worker harness: [Workers](worker-harness/workers/module.md) |

Calls go only downward. Results and errors come back up.
[Agents at both ends, programs
between](#agents-at-both-ends-programs-between) explains why the levels are split this way.

Work that only reads need not open a task.
The main agent may start an [unbound run](glossary.json#concept.unbound-run) directly in the primary
worktree. Examples are:

- An `understand`.
- A `survey`.
- A Spec review.

It has no workspace.
So that the run examines committed material rather than uncommitted changes, its steps and workers
work in a throwaway detached checkout of that worktree's `HEAD`.
It changes no Spec or code in that checkout or in the worktree it started in.
Besides its own record, its only possible lasting changes are publishing
[Issues](glossary.json#concept.issue) and the review record of a `project_review` run.
Where the issues part is installed, a review reports its findings only through the
[Issues](issues/module.md) store.
The store commits each on the primary branch as its own commit under the
[merge lock](glossary.json#concept.merge-lock).
`project_review` commits its review record the same way, alone in a commit of its own.
[Execution](execution/module.md#unbound-runs) explains it.

### The life of a task

Except for a small change the developer approved, every change of a Spec or of code is a task.
The main agent makes that small change itself in the primary worktree.
Every task takes the same path.
The main agent opens it. This creates a branch and a worktree bound as the task's
[workspace](glossary.json#concept.workspace).
It records the [task brief](glossary.json#concept.task-brief) in the
[decision log](glossary.json#concept.decision-log).
It starts a task session there.
The task session changes Specs and code, itself or through runs.
Each run returns a run result with evidence.
The task session may commit each verified step on the task branch.
Decisions that are not its own go up to the main agent together.
The main agent decides them or asks the developer.
The answers come back down.
When the work is done, the task session delivers the workspace.
Method's `delivery` validates it whole.
When the workspace is ready, `delivery` commits what is left in a
[delivery commit](glossary.json#concept.delivery-commit).
That commit alone marks the task delivered.
The main agent merges the delivered task.
When a task follows a known procedure, such as describing existing code, it runs as a
[workflow](workflows/module.md) inside the same path.
Where the method part is not installed, the task session delivers with Coordination's own
`concorde task deliver`.
This runs the checks it is given.
It makes the same kind of delivery commit without Method's validation.

```d2 illustrative
grid-columns: 3
horizontal-gap: 100
main: "Main agent\nprimary worktree" {
  grid-columns: 1
  vertical-gap: 50
  open: "1. Open a task:\nbranch, worktree,\nworkspace binding"
  brief: "2. Record the task brief,\nstart a task session"
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
workspace: "The task's workspace" {
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
session.work <-> workspace.run: "run and\nrun result"
session.work <-> main.answer: "escalations\nand answers"
session.work -> session.deliver
session.deliver -> workspace.commit
workspace.commit -> main.merge: delivered
```

These Modules explain:

- The commands behind each step.
- How tasks run in parallel.
- How a merge is checked.

The Modules are:

- [Main session](coordination/main-session/module.md).
- [Tasks](coordination/tasks/module.md).
- [Task sessions](coordination/task-session/module.md).

[Execution](execution/module.md) explains a run's steps.
[Method](method/module.md) explains the Operations' steps.

### The parts

The levels are levels of work, not of Modules. Nine parts carry them.
Each part is a child of this root:

| Part | Module | Holds |
| --- | --- | --- |
| spec | [Spec tooling](spec-tooling/module.md) | loading, checking and serving Specs: Spec core, the Spec MCP server, Views |
| kernel | [Kernel](kernel/module.md) | the contracts the other parts cooperate through: error chain, trace node, typed values, file transactions, locks, the workspace binding and the delivery commit |
| worker harness | [Worker harness](worker-harness/module.md) | launching, bounding, auditing and recording one worker under a grant it receives as data; the [worker configuration](glossary.json#concept.worker-configuration) and the [model map](glossary.json#concept.model-map) |
| execution | [Execution](execution/module.md) | runs: the runner, the run store, the Operation and execution-command frameworks, Check execution |
| workflow | [Workflows](workflows/module.md) | ordering a workspace's runs for a known procedure, decision points and the workflow result |
| issues | [Issues](issues/module.md) | the project's durable problem records |
| coordination | [Coordination](coordination/module.md) | the main session, tasks, task sessions and their merges |
| method | [Method](method/module.md) | Concorde's Spec-driven development work: the Operations, the execution commands `task-validation`, `delivery` and `scaffold`, the [brownfield workflow](glossary.json#concept.brownfield-workflow) and the standard worker sequence |
| distribution | [Distribution](distribution/module.md) | the build, the installer, `concorde update`, the `concorde` command and the project MCP server that compose the installed parts |

Each arrow below is a dependency between parts, as
[req.concorde.part-dependencies](requirements.md#req.concorde.part-dependencies) gives them.
These are the only directions in which one part may rely on another.
Every other reliance is an optional integration.
The ones that matter most are drawn dashed.
Distribution is the installation host, installed beside whatever parts a project selects.
It is left out of the diagram:

- It depends on no part.
- No part imports it.
- It reaches only the parts installed beside it, through what they register.

"Installed alone" below always means with that host.

```d2 illustrative
spec: spec
kernel: kernel
harness: worker harness
execution: execution
workflow: workflow
issues: issues
coordination: coordination
method: method
harness -> kernel
execution -> kernel
workflow -> execution
workflow -> kernel
issues -> kernel
coordination -> kernel
method -> spec
method -> harness
method -> execution
method -> workflow
method -> kernel
method -> issues: optional {style.stroke-dash: 4}
coordination -> issues: optional {style.stroke-dash: 4}
coordination -> execution: optional {style.stroke-dash: 4}
coordination -> spec: optional {style.stroke-dash: 4}
coordination -> method: optional {style.stroke-dash: 4}
```

## How it is built

### Spec first

Because the Spec is the source of truth, every other choice follows from making that safe:

- What a worker may read and write is computed from the Specs.
- A program checks a worker's answer rather than trusting it.
- A missing promise stops work instead of being inferred from code.

A step needing an unstated promise stops with a [Spec gap](glossary.json#concept.spec-gap) instead.
Outside a `specify` run and the [Adoption](method/adoption/module.md) route, only these actors
change Specs:

- The developer.
- The main agent.
- A task session within its task's goal.

Concorde's normal flow is therefore Spec first.
A promise is written, then realized.
Only a project whose code came before its Specs is described the other way round, and only through
one explicit route: the Protocol's `code-to-spec` task type.
The [Adoption](method/adoption/module.md) Operations use it together with the `scaffold` command
that writes what a survey proposed.
This route writes down the behaviour it reads as it is.
It never changes what the code does.
Besides Specs, it touches only existing tests.
It adds the `verifies` declarations that link them to the scenarios they verify
([Adoption](method/adoption/requirements.md#req.adoption.no-code-change)).
It turns every behaviour whose intent the code does not settle into an
[open question](glossary.json#concept.open-question) rather than a promise.
The main agent or the developer settles it.
Once a Module is described, work on it is Spec first again.

### Parts that install apart

A project may want only some of Concorde:

- Spec tooling to keep its architecture described and checked.
- The worker harness to bound workers some other program orchestrates.
- Task management without Concorde's own method.

Since one shared package would still install everything, layering the code alone would not give that.
A missing piece would fail at the first call that reached it.
So each part is its own package with only its real dependencies.
It contributes its own:

- Commands.
- Tools.
- Guidance.
- Files.

Every reach into a part it does not depend on becomes an optional integration that its owner states.

The dependency directions follow from what each part needs to do its job alone.
The spec part depends on nothing, not even the kernel.
The spec part keeps its own copy of the few data utilities it shares with the kernel for this reason:

- A project can check its Specs with nothing else installed.
- A project can publish its Specs with nothing else installed.
It accepts the duplication.

The kernel holds only what two parts must agree on without importing each other.
One example is the [workspace binding](glossary.json#concept.workspace-binding) one part writes
and another reads.
It includes small mechanisms that keep those contracts, such as:

- File transactions.
- Locks.
- Traces.

It holds no work of its own that a part could come to depend on by accident, such as:

- Running.
- Delegating.
- Reviewing.

The worker harness receives its grant as data.
It receives its round validation as a callback.
It therefore bounds and records a worker without reading a Spec.
Method takes the grant from the Spec tooling and hands it over.
Execution runs what definitions tell it.
It launches no worker itself.
It knows no Spec.
Coordination needs nothing but the kernel for these actions on tasks:

- Open.
- Delegate.
- Merge.
- Close.

Only where they are installed does it reach:

- Runs.
- Issues.
- Specs.
- Method's delivery.

Distribution is the installation host, present in every installation whatever parts it holds.
It installs the selected parts.
It composes the `concorde` command and the
[project MCP server](glossary.json#concept.project-mcp-server) from the
[registrations](glossary.json#concept.part-registration) of those installed.
Since it depends on none of them, a spec-only installation is the spec part and its host.

A part's dependencies are package dependencies.
They say what must be installed.
They also say what may be imported.
A Module's `uses`, the Protocol's relation, says something else: whose promises it relies on.
A `uses` into another part is one of two things.
It can be reliance on a format or convention that part defines, such as:

- The Kernel's [typed values](glossary.json#concept.typed-value) the Spec tooling implements in
  its own copy.
- The error contract Distribution prints its refusals in.
- The host promises of the always-present Distribution.

The relying part implements or meets that format itself.
It imports nothing.
It needs nothing else installed.
Or it is an [optional integration](glossary.json#concept.optional-integration).
That behaviour runs only where the other part is installed.

### Two halves, one seam

Project management and the work done in a workspace change for different reasons.
How the developer wants to work determines how tasks are:

- Opened.
- Parallelized.
- Delegated.
- Merged.

The Protocol determines how a worker is:

- Bounded by the Specs.
- Launched.
- Audited.
- Checked.

This is Concorde's core.
So they are two halves with one narrow seam.
The upper half is Coordination.
The lower half is the parts that do the work in a workspace:

- Execution.
- Workflows.
- Method.
- The worker harness Method launches its workers through.

The upper half reaches the lower one only through:

- A [workspace binding](glossary.json#concept.workspace-binding).
- The commands of the parts that work in a workspace.
- What those parts recorded.

It writes the binding into each task worktree.
It runs those commands inside that worktree.
It reads what the lower half recorded:

- Where the execution part is installed, its runs in the [run store](glossary.json#concept.run-store),
  with their [run progress files](glossary.json#concept.run-progress-file).
- Its [delivery commits](glossary.json#concept.delivery-commit) on the task branch.

Since the binding and delivery commit are kernel contracts,
both halves agree on them without importing each other.
The lower half reads the binding.
It never learns that tasks exist.
No record is written by both.
In an installation, exactly one delivering command makes the delivery commits.
Where the method part is installed, that command is Method's `delivery`.
Otherwise, it is Coordination's `task deliver`.
Whichever made it, a task's state follows from the Kernel's one rule for recognizing a delivery commit.
So whether a task is active or delivered is derived each time from:

- What happened.
- The task branch's head.
- Whether its worktree is clean.

It is never kept as a second copy that could disagree.
The parts of the lower half serve any workspace someone prepares, not only a task.

```d2 illustrative
coordination: Coordination {
  main: Main session
  task: Task sessions
  tasks: Tasks
}
kernel: Kernel {
  binding: Workspace binding
  commit: Delivery commit
}
lower: "Lower half: Execution, Workflows,\nMethod, worker harness" {
  runs: "Runs: Operations and\nexecution commands"
  store: Run store
}
coordination.tasks -> kernel.binding: writes
coordination.main -> lower.runs: "starts unbound runs\nin the primary worktree"
coordination.task -> lower.runs: starts in its worktree
lower.runs -> kernel.binding: read
lower.runs -> lower.store: record
lower.runs -> kernel.commit: "delivery makes,\nwhere Method is installed"
coordination.task -> kernel.commit: "task deliver makes,\nwhere it is not"
coordination.tasks -> lower.store: reads
coordination.tasks -> kernel.commit: reads
```

### Agents at both ends, programs between

A model is needed in two places, for opposite reasons.
At the top, someone must:

- Understand the developer.
- See the whole project.
- Judge what to do next.

Since the main agent has the global view and the developer's trust, Concorde does not restrict it.
It hands every task to a task session.
It never works inside a task worktree itself.
Of the changes of Spec meaning or code behaviour, it makes in the primary worktree only a small
change the developer approved.
At the bottom, someone must read and write code and Specs.
A worker has:

- One bounded job.
- No human to ask.
- A boundary derived from the Specs.

Keeping the two apart lets a large change be split into small, checkable steps without the developer
supervising each one.

The levels between them are programs on purpose.
What happens to a worker's answer decides what the next level sees. So it must be reproducible and
checkable rather than another model's opinion.
An Operation performs these steps:

- It computes the grant.
- It launches the worker.
- It audits the worker.
- It runs the checks.
- It turns the outcome into a result whose host evidence the task level can trust.

A workflow's procedure declares its order.
It also declares its continuation rules.
A worker's answer therefore never reaches the task level without a program's check.
The two agents of Coordination exchange their judgments directly instead.
A task session reports its decisions and escalations to the main agent.
The main agent answers them or asks the developer.
No program judges either side.
The decision log records them for the main agent and the developer to read.
Programs check what a task session changes, itself or through runs, before it counts.
Where the method part is installed, only when the workspace validates whole does `delivery` deliver
the workspace.
Without Method, Coordination's `task deliver` delivers in its place.
It certifies only the checks its caller gives it.
A merge can run checks on the primary branch once more.
Only where a model works does an Operation exist.
Deterministic steps, such as deciding readiness and delivering, are execution commands.
The same runner records them without any worker machinery.

Keeping one session inside one task worktree makes parallel tasks independent.
The main agent delegates each task to a task session whose writes are confined to that task.
It retains:

- The project-wide view.
- The conversation with the developer.
- Sole responsibility for merging.

The [error chain](#errors-as-a-chain) preserves failures across that extra session.
Where a task's commands run with the branch's own copy of the Framework, their success is
self-validation.
Concorde's own source checkout is such a case.
Because of that self-validation, its main agent merges with these checks, as that checkout's
development guidance requires:

- The build.
- `spec-validation`.

Both therefore run once more on the primary branch.
A merge runs the checks its caller gives it.
Where the spec part is installed, if the caller gives no checks, a merge runs `spec-validation`
([req.tasks.merge-default-check](coordination/tasks/requirements.md#req.tasks.merge-default-check)).
While a `concorde update` is not validated yet, it adds `spec-validation` after them
([req.tasks.merge-update-validated](coordination/tasks/requirements.md#req.tasks.merge-update-validated)).
In an installed project, a task worktree ordinarily runs the primary worktree's copy
([Distribution](distribution/module.md)).

Calls go only downward. A level may be skipped.
Whenever no workflow fits, the task level runs an Operation or a command directly.
Execution commands use no worker at all.
Nothing calls upward.
The restrictions are:

- A worker never touches Git.
- A worker never runs an Operation.
- A worker never starts an agent.
- A run never starts another run.
- A workflow never opens a task.
- A workflow never merges a task.
- A workflow never closes a task.
- Nothing below the task level reads or writes a [task record](glossary.json#concept.task-record).
- Only the main agent merges a task into the primary branch.
- A task session merges only the primary branch into its own task branch, and only when asked
  after a conflict or a `concorde update`.

A run's steps call deterministic services such as [Check execution](execution/checks/module.md)
in-process.
Between a worker's rounds, the worker harness does the same through the round validation its caller
gives it.
Such a call is not a level of its own.
It starts no run.
So that failing checks can drive a repair loop inside one Operation,
it returns to the step that made it.

### What serves every level

These serve the levels without being one:

- The kernel.
- The worker harness.
- The Spec tooling.

The [kernel](kernel/module.md) holds the contracts parts cooperate through.
Its child [Tracing](kernel/tracing/module.md) gives every level the place and shape of its trace.
Each level records its own content.
Tracing decides:

- The structure the content is kept in.
- The locks kept apart from it.
- The error chain.

While a task is current, these occupy one folder, `.concorde/tasks/<task>/`:

- Its record.
- Its decision log.
- Its traces.

Tasks places that folder.
When the task closes, Tasks moves it to the [history](glossary.json#concept.history).
`concorde trace show <task>` reads a task's whole [trace](glossary.json#concept.trace), from its
sessions down to each worker round with its cost.

The [worker harness](worker-harness/module.md) applies a worker's agent harness from its grant.
On Claude Code, it uses:

- Settings with [deny rules](glossary.json#concept.deny-rules).
- A [write hook](glossary.json#concept.write-hook).
- The Bash sandbox.

On pi, it uses a [permission extension](glossary.json#concept.permission-extension) with the same
sandbox engine.
It records the worker run.
It guards against scope drift and mistakes, not a malicious actor.
The [Harness](worker-harness/harness/module.md) explains why these layers were chosen and what they
leave out.
A task session's session boundary is Coordination's own, applied by
[Task sessions](coordination/task-session/module.md).

Every Module that reads Specs relies on the [Spec tooling](spec-tooling/module.md).
Its Spec core:

- Loads the Specs.
- Checks the Specs.
- Computes the grants.

When Spec core reports a structure untrustworthy, a Module refuses to act on it.
Spec tooling depends on no other part.
It imports no other part.
For these agent-free uses of the Specs, Spec tooling meets the Kernel's formats with its own copy:

- Checked without any agent.
- Served without any agent.
- Published without any agent.

### Errors as a chain

Every run returns a structured result.
A failure carries an [error chain](glossary.json#concept.error-chain) that climbs the levels:

- A worker reports its link to Workers.
- The Operation adds its own.
- A workflow keeps each run's chain whole in its result.
- A task session escalates to the main agent with its link on top.
- When the developer must decide, the main agent adds its link above that.

Except for these commands, every `concorde` command refuses in the same shape:

- Spec tooling's deterministic commands.
- Distribution's `build`.
- Distribution's `protocol-manifest`.

These report with Spec tooling's own error record.
[Tracing](kernel/tracing/contracts.md#reading-an-error-chain) explains how to read a chain.

Errors travel as a chain because every level handles some errors and must pass the others up:

- Except for a Spec gap, Workers resumes a worker for what its caller's round validation reports.
- A run reruns nothing.
- The main agent decides ordinary questions but not the project's direction.
  Only when the impact is major does it log and escalate the project's direction.

Every level therefore keeps the causes it received unchanged.
So that the developer receives the whole path from the failing check to their question,
it adds its own reason on top.
That reason follows the shape of the
[error contract](kernel/tracing/contracts.md#contract.tracing.error).
The chain is part of what [Tracing](kernel/tracing/module.md#the-error-chain) retains.
It stays in band. Each result carries its chain whole.

### Around the framework

Three Modules face these people rather than a project's work:

- People who install Concorde.
- People who test Concorde.
- People who develop Concorde.

The Modules are:

- Distribution installs the parts a project chooses. It installs the
  [main-session guidance](glossary.json#concept.main-session-guidance) composed from the guidance
  each installed part contributes. It also installs the workflows. It installs the docsite of
  [Views](spec-tooling/views/module.md).
- Dogfooding runs a [develop install](glossary.json#concept.develop-install).
  It reports Concorde's defects as Issues.
- End-to-end testing runs installed Concorde on real codebases.

```d2
distribution: Distribution
dogfooding: Dogfooding
e2e: End-to-end testing
main: Main session
workflows: Workflows
issues: Issues
dogfooding -> distribution
dogfooding -> main
dogfooding -> issues
e2e -> distribution
e2e -> workflows
```

## The children

The root is the composition of nine parts and the two Modules of Concorde's own development, listed
here by their role.

<a id="contains-spec-tooling"></a>

**Spec tooling**, the spec part, maintains and serves Specs through these activities:

- Loading Specs.
- Checking Specs.
- Computing [boundary sets](glossary.json#concept.boundary-set) and grants.
- Answering agents over MCP.
- Publishing Specs.

Every Module that reads Specs relies on it to refuse an untrustworthy structure.
It depends on no other part.
It imports no other part's code.
It implements the Kernel's formats it follows in its own copy, such as typed values and file
transactions.

<a id="contains-kernel"></a>

The **Kernel**, the kernel part, holds the contracts parts cooperate through without importing each
other:

- [typed values](glossary.json#concept.typed-value).
- [file transactions](glossary.json#concept.file-transaction).
- The [workspace binding](glossary.json#concept.workspace-binding) with the
  [workspace lock](glossary.json#concept.workspace-lock).
- The [merge lock](glossary.json#concept.merge-lock).
- The [delivery commit](glossary.json#concept.delivery-commit).

Through its child Tracing, it also holds:

- The uniform [trace node](glossary.json#concept.trace-node) every level records.
- The locks kept apart from the records.
- Retention.
- The `concorde trace` command.
- The [error chain](glossary.json#concept.error-chain).

It depends on no part.

<a id="contains-worker-harness"></a>

The **Worker harness**, the worker harness part, runs one headless worker under a grant it receives
as data.
The Harness derives the worker's settings or permission extension from the grant.
With the worker configuration and the model map, Workers performs these actions:

- It launches the worker.
- It audits the worker.
- It resumes the worker.
- It records the worker.

It depends on the kernel alone.
It reads no Spec.

<a id="contains-execution"></a>

**Execution**, the execution part, runs work in one bound workspace through:

- The runner that runs Operations and execution commands from the definitions the installed parts
  register.
- The [Operation catalog](glossary.json#concept.operation-catalog) assembled from those definitions.
- Check execution.

It knows no task.
It knows no Spec.
It launches no worker itself.
It records every run in its run store.

<a id="contains-workflows"></a>

**Workflows**, the workflow part, orders one workspace's runs for a known procedure.
It handles the [decision points](glossary.json#concept.decision-point) their outputs declare.
It ends with one [workflow result](glossary.json#concept.workflow-result).
Since its steps are only runs, it depends on execution and the kernel.
It knows no particular Operation.

<a id="contains-issues"></a>

**Issues**, the issues part, keeps durable, project-level [Issue](glossary.json#concept.issue)
records, each report with its tier and severity.
This lets a problem worth keeping survive the task that found it.
It also lets work start from the most severe.
Solving one is ordinary work of a task.
Where the coordination part is installed, that task's merge closes it.
Recording a report never changes the outcome of the work that found the problem
([req.issues.report-no-outcome](issues/requirements.md#req.issues.report-no-outcome)).
A failure of the Issue system itself is never recorded as an Issue.
Instead, it travels as an error chain in one of these
([req.issues.own-failures](issues/requirements.md#req.issues.own-failures)):

- The decision log.
- An escalation.
- A run result.

It depends on the kernel alone.

<a id="contains-coordination"></a>

**Coordination**, the coordination part, is the upper half: the Main session at level 1 and the
task level at level 2.
At the task level, a task session carries each task the main agent hands it, with each task's
workspace from Tasks.
It hands work to the lower half only by binding a task worktree.
It derives each task's state from what was recorded there.
It depends on the kernel alone.
These are its optional integrations:

- Runs.
- Issues.
- Specs.
- Workflows.
- Method's delivery.

<a id="contains-method"></a>

**Method**, the method part, is Concorde's Spec-driven way of working.
It includes:

- The Operations for these activities:
  - Understand.
  - Specify.
  - Implement.
  - Test.
  - Review.
- The Adoption route for existing code.
- The execution commands for these activities:
  - Validate.
  - Deliver.
  - Scaffold.
- The brownfield workflow.
- The [standard worker sequence](glossary.json#concept.standard-worker-sequence), by which a step
  takes a grant from the Spec tooling and hands it to the worker harness.

It depends on these parts:

- spec.
- worker harness.
- execution.
- workflow.
- The kernel.

It depends on issues only as an optional integration.

<a id="contains-distribution"></a>

**Distribution**, the distribution part, performs these actions:

- It builds the packages.
- It installs the parts a project chooses.
- It updates them.
- It provides these, composed from the installed parts' registrations:
  - The `concorde` command.
  - The [project MCP server](glossary.json#concept.project-mcp-server).

Every flow above starts from such an install.
In either of these cases, the installer refuses before writing anything:

- A program it needs is missing
  ([req.distribution.installer-programs-first](distribution/requirements.md#req.distribution.installer-programs-first)).
- An installed part reports that work is running
  ([req.distribution.idle-install](distribution/requirements.md#req.distribution.idle-install)).

It prints every refusal as an error link
([req.distribution.installer-error-links](distribution/requirements.md#req.distribution.installer-error-links)).
That link reaches the developer whole.

<a id="contains-dogfooding"></a>

**Dogfooding** lets the developer use Concorde on a real project while developing it:

- A develop install runs the Concorde of an independent
  [Concorde repository](glossary.json#concept.concorde-repository).
- The project's main agent watches Concorde.
- The project's main agent reports its defects as [Issue reports](glossary.json#concept.issue-report).
- The Concorde repository fixes them under its own tasks.
- The project then takes those fixes with an update.

It never changes Concorde from the project.

<a id="contains-e2e"></a>

**End-to-end testing** is how this project tests Concorde itself on real codebases from SWE-bench
with real agents. Its runs are headless or go through a deterministic driver.
It serves the developers of Concorde only.
It reaches no user's project
([req.e2e.never-installed](e2e/requirements.md#req.e2e.never-installed)). A run reports only
the [workflow result](glossary.json#concept.workflow-result) of its own workflow
([req.e2e.own-result](e2e/requirements.md#req.e2e.own-result)).
Therefore, a failure it shows is the failure of the run it started.

## Files of the root

The root also binds files that belong to no single child.
Because they keep the repository running rather than carry the framework's function, no diagram
above draws them:

- <a id="realization.concorde.project-files"></a>**Project files** are what belongs to no single
  responsibility:
  - README.
  - Agent instructions.
  - Licence.
  - Repository configuration.
  - The `.mcp.json` that gives this checkout's Claude Code sessions the
    [project MCP server](glossary.json#concept.project-mcp-server) run by the worktree's own
    `scripts/concorde.py`.
  - The CI workflow that validates this checkout.
- <a id="realization.concorde.user-documents"></a>**User documents** under `docs/` are written for
  the people who use Concorde, starting with the guide to using it.
  They follow no Spec Protocol structure.
  They are never agent context.
  The docsite publishes them as its user documents, the first tab, with `docs/README.md` as the
  site's home page.
- <a id="realization.concorde.development-environment"></a>**Development environment** consists of
  these items in this checkout:
  - The Python project and lock.
  - The pytest setup and shared test support.
  - The reference initializer.
  - The Claude Code documentation fetcher.
  - The docsite type check.
  - The part dependency check.
  - The style check of the prompts.
  - The tests of that environment.

  See [Development environment](development.md).
- <a id="realization.concorde.development-guidance"></a>**Development guidance** is the
  `concorde-development` skill's source, `prompts/development/skill.md`.
  It says how Concorde itself is developed in this checkout.
  The build renders it beside the `concorde` skill.
  The checkout's agent instructions tell every session to load it with that skill.
  See [Development environment](development.md#agent-instructions).
- <a id="realization.concorde.acceptance-tests"></a>**Acceptance tests** exercise the root's
  cross-Module [scenarios](scenarios.md) through the installer and the `concorde` command.
