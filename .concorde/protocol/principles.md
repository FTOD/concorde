# Spec Protocol principles

Concorde Spec Protocol 9.0.0 defines Module specifications, their complete content and the subset
intended for human reading. It applies to project Specs, including those of software implementing
this Protocol. The standard's own chapters need not describe themselves as software Modules.

## Requirement language

**MUST** is required for conformance; **MUST NOT** is prohibited. **SHOULD** is recommended and may
be departed from for an explained reason. **MAY** permits a choice. Examples prescribe neither
project names nor business behavior.

### P1. A Module has one complete specification and a readable subset

A **Module** is one cohesive software responsibility, not necessarily a package, directory, service
or process. Its realization may span or share physical units or be supplied entirely by children.
Its purpose, behavior, concepts and relationships establish its boundary; file bindings locate its
realization and do not establish that boundary.

Let `Content(M)` be the complete specification content owned by Module M and `Reading(M)` its
human-readable content. **Reading(M) is a subset of Content(M)**. The Protocol defines membership
and completeness of both, not a docsite's layout. Reading is not an independently maintained
summary, a weaker contract or whatever a renderer chooses to retain.

Reading content MUST explain:

- **Purpose:** responsibility, intended consumers, scope and relevant non-goals.
- **Terminology:** the concepts needed to understand this document, introduced before detailed use.
  Define a term once in its canonical Terminology table; elsewhere link to that table instead of
  repeating a definition. This is a reader aid, not an entity inventory or file-binding declaration.
- **Usage:** when and how to use the Module, concepts and prerequisites, actual entry points,
  inputs, results, effects, errors and applicable repeat, cancellation and compatibility behavior.
  Start with a coherent explanation rather than asking readers to assemble instructions from formal
  statements. A logical responsibility MUST NOT invent an executable interface to fill a template.
- **Design:** responsibility decomposition, collaborations, significant control/data flow and state,
  internal invariants, constraints, choices and how they support the guarantees. Intended design
  is not proof that existing code conforms. A diagram or inventory is not a design explanation.
- **Relationships:** what the participating entities mean, how they collaborate, and the distinction
  between structural composition and capability use. Explain conditions and reactions that arrows
  cannot express. A scoped diagram is not required to reproduce the entire entity inventory.
- **Precise obligations:** Module requirements, concrete scenarios, interface definitions and the
  local duties and relied-upon guarantees of collaborators. Infrequent failures, concurrency,
  security and compatibility promises remain readable even when they are not on the initial path.

Identity, ownership, registration, implementation bindings and pending markers are machine
metadata, not mandatory reading. Their mechanical records MUST NOT be mixed into the reading
body. Metadata MUST refer to readable meaning rather than become the only place an essential
responsibility or obligation is stated. This distinction is about information, not syntax:
interface schemas and examples can be reading content; a file listing written as a Markdown table
is still implementation metadata. A publisher MAY expose metadata as an auxiliary inspection view.

The complete Module specification has two explicit document roles, both within Reading(M):

- **Module Specs** (`module`): the reading entry and explanatory topic documents. The entry follows
  **Purpose, Terminology, Usage, Design, Relationships**. Topics explain concepts, correct use, collaborations,
  significant design and important guarantees. Together these explanations MUST establish a usable
  mental model without requiring readers to reconstruct it from formal definitions. They MUST NOT
  become empty link indexes or independently maintained summaries.
- **Implementation Specs** (`implementation`): the precise normative requirements, scenarios and
  interface contracts that implementations must satisfy, including external behavior and internal
  constraints. They are not implementation source, temporary plans or descriptions of incidental code.

Formal requirement and scenario definitions MUST occur only in implementation-role document units.
The entry and module-role topics MUST NOT define them. Canonical structured interface contracts
MUST also be defined in implementation-role units; explanation, usage examples and links to those
contracts belong in Module Specs. Define each precise obligation once. Explanations retain important
meaning and link to its exact definition rather than duplicating a second formal contract.

The intended reader understands general software concepts but does not know the project's
implementation, internal type names, execution library or migration history. Explanatory reading
MUST let that reader explain the problem, when to use the Module, a normal interaction, its result,
important stopping conditions and why the design works. Purpose uses ordinary verbs before internal
names. Usage presents a representative normal path before exceptional recovery. Illustrative examples
SHOULD make abstract distinctions concrete; they explain existing promises, not invent new ones.

Role separation is about meaning, not just heading syntax. Exact private APIs, wire fields, byte
algorithms, persistence layouts, internal limits and executable-node/state catalogs belong in
Implementation Specs even when written as ordinary prose without SHALL or scenario headings.
Module Specs retain architecture, design reasons, actual public entry points, and any limits or
hazards a consumer needs for correct use. They MUST NOT hide destructive defaults, security limits
or known unfulfilled guarantees behind detail links. A simple usage example is not an API inventory.

Design MUST connect a decision to the problem it solves and the guarantee it supports, not merely
list implementation calls in order. Conceptual diagrams SHOULD answer one reader question with
recognizable labels. They MUST be distinguished from exact executable diagrams; the latter belong
in implementation-role units and remain the single authority for execution topology. A concept view
must not become a competing executable model. Explain relevant collaborations locally, but do not
repeat generic permission, compatibility or completeness disclaimers on every path. Historical
migration records MUST be labeled with their baseline and kept apart from the default explanation
of current behavior; preserve any still-applicable obligations in the current specification.

Terminology tables MUST contain only concepts relevant to the page. A local definition uses familiar
language rather than another chain of unexplained terms. An imported term links directly to its
canonical document's Terminology table; an intermediate glossary that only forwards the reader is
not its definition. Table links grant no context: required defining units must be explicitly included.
Entity identities and realization bindings stay in metadata; Design and Relationships explain how
particular entities participate. A glossary neither duplicates those declarations nor replaces that
contextual explanation. Identical words with distinct meanings must be qualified explicitly.

Both roles belong directly to the same owning Module. A topic such as Registry is an explanation,
not a new owner, sub-Module or requirements container. Implementation Specs MAY be split into several
owned units and grouped by subject, but requirements and scenarios remain Module-owned. Roles
MUST be explicit metadata, never inferred from paths, headings, body syntax or publishing preferences.
Roles change neither complete context inclusion nor execution authority. There are no mandatory
usage/architecture wrappers or standalone entity-inventory chapters.

A **requirement** is one decidable Module-wide SHALL statement with a stable identity. A **scenario**
is one testable situation expressed through GIVEN, WHEN and THEN steps. A situation-specific
obligation belongs in its scenario, not in a second attached requirement. Both external behavior
and internal constraints are normative where prescribed. Define each obligation once and link to
it; editorial organization MUST NOT silently weaken, duplicate or contradict it.

**Entities** are named programs, records, concepts, interfaces, files, Modules or boundary actors.
Their identities and bindings are metadata; their meaning belongs in reading prose. **Relationships**
are directed edges with meaningful free-text labels, preferably verbs. An interface is an entity
whose behavior is specified by readable definitions and scenarios, not another Spec kind.

The Module model is recursive. A Module has at most one structural parent; composition is acyclic.
Using a provider does not acquire it as a child. A capability shared by consumers has one identity
and is a sibling of those consumers. Missing or inapplicable facts MUST be stated honestly, not
invented from code, examples or template placeholders.

### P2. Implementation bindings are metadata, not reading or implicit code access

An entity MAY bind exact project-relative files or directory prefixes. A prefix binds every regular
file below it, including future files, under a tool's explicit deterministic exclusion rule. The
Module's implementation listing is the union of its entities' entries. It records realization,
not a promise omitted from reading content or permission to inspect the files.

Within a Module each entry belongs to one entity. When entries cover the same file, an exact entry
wins over a directory, and a longer directory prefix wins over a shorter one. Several Modules MAY
bind the same implementation; each retains its own identity and contract, and changes concern all
listing Modules. No document-unit member, generated output or project-control record may be bound
as implementation; a directory binding MUST NOT contain a document-unit member.

A pending marker names an intended entry that does not yet exist. A non-pending entry MUST exist.
Pending is intent, not evidence. File contents and external material remain separately authorized.

Tests are implementation files. A test names the scenario it verifies; reading content MUST NOT
list verifying tests or prescribe coverage declarations. A tool derives coverage from those test
annotations without executing them. Metadata may bind test files like other implementation files.
Missing coverage does not cancel a promise, and a declared test is not proof of fulfillment.

### P3. A Module resolves complete document units

Each Module MUST have a stable identity and a nonempty owned `documents` collection with exactly one
local `module.md` reading entry. Each registered **document unit** has one stable document identity,
one owner and two source members: reading Markdown and its associated metadata. Registering the
reading path registers the pair. Neither member is independently owned or included.

The Module separately declares `references`: another Module's whole owned collection, one document
unit by stable identity, or existing project-relative vendored external material pinned at a known
revision. References select knowledge, not ownership, composition, dependency, implementation or
permission. Only the selected Module's references expand, once. Referenced Modules' references,
Markdown links, neighbors and directory structure MUST NOT expand the context.

The complete Spec context is the deduplicated union of all owned and directly referenced units,
with **both source members available whole**. Reading content is a subset of this context, never a
replacement for it. External references and implementation contents remain outside Spec context.
A tool MUST provide all admitted sources and no sources outside its explicit grant, whatever file
delivery mechanism it chooses. A scenario query resolves its sole owner and then that owner's
complete context; it never trims to the scenario or selects the consumer that happened to read it.

The resolved reading subset MUST explain purpose, correct use, design and obligations without
undeclared reading or source code supplying missing meaning. For every child and direct dependency,
state responsibility, use conditions, canonical promises relied upon and local obligations/reactions.
Necessary provider definitions must be included through explicit references; use ordinary links,
not copies or transclusion. Included entities keep their owner and do not join the consumer's local
entity inventory, diagram or implementation listing.

Record exact source-byte digests, member roles, document identity, owner and inclusion provenance,
and bind the selecting registration to the context identity. Changing metadata alone invalidates
dependent context and review evidence just as changing reading does. Identity links MUST continue
to reach canonical readable definitions after publication. Missing meaning remains an attributed
gap; a reader MUST NOT silently fetch more files to repair it.

### P4. Conformance covers content, reading, structure and consistency

A conformance claim identifies its Protocol version. Stable identities, unique unit ownership,
complete paired source inclusion, explicit document roles and definition placement, explicit
one-level references, consistent declarations, required reading structure, one statement per requirement and consistent file listings are structural
requirements. Complete and mutually consistent readable obligations, design and relationships,
including decidable requirements and an explanation usable without implementation knowledge, are
semantic requirements. Readability review checks the stated reader's questions, terminology,
normal-path order, concrete examples, causal design and visible safety limits. It is not a word-count
gate or a preference for shorter prose. A correctly named section or table cannot prove understanding.

Passing shape checks, headings, diagrams or coverage checks cannot establish semantic completeness
or implementation conformance. Reading must not hide necessary guarantees in metadata, while
metadata must not override prose or silently infer relationships absent from the registry.

The [Required format](format.md) defines representation, and templates provide starters, not proof.
A tool's configuration version, registry serialization, worker wire types, execution policy and
context delivery are separate agreements. Tools MUST preserve the content model and its reading
subset, identities, ownership, inclusion, relationships and obligations. The Protocol does not
prescribe docsite pages, sidebars, tabs, themes, folding or interaction behavior.

# Spec management

Spec management identifies and relates complete Module specifications independently of a publisher.
It separates document ownership, context inclusion, composition, dependency and implementation
listing. The [Required format](format.md) specifies their representation; [Spec and Context](spec-management/spec-and-context.md)
defines exact source selection.

## Document units and ownership

Every Module owns a nonempty collection of registered reading paths, including exactly one local
`module.md` entry. Each reading path registers its paired `.md.json` metadata source. The unit has
one stable document ID and one owner, recorded in its metadata and consistent with registration.
The two members cannot have different owners or be referenced independently. Aliases, duplicate
ownership, duplicate IDs, unregistered members and missing partners are invalid.

Every unit declares role `module` (entry or explanatory topic) or `implementation` (precise
specifications). Requirements, scenarios and canonical structured interfaces are defined only in
implementation-role reading; entity declarations bind identities to readable meaning in either role.
All belong directly to the Module owner of their defining unit, not to a topical page or group.
Roles are document organization, never structural parentage, Spec kinds or context filters. A document relocation or title change does not itself change identity. Links
use the reading path and the definition ID as fragment; a publisher must expose those anchors.

Reading membership is defined by the Protocol, not a visibility preference. All reading members
are human-readable specification content. Metadata remains part of the complete content and
context, even when a site omits it from its main page. Presentation does not select agent knowledge.

## Registration and references

A registry distinguishes these facts:

- `parent`: at most one structural parent, with acyclic composition.
- `uses`: directed capability dependencies, not ownership.
- `documents`: solely owned document units named by their reading paths.
- `references`: explicitly included Module collections, individual document units or external material.
- `files`: the union of local entity implementation entries, exact paths and directory prefixes.

These relations are independent. A filename, path, display title, diagram edge or ordinary prose
link must not create one implicitly. Registry serialization is a tool agreement; it must preserve
the Protocol's meanings and required declarations.

```json
{
  "id": "module.checkout",
  "documents": ["checkout/module.md", "checkout/scenarios.md"],
  "references": [
    {"kind": "module", "id": "module.inventory"},
    {"kind": "document", "id": "document.delivery-terms"},
    {"kind": "external", "path": "reference/payment-sdk/"}
  ]
}
```

A Module reference includes all units owned by that Module, not its references. A document
reference includes exactly that unit's two members. Self references and duplicate kind/identity
pairs are invalid; overlapping Module/document references are allowed, supply each source once and
retain every inclusion reason. Cycles terminate because expansion is not recursive. Only the
selected Module's external references are granted separately; included providers do not bring theirs.

## Entity identity and realization

Metadata gives each entity a stable ID, title, free-text kind and local readable `meaning` anchor.
It does not carry another copy of that meaning. An entity can be a program, record, interface,
concept, actor, child or used Module. Titles are unique within a Module so diagram labels resolve.
Meaning must be understandable where it occurs in Design, Usage or collaboration explanations;
an inventory is not mandatory reading and cannot replace those explanations.

An entity may bind exact implementation files or directory prefixes with optional pending markers.
The Module listing equals their union. Within the Module an entry belongs to one entity and the
most specific covering entry owns a file. Several Modules may list one implementation without
merging contracts. Tests are ordinary implementation files whose own annotations name scenarios.
No document-unit member, generated output or control record can be bound as implementation, and a
bound directory cannot contain a Spec unit. Listing names never grants contents or write authority.

Every direct child and used provider is represented exactly once by a local entity with `target_id`.
That entity lists no implementation files: the provider's files stay with the provider. External
libraries are entities without local provider identities; their vendored material is an external
reference, not an entity's implementation listing.

## Local collaboration agreements

A dependency metadata record names the provider and a local readable explanation. For every child
and direct use, this explanation states responsibility, selection conditions and the canonical
promises relied upon, together with the consumer's own duties and failure reactions. A relationship
edge alone is insufficient. The declaration set agrees with registered children/uses exactly.

Necessary provider definitions must occur in the selected context through explicit references.
Ordinary links identify them but do not include them. Prefer links and local explanations of reliance
to copied common schemas or promises. Dependency conditions are behavioral meaning, not routing
commands or grants to read a provider implementation.

## Shared interfaces and participants

An interface remains a local entity with one canonical readable contract in an implementation-role
companion unit owned by one Module and referenced by many. Each canonical contract has a stable ID,
positive version, offline schema, semantics and conforming example, plus readable behavior and
scenarios. Definition ownership need not equal every provider's identity.

Participant metadata selects that exact ID/version, a provided/required role and a peer, and refers
to local readable participation conditions, guarantees and obligations. A binding cannot override
the definition or repeat its schema/example/common meaning. Every participant includes the canonical
definition version. Internal peers declare complementary roles with mutually named participants;
external peers require no local counterpart. Duplicate participant/peer/role bindings are invalid.
Structural matching does not prove behavioral compatibility.

Changing a canonical unit affects its owner and every direct context consumer, including consumers
that reference the entire owner Module. A behavior/schema change increments the contract version and
reconciles bindings atomically. Editorial changes, metadata-only edits, changed references and
ownership changes also invalidate byte-bound context and review evidence. Ownership transfer keeps
IDs stable and reconciles both source members, registrations, references, links and bindings together.
Publication shows a canonical definition once, with owner/reference navigation rather than copies.

## Relationship views

The authoritative authored relationship views are Mermaid flowcharts in the reading entry's
Relationships section, with explicit scope and labeled edges between declared local entities.
A view may omit irrelevant inventory entities; additional views can explain another collaboration.
Provider definitions included as context do not expand the local diagram or entity inventory.
Composition remains the registry's parent relation and dependency remains its uses relation; prose
and diagrams must agree with them rather than establish alternate structural ownership.

A tool may derive diagrams, navigation and indexes from these declarations. Such output is not
another authored model. The Protocol specifies readable meaning and identity preservation, not
website pages, sidebars, themes, folded panels or visual interaction.

## Versions, evidence and gaps

A project identifies the accepted Protocol version separately from its own interface versions,
registry serialization and development-tool configuration. Exact content digests can additionally
bind sources and evidence. Metadata and reading must form one consistent model: neither silently
overrides the other. A correctly shaped record cannot prove complete meaning.

Missing necessary behavior is a semantic gap even when all files exist and all references resolve.
A reader names that gap instead of reading outside its granted context or inferring promises from
code. Test-declared coverage and reverse implementation indexes remain derived evidence, not Spec
content or permission to widen the selected task.

# Spec and Context

A Module is the unit of complete Spec context selection. A scenario query first resolves its sole
owner and selects that Module. Reading is the Protocol-defined human-readable subset of content,
not an additional query kind, a summary substitute or an execution grant.

## Exact source selection

Let `D(M)` be the document units owned by M, `R(M)` its explicit references, and `members(U)` the
reading and metadata files of unit U. A Module reference includes its owned units; a document
reference includes exactly the identified unit. External material is selected separately.

```text
Units(M) = D(M) union (union of include(r) for r in R(M) when r is a context reference)
Context(M) = union of members(U) for U in Units(M)
ReadingContext(M) = the reading member of each U in Units(M)
Context(scenario S) = Context(owner(defining_unit(S)))
```

Only `R(M)` expands. Never recursively resolve a provider's context. Neither links, parentage,
uses, directory neighbors, entity target IDs nor implementation bindings add sources. Each selected
unit contributes both exact members, even when a publisher puts its reading on an auxiliary page.
No excerpt, summary, diagram export or reading-only projection replaces a complete unit.
`D(M)` includes both module-role explanations and implementation-role precise specifications.
A document's role never filters this union, including during discovery, planning or Spec review.
Implementation Specs are Spec context, not the separately authorized implementation source context.

```text
resolve(registry, query):
    find the unique selected Module or scenario owner
    validate registration, ownership, paths, kinds and source availability
    include each owned unit, reason = owned(Module ID)
    include each directly referenced unit, retaining its typed reference reason
    expand each included unit to its exact reading and metadata source members
    deduplicate sources and retain all sorted inclusion reasons
    return source records sorted by canonical project-relative path
```

Every record contains document ID, sole owner, path, source role (`reading` or `metadata`), exact-byte
SHA-256 digest and inclusion reasons. The selecting registration, including owned collection and
explicit references, is bound to context identity. Both members have the same owner, document ID
and inclusion provenance. Changing only whitespace, metadata, reference declarations or provenance
invalidates dependent byte-bound evidence even if the set of paths is unchanged.

Unknown IDs, wrong kinds, duplicate identities, unsafe or aliased paths, ambiguous ownership and
missing members fail without partial successful resolution. Identity lookup may inspect registered
metadata without reading unselected human bodies. Requirement, entity, contract, document and
heading anchors are addressable artifacts, not separate task-context query kinds.

## Visibility and delivery

The resolved context is the exact Spec visibility scope of a bounded reader. The tool must make
every selected source available whole and no unselected source visible. It may grant paths in place,
copy byte-identical members into a capsule, provide their bodies, or combine these mechanisms.
Delivery mechanism does not change membership, ownership, source identity or authority.

A tool may also provide task material derived from in-scope files, such as their changes since a
baseline. Such material adds no file and cannot replace complete sources. An agent that reads only
some granted files still received the complete context; missing meaning is judged against the full
scope, not against what that reader happened to open.

## Example: overlapping references

Checkout owns its entry and scenario units. It references Inventory's entire collection and also
Inventory's interface unit. Inventory owns its entry and interface and references Tax. Checkout
therefore receives four units, eight source members, with two reference reasons on both interface
members. Tax is absent. Querying an Inventory scenario selects Inventory's own context, including
Tax. Removing Checkout's redundant interface reference changes provenance and invalidates its
context identity even though its source paths are unchanged.

## Implementation context

Implementation context is derived only from local entity file bindings. Exact entries and files
below directory prefixes are resolved under an explicit deterministic exclusion rule. Metadata
records pending intent without pretending missing file contents exist.

```text
ImplementationContext(M) = union of bound files of locally owned entities
ImplementationContext(scenario S) = ImplementationContext(owner(S))
```

Neither reading nor metadata members belong to implementation context. A file shared with another
Module adds that Module to reverse-use metadata, not its Spec or implementation to the selected
reader's context. A Module with no bindings has an empty implementation context; this does not
prove it has no realization.

Implementation names and pending status are visible through admitted metadata. Contents are a
separate phase-specific grant. A tool may grant names for planning, read-only contents for review,
or writable contents for implementation, but never add unlisted files implicitly. Context inclusion
alone grants no write, command, credential or network authority. Test-to-scenario coverage is derived
from tests in implementation context, not from a second Spec-authored test list.

## External reference material

External references declare existing project-relative vendored library, service or tool material,
pinned at a known revision. They are neither specification promises nor implementation files and
cannot overlap a document unit or the selecting Module's implementation listing. They are never
pending. Only the selected Module's external references are considered.

```text
References(M) = union of readable files selected by M's external entries
References(scenario S) = References(owner(S))
```

A tool may exclude media and archives by a documented deterministic rule and record one tree digest
per external entry. The entries are metadata; their contents are separately authorized read-only.
An undeclared network fetch or installed dependency's sources must not substitute for declared
material. Missing necessary external knowledge is a gap, not permission to widen the grant.

## Changes and gaps

Source members stay paired for ownership, context and review. An owner-only authoring proposal may
change either or both members, but must be checked as one complete overlay before application.
Referenced units remain read-only. A metadata-only ownership or binding edit cannot evade affected
context review, stale-input checks or the prohibition on code writers changing Specs.

A missing definition is a semantic gap, even after successful structural resolution. Record the
needed promise, its owner when known, selected Module, context identity and blocked step. Do not
follow an included Module's references or a prose link to repair it. An additional explicit Module
selection is a new bounded context, not a retrospective claim that the old one was complete.

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

## Concorde Framework execution profile

This profile applies the independent Spec Protocol to Concorde's runtime. Framework configuration
uses `profile_version: 14` for the content/reading document-unit model and registry schema 5 for its JSON
storage. `.concorde/config.json` declares `profile_version`, `registry`, `protocol` and
`capability_configuration`. Its `protocol` binding identifies the accepted version and exact
manifest digest. These configuration and storage versions are Framework compatibility identifiers,
not additional versions of the specification language. Older configurations require explicit
migration; the runtime must not infer their meaning from paths or names.

### P5. One complete Module context per bounded task

A bounded invocation selects one Module and freezes four kinds of context. Its **Spec context** is
the Protocol's one-level union of complete owned document units and explicit Module references; scenario focus
does not trim it. Definitions in included documents retain their original owner. The Protocol
fixes which files are visible, not how they are delivered; this profile chooses the delivery. The
host delivers the Spec context as a **context index and grant**: the invocation's frozen record
lists both source members of every included unit with document identity, owner, source role, digest,
inclusion reasons and the reading entry; reading and metadata members themselves are granted read-only at their project-relative paths, copied
byte-for-byte into a capsule when the phase has no project workspace. No Spec document body is
embedded in an invocation's input, so an invocation pays only for the documents its task opens;
the agent opens the granted files with its own tools, starting from the reading entry, and nothing
outside the grant is readable. Its
**implementation context** is the Protocol-defined set of files bound by the Module's entities:
their exact entries plus every regular file below their directory prefixes, excluding directories
named `node_modules`, `__pycache__`, `.venv`, `build` or `dist`, directories and files whose names
start with a dot, and `.pyc` and `.log` files. Every phase may see the declared entries and the
resulting file names, because the entity declarations are part of the Spec context; only
code-writing and code-review phases receive file contents, in their declared subsets. Its
**capability context** is the set of admitted Capability and Tool contracts the invocation may use
together with the Module's Protocol-defined external references: the vendored documentation and
source of the libraries, services and tools it declares with `references` of kind `external`,
each identified by one tree digest. Every phase sees those entries; planning, task authoring,
code-writing and code-review phases receive their readable files read-only, copied into a capsule
when the phase has no project workspace, with media and archives excluded. No phase receives an
undeclared network or an installed dependency's sources in their place. Its **task context** is the
task, constraints, admitted stage artifacts and lifecycle metadata. Task context travels inline in
the invocation input: stage artifacts and, for a review, the typed changes to the reviewed Module's
own Spec documents or implementation files since the baseline revision. Those changes are derived
from files inside the phase's visible scope, add no file to it and replace no granted file. A
kind may be empty for a phase, but the frozen closure is never empty. Planner and task-author inputs
contain no implementation file contents. Global discovery workers may reason across explicitly selected
complete Module Spec contexts for questions, routing and topology design. The host deterministically
resolves their registered documents, grants each source once as a read-only file listed in the
index, and preserves unique ownership, per-Module inclusion provenance and source byte digests. Questions are answered directly from these original
sources; additional Module contexts require explicit selection. For mutations, each selected worker
is a fresh invocation with only its own complete Module context. Routing metadata is an explicit
input, not permission to inspect implementation. Discovery never loads implementation
files.

Spec authors, assessors, planners and task authors use only the selected Module's complete
project-Spec collection and, for planners and task authors, its declared external references.
They MUST NOT read source code to supply missing Module meaning. Only the
code-writing phase receives the complete implementation context; code review receives its separately
declared read-only subset. Agent instructions, the Protocol rule bundle and Skills are not context:
instructions belong to a model-backed Capability's execution profile, and a Skill is the installed projection of a public
Capability for the developer's own agent runtime. Every worker's system prompt is its common worker
rules, then its own role instructions, then the Protocol rule bundle; the bundle's files are also
listed in the index with their digests and readable at their paths.

Context identities cover ownership, explicit references, inclusion reasons and document bytes,
Protocol and instructions, declared stage artifacts, declared listing entries and lifecycle
identity. Code-phase context identities additionally cover the bound file names and their current
digests; a code writer may create files below a listed directory without a prior pending
declaration. A changed input requires a new snapshot. Implementation-only changes do not add
implementation knowledge to a planner.

### P6. Gaps and review are tied to the affected contract

Missing required behavior is a Module Spec gap. Name the missing promise, blocked step, Module and
snapshot; continue only independent work. Implementation source cannot resolve that gap implicitly.
A failed execution, an explicit prohibition and a missing runtime value with defined failure
behavior are distinct from an unspecified contract.

Spec review uses complete Module specifications, including both document roles. Code review uses the same Module contracts and authorized code in a
fresh read-only invocation. A review records its exact inputs, coverage, findings and completion.
Changed relevant inputs invalidate it. Skipped, failed, incomplete and successful reviews remain
distinct. A changed canonical Spec document requires review for its owner and every Module whose
resolved context includes it, including Module-reference consumers. Reference and ownership changes
also invalidate their snapshots, plans and reviews. A change to a file listed by several Modules
requires checks for all listing Modules, with separate Module contexts and explicit per-consumer
evidence. Deterministic validation also reads the scenario declarations of the listed tests
and reports every scenario that no test declares, unless its Module binds no implementation file at
all; that coverage is evidence about the tests, never a change to the contract. No passing structural check proves semantic completeness.

### P7. Execution authority is explicit

The host binds each normal Framework invocation to declared context and file permissions. Only
code-writing invocations receive file contents with write authority, and only for the files the
selected Module lists; they never change Spec documents, entity declarations or the registry. Code
review and deterministic checks have separately declared read authority. The registry's reverse
index never grants a writer another Module's Spec or unrelated code. How the host keeps an
invocation within that authority belongs to the Harness Module's Specs, not to this profile. An
outer developer-authorized maintenance session may read and modify the project directly;
its explicit authorization does not silently widen normal worker permissions or become a project
business contract.

Every Framework capability's control flow is a LangGraph graph built with the Graph API: a
`StateGraph` whose nodes and edges are declared before it is compiled. The Functional API,
`entrypoint` and `task` from `langgraph.func`, MUST NOT be used, because it keeps control flow
inside ordinary Python where neither a Flow Spec nor Studio can inspect it; a deterministic check
refuses it. Every executable node is a Capability with declared input State and output State
updates. Its implementation may be deterministic code, a model invocation or a compiled subgraph;
these are not separate entity kinds. Capability composition uses one explicit USES relation.
Model instructions, tools and limits are execution configuration, not a parallel Agent identity.
The same graphs are the inspectable Studio surface, and no capability runs control flow outside
them. State channels carry data, not execution authority; runtime context and permission checks
remain separate. Parent graphs define reducers for shared channels explicitly.

Agent instructions, Skills, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute the Module kind definition and
the accepted Protocol binding. Configuration, installation and publication must agree on that
binding. Runtime Agent responsibility files are authored implementation assets, not another category
of project Spec.

### P8. Structure and file listings change together

Topology changes reconcile Module parentage, uses, document ownership, explicit references,
interface bindings and file listings as one consistent proposal. A candidate registry states each
Module's `files` as exact files and directory prefixes; the private author of that Module writes
entity declarations whose entry union equals it, entry for entry, marking files and directories that
do not yet exist as pending. Within one Module the most specific entry owns a file, and a listed
directory never contains a registered Spec document. The reverse index identifies every listing
Module before a shared file changes. A new or changed Module's author sees its resolved context but
may propose replacements only for its owned documents; referenced provider documents remain
read-only. A canonical shared-interface change is authored once by its owner and checked in every
affected consumer context; consumer agreement does not mean several authors submit identical copies.
Ownership transfers and reference changes reconcile old and candidate affected contexts atomically.
Each code-writing invocation receives the listed entries and the files they bind. Other Module
contracts are reviewed separately. An atomic application checks source versions and preserves prior
bytes if applying the proposed structure fails. Human acceptance is explicit where the selected
workflow requires it; direct maintenance follows the developer's explicit task authorization.

### P9. Candidate and delivery evidence belong to a worktree

One candidate worktree holds one change, including its component progress, gaps and implementation
impact evidence. Partial work is inspectable and resumable, not represented as completed delivery.
Validation and review evidence bind to actual candidate inputs. Changes to a file listed by several
Modules invalidate evidence for every listing Module even if only one Module initiated the change.
Shared Spec document changes invalidate evidence for the owner and every direct context consumer;
inclusion never gives those consumers provider implementation files or write authority. Delivery
preserves unrelated local changes, checks the actual integration and records incomplete cleanup
separately from a completed merge. After the candidate is verified, delivery confirms pending
entries: every declared pending file or directory that now exists has its marker removed by a
deterministic host edit included in the delivered commit, and the receipt names the confirmed
entries; an entry that still does not exist stays pending and is reported. No component
independently delivers its enclosing change.

### P10. Explicit session handoffs

When the selected workflow requires a new outer session, start it in the intended worktree with
fresh context and that worktree's instructions. Changing cwd does not erase prior cognitive inputs.
Supply a self-contained prompt in the developer's language with the absolute directory, branch,
task, authorizations, completed and remaining work, artifacts, checks and next steps. Start the
session automatically when isolation can be established; otherwise provide a complete copyable
prompt. A direct maintenance task explicitly authorized by the developer does not require a workflow
handoff solely because it updates the Framework's own instructions.

### Framework authoring and publication conventions

Every Concorde Module's `module.md` starts with Purpose, Terminology, Usage, Design and Relationships as
level-2 headings. The entry and explanatory topic companions have `document.role: module` and
contain no formal requirement/scenario definitions or canonical structured contracts. Those belong
in directly Module-owned implementation-role companions. Both roles remain complete Spec reading,
not separate ownership or context scopes. Companion topics do not repeat a mandatory entry template.
Each Markdown source has one schema-2 `.md.json` companion with explicit document identity, owner,
role, and entity, dependency and participant declarations. Mechanical fields
stay there; readable responsibilities, conditions, guarantees and obligations have local anchors
referenced by metadata. Group adjacent anchors on one line when a coherent explanation covers
several entities. Do not replace the retired JSON inventory with another giant human inventory.

Both source members are indexed, granted whole and byte-bound. A metadata-only change invalidates
owner and direct-consumer evidence. Authors return complete changed source members in `documents`;
a topology author returns both members of every candidate-owned unit in registration order.
Validate one combined overlay, not one file at a time. Ordinary authoring preserves document identity
and ownership; topology reconciles structural changes. Code writers never edit either member.

A requirement is one Module-wide SHALL statement with a stable heading ID. A scenario has ordered
GIVEN/WHEN/THEN steps and its own situational guarantees, not attached requirements. Internal
constraints remain normative; link rather than duplicate obligations. The Relationships view uses
English labels, accTitle and accDescr, a nonempty subset of local entity titles and labeled edges.
Explain its scope; inventory coverage is not a readability requirement or proof of completeness.
Files are bound in entity metadata, using owned package directory prefixes and exact shared files;
the registry listing remains their exact union. Project-owned metadata extensions
`concorde.capabilities` records the single checked inventory, including State contracts, USES and
optional model execution profiles; its
behavioral explanations remain reading content and unknown extensions cannot override the Protocol.

Every executable Flow has one Flow Spec in its owning Module's implementation-role documents,
not its explanation-first topics. Module-role reading explains the conceptual sequence and its
reasons, with clearly labeled conceptual diagrams when useful, and links to this exact Flow Spec.
The Flow Spec is written with LangGraph's
concepts: a State part, a Nodes table (node name, what executes, `in` and `out` state) and a
Mermaid flowchart bound to the compiled Flow by `%% flow: <name>` whose node identifiers are the
compiled node names including `__start__` and `__end__`, whose node labels state `in:` and
`out:`, and whose edges carry their routing condition as a label exactly when the source node has
several successors. The configured Flow Spec check keeps every diagram equal to its compiled Flow.

A Python test declares the scenarios it verifies with the `verifies` decorator from
`concorde.spec.verification`, for example `@verifies("scenario.harness.context-freeze")` on the test
function or method. A TypeScript test declares them with an own-line `// verifies:` comment above
the test, for example `// verifies: scenario.views.publish-candidate` above its `it` call; several
IDs are separated by commas or spaces, and the following `it`, `test` or `describe` title names the
declaring test. A test may name several scenarios in either language, and the declaration is read by
parsing, never by compiling or running the test. A Module whose entities bind no implementation file
has no test to declare its scenarios, and its scenarios are not reported as uncovered. No Spec
document lists tests. Links inside Specs address definitions by ID
(`scenarios.md#scenario.harness.context-freeze`, `requirements.md#req.harness.permission-no-widen`); publication
turns every scenario, requirement, entity and canonical contract ID into an anchor. Rendered views
and navigation are derived and create no ownership or context inclusion. Links to canonical shared
definitions remain links in rendered pages, never transclusions; the site exposes owner and
reference provenance. These conventions implement the Protocol's requirements for this project; they
are not requirements on every Protocol implementation.
