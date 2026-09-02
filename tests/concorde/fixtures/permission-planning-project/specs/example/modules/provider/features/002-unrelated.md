---
id: feature.example.provider.unrelated
kind: feature
module: module.example.provider
related_features: []
interfaces:
  provided:
    - contract.provider.unrelated
  required: []
evidence_status: unknown
---

# Feature Design: Unrelated Provider Behavior

## Outcome and Scope

Publish behavior that the selected consumer does not require.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.example.provider-service` | Implements unrelated behavior. |

## Interfaces

### `contract.provider.unrelated` — Unrelated provider behavior

- **Consumer**: Another consumer
- **Direction**: Request to result.
- **Entry points**: `entity.example.provider-service`
- **Inputs**: An unrelated request.
- **Outputs**: An unrelated result.
- **Obligations**: Keep the behavior independent.
- **Failures**: Invalid requests fail.
- **Compatibility**: Stable fixture contract.
- **Implementing entities**: `entity.example.provider-service`

## Usage Scenarios

1. Another consumer invokes the unrelated behavior.

## Requirements

- **FR-001**: The unrelated behavior stays outside selected planning context.

## Edge Cases

- A `related_features` mention alone grants no read permission.
