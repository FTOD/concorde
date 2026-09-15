# Spec Protocol 7: content and reading separation

Status: implementation in progress. This document records the developer-authorized migration
contract. It is not the project's accepted Protocol binding. Protocol 6 / Profile 13 remains active
until the complete runtime, authoring, publication and source migration can be verified together.
Do not claim that the active runtime already admits the representation described here.

## Accepted decisions

- Publish an incompatible Protocol revision and migrate this checkout completely. Do not add a
  dual-format runtime, silently reinterpret old projects, or discard unrelated edits.
- The Protocol defines the complete content model **and its human-readable subset**. It does not
  prescribe a docsite's pages, tabs, sidebar, layout, progressive disclosure or interactions.
- Reading content is not a summary. Purpose, correct use, design, entity meaning, collaborations,
  requirements, scenarios, interface definitions and participant obligations remain readable.
  Low-frequency failure and security obligations do not become non-reading metadata.
- A Module's reading entry starts with Purpose, Usage, Design, Relationships. Requirements,
  Scenarios and other details follow or live in explicitly registered companion documents.
  Remove the two mandatory enclosing parts and the separate Entities reading chapter.
- Separate all mechanical identity, mapping and implementation-binding declarations, not just the
  entity inventory. Preserve readable semantics once, with metadata referring to their definitions.
- Rewrite existing Specs for understanding, not just for syntax. Preserve effective obligations,
  stable identities and canonical interface versions. Escalate actual behavioral contradictions or
  proposed weakening rather than treating them as editorial cleanup.

## Information model

For a Module M, let C(M) be its complete owned specification content and R(M) the subset designated
for human reading. R(M) is a subset of C(M), not a separately authored summary or a renderer's
heuristic selection. The Protocol requires both content completeness and reading completeness.
A machine declaration cannot be the only place that states a fact a developer needs to understand,
use, implement or maintain the Module.

Mechanical metadata supplies identity, ownership and realization mappings. Reading content supplies
meaning, including normative internal constraints. The distinction is about information, not syntax:
a JSON interface schema and example can be useful reading content; a Markdown table of file bindings
is still mechanical metadata. Publication may expose metadata as an auxiliary inspection surface,
but that does not make it mandatory reading or alter the complete context.

Relationships distinguish composition from capability use. Diagrams explain a named scope and may
omit inventory entities irrelevant to that scope. Every depicted node resolves to a local entity;
every relationship edge has a meaningful label. Unknown nodes and unlabeled edges remain errors.
Completeness of the content is not established by drawing all inventory nodes. Ordinary prose
explains collaboration conditions, relied-upon guarantees and local reactions that arrows cannot.

## Representation chosen for the implementation

Each registered Markdown document is a **document unit**, comprising two exact source files:

- `path/to/topic.md`: reading content;
- `path/to/topic.md.json`: associated machine metadata.

Appending `.json` is a deterministic part of the format, not directory discovery. Registration of
`topic.md` registers the pair under one document identity and one owner. The pair is indivisible for
context inclusion and ownership transfer; a document reference includes exactly that pair, not the
rest of its owner's documents. Neither member can be an implementation file or external reference.
The registry continues to declare Module composition, uses, document units and one-level references.

The metadata object has these fields:

```json
{
  "schema_version": 1,
  "document": {"id": "document.checkout.module", "owner": "module.checkout"},
  "entities": [
    {
      "id": "entity.checkout.service",
      "title": "Checkout service",
      "kind": "program",
      "meaning": "#entity.checkout.service",
      "files": ["src/checkout/"],
      "pending": []
    }
  ],
  "dependencies": [
    {"target_id": "module.inventory", "meaning": "#checkout-inventory-agreement"}
  ],
  "bindings": [
    {
      "id": "contract.inventory.reserve",
      "version": 1,
      "role": "required",
      "peer": "module.inventory",
      "meaning": "#checkout-reservation-obligations"
    }
  ]
}
```

The three declaration arrays are explicit and may be empty. Entity fields `files`, `pending` and
`target_id` are optional; the ordinary exclusive target/file and pending-subset rules still apply.
A metadata declaration contains no copied responsibility, selection-condition or obligation prose.
Its `meaning` is a local identity anchor in this unit's reading file, never a remote URL or a path
that loads another file. Entities use their stable identity as that anchor. Dependency and binding
anchors identify local explanations, not another contract definition or additional query kind.

A reading anchor can be a standalone `<a id="..."></a>` before an explanation or an explicit
heading suffix `{#...}`. Requirement and scenario headings retain their stable-ID syntax.
`concorde-contract` definitions retain their canonical schema, semantics and example. Publication
must preserve identity links. It must not publish the metadata file as a second canonical page.

Dependency explanations state provider responsibility, use conditions and canonical promises relied
upon, together with local duties/reactions. Binding explanations state participation conditions,
relied-upon guarantees and obligations. Structural checks can require a local nonempty explanation;
semantic review must judge whether it supplies those facts. Merely filling labels is not proof.

No `main_visible` flag is used to decide the Protocol's reading subset. All registered Markdown is
reading content; presentation preferences belong to the publisher. The existing flag's removal
must be reconciled explicitly in runtime value schemas and consumers rather than silently given a
new meaning.

## Complete context and source identity

Resolve owned and directly referenced **document units** once, preserving the current nonrecursive
selection rule. Expand each selected unit to its reading and metadata files. Record the same
stable document identity and owner on both records, and distinguish their source roles as `reading`
and `metadata`. Sort by canonical project-relative path; hash each file's exact bytes independently.
Every file is available whole. Metadata-only edits invalidate context/review identities just as
reading edits do. A reading-only projection is never a substitute for this complete grant.

The complete Spec context still excludes implementation contents and external references. Listed
implementation names and pending status remain visible through metadata; contents remain separately
authorized. A missing or unsafe metadata member rejects resolution without partial admission.

Authors may propose changes only to both members of their owned units. Providers' pairs remain
read-only. All changes in one proposal must be validated as one overlay and applied atomically.
A code writer cannot modify either member. Pending confirmation edits only the associated metadata,
not the reading prose. Ownership transfer preserves the document and definition IDs and reconciles
both members, registrations, references and links together.

## Migration and activation gates

1. Implement and test the new document-unit admission and reading-reference primitives without
   changing the active profile. Prove exact-byte identities and rejection of malformed/unsafe pairs.
2. Build an explicit, loss-accounted migration. Preserve all requirement/scenario/contract IDs and
   all old responsibility, dependency and binding semantics in reading content. Do not represent a
   mechanical conversion as completed editorial work.
3. Replace runtime parsing and wire shapes, complete context/grant delivery, authoring overlays,
   topology, review impact, pending confirmation, initialization and templates. Reject old profiles
   with an explicit migration error; no fallback parser.
4. Migrate and rewrite every registered Spec. Review composite Modules, shared-interface consumers
   and dense implementation Modules, not just a small leaf example. Remove obsolete statements
   describing the two-part model and keep all valid obligations.
5. Update publication admission, provenance, identity anchors, links, sidebars and generated outputs.
   Publish reading content without appending a duplicate Files inventory. Keep custom docs independent.
6. Update Protocol chapters, templates, Framework profile, authoring prompts and Skills; bind the new
   version only when the complete checkout passes structural validation and deterministic checks.
7. Run build, build --check, repository validation, Python tests, docsite typechecking/tests/build,
   flow checks and direct visual inspection. Record limitations honestly: structural success is not
   semantic review or visual evidence.

Verified steps are separate commits. A partially implemented parser is not a completed migration,
and an explicit skipped or incomplete check is never described as passing.
