# Boundaries

This chapter serves the Protocol's second purpose: letting a harness give each task a clear
boundary of what it may read and write. The specification determines this boundary rather than
leaving it to guesswork. [Context](context.md) defines the read sets in detail. This chapter defines:

- the write sets
- the impact of a write
- how a harness composes sets into the boundary of one task

The Protocol defines the **sets** and the **task types**. A task type fixes which sets a task
receives and at which access level. Thus, two harnesses give the same task the same boundary.
Which task type a harness assigns to a piece of work remains the harness's decision.
How it enforces the resulting boundary remains the harness's decision.
A specification never grants a task anything by itself.

## Boundary sets of a Module

Every set is computed from declarations alone. Thus, two tools computing the same set from the
same checkout get the same answer.

| Set | Definition | Derived from |
| --- | --- | --- |
| `SpecContext(M)` | both members of every document M owns or selects, and the glossary entries of `Terms(M)` | `owns`, `contains`, `uses`, `includes`; term selection |
| `ExternalContext(M)` | pinned material M includes | `includes` of kind `external` |
| `ImplementationContext(M)` | the names of every file M's realizations bind | `binds` |
| `SpecScope(M)` | both members of every document M owns, including the entry and its `module` block, and the glossary entries M owns | `owns`, glossary `owner` |
| `ImplementationScope(M)` | every file covered by M's realization entries | `binds` |
| `ProjectImplementation` | every file any Module's realizations bind and all external material any Module includes; the same for every Module | `binds`, `includes` of kind `external` |
| `ProjectSpecification` | both members of every document any Module owns, and the whole glossary; the same for every Module | `owns`, the glossary |

`SpecContext`, `ExternalContext`, `ImplementationContext`, `ProjectImplementation` and
`ProjectSpecification` are **read** sets. `SpecScope` and `ImplementationScope` are **write** sets.
They are deliberately different. Because M `uses` a provider, M may read the provider's documents.
Those documents stay in the provider's `SpecScope`, never in M's. Reading never widens what may be
written.

Every declaration a Module makes lies in its own documents or in its own glossary entries. The
documents make `SpecScope(M)` a plain set of files that a harness can enforce with file
permissions. The glossary entries are the one part it enforces by entry, as
[The glossary](#the-glossary) describes.

## What no Module may write

The following are outside every Module's write sets:

- another Module's documents
- another Module's glossary entries, including their `owner`
- the project registry
- external material
- generated outputs and project-control records, which are owned by the tools that produce them
- files bound by no Module
- the installed Protocol copy
- installed files: files an installer placed in the project and lists as its own in
  `.concorde/install.json`, the installation record. These never include a project file it only
  amends.

An installed file may be bound only by its exact path, so that every version-controlled file has
an owner. A directory entry covering an installed file is refused. However the Module binding it
is granted, a task's grant gives the file at most read access. The installer replaces these files
on every update. These files configure the agents working on the project. For these reasons, a
Module-scoped task never changes them.

A file bound by no Module is therefore not writable by any Module-scoped task. To change such a
file, first bind it: add it to a realization as an entry. A realization binds only paths that
exist. Before a task that fills a new file outside every bound directory starts, the work that
prepares that task creates and binds the file together. A Module-scoped task does not do this
preparation. The file, with the least content its format needs to be valid, and the entry that
binds it are one change. A task bound to the Module may then write the file within
`ImplementationScope(M)`. A file created below a bound directory needs no new entry.

## The glossary

The glossary is one file holding every Module's concepts. Thus, file permissions alone cannot keep
a task inside its own entries. A task whose type writes `SpecScope` MAY therefore be given the
whole glossary file to change. The harness MUST then compare the file before and after the task.
Every added, changed or removed entry MUST be owned, before and after the change, by a Module the
task is bound to.

Any other difference is a write outside the boundary. This includes an entry moved to another
owner by a task bound only to one of them. Moving a concept between owners is a change of both
Modules. It needs a task bound to both.

Reading follows term selection, not the file: a task reads the entries its bound Modules' contexts
select. A harness that makes the file readable for a writing task also shows other Modules'
entries. Because the task cannot change them, that over-inclusion is accepted.

## The project registry

The registry is the project-wide index of Modules and a checked mirror of their `module` blocks.
A coordinating session reads it to:

- plan work
- compute the sets of every Module involved
- assign each task its boundary

A Module-scoped task needs neither to read nor to write it. Its own relations are in its entry.
The harness resolves identities for it.

Because the registry is outside every Module's write sets, a Module-scoped task that changes its
own `module` block leaves the mirror stale. `CHK.registry.mirror` reports that. A project-level
step reconciles it. That step MAY regenerate the mirrored fields. Adding or removing a Module
changes which Modules exist. This is always such a project-level step. The step writes the
registry and the parent's `contains` together with whatever else the change of composition needs.
Examples include the new Modules' first documents and the parent's realization entries that move
to them.

## Impact of a write

A write can break promises that other Modules rely on. The derived **impact** of a write lists
them, so that a harness can take any of these actions:

- widen the task's read boundary
- schedule review
- reject the write

| Written | Concerns |
| --- | --- |
| a document D | every Module whose `SpecContext` contains D |
| a requirement or scenario | every Module whose `relies_on` lists it |
| a concept's glossary entry | every Module whose `Terms` contains the concept |
| a contract | every Module that participates in it |
| a file F | every Module whose `ImplementationScope` contains F, and every Module that uses one of them, directly or through further `uses` |

Two rules follow from the model:

- **Shared files.** When several Modules bind a file, a task that writes it MUST be bound to every
  binding Module. The file carries the promises of all of them. A writer bound to only one could
  break a promise it cannot see. Binding the task to every binder keeps its reads within the
  `SpecContext` of the Modules it is bound to (rule 3 below). Sharing grants no extra read.
  A task that only reads the file needs no such widening.
- **Atomic reconciliation.** Some changes are valid only if other Modules change with them.
  A contract version increment requires every participant's `participates` version to move.
  Retiring a concept requires the documents that mention it to follow. Such a change is a
  multi-Module change. Its write boundary is the union of the write sets of every Module it edits.
  A single-Module task MUST NOT be given another Module's scope to complete it.

## Composing a task boundary

A task is bound to one or more Modules. Its boundary assigns each boundary set of those Modules one
access level:

| Level | Meaning |
| --- | --- |
| `none` | not visible |
| `names` | paths are visible, contents are not |
| `read` | contents are visible and immutable |
| `write` | contents may be changed, files created or removed within the set |

A harness MUST keep every boundary within these limits:

1. **Write only within write sets.** Everything writable belongs to `SpecScope` or
   `ImplementationScope` of a Module the task is bound to.
2. **Write implies read.** Anything writable is also readable.
3. **Read only within read sets.** Contents come from these sets:
   - Specification contents come from the bound Modules' `SpecContext` or, for the task type that
     assigns it, from `ProjectSpecification`.
   - Implementation contents come from their `ImplementationScope` or, for the task types that
     assign it, from `ProjectImplementation`.
   - External material comes from their `ExternalContext` or `ProjectImplementation`.

   A provider's code may be read and run, never changed. The code never replaces the provider's
   Specs as the statement of what the provider promises.
4. **Task material adds no source.** A harness MAY supply material produced for the task, such as:
   - a plan
   - a brief
   - a diff since a baseline

   This material is not a Protocol source. It widens no set.

## Task types

Every task has exactly one task type. The type assigns each boundary set of the bound Modules one
access level:

| Task type | `SpecContext` | `ImplementationContext` | `ImplementationScope` | `SpecScope` | `ExternalContext` | `ProjectImplementation` | `ProjectSpecification` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `understand` | read | names | none | none | read | none | none |
| `specify` | read | names | none | write | read | none | none |
| `implement` | read | names | write | none | read | read | none |
| `test` | read | names | read | none | read | read | none |
| `review-spec` | read | names | none | none | read | none | none |
| `review-code` | read | names | read | none | read | read | none |
| `code-to-spec` | read | names | read | write | read | read | none |
| `review-architecture` | read | names | none | none | read | names | read |

The task types that read code, `implement`, `test`, `review-code` and `code-to-spec`, read the
whole `ProjectImplementation`. Code is read and run together with the code it uses and the code
that uses it. A package can only be imported whole. What they may change stays within the bound
Modules' scopes. Thus, a Module's `uses` limits what a task changes, not what it reads. The task
types that work on Specs alone never see code contents.

- **`understand`** learns what a Module promises and how it is realized, without reading code.
  Its uses include:
  - explaining a change
  - assessing a change
  - planning a change

  Planning is one use of understanding, not a task type of its own.
- **`specify`** changes the Module's own documents, including their realization entries for files
  that exist.
- **`implement`** changes the Module's realization: its bound files, and new files below its bound
  directories.
- **`test`** reads the realization and its tests against the Specs. Running checks is evidence
  produced for the task, not a wider read.
- **`review-spec`** judges the Module's documents. **`review-code`** judges its realization against
  its Specs. A diff since a baseline is task material (rule 4).
- **`code-to-spec`** describes an existing realization in the Module's own documents. It exists for
  the uncommon project whose code came before its specification. A project that is specified first
  never needs it. It is the only task type that reads code in order to write Specs. It never
  changes code. It records the behaviour it read as it is. When the code does not settle a
  behaviour's intent, that behaviour MUST NOT be written as a promise. Instead, the documents state
  it as an honest unknown, and the task reports it as an open question for a human to decide. Examples
  of such behaviour include a probable defect or an unexplained special case.
- **`review-architecture`** judges the architecture between Modules against
  [Architecture quality](evaluation.md#architecture-quality). That architecture is how the project
  is divided into Modules and how they depend on each other. The task writes nothing. The task is
  bound to the Modules whose place in the architecture it is asked about. The task judges them
  first. Since its reads do not depend on its bound Modules, a task that judges the whole project
  may be bound to the root Module alone.

`review-architecture` is the only task type that reads `ProjectSpecification`. Every other task
type reads the Specs its bound Modules' declarations select. This keeps a Module's context small
and self-sufficient. Architecture is a property between Modules, including Modules that declare no
relation to each other. Only when every Module's Specs are read together is an overlap of
responsibilities or a promise two Modules state differently visible.

The task sees the names of the whole project's files. Those names show where each Module's
realization lies. The task sees no code contents. Architecture is judged from what the Modules
promise and how they rely on each other, not from how their code happens to work.
A [context identity](context.md#context-identity) of such a task covers every member of
`ProjectSpecification`. Thus, a change to any Module's Specs changes what the task judged.

A `none` in the `SpecScope` column does not hide the Module's own documents. They are in
`SpecContext`, which every type reads. `ProjectSpecification` holds every Module's documents and
the whole glossary. It therefore contains every `SpecContext`. Each row stays inside rules 1 to 4.
Every level can be computed exactly from declarations. A harness MUST NOT give a task a level its
type does not assign. A harness MAY give less, for example by withholding external material a task
does not need.

A scenario-scoped task is bound to the scenario's owner. A task bound to several Modules receives,
for each bound Module, that Module's sets at the levels its type assigns. When a path falls into
several sets, it receives the highest level any of them assigns. The levels are ordered `none`,
`names`, `read`, `write`.
