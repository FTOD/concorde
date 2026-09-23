# Task context in detail

This topic extends the [Task context](module.md) entry with the reasoning a maintainer of Task
context needs. Consumers do not need it: the entry states every promise they rely on, and the
precise obligations and records are in [requirements](requirements.md), [scenarios](scenarios.md)
and [records](records.md).

## How one call's context is composed

| Kind | What Task context puts into the call | How the Agent receives it |
| --- | --- | --- |
| Spec context | every document of the bound Modules' `SpecContext`, with owners, digests and the declarations that selected them; the Protocol files; one digest per `ExternalContext` inclusion | copies in the capsule; external material only when the Agent definition reads references |
| Implementation context | the realization entries and bound file names of the selected Module, in every phase; the path and digest of every `ImplementationScope` file only when the Agent definition reads implementation | names in the snapshot; for a code reviewer copies in the capsule; for the programmer the worktree and its intended write paths |
| Capability context | the Agent binding, which fixes the Agent's tool list and effects | Agent execution launches the Agent with exactly those tools and the contracts of the Host services they reach |
| Task context | the task, focus and constraints, the admitted stage inputs and the workspace facts | inline in the snapshot, which the capsule holds as `context.json` |

For example, when `concorde-code-review` reviews `module.checkout`, the code reviewer's definition
names the phase `code-review` and reads Spec context and implementation, so the snapshot holds the
Module's `SpecContext`, the Protocol files, the implementation file names and their paths and
digests, one digest per external inclusion, the Agent binding, the task and the workspace facts. A
planner for the same Module gets the same Spec side but only the names of the implementation files.
A scenario focus changes the question, not the context: it selects the whole context of the
scenario's owning Module.

## Workspace kinds

A `capsule` Agent (the context assessor, planner, task author, spec reviewer and Issue solver) works
only from its capsule: the capsule is its working directory and holds every file it is given. A
`project` Agent (the programmer and the code reviewer) also starts in its capsule, but its step
concerns the project worktree: the code reviewer receives copies of the implementation files and
runs configured checks against the worktree, and the programmer's `context.json` names the worktree
and the files it is intended to write there, which it edits in place.

## Freezing and rechecking

Spec tooling computes the boundary sets from declarations alone; Task context records its answer
with byte digests so that a later recheck can prove nothing moved. The recheck recomputes, from the
current checkout, the snapshot's identity digest, the current worktree's workspace facts other than
the list of other worktrees, the Protocol binding, the Spec context record of every bound Module,
the selected Module's realization entries, its bound file names, the implementation file bytes the
snapshot holds, the external reference digests and the Agent binding. For an Agent that writes
implementation, bound file names and implementation bytes are exempt, because changing them is the
purpose of the call; everything else is rechecked. Agent execution also has Task context verify that
every capsule file still has the digest it was written with.

## Names are not contents

Every phase sees the names of the Module's implementation files, because a planner must be able to
say where code goes. Only an Agent whose definition reads implementation receives paths and
digests, and no snapshot embeds code. The same rule applies again when an Agent's typed input is
admitted.

## Shared files

The Protocol resolves a shared file by binding the writing task to every binding Module. Task
context does exactly that for an Agent that writes implementation: each additional Module
contributes its own `SpecContext`, selected by its own declarations, and no special selection is
added, so what the programmer reads is always explained by the declarations of the Modules it is
bound to. The intended write paths stay the selected Module's `ImplementationScope`.

## Copies instead of grants, and what is not enforced

An Agent runs as a native Pi process with the developer's file access. Rather than pretend to
restrict that, Task context makes the intended context easy to use and checkable: the capsule holds
exactly the delivered files, and their digests are verified before acceptance.

| Boundary set | In the snapshot | Reaches the Agent as | Enforced |
| --- | --- | --- | --- |
| `SpecContext` | every selected document of every bound Module | copies in the capsule | Not enforced: the Agent's file tools can name other paths; the recheck refuses changed bytes. |
| `ExternalContext` | one tree digest per inclusion | copies, only for definitions that read references | Not enforced; changes are detected by the recheck. |
| `ImplementationContext` | entries and bound file names | names in `context.json` | Names only in delivery; the Agent can still open the files. |
| `ImplementationScope` | paths and digests, only for definitions that read implementation | copies for the code reviewer; the worktree for the programmer | Not enforced: the programmer's edits and shell are limited by its instructions only. |
| `SpecScope` | not recorded | never delivered as writable | Not enforced: an Agent with `edit`, `write` or `bash` could change a Spec file on disk. |

What holds is the Agent's tool list, fixed by its binding and checked by Agent execution's
preflight, and the independent acceptance of its result after the recheck.

## Bindings, revision identities and reference versions

The Agents Module says what each Agent is; Task context turns a definition into a binding for one
call and refuses one that is inconsistent or not built, because the binding is what the snapshot,
the capsule and the recheck must agree on. The effect roles a definition may declare are
`spec-context`, `implementation` and `references`.

Revision identities give Planning, Review, Validation, Implementation and Issue solving one shared
meaning of "changed": one digest over a Module's registry record, Protocol binding and resolved
`SpecContext`, and one over its realization entries and the bytes of every bound file.

The reference version check is a configured check rather than part of freezing, because it compares
the installed LangGraph with the pinned reference checkout, which is not a Spec input.

## Open questions

A snapshot lists a fixed pair of Protocol files; which chapters of the installed Protocol bundle an
Agent should receive is not decided.
