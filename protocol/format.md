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

A readable anchor is either a standalone `<a id="identity"></a>` line before its explanation, or an
ATX heading carrying a trailing `{#identity}`. Requirement and scenario headings supply their
identity directly. Anchors are unique within their document and outside fences. A heading anchor
extends to the next heading of the same or higher level; a standalone anchor extends to the next
heading; either ends at the next anchor group.

Adjacent anchors on one standalone line identify several nodes explained together by the following
prose, and that prose MUST explain all of them.

## Reading structure

The first level-2 headings of an entry `module.md`, outside fences, are exactly once and in order:

```text
Purpose
Terminology
Usage
Design
Relationships
```

A level-1 title and brief navigation may precede them. Purpose is nonempty plain prose: no lists,
tables, nested headings or fences. Usage, Design and Relationships contain explanatory prose, not
only links, headings or diagrams. Honest unknowns are stated explicitly.

A `module`-role topic begins with a short orienting introduction. When the topic defines or imports
a concept, its first level-2 section is `## Terminology`. In the entry, Terminology always follows
Purpose; it may hold only prose when the entry defines and imports nothing.

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

A Mermaid block in reading is either a **checked flowchart** or marked `illustrative`. The rules are
in [Views](views.md).

## Links

Ordinary Markdown links navigate to readable definitions. A stable-identity fragment MUST name an
actual definition in the addressed reading document; other fragments use the renderer's slug rules.
A link never adds a document to context.

## Evidence declarations

A test declares the scenario identities it verifies in the test source, in a syntax documented by
the development tool. Tools read these declarations without executing tests and reject unknown
identities. Reading content MUST NOT contain that syntax outside fences, list test locations or
prescribe coverage declarations.
