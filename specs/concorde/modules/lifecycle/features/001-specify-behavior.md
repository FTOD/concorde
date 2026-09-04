---
id: feature.lifecycle.specify-behavior
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.understanding.resolve-feature-workspace
    relation: depends_on
interfaces:
  provided:
    - interface.concorde.specify
  required: []
---

# Feature Design: Specify Behavior

## Outcome and Scope

A maintainer can create or revise one level-local feature's complete outcome, interfaces, usage,
requirements, failures, related-feature links, and architecture zoom in its sole direct feature file.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.specify-skill` | Supplies the design-only specification prompt that authors or revises the feature file. |
| `entity.concorde.coding-agent` | Authors and reviews the bounded feature design and quality checklist within the prompt's declared effects. |
| `module.concorde.understanding` | Supplies the feature-file format template and confirms the providing module, canonical flat path, and stable ID through Protocol 13. |
| `entity.lifecycle.attempt` | Receives the seeded requirements-quality checklist once the authored stable ID resolves. |

## Interfaces

### `interface.concorde.specify` — Author one feature design

- **Consumer**: Maintainer defining or changing a module capability.
- **Direction**: Natural-language intent and bounded architecture to durable feature design/checklist.
- **Entry points**: `concorde-specify`, optionally followed by `concorde-clarify` or
  `concorde-checklist` review.
- **Inputs**: Feature description, providing module architecture, related feature IDs, and existing design when revising.
- **Outputs**: One validated `features/<NNN-name>.md`, `feature_path` selection pointer, and temporal requirements-quality checklist in the matching stable-ID control attempt after the post-front-matter workspace rerun.
- **Obligations**: Define every interface and architecture reference, make requirements testable, and avoid implementation prose.
- **Failures**: Unclear ownership, unresolved material ambiguity, or invalid entity/interface references block readiness.
- **Compatibility**: Creates no abstract, implementation, feature contract directory, feature diagram, or nested subfeature.
- **Implementing entities**: `entity.lifecycle.specify-skill`, `entity.concorde.coding-agent`, `module.concorde.understanding`.

## Related Features

- `feature.concorde.workflow` is the root umbrella feature this phase realizes as the first stage of
  the end-to-end lifecycle.
- `feature.understanding.resolve-feature-workspace` supplies the Protocol 13 workspace resolution —
  providing module, ancestry, and canonical flat path — that specification depends on before authoring
  and again after a new stable ID is written.

## Usage Scenarios

1. Place a new feature at the module where every participating child module/entity is visible.
2. Author/revise outcome, embedded interfaces, representative usage, testable requirements, failures, relations, and architecture zoom.
3. Validate a temporal requirements-quality checklist and resolve only material ambiguities before planning.
4. For a new file, accept unavailable attempt fields on the first Protocol 13 gate, write valid stable-ID front matter, rerun the gate, then create only the returned checklist path.

## Requirements

- **FR-001**: Specification MUST author exactly one durable direct feature file and register its stable ID in one module architecture.
- **FR-002**: Every provided interface MUST define consumer/direction/entry points/inputs/outputs/obligations/failures/compatibility/implementing entities and example when custom serialized.
- **FR-003**: Every architecture zoom entity MUST resolve visibly and MUST NOT be retyped/reowned by the feature.
- **FR-004**: Requirements/scenarios MUST be independently testable, bounded, and free of implementation-detail authority.
- **FR-005**: Specification MUST NOT infer a stable feature ID from a planned path or create an attempt/checklist before Protocol 13 resolves the authored ID.

## Edge Cases

- The feature needs a new entity: architecture changes before/with the feature rather than defining it locally.
- A shared external interface is required by several features but provided by no Concorde feature.
