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
architecture_view: specs/example/architecture.json
evidence_status: partial
canonical_spec: specs/example/features/001-checkout/subfeatures/002-confirm-order/spec.md
---
# Feature Specification: Confirm Order
**Status**: Partial fixture
## Outcome
An authorized checkout receives one confirmation.
## Requirements
Confirmation preserves the parent checkout identity.
