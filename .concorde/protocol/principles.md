# Spec Protocol principles

Concorde Spec Protocol 12.0.0 defines how a project describes itself as a set of Modules, what each
Module promises, and how the Modules and their files relate. The Protocol applies to project Specs,
including those of software implementing the Protocol. The standard's own chapters need not
describe themselves as Modules.

## Two purposes

The Protocol exists for two purposes. Every rule in it serves at least one of them, and each
chapter says how its rules do.

1. **Understanding.** A human grasps the backbone of the project quickly from its specification:
   its parts, what each is for, how they fit together and how the main flows run. The ultimate goal
   is that a human never needs to read the code to understand the project; the specification is
   enough.
2. **Boundaries.** A harness running an AI task can derive from the specification exactly what the
   task may read and what it may write. Different tasks need different boundaries, so the Protocol
   defines the sets that boundaries are composed from and the task types that compose them.

The two support each other. A boundary is only useful if what lies inside it is understandable, and
a Module that a human can understand as one responsibility is also the natural unit of a task.

Four failures undermine these purposes, and the rules of the Protocol are designed against them:

1. **Inferred promises.** A reader concludes that something is promised because a file, a
   directory, a name, a link or an adjacent paragraph suggested it. Nothing promised it.
2. **Meaning drift.** The same word denotes different things in different documents, silently.
3. **Authority creep.** Permission to read something becomes permission to change it, or a
   relationship becomes an execution grant.
4. **Fabricated evidence.** Coverage or conformance is claimed by the promise itself rather than by
   anything that ran.

## The model at a glance

A project's specification is **one graph**. Its nodes are the things the specification declares;
its edges are the relations between them. Everything else in the Protocol is either how the graph
is written down, or something computed from it.

```d2 illustrative
direction: right
parent: Module {
  m: Module {
    d: Document {
      c: Concept
      rz: Realization {
        f: Implementation files {shape: cylinder}
      }
      rs: Requirement / Scenario
      k: Contract
    }
  }
}
provider: Module
foreign: Concept of another Module
t: Test file {shape: cylinder}
parent.m -> provider: uses / includes
parent.m.d -> foreign: imports
parent.m -> parent.m.d.k: participates
t -> parent.m.d.rs: verifies
```

Nesting shows composition: a Module contains Modules, owns documents, a document defines nodes and
a realization binds files.

**Nodes.** Seven types, defined in [Node types](model.md):

| Node | What it is |
| --- | --- |
| Module | One responsibility. The unit of ownership, of context and of task boundaries |
| Document | A Markdown reading file paired with its JSON metadata; the unit a Module owns |
| Concept | A named meaning a reader must understand; its title is a term |
| Realization | A binding of implementation files to the Module |
| Requirement | One Module-wide `SHALL` obligation |
| Scenario | One concrete situation in `GIVEN`/`WHEN`/`THEN` steps |
| Contract | The versioned agreement for a shared interface |

**Edges.** Thirteen typed, directed relation types, defined in [Relations](relations.md): `owns`,
`defines`, `contains` and `uses` state who is responsible for what; `includes` selects extra
reading; `binds` joins the specification to code; `imports`, `narrows`, `supersedes`, `contrasts`
and `relates` connect meanings and architecture; `participates` and `verifies` tie contracts and
tests to promises.

**Where the graph is written.** Every node and edge is declared exactly once, in a document owned
by the Module responsible for it: in its reading, by a fixed syntax, or in its metadata. A Module's
own relations are in its entry's metadata; the project registry mirrors them for a global view.

**What is computed from the graph.** Nothing below is declared; all of it is derived:

- **Context** — what a reader of a Module may read. See [Context](context.md).
- **Scope** — what a task bound to a Module may be given to write. See
  [Boundaries](boundaries.md).
- **Boundary** — the read and write sets a task receives, fixed by its task type.
- **Views** — diagrams, indexes and pages a human reads. See [Views](views.md).
- **Checks** — decidable rules that the graph is well formed. See [Checks](checks.md).

A few more words are used throughout:

| Term | Meaning |
| --- | --- |
| Declared | Written in the specification: a node or relation stated at its declaration site |
| Derived | Computed from declarations, never written by hand |
| Declaration | The single place where a node or relation is stated |
| Owner | The Module entitled to change a node; every node has exactly one |
| Entry | A Module's `module.md` document, the start of reading it and the home of its own relations |
| Reading | The Markdown member of a document, written for humans |
| Metadata | The JSON member of a document, holding identities and declarations |
| Registry | The project-wide index of Modules, a checked mirror of their entries |

## Axioms

### A1. Every node has one identity, one owner and one explanation

Every declared node MUST have a stable project-wide identity, exactly one owning Module, and
nonempty explanatory prose in the document that defines it. A declaration without an explanation is
invalid, not merely incomplete. Identity survives title and path changes.

*Serves both:* a reader always finds the explanation, and a harness always knows whose write set a
node lies in.

### A2. Every relation is typed, directional and declared exactly once

A relation MUST have a registered type, an explicit source and target, and one declaration site
fixed by its type. The same fact MUST NOT be declarable in two places; the only permitted copy is
a mirror the Protocol names, the project registry, whose equality with the declarations is
checked. A filename, path, title, link, prose sentence, unchecked diagram or directory
neighbourhood MUST NOT create a relation.

*Serves both:* nothing is promised by accident, and boundaries depend only on declarations.

### A3. Reading, writing and proving stay separate

Read sets and write sets are derived from different declarations. Being able to read a document
never makes it writable: a provider's Specs are readable by its consumers and writable only within
the provider's own scope. Realization bindings put file **names** in the read side; contents
become readable or writable only through a task boundary. Evidence is never produced by
specification content.

*Serves boundaries:* this is the rule against authority creep.

### A4. Every relation declares what context it grants and what it requires

A relation type MUST declare `context_grants` and `context_requires`. For every Module, everything
its declared relations require MUST be granted by its declared relations. The reconciliation is a
structural check, defined in [Context](context.md).

*Serves both:* a reader of a Module has every definition its Spec relies on, and a harness that
grants the Module's read set grants a self-sufficient one.

### A5. Evidence originates from what ran, never from what was promised

An evidence relation MUST be declared by the artifact that executes, not by the specification that
the artifact verifies. A specification MUST NOT declare its own coverage.

*Serves both:* a reader can trust that coverage was not merely claimed, and coverage cannot be
claimed from inside the write set of the Module whose promises it covers.

### A6. Views are derived or checked

A published diagram, index or navigation tree is derived from declared relations. A diagram
written in reading is either **checked**, asserting only declared relations, or **illustrative**, explicitly
marked and excluded from the model. See [Views](views.md).

*Serves understanding:* pictures a human relies on cannot silently diverge from the model.

### A7. No inference, no recursion

The model is assertional. Every check operates on declared relations only. No relation is
transitive, symmetric or invertible unless its type says so; derived indexes are never a source of
obligations. Context expansion is one level and never recursive.

*Serves boundaries:* every set is computable and every member is attributable to a declaration.

## Conformance

A conformance claim identifies its Protocol version and distinguishes three claims that cannot
substitute for one another:

- **Structural conformance.** Identities, ownership, pairing, declaration sites, cardinalities,
  checked views and the context reconciliation all hold. This is machine-decidable; see
  [Checks](checks.md). It is what makes boundaries computable.
- **Semantic sufficiency.** The readable content explains the responsibility, its correct use, its
  design and its obligations to the intended reader. This is what makes the specification
  understandable, and it is not machine-decidable.
- **Implementation conformance.** The realization satisfies the requirements and scenarios. This is
  established by evidence, never by structure.

Passing structural checks MUST NOT be reported as either of the other two. Missing meaning is an
attributed gap; a reader MUST NOT read outside its boundary, or infer a promise from source code, to
repair it.

## What the Protocol does not define

Which task type a harness assigns to a piece of work, and how it enforces the resulting boundary. Docsite pages, navigation,
themes and interaction. The serialization and location of the project registry, tool
configuration, worker wire formats and context delivery. These are separate agreements; a change
in any of them is not a Protocol version change.

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

# Relations

Relations serve both purposes of the Protocol: they are the explained connections a human reads
as architecture, and the only input from which a harness computes read and write sets.

Every relation type declares the same attribute set. A connection that cannot fill these fields is
not a relation (axiom A2). The vocabulary is closed: a project cannot register relation types of
its own, and tool data in a metadata `extensions` object never creates a relation.

| Attribute | Meaning |
| --- | --- |
| `source` / `target` | Permitted node or value types |
| `cardinality` | How many may exist, and any uniqueness rule |
| `declared_in` | The single site where it is declared: `entry` (the entry's `module` block), `metadata`, `reading` or `implementation-source` |
| `mirrored_in` | Where a checked copy is kept, if anywhere: only `registry` |
| `reified` | Attributes the relation itself carries |
| `symmetric` | Whether one declaration holds in both directions |
| `context_grants` | What it adds to the declaring Module's context, in the expression language of [Context](context.md) |
| `context_requires` | What MUST be in the declaring Module's context for the declaration to be honest |
| `checks` | Decidable rules, by identity, defined in [Checks](checks.md) |

**Where a relation is declared** follows one rule: a relation whose source is a Module is declared
in the `module` block of that Module's entry; a relation whose source is a document or a node
defined in a document is declared in that document, in its metadata or by reading syntax. Either
way the declaration lies in the source Module's own `SpecScope`: a Module changes its own
collaborations without writing into another Module, and a task bound to it sees all of its
relations in its own documents.

Module-level relations are also **mirrored** in the project registry, which gives a project-wide
view without opening every entry. The mirror is not a second declaration site: it MUST equal the
entries, and `CHK.registry.mirror` reports any difference.

The attribute blocks below are the prose form of [`model.yaml`](model.yaml). The two MUST agree.

---

## Ownership and collaboration

### `owns`

```yaml
source: module
target: document
cardinality: "1..N per Module; a document is owned exactly once"
declared_in: entry
mirrored_in: registry
context_grants: spec(target)
context_requires: []
```

This Module is responsible for this document. Ownership is exclusive so that "who can change
this promise" has exactly one answer: the document lies in this Module's `SpecScope` and in no
other Module's write set. A Module always reads its own promises.

**Checks.** `CHK.owns.unique`, `CHK.document.entry`.

### `defines`

```yaml
source: document
target: [concept, realization, requirement, scenario, contract]
cardinality: "0..N; a node is defined exactly once"
declared_in: metadata (concept, realization) | reading (requirement, scenario, contract)
context_grants: none
context_requires: []
```

This document is the defining site of this node, so its owner is the node's owner and its
explanation lives here. The declaration site is fixed by the target's node type: concepts and
realizations are metadata records, while requirements, scenarios and contracts are located by their
reading syntax. A concept's one-sentence definition is its defining row in the document's
Terminology table.

**Checks.** `CHK.defines.once`, `CHK.defines.role` — requirements, scenarios and contracts are
defined only in `implementation` documents.

### `contains`

```yaml
source: module
target: module
cardinality: "0..N; a Module has at most one parent; acyclic"
declared_in: entry
mirrored_in: registry
reified: [meaning, relies_on]  # relies_on optional
context_grants: spec(selection)
context_requires: []
```

The source Module is accountable for a responsibility that this child fulfils in part, and its
`meaning` explains how. The parent receives the child's Specs, because it cannot explain the child's
part without them. `relies_on` narrows that grant exactly as for `uses`.

Composition is the top-down reading path through a project. A project SHOULD have exactly one
Module without a parent, its **root**, so that every Module is reachable from one entry. A root, or
any composite Module, MAY realize nothing itself or MAY bind files of its own, such as end-to-end
tests of its promises.

Whether a parent's explanation of its decomposition is adequate is a semantic judgement. The
decidable consequences are acyclicity, single parenthood, a resolvable explanation and the grant.

**Checks.** `CHK.contains.acyclic`, `CHK.contains.single-parent`, `CHK.contains.root`,
`CHK.relation.meaning`, `CHK.relies-on.owned`, `CHK.relies-on.linked`.

### `uses`

```yaml
source: module
target: module
cardinality: "0..N; at most one per target"
declared_in: entry
mirrored_in: registry
reified: [meaning, relies_on]  # relies_on optional
context_grants: spec(selection)
context_requires: []
```

The source Module relies on promises this provider makes. The `meaning` anchor states the
provider's responsibility, when the collaboration applies, the canonical promises relied upon, and
this Module's own duties and failure reactions, so a reader never meets a collaboration as a bare
arrow. The consumer receives the provider's Specs.

`relies_on` optionally lists the provider's promises this Module depends on: requirements,
scenarios, contracts and concepts, by identity. When present, the consumer receives only the
provider's entry and the documents defining those nodes, instead of every document the provider
owns. The list is exact and checkable, it turns the prose "promises relied upon" into links a reader
can follow, and it makes the impact of changing one promise precise.

`uses` is not ownership: the provider keeps one identity and is owned by none of its consumers. It
implies no deployment, directory nesting or shared source. Mutual `uses` between two Modules is
legitimate.

**Checks.** `CHK.uses.no-self`, `CHK.uses.unique`, `CHK.relation.meaning`, `CHK.relies-on.owned`,
`CHK.relies-on.linked`.

---

## Context

### `includes`

```yaml
source: module
target: [module, document, path-literal]
cardinality: "0..N; unique per (kind, target)"
declared_in: entry
mirrored_in: registry
reified: [kind, reason]
context_grants: spec(selection) | external(target)
context_requires: []
```

This Module reads something it neither owns nor depends on. `kind` is `module` (that Module's owned
documents), `document` (one document) or `external` (a directory or file of pinned third-party
material). `reason` records why, because removing an inclusion changes provenance and context
identity.

Specification inclusions and external inclusions are one relation because both answer the same
question, *what else does this Module read*, and differ only in the channel they fill.

**Checks.** `CHK.includes.no-self`, `CHK.includes.unique`, `CHK.includes.reason`,
`CHK.includes.redundant`, `CHK.external.exists`, `CHK.external.no-overlap`.

---

## Realization

### `binds`

```yaml
source: realization
target: path-literal
cardinality: "1..N per realization"
declared_in: metadata (the realization's entries)
context_grants: implementation(target)
context_requires: []
```

These paths realize this Module's promises. On the read side the grant is the implementation
channel: **names only**. On the write side the covered files form the Module's
`ImplementationScope`, the code a task bound to this Module may be given to change; see
[Boundaries](boundaries.md). A file bound by no Module is in no Module's scope.

**Checks.** `CHK.binds.exists`, `CHK.binds.disjoint`, `CHK.binds.no-spec`,
`CHK.binds.pending-subset`, `CHK.binds.unbound`.

---

## Meaning

### `imports`

```yaml
source: document
target: concept
cardinality: "0..N; unique per target"
declared_in: reading (an import row of a module document's Terminology table)
context_grants: none
context_requires: spec(definer(target))
```

This document uses a term whose canonical definition another Module owns. The import row links to
the definition and never copies it. The document that defines the concept MUST be in the
importer's context.

The owner of a shared word is the Module entitled to change its meaning; see
[Node types](model.md#concept). An import from a Module that is neither a provider the importer
uses, nor one of its ancestors or descendants, usually means the word belongs higher in the
composition tree, which `CHK.imports.owner` reports.

**Checks.** `CHK.imports.foreign`, `CHK.imports.owner`, `CHK.terminology.import-row`,
`CHK.context.reconciled`.

### `narrows`

```yaml
source: concept
target: concept
cardinality: "0..N"
declared_in: metadata
context_grants: none
context_requires: spec(definer(target))
```

The source concept is a strictly more specific case of the target concept, so the two cannot drift
apart unnoticed.

**Checks.** `CHK.narrows.acyclic`, `CHK.context.reconciled`.

### `supersedes`

```yaml
source: concept
target: concept
cardinality: "0..1 per source"
declared_in: metadata
context_grants: none
context_requires: spec(definer(target))
```

The source concept is retired and the target replaces it. A retired concept without a replacement
states why in its `retired.reason`.

**Checks.** `CHK.concept.retired`, `CHK.context.reconciled`.

### `contrasts`

```yaml
source: concept
target: [concept, module]
cardinality: "0..N; at most one per unordered pair"
declared_in: metadata
reified: [reason]
symmetric: true
context_grants: none
context_requires: []
```

These two are easily confused and are **not** the same thing. The `reason` states the difference,
so a reader who has met only one of them is warned. It requires no context: the warning is the
point, and forcing each side to read the other would couple unrelated Modules by an accident of
naming.

**Checks.** `CHK.contrasts.required`, `CHK.contrasts.once`.

### `relates`

```yaml
source: [concept, realization, module]
target: [concept, realization, module]
cardinality: "0..N; unique per (source, verb, target)"
declared_in: metadata
reified: [verb]
context_grants: none
context_requires: spec(definer(target))
```

A named architectural relationship: the realization *saves* the record, the actor *submits* the
request, the Module *publishes* the event. `verb` is free text, recommended as a verb phrase. The
source is a node this document's owner owns, or that Module itself; the target may belong to any
Module, whose defining document then MUST be in context.

`relates` states structure for readers and for checked diagrams. It is not a dependency: relying on
another Module's promises is still a `uses`.

**Checks.** `CHK.relates.source`, `CHK.relates.verb`, `CHK.context.reconciled`.

---

## Interfaces and evidence

### `participates`

```yaml
source: module
target: contract
cardinality: "0..N; unique per (contract, peer, role)"
declared_in: entry
mirrored_in: registry
reified: [version, role, peer, meaning]
context_grants: none
context_requires: spec(definer(target))
```

This Module provides or requires a shared contract. `version` is the contract version the
participant conforms to; `role` is `provided` or `required`; `peer` names the internal Module on the
other side or `external`. A participant that has not received the canonical definition cannot
honestly claim conformance, so the defining document MUST be in context.

**Checks.** `CHK.participates.version`, `CHK.participates.complementary`,
`CHK.participates.unique`, `CHK.relation.meaning`, `CHK.context.reconciled`.

### `verifies`

```yaml
source: path-literal
target: scenario
cardinality: "0..N"
declared_in: implementation-source
context_grants: none
context_requires: []
```

This test asserts that it verifies this scenario. It is the only relation declared outside
specification content, because coverage must originate from the artifact that runs (axiom A5).
Reading content MUST NOT list verifying tests or prescribe coverage declarations. A declared test
is not proof of fulfilment, and missing coverage does not cancel a promise. Because tests declare
coverage, it cannot be claimed from inside the write set of the Module whose promises it covers.

**Checks.** `CHK.verifies.resolves`, `CHK.evidence.no-spec-coverage`.

---

## Derived indexes

These are computed, never declared. They are evidence, navigation and impact aids, never a source
of obligations, and never widen a boundary.

| Derived | Computed from | Used for |
| --- | --- | --- |
| `selected-by` | inverting context selection | which Modules read a document, and so are concerned when it changes |
| `referenced-by` | inverting `relies_on`, `imports`, `narrows`, `supersedes`, `relates` and `participates` | which declarations depend on a concept, node or contract |
| `implemented-by` | inverting `binds` | which Modules a file change concerns |
| `covered-by` | aggregating `verifies` | per-scenario coverage reports |

# Context

Context is the information explicitly made available to a reader of one Module. Knowing that a
document exists does not make it available; neither does linking to it or naming a word it defines.
Only declared relations grant context.

This chapter defines the read side of the Protocol's boundary purpose: the three context
channels, how a Module's context is selected, the reconciliation of what relations grant against
what they require, and context identity. The write side is in [Boundaries](boundaries.md). Because
the reconciliation guarantees that a Module's context holds every definition its own Spec relies
on, the same selection is also what a human reader of the Module needs open beside it.

## Three channels

| Channel | Granted by | Contains | Authority conveyed |
| --- | --- | --- | --- |
| `spec` | `owns`, `contains`, `uses`, `includes` of kind `module` or `document` | both members of each selected document | read only |
| `implementation` | `binds` | the **names** of bound paths | none |
| `external` | `includes` of kind `external` | pinned third-party material | read only |

The channels stay separate so that "may read this Module's promises" never implies "may read or
change its code". Whether a task receives implementation contents, read-only or writable, is part
of its task boundary; see [Boundaries](boundaries.md).

## Expressions

`context_grants` and `context_requires` in [`model.yaml`](model.yaml) use this expression language:

```text
spec(target)             the target document
spec(selection)          for a contains or uses with relies_on: the target's entry and the
                         documents defining the listed nodes; otherwise every document the
                         target Module owns
spec(definer(target))    the document that defines the target node; for a Module target,
                         that Module
external(target)         the pinned material at the target path
implementation(target)   the name of the target path
none                     nothing
```

A requirement `spec(D)` naming a document D is satisfied when D is in the Module's spec channel. A
requirement `spec(N)` naming a Module N is satisfied when at least one document N owns is in it.

## Spec context selection

Let `D(M)` be the documents Module M owns, and `members(U)` the reading and metadata members of a
document U.

```text
Spec(M)        = D(M)
               ∪ ⋃ { selection(r) : r a contains, uses or spec includes declared by M }
SpecContext(M) = ⋃ { members(U) : U ∈ Spec(M) }

selection(r to Module N) = { entry(N) } ∪ { definer(x) : x ∈ r.relies_on }  if relies_on present
                         = D(N)                                               otherwise
selection(includes document U) = { U }
```

Selection is one level. A selected Module contributes its owned documents, never the documents its
own relations select. Parentage, dependency and inclusion of the target, term usage, participation,
Markdown links, directory neighbourhood and implementation bindings add nothing further. Because
expansion is not recursive, cycles among Modules are harmless, and every member of a read set is
explained by the one declaration that selected it.

A scenario query resolves the scenario's owner and selects that owner's whole context. It never
trims to the scenario, and never selects the consumer that happened to read it.

Every selected document contributes **both** members whole. No excerpt, summary, rendered view or
diagram export substitutes for a complete document.

## Reconciliation

```text
Requires(M) = ⋃ { r.context_requires : r declared in the metadata or reading
                                        of a document M owns, including its entry }

CONFORMANCE:  ∀ q ∈ Requires(M) :  satisfied(q, Spec(M))
```

`imports`, `narrows`, `supersedes`, `relates` and `participates` each require the document that
defines their target. A Module that declares one without having that document in its context fails
`CHK.context.reconciled`. The repair is an explicit grant: a `uses` or `contains` that selects the
document, or an `includes` that states a reason.

The check is exact, because a node has exactly one defining document. A `uses` or `contains` that
narrows its grant with `relies_on` selects the documents defining the listed promises, so the
narrowing is exact as well. What no check establishes is that the list names every promise the
Module actually relies on; `CHK.relies-on.linked` catches every one the explanation links to.

## Implementation context

```text
ImplementationContext(M) = ⋃ { entries of M's realizations }
ImplementationContext(scenario S) = ImplementationContext(owner(S))
```

Exact entries and files below directory prefixes resolve under an explicit deterministic exclusion
rule. Pending entries record intent without pretending that missing content exists.

Document members never belong to implementation context. When another Module binds the same file,
a change to it concerns that Module too; this adds neither that Module's Specs nor its code to this
reader's context. A Module with no bindings has an empty implementation context, which does not
prove it has no realization.

## External context

```text
ExternalContext(M) = ⋃ { readable files below M's external inclusions }
```

Only the selecting Module's own external inclusions count; a selected Module does not bring its
own. External material MUST be pinned by the project's version control, for example as a
submodule at a fixed commit, so that its content is identified by the checkout rather than by a
second declared revision. A tool MAY exclude media and archives by a documented deterministic rule.
An undeclared network fetch or an installed dependency's sources MUST NOT substitute for declared
material. External material supplies no promise absent from the Spec.

## Context identity

A resolved context is identified by its selected sources and the declarations that selected them,
so a harness can tell whether anything inside a boundary changed since a check.
Every source record carries document identity, owner, path, member role (`reading` or `metadata`),
an exact-byte SHA-256 digest, and every relation that selected it. External entries carry one tree
digest each.

The identity changes, even when the set of paths is unchanged, on:

- any byte change in either member of a selected document, including whitespace;
- a change to the declarations that selected the context, including removing a redundant inclusion;
- an ownership transfer;
- a change to pinned external material.

What a tool does with evidence bound to a previous identity is the tool's policy.

## Visibility

The resolved context is the exact visibility scope of a bounded reader: every selected source is
available whole and no unselected source is visible. How a tool makes it available is not part of
the Protocol. A tool MAY also supply task material such as changes since a baseline; such material
adds no source and replaces none. A reader that opened only some granted files still received the
complete context: missing meaning is judged against the full granted scope.

## Gaps

A missing definition is a semantic gap even after structural resolution succeeds. Record the needed
promise, its owner when known, the selected Module, the context identity and the blocked step. Do
not follow a selected Module's own relations or a prose link to repair it. An additional explicit
selection is a new context, not a retrospective claim that the previous one was complete.

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
   Modules, implementation contents only from their `ImplementationScope`, and external material
   only from their `ExternalContext`. A provider's code is never read in place of its Specs.
4. **Task material adds no source.** A harness MAY supply material produced for the task, such as a
   plan, a brief or a diff since a baseline. It is not a Protocol source and widens no set.

## Task types

Every task has exactly one task type. The type assigns each boundary set of the bound Modules one
access level:

| Task type | `SpecContext` | `ImplementationContext` | `ImplementationScope` | `SpecScope` | `ExternalContext` |
| --- | --- | --- | --- | --- | --- |
| `understand` | read | names | none | none | read |
| `specify` | read | names | none | write | read |
| `implement` | read | names | write | none | read |
| `test` | read | names | read | none | read |
| `review-spec` | read | names | none | none | read |
| `review-code` | read | names | read | none | read |

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

A `none` in the `SpecScope` column does not hide the Module's own documents: they are in
`SpecContext`, which every type reads. Each row stays inside rules 1 to 4, and every level can be
computed exactly from declarations. A harness MUST NOT give a task a level its type does not
assign; it MAY give less, for example by withholding external material a task does not need.

A scenario-scoped task is bound to the scenario's owner. A task bound to several Modules receives,
for each bound Module, that Module's sets at the levels its type assigns. When a path falls into
several sets, it receives the highest level any of them assigns, ordered `none`, `names`, `read`,
`write`.

# Required format

This chapter defines how the [node types](model.md) and [relations](relations.md) are written.
The fixed reading structure serves understanding: every Module reads the same way. The fixed
declaration syntax serves boundaries: a tool computes every set without interpreting prose.
Satisfying the syntax establishes structural conformance only; it proves nothing about meaning.

## Documents

A registered document is a pair: an explicit project-relative Markdown reading path, and that same
path with `.json` appended. `checkout/module.md` and `checkout/module.md.json` are **one** document.

Reading files are nonempty UTF-8 Markdown. Metadata files are UTF-8 JSON with unique keys and no
non-JSON numeric constants. Paths use canonical project-relative POSIX spelling: no absolute paths,
backslashes, empty, dot or traversal components, control characters or symlink aliases.

Both members always travel together: same owner, same identity, same selection provenance, both in
context, both in source digests. Registering a reading path
registers its exact companion. Tools MUST NOT discover documents from the filesystem or by
following Markdown links; this is what lets every boundary set be enumerated from declarations
alone.

## Module declaration

A Module declares itself and its Module-level relations in a `module` block of its **entry's**
metadata. This is the one declaration site of those relations: a task bound to the Module reads and
writes it as part of its own documents, and learns who it relates to without any global file.

```json
{
  "schema_version": 3,
  "document": {"id": "document.checkout.module", "owner": "module.checkout", "role": "module"},
  "module": {
    "title": "Checkout",
    "owns": ["checkout/module.md", "checkout/contracts.md"],
    "contains": [],
    "uses": [
      {"target": "module.inventory", "meaning": "#uses-inventory",
       "relies_on": ["req.inventory.hold-expiry", "concept.inventory.reservation",
                     "contract.inventory.reserve"]}
    ],
    "includes": [
      {"kind": "document", "target": "document.delivery-terms", "reason": "delivery window wording"},
      {"kind": "external", "target": "references/payment-sdk/", "reason": "payment request fields"}
    ],
    "participates": [
      {"contract": "contract.inventory.reserve", "version": 1, "role": "required",
       "peer": "module.inventory", "meaning": "checkout/contracts.md#reserve-participation"}
    ]
  },
  "defines": [],
  "relations": []
}
```

- The `module` block appears in the entry's metadata and in no other document. The Module's
  identity is the entry's `document.owner`.
- `title` is required. Module titles are unique in the project.
- `owns` lists reading paths, is nonempty and includes the entry itself.
- `contains` and `uses` entries have `target` and `meaning`, and optionally a nonempty `relies_on`
  list of identities of requirements, scenarios, contracts and concepts the target owns. Without
  `relies_on` the whole target is selected.
- `includes` entries have `kind` (`module`, `document` or `external`), `target` (a Module identity,
  a document identity, or a project-relative path; a directory ends in `/`) and a nonempty `reason`.
- `participates` entries have `contract`, `version`, `role` (`provided` or `required`), `peer` (a
  Module identity or `external`) and `meaning`.
- `contains`, `uses`, `includes` and `participates` are explicit arrays and MAY be empty.
- A relation `meaning` is a local `#anchor` into the entry, or a qualified `<reading path>#<anchor>`
  into another document the Module owns.

## Project registry

The project registry is the index of all Modules and a **mirror** of their declarations. It gives
a project-wide view, such as the one a coordinating session uses to plan work and set each task's
boundary, without opening every Module. It is not a declaration site.

```json
{
  "modules": [
    {"id": "module.checkout", "title": "Checkout", "entry": "checkout/module.md",
     "owns": ["checkout/module.md", "checkout/contracts.md"], "contains": [],
     "uses": [{"target": "module.inventory", "meaning": "#uses-inventory",
               "relies_on": ["req.inventory.hold-expiry", "concept.inventory.reservation",
                             "contract.inventory.reserve"]}],
     "includes": ["..."], "participates": ["..."]}
  ]
}
```

- Every Module has exactly one registry record: `id`, `title`, `entry` (the entry's reading path)
  and every field of its `module` block, equal to that block.
- The registry lists which Modules exist. A tool MAY regenerate the mirrored fields from the
  entries; adding or removing a Module is a deliberate registry change.
- A disagreement between the registry and an entry is a structural error
  (`CHK.registry.mirror`). Neither side silently wins; the change that caused it is reconciled.

The Protocol fixes the registry's content. Its serialization and location are a tool agreement.

## Metadata

```json
{
  "schema_version": 3,
  "document": {"id": "document.checkout.topic.holds", "owner": "module.checkout", "role": "module"},
  "defines": [
    {"id": "concept.checkout.basket", "type": "concept", "title": "Basket",
     "meaning": "#concept.checkout.basket"},
    {"id": "concept.checkout.hold", "type": "concept", "title": "Hold",
     "meaning": "#concept.checkout.hold"},
    {"id": "realization.checkout.service", "type": "realization", "title": "Checkout service",
     "meaning": "#realization.checkout.service", "entries": ["src/checkout/"], "pending": []}
  ],
  "relations": [
    {"type": "narrows", "source": "concept.checkout.hold",
     "target": "concept.inventory.reservation"},
    {"type": "contrasts", "source": "concept.checkout.basket", "target": "concept.catalog.basket",
     "reason": "a catalog basket is a saved wish list; this one is submitted immediately"},
    {"type": "relates", "source": "realization.checkout.service", "verb": "records",
     "target": "concept.checkout.hold"}
  ],
  "extensions": {}
}
```

- `schema_version` is the integer `3`.
- `document` has exactly `id`, `owner` and `role`, agreeing with the owner's `owns`. `role` is
  exactly `module` or `implementation` with no default; the entry `module.md` has role `module`.
- `module` is present exactly in the entry; see [Module declaration](#module-declaration).
- `defines` lists only `concept` and `realization` records. Concepts are defined only in `module`
  documents, and each concept's definition is its row in the document's Terminology table.
  Requirements, scenarios and contracts are located by their reading syntax below.
- `relations` lists `narrows`, `supersedes`, `contrasts` and `relates`, each naming a `source` that
  this document defines or, for `relates`, the owning Module itself. Imports are declared by
  Terminology rows, not here.
- `defines` and `relations` are explicit arrays and MAY be empty.
- `extensions`, if present, is an object keyed by stable names holding tool data. A tool MUST define
  and validate the extension vocabulary it uses. An extension MUST NOT create a relation, change
  ownership or selection, or hide essential meaning.

## Identities and anchors

Module, document, concept, realization, requirement, scenario and contract identities are
project-wide unique and match:

```text
^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$
```

Requirement identities begin `req.`; scenario identities begin `scenario.`. Prefixes do not
establish ownership. Stable identities let links survive renames and moves, and let boundaries,
reviews and tests name exactly one thing.

A readable anchor is one of three forms:

- a **standalone** line of one or more `<a id="identity"></a>` before its explanation, which
  extends to the next heading;
- an **opening** group of one or more `<a id="identity"></a>` at the very start of a paragraph or of
  a list item's text, which explains exactly that paragraph or list item: the paragraph ends at the
  next blank line, heading or fence, and the list item also at the next list item that is not
  indented deeper;
- an ATX heading carrying a trailing `{#identity}`, which extends to the next heading of the same or
  higher level. Requirement and scenario headings supply their identity directly.

A standalone or heading anchor also ends at the next anchor group. Anchors are unique within their
document and outside fences, and an anchor anywhere else, such as inside a sentence or a table, is
not a readable anchor.

Several anchors in one group identify several nodes explained together by the same prose, and that
prose MUST explain all of them. The region of an anchor is the text a tool attributes to its nodes,
for instance when it compares definitions between revisions, so an opening group is the precise
choice for an item in a list of short explanations.

## Reading structure

An entry `module.md` has these level-2 sections, outside fences, each exactly once and in any order:

```text
Purpose
Terminology
Usage
Design
Relationships
```

It MAY have further level-2 sections, for example one that shows how the Module is built. A level-1
title and brief navigation may precede the first of them. Purpose is nonempty plain prose: no lists,
tables, nested headings or fences. Usage, Design and Relationships contain explanatory prose, not
only links, headings or diagrams. Honest unknowns are stated explicitly.

A `module`-role topic begins with a short orienting introduction. When the topic defines or imports
a concept, its first level-2 section is `## Terminology`. In the entry, Terminology may hold only
prose when the entry defines and imports nothing.

`module` documents MUST NOT contain requirement or scenario definitions or canonical contract
fences. `implementation` documents contain those definitions and MAY group them under headings
that carry no identity. Both roles are reading content; role never filters context.

Exact private APIs, wire fields, serialization rules, internal limits and executable topology belong
in `implementation` reading regardless of the syntax used to write them. Conceptual design and
safe-use explanation stay in `module` reading. A `module` document MUST NOT hide destructive
defaults, security limits or known unfulfilled guarantees behind a link.

## Terminology

The Terminology section of a `module` document holds exactly one Markdown table with the columns
`Term` and `Definition`, optionally followed by orienting prose. Every row is one of two kinds:

```markdown
## Terminology

| Term | Definition |
| --- | --- |
| Hold | Stock withheld from other customers until a submission succeeds or expires. |
| [Reservation](../inventory/module.md#concept.inventory.reservation) | |
```

- A **defining row** has the plain title of a concept this document defines and its definition: one
  sentence. The row is the definition's only home; the metadata record holds the concept's identity,
  title, explanation anchor and relations.
- An **import row** has a link to another Module's concept, addressed by that concept's identity,
  and an empty `Definition` cell. The row declares the `imports` relation. It never copies the
  definition, because copies drift; the link text is free, so renaming the concept breaks nothing.

The rows correspond one to one with the concepts the document defines and imports. A document with
neither has no table. A publisher MAY show imported definitions inline; that enrichment is a
[view](views.md) and never written into the file.

Each definition is written once, in its owner's table. A change to it rewrites no document of an
importer; the importer's context still changes, because the defining document is in it.

## Requirements

In an `implementation` document, a requirement is a level-2 to level-5 ATX heading
`req.<identity> — Title`, followed by its statement. A spaced en dash or hyphen is accepted.

```markdown
### req.checkout.single-order — One order per submission

Checkout SHALL create at most one order for a successfully admitted request.
```

The first paragraph is one sentence containing uppercase `SHALL` or `SHALL NOT` exactly once. The
section ends at the next heading of any level and contains no nested heading. Later paragraphs,
lists and fences explain the statement; a list item beginning with a requirement identity is
invalid.

## Scenarios

In an `implementation` document, a scenario is a level-2 to level-5 ATX heading
`scenario.<identity> — Title`, followed by its steps.

```markdown
### scenario.checkout.submit — Successful checkout

- GIVEN a customer has a valid basket and delivery details
- WHEN the customer submits it
- THEN Checkout creates one order
- AND returns its identifier
- BUT does not charge the payment method twice
```

Every list item in the section is a step beginning with `GIVEN`, `WHEN`, `THEN`, `AND` or `BUT` and
a space. The first step is `GIVEN` or `WHEN`; at least one `WHEN` and one `THEN` are required.
`AND` and `BUT` continue the preceding kind, and the sequence never returns to an earlier kind. The
section ends at the next heading of any level and has no nested heading. Prose may explain the
situation.

## Canonical contracts

In an `implementation` document, a `concorde-contract` JSON fence defines exactly `id`, `version`,
`schema`, `semantics`, `example`. The version is a positive integer, `semantics` is nonempty, and
the example satisfies the schema. Schema references MUST NOT load Spec documents or remote
resources. Publishers expose the contract identity as an anchor at the fence.

No role or peer appears in a definition; those belong to `participates`. A behaviour or schema
change increments the version, and every participant is reconciled in the same change. Editorial
changes need no version increment.

## Diagrams

Diagrams in reading are D2 blocks. A `d2` block is either a **checked diagram**, written in the
semantic subset and allowed only in `module` reading, or marked `d2 illustrative`. A block in any
other diagram language, such as Mermaid, is an error. The rules are in [Views](views.md).

## Links

Ordinary Markdown links navigate to readable definitions. A stable-identity fragment MUST name an
actual definition in the addressed reading document; other fragments use the renderer's slug rules.
A link never adds a document to context.

## Evidence declarations

A test declares the scenario identities it verifies in the test source, in a syntax documented by
the development tool. Tools read these declarations without executing tests and reject unknown
identities. Reading content MUST NOT contain that syntax outside fences, list test locations or
prescribe coverage declarations.

# Checks

Every check has a stable identity, a decidable statement and a severity. The identities listed
here are exactly those referenced by [`model.yaml`](model.yaml) and the other chapters.

Checks serve boundaries directly: a harness can only compute a trustworthy boundary from a
specification whose ownership, declaration sites and selections are structurally sound. They serve
understanding only indirectly, by keeping explanations attached to what they explain; no check
proves that an explanation is understandable.

Severities: **error** blocks structural conformance. **warning** is reported and does not block.

## Nodes

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.node.id` | Every node identity matches the grammar, is project-wide unique and, for requirements and scenarios, carries its prefix. | error |
| `CHK.node.type` | Every `defines` record has type `concept` or `realization`. | error |
| `CHK.node.owner` | Every node resolves to exactly one owning Module. | error |
| `CHK.node.title` | Titles are nonempty. Module titles are unique in the project; concept and realization titles are unique among the concepts and realizations of their owner. | error |
| `CHK.node.meaning` | A metadata-declared node's `meaning` is a local `#anchor` resolving to nonempty prose in the same document. | error |
| `CHK.node.explained` | An anchor group's prose is not empty and not only links, headings or fences. | warning |
| `CHK.concept.definition` | Each concept has exactly one defining row in its document's Terminology table, whose definition is one nonempty sentence. | error |
| `CHK.concept.retired` | `retired`, when present, has a nonempty `reason`; only a retired concept is the source of `supersedes`. | error |
| `CHK.requirement.statement` | The first paragraph is one sentence containing `SHALL` or `SHALL NOT` exactly once; the section has no nested heading. | error |
| `CHK.scenario.steps` | Every list item is a step; the grammar of [Format](format.md) holds. | error |
| `CHK.contract.fence` | The fence has exactly the five fields, a positive version, nonempty semantics, an offline schema and an example that satisfies it. | error |

## Documents

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.document.pair` | Both members exist and agree with the owner's `owns` on identity and owner; `role` is declared. | error |
| `CHK.document.path` | Paths are canonical project-relative POSIX, with no alias, traversal or symlink. | error |
| `CHK.document.role` | `role` is exactly `module` or `implementation`, explicitly declared. | error |
| `CHK.document.schema` | Metadata is `schema_version` 3 with the required fields and no unknown keys outside `extensions`. | error |
| `CHK.document.entry` | Each Module owns exactly one `module`-role document whose reading path ends in `module.md`; its metadata, and no other, has the `module` block, whose `owns` includes the entry. | error |
| `CHK.document.sections` | An entry has the level-2 sections Purpose, Terminology, Usage, Design and Relationships, each exactly once, in any order. | error |
| `CHK.document.topic-terminology` | A `module`-role topic that defines or imports a concept has `## Terminology` as its first level-2 section. | error |
| `CHK.document.prose` | Purpose is plain prose; Usage, Design and Relationships are not only links, headings or diagrams. | error |
| `CHK.terminology.rows` | A Terminology section has at most one table, with columns `Term` and `Definition`, whose rows correspond one to one with the concepts the document defines and imports. | error |
| `CHK.terminology.import-row` | An import row links to a concept anchor of another document by identity, and its `Definition` cell is empty. | error |

## Relations

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.relation.type` | Every relation has a registered type. | error |
| `CHK.relation.endpoints` | Source and target resolve and have permitted types. | error |
| `CHK.relation.site` | Every relation is declared at its site; a metadata relation's source is defined by that document, or is its owning Module for `relates`. | error |
| `CHK.relation.meaning` | A Module relation's `meaning` is a local anchor into the entry, or a qualified anchor into another document the source Module owns, resolving to nonempty prose. | error |
| `CHK.registry.mirror` | The registry has exactly one record per Module, with the entry's path and every field of its `module` block, equal to that block. | error |
| `CHK.owns.unique` | Each document is owned exactly once. | error |
| `CHK.defines.once` | Each node has exactly one defining document. | error |
| `CHK.defines.role` | Requirements, scenarios and contracts are defined only in `implementation` documents; concepts only in `module` documents. | error |
| `CHK.contains.acyclic` | Composition is acyclic. | error |
| `CHK.contains.single-parent` | A Module has at most one parent. | error |
| `CHK.contains.root` | Exactly one Module has no parent. | warning |
| `CHK.uses.no-self` | A Module does not use itself. | error |
| `CHK.uses.unique` | A Module uses each provider at most once. | error |
| `CHK.relies-on.owned` | Every identity in `relies_on` names a requirement, scenario, contract or concept owned by the relation's target. | error |
| `CHK.relies-on.linked` | When `relies_on` is present, every stable-identity link from the relation's `meaning` section to a node of the target names a listed node. | error |
| `CHK.includes.no-self` | A Module does not include itself or a document it owns. | error |
| `CHK.includes.unique` | No duplicate `(kind, target)` pairs. | error |
| `CHK.includes.reason` | Each `includes` has a nonempty `reason`. | error |
| `CHK.includes.redundant` | A spec inclusion whose documents are all already selected by `owns`, `contains`, `uses` or another inclusion is reported. | warning |
| `CHK.external.exists` | External material exists at the declared path and is tracked by the project's version control. | error |
| `CHK.external.no-overlap` | External paths overlap no document member and no realization entry. | error |
| `CHK.binds.exists` | Non-pending entries exist; exact entries are files and `/` entries are directories. | error |
| `CHK.binds.disjoint` | No two realizations in one Module list the same entry. | error |
| `CHK.binds.no-spec` | No document member, generated output or control record is bound; a bound directory contains no document member. | error |
| `CHK.binds.pending-subset` | `pending` is a subset of `entries`, and pending entries do not exist. | error |
| `CHK.binds.unbound` | Every version-controlled file is bound by some Module, unless it is a document member, generated output, external material or a control record such as the project registry and configuration. | error |
| `CHK.imports.foreign` | An imported concept is owned by a Module other than the importer's owner. | error |
| `CHK.imports.owner` | An imported concept's owner is a Module the importer uses, an ancestor of the importer, or a descendant of it. | warning |
| `CHK.narrows.acyclic` | `narrows` never relates a concept to itself, directly or through other `narrows`. | error |
| `CHK.contrasts.required` | Two nodes of different owners whose titles normalize equal have a `contrasts` between them. | error |
| `CHK.contrasts.once` | At most one `contrasts` is declared per unordered pair, and it has a nonempty `reason`. | error |
| `CHK.relates.source` | A `relates` source is defined by the declaring document or is its owning Module. | error |
| `CHK.relates.verb` | `verb` is nonempty; `(source, verb, target)` is unique. | error |
| `CHK.participates.version` | The contract exists and the declared version is its current version. | error |
| `CHK.participates.complementary` | Internal peers declare complementary roles for the same contract and version and name each other. | error |
| `CHK.participates.unique` | `(contract, peer, role)` is unique per Module. | error |
| `CHK.verifies.resolves` | Every verified scenario identity exists. | error |
| `CHK.evidence.no-spec-coverage` | Reading content contains no test-declaration syntax outside fences. | error |

**Name normalization** for `CHK.contrasts.required`: Unicode NFKC, case folding, and every run of
whitespace, hyphens and underscores treated as one space, trimmed. The compared nodes are concepts
and Modules; a concept is not compared with its own Module.

## Views

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.view.marked` | Every diagram in reading is a `d2` block; a checked one lies in `module` reading, and every other is marked `illustrative`. A Mermaid block is an error. | error |
| `CHK.view.subset` | A checked diagram uses only the semantic subset of D2. | error |
| `CHK.view.nodes` | Every shape of a checked diagram resolves to exactly one node, Module or, inside a realization, bound file. | error |
| `CHK.view.nesting` | Every nesting of a checked diagram matches a declared `contains`, the ownership of a node or the binding of a file. | error |
| `CHK.view.edges` | Every edge of a checked diagram matches a declared relation in its direction: an unlabelled edge between two Modules a `uses`, and a labelled edge a `relates`; an edge touching a node is labelled and no edge touches a file. | error |

## Reconciliation

| Identity | Statement | Severity |
| --- | --- | --- |
| `CHK.context.reconciled` | For every Module M and every `q ∈ Requires(M)`, `satisfied(q, Spec(M))` holds. | error |

## Limits of the checks

These checks are weaker than the obligations they serve:

| Check | What it does not establish |
| --- | --- |
| `CHK.relies-on.linked` | That `relies_on` lists a relied-upon promise the explanation never links to. |
| `CHK.relation.meaning` | That a parent's or consumer's explanation of a collaboration is adequate. |
| `CHK.node.explained` | That prose explains its node; it detects empty regions only. |
| `CHK.contrasts.required` | Collisions that normalization misses. Unrelated same-named nodes also trigger it; declaring the `contrasts` with its reason is then the correct answer, not an escape. |
| `CHK.view.edges` | That a drawn label describes the declared relation accurately. |
| `CHK.participates.version` | That the participant behaves as the contract says; that is implementation conformance. |

Not checked at all: whether a requirement is true of the implementation, whether reading is
sufficient for its reader, whether a scenario is worth having, and whether an illustrative block is
accurate.

## Tool obligations

These are requirements on tools rather than checks of declarations:

- Context selection is one level and never follows a selected Module's own relations.
- Documents are registered, never discovered from the filesystem or links.
- Coverage is read from test declarations without executing tests.
- Derived views are never written into reading files.
- A harness keeps every task boundary within the composition rules of [Boundaries](boundaries.md):
  writes only within write sets of bound Modules, write implies read, reads only within their read
  sets, and task material adds no source.

# Views

A view is any rendering of the model: a diagram, a terminology table, an index, a navigation tree,
a graph export, a documentation site. Views serve understanding: they are how most humans meet the
specification. Axiom A6 governs all of them: **a view is derived or checked, and an unchecked
picture is marked as such**, so that what a human sees cannot contradict what a harness computes
boundaries from.

## Derived views

A publisher renders views from declared relations. The renderer chooses:

- **scope** — which Modules, nodes and relation types to show;
- **grouping** — nesting, layers and ordering;
- **layout and styling**.

The renderer MUST NOT choose which relations exist. An omitted node or edge is a scope decision and
is not by itself a missing contract; an added edge is invalid output. Rendered views state their
scope and the relation types they display, so a reader knows what the absence of an edge means.

Derived views are rendered at publication or delivery time and are never written into reading
files. A publisher MAY enrich a written table, for example by showing an imported term's
definition next to its link; the enrichment is a view.

## Checked diagrams

A document draws structure in [D2](https://github.com/d2lang/d2). A `d2` block that is not marked
`illustrative` is a **checked diagram**: it states only what is drawn, what nests in what and what
points at what, and it may only assert what is declared. How the diagram looks (shapes, colours,
line styles, layout, direction) is chosen by the publisher from what each shape resolves to, never
written in reading. A checked diagram appears only in `module` reading.

**The semantic subset.** A checked diagram consists of:

- **shapes**, written `key` or `key: Label`, where a key may be quoted and the label is the text
  that resolves;
- **nesting**, written as a shape followed by a `{ ... }` block holding other statements;
- **edges**, written `a -> b` or `a -> b: label`, possibly chained, whose ends are keys or dotted
  key paths relative to the enclosing block;
- comments starting with `#`, and `;` between statements on one line.

Nothing else is allowed: no D2 keyword (such as `style`, `shape`, `class`, `direction`, `near`,
`label`, `icon`, `vars`), no imports, globs, filters, substitutions, block strings or arrays, and no
edge other than `->`.

**Shapes.** Every shape resolves by its label, or by its key when it has no label, to exactly one of:
a concept or realization of the owning Module, by title; a Module, by title; a node of another
Module, by the qualified form `Module title / node title`; or, only directly inside a realization
shape, a **file** of that realization: a bound entry path, or a suffix of exactly one bound entry
that begins after a `/`. An unresolved or ambiguous shape is an error. In a Module's own reading,
its own title always names the Module, even when one of its concepts shares that title; such a
concept is drawn with the qualified form, `Checkout / Checkout`.

**Nesting** asserts what it encloses:

| Outer shape | Inner shape | Asserts |
| --- | --- | --- |
| Module | Module | the outer Module `contains` the inner one |
| Module | concept, realization or qualified node | the outer Module owns the node |
| realization | file | the realization binds the file |

Any other nesting is an error. Containment is drawn only by nesting, never by an edge.

**Edges** assert a declared relation in the drawn direction:

- An unlabelled edge between two Modules asserts a `uses`: the plain arrow is the dependency.
- A labelled edge asserts a `relates` between its ends, and its label SHOULD be the relation's
  `verb`. An edge that touches a concept, realization or qualified node always carries a label.
- A file shape has no edges; it asserts only its binding.

A checked diagram need not show every declared relation; like a derived view, its omissions are
scope decisions. The `Relationships` section of an entry SHOULD contain a checked diagram of the
principal collaboration, and a Module that binds files SHOULD draw the realizations that carry its
function with the files they bind, so a reader sees how the Module is built. Realizations that only
keep the repository running, such as project configuration, development tooling or test suites,
are left to prose: a diagram shows architecture, not an inventory of files.

````markdown
```d2
checkout: Checkout {
  service: Checkout service {
    "service.py"
  }
  record: Order record
  service -> record: saves
}
inventory: Inventory
checkout -> inventory
```
````

Here `Checkout` and `Inventory` resolve to Modules, `Checkout service` to a realization and
`Order record` to a concept of Checkout, and `service.py` to a file that Checkout service binds.
The picture asserts that Checkout owns both nodes, that the realization binds the file, that a
`relates` with verb `saves` connects them, and that Checkout `uses` Inventory.

Naming a shape in a view grants no context and transfers no ownership. The owner is visible in a
qualified label or in the enclosing Module, so a node of another Module cannot be mistaken for a
local one.

## Illustrative blocks

Explanation sometimes needs a picture that is not a relationship inventory: a flow over time, a
state sketch, a before/after comparison. Such a block is marked `illustrative` in its info string
and may use the whole D2 language:

````markdown
```d2 illustrative
shape: sequence_diagram
client: Client
checkout: Checkout
client -> checkout: submit
checkout -> client: order number
```
````

An `illustrative` block is excluded from the model, labelled non-normative by the publisher and not
checked against declarations. It carries no authority beyond the surrounding prose, and it MUST NOT
be the only place a collaboration is described: a load-bearing relationship is declared. Diagrams
in any other language are not part of reading; a Mermaid block is an error.

## Publication obligations

A publisher MUST expose every stable identity as an addressable anchor, keep links as links rather
than transclusion, and show one canonical definition per node with its owner rather than copies.

A rendered view grants no reader context and MUST NOT be offered as a substitute for a complete
document. The Protocol specifies readable meaning and identity preservation; it does not prescribe
pages, sidebars, themes, folding or interaction behaviour.
