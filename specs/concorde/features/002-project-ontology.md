---
id: feature.concorde.define-project-ontology
kind: feature
module: module.concorde
related_features:
  - id: feature.concorde.workflow
    relation: depended_on_by
  - id: feature.auto-docs.create-project-docsite
    relation: depended_on_by
  - id: feature.understanding.explore-alignment
    relation: depended_on_by
  - id: feature.understanding.validate-architecture
    relation: depended_on_by
  - id: feature.understanding.initialize-architecture
    relation: depended_on_by
  - id: feature.concorde.evolve-protocol
    relation: depended_on_by
interfaces:
  provided:
    - contract.concorde.ontology
  required:
    - contract.understand-anything.knowledge-graph
---

# Feature Design: Adopt a Module and Capability Ontology

**Created**: 2026-08-31

**Revised**: 2026-09-04

**Input**: Preserve the module-centered durable specification and replace the flat command/example
concept with a structural capability hierarchy. Scripts are basic runnable tools; public or internal
skills are effect-declared leaves; operations are public LangGraph control graphs that compose
ordered Skills or Operations without cycles or flattening. Every operation Python source has an
associated Markdown skill and public capabilities are installed as user-facing skills.
Migrate ontology, architecture, package layout, installation, projection, validation, documentation,
tests, and maintained sources together. Partition modules by business capability, use case, or axis
of change rather than by artifact type, apply that partition to Concorde's own architecture, and
define Concorde Protocol as the complete normative selected-feature process that only the Concorde
repository both implements and self-applies.

## Outcome and Scope

A maintainer can enter the specification at any module, understand that module's architecture as a
graph of typed entities and interactions, then open one direct feature file to learn what the module
provides, how to use it, and how the relevant architecture entities collaborate. The `specs/` tree
contains only durable architecture, feature intent, required Archify system overviews, and optional
additional explanatory diagrams; project-level
workflow state is isolated under `.concorde/`.

This migration is repository-wide. It preserves the module-centered specification and control-state
model while changing Concorde's capability vocabulary, package layout, agent projection, workflow
runtime, installation, documentation, validation, fixtures, and maintained architecture.

## Target Specification Model

```text
<module>/
├── architecture.md             # the module's structure, entities, and interactions
├── diagrams/                   # required system overview + optional architecture-owned views
├── modules/<child>/            # immediate child modules with the same shape
└── features/
    └── <NNN-name>.md           # one complete durable feature specification

<project>/.concorde/
├── config.json                 # source-profile and root-module configuration
├── attempts/
│   └── <stable-feature-id>/    # temporary plan/tasks/evidence; absent after delivery
└── reflections/
    ├── index.json              # tracked allocation high-water only
    ├── pending/R-NNN.md        # recorded; triage pending
    ├── planned/R-NNN.md        # triaged; no maintainer input needed
    ├── needs-comments/R-NNN.md # triaged; waiting for User Comments
    ├── config.json             # triage configuration
    ├── plans/                  # disposable/ignored triage plans
    └── worktrees/              # disposable/ignored implementation worktrees
```

- A module is the only hierarchical specification unit. A child module is stored directly under its parent's `modules/` directory.
- `architecture.md` is the module's single architectural authority. It replaces `module.md`, the adjacent module `design.md`, and module-owned contract documents.
- A feature is specified exactly once as `features/<NNN-name>.md`. Features do not contain features; composition and refinement are explicit stable-ID relationships.
- Every `related_features` entry names its relation from one shared vocabulary: `composes`, `refines`, and `depends_on` are directional from the declaring feature to the target; `composed_by`, `refined_by`, and `depended_on_by` are their inverse forms so each side can state its own view; `relates_to` is symmetric. An entry is written as `{id, relation}`; a plain stable ID means `relates_to`. Each directional family is acyclic, and validation reports the cycle otherwise. Feature interfaces add a fourth directional family: a feature that requires an interface another feature provides depends on that provider, which the published feature graph exposes as a `requires` edge.
- The feature file contains its outcome, interfaces, usage, requirements, and architecture zoom. Its filename is storage/navigation; the stable feature ID remains semantic identity.
- `.concorde/` is project control state, outside the recursive specification hierarchy. It owns source-profile configuration, active attempts, and reflection workflow state.
- `.concorde/attempts/<stable-feature-id>/` is temporary workflow memory keyed by the feature's globally unique semantic identity rather than its mutable filename or module path. Successful delivery validates and removes it without changing the feature file or generating another durable narrative.
- `.concorde/reflections/<bucket>/R-NNN.md` files are tracked process memory filed by triage state (`pending/`, `planned/`, `needs-comments/`); `index.json` stores allocation metadata only. Triage configuration shares the directory, while plans and worktrees remain disposable and ignored.
- Source code is the implementation. Tests and deterministic checks are evidence. Generated sites, diagrams, indexes, and delivery results are disposable projections.
- Module `architecture.md` and direct feature files are also the maintained prose documentation.
  A root `docs/` tree is a duplicate authority and is rejected after its unique intent is reconciled
  into those owners; a repository README may orient checkout readers but is not a published content
  collection.
- Modules are partitioned by business capability, use case, or axis of change, never by artifact
  type or residual bucket (constitution A.VI). A module's responsibility is one capability a consumer
  could ask for; its features are use cases of that capability; it owns every Skill, Tool, Operation,
  template, schema, and rule that capability needs. The root module holds only project-wide features.
  Physical distribution directories such as flat `skills/` or `operations/` never determine module
  ownership: stable entity identity binds each artifact to the module whose use case it realizes.

### Capability Module Map

Concorde applies the partition to itself. Each child of `module.concorde` is one capability:

| Module | Capability | Owns, among others |
|---|---|---|
| `module.concorde.understanding` | Know what a project is. | Profile 7 model and loader, validation rules, initialization, bounded context, Protocol 13 and permission-role paths, planning context, alignment exploration, the init/context/ask/validate/constitution/plan-context Skills, feature and constitution templates. |
| `module.concorde.lifecycle` | Change one feature safely from specify to deliver. | The specify/clarify/checklist/plan-author/tasks/analyze/implement/converge/taskstoissues/deliver/fast-loop Skills, the plan and standard-loop Operations, attempts, Delivery Proposal 9, plan/tasks/checklist templates. |
| `module.concorde.reflections` | Record and resolve process problems. | Reflection Document v2, the per-file collection and index, the queue Tool, the triage Operation, investigator/implementer roles and their agent projections. |
| `module.concorde.capabilities` | Run any capability on a coding agent under an enforced policy. | Portable launchers and the Tool envelope, Skill/Operation source grammar and loader, capability validation, the Operation runtime, policy compiler, process launcher, managed launcher, Codex/Claude projection. |
| `module.concorde.distribution` | Ship and install the package. | Package Manifest 2 semantics, installer, managed runtime, framework projection, receipt. |
| `module.concorde.auto-docs` | Publish the validated read model. | Docsite scaffold and template, content registry, routes, Build Manifest 13, diagram rendering, atomic promotion. |

A module named after an artifact type (`skills`, `operations`, `runtime`, `scripts`, `models`) or a
residual bucket (`misc`, `common`, `shared`) is the signature of the partition this profile rejects.

## Architecture Authoring and Review Contract

The architecture's first job is to define the system's concepts and how they collaborate. Module
and file inventories are useful implementation navigation after that model is understood. For
Concorde the organizing concept is an Operation: a named callable unit exposed by one associated
Skill and realized by at least one executable Python script. A definition, its installed projection,
and a particular execution are different things. The shipped Package Manifest 2 specialization is
the paired LangGraph described below; it currently has exactly one primary `operation.py` per
Operation. The concept model does not turn existing public leaf Skills into registered Operations
or claim support for arbitrary script layouts.

Apply this review sequence when authoring or changing architecture:

1. Identify the project's own significant concepts from user intent and repository evidence. Define
   each once with a stable ID, type, non-circular meaning, owner, identity rule, lifetime, and source
   of truth. Separate definitions, runtime instances, payloads, and stored artifacts. Do not impose
   Concorde's Operation vocabulary on an unrelated product.
2. Define structural relationships with direction, cardinality, ownership, and invariants. Define
   execution dependencies separately from data handoffs; `calls` does not explain a payload.
3. For each entry point separate project configuration, caller runtime input, and host-derived
   context. Name initialization/default/change behavior. Define each input/output type ID and
   version, fields/types, requiredness, allowed values, empty/null behavior, and a conforming example.
4. For each handoff name the producer, consumer, governing interface, source fields, destination
   fields, transformation, artifact lifetime, and rejection behavior. References carry identity,
   safe locator, and freshness evidence; natural-language prior results are not a typed contract.
5. Walk one successful use and one missing/incompatible/stale-input failure using those definitions.
   A reader must be able to state what crosses every boundary without reading scripts or prompts.
6. Use an entity/component view for structure and a dataflow view when payload movement is the
   question. Give every diagram node/edge a textual counterpart. Do not use a DFD as the sole
   ownership model or a stage-order diagram as evidence of data compatibility.
7. Compare against actual code and tests. Name concrete current gaps and their owning feature;
   label future contracts as target design and keep current invocation examples truthful. Do not
   silently change runtime metadata or claim a schema/validator exists because prose requires it.

An architecture review reports missing definitions and broken handoffs as primary findings, ahead
of folder-layout or diagram polish. Structural validation checks references and shape; these
semantic questions require review. Initialization's minimal seed is only a boundary scaffold and
must be expanded from project evidence before being described as a complete product model.

For Concorde, the [root concept model](../architecture.md) owns shared abstractions;
[Operation data contracts](../modules/capabilities/features/002-provide-capability-surfaces.md#operation-data-contract)
own the common JSON transport; domain payload fields stay with the feature that provides them.

## Current Capability Source Model (Package Manifest 2)

```text
<project>/
├── scripts/                              # basic deterministic runnable tools
├── skills/
│   └── <skill-name>/
│       └── SKILL.md                      # one public/internal effect-declared leaf
└── operations/
    └── <operation-name>/
        ├── operation.py                  # one acyclic mixed-capability LangGraph
        └── SKILL.md                      # required user-facing operation skill
```

- A Tool script in the current `scripts/` inventory exposes a basic deterministic Tool. It may
  parse inputs and inspect or mutate within its explicit contract; that inventory contains no
  conversational graph. An Operation Python entry point is also an executable script in the project
  concept model, but is inventoried under `operations/`, not under Tool scripts.
- A skill is a leaf capability whose canonical authority is one `skills/<skill-name>/SKILL.md`. It
  may invoke scripts/tools, but it does not orchestrate multiple skills into a loop. Its metadata
  declares `exposure: public|internal` and, when composed, exact read/write/network/credential
  `effects`; internal leaves remain package/runtime inputs and do not project to users.
- An operation is the next structural level above skills. Its `operation.py` uses LangGraph to
  compose two or more ordered direct leaf Skills or public Operations with state, branching, retries,
  review gates, or other explicit controls. Nested Operations remain opaque; direct and indirect
  composition cycles are invalid.
- Every operation has exactly one associated `SKILL.md` in the same directory. The Python graph is
  execution authority; the Markdown file is its user-facing invocation and behavioral contract.
- Installation packages every leaf and Operation pair but projects only public leaves plus every
  operation `operations/*/SKILL.md` into the selected agent's skill directory. Operation Python
  remains installed under the framework package and is invoked by its projected skill.
- Every direct leaf occurrence has one exact narrowing binding. Trusted runtime code resolves
  Protocol 13 roles into concrete paths, renders Codex/Claude/outer enforcement, and supplies one
  immutable launch specification and matching receipt; a stage never shares its permission union.
- `commands/` is obsolete because its Markdown files are skills, not commands. `examples/` is
  obsolete for maintained LangGraph loops because those graphs are operations, not illustrative code.
- A mixed layout is invalid: no canonical prompt may remain under `commands/`, and no maintained
  operation Python may lack its paired Markdown skill.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Module` | The recursive unit of specification ownership. A module has one responsibility, one boundary, one `architecture.md`, zero or more immediate child modules, and zero or more level-local features. | `contains` → `Module`; `specifies` → `Feature`; `owns` → `Architecture specification` |
| `Feature relation` | The typed, directed meaning of one `related_features` entry: `composes` (the declaring feature sequences the target as a part), `refines` (it narrows or extends the target's behavior), `depends_on` (it needs the target's promise), their inverse forms, or symmetric `relates_to`. Directional families stay acyclic. | `connects` → `Feature`; `projected as` → feature graph edge; `explained by` → Related Features prose |
| `Concorde Protocol` | The complete normative process by which a selected feature is resolved, permission-bounded, specified, planned, executed, validated, reflected on, and delivered, together with its Source Profile and control-state authority rules. Feature Workspace Protocol is one serialized component, not a synonym. | `governs` → `Understanding`, `Lifecycle`, `Reflections`, `Capabilities`; `consumed by` → every Concorde project; `defined, implemented, and self-applied by` → Concorde repository |
| `Agent mutation worktree` | The default Git boundary for any coding-agent mutation: one unique linked worktree created from the primary worktree's exact committed `HEAD` before planning or control creation; primary dirty state is excluded unless the maintainer explicitly authorizes that boundary. | `depends on` → `Git`; `isolates` → `Coding agent`; `precedes` → mutating lifecycle work |
| `Protocol evolution` | The Concorde-repository-only, explicitly authorized change boundary for any normative Concorde Protocol semantic change: one exact committed Git base, one isolated worktree that excludes primary dirty state, no attempt/lifecycle/delivery, complete target validation, and one reviewable cutover commit. | `evolves` → `Concorde Protocol`; `depends on` → `Git`; `refines` → normal Concorde workflow |
| `Capability module` | A module bounded by one business capability, use case, or axis of change. It owns every kind of artifact its capability needs and never collects one artifact kind across capabilities. | `is a` → `Module`; `owns` → `Skill`, `Tool`, `Operation`, `Feature`; `rejects` → artifact-type layer, residual bucket |
| `Architecture specification` | A module's single durable account of its typed entities, organization, relationships, and interactions. | `defines` → `Architecture entity`; `defines` → `Entity relationship`; `replaces` → `Module summary`; `replaces` → `Module design reference` |
| `Architecture entity` | An architecture-significant module, package, program, file, script, class, function, interface, data store, schema, configuration, test surface, external system, or other explicitly typed thing. | `belongs to` → `Module`; `participates in` → `Entity relationship`; `realized by` → `Source code` |
| `Entity type` | A preferred classification that tells a reader what an architecture entity is. Concorde adapts Understand Anything's code-oriented node vocabulary but permits project-defined types with an explicit meaning. | `classifies` → `Architecture entity` |
| `Entity relationship` | A typed, directed structural or behavioral connection between architecture entities, such as contains, imports, calls, implements, exposes, reads, writes, produces, consumes, validates, renders, or depends on. | `connects` → `Architecture entity`; `governs` → `Interaction` |
| `Interaction` | An ordered or conditional collaboration among architecture entities described at the current module level. | `uses` → `Entity relationship`; `supports` → `Feature` |
| `Tool` | One basic deterministic runnable capability, normally exposed by a script or program entry point. It performs a bounded action but does not compose conversational skills. | `implemented by` → `Script`; `invoked by` → `Skill`; `returns` → `Tool result` |
| `Script` | Executable source entry point. A Tool script exposes bounded deterministic actions; an Operation script executes its callable definition. Package Manifest 2 inventories these separately under scripts/ and operations/. | `realizes` → `Tool` or `Operation`; `invoked by` → `Skill` or runtime |
| `Skill` | One public or internal leaf capability defined by a canonical `skills/<skill-name>/SKILL.md`. Its complete prompt may call tools, contains no multi-skill loop, and owns integration-neutral effects when composed. | `invokes` → `Tool`; `composed by` → `Operation`; `declares` → `Exposure`; `declares` → `Effects`; `projected to` → `Agent skill` when public |
| `Operation` | A stable named callable definition exposed by one associated Skill and realized by at least one executable Python script with one primary entry point. The current Manifest 2 specialization is a paired controlled LangGraph; a particular invocation is a separate entity. | `exposed by` → `Operation skill`; `realized by` → `Script`; `instantiated by` → invocation; composite specialization `composes` → `Skill` or `Operation` |
| `Operation skill` | The required Markdown surface paired with an operation Python graph and installed to users as an agent skill. | `describes` → `Operation`; `invokes` → `operation.py`; `projected to` → `Agent skill` |
| `Exposure` | `public` makes a leaf projectable; `internal` keeps it package-loadable only for Operations. Operations are always public. | `controls` → `Agent skill`; `declared by` → `Skill` |
| `Effects` | Leaf-owned path-role reads/writes plus network and credential posture that Operation bindings may narrow but never widen. | `declared by` → `Skill`; `compiled by` → `Operation runtime`; `enforced by` → `Coding-agent sandbox` |
| `Stage` | One named node or controlled step inside an operation, containing one or more ordered direct capability occurrences plus explicit state/control semantics. | `part of` → `Operation`; `uses` → `Skill` or `Operation`; `transitions to` → `Stage` |
| `Feature` | One module-level functionality or interface that a consumer can use, specified in one durable `features/<NNN-name>.md` file. | `belongs to` → `Module`; `exposes` → `Feature interface`; `zooms into` → `Architecture entity`; `relates to` → `Feature` |
| `Feature file` | The direct Markdown authority for one feature; its filename supplies navigation while its front-matter `feature.*` ID supplies semantic identity. | `specifies` → `Feature`; `belongs to` → `Module`; `corresponds to` → `Attempt` |
| `Feature interface` | The human-readable entry points, inputs, outputs, obligations, failures, and compatibility expectations through which a feature is used. Existing stable `contract.*` identifiers remain valid prototype interface identities. | `part of` → `Feature`; `implemented by` → `Architecture entity`; `replaces` → `Architecture contract` |
| `Architecture zoom` | A feature-local explanation of which entities from its module architecture participate and how they collaborate for that feature. It adds behavioral detail without redefining entity identity or ownership. | `part of` → `Feature`; `references` → `Architecture entity`; `explains` → `Interaction` |
| `Source code` | The executable files and symbols that are the actual implementation at the checked-out revision. | `realizes` → `Architecture entity`; `implements` → `Feature`; `evidenced by` → `Test` |
| `Project control state` | Tracked or disposable workflow metadata below `<project>/.concorde/`; it is neither product specification nor generated publication. | `configures` → `Module`; `contains` → `Attempt`; `contains` → `Reflection collection` |
| `Attempt` | Temporary planning, task, research, checklist, and validation memory at `.concorde/attempts/<stable-feature-id>/`, corresponding to one selected feature identity. | `belongs to` → `Feature`; `changes` → `Source code`; `removed by` → `Delivery` |
| `Reflection collection` | Tracked `.concorde/reflections/<bucket>/R-NNN.md` documents, one detailed problem per file filed under `pending/`, `planned/`, or `needs-comments/` by triage state, plus a metadata-only `index.json`. | `belongs to` → `Project control state`; `records` → `Feature work` |
| `Delivery` | The terminal cleanup tool that proves a completed attempt is eligible and removes its temporal workspace; it does not author an implementation narrative. | `validates` → `Attempt`; `retains` → `Feature`; `retains` → `Source code` |

## Architecture Zoom

This feature governs the following root-architecture entities; their definitions and relationships belong in `specs/concorde/architecture.md`:

| Entity ID | Type | Role in this feature |
|---|---|---|
| `entity.concorde.operation` | concept | Defines the project-wide callable unit independently of its physical source paths. |
| `entity.concorde.operation-invocation` | concept | Separates one execution from the definition and the feature attempt. |
| `entity.concorde.data-handoff` | type | Names typed producer/consumer mappings, distinct from control order. |
| `module.concorde.understanding` | module | Discovers and models recursive `architecture.md` modules, direct feature files, typed entities/relations, interfaces, control-state attempts/reflections, evidence, and projections; resolves Protocol 13; validates the profile. |
| `module.concorde.capabilities` | module | Realizes the Script/Tool, Skill, and Operation structure, its metadata grammar, package capability validation, and public projection. |
| `module.concorde.lifecycle` | module | Owns the stable-ID attempt and cleanup-only delivery that this profile defines. |
| `module.concorde.auto-docs` | module | Publishes module architecture and direct feature files without interpreting a wrapper directory or `design.md` basename. |
| `entity.concorde.protocol` | interface | Owns the complete normative process definition and distinguishes it from Feature Workspace Protocol 13. |
| `entity.concorde.protocol-cutover` | pipeline | Evolves Protocol semantics directly in one isolated, attempt-free, target-valid Git transition. |
| `entity.concorde.git` | external-system | Supplies exact committed bootstrap checkpoints, default per-agent linked worktrees, diff/commit review, merge, abandonment, and revert while excluding primary dirty state from implicit authority. |
| `entity.concorde.specification` | directory | Self-applies the profile across six capability modules and twenty-six features. |
| `entity.concorde.control-state` | directory | Owns Profile 7 configuration, stable-ID attempts, tracked reflections, and triage state outside module specifications. |
| `entity.concorde.source-code` | package | Realizes every module's programs; its subpackages mirror the capability modules. |

The feature is cross-cutting because these entities share one source profile. They must switch together; a mixed old/new durable layout is invalid after migration.

## Interfaces

### `contract.concorde.ontology` — Module-centered specification profile

- **Consumer**: Maintainers, coding agents, validators, installers, operation runtimes, and documentation/exploration projections.
- **Direction**: Profile and capability sources plus tool/operation requests to validated bounded structure, installed skills, controlled graphs, and lifecycle results.

- **Entry points**: A module's `architecture.md`; a direct `features/<NNN-name>.md`; Protocol 13
  workspace JSON; `scripts/`; leaf `skills/*/SKILL.md`; paired
  `operations/*/{operation.py,SKILL.md}`; deterministic initialization, context, validation, and
  delivery tools.

- **Inputs**:

- a configured root module and recursively nested `modules/` tree;
- architecture front matter and the required entity/relationship/interaction sections;
- feature front matter, embedded interface definitions, architecture references, requirements, and usage scenarios;
- optional project control state containing `.concorde/attempts/<stable-feature-id>/` and tracked
  `.concorde/reflections/<bucket>/R-NNN.md` documents.
- canonical public/internal leaf sources with effects and paired operation Python/Markdown sources
  with ordered capabilities and occurrence bindings.

- **Outputs**:

- a bounded module or feature context with stable IDs and canonical paths;
- deterministic findings for invalid structure or unresolved semantic references;
- generated navigation and architecture views with source provenance;
- installed public-leaf and operation skill surfaces with source/kind/policy provenance;
- a delivery result that lists removed temporal artifacts and retained durable/code authorities.

- **Obligations**: Producers define each architecture-significant entity once at its owning module,
  use stable IDs for every cross-reference, keep feature interfaces in the owning design, distinguish
  code/test reality from prose/projections, keep Skills leaf-level, declare exposure/effects, keep
  Operation nesting acyclic and opaque, and pair every Operation Python graph with the Markdown skill
  installed to users. Every direct leaf launch is deny-by-default and narrowing-only.

- **Failures**: Resolution or validation fails on unsafe paths, duplicate IDs, cyclic module
  containment, untyped entities, unresolved relationships, missing interface semantics, legacy
  durable files, residual `commands/` or `examples/` capability sources, unpaired operation files,
  non-leaf skills, unknown effects, internal projection, missing/mismatched occurrence policy,
  Operation cycle, or ambiguous ownership; delivery failures preserve the complete attempt.

- **Compatibility**: Profile 7 / Protocol 13 are an intentional breaking control-state path revision
  with no dual-layout mode. Initialization Proposal 4 adds the reflection allocation index and
  required root system overview. Reflection Document v2 replaces the single-file log. Stable
  module/feature/interface IDs, Delivery Proposal 9 semantics, and Build Manifest 13 semantics remain unchanged.
- **Implementing entities**: `module.concorde.understanding`, `module.concorde.capabilities`, `module.concorde.lifecycle`, `entity.concorde.specification`, `entity.concorde.control-state`.
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
- **Implementing entities**: `module.concorde.understanding`, `entity.concorde.specification`.
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
   workspace gate runs, **Then** Protocol 13 returns no guessed feature ID or attempt path; after the
   feature is written with a valid stable ID, a required second resolution returns its exact control-state paths before checklist creation.

### User Story 4 - Validate and Deliver the Migrated Project (Priority: P2)

As a maintainer, I can validate that the entire project uses the new ontology and deliver a completed attempt without generating or retaining redundant implementation prose.

**Independent Test**: Run complete Concorde validation, Python tests, docsite tests/build, package verification, and delivery on the selected ontology feature; verify zero legacy durable artifact names remain and delivery removes only its attempt.

**Acceptance Scenarios**:

1. **Given** any `module.md`, adjacent module `design.md`, feature `abstract.md`, feature `implementation.md`, nested `subfeatures/`, or specification-owned contract document remains, **When** validation runs, **Then** it reports a migration error with the canonical replacement.
2. **Given** all tasks and checklists are complete and validation passes, **When** delivery is invoked,
   **Then** it removes exactly `.concorde/attempts/<stable-feature-id>/`, retains `architecture.md`,
   the direct feature file, source code, tests, and `.concorde/reflections/`, and reports their digests.
3. **Given** a delivery is ineligible or stale, **When** it is attempted, **Then** no durable source, code, test, or attempt artifact is changed.

### User Story 5 - Compose and Install Structured Capabilities (Priority: P1)

As a workflow author, I can discover basic tools under Scripts, public/internal effect-declared leaf
capabilities under Skills, and controlled acyclic mixed-capability LangGraphs under Operations
without treating all Markdown prompts as flat commands.

**Independent Test**: Install a package containing public/internal leaves and nested Operations, then
verify only public leaves plus every Operation appear as agent skills, paired Markdown points to
installed Python, internal leaves remain package-loadable, and deterministic validation rejects
missing effects/bindings, cycles, or pair members.

**Acceptance Scenarios**:

1. **Given** a leaf capability, **When** its source is inspected, **Then** exactly one canonical
   `skills/<name>/SKILL.md` owns its prompt and contains no multi-skill graph topology.
2. **Given** a LangGraph that composes several skills, **When** its source is inspected, **Then** it
   lives at `operations/<name>/operation.py` beside exactly one associated `SKILL.md` that exposes it
   to users.
3. **Given** an installation for Codex or Claude, **When** capabilities are projected, **Then** public
   leaf Skills and Operation skills share the agent namespace, internal leaves stay unprojected, and
   graph Python remains in the installed framework.
4. **Given** a basic deterministic runnable entry point, **When** it is classified, **Then** it remains
   a Script/Tool and is not promoted to a Skill or Operation unless a corresponding user capability
   or multi-skill graph actually exists.

### User Story 6 - Find a Capability in One Module (Priority: P1)

As a maintainer, I can name a capability Concorde provides, such as planning or reflection triage,
open exactly one child module, and find every Skill, Tool, Operation, template, and rule that
capability needs, without visiting a module for each artifact kind.

**Independent Test**: For each maintained child module, verify that its responsibility is one
capability sentence, that each of its features is a use case of that capability, that no child module
is named after an artifact type or residual bucket, and that the root module holds only project-wide
features.

**Acceptance Scenarios**:

1. **Given** a change to how planning selects its context, **When** the affected modules are listed,
   **Then** the understanding and lifecycle modules own every affected artifact and no artifact-type
   layer module exists to be touched.
2. **Given** a proposed module whose only honest responsibility is "contains all X", **When**
   initialization, specification, planning, or analysis guidance evaluates it, **Then** the
   partition is routed back to architecture work and deterministic validation reports the name as
   an advisory finding.

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
- Reflection triage plans/worktrees are ignored while individual reflection documents and the allocation index remain tracked.
- A skill directory contains graph-control Python and therefore is not a leaf capability.
- An operation contains `operation.py` but no `SKILL.md`, or contains a Markdown surface with no graph.
- An operation skill is projected to an agent while its Python graph is absent from the installed framework.
- Two operations compose the same leaf skill in different stage orders without changing that leaf's canonical prompt.

## Related Features

- `feature.concorde.workflow` depends on this ontology for the module, feature, interface, and
  relation model every lifecycle phase reads and writes.
- `feature.auto-docs.create-project-docsite` depends on this ontology for the page kinds and file
  roles the docsite publishes.
- `feature.understanding.explore-alignment` depends on this ontology for the stable identities it
  projects beside implementation evidence.
- `feature.understanding.validate-architecture` depends on this ontology for the layout, identity,
  relation, and vocabulary rules it enforces deterministically.
- `feature.understanding.initialize-architecture` depends on this ontology for the minimal root
  scaffold it proposes.
- `feature.concorde.evolve-protocol` depends on this ontology for the Concorde Protocol identity,
  component boundary, self-application distinction, and isolated evolution semantics.

## Requirements

### Functional Requirements

- **FR-001**: The specification hierarchy MUST be a recursive tree of modules rooted at the configured project module; features MUST NOT be hierarchy containers.
- **FR-002**: Every module MUST contain exactly one durable `architecture.md` and MAY contain only
  immediate `modules/`, direct level-local `features/*.md`, and architecture-owned `diagrams/` in
  addition to that architecture; attempts and reflection documents MUST NOT live in the specification tree.
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
- **FR-015**: Protocol 13 MUST expose `feature_path`, providing module architecture, bounded module
  ancestry, bounded related-feature summaries, stable-ID-derived attempt paths/state,
  `.concorde/reflections/`, and code/test discovery context without module-local control state or
  removed authority fields.
- **FR-016**: Specification, clarification, planning, task generation, analysis, convergence, implementation, fast-loop, initialization, context, validation, and delivery guidance MUST use the new authority model consistently in canonical and installed surfaces.
- **FR-017**: Initialization MUST propose a minimal root `architecture.md` with a valid typed
  entity/relationship scaffold, its Archify system overview, and initialize `.concorde/reflections/index.json`; when explicitly requested,
  it MAY add one direct feature file and its stable-ID attempt mapping, but MUST NOT create module-local
  attempts or feature wrapper directories. The five-file initialization transaction MUST use
  Initialization Proposal 4.
- **FR-018**: Validation MUST deterministically check canonical direct-file layout, module cycles,
  unique/path-safe stable IDs, entity types and locators, relationship endpoints, stable-ID attempt
  mapping, related-feature references, embedded interface completeness, architecture zoom references,
  one showcase Archify system overview per module with principal entity relationships, control-state
  safety, and legacy residue without mutating sources.
- **FR-019**: Documentation generation MUST publish only `architecture.md` as each module landing
  page and each direct feature file as one feature landing page, preserve source provenance, publish
  architecture-owned diagrams, exclude README and `.concorde/` control state from public content
  discovery, and reject a root `docs/` tree as a parallel prose authority.
- **FR-020**: Delivery MUST require complete tasks and existing checklists plus current validation
  evidence, then remove exactly `.concorde/attempts/<stable-feature-id>/` without writing or moving the
  feature file or reflection collection; ineligible, unsafe, ambiguous, or stale delivery MUST be non-mutating.
- **FR-021**: Every maintained Concorde module and feature specification, fixture, schema/example reference, test, guide, manifest, and generated-source expectation MUST migrate in the same prototype milestone; mixed-profile support is out of scope.
- **FR-022**: The full migrated repository MUST contain no stale semantic references that treat
  abstracts, accepted implementation narratives, module summaries/design references, nested
  subfeatures, architecture-owned contracts, module-local attempts, or specification-root reflections
  as current authorities.
- **FR-023**: Protocol 13 MUST NOT derive a stable feature ID from a planned filename. Before a new
  feature exists, specify-phase attempt fields MUST be explicitly unavailable; after the feature file
  declares a valid ID, specification MUST re-resolve the workspace before creating its checklist or attempt.
- **FR-024**: Concorde capability sources MUST use exactly three structural layers: basic runnable
  tools under `scripts/`, public/internal leaf capabilities under `skills/<skill-name>/SKILL.md`, and
  controlled acyclic mixed-capability LangGraphs under `operations/<operation-name>/`.
- **FR-025**: Every canonical Skill MUST be one leaf `SKILL.md` that may invoke Scripts/Tools but MUST
  NOT define a loop or graph that orchestrates multiple Skills.
- **FR-026**: Every canonical Operation MUST contain exactly one `operation.py` LangGraph and exactly
  one associated `SKILL.md`; either file without its pair MUST be invalid.
- **FR-027**: An Operation MUST compose at least two ordered direct canonical Skills or public
  Operations, MUST remain acyclic and keep nested Operation internals opaque, and MUST define stage
  order, occurrence policies, state, failure propagation, and branching/retry/review controls in
  Python rather than duplicating or flattening prompt bodies.
- **FR-028**: Installation MUST include every leaf Skill plus every complete
  Operation pair, project only public leaves plus all Operation Markdown surfaces into the selected
  agent namespace, and keep internal leaves and Operation Python under the installed framework.
- **FR-029**: The canonical capability layout MUST contain no `commands/` directory and no maintained
  LangGraph under `examples/`; validation, tests, docs, and manifests MUST reject or omit those legacy
  concepts after migration.
- **FR-030**: Canonical Skill and Operation identities MUST be safe, unique, stable across source and
  installed layouts, and traceable from projected agent skill back to its owning source and, for an
  Operation, its paired graph.
- **FR-031**: Every Operation-composed leaf MUST declare exact effects and every direct occurrence
  MUST have one order-matched narrowing policy; concrete unsafe/unresolved paths, widened policy,
  missing native/outer enforcement, or stale receipt MUST stop before launch.
- **FR-032**: Module decomposition MUST follow business capability, use case, or axis of change
  (constitution A.VI); the constitution, the feature and constitution format references, and the
  initialization, specification, planning, and analysis guidance MUST state and check that rule
  before a module is created, split, merged, or renamed.
- **FR-033**: Deterministic validation MUST report, at warning severity and without failing the
  project, any child module whose ID or directory names an artifact type or residual bucket.
- **FR-034**: Concorde's own specification MUST be partitioned into the capability modules
  `understanding`, `lifecycle`, `reflections`, `capabilities`, `distribution`, and `auto-docs`; the
  root MUST hold only genuinely project-wide features—the end-to-end workflow, this ontology, and
  Concorde Protocol evolution—while every capability-local feature MUST be a use case of exactly one
  child capability module.
- **FR-035**: `src/concorde` and `tests/concorde` MUST be organized into subpackages that mirror the
  capability modules, and every architecture entity locator MUST resolve to the owning subpackage.
- **FR-036**: Every `related_features` entry MUST be a stable feature ID or an `{id, relation}` object
  whose relation is `composes`, `refines`, `depends_on`, `composed_by`, `refined_by`,
  `depended_on_by`, or `relates_to`; a plain ID MUST be read as `relates_to`; the loader, validator,
  bounded context, Protocol 13 summaries, templates, and authoring guidance MUST carry the relation.
- **FR-037**: Validation MUST reject an unknown relation, a self-reference, and any cycle in the
  `composes`, `refines`, or `depends_on` family after inverse forms are normalized, naming every
  feature on the cycle.
- **FR-038**: The ontology MUST define Concorde Protocol as the complete normative selected-feature
  process and MUST distinguish it from Feature Workspace Protocol, which is one serialized component.
- **FR-039**: Every Concorde project MUST consume Concorde Protocol, while only the Concorde repository
  MAY define, implement, and self-apply it; every normative semantic change in that repository MUST
  use `feature.concorde.evolve-protocol` rather than an attempt, fast loop, standard loop, or delivery.
- **FR-040**: Every agent-authored mutation MUST use one committed-base linked worktree before
  planning, selection persistence, or attempt/checklist/reflection creation unless the maintainer
  explicitly authorizes primary-worktree mutation. Primary staged, unstaged, untracked, and ignored
  paths MUST remain outside authority and untouched; deterministic mutating entry points MUST reject
  the primary worktree by default and expose only an explicit override.

- **FR-041**: Architecture authoring and review MUST start with project concepts, identity,
  ownership, lifetime, and relationship cardinality; implementation inventories alone are incomplete.
- **FR-042**: Significant data handoffs MUST name producer/consumer, payload type/version, field
  mapping, governing interface, reference lifetime, and missing/incompatible/stale-data behavior.
- **FR-043**: Interface review MUST distinguish initialized project configuration, caller runtime
  input, and host-derived context; fixed type IDs require readable field definitions and examples.
- **FR-044**: Review MUST explicitly distinguish target design from code-supported contracts;
  validation success MUST NOT be presented as evidence that an unimplemented JSON ABI is available.

## Success Criteria

- **SC-001**: 100% of maintained and fixture modules use the canonical `architecture.md` layout, and 100% of maintained and fixture features are direct `features/<NNN-name>.md` files with zero feature directories.
- **SC-002**: 100% of maintained module architecture entity and relationship references and feature architecture-zoom/interface entity references resolve with zero validation findings.
- **SC-003**: A maintainer can identify what any sampled architecture entity is, where it is realized, and how it relates to its neighbors in under three minutes from one module architecture.
- **SC-004**: A maintainer can identify how to use any sampled feature, including inputs, outputs, failures, and participating entities, in under three minutes from its single design.
- **SC-005**: Workspace JSON and all Skill/Operation contracts contain `feature_path`, Protocol 13,
  `.concorde/attempts/<stable-feature-id>/`, and `.concorde/reflections/`, with zero module-local
  control-state or other deprecated authority fields.
- **SC-006**: Complete Python, documentation-site, native package, agent-surface, and Concorde validation suites pass under the new source profile.
- **SC-007**: The selected ontology attempt is delivered successfully from
  `.concorde/attempts/feature.concorde.define-project-ontology/`, that directory is absent afterward,
  and both `specs/concorde/features/002-project-ontology.md` and `.concorde/reflections/` remain
  byte-identical through delivery.
- **SC-008**: A planned-feature fixture receives no guessed attempt path on its first Protocol 13
  specify resolution and receives the exact stable-ID path only after its feature front matter exists.
- **SC-009**: 100% of canonical leaf capabilities reside under `skills/*/SKILL.md`, with zero
  canonical capability prompts under `commands/`.
- **SC-010**: 100% of operation directories contain exactly one `operation.py` and one `SKILL.md`,
  every capability/binding/cycle check passes, and the standard loop nests public `concorde-plan`
  without embedding its private leaves or prompt bodies.
- **SC-011**: Fresh Codex and Claude installations expose exactly 15 public leaves plus three
  Operations, package both internal planner leaves, and include every paired Operation Python graph
  under `.concorde/framework/operations/`.
- **SC-012**: Complete Python, installation, agent-surface, documentation, and validation
  tests contain zero current terminology that classifies leaf prompts as commands or maintained
  LangGraphs as examples.
- **SC-013**: No maintained child module is named after an artifact type or residual bucket, every
  root feature is genuinely project-wide, every child module declares at least one use-case feature,
  and no child module has a feature whose outcome is an inventory of what it contains.
- **SC-014**: A change that touches one capability (for example how planning selects its context)
  changes architecture files in at most two capability modules and no artifact-type layer.
- **SC-015**: Every maintained Concorde feature declares a typed relation for each related feature,
  the three directional families are acyclic, and the published feature graph reproduces every
  declaration as one typed edge.
- **SC-016**: Canonical and projected mutating capabilities name the same committed-base isolation
  rule, and executable preflight tests reject a primary worktree, accept a linked worktree at the
  committed base, and prove primary dirty files do not appear in that linked worktree.

## Assumptions

- This is an intentionally breaking prototype source profile; no compatibility reader for the old layout is required after the repository itself migrates.
- Architecture inventories include only entities significant to understanding structure, evolution, interfaces, or risk. Concorde does not require a duplicate row for every implementation symbol.
- Understand Anything supplies a useful code-entity and relationship vocabulary, but Concorde remains authoritative for recursive modules, feature interfaces, attempts, evidence, and specification ownership.
- The artifact-type module IDs `module.concorde.skills`, `module.concorde.operations`,
  `module.concorde.runtime`, and `module.concorde.workspace` are retired without alias; their
  features, entities, and module-prefixed `contract.*` IDs moved to the owning capability modules
  with new stable IDs, while `interface.concorde.*` and `contract.concorde.*` identities are
  preserved. Legacy Commands-owned identities migrated to Skills/Operations identities as one
  intentional breaking change.
- Stable feature IDs are globally unique and restricted to a path-safe grammar. The exact stable ID
  deterministically names its `.concorde/attempts/` directory; renaming a feature file does not move
  active work, while changing the stable ID with active work is rejected rather than guessed.
- Per-file reflections, their allocation index, and active attempt files are tracked reviewable state. Reflection-triage plans,
  worktrees, and legacy compatibility assets remain ignored/disposable.
- A primary worktree may contain another programmer's in-progress tracked or untracked changes;
  committed `HEAD`, not those transient bytes, is the default agent bootstrap authority.
- Each module owns one required Archify architecture system overview; other architecture-owned JSON
  diagrams remain optional supporting sources. Feature-specific dynamic diagrams are either promoted
  to the providing module's diagram set or retired; they do not restore a multi-file feature specification.
- Git history is sufficient durable milestone history after delivery removes temporal attempt evidence. Current code and tests, not a generated narrative, describe the accepted implementation.

## Out of Scope

- Automatically extracting a complete entity graph from source code.
- Proving semantic completeness of a human-authored entity inventory beyond deterministic structural/reference checks.
- Maintaining a dual reader or automated downgrade path for the old source profile.
- Supporting both feature directories and direct feature files after the repository cutover.
- Supporting module-local attempts or a specification-root reflection document after the control-state cutover.
- Supporting multiple concurrent attempts for one stable feature ID; separate branches/worktrees remain the prototype mechanism.
- Renaming every preserved `contract.*` stable identity to `interface.*` during the prototype.
- Replacing Archify, Docusaurus, or the supported coding-agent platforms.
- Defining a general-purpose visual or declarative Operation DSL beyond the required Python/Markdown pair.

## Concorde Architecture Alignment

- **Stable feature ID**: `feature.concorde.define-project-ontology`
- **Providing module**: `module.concorde`
- **Related features**: every Concorde workflow and publication feature participates because the source profile is shared; the capability module map above names their owners.
- **Interface**: this design embeds `contract.concorde.ontology`; the former standalone ontology contract is removed during migration.
- **Implementation authority**: current source code and tests; feature files never contain or sit beside a prose realization artifact.
- **Architecture authority**: the migrated root `specs/concorde/architecture.md` and recursive child module architecture files.
- **Protocol evolution**: the original repository-wide attempt exposed the self-reference recorded
  by R-036. Future normative Concorde Protocol changes use one direct isolated-worktree cutover with
  no attempt or delivery, preserving a valid base until the complete target passes validation.
