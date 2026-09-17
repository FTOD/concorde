# Required format

Protocol 9 separates complete content from its human-readable subset and assigns each document
unit an explicit explanatory or precise-specification role. This chapter defines the
representation of both. It does not define a documentation site's navigation or layout. Templates
are starters; satisfying syntax does not establish semantic completeness.

## Document units

Each registered document is a pair: the explicit project-relative Markdown reading path and that
same path with `.json` appended. For example, `checkout/module.md` and `checkout/module.md.json`
are one unit, not two documents. A Module registers a nonempty `documents` collection with exactly
one local `module.md` entry. Registration of a reading path registers its exact companion; no
filesystem discovery or Markdown link expansion is permitted.

Reading files are nonempty UTF-8 Markdown. Metadata files are UTF-8 JSON with unique keys and no
non-JSON numeric constants. Paths use canonical project-relative POSIX spelling: no absolute paths,
backslashes, empty, dot or traversal components, control characters or symlink aliases. Physical
source aliases and multiple ownership are invalid. Both members have one identity and owner and
must be included together in context, source digests, proposals and ownership reconciliation.

## Reading structure

The first five level-2 ATX headings of `module.md`, outside fences, are exactly once and in order:

```text
Purpose
Terminology
Usage
Design
Relationships
```

A level-1 title and brief navigation may precede them. Purpose contains nonempty plain prose, not
lists, tables, nested headings or fences. Invisible identity anchors are allowed. Usage, Design and
Relationships each contain explanatory prose, not only links, headings or diagrams. Relationships
contains at least one Mermaid flowchart for the principal collaboration. Honest unknowns are stated
explicitly; the presence of prose is not proof that its explanation is sufficient.

Every module-role topic starts with a short orienting introduction followed by `## Terminology` as
its first level-2 section; the entry puts Terminology immediately after Purpose. There is exactly one
Terminology section, with a nonempty two-column Markdown table headed `Term` and `Meaning / definition`.
A term is either defined plainly in its row or linked to its canonical table by a relative Markdown
link ending in `#terminology`. Imported rows say where the term is defined rather than copy its
meaning. Qualify distinct meanings instead of merging them. Do not list files, implementation IDs or
all declared entities to fill the table. If no specialized terms are needed, state that explicitly
instead of inventing rows. Implementation-role units MAY use the same convention for orientation.
The heading publishes the stable `terminology` anchor. Necessary linked tables must belong to the
owner's complete selected context; they do not expand it implicitly.

`module.md` has role `module`. Its additional sections and module-role companions explain topics,
rationale, correct use and unresolved facts. They MUST NOT contain formal `req.*` or `scenario.*`
definitions or canonical `concorde-contract` fences. Usage examples and links to precise definitions
are permitted. A topic remains an explanation owned by its Module, not a nested specification owner.

Role `implementation` contains the Module's formal requirements, scenarios and canonical interface
contracts. Units may group definitions by subject without creating a second ownership hierarchy.
Both roles are registered, paired human-readable Spec content. Topics need no full entry template
beyond early Terminology. Required exact private APIs, serialization rules, implementation algorithms
and executable Flow catalogs belong in implementation-role reading regardless of their syntax.
Conceptual design and safe-use explanations stay in module-role reading. Implementation details that do not constrain behavior or significant
design do not become obligations merely by appearing in code. The former `Usage & Contract`,
`Architecture & Realization` and standalone `Entities` entry structure is not admitted.

Machine management blocks `concorde-document`, `concorde-entities`, `concorde-dependencies` and
`concorde-contract-binding` are not reading declarations. They must be migrated to metadata with
readable meaning references. Examples inside enclosing fences remain opaque. Interface schemas,
examples and `concorde-contract` definitions remain human-readable content; canonical definitions
belong in implementation-role units. Fenced examples of Spec syntax do not declare definitions.

## Metadata representation

The companion has these required fields and optional `extensions`:

```json
{
  "schema_version": 2,
  "document": {"id": "document.checkout.module", "owner": "module.checkout", "role": "module"},
  "entities": [
    {"id": "entity.checkout.service", "title": "Checkout service", "kind": "program",
     "meaning": "#entity.checkout.service", "files": ["src/checkout/"], "pending": []}
  ],
  "dependencies": [
    {"target_id": "module.inventory", "meaning": "#inventory-collaboration"}
  ],
  "bindings": [
    {"id": "contract.inventory.reserve", "version": 1, "role": "required",
     "peer": "module.inventory", "meaning": "#reservation-participation"}
  ]
}
```

`schema_version` is the integer 2. `document` has exactly `id`, `owner` and `role`. Identity and
owner agree with registration; `role` is exactly `module` or `implementation`, with no implicit
default. The unique `module.md` entry MUST have role `module`. Unknown/missing roles, version-1
metadata and an implementation-role entry require explicit migration and are invalid. The three
declaration arrays are explicit and may be empty. There is no `main_visible` property: both roles
remain Protocol reading content. The retired `concorde.publication` classification extension MUST
NOT be used: publishers derive classification from `document.role`, not a competing role declaration.
`extensions`, if present, is a nonempty object keyed by stable names. An implementation must define
and validate the extension vocabulary it uses; an extension cannot change Protocol ownership,
inclusion or the required reading subset. Essential meaning cannot be hidden in extension payloads.

### Identities and readable anchors

Module, document, entity, requirement, scenario and canonical contract IDs are project-wide unique
and match `^[a-z][a-z0-9]*(?:[.-][a-z0-9-]+)*$`. Requirements additionally start with `req.` and
scenarios with `scenario.`. Prefixes do not establish ownership. Titles and paths may change without
changing identity. Participant bindings use an existing contract ID, not a new definition.

A readable anchor is either a standalone `<a id="identity"></a>` before its explanation or an
ATX heading with a trailing `{#identity}`. Requirement/scenario headings supply their ID directly.
A heading cannot redirect a definition to a different ID. Anchors are unique in their document,
outside fences. Adjacent anchors on one standalone line can identify several entities explained together by the
following prose. Separate anchor lines delimit separate explanations. All of those entities must actually be
explained; an empty or unrelated paragraph is a semantic gap.

A heading anchor extends to the next heading of the same or higher level; a standalone anchor
extends to the next heading. Either ends at the next anchor group. A metadata `meaning` is a
nonempty local `#anchor`, never a URL or another document path. It resolves to nonempty readable
explanation in this unit, without following links. Required context inclusion for links within that
explanation is checked separately.

### Entities

An entity has required `id`, `title`, `kind`, `meaning` and optional `files`, `pending`, `target_id`.
Title and kind are nonempty strings; titles are unique within the Module. Its readable meaning
anchor is its stable ID. Files, when present, are a nonempty unique list of exact project-relative
paths or directory prefixes ending in `/`; `pending` is a unique subset of those entries.
No two entities in a Module list the same entry. More specific overlapping entries determine file
ownership. The union equals the registry listing entry for entry. Existing exact entries are files;
existing directory entries are directories. Non-pending entries must exist.

A Module entity's `target_id` names one direct child or used Module. Such an entity has no `files`
or `pending`. Every direct child and used provider has exactly one such local entity. Other
entities may be concepts, records, interfaces or external actors without implementation bindings.
Entity meaning is reading prose, not a `responsibility` string copied into metadata.

### Dependency explanations

Each dependency record has exactly `target_id` and `meaning`. Across the owner's collection the
provider set equals the union of its direct uses and children, each once. The pointed reading
explains responsibility, when the collaboration applies, canonical guarantees relied upon and
local duties/reactions. It should link to provider definitions in the explicitly included context,
not copy their schemas. A provider both used and contained has one local agreement.

### Participant bindings

A binding has exactly `id`, `version`, `role`, `peer`, `meaning`. Version is a positive integer;
role is `provided` or `required`; peer is a Module ID or nonempty `external:<name>`. The local
explanation states participation conditions, relied-upon guarantees and obligations. It does not
repeat the canonical schema, example or common semantics. Participant/peer/role bindings are unique
across the owner's collection. Internal peers require complementary roles for the same ID/version,
with mutually named participants; external peers require no project-owned counterpart. Every
participant's complete context includes the exact canonical definition version.

## Requirements

In an implementation-role unit, a definition is a level-2 through level-5 ATX heading `req.<identity> — Title`, followed by a
statement. A spaced en dash or hyphen is also accepted. The first paragraph is one sentence with
uppercase SHALL or SHALL NOT exactly once. A requirement section ends at the next heading of any
level and has no nested heading. It cannot be defined inside a scenario. Subsequent paragraphs,
lists and fences explain the statement; a list item beginning with a requirement ID is invalid.

## Scenarios

In an implementation-role unit, a definition is a level-2 through level-5 ATX heading `scenario.<identity> — Title`, with the same
dash choices. Its section ends at the next heading of any level and has no nested heading. Every
list item in that section is a step beginning with GIVEN, WHEN, THEN, AND or BUT and a space.
The first step is GIVEN or WHEN; at least one WHEN and one THEN are required. AND and BUT continue
the preceding kind. A sequence never returns to an earlier kind. Prose may explain the situation.
Requirements and scenarios belong to the sole owner of their defining unit.

## Canonical structured contracts

An implementation-role unit's `concorde-contract` JSON fence defines exactly `id`, `version`, `schema`, `semantics`, `example`.
The version is a positive integer, semantics is nonempty, and the example satisfies the schema.
The tool's schema vocabulary is explicit and offline: schema references cannot load Spec units or
remote resources. The contract ID has one canonical definition; its anchor is exposed in reading.
Inputs, outputs, effects, failures, compatibility and related scenarios must be explained in the
resolved readable context, not inferred from shape alone. No role or peer appears in a definition.
Behavior or schema changes increment the version and reconcile affected bindings atomically.
Editorial changes still invalidate byte-bound evidence without requiring a behavior-version bump.

## Relationship diagrams

The reading entry's `## Relationships` section contains Mermaid fences beginning with `flowchart`
or `graph`, with one statement per line in an authoritative relationship view. A diagram's node
labels form a nonempty subset of the Module's own entity titles.
A shaped node's first label line (before `<br/>`) is its title; an unshaped node uses its identifier.
Edges are labeled `A -->|label| B` or `A -- label --> B`, with the supported Mermaid arrow styles.
Every relationship edge has a nonempty label. The surrounding prose states the diagram's scope;
additional diagrams can cover other scopes without duplicating inventory. Accessible `accTitle`
and `accDescr`, grouping and styling are supported; their rendering is not another authority.

## Links, references and verification

Ordinary Markdown links navigate to readable definitions. A stable-ID fragment must name the actual
definition in the addressed reading document. Publishers expose these anchors and keep links as
links, not transclusion. Other heading fragments use the renderer's slug rules. A link never adds
a file to agent context; Module registration's explicit references are the sole inclusion authority.

Each Module declares an explicit reference array. A context reference has exactly `kind` and `id`,
with kind `module` or `document`. An external reference has exactly `kind: external` and `path`,
naming existing vendored material. Duplicate references, self selections, wrong kinds and unknown
IDs are invalid. Overlapping module/document references deduplicate the paired sources while
retaining all reasons. Only the selecting Module's references expand, once.

A test declares verified scenario IDs in the test, in a syntax documented by its development tool.
Tools read these declarations without executing tests and reject unknown scenario IDs. Reading
content contributes no test locations. Derived coverage and reverse file indexes are evidence,
not another source of specification obligations.

## Drafts and migration

Unresolved facts are explicit gaps. Templates do not invent behavior or establish completeness.
Migrating Protocol 8 requires adding early, canonical Terminology tables, editing explanation for
readers without implementation knowledge, and separating remaining technical contracts from topics.
Keep important operational risks visible; preserve exact obligations, IDs and executable diagrams
while reconciling relocated anchors and explicit references. Metadata schema 2 is unchanged.
For older projects, migrating Protocol 7 additionally requires explicit schema-2 roles for every unit, moving all formal requirements,
scenarios and canonical structured contracts out of entries and explanatory topics into Module-owned
implementation units, and removing publisher-specific classification extensions. Preserve definition
IDs, Module ownership and valid obligations; retain coherent explanatory meaning in topic documents.
If a unit is split, the retained unit keeps its document identity and each new unit gets a new one.
Update references to include moved definitions explicitly; links alone cannot repair context.
Moving a definition does not change interface behavior or require a behavior-version increment. It also reconciles owned
pairs, reference sets, links, file exclusions, context digests and affected evidence. A format
migration is an explicit project change, never an installer's silent reinterpretation. Registry,
Framework configuration and worker-wire versions are separate implementation compatibility gates.
