---
id: feature.example.consumer.change
kind: feature
module: module.example.consumer
related_features:
  - feature.example.provider.api
  - feature.example.provider.unrelated
interfaces:
  provided:
    - contract.example.consumer.change
  required:
    - contract.provider.api
evidence_status: unknown
---

# Feature Design: Change Consumer

## Outcome and Scope

The consumer changes using only the provider's published API feature.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.example.consumer-service` | Implements the selected change. |

## Interfaces

### `contract.example.consumer.change` — Change the consumer

- **Consumer**: Fixture maintainer
- **Direction**: Request to consumer result.
- **Entry points**: `entity.example.consumer-service`
- **Inputs**: A bounded change request.
- **Outputs**: Updated consumer behavior.
- **Obligations**: Use only the published provider contract.
- **Failures**: Missing provider behavior stops the change.
- **Compatibility**: Stable fixture identity.
- **Implementing entities**: `entity.example.consumer-service`

## Usage Scenarios

1. The maintainer changes the consumer through `contract.provider.api`.

## Requirements

- **FR-001**: Planning includes the provider feature that owns `contract.provider.api`.

## Edge Cases

- An unrelated provider feature remains unreadable.
