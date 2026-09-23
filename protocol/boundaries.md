# Boundaries

This chapter serves the Protocol's second purpose: letting a harness give each task a clear
boundary of what it may read and what it may write, derived from the specification rather than
guessed. [Context](context.md) defines the read sets in detail; this chapter defines the write sets,
the impact of a write, and how a harness composes sets into the boundary of one task.

The Protocol defines the **sets**. Which sets a given task receives, at which access level, and how
the boundary is enforced are decisions of the harness running the task. A specification never
grants a task anything by itself.

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

The first three are **read** sets, the last two are **write** sets. They are deliberately different:
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
- the installed Protocol copy.

A file bound by no Module is therefore not writable by any Module-scoped task. To change or create
such a file, first bind it: add it to a realization as an entry, or as a `pending` entry when it
does not exist yet. Declaring the file is a Spec change within `SpecScope(M)`; creating it is then
within `ImplementationScope(M)`. This two-step shape is what lets a planning task decide where code
may go before a coding task writes it.

## The project registry

The registry is the project-wide index of Modules and a checked mirror of their `module` blocks. It
is what a coordinating session reads to plan work, to compute the sets of every Module involved and
to assign each task its boundary. A Module-scoped task needs neither to read nor to write it: its
own relations are in its entry, and the harness resolves identities for it.

Because the registry is outside every Module's write sets, a Module-scoped task that changes its
own `module` block leaves the mirror stale. `CHK.registry.mirror` reports that, and a project-level
step, which MAY regenerate the mirrored fields, reconciles it. Adding or removing a Module changes
which Modules exist, and is always such a project-level step: it writes the registry and the
parent's `contains`.

## Impact of a write

A write can break promises that other Modules rely on. The derived **impact** of a write lists
them, so that a harness can widen the task's read boundary, schedule review, or reject the write:

| Written | Concerns |
| --- | --- |
| a document D | every Module whose `SpecContext` contains D |
| a requirement, scenario or concept | every Module whose `relies_on` lists it, and every document that imports, narrows or relates to it |
| a contract | every Module that participates in it |
| a file F | every Module whose `ImplementationScope` contains F |

Two rules follow from the model:

- **Shared files.** When several Modules bind a file, a task that writes it MUST also be able to read
  the documents of every binding Module, because it can otherwise break a promise it cannot see.
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
   Modules, implementation contents only from their `ImplementationScope`, and external material
   only from their `ExternalContext`. A provider's code is never read in place of its Specs.
4. **Task material adds no source.** A harness MAY supply material produced for the task, such as a
   plan, a brief or a diff since a baseline. It is not a Protocol source and widens no set.

Within these limits, different tasks receive different boundaries. For example, bound to one
Module M:

| Task | `SpecContext` | `ImplementationContext` | `ImplementationScope` | `SpecScope` | `ExternalContext` |
| --- | --- | --- | --- | --- | --- |
| Explain or plan | read | names | none | none | read |
| Write the Spec | read | names | none | write | read |
| Implement | read | names | write | none | read |
| Review code | read | names | read | none | read |

This table is illustrative; the Protocol does not prescribe task kinds. What it guarantees is that
each row can be computed exactly and stays inside rules 1 to 4.

A scenario-scoped task is bound to the scenario's owner. A task bound to several Modules receives
the union of their sets at the levels the harness chooses.
