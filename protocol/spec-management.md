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

Requirements and scenarios are defined in reading; entity declarations bind identities to readable
meaning; canonical interfaces retain their single readable definition. All belong to the owner of
their defining unit. A document relocation or title change does not itself change identity. Links
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

An interface remains a local entity with one canonical readable contract. It may occupy an ordinary
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
