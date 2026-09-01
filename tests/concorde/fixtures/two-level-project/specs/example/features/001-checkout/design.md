---
id: feature.example.checkout
kind: feature
module: module.example
refines: []
subfeatures:
  - feature.example.checkout.authorize
  - feature.example.checkout.confirm
scenarios:
  - scenario.example.checkout
contracts:
  provided:
    - contract.example.checkout
  required: []
evidence_status: partial
canonical_design: specs/example/features/001-checkout/design.md
---
# Checkout
**Status**: Decomposed fixture
## Outcome
A shopper completes one correlated checkout outcome.
## Shared Invariants
Authorization precedes confirmation and both children share the checkout identity.

## Terminology

No local terminology. This level uses inherited terminology unchanged.
