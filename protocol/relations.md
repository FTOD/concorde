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
