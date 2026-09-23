# Shared vocabulary

These words are used by every part of Concorde, so they are defined once here, at the root, and
imported by the Modules that use them. Words that belong to one Module's own interface, such as
Operation, Task, Grant or Issue, are defined by that Module instead. Read this page first if
Concorde is new to you.

## Terminology

| Term | Definition |
| --- | --- |
| Developer | The person who uses Concorde to specify, change and understand a project. |
| Main agent | The developer-facing Claude Code session in the primary worktree that discusses the project, splits work into tasks, runs Operations and merges their results. |
| Worker | One headless Claude Code process that performs one bounded task of one task type under a frozen grant and reports only to the Operation host that launched it. |
| Module | One cohesive responsibility of the software, with its own Spec; it need not be a package or directory. |
| Spec | The documents in which a Module explains what it is for, how to use it, how it is designed and what it precisely promises. |
| Task type | One of the six Protocol task types (understand, specify, implement, test, review-spec, review-code) that fixes the access level of every boundary set a task receives. |
| Context | Everything one worker may know: the union of its Spec context, implementation context, capability context and task context. |
| Spec context | The read-only documents the bound Modules' declarations select: the Protocol's SpecContext of those Modules together with their ExternalContext. |
| Implementation context | The code side of a worker's context: the names of the bound Modules' implementation files, and the contents of those files when the task type grants them. |
| Capability context | The tools a worker may use and the contracts those tools reach, which tell it what it can do and never what the project promises. |
| Task context | The material produced for one task, namely its brief, constraints and admitted artifacts, which adds no Spec or code source. |
| Boundary | The read and write limits one task receives, fixed by its task type and its bound Modules. |
| Evidence | A recorded check or review result, bound to the exact inputs it examined. |
| Escalation | A structured report of a problem one tier cannot resolve, with its evidence and options, passed to the tier above. |

The words fall into four groups: who works (developer, main agent, worker), what is described
(Module, Spec), what a worker may know and do (task type, context and its four kinds, boundary),
and how results and problems travel (evidence, escalation).

## The people and agents

<a id="concept.concorde.developer"></a><a id="concept.concorde.main-agent"></a>

The **developer** works with a **main agent**: an ordinary Claude Code session opened in the
project's primary worktree. The main agent is where understanding and decisions happen. It
discusses the state of the project with the developer, answers questions, and sets the direction
of larger changes. It splits work into tasks, each a branch with its own worktree, decides which
tasks run in parallel, and runs Operations inside those worktrees. Concorde adds no permission
limits to the main agent, but the main agent normally does not edit the project itself.

The main agent decides ordinary design uncertainties on its own, records them, and reports them at
the end. It asks the developer only when a decision has a major impact.

<a id="concept.concorde.worker"></a>

A **worker** is one headless Claude Code process that an Operation host launches for one bounded
task, such as assessing a Module, changing its Spec or changing its code. It works under a frozen
grant computed from the Specs of the task's worktree, needs no human input, and reports only to the
host that launched it. It never touches Git, never runs Operations and never starts other agents.
A worker's answer is a proposal: the host audits what it changed and runs the checks itself before
anything counts.

## Specs, context and boundaries

<a id="concept.concorde.module"></a><a id="concept.concorde.spec"></a>

A **Module** is one responsibility, such as reviewing code or publishing documentation. Its
**Spec** is the set of documents it owns, written under the Spec Protocol: an entry that explains
the Module, optional topics, and implementation documents with precise requirements, scenarios and
contracts. A Module may span several directories, share files with others, or have no files at
all.

<a id="concept.concorde.task-type"></a>

Every task has a **task type**. The Spec Protocol defines six of them and, for each, the access
level of every boundary set of the bound Modules: `understand` reads Specs and only the names of
code files, `specify` may change the bound Modules' own documents, `implement` may change their
code, `test` and `review-code` read their code, and `review-spec` reads their Specs.

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
`implement`, `test` and `review-code`, does it also carry the contents of the files in the bound
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

<a id="concept.concorde.escalation"></a>

An **escalation** is how a problem travels up. A worker that cannot finish returns a structured
result that names the problem, what it tried, its evidence, the options it sees and its
recommendation. The Operation host adds the evidence it produced itself, such as audit findings and
check output, and never turns a worker's claim into a fact. The main agent decides what it can,
records the decision in the task's decision log, and escalates to the developer only when the
impact is major.
