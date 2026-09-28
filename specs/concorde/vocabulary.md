# Shared vocabulary

This page explains the words the whole Framework shares, which the root
[Module](glossary.json#concept.module) owns. Their one-sentence definitions, like every term of the
project, are in the [glossary](glossary.json); this page says how they fit together. Words of one
Module's own interface, such as [Operation](glossary.json#concept.operation),
[Task](glossary.json#concept.task), [Grant](glossary.json#concept.grant) or
[Issue](glossary.json#concept.issue), are owned and explained by that Module.

## The people and agents

<a id="concept.developer"></a><a id="concept.main-agent"></a>

The **developer** sets the project's direction with the
**[main agent](glossary.json#concept.main-agent)**, the developer-facing session with the
project-wide view. The main agent may also carry out a task itself; the role is not tied to staying
in the primary worktree. The [levels of work](module.md#the-levels-of-work) place both,
[Coordination](coordination/module.md) explains how tasks are worked, and
[Main session](coordination/main-session/module.md) explains the working method and decision policy.

<a id="concept.task-session"></a>

A **[task session](glossary.json#concept.task-session)** carries one delegated task for the main
agent, using the same agent program. It has a task-wide goal and reports to the main agent. Its
lifecycle is explained by [Task sessions](coordination/task-session/module.md).

<a id="concept.worker"></a>

A **worker** carries one bounded job under a frozen grant and reports to the Operation run that
launched it, whose steps the [Execution runner](glossary.json#concept.execution-runner) executes.
Its answer is a proposal until those steps verify it. [Workers](execution/workers/module.md)
explains how a worker is launched, audited and recorded. Inside a run, a worker is the only part
that reasons with a model; the run's steps and the services they call, such as
[Check execution](execution/checks/module.md), are programs. Workers, plural, names the Execution
code that manages workers, not the AI process itself.

## Specs, context and boundaries

<a id="concept.module"></a><a id="concept.spec"></a>

A **Module** is one responsibility, such as reviewing code or publishing documentation. Its
**[Spec](glossary.json#concept.spec)** is the set of documents it owns, written under the Spec
Protocol: an entry that explains the Module, optional topics, and implementation documents with
precise requirements, scenarios and contracts. A Module may span several directories, share files
with others, or have no files at all.

<a id="concept.task-type"></a>

A **[task type](glossary.json#concept.task-type)** fixes access to the
[boundary sets](glossary.json#concept.boundary-set) of the bound Modules. For example, `specify`
grants writes to their Specs and `implement` to their code; `code-to-spec` reads existing code to
describe it in Specs when the code came first. The Protocol defines the complete access table.

<a id="concept.context"></a>

The **context** of one worker is everything it may know. It always has the same four kinds, each
computed from declarations or produced for the task rather than chosen by hand. Some kinds may be
empty for a given task, but never all four.

<a id="concept.spec-context"></a>

The **[Spec context](glossary.json#concept.spec-context)** is what the Protocol calls the
SpecContext of the bound Modules, the documents they own and the documents their `contains`, `uses`
and `includes` select, one level deep, together with their ExternalContext, the pinned third-party
material they include. It is read only. A provider's Specs arrive here instead of its code.

<a id="concept.implementation-context"></a>

The **[implementation context](glossary.json#concept.implementation-context)** starts from the
Protocol's ImplementationContext, the names of the files the bound Modules' realizations bind. Only
when the task type grants it, as for `implement`, `test`, `review-code` and `code-to-spec`, does it
also carry the contents of the files in the bound Modules' ImplementationScope; an `understand`
worker sees only the names.

<a id="concept.capability-context"></a>

The **[capability context](glossary.json#concept.capability-context)** is not a Protocol set. It is
the list of tools the worker may use, fixed by its Operation and task type, and the contract of the
result it must return. It tells the model what it can do, never what the project promises.

<a id="concept.task-context"></a>

The **[task context](glossary.json#concept.task-context)** is what the Protocol calls task material:
the brief with the task and its constraints, the admitted artifacts of earlier steps, such as an
accepted assessment or the diff to review, and the explicit lists of paths the worker may change,
read or only know by name. It is produced for the task and adds no source; it never replaces a Spec
document or a file.

<a id="concept.boundary"></a>

A task's **boundary** is the read and write limits its task type assigns to its bound Modules. The
Protocol defines the sets and the task types; how far Concorde enforces the boundary of a worker is
explained by the [Harness](harness/module.md).

## Results and problems

<a id="concept.evidence"></a>

**[Evidence](glossary.json#concept.evidence)** is what a check or an independent review recorded
about specific inputs. When any of those inputs change, the evidence no longer applies; it is never
a permanent property of a Module, and a Spec never stores it.

<a id="concept.error-chain"></a>

An **[error chain](glossary.json#concept.error-chain)** preserves both the original failure and why
each receiving level could not handle it. Each level adds its own detailed link, keeping the errors
it received unchanged as causes. Worker links are claims; the links of runs, commands and components
record observations. The [error contract](contracts.md#contract.concorde.error) defines the shape
and contents, and [Main session](coordination/main-session/module.md) explains how the main agent
handles and escalates a chain.
