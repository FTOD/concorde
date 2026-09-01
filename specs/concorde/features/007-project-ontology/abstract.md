# Feature Abstract: Define Project Ontology

`feature.concorde.define-project-ontology` · specified at `module.concorde` · about 8 minutes.

## Purpose

Concorde gives maintainers and coding agents a consistent vocabulary for every architecture and feature level. Each level defines the important concepts it introduces, inherits terminology from its ancestors without copying it, and makes concept relationships explicit enough to validate and visualize.

The result is a project ontology rather than a loose glossary: readers can learn what a concept means, where it was defined, which other concepts it relates to, and whether a descendant is using it consistently.

## Functionality

| Capability | Outcome |
|---|---|
| Local terminology declaration | Every module, feature, and sub-feature `design.md` contains a `Term / Meaning / Relationships` table or explicitly declares that it introduces no local terms. |
| Terminology inheritance | Lower levels use ancestor terms directly without duplicating their rows. |
| Consistency validation | Conflicting redefinitions, invalid aliases, malformed tables, and unresolved relationship references are reported with their defining levels. |
| Relationship visualization | A maintained Archify architecture view shows Concorde's core entities and typed relationships. |
| Project migration | Existing Concorde design levels adopt the same ontology contract. |
| Documentation projection | Generated documentation renders the maintained tables and views without becoming authoritative. |

**Not part of this feature**: renaming Concorde's stable architecture, extracting incidental source-code identifiers into the ontology, or treating generated HTML as maintained truth.

## Structure

The core view is maintained in `diagrams/concorde-ontology-model.json` and delivered as <a href="/architecture/concorde-ontology-model.html">Concorde Ontology Model</a>. It shows the specification root containing module levels, modules providing features, features optionally refining into one sub-feature level, level-local terminology defining concepts, relationships connecting concepts, and features owning temporal attempts.

Text in `design.md` and level terminology tables remains authoritative. The Archify view is the searchable structural explanation of those textual facts.

## Logic

1. Resolve the current design level and its ordered ancestor chain.
2. Read ancestor terminology as already-known vocabulary.
3. Define only important concepts introduced at the current level, with meanings, aliases, and typed relationships.
4. Resolve every relationship target locally or through the ancestor chain and reject incompatible inherited redefinitions.
5. Validate the textual ontology, then validate and deliver any maintained Archify relationship view.
6. Publish tables and diagrams as disposable documentation projections.

**Rules the implementation must keep**

- Every maintained module, feature, and sub-feature design has the standard terminology section and covers all important local concepts. (FR-001, FR-002, FR-003, FR-004)
- Meanings, aliases, and relationship references are explicit, typed, and resolvable. (FR-005, FR-006, FR-011)
- Modules, features, and sub-features inherit from their permitted ancestors without copying or incompatibly redefining terms. (FR-007, FR-008, FR-009, FR-010)
- Authoring guidance and templates keep terminology current whenever a design changes. (FR-012)
- The text-backed ontology view and any required level-specific views remain hidden-legend, showcase-valid, fresh, and subordinate to textual authority. (FR-013, FR-014, FR-015)
- Documentation renders the ontology faithfully, and all existing Concorde levels are migrated before completion. (FR-016, FR-017, FR-018)

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md)
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md)
- **Contracts** — `specs/concorde/features/007-project-ontology/contracts/`
- **The level this feature belongs to** — [../../module.md](../../module.md)
- **Related project-wide ontology** — [../../../../docs/ontology.md](../../../../docs/ontology.md)
