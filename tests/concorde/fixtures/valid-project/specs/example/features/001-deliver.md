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
---

# Feature Design: Deliver

## Outcome and Scope

The maintainer receives the example workflow result; API internals remain outside this feature.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.maintainer` | Invokes delivery and consumes the result. |
| `entity.example.runtime` | Orchestrates delivery. |
| `module.example.api` | Provides the bounded transport operation. |

## Interfaces

### `contract.example.workflow` — Delivery workflow

**Consumer**: example maintainer

**Direction**: bidirectional

**Entry points**: `entity.example.runtime`

**Inputs**: A workflow request.

**Outputs**: A named workflow result.

**Obligations**: The consumer supplies a request; the provider delegates once and returns deterministically.

**Failures**: Invalid requests produce a named error without durable mutation.

**Compatibility**: The preserved contract identity retains compatible request/result semantics.

**Implementing entities**: `entity.example.runtime`, `module.example.api`

## Usage Scenarios

1. A maintainer invokes the runtime and receives an API-backed result.

## Requirements

- **FR-001**: Delivery returns one named result.

## Edge Cases

- An invalid request returns a named error.
