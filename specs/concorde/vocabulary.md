# Shared vocabulary

These words are used by every part of Concorde, so they are defined once here, at the root, and
imported by the Modules that use them. Words that belong to one Module's own interface, such as
Agent, Operation, Candidate or Issue, are defined by that Module instead.

## Terminology

| Term | Definition |
| --- | --- |
| Developer | The person who uses Concorde to specify, change and understand a project. |
| User session | The developer's Pi coding-agent session, which talks with the developer, reads and edits Specs, and decides which Concorde capability to call next. |
| Task subagent | A fresh Pi agent that the user session delegates one complete task to, in one fixed worktree, without further delegation. |
| Capability | One public Concorde entry, such as `concorde-plan`, that the user session invokes through the Pi `concorde` tool. |
| Module | One cohesive responsibility of the software, with its own Spec; it need not be a package or directory. |
| Spec | The documents in which a Module explains what it is for, how to use it, how it is designed and what it precisely promises. |
| Context | What a task bound to a Module may read, as computed from that Module's declarations in the Specs. |
| Boundary | The complete read and write limits a task receives: what it may read and what it may change. |
| Host | The trusted, non-model Concorde program that admits requests, prepares workers, checks their results and records what was accepted. |
| Worker | One fresh, bounded model execution for one step of a task, such as writing a plan or reviewing code. |
| Evidence | A recorded check or review result, bound to the exact inputs it examined. |

## The people and sessions

<a id="concept.concorde.developer"></a><a id="concept.concorde.user-session"></a><a id="concept.concorde.task-subagent"></a>

The **developer** works through a **user session**: an ordinary Pi coding-agent conversation with
Concorde's session extension loaded. The user session is where understanding and decisions happen.
It reads Specs, answers questions, edits Specs directly when the developer agrees, and chooses which
capability to call. Concorde never decides the next step on its own.

When a task is large or needs isolation, the user session can hand it to a **Task subagent**: a
fresh Pi agent with its own worktree and an explicit task. A Task subagent does the whole task and
reports back; it cannot delegate further. Source maintenance of Concorde itself and independent
testing are the two kinds in use today.

## Capabilities, Host and workers

<a id="concept.concorde.capability"></a><a id="concept.concorde.host"></a><a id="concept.concorde.worker"></a>

A **capability** is what the user session calls: `concorde-plan`, `concorde-implement`,
`concorde-validate` and the others listed in the [Framework entry](module.md#usage). Every call goes
through the **Host**, the deterministic part of Concorde. The Host checks the request, binds it to a
Module and a worktree, prepares any model work, and later accepts or rejects what came back.

Model work runs as **workers**: fresh Pi agents, each doing one step with one Module's context.
A worker's answer is only a proposal. It becomes a result when the Host has checked it against the
current inputs. This split is the main safety property of Concorde: nothing a model says can by
itself change what counts as accepted.

## Specs, context and boundaries

<a id="concept.concorde.module"></a><a id="concept.concorde.spec"></a>

A **Module** is one responsibility, such as planning a change or publishing documentation. Its
**Spec** is the set of documents it owns, written under the Spec Protocol:
an entry that explains the Module, optional topics, and implementation documents with precise
requirements, scenarios and contracts. A Module may span several directories, share files with
others, or have no files at all.

<a id="concept.concorde.context"></a><a id="concept.concorde.boundary"></a>

Everything a worker may know comes from its Module's Spec. The Module's **context** is computed from
its declarations: its own documents, the Specs of the Modules it uses or contains, what it explicitly
includes, and the names of the files that realize it. A task's **boundary** adds what it may change:
typically the Module's own documents or its implementation files, depending on the task. The rules
for these sets belong to the Spec Protocol; how far Concorde enforces them today is explained by
the [Harness](harness/module.md).

<a id="concept.concorde.evidence"></a>

**Evidence** is what a check or an independent review recorded about specific inputs. When any of
those inputs change, the evidence no longer applies; it is never a permanent property of a Module.
