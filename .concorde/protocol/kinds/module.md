# Spec writing guidelines

Use these guidelines to write and evaluate a Module's Specs. They have four separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax:
  - Document pairs.
  - Declarations.
  - Metadata.
  - Identities.
  - Anchors.
  - Precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader. It recommends this reading order:
  - Purpose.
  - Core concepts.
  - Overview diagrams.
  - Details of correct use, design and collaborations.

  Applying it requires reader and editor judgment.
- **[Sentence style](style.md)** states how each sentence is written:
  - One fact in each sentence.
  - Short sentences.
  - Lists instead of long runs of clauses.
  - The actor named.
  - No semicolons.

  Its rules are inspired by the structural rules of ASD-STE100 Simplified Technical English.
- **[Evaluating a Spec](evaluation.md)** states how a Spec is judged good:
  - The quality of one Module's Specs for its reader.
  - The quality of the architecture between Modules.
  - When a problem is blocking or advisory.

  It is a judgment and not deterministic.

All four parts serve the Protocol's purposes of understanding and boundaries. When structural
checks pass, semantic writing requirements still apply. Mandatory terms retain their force in every
part. **MUST** states requirements. **MUST NOT** states prohibitions. **SHOULD** allows departure
for an explained reason. **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning.

The [Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify. Choose a workflow diagram for any
process, including one among several participants, or another view suited to the reader's question.
See [Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Evaluate the content for semantic
sufficiency as well, as [Evaluating a Spec](evaluation.md) states. Evidence from the implementation
establishes implementation conformance. None of these substitutes for another.
See [Conformance](principles.md#conformance).

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

# Writing guidance

<a id="module-specifications"></a>

This is the content part of [Spec writing guidelines](writing.md). Its companion,
[Required format](format.md), defines the machine-checkable structure and syntax. This chapter
explains what the **reading content** must communicate. Applying it requires reader and editor
judgment. Its semantic requirements remain in force even when structural checks pass.

[Node types](model.md) and [Relations](relations.md) define what a specification declares.
No declaration alone establishes understanding.

This chapter serves understanding above all: it is what makes a structurally valid specification
worth reading.

A Module specifies one responsibility for consumers and implementers. It need not correspond to any
of these:

- A package.
- A directory.
- A service.
- A process.

These establish its boundary:

- Its purpose.
- Its behaviour.
- Its concepts.
- Its collaborations.

Realization bindings locate its code. They establish nothing about scope.

## Choosing Module boundaries

Draw Modules around responsibilities and axes of change:

- A capability.
- A use case.
- A boundary with one collaborator.

Things that change together SHOULD belong to one Module. A Module SHOULD NOT collect things only
because they are the same kind of artifact, such as:

- All scripts.
- All prompts.
- All configuration.

This choice serves both purposes at once. A reader understands a responsibility, not a file type.
A task's boundary is built from Modules. Therefore, a Module that matches how the project actually
changes yields boundaries that fit real tasks. A typical change needs one Module's write sets, not
slices of five.

A Module MAY be purely compositional, explaining how its children together fulfil a responsibility.
A Module MAY bind files of its own.

## The intended reader

Assume a reader with general software knowledge who does **not** know any of these:

- This project's implementation.
- This project's internal type names.
- This project's execution library.
- This project's history.

From the reading content alone, that reader must be able to explain:

- The problem the Module solves.
- When to use it.
- A normal interaction and its result.
- The important stopping conditions.
- Why the design supports the guarantees.

If reaching that state requires any of the following, the specification is incomplete regardless
of how many checks pass:

- Reading source code.
- Reading an unselected document.
- Reading a maintainer.

This reader is the measure of the Protocol's first purpose: a human understands the project from
its specification without reading its code.

## Document roles

One Module specification has two roles of document. Both are reading content. Both are owned
directly by the Module.

- **Module documents** (`role: module`) — the `module.md` entry and explanatory topics. They explain:
  - The responsibility.
  - Correct use.
  - Design.
  - Collaborations.

  Module documents MUST NOT become link indexes or independently maintained summaries with weaker
  promises.
- **Implementation documents** (`role: implementation`) specify:
  - The precise requirements.
  - The scenarios.
  - The canonical contracts.

  They are specifications, not any of these:
  - Source code.
  - Plans.
  - Descriptions of incidental implementation.

Role separation is about meaning, not heading syntax. Even when written as ordinary prose, the
following belong to `implementation` reading:

- Exact private APIs.
- Wire fields.
- Byte algorithms.
- Persistence layouts.
- Internal limits.
- Executable topology.

The following belong to `module` reading:

- Architecture.
- Design reasons.
- Actual public entry points.
- Any limit or hazard a consumer needs for correct use.

A topic is an explanation, never a second owner or a nested requirements container.

A Module's design is its entry. No part of it moves to a topic. Thus, a reader never has to leave
the entry to learn what the Module is and why it is built the way it is.
The concepts a Module owns SHOULD be explained in its entry too, at the anchors their glossary
entries name, not in a separate topic collecting them.

A topic explains something else, such as what a result means for its reader or how to proceed in
one situation. When a topic needs a design reason, it links to the entry.

## The entry

The entry is where a reader meets the Module. The whole entry is its design:

- What the Module is for.
- The ideas it rests on.
- How its parts and the Modules around it work together.
- Why it is built that way.

The Protocol imposes no section structure on it. No section is required. These are chosen for its
reader:

- Its headings.
- Their titles.
- Their order.

This reading order serves a developer who wants to understand the Module quickly.
A writer SHOULD follow this reading order: the picture first, and the details once the picture is
clear.

1. **Purpose.** What the Module is for, who relies on it and where its promises stop, including
   relevant non-goals, in short plain prose. A directory or package name establishes no responsibility.
2. **Core concepts.** The ideas a reader needs before the rest makes sense. These are the Module's
   own terms, each explained at the anchor its glossary entry names, and the terms of other Modules
   it builds on, linked.
3. **Overview.** Diagrams of the Module's main structure, functions and flows.

   Each diagram has short prose saying what it shows:
   - How the parts are arranged.
   - What the Module does with its input.
   - How a typical piece of work progresses.

   See [Diagrams](#diagrams).
4. **Details.** Everything else the reader needs, in the order that suits the Module:
   - Its parts and how each carries the function.
   - Its collaborations with its children and providers.
   - Its actual entry points.
   - Its errors and limits.
   - The reasons for its significant choices.

Keep operational detail with the Module that owns it. A parent or the root shows a process its
children carry out at the level of its own concepts. The parent or root links to the child whose
Spec walks through the commands. The parent or root does not repeat that walk-through. How a Module
fits with the rest is part of its explanation. Thus, a separate list of relationships that only
repeats it adds nothing.

Whatever its structure, the entry satisfies [the intended reader](#the-intended-reader). The
following explains what its content must communicate.

### How the Module is used

Explain these:

- The audience.
- The use conditions and prerequisites.
- The actual entry points.

Where the Module has entry points, follow a representative input through its result and effects on
a coherent normal path before turning to:

- Errors.
- Repeat invocation.
- Cancellation.
- Compatibility.

A reader MUST NOT have to assemble instructions from formal statements. Wherever abstraction would
otherwise hide a decision the user has to make, include a concrete illustration.
An unsupported behaviour is identified as unsupported, never invented to fill a template.
A logical responsibility may participate in a collaboration without having any callable entry point.
A logical responsibility MUST NOT invent one.

The entry's prose is canonical explanation, not a second summary with weaker promises. Link to
precise definitions rather than restating them.

### Why it is built this way

The design has an inside and an outside. Inside, the entry explains how the Module is built:

- Its children.
- The realizations that carry its function and the files they bind.
- How these work together.

Outside, the entry explains how the Module works with the Modules around it:

- The providers it relies on, including which of its parts meets which of theirs.
- Where a reader needs them, the Modules that rely on it, including which of its parts meets which
  of theirs.

Explain why these fulfil the guarantees:

- The decomposition.
- The state.
- The control and data flow.
- The collaboration.
- The failure containment.

Connect each significant choice to a problem it prevents. A list of class or function names in call
order is not an explanation. Intended design is not evidence that code conforms.

For every child and every provider, state:

- Its responsibility.
- When the collaboration applies.
- The canonical promises relied upon.
- This Module's own duties and failure reactions.

These explanations are what the `contains` and `uses` `meaning` anchors point to. A declared
relation with a link and no explanation does not satisfy this.

Record significant choices and required internal constraints. Distinguish them from incidental
current implementation and unresolved questions. Prefer linking to a guarantee over restating it as
a new obligation.

Identity and bindings stay in metadata. Provided the prose explains all of them, several nodes may
share one coherent explanation with distinct anchors.

### Diagrams

Use diagrams wherever they make any of these clearer:

- Relationships.
- Order.
- Branching.
- State.
- Data.

Choose the view by the reader's question, not by a quota or a fixed set of pictures. Each diagram
answers one clear question. Each diagram stands next to the prose that explains it.
Overview diagrams stand near the top of the entry. The others stand beside the details they clarify.

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
agents. Follow these steps:

- Start with step nodes and directed edges.
- Make the main path easy to follow.
- Where these matter, separate branches, recovery and evidence.

When who does a step matters, give each participant a lane so that an edge between lanes shows a
hand-off. A sequence diagram is heavier to read. The reader must follow lifelines and messages to
find the steps. Use one only when the interleaving of messages is itself the point.

All these views use D2. A checked `d2` diagram uses only the semantic subset. It asserts only
declared static relations:

- Nesting for containment, ownership and bindings.
- Unlabelled edges between Modules for `uses`.
- Labelled edges for `relates` with their declared verbs.

Mark every other view `d2 illustrative`. This includes the following views that show behaviour or
runtime facts beyond those relations:

- Workflow views.
- Sequence views.
- State views.
- Deployment views.

Only when a component, context or data-model view fits those same rules is it checked.
See [Views](views.md).

Keep names and meanings consistent with the surrounding Spec. A diagram complements explanatory
prose. Where a diagram cannot carry them, explain the following:

- The conditions.
- The invariants.
- The effects.
- The failure reactions.

Do not invent a promise or a relation to fill a picture. An illustrative view grants no authority.
It never replaces the declaration and prose of a load-bearing collaboration.

Draw the relationships that matter to the question. An inventory of disconnected boxes or files
usually adds nothing to a list. Leave realizations that only keep the repository running to prose.
Examples include:

- Project configuration.
- Development tooling.
- Test suites.

A small Module may need no diagram. A Module with little static structure may still benefit from a
workflow or state view. Use as many diagrams as help understanding, with none drawn only to have one.

## Terms

The words of the whole project live in one glossary. Thus, a word means one thing everywhere.
A reader looks it up in one place. Where a document first uses a term, link it with a
[term link](format.md#term-links) to its glossary entry. Wherever a reader arriving mid-document
would need it, link it again. A reader receives the definition of every term its documents link,
and only those. Thus, an unlinked term is a word the reader may not know.

Deciding which concepts exist is substantive. Declare a concept for a domain word, a record, a
boundary actor or an external standard a reader must understand.

Do not declare a concept for any of these:

- A file.
- An identity.
- An internal class.

Before adding one, look for an existing term with that meaning and link it instead.
Decide who owns each word by who is entitled to change its meaning. See
[Node types](model.md#concept). Write the definition as one sentence a newcomer understands without
the owner's documents. Write the extended explanation in the owner's document at the anchor the
entry names. When a word could be confused with another term or with a Module's name, declare
`contrasts`. When a word conflicts with common usage outside the project, state `external_conflict`.

Titles are unique in the project. Two meanings of one word are two terms with distinct titles, such
as `Session round` and `Headless round`, not one title defined twice.

## Precise obligations

Define these only in `implementation` documents owned by the Module. Group headings may organize
definitions but never own them. Module documents explain the important guarantees.
Module documents link to the canonical definitions. A reader should not need to read every
acceptance case to understand the Module.

A **requirement** is one decidable Module-wide `SHALL` statement with a stable identity. A
**scenario** is one testable situation in `GIVEN`/`WHEN`/`THEN` steps. A situation-specific
guarantee belongs in that scenario's steps or explanation, not in a second requirement. Define each
obligation once. Link to it. Editorial organization MUST NOT do any of the following to it:

- Weaken it.
- Duplicate it.
- Contradict it.

An **interface** is specified by a canonical contract plus readable behaviour and scenarios, not by
a schema alone. In selected readable context, these MUST be explained, never inferred from shape:

- Inputs.
- Outputs.
- Effects.
- Failures.
- Compatibility.
- Repeat behaviour.

## Composition, dependency and inclusion

- `contains` states structural accountability. A parent explains how its children fulfil the
  responsibility it holds. The parent receives their Specs to do so. A Module has at most one
  parent. Composition is acyclic.
- `uses` states reliance on a provider's promises. It gives the consumer the provider's Specs.
  It implies none of these:
  - Ownership.
  - Deployment.
  - Directory nesting.
  - Shared source.

  Dependencies may cross hierarchy levels. Two Modules may use each other.
- `includes` states what else this Module reads, with a reason. It implies no ownership and no
  dependency.

When a Module relies on a few promises of a large provider, list them in the relation's
`relies_on` and link them from the explanation of the collaboration.

The reader then receives the provider's entry and exactly the documents defining those promises.

## Realization

A `realization` binds exact files or directory prefixes. See [Node types](model.md). Tests are
ordinary implementation files. A test declares the scenarios it verifies **in the test**.
Reading content MUST NOT list verifying tests. Reading content MUST NOT prescribe coverage
declarations. Missing coverage does not cancel a promise. A declared test is not proof of
fulfilment.

## Completeness

The selected context makes every owned and selected document available with both members intact.
Its readable subset must supply the meaning the task needs.

None of the following is proof of sufficient meaning:

- A schema.
- A heading.
- A rendered table.
- A checked diagram.
- A correctly registered file set.

Honest drafts name their unknowns. Until an explicit change to the specification repairs it,
missing necessary meaning remains a gap. None of the following can silently supply a missing
contract:

- Source code.
- Another Module's own selections.
- Publisher summaries.

The one explicit route from code to specification is a `code-to-spec` task
(see [Boundaries](boundaries.md#task-types)). Its changes are ordinary specification changes.
Its changes leave every doubtful intent a reported gap.

# Sentence style

This is the sentence part of [Spec writing guidelines](writing.md). [Writing guidance](module.md)
says what a Spec must communicate. This chapter says how its sentences are written. It applies to
the reading of every document and to every concept definition in the glossary.

The rules are inspired by the structural rules of ASD-STE100 Simplified Technical English. The
Protocol adopts only those structural rules, stated here in its own words. It does not adopt the
STE dictionary or the STE rules for modal verbs.

This chapter serves understanding. A short sentence that carries one fact is read correctly on the
first pass. This is true for a person and for a model. A requirement that names its actor and
carries one obligation tells each task what it must do.

The rules never change what a text means. A rewrite in this style keeps every fact, every
condition and every link between facts. When a rule would change the meaning of a sentence, keep
the meaning and break the rule.

## The rules

### One fact in each sentence

Write one fact, one step or one requirement in each sentence. A normative sentence carries one
obligation, so it contains one of the [requirement keywords](#requirement-keywords) at most. When a
statement has two obligations, write two sentences.

The conditions, exceptions and failures of one obligation are part of that one fact. They stay in
its sentence, as [Requirements](#requirements) says.

### Short sentences

A descriptive sentence SHOULD have 25 words or fewer. Split a longer sentence into two sentences,
or move its details into a list. Count every word of a link's text. Count an inline code span as
one word. `CHK.style.sentence-length` reports a sentence of more than 35 words.

Shorten a sentence only by its form, never by its meaning. Keep the words that carry meaning, as
[The links between facts](#the-links-between-facts) says.

A concept definition is one sentence that must identify its term. It can need more words than a
sentence of a reading. Keep it as short as identifying its term allows, and move every other detail
into the term's explanation. `CHK.style.sentence-length` reports a concept definition of more than
50 words.

The statement of a requirement has no length bound. It keeps its one obligation whole, with every
condition, exception and failure, as [Requirements](#requirements) says.
`CHK.style.sentence-length` does not measure it.

### Lists for three or more

When a sentence would name three or more conditions, cases, steps or items, write a vertical list.
Introduce the list with a short sentence that ends with a colon. Give each item one fact. Write the
items in the same grammatical form, all sentences or all phrases.

A requirement can use a list too. Its first paragraph states the obligation once and ends with a
colon. The list below it gives the conditions of that one obligation, never new obligations:

```markdown
### req.checkout.refuse-stale — Refuse a stale cart

Checkout SHALL refuse the submission when any of these conditions is true:

- The cart changed after the price was shown.
- An item in the cart is no longer sold.
- The delivery address is outside every delivery zone.
```

### The condition before the statement

Put a condition before the statement it limits, so that the reader knows the situation before the
rule. Write "When the lock is busy, the store SHALL refuse the write." Do not write "The store
refuses the write if the lock is busy and no merge runs, unless the caller waits."

A condition stays next to what it limits. When it limits only a part of a sentence, such as an
action that a guidance tells its reader to take, it stays with that part. See
[Requirements](#requirements).

### The links between facts

Keep the words that link facts or limit them. These words carry meaning:

- Causes and purposes, such as "since", "because", "so" and "so that".
- Limits, such as "only", "each", "every", "never" and "at most".
- Conditions and exceptions, such as "when", "unless", "until" and "except".

Do not drop such a word to shorten a sentence. When you split a sentence, carry the link into the
new sentence. Write "The host removes the directory when the run ends. It does this so that no
credential outlives the run." Do not drop the second sentence, because it says why the rule
exists.

### No semicolons

Do not use a semicolon in prose. Write two sentences, or write a list. A semicolon in an inline
code span or a code block is not prose. `CHK.style.semicolon` reports a semicolon in prose.

### The actor and the active voice

A requirement names the Module, component or person that acts, and uses the active voice. Write
"The host SHALL delete the file." Do not write "The file is deleted." Use the passive voice only
when the actor does not matter to the reader, as in "The file is created at install."

The subject of an obligation is the party that bears it. A rewrite keeps that party as the subject.
It never introduces an actor that the original text did not name. When a requirement names no
actor, the choice of an actor changes its promise. That choice is a change of the Spec, not of its
style.

### Requirements

The statement of a requirement is one sentence with one obligation. Its conditions, exceptions and
failures belong to that obligation, so they stay in the same sentence. Never split one obligation
into separate rules to make its sentences shorter. A requirement keeps this sentence whatever its
length.

Three or more conditions can stand in a list below the statement, as
[Lists for three or more](#lists-for-three-or-more) shows. The statement ends with a colon, and
each item is a condition of the one obligation. An item is never an obligation of its own.

Write this:

```markdown
### req.runner.remove-checkout — Remove the checkout after each run

The runner SHALL remove the checkout of each run when the run ends, also when the run failed, so
that no later run finds a stale checkout.
```

Do not write this, because the list turns one obligation into separate rules and drops its purpose:

```markdown
### req.runner.remove-checkout — Remove the checkout after each run

The runner SHALL follow these rules for the checkout:

- Remove the checkout when the run ends.
- Remove the checkout when the run failed.
```

Each condition stays next to what it limits:

- A condition of the whole obligation comes before the subject.
- A condition of one part, such as one action or one object, stays next to that part.

Write "The guidance SHALL tell the main agent to merge a task only after its delivery." Do not
write "Only after its delivery, the guidance SHALL tell the main agent to merge a task." The
delivery limits the merge, not what the guidance says.

Keep the subject that bears the obligation. Write "The guidance SHALL tell each task session to
stay inside its worktree." Do not change it to "Each task session SHALL stay inside its worktree."
That sentence gives the obligation to another party.

### Simple tenses

Use the simple present for what is true and for what a component does. Use the simple past for
what happened before, and the simple future only when the order in time matters. Avoid
progressive and perfect forms when a simple form says the same.

### One word for one meaning

The project glossary is the controlled vocabulary of the Specs. Use a defined term only with the
meaning its definition gives. Do not use a synonym for a defined term. Do not use the word of a
term in another sense. A word that the glossary does not define keeps its ordinary meaning. See
[Terms](module.md#terms).

### Requirement keywords

The requirement keywords `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD` and `MAY` keep the
meanings that the Protocol gives them. They are not the modal verbs that STE restricts. A rule of
STE that forbids "should" or "may" does not apply to a Spec. `CHK.style.one-obligation` reports a
sentence that contains more than one of these keywords in capital letters. A keyword with its NOT
is one keyword.

## What a program measures

The three style checks of [Checks](checks.md#style) have strictness warning. They measure the prose
of the reading as a reader sees it:

- Fences, headings, tables, front matter, comments and HTML anchors are not prose.
- A link counts as its text. An inline code span counts as one word.
- Each paragraph and each list item is split into sentences by the sentence-break rule of
  `CHK.concept.definition`.

A concept definition is one sentence, so the checks measure it as one sentence. Its length bound is
50 words instead of 35.

The statement of a requirement is the first sentence of the paragraph that follows the
requirement's heading, as `CHK.requirement.statement` reads it. `CHK.style.sentence-length` does
not measure it. `CHK.style.semicolon` and `CHK.style.one-obligation` measure it as any other
sentence.

The other rules need a reader's judgment. A review judges them as part of readability, by the
criteria of [Evaluating a Spec](evaluation.md#readability). A text with no style warning can still
break a rule. A sentence of 30 words passes the check and is still longer than the target.

# Evaluating a Spec

This is the evaluation part of [Spec writing guidelines](writing.md). [Required format](format.md)
defines the structure a Spec must have. [Writing guidance](module.md) defines what its content must
communicate. This chapter states how a Spec is judged good. It serves understanding. A Spec that
passes every structural check can still leave its reader unable to rely on it. Only a judgment of
its content finds that.

## A judgment, not a check

Evaluation is a judgment of meaning. It is **not deterministic**. Two careful evaluations of the
same Specs may differ in these ways:

- They may notice different problems.
- They may weigh them differently.
- They may word them differently.

The criteria below make evaluations comparable in what they look for. They do not make them
decidable. No criterion is a [structural check](checks.md) or can become one. A result of
evaluation is never structural conformance, and never implementation conformance either. It is
evidence about [semantic sufficiency](principles.md#conformance) only, bound to the exact Specs it
read. An evaluation that found no problem shows that it found none, not that none exists.

A problem is established by the text of the Specs that shows it. The evaluation can point to any
of the following:

- The passage.
- The declaration.
- The absence.

An impression that cannot be tied to the Specs is not a problem.

Evaluation happens at two levels, each read from its own boundary:

| Level | What is judged | What is read |
| --- | --- | --- |
| [Module quality](#module-quality) | one Module's own documents, for the reader of that Module | the Module's `SpecContext` and external context, as a `review-spec` task receives them |
| [Architecture quality](#architecture-quality) | how the project is divided into Modules and how they rely on each other | every Module's Specs, `ProjectSpecification`, as a `review-architecture` task receives them |

Neither level reads code contents (see [Task types](boundaries.md#task-types)). A Spec is judged by
what it tells its reader. Whether the code does what the Spec says is implementation conformance,
established by evidence. Code never repairs a Spec's missing meaning.

## Blocking and advisory problems

Every problem is **blocking** or **advisory**:

- **Blocking**: a reader of the Module, or a task bound to it, could not rely on the Spec as
  written. The Spec leaves them unable to act, or leads them to act wrongly:
  - A requirement that joins two obligations.
  - A scenario whose outcome cannot be observed.
  - An entry that never shows how a normal interaction goes.
  - Two documents or two Modules that contradict each other.
  - A term used in two meanings.
  - A responsibility two Modules both claim or none owns.
  - A dependency that is relied upon but not declared.
- **Advisory**: the Spec can be relied upon, but could serve its reader better:
  - Wording that could be clearer without changing what a reader would do.
  - An order that makes the reader wait for the idea they need.
  - A diagram that would make a relationship easier to follow.
  - A boundary that could be drawn more cleanly without any task being misled today.

Whether a problem is blocking depends on its effect on a reader and a task, not on the size or
difficulty of the repair. A missing diagram alone is advisory. When the meaning a picture would
show is itself missing or contradictory, a picture alone cannot supply the missing meaning that
is the problem.

The Protocol defines no further grading. The following belong to the tools and the project's own
process:

- What is done with a problem once found.
- Who repairs it.
- Whether it must be decided by someone else.

## Module quality

Module quality is judged for the [intended reader](module.md#the-intended-reader). This reader has
general software knowledge and does not know the project's code or history. From the Module's
Specs alone, the reader must be able to explain:

- What it is for.
- When and how to use it.
- A normal interaction and its result.
- The important stopping conditions.
- Why its design supports its guarantees.

Only the Module's own documents are judged. A problem seen in a provider's or an included document
concerns that other Module. Its own evaluation judges it. The criteria fall into six dimensions.

### Readability

- The entry lets a reader understand the Module quickly, in the
  [reading order](module.md#the-entry) the guidance recommends:
  - First, short plain prose about:
    - What the Module is for.
    - Who relies on it.
    - Where its promises stop.
  - Then, the core concepts.
  - Then, overview diagrams of its main structure, functions and flows.
  - Then, the details.

  The Protocol requires no section, so the order is judged, not the headings.
- Where the Module has entry points, a reader can follow a coherent normal path from an input to
  its result. The reader meets this path before errors, repetition and cancellation. On the path,
  a concrete illustration stands wherever an abstraction would hide a decision the reader has to
  make.

  A reader never has to assemble instructions from formal statements.
- Operational detail stays with the Module that owns it. A parent shows its children's process at
  the level of its own concepts. The parent leaves their commands to them.
- Unknowns and unsupported behaviour are stated honestly, never invented to fill a structure.
- The sentences follow [Sentence style](style.md). The style checks report:
  - Sentences that are long.
  - Semicolons.
  - Sentences with more than one requirement keyword.

  An evaluation does not report them again. It judges the rules that no program decides:
  - A requirement and every statement of behaviour name the actor and use the active voice.
  - Each sentence carries one fact, even when it is short.
  - Three or more conditions, cases or items stand in a list, not in a run of clauses.
  - A condition comes before the statement it limits.
  - Simple tenses say what is true and what happens.
- A text in this style still says what it means. An evaluation reports each of these drifts, which
  a rewrite for shorter sentences can cause:
  - One obligation split into separate rules, such as a list whose items are obligations of their
    own instead of conditions of the statement.
  - A condition, exception or failure moved out of the statement of its requirement.
  - A condition moved away from what it limits, such as a limit of one action placed before the
    subject of the whole obligation.
  - The subject of an obligation changed to a party that does not bear it, or an actor that the
    text did not name before.
  - A dropped word that links or limits facts, such as "since", "because", "so that", "only",
    "each", "every" or "never".
- While a reader still understands it correctly, a sentence that breaks the style is advisory.
  When the reader cannot tell who must act or what is required, it is blocking. A requirement that
  hides its actor in the passive voice is an example. A drift that changes what a requirement
  requires or who bears it is blocking too.

### Obligations

- Each requirement is one decidable Module-wide obligation, with exactly one `SHALL` or
  `SHALL NOT`. It is not two obligations joined in one sentence. A guarantee that holds only in
  one situation belongs in a scenario, not a requirement.
- Each scenario is one testable situation whose `THEN` steps state observable outcomes.
- Each obligation is defined once. Module-role prose explains the important guarantees. It links
  to them. Module-role prose never does any of the following:
  - Weaken an obligation.
  - Duplicate an obligation.
  - Contradict an obligation.
- An interface is specified by behaviour. Readable text explains its inputs, outputs, effects,
  failures, compatibility and repeat behaviour.
  These are not left to be inferred from a schema's shape.

### Design

- The entry explains why the following fulfil the guarantees, connecting each significant choice
  to a problem it prevents:
  - The decomposition.
  - The state.
  - The control and data flow.
  - The collaboration.
  - The failure containment.

  A list of names in call order is not an explanation.
- Every child and every provider has an explanation of:
  - What its responsibility is.
  - When the collaboration applies.
  - Which promises are relied upon.
  - What the Module's own duties and failure reactions are.

  A declared relation with a link and no explanation does not meet this.
- Significant choices are told apart from incidental current implementation and from open
  questions.

### Views

- A diagram answers one clear question. It stands next to the prose it complements. The diagram
  uses the same terms. The kind of view suits the question. A process is a workflow by default.
  Only when the interleaving of messages is the point is a sequence diagram used.
- A checked diagram asserts only declared relations. Any other view is marked illustrative. It
  claims no authority beyond its prose. A load-bearing collaboration is never described only in an
  illustrative diagram.
- A place where a diagram would make relationships, order, branching, state or data clearer is a
  problem of readability.
  No count or kind of diagram is required.

### Terminology

- Every term the Module owns has one clear one-sentence definition and an explanation. The term
  is used with that meaning throughout. Where it could be confused with another term or with
  common usage, it says so.
- Every term a reader needs is linked where a document first uses it, before the rest relies on
  it.
- Only when a word's meaning in the project is narrower than or different from its ordinary sense
  and another Module uses it is a concept declared.

  Any other word is explained in its owner's own document. Deciding which concepts exist is part
  of the Module's quality, not a formality.

### Context

- The Module's context holds every document and definition its Specs rely on. If the Module relies
  on a promise whose defining document its declarations do not select, the Module has a gap. An
  explicit selection repairs the gap. Reading outside the boundary never repairs it.
- When an evaluation needed a document it was not given, it names that document and why it needed
  it, instead of guessing its content.

## Architecture quality

Architecture quality is judged between Modules, from every Module's Specs read together.
It asks whether the division of the project into Modules serves both of the Protocol's purposes.
The first purpose is that a reader understands the project as a set of responsibilities that fit
together. The second purpose is that the boundaries built from those Modules fit the tasks the
project actually needs.

Each problem names every Module it concerns. A problem between two Modules concerns both. The
criteria fall into six dimensions.

### Responsibilities

- Each Module is drawn around one responsibility and one axis of change, as
  [Choosing Module boundaries](module.md#choosing-module-boundaries) explains:
  - A capability.
  - A use case.
  - A boundary with one collaborator.

  Things that change together are in one Module. A Module does not collect things only because
  they are the same kind of artifact.
- Each Module is cohesive. Its purpose can be said in one plain sentence. Every part of it
  serves that purpose. A Module whose parts change for unrelated reasons is two Modules.
- A typical change of the project needs the write sets of one Module, or of a few whose
  collaboration it changes, not slices of many.
- Siblings are drawn at comparable levels of abstraction. Each Module's Specs stay at one level.
  A Module that orchestrates others relies on their promises. It does not restate their internal
  steps.

### Ownership

- The following each have exactly one owner:
  - Every concept the project relies on.
  - Every promise the project relies on.
  - Every responsibility the project relies on.

  If two Modules promise the same thing or both describe themselves as responsible for the same
  decision, they overlap. One of them owns it and the other relies on it.
- Nothing the project relies on is left unowned. Each of the following is promised by some Module:
  - Every step of a main flow.
  - Every record several Modules share.
  - Every rule a guarantee depends on.

  A responsibility that every Module assumes another carries is a gap.
- A boundary between two Modules is clear. From their Specs alone, a reader can tell which Module
  promises any piece of behaviour in the project.

### Interfaces

- Modules are decoupled. A consumer relies on a few, stable promises of its provider, named where
  it can with `relies_on`. The consumer does not rely on any of the following of the provider:
  - Its internal structure.
  - Its records.
  - Its order of steps.
- An interface between Modules is narrow and defined by behaviour. Where it is shared, a contract
  defines it. Readable promises define it in every case. A consumer that could only work by knowing
  how its provider is built has an interface that is too wide.
- A consumer's account of what it relies on agrees with what the provider actually promises.

### Dependencies

- Every reliance is declared. A Module whose Specs rely on another Module's promises declares
  `uses` of it. A dependency stated only in prose, or only visible in the code, is undeclared. Its
  impact on the consumer cannot be derived from declarations.
- The direction of each dependency is sensible: it follows who relies on whom. A general Module
  does not depend on a specific consumer in order to serve it. A provider does not gain a relation
  to a consumer only so that its own Specs can describe that consumer's use.
- Mutual `uses` between two Modules are acceptable, because two Modules may rely on each other's
  promises. A cycle of `uses` alone is not a problem. Each reliance is judged on whether:
  - The reliance is real.
  - The reliance is declared.
  - The reliance is explained.

### Failure containment

- For each of these cases, each Module states how it reacts and what its own consumers then
  observe:
  - A collaborator it relies on fails.
  - A collaborator it relies on refuses.
  - A collaborator it relies on is unavailable.

  A failure crosses a boundary between Modules as a stated outcome, never as undefined behaviour
  of the consumer.
- A Module's failure cannot silently corrupt another Module's state or promises. Where a failure
  leaves work half done, the Spec says which Module detects it and how it is recovered.

### Consistency

- Promises that several Modules make about the same thing agree. Wherever it appears, each of the
  following is described the same way:
  - The same record.
  - The same limit.
  - The same state.
  - The same flow.
  - The same term.

  A statement in one Module never contradicts its owner's.
- Unless a Spec explains the difference, the same kind of problem is solved the same way across
  Modules:
  - Errors are reported alike.
  - Identities are formed alike.
  - Repeated invocations are handled alike.
- A parent explains how its children together fulfil its responsibility. What it says of each
  child agrees with that child's own Specs.

# Module entry template

A starter for `module.md`. Begin with [Spec writing guidelines](../writing.md). Use both parts:
[Required format](../format.md) for structure and syntax, and [Writing guidance](../module.md) for
what the entry must explain. Satisfying this shape establishes nothing about meaning.

The Protocol requires no section of an entry. The headings below follow the recommended reading
order:

- Purpose.
- Core concepts.
- Overview.
- Details.

As the Module's reader needs, adapt the headings in any of these ways:

- Rename them.
- Merge them.
- Split them.

Give the details whatever headings suit the Module.

Register the entry in the project registry. Write its paired `.md.json` with:

- `schema_version: 3`.
- `document.role: module`.
- The `module` block.
- Explicit `defines` and `relations` arrays.

Declare the Module's concepts as entries of the project glossary. The
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
owns, and `concept.thing`, which the provider owns. A reader of Example receives both definitions.
The anchor `concept.example-record` holds the extended explanation the glossary entry names, in the
entry of its owner rather than in a separate topic.

The overview diagram is checked. It answers one question: how Example is built and how it meets
its provider. The labels resolve as follows:

- `Example` and `Provider` resolve to Module titles.
- `Example service` and `Example
record` resolve to this Module's nodes.
- `src/example/` resolves to the entry the service binds.

Nesting asserts that Example owns both nodes. Nesting also asserts that the service binds its
entry. The labelled edges match the `relates` declarations below. The unlabelled edge between the
two Modules matches the `uses`. A Module with more structure may draw its inside and its outside
in two diagrams. Checked diagrams use only the D2 semantic subset and declared static relations.
The look is the publisher's.

The workflow is `d2 illustrative`. Its steps and progression explain behaviour, not declared
static relations. Its lanes show who does each step. An edge between lanes is a hand-off, which
is why a process among several participants needs no sequence lifelines. Illustrative views carry
no authority beyond the surrounding prose. Illustrative views never substitute for declaring
load-bearing collaborations. How the Module fits with the rest is part of its explanation, not a
separate list of relationships.

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

The `uses` entry selects the provider's entry and the document explaining `concept.thing`.
This selection satisfies the context requirement of relating to `module.provider`. Because the
provider Module's title is `Provider`, the `Provider` label in the diagram resolves.

## Glossary entry

Example's concept is an entry of the project glossary. The glossary entry names Example as its
owner and the anchor above as its explanation:

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
internal verification situation. It is not any of these:

- A separate Spec kind.
- A document owner.
- A context filter.

Define it only in an `implementation` document, never in `module.md` or a `module`-role topic.
Register the reading path. Write its paired metadata with `schema_version: 3`, the owner's
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

When situations differ in any of these outcomes, write separate scenarios:

- Successful outcomes.
- Failed outcomes.
- Repeated outcomes.
- Concurrent outcomes.

Put a situation's guarantees in its own steps or explanation. Define a Module-wide obligation once
as a requirement and link to it.

Identities stay stable across title and path changes. A test names the scenario identity **in the
test source**. Reading content never lists verifying tests. Publication exposes the identity as an
anchor.

Querying a scenario selects its owner's entire context, including both members of every owned and
selected document. It never trims to this fragment. It never selects the consumer that happened to
read it.
