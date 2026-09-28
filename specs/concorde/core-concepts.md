# Core concepts

This topic gives focused, detailed explanations of the concepts the root
[Module](glossary.json#concept.module) owns. Start with the [Concorde Framework](module.md) for
how the concepts fit together and how the Modules collaborate. The [glossary](glossary.json) is the
sole source of term definitions; the explanations here develop those meanings without defining
another vocabulary. Concepts of a Module's own interface, such as
[Operation](glossary.json#concept.operation), [Task](glossary.json#concept.task),
[Grant](glossary.json#concept.grant) or [Issue](glossary.json#concept.issue), are owned and explained
by that Module.

## The people and agents

<a id="concept.main-agent"></a>

The **developer** sets the project's direction with the
**[main agent](glossary.json#concept.main-agent)**. The main agent's project-wide view lets it
judge which responsibilities a change affects and which questions need the developer. It may also
carry out a task itself; the role is not tied to staying in the primary worktree. The
[levels of work](module.md#the-levels-of-work) place both, and
[Main session](coordination/main-session/module.md) explains the working method and decision policy.

<a id="concept.task-session"></a>

A **[task session](glossary.json#concept.task-session)** works toward a task-wide goal: it may
change Specs and code directly or use Operations, then validate and deliver. That responsibility
is broader than a worker's single bounded job. It reports to the main agent, which alone merges;
[Task sessions](coordination/task-session/module.md) explains its lifecycle.

<a id="concept.worker"></a>

A **[worker](glossary.json#concept.worker)** receives a frozen grant for one job. Its answer is a
proposal until the Operation's steps verify it; it cannot substitute its own judgement for the
checks around it. [Workers](execution/workers/module.md) explains how it is launched, audited and
recorded. Workers, plural, names the Execution code that manages workers, not the AI process
itself. The root's [design](module.md#agents-at-both-ends-programs-between) explains why model
reasoning and deterministic steps occupy different levels.

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

The **context** of one worker is everything it may know. It always has the same five kinds, each
computed from declarations or produced for the task rather than chosen by hand. Some kinds may be
empty for a given task, but never all five.

<a id="concept.spec-context"></a>

The **[Spec context](glossary.json#concept.spec-context)** is what the Protocol calls the
SpecContext of the bound Modules: the documents they own and the documents their `contains`, `uses`
and `includes` select, one level deep, and the glossary entries of the terms they use. It is read
only. A provider's Specs arrive here instead of its code. It holds only the project's own
documents and terms, never external material.

<a id="concept.external-context"></a>

The **[external context](glossary.json#concept.external-context)** is what the Protocol calls the
ExternalContext of the bound Modules: the documentation and source of external dependencies that
their `external` inclusions pin, such as a library's reference documentation or a vendored copy of
its code, checked out at the commit the project's version control records. Only the bound Modules'
own inclusions count; a Module their relations select brings none. Every task type grants it read
only, beside the Spec context. It explains how a dependency works and never adds a promise the Spec
does not state.

<a id="concept.implementation-context"></a>

The **[implementation context](glossary.json#concept.implementation-context)** starts from the
Protocol's ImplementationContext, the names of the files the bound Modules' realizations bind. Only
when the task type grants it, as for `implement`, `test`, `review-code` and `code-to-spec`, does it
also carry contents: the whole project's code, the Protocol's ProjectImplementation, which also
holds every Module's external material, so that a task reading code reads the code it uses; it may
change at most the bound Modules' ImplementationScope. An `understand` worker sees only the names.

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
each receiving level could not handle it. Read it from the top: first the account of the actor
reporting to you, then the errors it received as causes. Each level adds its own detailed link and
keeps those causes unchanged, so you can follow the account back to the failure without losing
what earlier levels observed or tried.

A link records the failure, the evidence and attempts, the specific reason that level cannot
handle it, and any options and recommendation it offers. Reasons distinguish, for example, missing
permission, a decision reserved to a higher level and used-up rounds. Worker links are claims;
the links of runs, commands and components record observations. The
[error contract](contracts.md#contract.concorde.error) gives the exact shape and fixed reasons.
The root's [error flow](module.md#errors) explains how the chain moves between levels, and
[Main session](coordination/main-session/module.md) explains how the main agent handles and
escalates it.
