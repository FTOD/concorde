---
id: feature.example.checkout.authorize
kind: feature
module: module.example
related_features:
  - feature.example.checkout
  - feature.example.checkout.confirm
interfaces:
  provided:
    - contract.example.authorization
  required: []
evidence_status: verified
---

# Feature Design: Authorize Payment

## Outcome and Scope

A valid checkout receives an explicit authorization decision.

## Architecture Zoom

| Entity | Role |
|---|---|
| `entity.example.authorizer` | Produces the authorization decision. |

## Interfaces

### `contract.example.authorization` — Authorization decision

**Consumer**: checkout coordinator

**Direction**: bidirectional

**Entry points**: `entity.example.authorizer`

**Inputs**: A payment authorization request.

**Outputs**: Approved or declined decision.

**Obligations**: Every request receives one traceable decision.

**Failures**: Provider failure returns an unavailable decision.

**Compatibility**: Decision identity remains stable.

**Implementing entities**: `entity.example.authorizer`

## Usage Scenarios

1. Checkout requests and receives authorization.

## Requirements

- **FR-001**: The decision is explicit and traceable.

## Edge Cases

- An unavailable provider produces a named unavailable decision.
