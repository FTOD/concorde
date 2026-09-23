# Shared vocabulary

These words are used by every part of Concorde, so they are defined once here, at the root, and
imported by the Modules that use them. Words that belong to one Module's own interface, such as
Agent, Operation, Candidate or Issue, are defined by that Module instead. Read this page first if
Concorde is new to you.

## Terminology

| Term | Definition |
| --- | --- |
| Developer | The person who uses Concorde to specify, change and understand a project. |
| User session | The developer's Pi coding-agent session with Concorde's session integration loaded, which talks with the developer, reads and edits Specs, and decides which Concorde capability to call next. |
| Task subagent | A fresh Pi agent, either the tester or the maintenance worker, to which the user session hands one complete task in one fixed worktree and which cannot delegate further. |
| Capability | One named Concorde entry, such as `concorde-plan`, that the user session calls through the Pi `concorde` tool. |
| Module | One cohesive responsibility of the software, with its own Spec; it need not be a package or directory. |
| Spec | The documents in which a Module explains what it is for, how to use it, how it is designed and what it precisely promises. |
| Context | Everything one Agent call may know: the union of its Spec context, implementation context, capability context and task context. |
| Spec context | The read-only reading that the bound Modules' declarations select: the Protocol's SpecContext of those Modules together with their ExternalContext. |
| Implementation context | The code side of a call's context: the names of the bound Modules' implementation files, and the contents of their implementation scope when the task boundary grants them. |
| Capability context | The definitions of the tools an Agent may use together with the contracts of the Operations and Host services those tools reach. |
| Task context | The material produced for one task, namely the task and its constraints, the admitted stage artifacts and workspace metadata, which adds no Spec or code source. |
| Boundary | The complete read and write limits one task receives: what it may read and what it may change. |
| Host | The trusted, non-model part of Concorde that admits requests, prepares Agent calls, checks their results and records what was accepted. |
| Worker | One fresh Pi agent that pi-subagents launches for one Agent call of a task, such as writing a plan or reviewing code. |
| Evidence | A recorded check or review result, bound to the exact inputs it examined. |

The words fall into four groups: who works (developer, user session, Task subagent), what is called
and by whom (capability, Host, worker), what is described (Module, Spec), and what a model may know
and do (context and its four kinds, boundary, evidence).

## The people and sessions

<a id="concept.concorde.developer"></a><a id="concept.concorde.user-session"></a><a id="concept.concorde.task-subagent"></a>

The **developer** works through a **user session**: an ordinary Pi coding-agent conversation in
which Concorde's session integration is loaded. The user session is where understanding and
decisions happen. It reads Specs, answers questions, edits Specs directly when the developer agrees,
and chooses which capability to call next. Concorde never decides the next step on its own, and no
capability calls the next one.

When a task is large or needs isolation, the user session can hand it to a **Task subagent**: a
fresh Pi agent with its own worktree and an explicit task. Two kinds exist. The **tester** runs
independent tests of a candidate and reports failures without repairing them. The **maintenance
worker** authors a change to Concorde's own source checkout. A Task subagent does the whole task and
reports back; it cannot delegate further. Task subagents are not Agents: they are defined,
projected and guarded by the Pi session Module, not by the Agents Module.

## Capabilities, Host and workers

<a id="concept.concorde.capability"></a><a id="concept.concorde.host"></a><a id="concept.concorde.worker"></a>

A **capability** is what the user session calls: `concorde-plan`, `concorde-implement`,
`concorde-validate` and the others listed in the [Framework entry](module.md#usage). Every call goes
through the **Host**, the deterministic part of Concorde. The Host checks the request, binds it to a
Module and a worktree, prepares any model work, and later accepts or rejects what came back.

Model work runs as **workers**. A worker is one fresh Pi agent, launched through the pi-subagents
extension for one Agent call, holding one bound context. A worker's answer is only a proposal. It
becomes a result when the Host has checked it against the current inputs. This split is the main
safety property of Concorde: nothing a model says can by itself change what counts as accepted.

## Specs, context and boundaries

<a id="concept.concorde.module"></a><a id="concept.concorde.spec"></a>

A **Module** is one responsibility, such as planning a change or publishing documentation. Its
**Spec** is the set of documents it owns, written under the Spec Protocol: an entry that explains
the Module, optional topics, and implementation documents with precise requirements, scenarios and
contracts. A Module may span several directories, share files with others, or have no files at all.

<a id="concept.concorde.context"></a>

The **context** of one Agent call is everything the call may know. It always has the same four
kinds, each computed from declarations rather than chosen by hand. Some kinds may be empty for a
given call, but never all four.

<a id="concept.concorde.spec-context"></a>

The **Spec context** is what the Protocol calls the SpecContext of the bound Modules, the documents
they own and the documents their `contains`, `uses` and `includes` select, one level deep, together
with their ExternalContext, the pinned third-party material they include. It is read only. A
provider's Specs arrive here instead of its code.

<a id="concept.concorde.implementation-context"></a>

The **implementation context** starts from the Protocol's ImplementationContext, the names of the
files the bound Modules' realizations bind. Only when the task boundary grants it, as for a
programmer or a code reviewer, does it also carry the contents of the files in the bound Modules'
ImplementationScope; a planner sees only the names.

<a id="concept.concorde.capability-context"></a>

The **capability context** is not a Protocol set. It is the definition of each tool the bound Agent
may use, taken from the Agent's definition, and the contracts of the Operations and Host services
those tools reach, such as the Issue report service or the Host's check runner. It tells the model
what it can do, never what the project promises.

<a id="concept.concorde.task-context"></a>

The **task context** is what the Protocol calls task material: the task and its constraints, the
stage artifacts admitted for this step (an accepted plan, a task list, a review result) and
metadata about the workspace. It is produced for the task and adds no source; it never replaces a
Spec document or a file.

<a id="concept.concorde.boundary"></a>

A task's **boundary** adds what it may change: typically the bound Modules' own documents or their
implementation files, depending on the task. The Protocol defines the sets a boundary is composed
from; which sets a task receives, and how far Concorde enforces them, is explained by the
[Harness](harness/module.md).

<a id="concept.concorde.evidence"></a>

**Evidence** is what a check or an independent review recorded about specific inputs. When any of
those inputs change, the evidence no longer applies; it is never a permanent property of a Module,
and a Spec never stores it.
