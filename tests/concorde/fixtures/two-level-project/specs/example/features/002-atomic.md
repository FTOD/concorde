---
id: feature.example.atomic
kind: feature
module: module.example
related_features:
  - feature.example.checkout
interfaces:
  provided:
    - contract.example.atomic
  required: []
evidence_status: unknown
---

# Feature Design: Atomic Feature

## Outcome and Scope

One small fixture behavior completes atomically.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.checkout` | Provides the atomic boundary. |

## Interfaces

### `contract.example.atomic` — Atomic behavior

**Consumer**: fixture maintainer

**Direction**: bidirectional

**Entry points**: `entity.example.checkout`

**Inputs**: One atomic request.

**Outputs**: One atomic result.

**Obligations**: The request either completes once or has no observable effect.

**Failures**: Failure returns a named result and leaves state unchanged.

**Compatibility**: Atomic all-or-nothing semantics remain stable.

**Implementing entities**: `entity.example.checkout`

## Usage Scenarios

1. A maintainer invokes one atomic operation.

## Requirements

- **FR-001**: Failure has no partial effect.

## Edge Cases

- Duplicate invocation returns the same named result.
