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
