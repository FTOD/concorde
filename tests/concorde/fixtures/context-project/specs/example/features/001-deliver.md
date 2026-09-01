---
id: feature.example.deliver
kind: feature
module: module.example
related_features:
  - feature.example.api.invoke
interfaces:
  provided:
    - contract.example.workflow
  required: []
evidence_status: unknown
---

# Feature Design: Deliver

## Outcome and Scope

The maintainer receives one API-backed workflow result.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.maintainer` | Requests and consumes delivery. |
| `entity.example.runtime` | Orchestrates the workflow. |
| `module.example.api` | Provides the child boundary. |

## Interfaces

### `contract.example.workflow` — Delivery workflow

**Consumer**: example maintainer

**Direction**: bidirectional

**Entry points**: `entity.example.runtime`

**Inputs**: A workflow request.

**Outputs**: A named result.

**Obligations**: The provider delegates once and returns deterministically.

**Failures**: Invalid input returns a named error.

**Compatibility**: The stable workflow interface remains compatible.

**Implementing entities**: `entity.example.runtime`, `module.example.api`

## Usage Scenarios

1. The maintainer invokes delivery and receives a result.

## Requirements

- **FR-001**: Delivery returns one result.

## Edge Cases

- Invalid input returns an error without mutation.
