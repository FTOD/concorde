# Boundaries

This chapter serves the Protocol's second purpose: letting a harness give each task a clear
boundary of what it may read and what it may write, derived from the specification rather than
guessed. [Context](context.md) defines the read sets in detail; this chapter defines the write sets,
the impact of a write, and how a harness composes sets into the boundary of one task.

The Protocol defines the **sets** and the **task types**. A task type fixes which sets a task
receives and at which access level, so two harnesses give the same task the same boundary. Which
task type a harness assigns to a piece of work, and how it enforces the resulting boundary, remain
the harness's decisions. A specification never grants a task anything by itself.

## Boundary sets of a Module

Every set is computed from declarations alone, so two tools computing the same set from the same
checkout get the same answer.

| Set | Definition | Derived from |
| --- | --- | --- |
| `SpecContext(M)` | both members of every document M owns or selects | `owns`, `contains`, `uses`, `includes` |
| `ExternalContext(M)` | pinned material M includes | `includes` of kind `external` |
| `ImplementationContext(M)` | the names of every file M's realizations bind | `binds` |
| `SpecScope(M)` | both members of every document M owns, including the entry and its `module` block | `owns` |
| `ImplementationScope(M)` | every file covered by M's realization entries, including pending entries not yet created | `binds` |
| `ProjectImplementation` | every file any Module's realizations bind and all external material any Module includes; the same for every Module | `binds`, `includes` of kind `external` |

`SpecContext`, `ExternalContext`, `ImplementationContext` and `ProjectImplementation` are **read**
sets, `SpecScope` and `ImplementationScope` are **write** sets. They are deliberately different:
M may read a provider's documents because it `uses` the provider, but those documents stay in the
provider's `SpecScope`, never in M's. Reading never widens what may be written.

Every declaration a Module makes, including its Module-level relations, lies in its own documents,
so `SpecScope(M)` is a plain set of files and a harness can enforce it with file permissions.

## What no Module may write

The following are outside every Module's write sets:

- another Module's documents;
- the project registry;
- external material;
- generated outputs and project-control records, which are owned by the tools that produce them;
- files bound by no Module;
- the installed Protocol copy;
- installed files: the files an installer placed in the project and lists as its own in the
  installation record `.concorde/install.json`, never a project file it only amends.

An installed file may be bound, so that every version-controlled file has an owner, but only by its
exact path: a directory entry covering one is refused, and a task's grant gives the file at most
read access, however the Module binding it is granted. The installer replaces these files on every
update and the agents working on the project are configured by them, so a Module-scoped task never
changes them.

A file bound by no Module is therefore not writable by any Module-scoped task. To change or create
such a file, first bind it: add it to a realization as an entry, or as a `pending` entry when it
does not exist yet. Declaring the file is a Spec change within `SpecScope(M)`; creating it is then
within `ImplementationScope(M)`. This two-step shape is what lets a `specify` task decide where
code may go before an `implement` task writes it.

## The project registry

The registry is the project-wide index of Modules and a checked mirror of their `module` blocks. It
is what a coordinating session reads to plan work, to compute the sets of every Module involved and
to assign each task its boundary. A Module-scoped task needs neither to read nor to write it: its
own relations are in its entry, and the harness resolves identities for it.

Because the registry is outside every Module's write sets, a Module-scoped task that changes its
own `module` block leaves the mirror stale. `CHK.registry.mirror` reports that, and a project-level
step, which MAY regenerate the mirrored fields, reconciles it. Adding or removing a Module changes
which Modules exist, and is always such a project-level step: it writes the registry and the
parent's `contains`, together with whatever else the change of composition needs, such as the new
Modules' first documents and the parent's realization entries that move to them.

## Impact of a write

A write can break promises that other Modules rely on. The derived **impact** of a write lists
them, so that a harness can widen the task's read boundary, schedule review, or reject the write:

| Written | Concerns |
| --- | --- |
| a document D | every Module whose `SpecContext` contains D |
| a requirement, scenario or concept | every Module whose `relies_on` lists it, and every document that imports, narrows or relates to it |
| a contract | every Module that participates in it |
| a file F | every Module whose `ImplementationScope` contains F, and every Module that uses one of them, directly or through further `uses` |

Two rules follow from the model:

- **Shared files.** When several Modules bind a file, a task that writes it MUST be bound to every
  binding Module. The file carries the promises of all of them, and a writer bound to only one
  could break a promise it cannot see. Binding the task to every binder keeps its reads within the
  `SpecContext` of the Modules it is bound to (rule 3 below); no extra read is granted for sharing.
  A task that only reads the file needs no such widening.
- **Atomic reconciliation.** Some changes are only valid if other Modules change with them: a
  contract version increment requires every participant's `participates` version to move, and
  retiring or re-owning a concept requires its importers to follow. Such a change is a
  multi-Module change, and its write boundary is the union of the write sets of every Module it
  edits. A single-Module task MUST NOT be given another Module's scope to complete it.

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
3. **Read only within read sets.** Specification contents come from the `SpecContext` of the bound
   Modules; implementation contents from their `ImplementationScope` or, for the task types that
   assign it, from `ProjectImplementation`; external material from their `ExternalContext` or
   `ProjectImplementation`. A provider's code may be read and run, never changed, and it never
   replaces the provider's Specs as the statement of what the provider promises.
4. **Task material adds no source.** A harness MAY supply material produced for the task, such as a
   plan, a brief or a diff since a baseline. It is not a Protocol source and widens no set.

## Task types

Every task has exactly one task type. The type assigns each boundary set of the bound Modules one
access level:

| Task type | `SpecContext` | `ImplementationContext` | `ImplementationScope` | `SpecScope` | `ExternalContext` | `ProjectImplementation` |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | read | names | none | none | read | none |
| `specify` | read | names | none | write | read | none |
| `implement` | read | names | write | none | read | read |
| `test` | read | names | read | none | read | read |
| `review-spec` | read | names | none | none | read | none |
| `review-code` | read | names | read | none | read | read |
| `code-to-spec` | read | names | read | write | read | read |

The task types that read code, `implement`, `test`, `review-code` and `code-to-spec`, read the
whole `ProjectImplementation`: code is read and run together with the code it uses and the code
that uses it, and a package can only be imported whole. What they may change stays within the
bound Modules' scopes, so a Module's `uses` limits what a task changes, not what it reads. The task
types that work on Specs alone never see code contents.

- **`understand`** learns what a Module promises and how it is realized, without reading code:
  explaining, assessing, or planning a change. Planning is one use of understanding, not a task
  type of its own.
- **`specify`** changes the Module's own documents, including declaring `pending` realization
  entries for files a later `implement` task will create.
- **`implement`** changes the Module's realization: its bound files, and the pending files it
  declares.
- **`test`** reads the realization and its tests against the Specs. Running checks is evidence
  produced for the task, not a wider read.
- **`review-spec`** judges the Module's documents; **`review-code`** judges its realization against
  its Specs. A diff since a baseline is task material (rule 4).
- **`code-to-spec`** describes an existing realization in the Module's own documents. It exists for
  the uncommon project whose code came before its specification; a project that is specified first
  never needs it. It is the only task type that reads code in order to write Specs, and it
  never changes code. It records the behaviour it read as it is. Behaviour whose intent the code does
  not settle, such as a probable defect or an unexplained special case, MUST NOT be written as a
  promise: the documents state it as an honest unknown and the task reports it as an open question
  for a human to decide.

A `none` in the `SpecScope` column does not hide the Module's own documents: they are in
`SpecContext`, which every type reads. Each row stays inside rules 1 to 4, and every level can be
computed exactly from declarations. A harness MUST NOT give a task a level its type does not
assign; it MAY give less, for example by withholding external material a task does not need.

A scenario-scoped task is bound to the scenario's owner. A task bound to several Modules receives,
for each bound Module, that Module's sets at the levels its type assigns. When a path falls into
several sets, it receives the highest level any of them assigns, ordered `none`, `names`, `read`,
`write`.
