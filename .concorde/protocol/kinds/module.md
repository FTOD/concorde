# Spec writing guidelines

Use these guidelines to write and evaluate a Module's Specs. They have three separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax: document
  pairs, declarations, metadata, identities, anchors and precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader, in a recommended reading order: purpose, core concepts, overview diagrams, then details
  of correct use, design and collaborations. Applying it requires reader and editor judgment.
- **[Evaluating a Spec](evaluation.md)** states how a Spec is judged good: the quality of one
  Module's Specs for its reader, the quality of the architecture between Modules, and when a
  problem is blocking or advisory. It is a judgment and not deterministic.

All three parts serve the Protocol's purposes of understanding and boundaries. Semantic writing
requirements still apply when structural checks pass. Mandatory terms retain their force in every
part: **MUST** and **MUST NOT** state requirements and prohibitions, **SHOULD** allows departure
for an explained reason, and **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning. The
[Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify, choosing a workflow diagram for
any process, including one among several participants, or another view suited to the reader's
question; see [Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Evaluate the content for semantic
sufficiency as well, as [Evaluating a Spec](evaluation.md) states; evidence from the implementation
establishes implementation conformance. None of these substitutes for another; see
[Conformance](principles.md#conformance).

# Required format

This is the structure and syntax part of [Spec writing guidelines](writing.md), covering the
machine-checkable rules. Read it with [Writing guidance](module.md), which explains the content
readers need and the judgments authors and reviewers must make. Semantic requirements still apply
where they accompany a format rule; the [Checks](checks.md) chapter states what tools establish.

This chapter defines how the [node types](model.md) and [relations](relations.md) are written.
The fixed declaration syntax serves boundaries: a tool computes every set without interpreting
prose. The reading itself has no fixed section structure: how an entry is organized is a writing
judgment, which [Writing guidance](module.md#the-entry) explains. Satisfying the syntax establishes
structural conformance only; it proves nothing about meaning.

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

An entry `module.md` has no required sections: the Protocol checks no heading of an entry, and its
level-2 sections, their titles and their order are the writer's choice. [Writing
guidance](module.md#the-entry) recommends an order, starting with the Module's purpose. Honest
unknowns are stated explicitly.

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

A Module's design is its entry: no part of it moves to a topic, so a reader never has to leave the
entry to learn what the Module is and why it is built the way it is. The concepts a Module owns
SHOULD be explained in its entry too, at the anchors their glossary entries name, not in a separate
topic collecting them. A topic explains something else, such as what a result means for its reader
or how to proceed in one situation; when it needs a design reason, it links to the entry.

## The entry

The entry is where a reader meets the Module, and the whole entry is its design: what the Module is
for, the ideas it rests on, how its parts and the Modules around it work together, and why it is
built that way. The Protocol imposes no section structure on it. No section is required, and its
headings, their titles and their order are chosen for its reader.

A writer SHOULD follow this reading order, because it serves a developer who wants to understand
the Module quickly: the picture first, and the details once the picture is clear.

1. **Purpose.** What the Module is for, who relies on it and where its promises stop, including
   relevant non-goals, in short plain prose. A directory or package name establishes no
   responsibility.
2. **Core concepts.** The ideas a reader needs before the rest makes sense: the Module's own terms,
   each explained at the anchor its glossary entry names, and the terms of other Modules it builds
   on, linked.
3. **Overview.** Diagrams of the Module's main structure, functions and flows, each with short
   prose saying what it shows: how the parts are arranged, what the Module does with its input, how
   a typical piece of work progresses. See [Diagrams](#diagrams).
4. **Details.** Everything else the reader needs, in the order that suits the Module: its parts and
   how each carries the function, its collaborations with its children and providers, its actual
   entry points, errors and limits, and the reasons for its significant choices.

Keep operational detail with the Module that owns it. A parent or the root shows a process its
children carry out at the level of its own concepts and links to the child whose Spec walks through
the commands; it does not repeat that walk-through. How a Module fits with the rest is part of its
explanation, so a separate list of relationships that only repeats it adds nothing.

Whatever its structure, the entry satisfies [the intended reader](#the-intended-reader). The
following explains what its content must communicate.

### How the Module is used

Explain the audience, use conditions and prerequisites, and the actual entry points. Where the
Module has entry points, follow a representative input through its result and effects on a coherent
normal path before turning to errors, repeat invocation, cancellation and compatibility.

A reader MUST NOT have to assemble instructions from formal statements. Include a concrete
illustration wherever abstraction would otherwise hide a decision the user has to make. An
unsupported behaviour is identified as unsupported, never invented to fill a template. A logical
responsibility may participate in a collaboration without having any callable entry point, and MUST
NOT invent one.

The entry's prose is canonical explanation, not a second summary with weaker promises. Link to
precise definitions rather than restating them.

### Why it is built this way

The design has an inside and an outside. Inside, the entry explains how the Module is built: its
children, the realizations that carry its function and the files they bind, and how these work
together. Outside, it explains how the Module works with the Modules around it: the providers it
relies on and, where a reader needs them, the Modules that rely on it, including which of its parts
meets which of theirs.

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

Identity and bindings stay in metadata. Several nodes may share one coherent explanation with
distinct anchors, provided the prose explains all of them.

### Diagrams

Use diagrams wherever they make relationships, order, branching, state or data clearer. Choose the
view by the reader's question, not by a quota or a fixed set of pictures. Each diagram answers one
clear question and stands next to the prose that explains it: overview diagrams near the top of the
entry, the others beside the details they clarify.

| Reader's question | Useful view |
| --- | --- |
| How does a process progress, including branches, joins, retries, stopping points and hand-offs between participants? | Workflow diagram: steps and directed edges, with a lane per participant or stage groups when helpful |
| Does the exact interleaving of messages between participants matter, as in a request and reply protocol? | Sequence diagram, only then |
| What states can a record or task occupy, and what causes each transition? | State diagram |
| How do the children and realizations carry the Module's function together? | Component view of the inside, with the bindings and edges that explain it |
| How does the Module interact with its users, providers and consumers? | Context view of the outside, or of the parts that meet across Modules |
| Where do processes or services run, and which boundaries do they cross? | Deployment view |
| How do records relate, or how is data transformed and passed between parts? | Data-model or data-flow view |

A process is a workflow diagram by default, including an interaction among several Modules or
agents: start with step nodes and directed edges, make the main path easy to follow, and separate
branches, recovery and evidence where these matter. Give each participant a lane when who does a
step matters, so that an edge between lanes shows a hand-off. A sequence diagram is heavier to
read, since the reader must follow lifelines and messages to find the steps; use one only when the
interleaving of messages is itself the point.

All these views use D2. A checked `d2` diagram uses only the semantic subset and asserts only
declared static relations: nesting for containment, ownership and bindings, unlabelled edges
between Modules for `uses`, and labelled edges for `relates` with their declared verbs. Mark every
other view `d2 illustrative`, including workflow, sequence, state and deployment views that show
behaviour or runtime facts beyond those relations. A component, context or data-model view is
checked only when it fits those same rules. See [Views](views.md).

Keep names and meanings consistent with the surrounding Spec. A diagram complements explanatory
prose: explain the conditions, invariants, effects and failure reactions it cannot carry, and do
not invent a promise or a relation to fill a picture. An illustrative view grants no authority and
never replaces the declaration and prose of a load-bearing collaboration.

Draw the relationships that matter to the question. An inventory of disconnected boxes or files
usually adds nothing to a list; leave realizations that only keep the repository running, such as
project configuration, development tooling or test suites, to prose. A small Module may need no
diagram, while a Module with little static structure may still benefit from a workflow or state
view. Use as many diagrams as help understanding, with none drawn only to have one.

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

# Evaluating a Spec

This is the evaluation part of [Spec writing guidelines](writing.md). [Required format](format.md)
defines the structure a Spec must have and [Writing guidance](module.md) what its content must
communicate; this chapter states how a Spec is judged good. It serves understanding: a Spec that
passes every structural check can still leave its reader unable to rely on it, and only a judgment
of its content finds that.

## A judgment, not a check

Evaluation is a judgment of meaning, and it is **not deterministic**. Two careful evaluations of
the same Specs may notice different problems, weigh them differently and word them differently.
The criteria below make evaluations comparable in what they look for; they do not make them
decidable, and no criterion is a [structural check](checks.md) or can become one. A result of
evaluation is never structural conformance, and never implementation conformance either: it is
evidence about [semantic sufficiency](principles.md#conformance) only, bound to the exact Specs it
read. An evaluation that found no problem shows that it found none, not that none exists.

A problem is established by the text of the Specs that shows it: the passage, the declaration or
the absence the evaluation can point to. An impression that cannot be tied to the Specs is not a
problem.

Evaluation happens at two levels, each read from its own boundary:

| Level | What is judged | What is read |
| --- | --- | --- |
| [Module quality](#module-quality) | one Module's own documents, for the reader of that Module | the Module's `SpecContext` and external context, as a `review-spec` task receives them |
| [Architecture quality](#architecture-quality) | how the project is divided into Modules and how they rely on each other | every Module's Specs, `ProjectSpecification`, as a `review-architecture` task receives them |

Neither level reads code contents (see [Task types](boundaries.md#task-types)). A Spec is judged by
what it tells its reader; whether the code does what the Spec says is implementation conformance,
established by evidence. Code never repairs a Spec's missing meaning.

## Severity

Every problem is **blocking** or **advisory**:

- **Blocking**: a reader of the Module, or a task bound to it, could not rely on the Spec as
  written. The Spec leaves them unable to act, or leads them to act wrongly: a requirement that
  joins two obligations, a scenario whose outcome cannot be observed, an entry that never shows
  how a normal interaction goes, two documents or two Modules that contradict each other, a term
  used in two meanings, a responsibility two Modules both claim or none owns, a dependency that is
  relied upon but not declared.
- **Advisory**: the Spec can be relied upon, but could serve its reader better: wording that could
  be clearer without changing what a reader would do, an order that makes the reader wait for the
  idea they need, a diagram that would make a relationship easier to follow, a boundary that could
  be drawn more cleanly without any task being misled today.

Severity measures the effect on a reader and a task, not the size or difficulty of the repair. A
missing diagram alone is advisory; when the meaning a picture would show is itself missing or
contradictory, the missing meaning is the problem, and a picture alone cannot supply it. The
Protocol defines no further grading: what is done with a problem once found, who repairs it and
whether it must be decided by someone else, belongs to the tools and the project's own process.

## Module quality

Module quality is judged for the [intended reader](module.md#the-intended-reader): someone with
general software knowledge who does not know the project's code or history, and who must be able to
explain, from the Module's Specs alone, what it is for, when and how to use it, a normal
interaction and its result, the important stopping conditions, and why its design supports its
guarantees. Only the Module's own documents are judged; a problem seen in a provider's or an
included document concerns that other Module, and its own evaluation judges it. The criteria fall
into six dimensions.

### Readability

- The entry lets a reader understand the Module quickly, in the
  [reading order](module.md#the-entry) the guidance recommends: first what the Module is for, who
  relies on it and where its promises stop, in short plain prose; then the core concepts; then
  overview diagrams of its main structure, functions and flows; then the details. The Protocol
  requires no section, so the order is judged, not the headings.
- Where the Module has entry points, a reader can follow a coherent normal path from an input to
  its result before errors, repetition and cancellation, with a concrete illustration wherever an
  abstraction would hide a decision the reader has to make. A reader never has to assemble
  instructions from formal statements.
- Operational detail stays with the Module that owns it: a parent shows its children's process at
  the level of its own concepts and leaves their commands to them.
- Unknowns and unsupported behaviour are stated honestly, never invented to fill a structure.

### Obligations

- Each requirement is one decidable Module-wide obligation, with exactly one `SHALL` or
  `SHALL NOT`: not two obligations joined in one sentence, and not a guarantee that holds only in
  one situation, which belongs in a scenario.
- Each scenario is one testable situation whose `THEN` steps state observable outcomes.
- Each obligation is defined once. Module-role prose explains the important guarantees and links
  to them, and never weakens, duplicates or contradicts one.
- An interface is specified by behaviour: its inputs, outputs, effects, failures, compatibility and
  repeat behaviour are explained in readable text, not left to be inferred from a schema's shape.

### Design

- The entry explains why the decomposition, state, control and data flow, collaboration and
  failure containment fulfil the guarantees, connecting each significant choice to a problem it
  prevents. A list of names in call order is not an explanation.
- Every child and every provider has an explanation of its responsibility, when the collaboration
  applies, the promises relied upon, and the Module's own duties and failure reactions. A declared
  relation with a link and no explanation does not meet this.
- Significant choices are told apart from incidental current implementation and from open
  questions.

### Views

- A diagram answers one clear question, stands next to the prose it complements and uses the same
  terms. The kind of view suits the question: a process is a workflow by default, and a sequence
  diagram is used only when the interleaving of messages is the point.
- A checked diagram asserts only declared relations; any other view is marked illustrative and
  claims no authority beyond its prose. A load-bearing collaboration is never described only in an
  illustrative diagram.
- A place where a diagram would make relationships, order, branching, state or data clearer is a
  problem of readability; no count or kind of diagram is required.

### Terminology

- Every term the Module owns has one clear one-sentence definition and an explanation, is used with
  that meaning throughout, and says so where it could be confused with another term or with common
  usage.
- Every term a reader needs is linked where a document first uses it, before the rest relies on
  it.
- A concept is declared only for a word whose meaning in the project is narrower than or different
  from its ordinary sense and that another Module uses; any other word is explained in its owner's
  own document. Deciding which concepts exist is part of the Module's quality, not a formality.

### Context

- The Module's context holds every document and definition its Specs rely on. A promise the Module
  relies on whose defining document its declarations do not select is a gap of the Module, repaired
  by an explicit selection, never by reading outside the boundary.
- An evaluation that needed a document it was not given names that document and why it needed it,
  instead of guessing its content.

## Architecture quality

Architecture quality is judged between Modules, from every Module's Specs read together. It asks
whether the division of the project into Modules serves both of the Protocol's purposes: whether a
reader understands the project as a set of responsibilities that fit together, and whether the
boundaries built from those Modules fit the tasks the project actually needs. Each problem names
every Module it concerns; a problem between two Modules concerns both. The criteria fall into six
dimensions.

### Responsibilities

- Each Module is drawn around one responsibility and one axis of change, as
  [Choosing Module boundaries](module.md#choosing-module-boundaries) explains: a capability, a use
  case, a boundary with one collaborator. Things that change together are in one Module, and a
  Module does not collect things only because they are the same kind of artifact.
- Each Module is cohesive: its purpose can be said in one plain sentence, and every part of it
  serves that purpose. A Module whose parts change for unrelated reasons is two Modules.
- A typical change of the project needs the write sets of one Module, or of a few whose
  collaboration it changes, not slices of many.
- Siblings are drawn at comparable levels of abstraction, and each Module's Specs stay at one
  level: a Module that orchestrates others relies on their promises and does not restate their
  internal steps.

### Ownership

- Every concept, promise and responsibility the project relies on has exactly one owner. Two
  Modules that promise the same thing, or both describe themselves as responsible for the same
  decision, overlap; one of them owns it and the other relies on it.
- Nothing the project relies on is left unowned: every step of a main flow, every record several
  Modules share and every rule a guarantee depends on is promised by some Module. A responsibility
  that every Module assumes another carries is a gap.
- A boundary between two Modules is clear: from their Specs alone a reader can tell, for any piece
  of behaviour in the project, which Module promises it.

### Interfaces

- Modules are decoupled: a consumer relies on a few, stable promises of its provider, named where
  it can with `relies_on`, and not on the provider's internal structure, records or order of steps.
- An interface between Modules is narrow and defined by behaviour, through a contract where it is
  shared and through readable promises in every case. A consumer that could only work by knowing
  how its provider is built has an interface that is too wide.
- A consumer's account of what it relies on agrees with what the provider actually promises.

### Dependencies

- Every reliance is declared. A Module whose Specs rely on another Module's promises declares `uses`
  of it; a dependency stated only in prose, or only visible in the code, is undeclared, and its
  impact on the consumer cannot be derived from declarations.
- The direction of each dependency is sensible: it follows who relies on whom. A general Module
  does not depend on a specific consumer in order to serve it, and a provider does not gain a
  relation to a consumer only so that its own Specs can describe that consumer's use.
- Mutual `uses` between two Modules are acceptable, because two Modules may rely on each other's
  promises: a cycle of `uses` alone is not a problem. What is judged is whether each reliance is
  real, declared and explained.

### Failure containment

- Each Module states how it reacts when a collaborator it relies on fails, refuses or is
  unavailable, and what its own consumers then observe. A failure crosses a boundary between
  Modules as a stated outcome, never as undefined behaviour of the consumer.
- A Module's failure cannot silently corrupt another Module's state or promises: where a failure
  leaves work half done, the Spec says which Module detects it and how it is recovered.

### Consistency

- Promises that several Modules make about the same thing agree: the same record, limit, state,
  flow or term is described the same way wherever it appears, and a statement in one Module never
  contradicts its owner's.
- The same kind of problem is solved the same way across Modules unless a Spec explains the
  difference: errors are reported, identities formed and repeated invocations handled alike.
- A parent explains how its children together fulfil its responsibility, and what it says of each
  child agrees with that child's own Specs.

# Module entry template

A starter for `module.md`. Begin with [Spec writing guidelines](../writing.md) and use both parts:
[Required format](../format.md) for structure and syntax, and [Writing guidance](../module.md) for
what the entry must explain. Satisfying this shape establishes nothing about meaning.

The Protocol requires no section of an entry. The headings below follow the recommended reading
order, purpose, core concepts, overview, then details; rename, merge or split them as the Module's
reader needs, and give the details whatever headings suit the Module.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. Declare the Module's concepts as entries of the project glossary. The
[required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Core concepts

<a id="concept.example-record"></a>

[Explain the [example record](../glossary.json#concept.example-record): what it is, why the Module
needs it and how it relates to the other ideas here. Link every term of another Module where the
document first uses it, such as the provider's [thing](../glossary.json#concept.thing).]

## Overview

[How the Module is built and how it meets the Modules around it, in one picture if one suffices,
with short prose saying what it shows.]

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

[How a typical piece of work progresses, as a workflow with a lane per participant when who does
each step matters. Replace the placeholders with the actual steps and explain their conditions and
effects in prose, or omit the diagram if it adds no clarity.]

```d2 illustrative
direction: right
user: User {
  request: "[User's request]"
  result: "[Result and effects]"
}
example: Example {
  act: "[Module's action]"
}
user.request -> example.act -> user.result
```

## [A detail, under a heading that names it]

<a id="realization.example.service"></a>

[The details, in the order that suits the Module: its parts and how each carries the function; its
actual entry points, following a representative input through its result and effects, then errors,
repeat invocation, cancellation and compatibility, naming unsupported behaviour as unsupported; the
reasons for significant choices, distinguished from incidental implementation and open questions.]

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Add further diagrams beside the details they clarify: a
state view for a lifecycle, a workflow for a process with its branches and retries, or a component,
context, deployment or data-model view for the design question at hand. Draw a sequence diagram
only when the interleaving of messages is itself the point. There is no required count or set of
diagrams; invent no promises to fill them.]
````

The two term links declare that this document mentions `concept.example-record`, which Example
owns, and `concept.thing`, which the provider owns: a reader of Example receives both definitions.
The anchor `concept.example-record` holds the extended explanation the glossary entry names, in the
entry of its owner rather than in a separate topic.

The overview diagram is checked and answers one question: how Example is built and how it meets
its provider. `Example` and `Provider` resolve to Module titles, `Example service` and `Example
record` to this Module's nodes, and `src/example/` to the entry the service binds. Nesting asserts
that Example owns both nodes and that the service binds its entry; the labelled edges match the
`relates` declarations below and the unlabelled edge between the two Modules matches the `uses`. A
Module with more structure may draw its inside and its outside in two diagrams. Checked diagrams
use only the D2 semantic subset and declared static relations; the look is the publisher's.

The workflow is `d2 illustrative`: its steps and progression explain behaviour, not declared
static relations. Its lanes show who does each step, and an edge between lanes is a hand-off, which
is why a process among several participants needs no sequence lifelines. Illustrative views carry
no authority beyond the surrounding prose and never substitute for declaring load-bearing
collaborations. How the Module fits with the rest is part of its explanation, not a separate list
of relationships.

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
