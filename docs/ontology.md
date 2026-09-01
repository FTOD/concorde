# Concorde ontology

Concorde's core idea is that modules are the hierarchy. Architecture explains what exists inside one
module and how it relates; features explain what that module provides and how a consumer uses it.

## Module

A module is the recursive unit of specification ownership. It has:

- one stable `module.*` identity;
- one responsibility and explicit boundary;
- one `architecture.md`;
- zero or more immediate child modules under `modules/`;
- zero or more level-local features under `features/`; and
- optional architecture-owned diagrams under `diagrams/`.

A parent architecture exposes each child as one bounded entity and does not duplicate the child's
internal inventory. Workflow attempts and reflections belong to project control state, not a module.

## Architecture specification

`architecture.md` is the module's single durable structural authority. It defines:

1. module identity, parent, responsibility, and boundary;
2. immediate child-module and feature inventories;
3. architecture-significant entities;
4. typed directed relationships among visible entities;
5. representative ordered or conditional interactions; and
6. optional diagram declarations with textual counterparts.

### Architecture entity

An architecture entity is a significant thing at the current level. Required fields are a stable
qualified ID, explicit type, non-circular definition, and either a safe project-relative
implementation path or an external/conceptual locator when applicable.

Preferred types adapt a code-oriented knowledge-graph vocabulary:

| Type | Use |
|---|---|
| `module` | Recursive specification/product boundary. |
| `package` | Importable or cohesive source unit. |
| `program` | Runnable multi-file application or command. |
| `directory` | Architecture-significant physical source/package directory. |
| `file` | Architecture-significant source or data file. |
| `script` | Runnable automation whose script identity matters. |
| `class` | Significant class/type. |
| `function` | Significant callable or method. |
| `interface` | Machine or human boundary entry point. |
| `data-store` | Persistent or shared state boundary. |
| `schema` | Executed structural validator/representation. |
| `configuration` | Behavior-shaping configuration surface. |
| `test-surface` | Executable evidence boundary. |
| `external-system` | Service/tool outside project ownership. |
| `concept` | Architecture-significant non-filesystem object. |

A project-defined type is allowed when these would distort the thing; its meaning must be explicit.
Architectures inventory significant boundaries and collaborations, not every symbol.

## Understand Anything adaptation

Concorde adapts, rather than adopts, the formal Understand Anything model pinned at
`ba450c43425f3de6d43daf76526950ad8ca93536`. That snapshot defines 27 node types and 38 directed edge
types. Its `module` is a broad logical package, `Layer` is a flat grouping, scripts normalize to
`file`, and `program` and `directory` node types are absent.

Concorde reuses useful code/system types and directed edge names, then adds the distinctions its
specification model needs. Recursive modules remain the sole hierarchy, stable module/feature/entity
IDs remain Concorde-owned, and logical entities stay separate from their physical file or directory
locators. The Understand Anything adapter maps those types and edges only as a projection; it never
changes Concorde ownership or turns a physical path into logical identity.

### Entity relationship

A relationship is typed, directed, and resolves both endpoints at the current module visibility.
Common predicates include `contains`, `imports`, `calls`, `implements`, `exposes`, `reads`, `writes`,
`produces`, `consumes`, `validates`, `renders`, and `depends-on`. A relationship may name the feature
interface that governs it.

### Interaction

An interaction describes an ordered or conditional collaboration among visible entities. It uses
the relationship graph, names the supported feature/interface where relevant, and stays at the
current module's abstraction level.

## Feature

A feature is one module-level usable capability. It has one stable `feature.*` identity, exactly one
providing module, and exactly one durable `<NNN-name>.md` directly below that module's `features/`.

The feature file contains:

- observable outcome and scope;
- successful, edge, and failure usage;
- user scenarios, requirements, assumptions, and success criteria;
- embedded provided and required interfaces;
- an Architecture Zoom over visible entity IDs;
- stable related-feature relationships; and
- evidence status (`unknown`, `partial`, `verified`, or `disagrees`).

Features never contain features. Composition, refinement, and dependency are explicit relationships
between stable IDs, including across an ancestor or immediate child module when allowed.

## Feature interface

An interface is the usable promise of a feature and is defined inside its owning feature file. Machine
APIs, human workflows, and generated artifacts all qualify. Each interface states:

- stable ID and owner;
- consumer and direction from the provider's perspective;
- entry points;
- input and output shapes/meaning;
- provider and consumer obligations;
- visible failure behavior;
- compatibility/migration policy;
- a representative example for custom representations; and
- implementing architecture entity IDs.

Stable `contract.*` values may remain as interface identities during the prototype. Identity does
not imply a separate document. Executed schemas/examples live with source or tests when executable;
their readable promise remains in the feature file.

## Architecture Zoom

The Architecture Zoom is the feature-specific explanation of which visible module entities participate
and how they collaborate for this capability. It may add behavioral detail but cannot redefine an
entity's identity, type, locator, module ownership, or structural relationship.

## Source code and evidence

Source code at the checked-out revision realizes entities and features. Tests and deterministic
checks provide evidence. `evidence_status` summarizes evidence confidence, not workflow completion.
Version history can explain implementation evolution without creating a competing prose authority.

## Attempt

An attempt is temporary work memory at `.concorde/attempts/<stable-feature-id>/`. It may contain a
plan, research, data model, quickstart, dependency-ordered tasks, reviewer checklists, and validation
evidence. It belongs to exactly one globally identified feature and may not be symlinked or mirrored
elsewhere. Renaming or moving the feature file preserves this binding; changing its stable ID while
work is active is rejected rather than guessed.

States are:

```text
absent → active → complete → absent after successful delivery
                     └→ preserved on any failed delivery
```

## Delivery

Delivery Proposal 8 captures the selected target, current source/attempt digest, exact removal path,
completion/evidence summaries, and retained authority digests. Apply revalidates the proposal and
atomically removes exactly one attempt. It changes no architecture, feature file, code, test,
projection, reflection, or selection state.

## Reflection

The tracked `.concorde/reflections/log.md` records difficulties, workarounds, deferrals, blockers,
and provisional design choices encountered by lifecycle phases. Entries have stable `R-NNN` IDs and
maintainer-owned status/notes. Reflections are process memory, not behavioral requirements, and are
never copied into another persisted artifact. Triage configuration shares the directory; triage
plans and worktrees are disposable.

## Projection

A generated site page, diagram output, index, package, or delivery report is a projection. It carries
input provenance and generator/version evidence, is reproducible, and never overrides its source.
Maintained architecture diagram JSON is explanatory source owned by a module; generated HTML remains
a projection.
