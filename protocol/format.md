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
