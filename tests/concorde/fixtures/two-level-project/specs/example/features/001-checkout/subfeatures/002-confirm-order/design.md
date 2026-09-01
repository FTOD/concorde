---
id: feature.example.checkout.confirm
kind: feature
module: module.example
parent_feature: feature.example.checkout
refines: []
subfeatures: []
scenarios:
  - scenario.example.checkout.confirm
contracts:
  provided:
    - contract.example.checkout
  required: []
evidence_status: partial
canonical_design: specs/example/features/001-checkout/subfeatures/002-confirm-order/design.md
---
# Feature Design: Confirm Order
**Status**: Partial fixture
## Outcome
An authorized checkout receives one confirmation.
## Requirements
Confirmation preserves the parent checkout identity.

## Terminology

No local terminology. This level uses inherited terminology unchanged.
