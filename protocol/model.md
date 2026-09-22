# Node types

This chapter defines every kind of thing a specification may declare. [Relations](relations.md)
defines how they may be connected. The machine-readable vocabulary of both is
[`model.yaml`](model.yaml); the decision procedures are in [Checks](checks.md).

Each node type exists because a human reader needs the thing it names explained, a harness needs
it to compute a boundary, or both; each section says which.

The model has **seven node types** and three **value types**. A value type has no identity, no
owner and no explanation, because the specification makes no promise about it.

## Common obligations

| Field | Meaning |
| --- | --- |
| `id` | Stable, project-wide unique, matching `^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$` |
| `type` | One of the seven node types below |
| owner | Exactly one Module identity, derived from the defining document or declared for a document |
| explanation | Nonempty prose in the defining document; where it lives depends on the node type |

An ID prefix does not establish ownership. Titles and paths may change without changing identity.
An explanation cannot be outsourced: it is never a URL or a path into another document.

Nodes are declared at one of two sites. **Metadata-declared** nodes (`concept`, `realization`) are
records in a document's metadata and point to their explanation with a local `meaning` anchor.
**Reading-declared** nodes (`requirement`, `scenario`, `contract`) are located by reading syntax,
and their defining section is their explanation. A Module and the documents it owns are declared
in the `module` block of its entry's metadata, and mirrored in the project registry.

## module

**What it is.** One cohesive software responsibility, and the unit of context selection.

**Understanding.** A reader learns the system as a set of responsibilities, each explained by one
owner, independent of how files happen to be arranged.

**Boundaries.** A Module is what a task is bound to. Its read sets and write sets are all computed
from it, so "who promises this" and "what a task on it may read and write" have one answer that
survives file movement. The Protocol accepts over-inclusion in read sets deliberately, because a
reader cannot detect meaning that was silently withheld.

**Fields.** `id` (the entry's owner) and `title`, declared in the entry's `module` block and
mirrored in the registry. Its owner is itself. Its explanation is the
Purpose section of its entry document.

**Constraints.** A Module MUST own exactly one document whose role is `module` and whose reading
path ends in `module.md`; that document is its **entry**. A Module need not correspond to a package,
directory, service or process, and its realization may span, share or omit physical files. A
composite Module may bind no implementation of its own, and a composite Module may also bind files,
such as end-to-end tests of its own promises.

## document

**What it is.** A reading Markdown file **paired** with its metadata file. The pair is one node.

**Understanding.** Prose and the declarations it justifies cannot be separated, so metadata never
becomes a second, unreviewed specification.

**Boundaries.** The pair is the unit of ownership, selection and writing. A boundary always
contains both members or neither.

**Fields.** `id`, `owner` and `role`, stated in the metadata and agreeing with the owner's `owns`. `role` is
exactly `module` or `implementation`, with no default. A document explains itself; it has no
separate explanation.

- `module` — the entry and explanatory topics: the responsibility, its correct use, its design and
  its collaborations.
- `implementation` — the precise requirements, scenarios and canonical contracts. These are
  specifications, not source code, and are reading content like any other document.

**Constraints.** Both members have the same owner, identity and inclusion provenance. Registering
the reading path registers its exact companion. Role is document organization only: it MUST NOT act
as an ownership level, a context filter or a separate Spec kind.

The two roles serve understanding: explanation is not buried under acceptance cases, and precise
obligations are not diluted into prose.

## concept

**What it is.** One named meaning a reader must understand: a domain word, a record, a boundary
actor, an external standard, a participant in a collaboration. Its title is the **term** the
specification uses for it.

**Understanding.** Meaning is what crosses Module boundaries. A concept gives a word one owner and
one canonical sentence, so a reader finds one meaning per word, and importing, specializing,
retiring and colliding are declarations a tool checks instead of prose conventions.

**Boundaries.** Importing or relating to a concept puts its defining document into the read set,
and `referenced-by` makes the impact of changing its definition computable.

**Fields.** A metadata record with `id`, `type`, `title` and `meaning`, optional `retired` and
`external_conflict`; and a **definition**, written as the concept's row in the defining document's
Terminology table.

| Part | Meaning |
| --- | --- |
| definition | One sentence in the Terminology table: the canonical meaning, written once |
| `meaning` | Local anchor of the extended explanation in the defining document's reading |
| `retired` | Optional object `{"reason": "..."}`; the term is kept only for migration readers |
| `external_conflict` | Optional prose naming a conflicting usage outside this project |

The definition is one sentence on purpose, and it lives in the Markdown so that a human opening the
file reads it in place. Extended explanation belongs in reading prose at the `meaning` anchor.

**Constraints.** A concept is defined only in a `module` document. It MUST NOT bind implementation
and MUST NOT stand for another Module; a collaboration with another Module is a `uses` or
`contains` relation, and a naming collision with one is a `contrasts` relation.

**Who owns a word.** Owning a concept means being entitled to change its meaning: its definition
lies in the owner's write set, and a change concerns every importer. Ownership does not mean having
invented the word or using it most. Every concept has exactly one owner, chosen as follows:

- A word of a provider's own interface belongs to the provider; its consumers import it.
- A word several Modules use with one meaning belongs to their nearest common ancestor in the
  composition tree, or to the root. When the owner is hard to name, move the word one level up.
- A word that means different things in different Modules is several concepts, each owned where
  it is used, connected by `contrasts` or `narrows`.

A composite that owns shared vocabulary SHOULD keep it in one small `module` document, so that its
descendants select only that document when they import from it.

## realization

**What it is.** A declaration binding exact implementation paths or directory prefixes to this
Module.

**Understanding.** A reader learns where a promise is realized without inferring it from directory
names.

**Boundaries.** Its entries are the Module's `ImplementationScope`: the code a task bound to the
Module may be given to change. `pending` entries declare where new files may be created before any
code is written.

**Fields.** `id`, `type`, `title`, `meaning`, `entries` (exact project-relative paths, or directory
prefixes ending in `/`); optional `pending` (a subset of `entries` that does not yet exist).

**Constraints.** Non-pending entries MUST exist. Within a Module no two realizations list the same
entry, and the longest covering entry determines which realization a file belongs to. A directory
entry binds present and future regular files below it under the tool's deterministic exclusion
rule. No document member, generated output or project-control record may be bound, and a bound
directory MUST NOT contain a document member. Several Modules MAY bind the same path; each keeps
its own promises, and a change concerns all of them.

A pending entry records intent, not evidence, and is removed once the file exists. On the read
side, listing a path grants its **name**; contents are readable or writable only through a task
boundary. See [Boundaries](boundaries.md).

## requirement

**What it is.** One decidable, Module-wide obligation.

**Understanding.** A Module-wide promise is stated once, exactly, and survives the churn of the
situations that demonstrate it.

**Boundaries.** Its identity lets reviews, tasks and evidence name an exact promise.

**Constraints.** Declared by a heading in an `implementation` document; the heading supplies `id`
and title, and the section is its explanation. Its statement is one sentence containing `SHALL` or
`SHALL NOT` exactly once. Two obligations under one identity make partial satisfaction
undecidable, so they MUST be split.

## scenario

**What it is.** One concrete situation with preconditions, a trigger and a promised outcome.

**Understanding.** A concrete situation shows what a requirement means in practice; the step
grammar keeps a situation from quietly growing into a Module-wide obligation.

**Boundaries.** A requirement cannot be executed; a scenario is what tests declare they verify. A
task focused on a scenario is bound to the scenario's owner and receives that owner's whole
boundary.

**Constraints.** Declared by a heading in an `implementation` document; the heading supplies `id` and
title. Situations with different successful, failed, repeated or concurrent outcomes get their own
scenarios. A Module-wide obligation is defined once as a requirement and linked, never restated in
steps.

## contract

**What it is.** The canonical, versioned agreement for a shared interface: an API, command,
protocol, event or file boundary.

**Understanding.** A shared interface is stated once, with one owner, and every participant says
which version it conforms to.

**Boundaries.** Participants are declared, so the impact of a contract change and the multi-Module
write boundary it needs are computable. Without a version, a participant bound to an older meaning
is undetectable.

**Fields.** `id`, `version` (positive integer), `schema`, `semantics`, `example`, all inside one
`concorde-contract` fence in an `implementation` document. Its explanation is `semantics` together
with the prose of the section containing the fence.

**Constraints.** The schema vocabulary is explicit and offline: a schema MUST NOT load Spec documents
or remote resources. The example MUST satisfy the schema. A behaviour or schema change increments
`version`, and every participant is reconciled atomically.

## Value types

These appear as relation targets or attributes but are not nodes.

| Value | Where it appears | Why it is not a node |
| --- | --- | --- |
| **path literal** | `binds`, external `includes`, `verifies` | A path carries no promise and has no owner in the Spec's sense. |
| **anchor** | `meaning` of nodes and reified relations | It has no identity of its own; only its declaration refers to it. |
| **digest** | context identity | It is a measurement of a source member, not a declared thing. |
