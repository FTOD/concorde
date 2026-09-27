# Spec writing guidelines

Use these guidelines to write and review a Module's Specs. They have two separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax: document
  pairs, declarations, metadata, identities, anchors, reading sections and precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader: responsibility, terminology, correct use, design, collaborations and meaningful diagrams.
  Applying it requires reader and editor judgment.

Both parts serve the Protocol's purposes of understanding and boundaries. Semantic writing
requirements still apply when structural checks pass. Mandatory terms retain their force in both
parts: **MUST** and **MUST NOT** state requirements and prohibitions, **SHOULD** allows departure
for an explained reason, and **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning. The
[Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify, choosing a lightweight workflow
for process progression or another view suited to the reader's question; see
[Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Review the content for semantic
sufficiency as well; evidence from the implementation establishes implementation conformance.
None of these substitutes for another; see [Conformance](principles.md#conformance).

# Required format

This is the structure and syntax part of [Spec writing guidelines](writing.md), covering the
machine-checkable rules. Read it with [Writing guidance](module.md), which explains the content
readers need and the judgments authors and reviewers must make. Semantic requirements still apply
where they accompany a format rule; the [Checks](checks.md) chapter states what tools establish.

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
- `owns` lists reading paths, is nonempty and includes the entry itself.
- `contains` and `uses` entries have `target` and `meaning`, and optionally a nonempty `relies_on`
  list of identities of requirements, scenarios, contracts and concepts the target owns. Without
  `relies_on` the whole target is selected.
- `includes` entries have `kind` (`module`, `document` or `external`), `target` (a Module identity,
  a document identity, or a project-relative path; a directory ends in `/`) and a nonempty `reason`.
- `participates` entries have `contract`, `version`, `role` (`provided` or `required`), `peer` (a
  Module identity or `external`) and `meaning`.
- `glossary` is optional and appears only in the block of a Module without a parent: the
  project-relative path of the project's [glossary](#glossary), a `.json` file. At most one Module
  declares it.
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
               "relies_on": ["req.inventory.hold-expiry", "concept.reservation",
                             "contract.inventory.reserve"]}],
     "includes": ["..."], "participates": ["..."]}
  ]
}
```

- Every Module has exactly one registry record: `id`, `title`, `entry` (the entry's reading path)
  and every field of its `module` block, equal to that block; `glossary` appears in the record
  exactly when it appears in the block.
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
    {"id": "realization.checkout.service", "type": "realization", "title": "Checkout service",
     "meaning": "#realization.checkout.service", "entries": ["src/checkout/"], "pending": []}
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
  exactly `module` or `implementation` with no default; the entry `module.md` has role `module`.
- `module` is present exactly in the entry; see [Module declaration](#module-declaration).
- `defines` lists only `realization` records. Concepts are glossary entries, and requirements,
  scenarios and contracts are located by their reading syntax below.
- `relations` lists only `relates`, each naming as `source` a realization this document defines
  or the owning Module itself. A concept's relations are in its glossary entry; `mentions` is
  declared by term links.
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

Requirement identities begin `req.`; scenario identities begin `scenario.`; concept identities begin
`concept.`. Prefixes do not establish ownership. Stable identities let links survive renames and
moves, and let boundaries, reviews and tests name exactly one thing.

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
Usage
Design
```

It MAY have further level-2 sections, but none titled `Relationships`: how the Module relates to its
children and to other Modules is part of Design. A level-1 title and brief navigation may precede
the first of them. Purpose is nonempty plain prose: no lists, tables, nested headings or fences.
Usage and Design contain explanatory prose, not only links, headings or diagrams. Honest unknowns
are stated explicitly.

A `module`-role topic begins with a short orienting introduction. A document holds no table of
term definitions: definitions live in the glossary, and a document links the terms it uses.

`module` documents MUST NOT contain requirement or scenario definitions or canonical contract
fences. `implementation` documents contain those definitions and MAY group them under headings
that carry no identity. Both roles are reading content; role never filters context.

Exact private APIs, wire fields, serialization rules, internal limits and executable topology belong
in `implementation` reading regardless of the syntax used to write them. Conceptual design and
safe-use explanation stay in `module` reading. A `module` document MUST NOT hide destructive
defaults, security limits or known unfulfilled guarantees behind a link.

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

- `schema_version` is the integer `1`; `concepts` is an array of entries sorted by `id`.
- An entry has exactly `id`, `title`, `owner`, `definition` and `explanation`, and optionally
  `retired`, `external_conflict`, `narrows`, `supersedes`, `contrasts` and `relates`.
- `owner` is a registered Module identity. `definition` is one sentence; a term link inside it
  addresses another entry by fragment alone, `#concept.<identity>`.
- `explanation` is `<reading path>#<anchor>`, naming a `module` document the owner owns and an
  anchor in it that resolves to nonempty prose.
- `narrows` is an array of concept identities; `supersedes` is one concept identity; `contrasts`
  is an array of `{target, reason}` with a concept or Module target; `relates` is an array of
  `{verb, target}` with a concept, realization or Module target.

## Term links

A **term link** is a Markdown link whose fragment is a concept identity. In reading, its path
addresses the glossary file, relative to the document like any other link:

```markdown
A [hold](../glossary.json#concept.hold) expires unless the submission succeeds.
```

A term link declares `mentions` of that concept. Its text is free: a plural, an inflection or a
different letter case links the same term. A publisher sends every term link to the rendered
glossary page. A document SHOULD link a term where it first uses it, so that a reader meets the
definition before relying on it.

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

A schema is checked offline and uses only these JSON Schema keywords: `$schema`, `$id`, `$defs`,
`$ref` (only `#/$defs/<name>`), `title`, `description`, `examples`, `default`, `type`, `properties`,
`required`, `additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`,
`maxLength`, `pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and
`format`. Any other keyword, such as `propertyNames` or `patternProperties`, is an error; what it
would express goes into `semantics`.

No role or peer appears in a definition; those belong to `participates`. A behaviour or schema
change increments the version, and every participant is reconciled in the same change. Editorial
changes need no version increment.

## Diagrams

Diagrams in reading are D2 blocks. A `d2` block is either a **checked diagram**, written in the
semantic subset and allowed only in `module` reading, or marked `d2 illustrative`. A block in any
other diagram language, such as Mermaid, is an error. The rules are in [Views](views.md).

## Links

Ordinary Markdown links navigate to readable definitions. A stable-identity fragment MUST name an
actual definition in the addressed reading document; a concept fragment MUST address the glossary,
as a [term link](#term-links). Other fragments use the renderer's slug rules. A link never adds a
document to context; a term link adds the term's definition.

## Evidence declarations

A test declares the scenario identities it verifies in the test source, in a syntax documented by
the development tool. Tools read these declarations without executing tests and reject unknown
identities. Reading content MUST NOT contain that syntax outside fences, list test locations or
prescribe coverage declarations.

# Writing guidance

<a id="module-specifications"></a>

This is the content part of [Spec writing guidelines](writing.md). Its companion,
[Required format](format.md), defines the machine-checkable structure and syntax. This chapter
explains what the **reading content** must communicate; applying it requires reader and editor
judgment. Its semantic requirements remain in force even when structural checks pass.

[Node types](model.md) and [Relations](relations.md) define what a specification declares.
No declaration alone establishes understanding.

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

A Module's design is written only in its entry's Design section, never in a topic, so a reader
never has to leave the entry to learn why the Module is built the way it is. A topic explains
something else, such as what a result means for its reader or the words several Modules share; when
it needs a design reason, it links to the entry's Design section.

## The entry

Every entry has the same three sections in the same order, so that every Module reads the same way
and a newcomer meets them in the order they need: what it is for, how to use it, and how it is
built and why, inside and in the Modules around it. How a Module fits with the
rest is part of its design, never a separate section: a separate list of relationships only
repeats the design, or draws a picture for its own sake.

### Purpose

State what the Module is for, who relies on it, and where its promises stop, including relevant
non-goals. Short plain prose. A directory or package name establishes no responsibility.

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
definitions rather than restating them. Place a diagram next to the normal path wherever it makes
the process clearer. A lightweight workflow can show steps and progression, with responsibility
lanes when they help. Use a sequence diagram when the order of messages between participants is
what needs explaining. The [diagram guidance](#diagrams) applies to Usage as well as Design.

### Design

This section holds the Module's whole design, however long it grows; no part of it moves to a
topic. The design has an inside and an outside. Inside, it explains how the Module is built: its
children, the realizations that carry its function and the files they bind, and how these work
together. Outside, it explains how the Module works with the Modules around it: the providers it
relies on and, where a reader needs them, the Modules that rely on it, including which of its parts
meets which of theirs. Level-3 headings MAY divide the section, for example into its inside and its
outside.

Explain why the decomposition, state, control and data flow, collaboration and failure containment
fulfil the guarantees. Connect each significant choice to a problem it prevents. A list of class or
function names in call order is not an explanation, and intended design is not evidence that code
conforms.

For every child and every provider, state its responsibility, when the collaboration applies, the
canonical promises relied upon, and this Module's own duties and failure reactions. These
explanations are what the `contains` and `uses` `meaning` anchors point to. A declared relation with
a link and no explanation does not satisfy this.

Record significant choices and required internal constraints, and distinguish them from incidental
current implementation and unresolved questions. Prefer linking to a guarantee over restating it as
a new obligation.

Concepts and realizations are explained here or in Usage, where understanding them matters.
Identity and bindings stay in metadata. Several nodes may share one coherent explanation with
distinct anchors, provided the prose explains all of them.

#### Diagrams

Use diagrams wherever they make relationships, order, branching, state or data clearer. Choose the
view by the reader's question, not by a quota or a fixed set of pictures. Each diagram answers one
clear question and stands next to the prose that explains it: Usage diagrams next to the normal
path or other behaviour they explain, design diagrams in Design.

| Reader's question | Useful view |
| --- | --- |
| How does a process progress, including branches, joins, retries and stopping points? | Lightweight workflow, activity or flow diagram, with responsibility lanes or stage groups when helpful |
| In what order do participants send and receive messages? | Sequence diagram |
| What states can a record or task occupy, and what causes each transition? | State diagram |
| How do the children and realizations carry the Module's function together? | Component view of the inside, with the bindings and edges that explain it |
| How does the Module interact with its users, providers and consumers? | Context view of the outside, or of the parts that meet across Modules |
| Where do processes or services run, and which boundaries do they cross? | Deployment view |
| How do records relate, or how is data transformed and passed between parts? | Data-model or data-flow view |

For a process, start with action or step nodes and directed edges. Make the main path easy to
follow and separate branches, recovery and evidence where these matter. Add lanes when ownership
helps explain the process; ordinary process descriptions do not need sequence lifelines.

All these views use D2. A checked `d2` diagram uses only the semantic subset and asserts only
declared static relations: nesting for containment, ownership and bindings, unlabelled edges
between Modules for `uses`, and labelled edges for `relates` with their declared verbs. Mark every
other view `d2 illustrative`, including workflow/activity/flow, sequence, state and deployment views
that show behaviour or runtime facts beyond those relations. A component, context or data-model view
is checked only when it fits those same rules. See [Views](views.md).

Keep names and meanings consistent with the surrounding Spec. A diagram complements explanatory
prose: explain the conditions, invariants, effects and failure reactions it cannot carry, and do
not invent a promise or a relation to fill a picture. An illustrative view grants no authority and
never replaces the declaration and prose of a load-bearing collaboration.

Draw the relationships that matter to the question. An inventory of disconnected boxes or files
usually adds nothing to a list; leave realizations that only keep the repository running, such as
project configuration, development tooling or test suites, to prose. A small Module may need no
diagram, while a Module with little static structure may still benefit from a workflow, sequence
or state view. Use as many diagrams as help understanding, with none drawn only to have one.

## Terms

The words of the whole project live in one glossary, so a word means one thing everywhere and a
reader looks it up in one place. Link a term where a document first uses it, with a
[term link](format.md#term-links) to its glossary entry, and link it again wherever a reader
arriving mid-document would need it. A reader receives the definition of every term its documents
link, and only those, so an unlinked term is a word the reader may not know.

Deciding which concepts exist is substantive. Declare a concept for a domain word, a record, a
boundary actor or an external standard a reader must understand; not for a file, an identity or an
internal class. Before adding one, look for an existing term with that meaning and link it
instead. Decide who owns each word by who is entitled to change its meaning; see
[Node types](model.md#concept). Write the definition as one sentence a newcomer understands
without the owner's documents, and the extended explanation in the owner's document at the anchor
the entry names. When a word could be confused with another term or with a Module's name, declare
`contrasts`; when it conflicts with common usage outside the project, state `external_conflict`.

Titles are unique in the project. Two meanings of one word are two terms with distinct titles, such
as `Session round` and `Headless round`, not one title defined twice.

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
gap until an explicit change to the specification repairs it: source code, another Module's own
selections and publisher summaries cannot silently supply a missing contract. The one explicit route
from code to specification is a `code-to-spec` task (see [Boundaries](boundaries.md#task-types)),
whose changes are ordinary specification changes and leave every doubtful intent a reported gap.

# Module entry template

A starter for `module.md`. Begin with [Spec writing guidelines](../writing.md) and use both parts:
[Required format](../format.md) for structure and syntax, and [Writing guidance](../module.md) for
what each section must explain. Satisfying this shape establishes nothing about meaning.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. Declare the Module's concepts as entries of the project glossary. The
[required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Usage

[Audience, use conditions, prerequisites and actual entry points. Follow one representative input
through its result and effects. Then errors, repeat invocation, cancellation and compatibility.
Include a concrete illustration where abstraction would hide a user decision. Name unsupported
behaviour as unsupported. Use a diagram next to the normal path when it makes the process clearer.
The lightweight workflow below shows progression; replace its placeholders with the actual steps
and explain their conditions and effects in prose, or omit it if it adds no clarity. Add lanes or
stage groups only when responsibility or phases matter.]

```d2 illustrative
direction: right
start: "[User's first step]"
act: "[Module's action]"
finish: "[Result and effects]"
start -> act -> finish
```

<a id="concept.example-record"></a>

[Explain the [example record](../glossary.json#concept.example-record) where understanding it
matters. Link every term where the document first uses it, such as the provider's
[thing](../glossary.json#concept.thing).]

## Design

<a id="realization.example.service"></a>

[How the Module is built and why: the decomposition, state, flow and failure containment, and how
each significant choice fulfils a guarantee or prevents a problem. Distinguish significant choices
from incidental implementation and open questions.]

[The inside, if the Module has structure worth drawing: its children and the realizations that
carry its function, with the files they bind and the edges that matter.]

```d2
example: Example {
  service: Example service {
    "src/example/"
  }
  record: Example record
  service -> record: saves
}
```

[The outside: how the Module works with the Modules around it, and which of its parts meets which
of theirs.]

```d2
example: Example {
  service: Example service
}
provider: Provider
example.service -> provider: reserves stock through
example -> provider
```

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Explain the conditions and reactions a picture cannot
carry. Use further diagrams wherever they clarify relationships, order, branching, state or data:
a workflow/activity/flow view for a process and its branches or retries, a sequence for participant
message ordering, a state view for a lifecycle, or a component, context, deployment or data-model
view for the design question at hand. Each answers one question next to explanatory prose, using
the same terminology. There is no required count or set of diagrams; invent no promises to fill
them.]
````

The two term links declare that this document mentions `concept.example-record`, which Example
owns, and `concept.thing`, which the provider owns: a reader of Example receives both definitions.
The anchor `concept.example-record` holds the extended explanation the glossary entry names.

The Usage workflow is `d2 illustrative`: its steps and progression explain behaviour, not declared
static relations. Sequence lifelines are useful when message ordering needs explanation, not a
prerequisite for drawing a process. Keep Usage views by the normal path or other behaviour they
explain, and design views in Design.

Both Design diagrams are checked, and each answers one question: the first how Example is built,
the second how it meets its provider. `Example` and `Provider` resolve to Module titles, `Example
service` and `Example record` to this Module's nodes, and `src/example/` to the entry the service
binds. Nesting asserts that Example owns both nodes and that the service binds its entry; the
labelled edges match the `relates` declarations below and the unlabelled edge between the two
Modules matches the `uses`. Checked diagrams use only the D2 semantic subset and declared static
relations; the look is the publisher's. All other views use `d2 illustrative`, with no authority
beyond the surrounding prose and no substitute for declaring load-bearing collaborations. There
is no separate Relationships section: the design holds both the inside and the outside.

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
       "relies_on": ["concept.thing"]}
    ],
    "includes": [],
    "participates": []
  },
  "defines": [
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
     "target": "concept.example-record"},
    {"type": "relates", "source": "realization.example.service",
     "verb": "reserves stock through", "target": "module.provider"}
  ]
}
````

The `uses` entry selects the provider's entry and the document explaining `concept.thing`, which
satisfies the context requirement of relating to `module.provider`. The `Provider` label in the
diagram resolves because the provider Module's title is `Provider`.

## Glossary entry

Example's concept is an entry of the project glossary, which names Example as its owner and the
anchor above as its explanation:

````json
{
  "id": "concept.example-record",
  "title": "Example record",
  "owner": "module.example",
  "definition": "The durable record of one accepted request.",
  "explanation": "example/module.md#concept.example-record"
}
````

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
     "relies_on": ["concept.thing"]}
  ],
  "includes": [],
  "participates": []
}
````

# Scenario fragment

Use both parts of [Spec writing guidelines](../writing.md):
[Required format](../format.md#scenarios) for the step syntax and
[Writing guidance](../module.md#precise-obligations) for choosing and explaining the situation.

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
