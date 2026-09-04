---
id: feature.understanding.retrieve-bounded-context
kind: feature
module: module.concorde.understanding
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
interfaces:
  provided:
    - interface.concorde.context
  required: []
---

# Feature Design: Retrieve Bounded Context

## Outcome and Scope

A maintainer or agent can retrieve exactly one module or feature altitude with its visible entities,
relationships, interfaces, and navigation references, without reading descendants or unrelated bodies.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.capabilities` | Accepts a stable module/feature target and returns one structured envelope. |
| `entity.understanding.context-builder` | Loads Profile 7 and projects only the requested bounded context. |
| `entity.concorde.specification` | Supplies canonical architecture/design sources and related IDs. |

## Interfaces

### `interface.concorde.context` — Retrieve one bounded altitude

- **Consumer**: Maintainer or coding agent answering a scoped architecture/feature question.
- **Direction**: Input target to read-only structured output.
- **Entry points**: Leaf Skill `concorde-context` and native `context` Tool.
- **Inputs**: Stable module/feature ID and optional depth/format choices allowed by the Skill/Tool.
- **Outputs**: Current module, direct modules/features, visible entities/relations/interfaces, and deeper navigation references.
- **Obligations**: Never load or return descendant internals, unrelated feature bodies, attempts, or generated truth implicitly.
- **Failures**: Missing/ambiguous IDs, invalid hierarchy, or unsafe sources return findings and make no changes.
- **Compatibility**: Profile 7 context uses durable module/feature terminology and project-control paths explicitly.
- **Implementing entities**: `entity.understanding.context-builder`, `module.concorde.capabilities`.

## Usage Scenarios

1. Retrieve a module: responsibility/boundary/entities/relations/interactions/direct modules/features are returned.
2. Retrieve a feature: its design/interfaces/zoom plus providing module and related summaries are returned.
3. Follow an explicit deeper reference in a separate request rather than expanding the first result.

## Related Features

- `feature.concorde.workflow` composes this feature so every lifecycle phase can bound its reading to
  one module or feature altitude before acting.

## Requirements

- **FR-001**: Context MUST resolve stable IDs uniquely and load only canonical Profile 7 sources/control authorities.
- **FR-002**: Module context MUST stop at immediate children; feature context MUST not load unrelated feature bodies/attempts.
- **FR-003**: Returned paths/relations/interfaces MUST resolve and retain owning IDs/direction.
- **FR-004**: Context MUST be read-only and report ambiguity/missing sources as findings.

## Edge Cases

- A feature relates to a descendant-module feature whose body is not visible at the current request.
- A generated graph uses the same label as a maintained entity but has no source identity.
