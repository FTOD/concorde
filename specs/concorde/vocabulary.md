# Shared vocabulary

These shared terms are defined once by the root Module and imported by the Modules that use them.
Use this page as a reference when a term needs clarification. Words of one Module's own interface,
such as Operation, Task, Grant or Issue, are defined by that Module.

## Terminology

| Term | Definition |
| --- | --- |
| Developer | The person who uses Concorde to specify, change and understand a project. |
| Main agent | The developer-facing Claude Code or pi session in the primary worktree that discusses the project, splits work into tasks, carries them out or hands them to task sessions, and merges their results. |
| Task session | A session of the main agent's own program to which the main agent delegates the work of one task when it runs several at once, working only inside that task's worktree until delivery and reporting to the main agent. |
| Worker | One headless Claude Code or pi process that performs one bounded task of one task type under a frozen grant and reports only to the Operation host that launched it. |
| Module | One cohesive responsibility of the software, with its own Spec; it need not be a package or directory. |
| Spec | The documents in which a Module explains what it is for, how to use it, how it is designed and what it precisely promises. |
| Task type | One of the seven Protocol task types (understand, specify, implement, test, review-spec, review-code, code-to-spec) that fixes the access level of every boundary set a task receives. |
| Context | Everything one worker may know: the union of its Spec context, implementation context, capability context and task context. |
| Spec context | The read-only documents the bound Modules' declarations select: the Protocol's SpecContext of those Modules together with their ExternalContext. |
| Implementation context | The code side of a worker's context: the names of the bound Modules' implementation files, and the contents of those files when the task type grants them. |
| Capability context | The tools a worker may use and the contracts those tools reach, which tell it what it can do and never what the project promises. |
| Task context | The material produced for one task, namely its brief, constraints and admitted artifacts, which adds no Spec or code source. |
| Boundary | The read and write limits one task receives, fixed by its task type and its bound Modules. |
| Evidence | A recorded check or review result, bound to the exact inputs it examined. |
| Error chain | The structured report of an error that travels up: one link per level that could not handle it, each with its detailed account and its reason for not handling it, and the errors it received from below nested as its causes. |

The words fall into four groups: who works (developer, main agent, task session, worker), what is described
(Module, Spec), what a worker may know and do (task type, context and its four kinds, boundary),
and how results and problems travel (evidence, error chain).

## The people and agents

<a id="concept.concorde.developer"></a><a id="concept.concorde.main-agent"></a>

The **developer** sets the project's direction with the **main agent**, the developer-facing
session with the project-wide view. The main agent may also carry out a task itself; the role is
not tied to staying in the primary worktree. [Agents](agents/module.md) explains the levels of work,
and [Main session](agents/main-session/module.md) explains the working method and decision policy.

<a id="concept.concorde.task-session"></a>

A **task session** carries one delegated task for the main agent, using the same agent program.
It has a task-wide goal and reports to the main agent. Its lifecycle is explained by
[Task sessions](agents/task-session/module.md).

<a id="concept.concorde.worker"></a>

A **worker** carries one bounded job under a frozen grant and reports to its Operation host.
Its answer is a proposal until the host verifies it. [Workers](agents/workers/module.md) explains
how a run is launched, audited and recorded.

## Specs, context and boundaries

<a id="concept.concorde.module"></a><a id="concept.concorde.spec"></a>

A **Module** is one responsibility, such as reviewing code or publishing documentation. Its
**Spec** is the set of documents it owns, written under the Spec Protocol: an entry that explains
the Module, optional topics, and implementation documents with precise requirements, scenarios and
contracts. A Module may span several directories, share files with others, or have no files at
all.

<a id="concept.concorde.task-type"></a>

A **task type** fixes access to the boundary sets of the bound Modules. For example, `specify`
grants writes to their Specs and `implement` to their code; `code-to-spec` reads existing code to
describe it in Specs when the code came first. The Protocol defines the complete access table.

<a id="concept.concorde.context"></a>

The **context** of one worker is everything it may know. It always has the same four kinds, each
computed from declarations or produced for the task rather than chosen by hand. Some kinds may be
empty for a given task, but never all four.

<a id="concept.concorde.spec-context"></a>

The **Spec context** is what the Protocol calls the SpecContext of the bound Modules, the
documents they own and the documents their `contains`, `uses` and `includes` select, one level
deep, together with their ExternalContext, the pinned third-party material they include. It is
read only. A provider's Specs arrive here instead of its code.

<a id="concept.concorde.implementation-context"></a>

The **implementation context** starts from the Protocol's ImplementationContext, the names of the
files the bound Modules' realizations bind. Only when the task type grants it, as for
`implement`, `test`, `review-code` and `code-to-spec`, does it also carry the contents of the files in the bound
Modules' ImplementationScope; an `understand` worker sees only the names.

<a id="concept.concorde.capability-context"></a>

The **capability context** is not a Protocol set. It is the list of tools the worker may use, fixed
by its Operation and task type, and the contract of the result it must return. It tells the model
what it can do, never what the project promises.

<a id="concept.concorde.task-context"></a>

The **task context** is what the Protocol calls task material: the brief with the task and its
constraints, the admitted artifacts of earlier steps, such as an accepted assessment or the diff to
review, and the explicit lists of paths the worker may change, read or only know by name. It is
produced for the task and adds no source; it never replaces a Spec document or a file.

<a id="concept.concorde.boundary"></a>

A task's **boundary** is the read and write limits its task type assigns to its bound Modules. The
Protocol defines the sets and the task types; how far Concorde enforces the boundary of a worker is
explained by the [Harness](harness/module.md).

## Results and problems

<a id="concept.concorde.evidence"></a>

**Evidence** is what a check or an independent review recorded about specific inputs. When any of
those inputs change, the evidence no longer applies; it is never a permanent property of a Module,
and a Spec never stores it.

<a id="concept.concorde.error-chain"></a>

An **error chain** preserves both the original failure and why each receiving level could not
handle it. Each level adds its own detailed link, keeping the errors it received unchanged as
causes. Worker links are claims; host links record observations. The
[error contract](contracts.md#contract.concorde.error) defines the shape and contents, and
[Main session](agents/main-session/module.md) explains how the main agent handles and escalates a
chain.
