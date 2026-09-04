---
id: feature.example.checkout
kind: feature
module: module.example
related_features:
  - feature.example.checkout.authorize
  - feature.example.checkout.confirm
  - feature.example.atomic
interfaces:
  provided:
    - contract.example.checkout
  required:
    - contract.example.authorization
    - contract.example.confirmation
---

# Feature Design: Checkout

## Outcome and Scope

A shopper completes one correlated checkout outcome.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.shopper` | Starts checkout. |
| `entity.example.checkout` | Coordinates authorization and confirmation. |
| `entity.example.authorizer` | Supplies the authorization decision. |
| `entity.example.confirmer` | Supplies confirmation. |

## Interfaces

### `contract.example.checkout` — Checkout workflow

**Consumer**: shopper

**Direction**: bidirectional

**Entry points**: `entity.example.checkout`

**Inputs**: A checkout request.

**Outputs**: One correlated outcome.

**Obligations**: Authorization precedes confirmation and all steps share checkout identity.

**Failures**: Authorization or confirmation failure aborts the checkout outcome.

**Compatibility**: The checkout identity and ordering remain stable.

**Implementing entities**: `entity.example.checkout`, `entity.example.authorizer`, `entity.example.confirmer`

## Usage Scenarios

1. A shopper completes authorization then confirmation.

## Requirements

- **FR-001**: Authorization precedes confirmation.

## Edge Cases

- A declined authorization prevents confirmation.
