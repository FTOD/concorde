---
id: feature.[namespace].[outcome]
kind: feature
module: module.[namespace]
related_features: []
# Each entry is {id, relation}; relation is composes | refines | depends_on | composed_by |
# refined_by | depended_on_by | relates_to. A plain ID means relates_to. Directional families stay
# acyclic. Example:
#   - id: feature.[namespace].[other]
#     relation: depends_on
interfaces:
  provided: []
  required: []
---

# Feature Design: [FEATURE NAME]

**Input**: [Original user or product intent]

<!--
  This file owns durable feature behavior and human-readable interface promises. Source code owns
  implementation detail; executable tests/checks provide evidence. Do not copy either into prose.
  Place the feature in the module whose capability it is a use case of, never in a module that only
  collects the same kind of artifact; a project-wide use case stays at the root only when no single
  capability module owns it.
-->

## Outcome and Scope

**Outcome**: [One observable result for a consumer.]

**In scope**:

- [Behavior and interface owned by this feature.]

**Out of scope**:

- [Adjacent behavior deliberately excluded.]

## Usage

[Describe one representative successful use in plain language.]

### Edge Cases

- [Boundary condition and expected behavior.]
- [Externally visible failure and expected handling.]

## User Scenarios & Testing

<!--
  Prioritize independently testable journeys. Each scenario must deliver observable value without
  requiring later-priority scenarios. Examples illustrate requirements; requirements remain authority.
-->

### User Story 1 — [Brief title] (Priority: P1)

[Describe the consumer journey.]

**Why this priority**: [Value and ordering rationale.]

**Independent Test**: [Action, observable result, and evidence boundary.]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [observable outcome].
2. **Given** [edge/failure state], **When** [action], **Then** [safe observable handling].

### User Story 2 — [Brief title] (Priority: P2)

[Add only when it remains an independently useful slice.]

**Why this priority**: [Value and ordering rationale.]

**Independent Test**: [Action and observable result.]

**Acceptance Scenario**:

1. **Given** [initial state], **When** [action], **Then** [observable outcome].

## Interfaces

<!--
  Define every meaningful machine, human-workflow, or generated-artifact interface here. Existing
  stable contract.* IDs may remain interface identities. Do not create separate interface documents.
  If this feature exposes a Skill/Operation capability, state public/internal exposure, leaf effects,
  direct nested capabilities, narrowing obligations, and fail-closed enforcement in this interface;
  machine metadata remains in the canonical capability source rather than a duplicate registry.
-->

### `[interface.stable.id]` — [Interface name]

- **Consumer**: [consumer]
- **Direction**: [input, output, or bidirectional from provider]
- **Entry points**: [architecture entity IDs or named human workflow]
- **Inputs**: [shape, meaning, and explicit empty input when applicable]
- **Outputs**: [shape, meaning, and explicit empty output when applicable]
- **Obligations**: [provider and consumer invariants]
- **Failures**: [externally visible failure modes and handling]
- **Compatibility**: [versioning and migration expectations]
- **Example**: [representative use when serialized or non-obvious]
- **Implementing entities**: [stable entity IDs from module architecture]

## Architecture Zoom

<!--
  Reference only entities visible in the providing module architecture or permitted ancestry. Explain
  feature-specific collaboration without redefining entity identity, type, ownership, or locator.
  Diagrams belong to module architecture and may be linked here only as explanatory projections.
-->

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.[qualified.id]` | [Feature-specific role.] | [Ordered or conditional collaboration.] |

## Related Features

[For every `related_features` entry, explain the declared relation (composes, refines, depends on,
its inverse, or relates to) and why. Write `None.` when the list is empty.]

## Requirements

### Functional Requirements

- **FR-001**: The system MUST [specific testable behavior].
- **FR-002**: The system MUST [specific boundary or failure behavior].
- **FR-003**: [Named consumer] MUST be able to [observable interaction].

### Non-Functional Requirements

- **NFR-001**: [Measurable performance, safety, accessibility, portability, or compatibility rule.]

### Assumptions

- [Explicit bounded assumption that is not a hidden requirement.]

<!--
  Capability features must not assume that prompts or LangGraph enforce access. Require concrete
  path resolution plus supported native/outer enforcement, keep internal leaves unprojected, and
  require nested Operation composition to be acyclic and opaque.
-->

## Success Criteria

- **SC-001**: [Measurable, technology-independent outcome.]
- **SC-002**: [Evidence that material edge/failure behavior is covered.]
