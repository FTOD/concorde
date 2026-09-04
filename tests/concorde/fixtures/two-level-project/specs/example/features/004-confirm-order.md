---
id: feature.example.checkout.confirm
kind: feature
module: module.example
related_features:
  - feature.example.checkout
  - feature.example.checkout.authorize
interfaces:
  provided:
    - contract.example.confirmation
  required:
    - contract.example.authorization
---

# Feature Design: Confirm Order

## Outcome and Scope

An authorized checkout receives one confirmation.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.confirmer` | Produces order confirmation. |

## Interfaces

### `contract.example.confirmation` — Order confirmation

**Consumer**: checkout coordinator

**Direction**: bidirectional

**Entry points**: `entity.example.confirmer`

**Inputs**: An authorized checkout identity.

**Outputs**: One order confirmation.

**Obligations**: Confirmation preserves the checkout identity.

**Failures**: Missing authorization returns a named failure.

**Compatibility**: Checkout identity correlation remains stable.

**Implementing entities**: `entity.example.confirmer`

## Usage Scenarios

1. Checkout supplies authorization and receives confirmation.

## Requirements

- **FR-001**: Confirmation preserves checkout identity.

## Edge Cases

- Missing authorization prevents confirmation.
