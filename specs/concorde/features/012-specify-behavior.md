---
id: feature.concorde.workflow.specify-behavior
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.workflow.manage-feature-workspaces
interfaces:
  provided:
    - interface.concorde.specify
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Specify Behavior

## Outcome and Scope

A maintainer can create or revise one level-local feature's complete outcome, interfaces, usage,
requirements, failures, related-feature links, and architecture zoom in its sole direct feature file.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.commands` | Supplies the design-only specification command and template. |
| `entity.concorde.coding-agent` | Authors/reviews the bounded feature design and quality checklist. |
| `entity.concorde.workspace-resolver` | Confirms the providing module and canonical flat feature path. |

## Interfaces

### `interface.concorde.specify` — Author one feature design

- **Consumer**: Maintainer defining or changing a module capability.
- **Direction**: Natural-language intent and bounded architecture to durable feature design/checklist.
- **Entry points**: `speckit.specify`, optionally followed by `speckit.clarify` or checklist review.
- **Inputs**: Feature description, providing module architecture, related feature IDs, and existing design when revising.
- **Outputs**: One validated `features/<NNN-name>.md`, `feature_path` selection pointer, and temporal requirements-quality checklist in the matching stable-ID control attempt after the post-front-matter workspace rerun.
- **Obligations**: Define every interface and architecture reference, make requirements testable, and avoid implementation prose.
- **Failures**: Unclear ownership, unresolved material ambiguity, or invalid entity/interface references block readiness.
- **Compatibility**: Creates no abstract, implementation, feature contract directory, feature diagram, or nested subfeature.
- **Implementing entities**: `entity.concorde.commands`, `entity.concorde.coding-agent`, `entity.concorde.workspace-resolver`.

## Usage Scenarios

1. Place a new feature at the module where every participating child module/entity is visible.
2. Author/revise outcome, embedded interfaces, representative usage, testable requirements, failures, relations, and architecture zoom.
3. Validate a temporal requirements-quality checklist and resolve only material ambiguities before planning.
4. For a new file, accept unavailable attempt fields on the first Protocol 12 gate, write valid stable-ID front matter, rerun the gate, then create only the returned checklist path.

## Requirements

- **FR-001**: Specification MUST author exactly one durable direct feature file and register its stable ID in one module architecture.
- **FR-002**: Every provided interface MUST define consumer/direction/entry points/inputs/outputs/obligations/failures/compatibility/implementing entities and example when custom serialized.
- **FR-003**: Every architecture zoom entity MUST resolve visibly and MUST NOT be retyped/reowned by the feature.
- **FR-004**: Requirements/scenarios MUST be independently testable, bounded, and free of implementation-detail authority.
- **FR-005**: Specification MUST NOT infer a stable feature ID from a planned path or create an attempt/checklist before Protocol 12 resolves the authored ID.

## Edge Cases

- The feature needs a new entity: architecture changes before/with the feature rather than defining it locally.
- A shared external interface is required by several features but provided by no Concorde feature.
