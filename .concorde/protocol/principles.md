# Spec Protocol principles

Concorde Spec Protocol 16.3.0 defines:

- How a project describes itself as a set of Modules.
- What each Module promises.
- How the Modules and their files relate.

The Protocol applies to project Specs, including those of software implementing the Protocol.
The standard's own chapters need not describe themselves as Modules.

## Two purposes

The Protocol exists for two purposes. Every rule in it serves at least one of them. Each chapter
says how its rules do.

1. **Understanding.** A human grasps the backbone of the project quickly from its specification:
   - Its parts.
   - What each is for.
   - How they fit together.
   - How the main flows run.

   The ultimate goal is that a human never needs to read the code to understand the project.
   The specification is enough.
2. **Boundaries.** From the specification, a harness running an AI task can derive exactly what
   the task may read and what it may write. Different tasks need different boundaries. The
   Protocol therefore defines the sets that boundaries are composed from and the task types
   that compose them.

The two support each other. Only if what lies inside it is understandable is a boundary useful.
A Module that a human can understand as one responsibility is also the natural unit of a task.

Four failures undermine these purposes. The rules of the Protocol are designed against them:

1. **Inferred promises.** A reader concludes that something is promised because one of these
   suggested it:
   - A file.
   - A directory.
   - A name.
   - A link.
   - An adjacent paragraph.

   Nothing promised it.
2. **Meaning drift.** The same word denotes different things in different documents, silently.
3. **Authority creep.** Permission to read something becomes permission to change it, or a
   relationship becomes an execution grant.
4. **Fabricated evidence.** Coverage or conformance is claimed by the promise itself rather than by
   anything that ran.

## The model at a glance

A project's specification is **one graph**. Its nodes are the things the specification declares.
Its edges are the relations between them. Everything else in the Protocol is either how the graph
is written down, or something computed from it.

```d2 illustrative
direction: right
parent: Module {
  m: Module {
    d: Document {
      rz: Realization {
        f: Implementation files {shape: cylinder}
      }
      rs: Requirement / Scenario
      k: Contract
    }
  }
}
glossary: Glossary {
  c: Concept
}
provider: Module
t: Test file {shape: cylinder}
parent.m -> provider: uses / includes
parent.m.d -> glossary.c: mentions
glossary.c -> parent.m: owned by
parent.m -> parent.m.d.k: participates
t -> parent.m.d.rs: verifies
```

Nesting shows composition:

- A Module contains Modules.
- A Module owns documents.
- A document defines nodes.
- A realization binds files.

The project's one glossary declares every concept. Each concept names the Module that owns it.

**Nodes.** Seven types, defined in [Node types](model.md):

| Node | What it is |
| --- | --- |
| Module | One responsibility. The unit of ownership, of context and of task boundaries |
| Document | A Markdown reading file paired with its JSON metadata; the unit a Module owns |
| Concept | A named meaning a reader would get wrong without its definition, shared by more than one Module; its title is a term, declared in the glossary |
| Realization | A binding of implementation files to the Module |
| Requirement | One Module-wide `SHALL` obligation |
| Scenario | One concrete situation in `GIVEN`/`WHEN`/`THEN` steps |
| Contract | The versioned agreement for a shared interface |

**Edges.** Thirteen typed, directed relation types are defined in [Relations](relations.md):

- `owns`, `defines`, `contains` and `uses` state who is responsible for what.
- `includes` selects extra reading.
- `binds` joins the specification to code.
- `mentions`, `narrows`, `supersedes`, `contrasts` and `relates` connect meanings and architecture.
- `participates` and `verifies` tie contracts and tests to promises.

**Where the graph is written.** Every node and edge is declared exactly once. Concepts and
relations whose source is a concept are entries of the project's one **glossary**.
Each entry names its owning Module. Everything else is declared in a document owned by the Module
responsible for it. The declaration is in its reading, by a fixed syntax, or in its metadata.
A Module's own relations are in its entry's metadata. The project registry mirrors them for a
global view.

**What is computed from the graph.** Nothing below is declared. All of it is derived:

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
| Glossary | The project's one file of concept entries, each with its owner and one-sentence definition |

## Axioms

### A1. Every node has one identity, one owner and one explanation

Every declared node MUST have:

- A stable project-wide identity.
- Exactly one owning Module.
- Nonempty explanatory prose in a document its owner owns.

A declaration without an explanation is invalid, not merely incomplete. Identity survives title
and path changes.

*Serves both:* a reader always finds the explanation. A harness always knows whose write set a
node lies in.

### A2. Every relation is typed, directional and declared exactly once

A relation MUST have:

- A registered type.
- An explicit source and target.
- One declaration site fixed by its type.

The same fact MUST NOT be declarable in two places. The only permitted copy is a mirror the
Protocol names, the project registry. Its equality with the declarations is checked.
Except for a **term link**, the following MUST NOT create a relation:

- A filename.
- A path.
- A title.
- A prose sentence.
- An unchecked diagram.
- A directory neighbourhood.
- A link.

A term link is a link to a glossary entry, which is the declaration of `mentions`.

*Serves both:* nothing is promised by accident. Boundaries depend only on declarations.

### A3. Reading, writing and proving stay separate

Read sets and write sets are derived from different declarations. Being able to read a document
never makes it writable. A provider's Specs are readable by its consumers.
They are writable only within the provider's own scope. Realization bindings put file **names**
in the read side.
Only through a task boundary do contents become readable or writable. Evidence is never produced
by specification content.

*Serves boundaries:* this is the rule against authority creep.

### A4. Every relation declares what context it grants and what it requires

A relation type MUST declare `context_grants` and `context_requires`. For every Module, its
declared relations MUST grant everything its declared relations require. The reconciliation is a
structural check, defined in [Context](context.md).

*Serves both:* a reader of a Module has every definition its Spec relies on. A harness that
grants the Module's read set grants a self-sufficient one.

### A5. Evidence originates from what ran, never from what was promised

An evidence relation MUST be declared by the artifact that executes, not by the specification
that the artifact verifies. A specification MUST NOT declare its own coverage.

*Serves both:* a reader can trust that coverage was not merely claimed. Coverage cannot be
claimed from inside the write set of the Module whose promises it covers.

### A6. Views are derived or checked

A published diagram, index or navigation tree is derived from declared relations. A diagram written
in reading is either **checked** or **illustrative**. A checked one asserts only declared
relations. An illustrative one is explicitly marked and excluded from the model.
See [Views](views.md).

*Serves understanding:* pictures a human relies on cannot silently diverge from the model.

### A7. No inference, no recursion

The model is assertional. Every check operates on declared relations only. Unless its type says
so, no relation is transitive, symmetric or invertible. Derived indexes are never a source of
obligations. Document selection is one level and never recursive. The only closure is over the
glossary. A selected definition brings the definitions it links. This adds sentences, never
documents.

*Serves boundaries:* every set is computable. Every member is attributable to a declaration.

## Conformance

A conformance claim identifies its Protocol version. It distinguishes three claims that cannot
substitute for one another:

- **Structural conformance.** Identities, ownership, pairing, declaration sites, cardinalities,
  checked views and the context reconciliation all hold. This is machine-decidable.
  See [Checks](checks.md). It is what makes boundaries computable.
- **Semantic sufficiency.** The readable content explains the following to the intended reader:
  - The responsibility.
  - Its correct use.
  - Its design.
  - Its obligations.

  The Modules together form an architecture a reader can understand and a task can rely on.
  This is what makes the specification understandable. It is not machine-decidable.
  It is judged against the criteria of [Evaluating a Spec](evaluation.md).
- **Implementation conformance.** The realization satisfies the requirements and scenarios. This is
  established by evidence, never by structure.

Passing structural checks MUST NOT be reported as either of the other two. Missing meaning is an
attributed gap. To repair it, a reader MUST NOT read outside its boundary or infer a promise from
source code. The one sanctioned route from code to specification is a `code-to-spec` task
(see [Boundaries](boundaries.md#task-types)). The task describes an existing realization under its
own rules. It leaves every doubtful intent as a reported gap.

## What the Protocol does not define

The Protocol does not define:

- Which task type a harness assigns to a piece of work and how it enforces the resulting boundary.
- Docsite pages, navigation, themes and interaction.
- The serialization and location of the project registry.
- Tool configuration.
- Worker wire formats.
- Context delivery.

These are separate agreements. A change in any of them is not a Protocol version change.

# Node types

This chapter defines every kind of thing a specification may declare. [Relations](relations.md)
defines how they may be connected. The machine-readable vocabulary of both is
[`model.yaml`](model.yaml). The decision procedures are in [Checks](checks.md).

Each node type exists because a human reader needs the thing it names explained, a harness needs
it to compute a boundary, or both. Each section says which.

The model has **seven node types** and three **value types**. Because the specification makes no
promise about a value type, it has:

- No identity.
- No owner.
- No explanation.

## Common obligations

| Field | Meaning |
| --- | --- |
| `id` | Stable, project-wide unique, matching `^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$` |
| `type` | One of the seven node types below |
| owner | Exactly one Module identity, derived from the defining document or declared for a document |
| explanation | Nonempty prose in a document the owner owns; where it lives depends on the node type |

An ID prefix does not establish ownership. Titles and paths may change without changing identity.
An explanation cannot be outsourced. It is never a URL or a path into another document.

Nodes are declared at one of three sites:

- A **concept** is an entry of the project [glossary](#the-glossary). The entry names its owner.
  It points to its explanation in a document that owner owns.
- A **realization** is a record in a document's metadata. The record points to its explanation
  with a local `meaning` anchor.
- **Reading-declared** nodes (`requirement`, `scenario`, `contract`) are located by reading syntax.
  Their defining section is their explanation.

A Module and the documents it owns are declared in the `module` block of its entry's metadata.
They are mirrored in the project registry.

## module

**What it is.** One cohesive software responsibility, and the unit of context selection.

**Understanding.** A reader learns the system as a set of responsibilities, each explained by one
owner, independent of how files happen to be arranged.

**Boundaries.** A Module is what a task is bound to. Its read sets and write sets are all computed
from it. Thus, "who promises this" and "what a task on it may read and write" have one answer that
survives file movement. Because a reader cannot detect meaning that was silently withheld, the
Protocol deliberately accepts over-inclusion in read sets.

**Fields.** The entry's `module` block declares `id` (the entry's owner) and `title`.
The registry mirrors these fields. Its owner is itself. Its explanation is its entry document.
The entry document opens with its purpose.

**Constraints.** A Module MUST own exactly one document whose role is `module` and whose reading
path ends in `module.md`. That document is its **entry**. A Module need not do any of these:

- Correspond to a package.
- Correspond to a directory.
- Correspond to a service.
- Correspond to a process.

Its realization may do any of these:

- Span physical files.
- Share physical files.
- Omit physical files.

A composite Module may bind no implementation of its own. A composite Module may also bind files,
such as end-to-end tests of its own promises.

## document

**What it is.** A reading Markdown file **paired** with its metadata file. The pair is one node.

**Understanding.** Prose and the declarations it justifies cannot be separated.
Thus, metadata never becomes a second, unreviewed specification.

**Boundaries.** The pair is the unit of:

- Owning the pair.
- Selecting the pair.
- Writing the pair.

A boundary always contains both members or neither.

**Fields.** `id`, `owner` and `role` are stated in the metadata and agree with the owner's `owns`.
`role` is exactly `module` or `implementation`, with no default. A document explains itself.
It has no separate explanation.

- `module` — the entry and explanatory topics cover:
  - The Module's responsibility.
  - The Module's correct use.
  - The Module's design.
  - The Module's collaborations.
- `implementation` — the precise requirements, scenarios and canonical contracts. These are
  specifications, not source code. They are reading content like any other document.

**Constraints.** Both members share:

- The same owner.
- The same identity.
- The same inclusion provenance.

Registering the reading path registers its exact companion. Role is document organization only.
Role MUST NOT act as any of these:

- An ownership level.
- A context filter.
- A separate Spec kind.

The two roles serve understanding. Explanation is not buried under acceptance cases.
Precise obligations are not diluted into prose.

## concept

**What it is.** One named meaning a reader would get wrong without its definition, shared by more
than one Module. A concept can be:

- A domain word.
- A boundary actor.
- An external standard.
- A participant in a collaboration.

Its title is the **term** the specification uses for it.

**Understanding.** Meaning is what crosses Module boundaries. A concept gives a word one owner and
one canonical sentence. The whole project shares one list of them, so a reader finds one meaning
per word everywhere. A tool checks these as declarations instead of prose conventions:

- Specializing a concept.
- Retiring a concept.
- Colliding concepts.

**Boundaries.** A reader receives the definition of every concept its documents link and of every
concept its declarations name, never the whole glossary.

See [Context](context.md#term-selection). The definition is one sentence.
The extended explanation lives in a document of the owner. It is read only through one of these:

- A `uses` of the owner.
- A `contains` of the owner.
- An `includes`.

`referenced-by` makes the impact of changing a definition computable.

**Fields.** One entry of the glossary:

| Field | Meaning |
| --- | --- |
| `id` | Identity; a concept identity begins `concept.` |
| `title` | The term, unique in the project under the normalization of `CHK.contrasts.required` |
| `owner` | The Module entitled to change the meaning |
| `definition` | One sentence: the canonical meaning, written once. It MAY link other concepts by term link |
| `explanation` | `<reading path>#<anchor>`: the extended explanation, in a `module` document the owner owns |
| `retired` | Optional object `{"reason": "..."}`; the term is kept only for migration readers |
| `external_conflict` | Optional prose naming a conflicting usage outside this project |

The entry also declares `narrows`, `supersedes`, `contrasts` and `relates` relations whose source
is the concept. See [Relations](relations.md#meaning).

**Which words are concepts.** A word earns a glossary entry only when both hold:

- **It is not common sense.** Its meaning in the project is narrower than, or different from,
  ordinary usage. Thus, a reader who takes the word in its ordinary sense would misread it.
- **It crosses a Module boundary.** A Module other than its owner uses it. The words of the Module
  that declares the glossary are the project's core terms and are exempt from this condition.

Any other word is written in its ordinary sense. When the owner needs it in a narrower sense, the
owner's own document explains it where it is first used.
Unless other Modules reason about them, these are not concepts:

- The name of an operation.
- The name of a command.
- The name of a rule.
- The name of a component.
- A record whose shape a contract already gives.

`CHK.concept.local` reports a concept no other Module uses. No check decides whether a word is
common sense.

**Constraints.** A concept MUST NOT bind implementation. A concept MUST NOT stand for another
Module. A collaboration with another Module is a `uses` or `contains` relation.
A naming collision with another Module is a `contrasts` relation.

**Who owns a word.** Owning a concept means being entitled to change its meaning.
Its entry lies in the owner's write set. A change concerns every Module whose context holds the
definition. Ownership does not mean inventing the word or using it most. Every concept has exactly
one owner, chosen as follows:

- A word of a provider's own interface belongs to the provider.
- A word several Modules use with one meaning belongs to their nearest common ancestor in the
  composition tree, or to the root. When the owner is hard to name, move the word one level up.
- A project has one meaning per term. A word two Modules use differently needs two terms, such as
  `Session round` and `Headless round`. When a reader could confuse them, the terms are connected
  by `contrasts` or `narrows`.

## The glossary

**What it is.** The project's one JSON file of concept entries. It is not a node.
It has no owner. Each of its entries has one. A project declares it by the `glossary` field of its
root Module's `module` block. See [Required format](format.md#glossary).
A project without concepts needs no glossary.

**Understanding.** A reader looks words up in one place and never meets two definitions of one
term. A publisher renders the glossary as a page. Every term link leads there.

**Boundaries.** The glossary is the declaration site of every concept.
Thus, it is a shared file with entry-level ownership. A task bound to a Module may change the
entries that Module owns and add entries naming it as owner, and nothing else in the file.

See [Boundaries](boundaries.md#the-glossary). Definitions reach a reader one by one, as
[term selection](context.md#term-selection) chooses them, never as the whole file.

## realization

**What it is.** A declaration binding exact implementation paths or directory prefixes to this
Module.

**Understanding.** A reader learns where a promise is realized without inferring it from directory
names.

**Boundaries.** Its entries are the Module's `ImplementationScope`: the code a task bound to the
Module may be given to change. Only paths that exist are bound. A new file is created before it is
bound, or below a bound directory.

**Fields.** `id`, `type`, `title`, `meaning`, `entries` (exact project-relative paths, or directory
prefixes ending in `/`).

**Constraints.** Every entry MUST exist. Within a Module no two realizations list the same
entry. The longest covering entry determines which realization a file belongs to. A directory
entry binds present and future regular files below it under the tool's deterministic exclusion
rule. None of these may be bound:

- A document member.
- Generated output.
- A project-control record.

A bound directory MUST NOT contain a document member. Several Modules MAY bind the same path.
Each keeps its own promises. A change concerns all of them.

A realization records what exists, never an intent. A path that does not exist yet is not bound.
On the read side, listing a path grants its **name**. Contents are readable or writable only
through a task boundary. See [Boundaries](boundaries.md).

## requirement

**What it is.** One decidable, Module-wide obligation.

**Understanding.** A Module-wide promise is stated once, exactly, and survives the churn of the
situations that demonstrate it.

**Boundaries.** Its identity lets an exact promise be named in:

- Reviews of the promise.
- Tasks concerning the promise.
- Evidence of the promise.

**Constraints.** A heading in an `implementation` document declares a requirement.
The heading supplies `id` and title. The section is its explanation.
Its statement is one sentence containing `SHALL` or `SHALL NOT` exactly once.
Because two obligations under one identity make partial satisfaction undecidable, they MUST be
split.

## scenario

**What it is.** One concrete situation with:

- Preconditions of the situation.
- A trigger for the situation.
- A promised outcome of the situation.

**Understanding.** A concrete situation shows what a requirement means in practice.
The step grammar keeps a situation from quietly growing into a Module-wide obligation.

**Boundaries.** A requirement cannot be executed. A scenario is what tests declare they verify.
A task focused on a scenario is bound to the scenario's owner.
The task receives that owner's whole boundary.

**Constraints.** A heading in an `implementation` document declares a scenario.
The heading supplies `id` and title. When their outcomes differ in any of these ways, situations
get their own scenarios:

- Successful outcomes.
- Failed outcomes.
- Repeated outcomes.
- Concurrent outcomes.

A Module-wide obligation is defined once as a requirement and linked, never restated in steps.

## contract

**What it is.** The canonical, versioned agreement for a shared interface: an API, command,
protocol, event or file boundary.

**Understanding.** A shared interface is stated once, with one owner.
Every participant says which version it conforms to.

**Boundaries.** Participants are declared, so the impact of a contract change and the multi-Module
write boundary it needs are computable.

Without a version, a participant bound to an older meaning is undetectable.

**Fields.** `id`, `version` (positive integer), `schema`, `semantics`, `example`, all inside one
`concorde-contract` fence in an `implementation` document. Its explanation is `semantics` together
with the prose of the section containing the fence.

**Constraints.** The schema vocabulary is explicit and offline.
A schema MUST NOT load Spec documents or remote resources. The example MUST satisfy the schema.
A behaviour or schema change increments `version`. For that change, every participant is reconciled
atomically.

## Value types

These appear as relation targets or attributes but are not nodes.

| Value | Where it appears | Why it is not a node |
| --- | --- | --- |
| **path literal** | `binds`, external `includes`, `verifies` | A path carries no promise and has no owner in the Spec's sense. |
| **anchor** | `meaning` of realizations and reified relations, `explanation` of concepts | It has no identity of its own; only its declaration refers to it. |
| **digest** | context identity | It is a measurement of a source member, not a declared thing. |

# Relations

Relations serve both purposes of the Protocol. They are the explained connections a human reads
as architecture. They are also the only input from which a harness computes read and write sets.

Every relation type declares the same attribute set. A connection that cannot fill these fields is
not a relation (axiom A2). The vocabulary is closed: a project cannot register relation types of
its own. Tool data in a metadata `extensions` object never creates a relation.

| Attribute | Meaning |
| --- | --- |
| `source` / `target` | Permitted node or value types |
| `cardinality` | How many may exist, and any uniqueness rule |
| `declared_in` | The single site where it is declared: `entry` (the entry's `module` block), `metadata`, `reading`, `glossary` (a concept's entry) or `implementation-source` |
| `mirrored_in` | Where a checked copy is kept, if anywhere: only `registry` |
| `reified` | Attributes the relation itself carries |
| `symmetric` | Whether one declaration holds in both directions |
| `context_grants` | What it adds to the declaring Module's context, in the expression language of [Context](context.md) |
| `context_requires` | What MUST be in the declaring Module's context for the declaration to be honest |
| `checks` | Decidable rules, by identity, defined in [Checks](checks.md) |

**Where a relation is declared** follows one rule:

- A relation whose source is a Module is declared in the `module` block of that Module's entry.
- A relation whose source is a concept is declared in that concept's glossary entry.
- A relation whose source is a document or a node defined in a document is declared in that
  document, in its metadata or by reading syntax.

In every case, the declaration lies in the source Module's own `SpecScope`. A Module changes its
own collaborations and meanings without writing into another Module.

Module-level relations are also **mirrored** in the project registry.
The registry gives a project-wide view without opening every entry. The mirror is not a second
declaration site. The mirror MUST equal the entries. `CHK.registry.mirror` reports any difference.

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
this promise" has exactly one answer. The document lies in this Module's `SpecScope` and in no
other Module's write set. A Module always reads its own promises.

**Checks.** `CHK.owns.unique`, `CHK.document.entry`.

### `defines`

```yaml
source: document
target: [realization, requirement, scenario, contract]
cardinality: "0..N; a node is defined exactly once"
declared_in: metadata (realization) | reading (requirement, scenario, contract)
context_grants: none
context_requires: []
```

This document is the defining site of this node. Thus, its owner is the node's owner. The node's
explanation lives here. The target's node type fixes the declaration site.
Realizations are metadata records. Requirements, scenarios and contracts are located by their
reading syntax.

Concepts are not defined by documents. Each concept is an entry of the glossary.
The glossary names its owner and the document explaining it. See [Node types](model.md#concept).

**Checks.** `CHK.defines.once`, `CHK.defines.role`.
Requirements, scenarios and contracts are defined only in `implementation` documents.

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

The source Module is accountable for a responsibility that this child fulfils in part. Its
`meaning` explains how. Because the parent cannot explain the child's part without the child's
Specs, the parent receives them. `relies_on` narrows that grant exactly as for `uses`.

Composition is the top-down reading path through a project. A project SHOULD have exactly one
Module without a parent, its **root**, so that every Module is reachable from one entry. A root, or
any composite Module, MAY realize nothing itself. A root, or any composite Module, MAY bind files
of its own, such as end-to-end tests of its promises.

Whether a parent's explanation of its decomposition is adequate is a semantic judgement. The
decidable consequences are:

- Acyclicity.
- Single parenthood.
- A resolvable explanation.
- The grant.

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

The source Module relies on promises this provider makes. The `meaning` anchor states:

- The provider's responsibility.
- The circumstances in which the collaboration applies.
- The canonical promises relied upon.
- This Module's own duties and failure reactions.

Thus, a reader never meets a collaboration as a bare arrow. The consumer receives the provider's
Specs.

`relies_on` optionally lists the provider's promises this Module depends on: requirements,
scenarios, contracts and concepts, by identity. When `relies_on` is present, the consumer receives
only the provider's entry and the documents defining those nodes instead of every document the
provider owns. For a concept, that document is the one its glossary entry names as its
explanation.
The list is exact and checkable. The list turns the prose "promises relied upon" into links a
reader can follow. The list makes the impact of changing one promise precise.

`uses` is not ownership. The provider keeps one identity. None of its consumers owns the provider.
`uses` implies none of these:

- Deployment.
- Directory nesting.
- Shared source.

Mutual `uses` between two Modules is legitimate.

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

This Module reads something it neither owns nor depends on. `kind` is one of these:

- `module` (that Module's owned documents).
- `document` (one document).
- `external` (a directory or file of pinned third-party material).

Because removing an inclusion changes provenance and context identity, `reason` records why.

Specification inclusions and external inclusions are one relation because both answer the same
question, *what else does this Module read*. They differ only in the channel they fill.

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
channel: **names only**. On the write side the covered files form the Module's `ImplementationScope`.
This is the code a task bound to this Module may be given to change. See
[Boundaries](boundaries.md). A file bound by no Module is in no Module's scope.

**Checks.** `CHK.binds.exists`, `CHK.binds.disjoint`, `CHK.binds.no-spec`,
`CHK.binds.unbound`.

---

## Meaning

### `mentions`

```yaml
source: [document, concept]
target: concept
cardinality: "0..N; one per (source, target), however often the term is linked"
declared_in: reading (a term link) | glossary (a term link in the source's definition)
context_grants: term(target)
context_requires: []
```

This document, or this concept's definition, uses a term. The **term link** is an ordinary Markdown
link whose fragment is the concept's identity. Its path addresses the glossary. Because
copies drift, the term link navigates to the definition and never copies it. The link text is free,
so renaming a term breaks nothing.

The grant is the definition, not the owner's explanation. A reader that must understand how the
concept works needs the owner's documents, through `uses`, `contains` or `includes`.
Where a document first uses a term, the document SHOULD link it. `CHK.term.unlinked` reports a
document that uses a term and never links it.

**Checks.** `CHK.term.link`, `CHK.term.unlinked`.

### `narrows`

```yaml
source: concept
target: concept
cardinality: "0..N"
declared_in: glossary
context_grants: term(target)
context_requires: []
```

The source concept is a strictly more specific case of the target concept, so the two cannot drift
apart unnoticed.

**Checks.** `CHK.narrows.acyclic`.

### `supersedes`

```yaml
source: concept
target: concept
cardinality: "0..1 per source"
declared_in: glossary
context_grants: term(target)
context_requires: []
```

The source concept is retired. The target replaces it. A retired concept without a replacement
states why in its `retired.reason`.

**Checks.** `CHK.concept.retired`.

### `contrasts`

```yaml
source: concept
target: [concept, module]
cardinality: "0..N; at most one per unordered pair"
declared_in: glossary
reified: [reason]
symmetric: true
context_grants: none
context_requires: []
```

These two are easily confused. They are **not** the same thing. The `reason` states the difference,
so a reader who met only one of them is warned. The relation grants and requires no context.
The warning is the point. Forcing each side to read the other would couple unrelated Modules by
an accident of naming.

**Checks.** `CHK.contrasts.required`, `CHK.contrasts.once`.

### `relates`

```yaml
source: [concept, realization, module]
target: [concept, realization, module]
cardinality: "0..N; unique per (source, verb, target)"
declared_in: glossary (concept source) | metadata (realization or module source)
reified: [verb]
context_grants: term(target) for a concept target; otherwise none
context_requires: spec(definer(target)) for a realization or module target; otherwise none
```

A named architectural relationship has examples such as these:

- The realization *saves* the record.
- The actor *submits* the request.
- The Module *publishes* the event.

`verb` is free text, recommended as a verb phrase. The source determines where its relations are:

- A concept's relations are in its glossary entry.
- A realization's relations are in the metadata of the document defining it.
- A Module's relations are in the metadata of any document it owns.

The target may belong to any Module. A concept target brings its definition. A realization or
Module target requires its defining document, or a document of that Module, to be in context.

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

This Module provides or requires a shared contract. The attributes describe its participation:

- `version` is the contract version the participant conforms to.
- `role` is `provided` or `required`.
- `peer` names the internal Module on the other side or `external`.

Without the canonical definition, a participant cannot honestly claim conformance. Thus, the
defining document MUST be in context.

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

This test asserts that it verifies this scenario. Because coverage must originate from the
artifact that runs (axiom A5), this is the only relation declared outside specification content.
Reading content MUST NOT list verifying tests or prescribe coverage declarations. A declared test
is not proof of fulfilment. Missing coverage does not cancel a promise. Because tests declare
coverage, it cannot be claimed from inside the write set of the Module whose promises it covers.

**Checks.** `CHK.verifies.resolves`, `CHK.evidence.no-spec-coverage`.

---

## Derived indexes

These indexes are computed, never declared. They are evidence, navigation and impact aids.
They are never a source of obligations. They never widen a boundary.

| Derived | Computed from | Used for |
| --- | --- | --- |
| `selected-by` | inverting context and term selection | which Modules read a document or a definition, and so are concerned when it changes |
| `referenced-by` | inverting `relies_on`, `mentions`, `narrows`, `supersedes`, `relates` and `participates` | which declarations depend on a concept, node or contract |
| `implemented-by` | inverting `binds` | which Modules a file change concerns |
| `covered-by` | aggregating `verifies` | per-scenario coverage reports |

# Context

Context is the information explicitly made available to a reader of one Module. Knowing that a
document exists does not make it available. Neither does linking to it or naming a word it
explains. Only declared relations grant context. A term link grants only the term's definition.

This chapter defines the read side of the Protocol's boundary purpose:

- The four context channels.
- How a Module's context is selected.
- Term selection.
- The reconciliation of what relations grant against what they require.
- Context identity.

The write side is in [Boundaries](boundaries.md). The reconciliation guarantees that a Module's
context holds every definition its own Spec relies on. Because of this guarantee, the same
selection is also what a human reader of the Module needs open beside it.

## Four channels

| Channel | Granted by | Contains | Authority conveyed |
| --- | --- | --- | --- |
| `spec` | `owns`, `contains`, `uses`, `includes` of kind `module` or `document` | both members of each selected document | read only |
| `term` | the concepts a Module owns, `mentions`, `narrows`, `supersedes`, concept-targeted `relates` and `relies_on` | the glossary entries of the selected concepts | read only |
| `implementation` | `binds` | the **names** of bound paths | none |
| `external` | `includes` of kind `external` | pinned third-party material | read only |

The channels stay separate so that "may read this Module's promises" never implies "may read or
change its code". Knowing what a word means never implies reading how its owner works.
Whether a task receives implementation contents, read-only or writable, is part of its task
boundary. See [Boundaries](boundaries.md).

## Expressions

`context_grants` and `context_requires` in [`model.yaml`](model.yaml) use this expression language:

```text
spec(target)             the target document
spec(selection)          for a contains or uses with relies_on: the target's entry and the
                         documents defining the listed nodes; otherwise every document the
                         target Module owns
spec(definer(target))    the document that defines the target node; for a Module target,
                         that Module
term(target)             the glossary entry of the target concept
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
definer(concept c)       = the document c's entry names as its explanation
selection(includes document U) = { U }
```

Selection is one level. A selected Module contributes its owned documents, never the documents its
own relations select. None of the following adds a document:

- Parentage of the target.
- Dependency of the target.
- Inclusion of the target.
- Term links.
- Participation.
- Other Markdown links.
- Directory neighbourhood.
- Implementation bindings.

Because expansion is not recursive, cycles among Modules are harmless. Every member of a read set
is explained by the one declaration that selected it.

A scenario query resolves the scenario's owner and selects that owner's whole context. It never
trims to the scenario. A scenario query never selects the consumer that happened to read it.

Every selected document contributes **both** members whole. None of the following substitutes for
a complete document:

- An excerpt.
- A summary.
- A rendered view.
- A diagram export.

## Term selection

A reader needs the meaning of every term the documents it reads use, and nothing more. Term
selection gives it exactly those definitions:

```text
Seeds(M) = { c : owner(c) = M }
         ∪ { c : a document in Spec(M) mentions c }
         ∪ { c : c ∈ r.relies_on, r a contains or uses of M }
         ∪ { c : a relates declared in a document in Spec(M) targets c }
Terms(M) = the least set containing Seeds(M) and closed under
           c ∈ Terms(M) mentions, narrows, supersedes or relates to concept d  ⇒  d ∈ Terms(M)
TermContext(M) = { entry(c) : c ∈ Terms(M) }
```

Because the reader reads them too, every selected document counts, including the provider
documents a `uses` selects. Since a Module is entitled to change its own concepts, it always
receives their definitions.

The closure is the Protocol's only recursive selection. It runs inside the glossary.
The closure adds one sentence per concept and never adds a document. Thus, a reader whose
definitions use further terms understands them without widening what it reads.
`contrasts` adds nothing: the warning is in the entry that declares it.

Each selected entry is available whole: identity, title, owner, definition and explanation
reference.

The explanation it references stays a document of the owner. Only when `Spec(M)` selects it is the
explanation readable.

## Reconciliation

```text
Requires(M) = ⋃ { r.context_requires : r declared in the metadata or reading
                                        of a document M owns, including its entry }

CONFORMANCE:  ∀ q ∈ Requires(M) :  satisfied(q, Spec(M))
```

The following relations require the document that defines their target:

- A `relates` to a realization.
- A `relates` to a Module.
- A `participates`.

A Module that declares one without having that document in its context fails
`CHK.context.reconciled`. The repair is an explicit grant through one of these relations:

- A `uses` that selects the document.
- A `contains` that selects the document.
- An `includes` that states a reason.

Because relations that target a concept grant its definition themselves, they require nothing.

Because a node has exactly one defining document, the check is exact. A `uses` or `contains` that
narrows its grant with `relies_on` selects the documents defining the listed promises. Thus, the
narrowing is exact as well. No check establishes that the list names every promise the Module
actually relies on. `CHK.relies-on.linked` catches every one the explanation links to.

## Implementation context

```text
ImplementationContext(M) = ⋃ { entries of M's realizations }
ImplementationContext(scenario S) = ImplementationContext(owner(S))
ProjectImplementation = ⋃ { ImplementationContext(M) ∪ ExternalContext(M) : every Module M }
```

Exact entries and files below directory prefixes resolve under an explicit deterministic exclusion
rule. Every entry exists, so implementation context never names missing content.

Document members never belong to implementation context. When another Module binds the same file,
a change to it concerns that Module too. This adds neither that Module's Specs nor its code to this
reader's context. A Module with no bindings has an empty implementation context. This does not
prove it has no realization.

## External context

```text
ExternalContext(M) = ⋃ { readable files below M's external inclusions }
```

Only the selecting Module's own external inclusions count. A selected Module does not bring its
own. External material MUST be pinned by the project's version control so that its content is
identified by the checkout rather than by a second declared revision. For example, the material
can be a submodule at a fixed commit. A tool MAY exclude media and archives by a documented
deterministic rule.
An undeclared network fetch or an installed dependency's sources MUST NOT substitute for declared
material. External material supplies no promise absent from the Spec.

## Context identity

A resolved context is identified by its selected sources, its selected terms and the declarations
that selected them. This lets a harness tell whether anything inside a boundary changed since a
check.
Every source record carries:

- The document identity.
- The owner.
- The path.
- The member role (`reading` or `metadata`).
- An exact-byte SHA-256 digest.
- Every relation that selected it.

Every term record carries the concept's whole entry and every declaration that selected it.
External entries carry one tree digest each.

The identity changes, even when the set of paths is unchanged, on:

- Any byte change in either member of a selected document, including whitespace.
- Any change to a selected glossary entry, or a change of which entries are selected.
- A change to the declarations that selected the context, including removing a redundant inclusion.
- An ownership transfer.
- A change to pinned external material.

What a tool does with evidence bound to a previous identity is the tool's policy.

## Visibility

The resolved context is the exact visibility scope of a bounded reader. Every selected source and
every selected glossary entry is available whole. No unselected source or entry is visible. The
glossary file as a whole is not a source of any context. How a tool makes it available is not part
of the Protocol. A tool MAY also supply task material such as changes since a baseline. Such
material adds no source and replaces none. A reader that opened only some granted files still
received the complete context. Missing meaning is judged against the full granted scope.

## Gaps

A missing definition is a semantic gap even after structural resolution succeeds. Record:

- The needed promise.
- Its owner when known.
- The selected Module.
- The context identity.
- The blocked step.

Do not follow a selected Module's own relations or a prose link to repair it. An additional explicit
selection is a new context, not a retrospective claim that the previous one was complete.

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

# Required format

This is the structure and syntax part of [Spec writing guidelines](writing.md), covering the
machine-checkable rules. Read it with [Writing guidance](module.md), which explains the content
readers need and the judgments authors and reviewers must make. Where semantic requirements
accompany a format rule, they still apply.
The [Checks](checks.md) chapter states what tools establish.

This chapter defines how the [node types](model.md) and [relations](relations.md) are written.
The fixed declaration syntax serves boundaries: a tool computes every set without interpreting
prose. The reading itself has no fixed section structure. How an entry is organized is a writing
judgment, which [Writing guidance](module.md#the-entry) explains. Satisfying the syntax establishes
structural conformance only. It proves nothing about meaning.

## Documents

A registered document is a pair: an explicit project-relative Markdown reading path, and that same
path with `.json` appended. `checkout/module.md` and `checkout/module.md.json` are **one** document.

Reading files are nonempty UTF-8 Markdown. Metadata files are UTF-8 JSON with unique keys and no
non-JSON numeric constants. Paths use canonical project-relative POSIX spelling, with none of the
following:

- Absolute paths.
- Backslash characters.
- Empty components.
- Dot components.
- Traversal components.
- Control characters.
- Symlink aliases.

Both members always travel together:

- They have the same owner.
- They have the same identity.
- They have the same selection provenance.
- Both are in context.
- Both are in source digests.

Registering a reading path registers its exact companion. Tools MUST NOT discover documents from
the filesystem or by following Markdown links. This lets every boundary set be enumerated from
declarations alone.

## Module declaration

A Module declares itself and its Module-level relations in a `module` block of its **entry's**
metadata. This is the one declaration site of those relations. A task bound to the Module
reads and writes it as part of its own documents. The task learns who it relates to without any
global file.

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
       "relies_on": ["req.inventory.hold-expiry", "concept.reservation",
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
- `owns` lists reading paths. The list is nonempty. The list includes the entry itself.
- `contains` and `uses` entries have `target` and `meaning`. They optionally have a nonempty
  `relies_on` list of identities the target owns:
  - Requirement identities.
  - Scenario identities.
  - Contract identities.
  - Concept identities.

  Without `relies_on` the whole target is selected.
- `includes` entries have `kind`, `target` and a nonempty `reason`.
  `kind` is `module`, `document` or `external`. The `target` is one of these:
  - A Module identity.
  - A document identity.
  - A project-relative path.

  For a directory, the path ends in `/`.
- `participates` entries have `contract`, `version`, `role` (`provided` or `required`), `peer` (a
  Module identity or `external`) and `meaning`.
- `glossary` is optional. It appears only in the block of a Module without a parent.
  Its value is the project-relative path of the project's [glossary](#glossary), a `.json` file.
  At most one Module declares it.
- `contains`, `uses`, `includes` and `participates` are explicit arrays.
  These arrays MAY be empty.
- A relation `meaning` is a local `#anchor` into the entry, or a qualified `<reading path>#<anchor>`
  into another document the Module owns.

## Project registry

The project registry is the index of all Modules and a **mirror** of their declarations. It gives
a project-wide view without opening every Module. For example, a coordinating session uses this
view to plan work and set each task's boundary. It is not a declaration site.

```json
{
  "modules": [
    {"id": "module.checkout", "title": "Checkout", "entry": "checkout/module.md",
     "owns": ["checkout/module.md", "checkout/contracts.md"], "contains": [],
     "uses": [{"target": "module.inventory", "meaning": "#uses-inventory",
               "relies_on": ["req.inventory.hold-expiry", "concept.reservation",
                             "contract.inventory.reserve"]}],
     "includes": ["..."], "participates": ["..."]}
  ]
}
```

- Every Module has exactly one registry record. The record contains `id`, `title`, `entry`
  (the entry's reading path) and every field of its `module` block, equal to that block.
  Exactly when `glossary` appears in the block, it appears in the record.
- The registry lists which Modules exist. A tool MAY regenerate the mirrored fields from the
  entries. Adding or removing a Module is a deliberate registry change.
- A disagreement between the registry and an entry is a structural error
  (`CHK.registry.mirror`). Neither side silently wins. The change that caused it is reconciled.

The Protocol fixes the registry's content. Its serialization and location are a tool agreement.

## Metadata

```json
{
  "schema_version": 3,
  "document": {"id": "document.checkout.topic.holds", "owner": "module.checkout", "role": "module"},
  "defines": [
    {"id": "realization.checkout.service", "type": "realization", "title": "Checkout service",
     "meaning": "#realization.checkout.service", "entries": ["src/checkout/"]}
  ],
  "relations": [
    {"type": "relates", "source": "realization.checkout.service", "verb": "records",
     "target": "concept.hold"}
  ],
  "extensions": {}
}
```

- `schema_version` is the integer `3`.
- `document` has exactly `id`, `owner` and `role`, agreeing with the owner's `owns`. `role` is
  exactly `module` or `implementation` with no default. The entry `module.md` has role `module`.
- `module` is present exactly in the entry. See [Module declaration](#module-declaration).
- `defines` lists only `realization` records. Concepts are glossary entries. The reading syntax
  below locates these nodes:
  - Requirement nodes.
  - Scenario nodes.
  - Contract nodes.
- `relations` lists only `relates`, each naming as `source` a realization this document defines
  or the owning Module itself. A concept's relations are in its glossary entry.
  Term links declare `mentions`.
- `defines` and `relations` are explicit arrays. These arrays MAY be empty.
- If present, `extensions` is an object keyed by stable names holding tool data.
  A tool MUST define and validate the extension vocabulary it uses.
  An extension MUST NOT do any of the following:
  - Create a relation.
  - Change ownership or selection.
  - Hide essential meaning.

## Identities and anchors

The following identities are project-wide unique:

- Module identities.
- Document identities.
- Concept identities.
- Realization identities.
- Requirement identities.
- Scenario identities.
- Contract identities.

Each of these identities matches this pattern:

```text
^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$
```

Requirement identities begin `req.`. Scenario identities begin `scenario.`.
Concept identities begin `concept.`. Prefixes do not establish ownership.
Stable identities let links survive renames and moves.
They let boundaries, reviews and tests name exactly one thing.

A readable anchor is one of three forms:

- A **standalone** line of one or more `<a id="identity"></a>` before its explanation.
  The explanation extends to the next heading.
- An **opening** group of one or more `<a id="identity"></a>` appears at the very start of a
  paragraph or a list item's text. The group explains exactly that paragraph or list item.
  The paragraph ends at whichever of these comes next:
  - A blank line.
  - A heading.
  - A fence.

  The list item also ends at the next list item that is not indented deeper.
- An ATX heading carrying a trailing `{#identity}`.
  Its explanation extends to the next heading of the same or higher level.
  Requirement and scenario headings supply their identity directly.

A standalone or heading anchor also ends at the next anchor group. Anchors are unique within their
document and outside fences. An anchor anywhere else, such as inside a sentence or a table, is
not a readable anchor.

Several anchors in one group identify several nodes explained together by the same prose.
That prose MUST explain all of them. The region of an anchor is the text a tool attributes to its
nodes, for instance when it compares definitions between revisions. For an item in a list of short
explanations, an opening group is therefore the precise choice.

## Reading structure

An entry `module.md` has no required sections. The Protocol checks no heading of an entry.
The writer chooses the following for the entry:

- Its level-2 sections.
- Their titles.
- Their order.

[Writing
guidance](module.md#the-entry) recommends an order, starting with the Module's purpose. Honest
unknowns are stated explicitly.

A `module`-role topic begins with a short orienting introduction. A document holds no table of
term definitions. Definitions live in the glossary. A document links the terms it uses.

`module` documents MUST NOT contain any of the following:

- Requirement definitions.
- Scenario definitions.
- Canonical contract fences.

`implementation` documents contain those definitions. These documents MAY group them under
headings that carry no identity. Both roles are reading content. Role never filters context.

Regardless of the syntax used to write them, the following belong in `implementation` reading:

- Exact private APIs.
- Wire fields.
- Serialization rules.
- Internal limits.
- Executable topology.

Conceptual design and safe-use explanation stay in `module` reading.
A `module` document MUST NOT hide any of the following behind a link:

- Destructive defaults.
- Security limits.
- Known unfulfilled guarantees.

## Glossary

The glossary is one UTF-8 JSON file with unique keys, at the path the root Module's `glossary`
field declares:

```json
{
  "schema_version": 1,
  "concepts": [
    {"id": "concept.hold", "title": "Hold", "owner": "module.checkout",
     "definition": "Stock withheld from other customers until a submission succeeds or expires.",
     "explanation": "checkout/module.md#concept.hold",
     "narrows": ["concept.reservation"]},
    {"id": "concept.basket", "title": "Basket", "owner": "module.checkout",
     "definition": "The items a customer submits together as one [Hold](#concept.hold).",
     "explanation": "checkout/module.md#concept.basket",
     "contrasts": [{"target": "concept.wish-list",
                    "reason": "a wish list is saved for later; a basket is submitted immediately"}]}
  ]
}
```

- `schema_version` is the integer `1`. `concepts` is an array of entries sorted by `id`.
- An entry has exactly `id`, `title`, `owner`, `definition` and `explanation`, and optionally
  `retired`, `external_conflict`, `narrows`, `supersedes`, `contrasts` and `relates`.
- `owner` is a registered Module identity. `definition` is one sentence. A term link inside it
  addresses another entry by fragment alone, `#concept.<identity>`.
- `explanation` is `<reading path>#<anchor>`, naming a `module` document the owner owns and an
  anchor in it that resolves to nonempty prose.
- `narrows` is an array of concept identities. `supersedes` is one concept identity.
  `contrasts` is an array of `{target, reason}` with a concept or Module target.
  `relates` is an array of `{verb, target}` with a concept, realization or Module target.

## Term links

A **term link** is a Markdown link whose fragment is a concept identity. In reading, its path
addresses the glossary file, relative to the document like any other link:

```markdown
A [hold](../glossary.json#concept.hold) expires unless the submission succeeds.
```

A term link declares `mentions` of that concept. Its text is free. The following link the same term:

- A plural.
- An inflection.
- A different letter case.

A publisher sends every term link to the rendered glossary page.
Where a document first uses a term, the document SHOULD link it.
This lets a reader meet the definition before relying on it.

## Requirements

In an `implementation` document, a requirement is a level-2 to level-5 ATX heading
`req.<identity> — Title`, followed by its statement. A spaced en dash or hyphen is accepted.

```markdown
### req.checkout.single-order — One order per submission

Checkout SHALL create at most one order for a successfully admitted request.
```

The first paragraph is one sentence containing uppercase `SHALL` or `SHALL NOT` exactly once. The
section ends at the next heading of any level. It contains no nested heading.
Later paragraphs, lists and fences explain the statement.
A list item beginning with a requirement identity is invalid.

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
a space. The first step is `GIVEN` or `WHEN`. At least one `WHEN` and one `THEN` are required.
`AND` and `BUT` continue the preceding kind. The sequence never returns to an earlier kind.
The section ends at the next heading of any level. It has no nested heading. Prose may explain the
situation.

## Canonical contracts

In an `implementation` document, a `concorde-contract` JSON fence defines exactly `id`, `version`,
`schema`, `semantics`, `example`. The version is a positive integer. `semantics` is nonempty.
The example satisfies the schema. Schema references MUST NOT load Spec documents or remote
resources. Publishers expose the contract identity as an anchor at the fence.

A schema is checked offline. It uses only these JSON Schema keywords:

`$schema`, `$id`, `$defs`, `$ref` (only `#/$defs/<name>`), `title`, `description`, `examples`,
`default`, `type`, `properties`, `required`, `additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`,
`maxLength`, `pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and
`format`.

Any other keyword, such as `propertyNames` or `patternProperties`, is an error.
What it would express goes into `semantics`.

No role or peer appears in a definition. Those belong to `participates`.
When a behaviour or schema changes, the change increments the version.
Every participant is reconciled in the same change.

Editorial changes need no version increment.

## Diagrams

Diagrams in reading are D2 blocks. A `d2` block is either a **checked diagram**, written in the
semantic subset and allowed only in `module` reading, or marked `d2 illustrative`.

A block in any other diagram language, such as Mermaid, is an error. The rules are in
[Views](views.md).

## Links

Ordinary Markdown links navigate to readable definitions. A stable-identity fragment MUST name an
actual definition in the addressed reading document.
A concept fragment MUST address the glossary, as a [term link](#term-links).
Other fragments use the renderer's slug rules. A link never adds a document to context.
A term link adds the term's definition.

## Evidence declarations

A test declares the scenario identities it verifies in the test source, in a syntax documented by
the development tool. Tools read these declarations without executing tests.
Tools reject unknown identities. Reading content MUST NOT do any of the following:

- Contain that syntax outside fences.
- List test locations.
- Prescribe coverage declarations.

# Checks

Every check has a stable identity, a decidable statement and a strictness. The identities listed
here are exactly those referenced by [`model.yaml`](model.yaml) and the other chapters.

Checks serve boundaries directly. Only from a specification that satisfies these conditions can a
harness compute a trustworthy boundary:

- Its ownership is structurally sound.
- Its declaration sites are structurally sound.
- Its selections are structurally sound.

Checks serve understanding only indirectly, by keeping explanations attached to what they explain.
No check proves that an explanation is understandable.

Strictness: a violation of an **error** check blocks structural conformance. A violation of a
**warning** check is reported. A violation of a **warning** check does not block.

## Nodes

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.node.id` | Every node identity matches the grammar, is project-wide unique and, for requirements and scenarios, carries its prefix. | error |
| `CHK.node.type` | Every `defines` record has type `realization`. | error |
| `CHK.node.owner` | Every node resolves to exactly one owning Module. | error |
| `CHK.node.title` | Titles are nonempty. Module titles are unique in the project; concept titles are unique in the project under name normalization; realization titles are unique among the concepts and realizations of their owner. | error |
| `CHK.node.meaning` | A realization's `meaning` is a local `#anchor` resolving to nonempty prose in the same document; a concept's `explanation` names a `module` document its owner owns and an anchor there resolving to nonempty prose. | error |
| `CHK.node.explained` | An anchor group's prose is not empty and not only links, headings or fences. | warning |
| `CHK.concept.definition` | Each concept's `definition` is one nonempty sentence. | error |
| `CHK.concept.local` | A concept not owned by the Module that declares the glossary is used by another Module: a document another Module owns links it, another Module's `relies_on` or `relates` names it, or a concept another Module owns links or relates to it. | warning |
| `CHK.concept.retired` | `retired`, when present, has a nonempty `reason`; only a retired concept is the source of `supersedes`. | error |
| `CHK.requirement.statement` | The first paragraph is one sentence containing `SHALL` or `SHALL NOT` exactly once; the section has no nested heading. | error |
| `CHK.scenario.steps` | Every list item is a step; the grammar of [Format](format.md) holds. | error |
| `CHK.glossary.declared` | At most one Module declares a `glossary`, it has no parent, and the declared file exists; a project whose documents or declarations name a concept declares one. | error |
| `CHK.glossary.schema` | The glossary is `schema_version` 1 with a `concepts` array sorted by `id`, and every entry has the fields of [Format](format.md#glossary) and no others; its `owner` is a registered Module. | error |
| `CHK.contract.fence` | The fence has exactly the five fields, a positive version, nonempty semantics, an offline schema using only the keywords [Format](format.md#canonical-contracts) lists and an example that satisfies it. | error |

## Documents

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.document.pair` | Both members exist and agree with the owner's `owns` on identity and owner; `role` is declared. | error |
| `CHK.document.path` | Paths are canonical project-relative POSIX, with no alias, traversal or symlink. | error |
| `CHK.document.role` | `role` is exactly `module` or `implementation`, explicitly declared. | error |
| `CHK.document.schema` | Metadata is `schema_version` 3 with the required fields and no unknown keys outside `extensions`. | error |
| `CHK.document.entry` | Each Module owns exactly one `module`-role document whose reading path ends in `module.md`; its metadata, and no other, has the `module` block, whose `owns` includes the entry. | error |
| `CHK.term.link` | Every term link, in reading or in a definition, addresses the glossary and names a declared concept. | error |
| `CHK.term.unlinked` | A document whose reading uses a concept's title outside code, headings, links and anchors links that concept somewhere. A one-word title counts only as written, a longer title in any letter case, each also with a plural `s`. | warning |

## Relations

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.relation.type` | Every relation has a registered type. | error |
| `CHK.relation.endpoints` | Source and target resolve and have permitted types. | error |
| `CHK.relation.site` | Every relation is declared at its site: a metadata relation is a `relates` whose source is a realization that document defines or its owning Module; a concept's relations are in its glossary entry. | error |
| `CHK.relation.meaning` | A Module relation's `meaning` is a local anchor into the entry, or a qualified anchor into another document the source Module owns, resolving to nonempty prose. | error |
| `CHK.registry.mirror` | The registry has exactly one record per Module, with the entry's path and every field of its `module` block, equal to that block. | error |
| `CHK.owns.unique` | Each document is owned exactly once. | error |
| `CHK.defines.once` | Each node has exactly one defining document. | error |
| `CHK.defines.role` | Requirements, scenarios and contracts are defined only in `implementation` documents. | error |
| `CHK.contains.acyclic` | Composition is acyclic. | error |
| `CHK.contains.single-parent` | A Module has at most one parent. | error |
| `CHK.contains.root` | Exactly one Module has no parent. | warning |
| `CHK.uses.no-self` | A Module does not use itself. | error |
| `CHK.uses.unique` | A Module uses each provider at most once. | error |
| `CHK.relies-on.owned` | Every identity in `relies_on` names a requirement, scenario, contract or concept owned by the relation's target. | error |
| `CHK.relies-on.linked` | When `relies_on` is present, every stable-identity link from the relation's `meaning` section to a requirement, scenario or contract of the target names a listed node; a term link names a word and needs no listing. | error |
| `CHK.includes.no-self` | A Module does not include itself or a document it owns. | error |
| `CHK.includes.unique` | No duplicate `(kind, target)` pairs. | error |
| `CHK.includes.reason` | Each `includes` has a nonempty `reason`. | error |
| `CHK.includes.redundant` | A spec inclusion whose documents are all already selected by `owns`, `contains`, `uses` or another inclusion is reported. | warning |
| `CHK.external.exists` | External material exists at the declared path and is tracked by the project's version control. | error |
| `CHK.external.no-overlap` | External paths overlap no document member and no realization entry. | error |
| `CHK.binds.exists` | Every entry exists; exact entries are files and `/` entries are directories. | error |
| `CHK.binds.disjoint` | No two realizations in one Module list the same entry. | error |
| `CHK.binds.no-spec` | No document member, the glossary, generated output or control record is bound; a bound directory contains no document member. | error |
| `CHK.binds.installed` | No directory entry covers an installed file, which is bound only by its exact path. | error |
| `CHK.binds.unbound` | Every version-controlled file is bound by some Module, unless it is a document member, the glossary, generated output, external material or a control record such as the project registry and configuration. | error |
| `CHK.narrows.acyclic` | `narrows` never relates a concept to itself, directly or through other `narrows`. | error |
| `CHK.contrasts.required` | A concept and a Module other than its owner whose titles normalize equal have a `contrasts` between them. | error |
| `CHK.contrasts.once` | At most one `contrasts` is declared per unordered pair, and it has a nonempty `reason`. | error |
| `CHK.relates.source` | A `relates` source is the concept whose entry declares it, a realization the declaring document defines, or the declaring document's owning Module. | error |
| `CHK.relates.verb` | `verb` is nonempty; `(source, verb, target)` is unique. | error |
| `CHK.participates.version` | The contract exists and the declared version is its current version. | error |
| `CHK.participates.complementary` | Internal peers declare complementary roles for the same contract and version and name each other. | error |
| `CHK.participates.unique` | `(contract, peer, role)` is unique per Module. | error |
| `CHK.verifies.resolves` | Every verified scenario identity exists. | error |
| `CHK.evidence.no-spec-coverage` | Reading content contains no test-declaration syntax outside fences. | error |

**Name normalization** for `CHK.node.title` and `CHK.contrasts.required` applies these operations:

- Apply Unicode NFKC.
- Apply case folding.
- Treat every run of whitespace, hyphens and underscores as one space, trimmed.

`CHK.node.title` compares concepts with each other. `CHK.contrasts.required` compares concepts with
Modules, never a concept with its own Module.

## Views

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.view.marked` | Every diagram in reading is a `d2` block; a checked one lies in `module` reading, and every other is marked `illustrative`. A Mermaid block is an error. | error |
| `CHK.view.subset` | A checked diagram uses only the semantic subset of D2. | error |
| `CHK.view.nodes` | Every shape of a checked diagram resolves to exactly one node, Module or, inside a realization, bound file. | error |
| `CHK.view.nesting` | Every nesting of a checked diagram matches a declared `contains`, the ownership of a node or the binding of a file. | error |
| `CHK.view.edges` | Every edge of a checked diagram matches a declared relation in its direction: an unlabelled edge between two Modules a `uses`, and a labelled edge a `relates`; an edge touching a node is labelled and no edge touches a file. | error |

## Style

These checks measure the decidable part of [Sentence style](style.md) in the reading of every
document and in every concept definition. That chapter's
[What a program measures](style.md#what-a-program-measures) states this scope.

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.style.sentence-length` | No sentence of prose has more than 35 words, and no concept definition has more than 50 words. | warning |
| `CHK.style.semicolon` | No sentence of prose contains a semicolon. | warning |
| `CHK.style.one-obligation` | No sentence of prose contains more than one requirement keyword. | warning |

## Reconciliation

| Identity | Statement | Strictness |
| --- | --- | --- |
| `CHK.context.reconciled` | For every Module M and every `q ∈ Requires(M)`, `satisfied(q, Spec(M))` holds. | error |

## Limits of the checks

These checks are weaker than the obligations they serve:

| Check | What it does not establish |
| --- | --- |
| `CHK.relies-on.linked` | That `relies_on` lists a relied-upon promise the explanation never links to. |
| `CHK.term.unlinked` | That a term is linked where it is first used, or that a word matching a title is used in the term's sense; an ordinary word spelled like a one-word title in the same letter case is reported too, and linking or rephrasing it is the answer. |
| `CHK.concept.local` | That a concept's meaning departs from ordinary usage; a shared concept that is common sense is not reported, and a concept only its owner uses is reported however specific it is. |
| `CHK.relation.meaning` | That a parent's or consumer's explanation of a collaboration is adequate. |
| `CHK.node.explained` | That prose explains its node; it detects empty regions only. |
| `CHK.contrasts.required` | Collisions that normalization misses. Unrelated same-named nodes also trigger it; declaring the `contrasts` with its reason is then the correct answer, not an escape. |
| `CHK.view.edges` | That a drawn label describes the declared relation accurately. |
| `CHK.participates.version` | That the participant behaves as the contract says; that is implementation conformance. |
| `CHK.style.sentence-length` | That a sentence of 35 words or fewer, or a definition of 50 words or fewer, is short enough, or that a sentence carries one fact. |
| `CHK.style.one-obligation` | That a sentence with one keyword carries one obligation. A sentence that joins two obligations under one keyword is not reported. |

The checks do not check any of the following:

- Whether a requirement is true of the implementation.
- How an entry is organized.
- Whether reading is sufficient for its reader.
- Whether a scenario is worth having.
- Whether an illustrative block is accurate.

## Tool obligations

These are requirements on tools rather than checks of declarations:

- Context selection is one level. Context selection never follows a selected Module's own relations.
  Term selection closes over the glossary only.
- Documents are registered. Documents are never discovered from the filesystem or links.
- Coverage is read from test declarations without executing tests.
- Derived views are never written into reading files.
- A harness keeps every task boundary within the composition rules of [Boundaries](boundaries.md):
  - The harness writes only within write sets of bound Modules.
  - Write implies read.
  - The harness reads only within their read sets.
  - Task material adds no source.

# Views

A view is any rendering of the model:

- A diagram.
- The glossary page.
- An index.
- A navigation tree.
- A graph export.
- A documentation site.

Views serve understanding: they are how most humans meet the specification. Axiom A6 governs all of
them: **a view is derived or checked**. Axiom A6 also states that **an unchecked picture is marked
as such**. These rules ensure that what a human sees cannot contradict what a harness computes
boundaries from.

## Derived views

A publisher renders views from declared relations. The renderer chooses:

- **scope** — which Modules, nodes and relation types to show.
- **grouping** — nesting, layers and ordering.
- **layout and styling**.

The renderer MUST NOT choose which relations exist. An omitted node or edge is a scope decision.
It is not by itself a missing contract. An added edge is invalid output. Rendered views state their
scope and the relation types they display, so a reader knows what the absence of an edge means.

Derived views are rendered at publication or delivery time. They are never written into reading
files. A publisher renders the glossary as a page. The publisher sends every term link to its entry
there. A publisher MAY enrich reading, for example by showing a term's definition when a reader
points at its link. Another example is listing the terms a Module owns on its page. Every such
enrichment is a view.

## Checked diagrams

A document draws structure in [D2](https://github.com/d2lang/d2). A `d2` block that is not marked
`illustrative` is a **checked diagram**. It states only:

- What is drawn.
- What nests in what.
- What points at what.

A checked diagram may only assert what is declared. The publisher chooses how the diagram looks
from what each shape resolves to. This look, its shapes, colours, line styles, layout and direction, is
never written in reading. A checked diagram appears only in `module` reading.

**The semantic subset.** A checked diagram consists of:

- **shapes**, written `key` or `key: Label`. A key may be quoted. The label is the text that
  resolves.
- **nesting**, written as a shape followed by a `{ ... }` block holding other statements.
- **edges**, written `a -> b` or `a -> b: label`, possibly chained. Their ends are keys or dotted
  key paths relative to the enclosing block.
- Comments starting with `#`, and `;` between statements on one line.

Nothing else is allowed. No D2 keyword (such as `style`, `shape`, `class`, `direction`, `near`,
`label`, `icon`, `vars`) is allowed. Imports, globs, filters, substitutions, block strings and arrays
are not allowed. No edge other than `->` is allowed.

**Shapes.** When a shape has no label, it resolves by its key. Otherwise, it resolves by its label.
Every shape resolves to exactly one of:

- A concept or realization of the owning Module, by title.
- A Module, by title.
- A node of another Module, by the qualified form `Module title / node title`.
- Only directly inside a realization shape, a **file** of that realization.

That file is a bound entry path, or a suffix of exactly one bound entry that begins after a
`/`. An unresolved or ambiguous shape is an error. In a Module's own reading, its own title always
names the Module, even when one of its concepts shares that title. Such a concept is drawn with the
qualified form, `Checkout / Checkout`.

**Nesting** asserts what it encloses:

| Outer shape | Inner shape | Asserts |
| --- | --- | --- |
| Module | Module | the outer Module `contains` the inner one |
| Module | concept, realization or qualified node | the outer Module owns the node |
| realization | file | the realization binds the file |

Any other nesting is an error. Containment is drawn only by nesting, never by an edge.

**Edges** assert a declared relation in the drawn direction:

- An unlabelled edge between two Modules asserts a `uses`: the plain arrow is the dependency.
- A labelled edge asserts a `relates` between its ends. Its label SHOULD be the relation's
  `verb`. An edge that touches a concept, realization or qualified node always carries a label.
- A file shape has no edges. It asserts only its binding.

A checked diagram need not show every declared relation. Like a derived view, its omissions are
scope decisions. An entry draws its structure in as many diagrams as it needs. Each diagram answers
one question. Typically, it shows the inside or the outside. A typical inside diagram is one where
a Module whose function is carried by several realizations draws them with the files they bind
and the edges between them. A typical outside diagram shows the Module among the Modules it uses
and those that use it.

Whichever Module declares the relation, an edge may join any two shapes whose relation is declared.
Thus, the outside view may draw a consumer's `uses` of this Module or a `relates` from one of its
realizations to another Module. Realizations that only keep the repository running are left to
prose. Examples include project configuration, development tooling or test suites. A diagram shows
architecture, not an inventory of files. See [Writing
guidance](module.md#diagrams).

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

Here the names resolve as follows:

- `Checkout` and `Inventory` resolve to Modules.
- `Checkout service` resolves to a realization.
- `Order record` resolves to a concept of Checkout.
- `service.py` resolves to a file that Checkout service binds.

The picture asserts the following:

- Checkout owns both nodes.
- The realization binds the file.
- A `relates` with verb `saves` connects the nodes.
- Checkout `uses` Inventory.

Naming a shape in a view grants no context. It transfers no ownership. The owner is visible in a
qualified label or in the enclosing Module. Thus, a node of another Module cannot be mistaken for a
local one.

## Illustrative blocks

Explanation sometimes needs a picture that is not a relationship inventory:

- A workflow.
- A state sketch.
- A before/after comparison.

Such a block is marked `illustrative` in its info string. It may use the whole D2 language:

````markdown
```d2 illustrative
direction: right
customer: Customer {
  submit: Submit basket
  receive: Receive order number
}
checkout: Checkout {
  hold: Hold stock
  order: Create order
  hold -> order
}
customer.submit -> checkout.hold
checkout.order -> customer.receive
```
````

An `illustrative` block has these properties:

- It is excluded from the model.
- It is labelled non-normative by the publisher.
- It is not checked against declarations.

It carries no authority beyond the surrounding prose. An `illustrative` block MUST NOT be the only
place a collaboration is described. A load-bearing relationship is declared. Diagrams in any other
language are not part of reading. A Mermaid block is an error.

## Publication obligations

A publisher MUST do all of the following:

- Expose every stable identity as an addressable anchor.
- Keep links as links rather than transclusion.
- Show one canonical definition per node with its owner rather than copies.

A rendered view grants no reader context. A rendered view MUST NOT be offered as a substitute for a
complete document. The Protocol specifies readable meaning and identity preservation. It does not
prescribe pages, sidebars, themes, folding or interaction behaviour.
