---
id: feature.concorde.define-project-ontology
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.explore-alignment
interfaces:
  provided:
    - contract.concorde.ontology
  required:
    - contract.understand-anything.knowledge-graph
evidence_status: partial
---

# Feature Design: Adopt a Module-Centered Specification Ontology

**Created**: 2026-08-31

**Revised**: 2026-09-01

**Status**: Approved for control-state prototype refinement

**Input**: Keep the module-centered durable specification, but move workflow-only state out of the
specification tree. Store active work at `.concorde/attempts/<stable-feature-id>/` and the tracked
reflection authority at `.concorde/reflections/log.md`, alongside reflection-triage control state.
Migrate routing, delivery, validation, publication, guidance, fixtures, and maintained sources together.

## Outcome and Scope

A maintainer can enter the specification at any module, understand that module's architecture as a
graph of typed entities and interactions, then open one direct feature file to learn what the module
provides, how to use it, and how the relevant architecture entities collaborate. The `specs/` tree
contains only durable architecture, feature intent, and optional explanatory diagrams; project-level
workflow state is isolated under `.concorde/`.

This migration is repository-wide. It changes Concorde's source profile, runtime protocol, initialization, context retrieval, validation, planning, implementation, delivery, generated documentation, canonical and installed guidance, fixtures, and every maintained Concorde module and feature specification.

## Target Specification Model

```text
<module>/
├── architecture.md             # the module's structure, entities, and interactions
├── diagrams/                   # optional architecture-owned explanatory sources
├── modules/<child>/            # immediate child modules with the same shape
└── features/
    └── <NNN-name>.md           # one complete durable feature specification

<project>/.concorde/
├── config.json                 # source-profile and root-module configuration
├── attempts/
│   └── <stable-feature-id>/    # temporary plan/tasks/evidence; absent after delivery
└── reflections/
    ├── log.md                  # tracked durable process memory
    ├── config.json             # triage configuration
    ├── plans/                  # disposable/ignored triage plans
    └── worktrees/              # disposable/ignored implementation worktrees
```

- A module is the only hierarchical specification unit. A child module is stored directly under its parent's `modules/` directory.
- `architecture.md` is the module's single architectural authority. It replaces `module.md`, the adjacent module `design.md`, and module-owned contract documents.
- A feature is specified exactly once as `features/<NNN-name>.md`. Features do not contain features; composition and refinement are explicit stable-ID relationships.
- The feature file contains its outcome, interfaces, usage, requirements, and architecture zoom. Its filename is storage/navigation; the stable feature ID remains semantic identity.
- `.concorde/` is project control state, outside the recursive specification hierarchy. It owns source-profile configuration, active attempts, and reflection workflow state.
- `.concorde/attempts/<stable-feature-id>/` is temporary workflow memory keyed by the feature's globally unique semantic identity rather than its mutable filename or module path. Successful delivery validates and removes it without changing the feature file or generating another durable narrative.
- `.concorde/reflections/log.md` is tracked process memory. Triage configuration shares its directory, while plans and worktrees remain disposable and ignored.
- Source code is the implementation. Tests and deterministic checks are evidence. Generated sites, diagrams, indexes, and delivery results are disposable projections.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Module` | The recursive unit of specification ownership. A module has one responsibility, one boundary, one `architecture.md`, zero or more immediate child modules, and zero or more level-local features. | `contains` → `Module`; `specifies` → `Feature`; `owns` → `Architecture specification` |
| `Architecture specification` | A module's single durable account of its typed entities, organization, relationships, and interactions. | `defines` → `Architecture entity`; `defines` → `Entity relationship`; `replaces` → `Module summary`; `replaces` → `Module design reference` |
| `Architecture entity` | An architecture-significant module, package, program, file, script, class, function, interface, data store, schema, configuration, test surface, external system, or other explicitly typed thing. | `belongs to` → `Module`; `participates in` → `Entity relationship`; `realized by` → `Source code` |
| `Entity type` | A preferred classification that tells a reader what an architecture entity is. Concorde adapts Understand Anything's code-oriented node vocabulary but permits project-defined types with an explicit meaning. | `classifies` → `Architecture entity` |
| `Entity relationship` | A typed, directed structural or behavioral connection between architecture entities, such as contains, imports, calls, implements, exposes, reads, writes, produces, consumes, validates, renders, or depends on. | `connects` → `Architecture entity`; `governs` → `Interaction` |
| `Interaction` | An ordered or conditional collaboration among architecture entities described at the current module level. | `uses` → `Entity relationship`; `supports` → `Feature` |
| `Feature` | One module-level functionality or interface that a consumer can use, specified in one durable `features/<NNN-name>.md` file. | `belongs to` → `Module`; `exposes` → `Feature interface`; `zooms into` → `Architecture entity`; `relates to` → `Feature` |
| `Feature file` | The direct Markdown authority for one feature; its filename supplies navigation while its front-matter `feature.*` ID supplies semantic identity. | `specifies` → `Feature`; `belongs to` → `Module`; `corresponds to` → `Attempt` |
| `Feature interface` | The human-readable entry points, inputs, outputs, obligations, failures, and compatibility expectations through which a feature is used. Existing stable `contract.*` identifiers remain valid prototype interface identities. | `part of` → `Feature`; `implemented by` → `Architecture entity`; `replaces` → `Architecture contract` |
| `Architecture zoom` | A feature-local explanation of which entities from its module architecture participate and how they collaborate for that feature. It adds behavioral detail without redefining entity identity or ownership. | `part of` → `Feature`; `references` → `Architecture entity`; `explains` → `Interaction` |
| `Source code` | The executable files and symbols that are the actual implementation at the checked-out revision. | `realizes` → `Architecture entity`; `implements` → `Feature`; `evidenced by` → `Test` |
| `Project control state` | Tracked or disposable workflow metadata below `<project>/.concorde/`; it is neither product specification nor generated publication. | `configures` → `Module`; `contains` → `Attempt`; `contains` → `Reflection log` |
| `Attempt` | Temporary planning, task, research, checklist, and validation memory at `.concorde/attempts/<stable-feature-id>/`, corresponding to one selected feature identity. | `belongs to` → `Feature`; `changes` → `Source code`; `removed by` → `Delivery` |
| `Reflection log` | The tracked project-wide record at `.concorde/reflections/log.md` for provisional choices, workarounds, and problems encountered during feature work. | `belongs to` → `Project control state`; `records` → `Feature work` |
| `Delivery` | The terminal operation that proves a completed attempt is eligible and removes its temporal workspace; it does not author an implementation narrative. | `validates` → `Attempt`; `retains` → `Feature`; `retains` → `Source code` |

## Architecture Zoom

This feature changes the following root-architecture entities; their final definitions and relationships belong in `specs/concorde/architecture.md`:

| Entity ID | Type | Role in this feature |
|---|---|---|
| `entity.concorde.runtime` | package | Discovers and models recursive `architecture.md` modules, direct feature files, typed entities/relations, interfaces, project-control attempts/reflections, evidence, and projections. |
| `entity.concorde.workspace-resolver` | program | Returns one selected feature file, its providing module architecture, bounded ancestry/relations, and stable-ID control-state paths through Protocol 12. |
| `entity.concorde.cli` | program | Exposes validation and cleanup-only delivery over the new package model. |
| `entity.concorde.preset-package` | directory | Teaches specification, planning, tasks, implementation, convergence, analysis, and fast loop using the new authorities. |
| `entity.concorde.extension-package` | directory | Teaches context, initialization, validation, ask, and cleanup-only delivery using the new authorities. |
| `module.concorde.auto-docs` | module | Publishes module architecture and direct feature files without interpreting a wrapper directory or `design.md` basename. |
| `entity.concorde.specification` | directory | Self-applies the new profile across all six modules and twenty-four features. |
| `entity.concorde.control-state` | directory | Owns Profile 7 configuration, stable-ID attempts, tracked reflections, and triage state outside module specifications. |

The feature is cross-cutting because these entities share one source profile. They must switch together; a mixed old/new durable layout is invalid after migration.

## Interfaces

### `contract.concorde.ontology` — Module-centered specification profile

- **Consumer**: Maintainers, coding agents, validators, installers, and documentation/exploration projections.
- **Direction**: Profile sources and operation requests to validated bounded structure, guidance, and lifecycle results.

- **Entry points**: A module's `architecture.md`; a direct `features/<NNN-name>.md`; Protocol 12 workspace JSON; deterministic initialization, context, validation, and delivery operations.

- **Inputs**:

- a configured root module and recursively nested `modules/` tree;
- architecture front matter and the required entity/relationship/interaction sections;
- feature front matter, embedded interface definitions, architecture references, requirements, and usage scenarios;
- optional project control state containing `.concorde/attempts/<stable-feature-id>/` and the tracked
  `.concorde/reflections/log.md`.

- **Outputs**:

- a bounded module or feature context with stable IDs and canonical paths;
- deterministic findings for invalid structure or unresolved semantic references;
- generated navigation and architecture views with source provenance;
- a delivery result that lists removed temporal artifacts and retained durable/code authorities.

- **Obligations**: Producers define each architecture-significant entity once at its owning module, use stable IDs for every cross-reference, keep feature interfaces in the owning design, and distinguish code/test reality from prose/projections.

- **Failures**: Resolution or validation fails on unsafe paths, duplicate IDs, cyclic module containment, untyped entities, unresolved relationships, missing interface semantics, legacy durable files, or ambiguous ownership; delivery failures preserve the complete attempt.

- **Compatibility**: Profile 7 / Protocol 12 are an intentional breaking control-state path revision
  with no dual-layout mode. Initialization Proposal 2 adds the reflection log and reflection-triage/v2
  changes its canonical locator. Stable module/feature/interface IDs, Delivery Proposal 8 semantics,
  and Build Manifest 10 semantics remain unchanged.
- **Implementing entities**: `entity.concorde.runtime`, `entity.concorde.workspace-resolver`, `entity.concorde.cli`, `entity.concorde.preset-package`, `entity.concorde.specification`, `entity.concorde.control-state`.
- **Example**: A module `architecture.md` defines `entity.example.worker`; a feature design references it in Architecture Zoom and exposes an interface whose entry point and implementing entities include that stable ID.

### `contract.understand-anything.knowledge-graph` — Required vocabulary reference

- **Provider**: `external:Egonex-AI/Understand-Anything@ba450c43425f3de6d43daf76526950ad8ca93536`.
- **Consumer**: Concorde ontology design and future graph adapters.
- **Direction**: Formal upstream entity/edge definitions to an explicitly adapted Concorde vocabulary.
- **Entry points**: Pinned upstream `types.ts`, `schema.ts`, and analyzer significance/direction rules.
- **Inputs**: Formal node/edge enums, aliases, directions, graph/layer metadata, and significant-symbol rules.
- **Outputs**: Documented adapted type/predicate choices that never replace Concorde ownership or stable IDs.
- **Obligations**: Distinguish formal schema from stale narrative guides and representation from semantic identity.
- **Failures**: Missing/changed upstream definitions require an explicit compatibility review rather than silent remapping.
- **Compatibility**: Profile 7 retains Concorde's Module hierarchy, Program, Directory, roles, and stable identities beyond UA's formal model.
- **Implementing entities**: `entity.concorde.understand-anything`, `entity.concorde.specification`.
- **Example**: Concorde `contains_module` may render as UA `contains`, while the maintained precise predicate remains authoritative.

## User Scenarios & Testing

### User Story 1 - Understand One Module's Architecture (Priority: P1)

As a maintainer, I can open one module's `architecture.md` and identify its responsibility, boundary, immediate modules, significant entities, entity types, and relationships without opening descendant modules or reading source code.

**Independent Test**: Select each maintained Concorde module and verify that its architecture document defines every immediate structural entity once, states what type it is, and resolves every relationship endpoint locally or through permitted ancestor references.

**Acceptance Scenarios**:

1. **Given** an architecture-significant file, program, function, module, data object, or external dependency, **When** it appears in a module architecture, **Then** the architecture assigns it a stable identity, an explicit type, a definition, an implementation path or external locator when applicable, and its important relationships.
2. **Given** a module contains a child module, **When** the parent architecture is read, **Then** the child is visible as one entity with its responsibility and interactions, while its internal entities remain in the child's architecture.
3. **Given** an entity relationship crosses the module boundary, **When** the architecture is validated, **Then** its direction, participants, and governing level-local feature interface resolve unambiguously.

### User Story 2 - Discover and Use a Module Feature (Priority: P1)

As a consumer of a module, I can open one direct feature Markdown file and learn what functionality it provides, how to invoke or consume it, what enters and leaves, what can fail, and which architecture entities collaborate.

**Independent Test**: Select every maintained `features/*.md` source and verify that a reader can exercise its representative usage without consulting a wrapper directory, abstract, implementation narrative, or architecture-owned contract document.

**Acceptance Scenarios**:

1. **Given** a feature exposes one or more entry points, **When** its design is read, **Then** every entry point's consumer, inputs, outputs, obligations, failures, and compatibility policy are present in that design.
2. **Given** a feature depends on or composes another feature, **When** its design is read, **Then** stable related-feature references explain the relationship without nested feature ownership.
3. **Given** a feature explains internal behavior, **When** its architecture zoom is validated, **Then** every referenced entity resolves in the providing module or an ancestor and the feature does not redefine the entity's architectural identity.

### User Story 3 - Plan and Implement Against Code Reality (Priority: P2)

As a coding agent, I can plan a feature change from its direct feature file, bounded module architecture,
current source code, and tests, then execute dependency-ordered tasks in the corresponding project-control
attempt without treating an `implementation.md` summary as a baseline.

**Independent Test**: Select a feature whose stable ID is `feature.example.change`, start
`.concorde/attempts/feature.example.change/`, generate a plan and tasks, implement a fixture change,
and confirm every phase receives `feature_path`, module architecture, separate control-state paths,
and code/test paths without module-local attempts or removed authority fields.

**Acceptance Scenarios**:

1. **Given** a selected feature has no corresponding control-state attempt, **When** planning starts,
   **Then** `.concorde/attempts/<stable-feature-id>/` is created and code/tests provide the current realization context.
2. **Given** related features exist, **When** bounded context is resolved, **Then** concise relationship summaries are available without implicitly loading unrelated feature bodies or attempts.
3. **Given** implementation changes an architecture entity or feature interface, **When** tasks execute, **Then** the owning architecture or feature design, code, tests, and generated projections are reconciled by explicit tasks in the same attempt.
4. **Given** a planned feature path whose file does not yet exist, **When** the first specification
   workspace gate runs, **Then** Protocol 12 returns no guessed feature ID or attempt path; after the
   feature is written with a valid stable ID, a required second resolution returns its exact control-state paths before checklist creation.

### User Story 4 - Validate and Deliver the Migrated Project (Priority: P2)

As a maintainer, I can validate that the entire project uses the new ontology and deliver a completed attempt without generating or retaining redundant implementation prose.

**Independent Test**: Run complete Concorde validation, Python tests, docsite tests/build, package/release verification, and delivery on the selected ontology feature; verify zero legacy durable artifact names remain and delivery removes only its attempt.

**Acceptance Scenarios**:

1. **Given** any `module.md`, adjacent module `design.md`, feature `abstract.md`, feature `implementation.md`, nested `subfeatures/`, or specification-owned contract document remains, **When** validation runs, **Then** it reports a migration error with the canonical replacement.
2. **Given** all tasks and checklists are complete and validation passes, **When** delivery is invoked,
   **Then** it removes exactly `.concorde/attempts/<stable-feature-id>/`, retains `architecture.md`,
   the direct feature file, source code, tests, and `.concorde/reflections/log.md`, and reports their digests.
3. **Given** a delivery is ineligible or stale, **When** it is attempted, **Then** no durable source, code, test, or attempt artifact is changed.

### Edge Cases

- A code file contains several architecture-significant classes or functions, while other symbols are intentionally omitted.
- An entity has no filesystem path because it is an external system or a conceptual data object.
- A script is represented by the adapted type `script` even though Understand Anything serializes shell scripts as `file` nodes.
- A runnable program is composed from multiple files and therefore has a locator rather than one canonical source path.
- Two unrelated modules use the same local entity name; their stable qualified IDs remain distinct.
- A feature relates to another feature in the same module, an ancestor module, or an immediate child module without implying ownership.
- A feature has no public machine API but still exposes a human workflow or generated artifact interface.
- An attempt changes files that are architectural implementation details but does not change the stable entity graph.
- Delivery encounters an untracked or symlinked path inside the attempt.
- A feature file is renamed while its stable ID and active attempt remain unchanged.
- A malformed or unsafe stable feature ID would escape the `.concorde/attempts/` boundary.
- A planned feature file does not exist yet, so no stable ID can honestly name an attempt.
- A legacy module-local attempt or specification-root `reflections.md` remains after migration.
- Reflection triage plans/worktrees are ignored while the authoritative reflection log remains tracked.

## Requirements

### Functional Requirements

- **FR-001**: The specification hierarchy MUST be a recursive tree of modules rooted at the configured project module; features MUST NOT be hierarchy containers.
- **FR-002**: Every module MUST contain exactly one durable `architecture.md` and MAY contain only
  immediate `modules/`, direct level-local `features/*.md`, and architecture-owned `diagrams/` in
  addition to that architecture; attempts and reflection logs MUST NOT live in the specification tree.
- **FR-003**: Each `architecture.md` MUST define the module's stable identity, parent, responsibility, boundary, immediate module and feature inventory, architecture-significant entities, typed relationships, and representative interactions.
- **FR-004**: Every architecture entity MUST have a stable qualified ID, explicit type, non-circular definition, and a project-relative implementation path or explicit external/conceptual locator when applicable.
- **FR-005**: Concorde MUST define a preferred entity-type vocabulary adapted from Understand Anything and MUST permit an explicit project-defined type when the preferred vocabulary cannot represent the entity without distortion.
- **FR-006**: Every entity relationship MUST use a typed direction and resolve both endpoints to entities visible at the current module level; relationships and interactions MUST identify any governing feature interface when one exists.
- **FR-007**: Parent module architectures MUST expose child modules as bounded entities and MUST NOT duplicate the child's internal entity inventory.
- **FR-008**: Every feature MUST be exactly one direct `<module>/features/<NNN-name>.md` file and express composition/refinement through stable related-feature references; feature directories and `design.md` basenames are invalid.
- **FR-009**: Every feature design MUST define its observable outcome, scope, representative usage, requirements, edge/failure behavior, related features, and architecture zoom.
- **FR-010**: Every externally meaningful entry point or promise MUST be a feature interface defined inside the owning feature design with consumer, direction, inputs, outputs, obligations, failure behavior, compatibility, and implementing entity references.
- **FR-011**: Existing stable `contract.*` identifiers MAY remain as feature-interface identities during the prototype, but no specification-owned contract document or contract directory MAY remain outside or beside a feature design.
- **FR-012**: Every entity named by a feature architecture zoom or interface MUST resolve in the feature's providing module architecture or its permitted module ancestry, and a feature MUST NOT redefine the entity's type or ownership.
- **FR-013**: Feature wrapper directories, feature `design.md`/`abstract.md`/`implementation.md`, module `module.md` and adjacent module `design.md`, nested `subfeatures/`, and specification-owned contract documents MUST be absent after migration.
- **FR-014**: Source code MUST be the current implementation authority; tests and deterministic checks
  MUST be evidence; plans, tasks, research, checklists, and validation logs MUST live only under
  `.concorde/attempts/<stable-feature-id>/`.
- **FR-015**: Protocol 12 MUST expose `feature_path`, providing module architecture, bounded module
  ancestry, bounded related-feature summaries, stable-ID-derived attempt paths/state,
  `.concorde/reflections/log.md`, and code/test discovery context without module-local control state or
  removed authority fields.
- **FR-016**: Specification, clarification, planning, task generation, analysis, convergence, implementation, fast-loop, initialization, context, validation, and delivery guidance MUST use the new authority model consistently in canonical and installed surfaces.
- **FR-017**: Initialization MUST propose a minimal root `architecture.md` with a valid typed
  entity/relationship scaffold and initialize `.concorde/reflections/log.md`; when explicitly requested,
  it MAY add one direct feature file and its stable-ID attempt mapping, but MUST NOT create module-local
  attempts or feature wrapper directories. The three-file initialization transaction MUST use
  Initialization Proposal 2.
- **FR-018**: Validation MUST deterministically check canonical direct-file layout, module cycles,
  unique/path-safe stable IDs, entity types and locators, relationship endpoints, stable-ID attempt
  mapping, related-feature references, embedded interface completeness, architecture zoom references,
  control-state safety, and legacy residue without mutating sources.
- **FR-019**: Documentation generation MUST publish `architecture.md` as each module landing page and
  each direct feature file as one feature landing page, preserve source provenance, publish
  architecture-owned diagrams, and exclude `.concorde/` control state from public content discovery.
- **FR-020**: Delivery MUST require complete tasks and existing checklists plus current validation
  evidence, then remove exactly `.concorde/attempts/<stable-feature-id>/` without writing or moving the
  feature file or reflection log; ineligible, unsafe, ambiguous, or stale delivery MUST be non-mutating.
- **FR-021**: Every maintained Concorde module and feature specification, fixture, schema/example reference, test, guide, manifest, and generated-source expectation MUST migrate in the same prototype milestone; mixed-profile operation is out of scope.
- **FR-022**: The full migrated repository MUST contain no stale semantic references that treat
  abstracts, accepted implementation narratives, module summaries/design references, nested
  subfeatures, architecture-owned contracts, module-local attempts, or specification-root reflections
  as current authorities.
- **FR-023**: Protocol 12 MUST NOT derive a stable feature ID from a planned filename. Before a new
  feature exists, specify-phase attempt fields MUST be explicitly unavailable; after the feature file
  declares a valid ID, specification MUST re-resolve the workspace before creating its checklist or attempt.

## Success Criteria

- **SC-001**: 100% of maintained and fixture modules use the canonical `architecture.md` layout, and 100% of maintained and fixture features are direct `features/<NNN-name>.md` files with zero feature directories.
- **SC-002**: 100% of maintained module architecture entity and relationship references and feature architecture-zoom/interface entity references resolve with zero validation findings.
- **SC-003**: A maintainer can identify what any sampled architecture entity is, where it is realized, and how it relates to its neighbors in under three minutes from one module architecture.
- **SC-004**: A maintainer can identify how to use any sampled feature, including inputs, outputs, failures, and participating entities, in under three minutes from its single design.
- **SC-005**: Workspace JSON and all command/skill contracts contain `feature_path`, Protocol 12,
  `.concorde/attempts/<stable-feature-id>/`, and `.concorde/reflections/log.md`, with zero module-local
  control-state or other deprecated authority fields.
- **SC-006**: Complete Python, documentation-site, package/release, self-hosting, and Concorde validation suites pass under the new source profile.
- **SC-007**: The selected ontology attempt is delivered successfully from
  `.concorde/attempts/feature.concorde.define-project-ontology/`, that directory is absent afterward,
  and both `specs/concorde/features/007-project-ontology.md` and `.concorde/reflections/log.md` remain
  byte-identical through delivery.
- **SC-008**: A planned-feature fixture receives no guessed attempt path on its first Protocol 12
  specify resolution and receives the exact stable-ID path only after its feature front matter exists.

## Assumptions

- This is an intentionally breaking prototype source profile; no compatibility reader for the old layout is required after the repository itself migrates.
- Architecture inventories include only entities significant to understanding structure, extension, interfaces, or risk. Concorde does not require a duplicate row for every implementation symbol.
- Understand Anything supplies a useful code-entity and relationship vocabulary, but Concorde remains authoritative for recursive modules, feature interfaces, attempts, evidence, and specification ownership.
- Existing stable module and feature IDs remain unchanged. Existing `contract.*` IDs are preserved as interface identities for this prototype to keep external references recognizable.
- Stable feature IDs are globally unique and restricted to a path-safe grammar. The exact stable ID
  deterministically names its `.concorde/attempts/` directory; renaming a feature file does not move
  active work, while changing the stable ID with active work is rejected rather than guessed.
- The reflection log and active attempt files are tracked reviewable state. Reflection-triage plans,
  worktrees, and legacy compatibility assets remain ignored/disposable.
- Architecture-owned JSON diagrams remain optional supporting sources. Feature-specific dynamic diagrams are either promoted to the providing module's diagram set or retired; they do not restore a multi-file feature specification.
- Git history is sufficient durable milestone history after delivery removes temporal attempt evidence. Current code and tests, not a generated narrative, describe the accepted implementation.

## Out of Scope

- Automatically extracting a complete entity graph from source code.
- Proving semantic completeness of a human-authored entity inventory beyond deterministic structural/reference checks.
- Maintaining a dual reader or automated downgrade path for the old source profile.
- Supporting both feature directories and direct feature files after the repository cutover.
- Supporting module-local attempts or a specification-root reflection log after the control-state cutover.
- Supporting multiple concurrent attempts for one stable feature ID; separate branches/worktrees remain the prototype mechanism.
- Renaming every preserved `contract.*` stable identity to `interface.*` during the prototype.
- Replacing Archify, Docusaurus, Spec Kit, or the coding-agent platforms.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.define-project-ontology`
- **Providing module**: `module.concorde`
- **Related features**: every Concorde workflow and publication feature participates because the source profile is shared.
- **Interface**: this design embeds `contract.concorde.ontology`; the former standalone ontology contract is removed during migration.
- **Implementation authority**: current source code and tests; feature files never contain or sit beside a prose realization artifact.
- **Architecture authority**: the migrated root `specs/concorde/architecture.md` and recursive child module architecture files.
- **Prototype delivery**: one repository-wide attempt is justified because partial migration would
  leave selection, control-state routing, reflection triage, delivery, publication, guidance, fixtures,
  and self-hosted paths mutually incompatible.
