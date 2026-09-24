# Module specifications

[Node types](model.md) and [Relations](relations.md) define what a specification declares.
[Format](format.md) defines how declarations are written. This chapter defines what the **reading
content** must explain, because no declaration establishes understanding.

This chapter serves understanding above all: it is what makes a structurally valid specification
worth reading.

A Module specifies one responsibility for consumers and implementers. It need not correspond to a
package, directory, service or process. Its purpose, behaviour, concepts and collaborations
establish its boundary; realization bindings locate its code and establish nothing about scope.

## Choosing Module boundaries

Draw Modules around responsibilities and axes of change: a capability, a use case, a boundary with
one collaborator. Things that change together SHOULD belong to one Module, and a Module SHOULD NOT
collect things only because they are the same kind of artifact, such as all scripts, all prompts or
all configuration.

This choice serves both purposes at once. A reader understands a responsibility, not a file type.
And because a task's boundary is built from Modules, a Module that matches how the project actually
changes yields boundaries that fit real tasks: a typical change needs one Module's write sets, not
slices of five.

A Module MAY be purely compositional, explaining how its children together fulfil a responsibility,
and MAY bind files of its own.

## The intended reader

Assume a reader with general software knowledge who does **not** know this project's implementation,
internal type names, execution library or history.

That reader must be able to explain, from the reading content alone: the problem the Module solves,
when to use it, a normal interaction and its result, the important stopping conditions, and why the
design supports the guarantees. If reaching that state requires reading source code, an unselected
document or a maintainer, the specification is incomplete regardless of how many checks pass.

This reader is the measure of the Protocol's first purpose: a human understands the project from
its specification without reading its code.

## Document roles

One Module specification has two roles of document, both reading content, both owned directly by
the Module.

- **Module documents** (`role: module`) — the `module.md` entry and explanatory topics. They explain
  the responsibility, correct use, design and collaborations. They MUST NOT become link indexes or
  independently maintained summaries with weaker promises.
- **Implementation documents** (`role: implementation`) — the precise requirements, scenarios and
  canonical contracts. They are specifications, not source code, plans or descriptions of incidental
  implementation.

Role separation is about meaning, not heading syntax. Exact private APIs, wire fields, byte
algorithms, persistence layouts, internal limits and executable topology belong to
`implementation` reading even when written as ordinary prose. Architecture, design reasons, actual
public entry points and any limit or hazard a consumer needs for correct use belong to `module`
reading. A topic is an explanation, never a second owner or a nested requirements container.

Write the design in the entry's Design section. A separate topic is warranted only when an
explanation is too long for the entry to stay readable; it then extends the entry and never repeats
it, so a reader never has to leave the entry to learn what the entry already should say.

## The entry

Every entry has the same five sections in the same order, so that every Module reads the same way
and a newcomer meets them in the order they need: what it is for, the words it uses, how to use
it, why it is built that way, and how it fits with the rest.

### Purpose

State what the Module is for, who relies on it, and where its promises stop, including relevant
non-goals. Short plain prose. A directory or package name establishes no responsibility.

### Terminology

List the words a reader needs before Usage and Design make sense, in the table defined by
[Format](format.md#terminology): one row per concept this document defines, with its one-sentence
definition, and one link-only row per concept it imports from another Module.

Deciding which concepts exist is substantive. Declare a concept for a domain word, a record, a
boundary actor or an external standard a reader must understand; not for a file, an identity or an
internal class. Decide who owns each word by who is entitled to change its meaning; see
[Node types](model.md#concept). When a word here could be confused with another Module's word or
with a Module's name, declare `contrasts`; when it conflicts with common usage outside the project,
state `external_conflict`.

Prose after the table may orient the reader, such as how the terms relate or which to learn first.

### Usage

Explain the audience, use conditions, prerequisites, the concepts involved and the actual entry
points. Follow a representative input through its result and effects before turning to errors,
repeat invocation, cancellation and compatibility.

Start with a coherent normal path. A reader MUST NOT have to assemble instructions from formal
statements. Include a concrete illustration wherever abstraction would otherwise hide a decision the
user has to make. An unsupported behaviour is identified as unsupported, never invented to fill a
template. A logical responsibility may participate in a collaboration without having any callable
entry point, and MUST NOT invent one.

Usage is canonical explanatory prose, not a second summary with weaker promises. Link to precise
definitions rather than restating them.

### Design

Explain why the decomposition, state, control and data flow, collaboration and failure containment
fulfil the guarantees. Connect each significant choice to a problem it prevents. A list of class or
function names in call order is not an explanation, and intended design is not evidence that code
conforms.

Record significant choices and required internal constraints, and distinguish them from incidental
current implementation and unresolved questions. Prefer linking to a guarantee over restating it as
a new obligation.

Concepts and realizations are explained here or in Usage, where understanding them matters.
Identity and bindings stay in metadata. Several nodes may share one coherent explanation with
distinct anchors, provided the prose explains all of them.

### Relationships

Explain the architecture: how the Module's concepts and realizations relate, and how it
collaborates with its children and providers.

- For every child and every provider, state its responsibility, when the collaboration applies, the
  canonical promises relied upon, and this Module's own duties and failure reactions. These
  explanations are what the `contains` and `uses` `meaning` anchors point to. A declared relation
  with a link and no explanation does not satisfy this.
- Declare the structural relationships a reader should see as `relates`, with a verb: the service
  *saves* the record, the operator *approves* the request.
- Draw the principal collaboration as a checked D2 diagram: the Module with its children and the
  providers it uses. A diagram shows architecture, not an inventory: draw the realizations that
  carry the Module's function with the files they bind, so a developer sees how it is built, and
  leave realizations that only keep the repository running, such as project configuration,
  development tooling or test suites, to prose. A checked diagram may only assert declared
  relations; a picture that shows something else is marked `illustrative`. See [Views](views.md).

Explain the conditions, invariants and reactions that a diagram cannot carry.

## Precise obligations

Define these only in `implementation` documents owned by the Module. Group headings may organize
definitions but never own them. Module documents explain the important guarantees and link to the
canonical definitions; a reader should not need to read every acceptance case to understand the
Module.

A **requirement** is one decidable Module-wide `SHALL` statement with a stable identity. A
**scenario** is one testable situation in `GIVEN`/`WHEN`/`THEN` steps. A situation-specific
guarantee belongs in that scenario's steps or explanation, not in a second requirement. Define each
obligation once and link to it; editorial organization MUST NOT weaken, duplicate or contradict it.

An **interface** is specified by a canonical contract plus readable behaviour and scenarios, not by
a schema alone. Inputs, outputs, effects, failures, compatibility and repeat behaviour MUST be
explained in selected readable context, never inferred from shape.

## Composition, dependency and inclusion

- `contains` states structural accountability. A parent explains how its children fulfil the
  responsibility it holds, and receives their Specs to do so. A Module has at most one parent and
  composition is acyclic.
- `uses` states reliance on a provider's promises, and gives the consumer the provider's Specs. It
  implies no ownership, deployment, directory nesting or shared source. Dependencies may cross
  hierarchy levels, and two Modules may use each other.
- `includes` states what else this Module reads, with a reason. It implies no ownership and no
  dependency.

When a Module relies on a few promises of a large provider, list them in the relation's
`relies_on` and link them from the explanation of the collaboration. The reader then receives the
provider's entry and exactly the documents defining those promises.

## Realization

A `realization` binds exact files or directory prefixes; see [Node types](model.md). Tests are
ordinary implementation files. A test declares the scenarios it verifies **in the test**; reading
content MUST NOT list verifying tests or prescribe coverage declarations. Missing coverage does not
cancel a promise, and a declared test is not proof of fulfilment.

## Completeness

The selected context makes every owned and selected document available with both members intact.
Its readable subset must supply the meaning the task needs.

A schema, a heading, a rendered table, a checked diagram or a correctly registered file set is not
proof of sufficient meaning. Honest drafts name their unknowns. Missing necessary meaning remains a
gap until an explicit change to the specification repairs it: source code, another Module's own selections and
publisher summaries cannot silently supply a missing contract.

# Module entry template

A starter for `module.md`. Satisfying this shape establishes nothing about meaning; see
[Module specifications](../module.md) for what each section must explain.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. The [required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Terminology

| Term | Definition |
| --- | --- |
| Example record | The durable record of one accepted request. |
| [Thing](../provider/module.md#concept.provider.thing) | |

[Optional prose orienting the reader among the terms.]

## Usage

[Audience, use conditions, prerequisites and actual entry points. Follow one representative input
through its result and effects. Then errors, repeat invocation, cancellation and compatibility.
Include a concrete illustration where abstraction would hide a user decision. Name unsupported
behaviour as unsupported.]

<a id="concept.example.record"></a>

[Explain the example record where understanding it matters.]

## Design

<a id="realization.example.service"></a>

[Why the decomposition, state, flow, collaboration and failure containment fulfil the guarantees.
Connect each significant choice to the problem it prevents. Distinguish significant choices from
incidental implementation and open questions.]

## Relationships

```d2
example: Example {
  service: Example service {
    "src/example/"
  }
  record: Example record
  service -> record: saves
}
provider: Provider
example.service -> provider: reserves stock through
example -> provider
```

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Explain the conditions and reactions a picture cannot
carry.]
````

The first Terminology row defines `concept.example.record`; the second is an import row, which
links to the provider's concept by identity and leaves the definition empty.

The diagram is checked. `Example` and `Provider` resolve to Module titles, `Example service` and
`Example record` to this Module's nodes, and `src/example/` to the entry the service binds. Nesting
asserts that Example owns both nodes and that the service binds its entry; the labelled edges match
the `relates` declarations below and the unlabelled edge between the two Modules matches the `uses`.
The look is the publisher's. A picture that should not be checked is marked `d2 illustrative`.

## Paired metadata

````json
{
  "schema_version": 3,
  "document": {
    "id": "document.example.module",
    "owner": "module.example",
    "role": "module"
  },
  "module": {
    "title": "Example",
    "owns": ["example/module.md"],
    "contains": [],
    "uses": [
      {"target": "module.provider", "meaning": "#uses-example-provider",
       "relies_on": ["concept.provider.thing"]}
    ],
    "includes": [],
    "participates": []
  },
  "defines": [
    {
      "id": "concept.example.record",
      "type": "concept",
      "title": "Example record",
      "meaning": "#concept.example.record"
    },
    {
      "id": "realization.example.service",
      "type": "realization",
      "title": "Example service",
      "meaning": "#realization.example.service",
      "entries": ["src/example/"]
    }
  ],
  "relations": [
    {"type": "relates", "source": "realization.example.service", "verb": "saves",
     "target": "concept.example.record"},
    {"type": "relates", "source": "realization.example.service",
     "verb": "reserves stock through", "target": "module.provider"}
  ]
}
````

The `uses` entry selects the provider's entry and the document defining `concept.provider.thing`,
which satisfies the context requirements of importing that concept and of relating to
`module.provider`. The `Provider` label in the diagram resolves because the provider Module's
title is `Provider`.

## Registry record

The project registry mirrors the `module` block and adds the entry path:

````json
{
  "id": "module.example",
  "title": "Example",
  "entry": "example/module.md",
  "owns": ["example/module.md"],
  "contains": [],
  "uses": [
    {"target": "module.provider", "meaning": "#uses-example-provider",
     "relies_on": ["concept.provider.thing"]}
  ],
  "includes": [],
  "participates": []
}
````

# Scenario fragment

A scenario belongs to the Module owning its defining document. It may describe boundary use or an
internal verification situation. It is not a separate Spec kind, document owner or context filter.

Define it only in an `implementation` document, never in `module.md` or a `module`-role topic.
Register the reading path and write its paired metadata with `schema_version: 3`, the owner's
identity and `document.role: implementation`. The [required format](../format.md) applies.

````markdown
### scenario.example.situation — [Scenario title]

- GIVEN [the precondition or state]
- AND [another precondition]
- WHEN [the trigger]
- THEN [the promised outcome]
- AND [another outcome]
- BUT [an outcome that explicitly must not occur]

[Explain relevant limits, the triggering interface or unresolved facts in ordinary prose.]
````

Write separate scenarios for situations whose successful, failed, repeated or concurrent outcomes
differ. Put a situation's guarantees in its own steps or explanation; define a Module-wide
obligation once as a requirement and link to it.

Identities stay stable across title and path changes. A test names the scenario identity **in the
test source**; reading content never lists verifying tests. Publication exposes the identity as an
anchor.

Querying a scenario selects its owner's entire context, including both members of every owned and
selected document. It never trims to this fragment, and never selects the consumer that happened to
read it.
