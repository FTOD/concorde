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
architecture_view: specs/example/architecture.json
evidence_status: partial
canonical_spec: specs/example/features/001-checkout/spec.md
---
# Checkout
**Status**: Decomposed fixture
## Outcome
A shopper completes one correlated checkout outcome.
## Shared Invariants
Authorization precedes confirmation and both children share the checkout identity.
